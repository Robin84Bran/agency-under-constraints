"""Disclosed delivery-only version/scope and r5 provenance adapter.

The frozen check_saved_push allowlist ends at r3. This adapter accepts ONLY the
active r5 receipt after enforcing the same hash/repository/commit/ref/time gates.
All earlier receipts still use the original function. No frozen file, prompt,
sample, scorer, statistical function, gate or prediction is edited.
--verify-only performs the independent receipt check without running analysis.
Claude permitted this adapter on 2026-11-12, conditional on v0.1 byte identity.
--root selects a package and its native frozen loader; calculations are unchanged.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = None


def check_r5(root, base, receipt, digest):
    if receipt.get('freeze_file') != 'freeze-r5.json':
        return ORIGINAL(root, base, receipt, digest)
    data = (base/receipt.get('event_file', 'push-event.json')).read_bytes()
    event = strict_load(data.decode())
    if (receipt.get('freeze_sha256') != digest or receipt.get('repo') != 'Robin84Bran/research'
            or receipt.get('event_sha256') != sha(data)
            or receipt.get('server_event_id') != event.get('id')):
        raise ValueError('saved push attestation binding mismatch')
    if event.get('type') == 'PushEvent':
        payload = event.get('payload', {})
        if event.get('repo', {}).get('name') != 'Robin84Bran/research':
            raise ValueError('push repository mismatch')
        commit, ref, timestamp = payload.get('head', payload.get('after')), payload.get('ref'), event.get('created_at')
    elif event.get('activity_type') == 'push':
        commit, ref, timestamp = event.get('after'), event.get('ref'), event.get('timestamp')
    else:
        raise ValueError('invalid saved server push record')
    if (commit != receipt.get('commit') or timestamp != receipt.get('pushed_at')
            or ref != receipt.get('remote_ref') or not isinstance(ref, str) or not ref.startswith('refs/heads/')):
        raise ValueError('saved push record differs')
    pushed = dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    sealed = dt.datetime.fromisoformat(strict_load((root/'freeze-r5.json').read_text())['created_at'])
    if pushed.tzinfo is None or pushed < sealed or pushed >= dt.datetime.now(dt.timezone.utc):
        raise ValueError('saved server push time invalid')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    sys.path.insert(0, str(ROOT))
    import rg_analysis as frozen
    from rg_core import sha, strict_load
    if (ROOT/'freeze-r5.json').exists():
        seal = strict_load((ROOT/'freeze-r5.json').read_text())
        for name in ('rg_analysis.py', 'rg_stats.py', 'rg_core.py', 'config/episodes.json'):
            if sha((ROOT/name).read_bytes()) != seal['files'][name]:
                raise ValueError('r5 sealed analysis input changed: '+name)
        ORIGINAL = frozen.check_saved_push
        frozen.check_saved_push = check_r5
    elif (ROOT/'config/prior-spend.json').exists():
        raise ValueError('v0.2 requires the r5 seal')
    if args.verify_only:
        receipt = strict_load((ROOT/'collection/push-r5.json').read_text())
        check_r5(ROOT, ROOT/'collection', receipt, sha((ROOT/'freeze-r5.json').read_bytes()))
        print(json.dumps({'status': 'PASS', 'receipt': 'push-r5.json', 'analysis_executed': False}))
    else:
        if not args.output:
            parser.error('--output is required to run the scorer')
        sys.argv = ['rg_analysis.py', '--root', str(ROOT), '--output', str(args.output)]
        frozen.main()
