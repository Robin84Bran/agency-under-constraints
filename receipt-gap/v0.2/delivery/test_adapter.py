"""Regression and rejection checks for the delivery-only scope adapter."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def functions(path):
    source = path.read_text()
    return {n.name: ast.get_source_segment(source, n) for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v01-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    old, out = args.v01_root.resolve(), args.output_root.resolve()
    out.mkdir(exist_ok=False)
    same = {}
    for filename, names in [('rg_analysis.py', ('replay', 'behavior', 'score', 'summarize', 'contrast', 'framing', 'analyze')),
                            ('rg_stats.py', tuple(functions(ROOT/'rg_stats.py')))]:
        a, b = functions(old/filename), functions(ROOT/filename)
        for name in names:
            assert a[name] == b[name], (filename, name)
            same[filename+':'+name] = hashlib.sha256(b[name].encode()).hexdigest()
    command = [sys.executable, '-B', str(ROOT/'delivery/r5_compatibility.py'), '--root', str(old), '--output', str(out/'analysis-v01.json')]
    proc = subprocess.run(command, cwd=out, capture_output=True, text=True)
    (out/'stdout').write_text(proc.stdout)
    (out/'stderr').write_text(proc.stderr)
    assert proc.returncode == 0, proc.stderr
    expected = ROOT/'delivery/source-v01/analysis-v01.json'
    assert (out/'analysis-v01.json').read_bytes() == expected.read_bytes(), 'v0.1 byte identity failed'
    sys.path.insert(0, str(ROOT))
    import r5_compatibility as adapter
    from rg_core import sha, strict_load
    import rg_analysis
    adapter.sha, adapter.strict_load = sha, strict_load
    adapter.ORIGINAL = rg_analysis.check_saved_push
    receipt = strict_load((ROOT/'collection/push-r5.json').read_text())
    seal = digest(ROOT/'freeze-r5.json')
    adapter.check_r5(ROOT, ROOT/'collection', receipt, seal)
    rejected = []
    for key, value in [('freeze_sha256', '0'*64), ('event_sha256', '0'*64), ('server_event_id', 'invalid'),
                       ('repo', 'wrong/repo'), ('commit', '0'*40), ('remote_ref', 'refs/heads/invalid'),
                       ('pushed_at', '2000-01-01T00:00:00Z'), ('freeze_file', 'freeze-r4.json')]:
        try:
            adapter.check_r5(ROOT, ROOT/'collection', {**receipt, key:value}, seal)
        except ValueError:
            rejected.append(key)
        else:
            raise AssertionError('accepted tampered '+key)
    record = {'status':'PASS', 'adapter_sha256':digest(ROOT/'delivery/r5_compatibility.py'),
              'command':command, 'returncode':proc.returncode, 'v01_byte_identical':True,
              'v01_sha256':digest(expected), 'v01_bytes':expected.stat().st_size,
              'unchanged_calculation_functions':same, 'r5_receipt_valid':True, 'tampered_receipt_fields_rejected':rejected,
              'v02_analysis_executed':False, 'model_calls':0}
    (out/'verification.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
    print(json.dumps(record, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
