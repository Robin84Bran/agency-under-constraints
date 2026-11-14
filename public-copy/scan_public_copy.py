#!/usr/bin/env python3
"""Scan a directory tree (every file, archives opened) for private-looking strings.

Usage: scan_public_copy.py <dir> [extra_regex ...]
Prints, per pattern, the number of files and the most common distinct matches.
Standard library only.
"""
import collections, gzip, io, lzma, os, re, sys, tarfile, zipfile
from multiprocessing import Pool

ROOT = sys.argv[1]
UUID = rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
PATTERNS = {
    "home_dir": rb"(?:\\*/)(?:Users|home)(?:\\*/)[A-Za-z0-9._-]+",
    "var_folders": rb"/var/folders/[A-Za-z0-9_]+/[A-Za-z0-9_]+",
    "tmp_claude": rb"/private/tmp/claude[A-Za-z0-9_./-]{0,40}",
    "dot_local_host": rb"[A-Za-z0-9-]+\.local\b",
    "email": rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}",
    "secret": rb"sk-ant-[A-Za-z0-9_-]{8,}|gh[opsu]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|xox[baprs]-[A-Za-z0-9-]{10,}",
    "id_key_with_uuid": rb'\\*"[A-Za-z_]*(?:id|Id|uuid)\\*"\s*:\s*\\*"' + UUID,
    "ipv4": rb"\b(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))\.[0-9]{1,3}\.[0-9]{1,3}(?:\.[0-9]{1,3})?\b",
    "chat_link": rb"claude\.ai/(?:chat|share|code/[a-z])[A-Za-z0-9/_-]*|chatgpt\.com/(?:c|share)/[A-Za-z0-9-]+",
    "account_field": rb'\\*"(?:email|account_uuid|accountUuid|organization_uuid|organizationUuid|org_id|user_id|userID|oauth[A-Za-z_]*)\\*"\s*:\s*\\*"[^"\\]{0,60}',
}
for i, extra in enumerate(sys.argv[2:]):
    PATTERNS[f"extra{i}"] = extra.encode()
RX = {k: re.compile(v) for k, v in PATTERNS.items()}


def payloads(path, data):
    low = path.lower()
    try:
        if low.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
            with tarfile.open(fileobj=io.BytesIO(data)) as t:
                for m in t:
                    yield m.name.encode()
                    if m.isfile():
                        yield t.extractfile(m).read()
            return
        if low.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for n in z.namelist():
                    yield n.encode(); yield z.read(n)
            return
        if low.endswith(".gz"):
            yield gzip.decompress(data); return
        if low.endswith(".xz"):
            yield lzma.decompress(data); return
    except Exception:
        pass
    yield data


def work(path):
    out = {}
    data = open(path, "rb").read()
    blobs = [path[len(ROOT):].encode()] + list(payloads(path, data))
    for k, rx in RX.items():
        c = collections.Counter()
        for b in blobs:
            for m in rx.findall(b):
                c[m[:90]] += 1
        if c:
            out[k] = c
    return out


if __name__ == "__main__":
    files = []
    for d, dirs, names in os.walk(ROOT):
        if ".git" in dirs:
            dirs.remove(".git")
        files += [os.path.join(d, n) for n in names]
    nfiles = collections.Counter(); matches = {k: collections.Counter() for k in RX}
    with Pool() as pool:
        for res in pool.imap_unordered(work, files, chunksize=2000):
            for k, c in res.items():
                nfiles[k] += 1; matches[k].update(c)
    print("files scanned:", len(files))
    for k in RX:
        print(f"--- {k}: {nfiles[k]} files, {len(matches[k])} distinct")
        for m, n in matches[k].most_common(12):
            print(f"   {n:8d}  {m.decode('utf-8', 'replace')}")
