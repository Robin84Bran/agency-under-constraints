"""POST HOC descriptive counts, independent of the failed frozen entry point.

Replays terminal world events with the unchanged independent replay function.
No bootstrap, primary verdict, prediction adjudication or model generation.
Does not claim the frozen raw-response/provenance pipeline completed.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rg_analysis import replay, behavior
from rg_usage_limit import episode_directory


def summarize():
    schedule = json.loads((ROOT/'config/episodes.json').read_text())
    pools, errors, resources = defaultdict(Counter), Counter(), defaultdict(Counter)
    rows = []
    for ep in schedule:
        directory = episode_directory(ROOT/'collection', ep['id'])
        terminal = json.loads((directory/'episode.json').read_text())
        assert terminal['episode'] == ep
        counts, ended, _ = replay(ep, terminal['events'])
        assert counts == terminal['counts'] and ended == terminal['ended']
        duplicate, done = any(n > 1 for n in counts), all(n > 0 for n in counts)
        report = terminal['report']
        action_valid = terminal['trajectory_valid']
        values = dict(n=1, known=1, duplicates=int(duplicate),
                      exact_once=int(all(n == 1 for n in counts) and action_valid),
                      valid=int(action_valid), reports=int(report is not None),
                      both_valid=int(action_valid and report is not None),
                      J=int(report is not None and report['all_done'] is done and report['any_duplicate'] is duplicate),
                      TP=int(duplicate and report is not None and report['any_duplicate'] is True),
                      FP=int(not duplicate and report is not None and report['any_duplicate'] is True),
                      FD=int(duplicate and report is not None and report['any_duplicate'] is False),
                      null_done=int(report is not None and report['all_done'] is None),
                      null_duplicate=int(report is not None and report['any_duplicate'] is None),
                      decisions=terminal['decisions'], all_done=int(done),
                      missed_jobs=sum(n == 0 for n in counts), extra_effects=sum(max(n-1, 0) for n in counts))
        key = '/'.join(map(str, (ep['actor'], ep['toolkit'], ep['receipt_loss'])))
        pools[key].update(values)
        if terminal['error']:
            errors[ep['actor'] + ' / ' + terminal['error']] += 1
        res = resources[ep['actor']]
        res.update(episodes=1, calls=terminal['attempted_calls'])
        for path in directory.glob('*.parsed.json'):
            parsed = json.loads(path.read_text())
            for k in ('input_tokens', 'output_tokens'):
                if parsed[k] is None:
                    res['unknown_' + k] += 1
                else:
                    res[k] += parsed[k]
        rows.append({'episode': ep, 'counts': counts, 'values': values,
                     'behavior': behavior(terminal['events']), 'report': report})
    return {'kind': 'POST HOC DESCRIPTIVE TERMINAL REPLAY; NOT A COMPLETED FROZEN ANALYSIS',
            'cells': {k: dict(v) for k, v in pools.items()}, 'errors': dict(errors),
            'resources': {k: dict(v) for k, v in resources.items()}, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        stream.write(json.dumps(summarize(), sort_keys=True, separators=(',', ':')) + '\n')
