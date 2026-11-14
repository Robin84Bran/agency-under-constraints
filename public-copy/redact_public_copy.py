#!/usr/bin/env python3
"""Redact machine-local details from a checkout, in place, and record every change.

Usage: redact_public_copy.py <checkout> <rules.json> <out_dir>

rules.json (kept outside the public repository, because it names the strings
being removed) is a list of [regex, replacement, label] triples, applied in
order to the raw bytes of every tracked text file. Archives are opened and
searched; an archive containing any match is withheld, not rewritten.

Outputs in <out_dir>: redactions.jsonl (one line per changed or withheld file,
with the SHA-256 of the original and public bytes and per-rule counts) and
summary.json. Standard library only.
"""
import gzip, hashlib, io, json, lzma, os, re, subprocess, sys, tarfile, zipfile
from multiprocessing import Pool

ROOT, RULES_PATH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
RULES = [(re.compile(p.encode()), r.encode(), label) for p, r, label in json.load(open(RULES_PATH))]
ARCHIVE = re.compile(r"\.(tar\.gz|tgz|tar\.xz|tar|gz|xz|zip)$", re.I)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def archive_payloads(path, data):
    low = path.lower()
    try:
        if low.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
            with tarfile.open(fileobj=io.BytesIO(data)) as t:
                for m in t:
                    yield m.name.encode()
                    if m.isfile():
                        yield t.extractfile(m).read()
        elif low.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    yield n.encode()
                    yield z.read(n)
        elif low.endswith(".gz"):
            yield gzip.decompress(data)
        elif low.endswith(".xz"):
            yield lzma.decompress(data)
    except Exception as e:  # unreadable archive: treat as a hit, withhold
        yield b"UNREADABLE-ARCHIVE " + repr(e).encode()


def work(path):
    full = os.path.join(ROOT, path)
    data = open(full, "rb").read()
    if ARCHIVE.search(path):
        counts = {}
        for blob in archive_payloads(path, data):
            if blob.startswith(b"UNREADABLE-ARCHIVE"):
                counts["unreadable"] = 1
            for rx, _, label in RULES:
                n = len(rx.findall(blob))
                if n:
                    counts[label] = counts.get(label, 0) + n
        if counts:
            os.remove(full)
            return {"path": path, "action": "withheld", "sha256_original": sha(data), "bytes": len(data), "counts": counts}
        return None
    if b"\0" in data[:8192]:
        counts = {label: len(rx.findall(data)) for rx, _, label in RULES if rx.search(data)}
        if counts:
            os.remove(full)
            return {"path": path, "action": "withheld", "sha256_original": sha(data), "bytes": len(data), "counts": counts}
        return None
    new, counts = data, {}
    for rx, rep, label in RULES:
        new, n = rx.subn(rep, new)
        if n:
            counts[label] = counts.get(label, 0) + n
    if new == data:
        return None
    with open(full, "wb") as f:
        f.write(new)
    return {"path": path, "action": "redacted", "sha256_original": sha(data), "sha256_public": sha(new), "counts": counts}


if __name__ == "__main__":
    files = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], capture_output=True, check=True).stdout.split(b"\0")
    files = [f.decode() for f in files if f]
    os.makedirs(OUT, exist_ok=True)
    totals, changed, withheld = {}, 0, 0
    with Pool() as pool, open(os.path.join(OUT, "redactions.jsonl"), "w") as log:
        for rec in pool.imap(work, files, chunksize=2000):
            if not rec:
                continue
            log.write(json.dumps(rec, sort_keys=True) + "\n")
            changed += rec["action"] == "redacted"
            withheld += rec["action"] == "withheld"
            for k, v in rec["counts"].items():
                totals[k] = totals.get(k, 0) + v
    json.dump({"files_tracked": len(files), "files_redacted": changed, "files_withheld": withheld,
               "replacements_by_rule": totals}, open(os.path.join(OUT, "summary.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps({"files": len(files), "redacted": changed, "withheld": withheld, "totals": totals}, indent=1))
