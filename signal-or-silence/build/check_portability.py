"""One-time offline integration check, using only copied project evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sos_import import import_evidence,sha,json_bytes,immutable_write
from sos_design import build_design
from sos_prepare import prepare_requests


def main():
    rebuilt=ROOT/'build/portable-rebuild'
    if rebuilt.exists():raise FileExistsError('keep old rebuild evidence; choose a new task-owned path')
    rebuilt.mkdir()
    # The archive evidence manifest names every required source and excludes
    # machine-local local.env; no original archive path is copied into a lookup.
    manifest=json.loads((ROOT/'evidence/manifest.json').read_text())
    for name in manifest['files']:
        dest=rebuilt/'evidence'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((ROOT/'evidence'/name).read_bytes())
    (rebuilt/'evidence/manifest.json').write_bytes((ROOT/'evidence/manifest.json').read_bytes())
    (rebuilt/'PROTOCOL.md').write_bytes((ROOT/'PROTOCOL.md').read_bytes())
    with patch.object(socket,'socket',side_effect=AssertionError('network forbidden during offline rebuild')):
        report=import_evidence(rebuilt,source_root=rebuilt/'missing-original-archive')
        design=build_design(rebuilt)
        request_summary=prepare_requests(rebuilt)
    names=['imported/dataset.json','imported/reconciliation.json','imported/validation_counts.json','imported/retrospective_sufficiency.json','config/all_certificates.json','config/design.json','config/instructions.json','config/requests.json','config/request_summary.json']
    hashes={}
    for name in names:
        original=(ROOT/name).read_bytes();new=(rebuilt/name).read_bytes()
        if original!=new:raise AssertionError('portable rebuild differs: '+name)
        hashes[name]=sha(new)
    result={'status':'PASS','original_archive_available':False,'network_allowed':False,'provider_modules_imported':False,'source_files':len(manifest['files']),'reconciliation':report['status'],'primary_episodes':len(design['primary_ids']),'receipt_episodes':len(design['receipt_ids']),'requests':request_summary['jobs'],'identical_outputs_sha256':hashes}
    immutable_write(ROOT/'build/portability_report.json',json_bytes(result))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
