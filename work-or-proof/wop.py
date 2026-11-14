"""Work or Proof? standard-library command line. Import/verify/test are offline."""
import argparse
import hashlib
import json
from pathlib import Path

from wop_freeze import make_freeze, verify_freeze, write_new

ROOT = Path(__file__).resolve().parent


def record_push(root, args):
    from datetime import datetime, timezone
    verify_freeze(root)
    when = datetime.fromisoformat(args.pushed_at.replace('Z', '+00:00'))
    if when.tzinfo is None or when > datetime.now(timezone.utc):
        raise ValueError('Push time must be a server-sourced past UTC timestamp with timezone')
    if args.remote != 'https://github.com/Robin84Bran/research':
        raise ValueError('Unexpected research remote')
    if len(args.commit) != 40 or any(c not in '0123456789abcdef' for c in args.commit):
        raise ValueError('Commit must be the 40-character pushed commit SHA')
    write_new(root / 'collection/push.json', {
        'freeze_sha256': hashlib.sha256((root / 'freeze.json').read_bytes()).hexdigest(),
        'pushed_at': when.isoformat(), 'remote': args.remote, 'commit': args.commit,
        'server_timestamp_source': args.timestamp_source,
        'attested_by': args.attested_by,
        'note': 'Offline attestation supplied by operator; build does not contact GitHub.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    imp = sub.add_parser('import', help='Copy once or verify portable evidence and reconcile offline')
    imp.add_argument('--source-root', type=Path)
    sub.add_parser('verify', help='Verify all frozen hashes, no network')
    sub.add_parser('freeze', help='Create freeze exactly once, no network')
    sub.add_parser('collect', help='LATER STAGE: actual local inference after verified push')
    analysis = sub.add_parser('analyze', help='Offline frozen policy/statistics/render rebuild')
    analysis.add_argument('--output', type=Path, required=True)
    push = sub.add_parser('record-push', help='Record operator-supplied server push evidence')
    push.add_argument('--pushed-at', required=True)
    push.add_argument('--commit', required=True)
    push.add_argument('--remote', default='https://github.com/Robin84Bran/research')
    push.add_argument('--timestamp-source', required=True)
    push.add_argument('--attested-by', default='Claude')
    args = parser.parse_args()
    if args.command == 'import':
        from wop_import import import_evidence
        report = import_evidence(ROOT, args.source_root)
        print(json.dumps(report, sort_keys=True))
    elif args.command == 'freeze':
        print(make_freeze(ROOT))
    elif args.command == 'verify':
        manifest = verify_freeze(ROOT)
        print('PASS:', len(manifest['files']), 'frozen files')
    elif args.command == 'record-push':
        record_push(ROOT, args)
        print('Saved collection/push.json; no network performed')
    elif args.command == 'collect':
        from wop_collect import collect
        print(json.dumps(collect(ROOT), sort_keys=True))
    elif args.command == 'analyze':
        verify_freeze(ROOT)
        output = args.output.resolve()
        if not output.is_relative_to(ROOT):
            raise ValueError('Analysis output must stay inside this project')
        from wop_analysis import analyze
        print(json.dumps(analyze(ROOT, output), sort_keys=True))


if __name__ == '__main__':
    main()
