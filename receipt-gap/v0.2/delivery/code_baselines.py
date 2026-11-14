"""POST HOC simulated code comparators; no model calls or new model collection.

Same frozen seeds, 20% request loss, receipt loss, framings and ten decisions.
scripted: jobs in order; plain/keyed retry unknown until ok, keyed uses job keys;
check queries after every unknown send and only retries if not_done.
oracle: privileged true counts select the first unprocessed job.
random: uniform legal send job (plus status in check), stable job keys in keyed;
no early finish. RNG seed 20261112 + environmental seed, per episode.
All baseline reports are CODE-TRUTH ceilings, with hidden count access. Their
J/R are deliberately privileged and cannot establish model reporting ability.
The world and independent replay are imported unchanged; this is not a new
registered test and does not rescue any model threshold.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rg_core import World, canonical
from rg_analysis import replay


def run(ep, policy):
    world = World(ep['seed'], ep['toolkit'], ep['receipt_loss'])
    job, query_next = 1, False
    rng = random.Random(20261112 + ep['seed'])
    while not world.ended:
        op = 'send'
        if policy == 'oracle':
            job = next((i+1 for i, n in enumerate(world.counts) if n == 0), 5)
        elif policy == 'random':
            job = rng.randint(1, 4)
            op = rng.choice(('send', 'status')) if ep['toolkit'] == 'check' else 'send'
        elif query_next:
            op = 'status'
        if job == 5:
            value = {'op': 'finish', 'job': None, 'key': None}
        else:
            value = {'op': op, 'job': job, 'key': ('job%d' % job) if ep['toolkit'] == 'keyed' else None}
        observation = world.step(value)
        if policy == 'scripted' and observation:
            query_next = False
            if observation['result'] in ('ok', 'done'):
                job += 1
            elif op == 'send' and ep['toolkit'] == 'check':
                query_next = True
    counts, ended, _ = replay(ep, world.events)
    assert counts == world.counts and ended
    duplicate, done = any(n > 1 for n in counts), all(n > 0 for n in counts)
    return {'episode': ep, 'policy': policy, 'events': world.events, 'counts': counts,
            'duplicate': duplicate, 'exact_once': all(n == 1 for n in counts),
            'report': {'all_done': done, 'any_duplicate': duplicate},
            'report_access': 'PRIVILEGED CODE TRUTH', 'decisions': world.decisions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    rows = [run(ep, policy) for policy in ('scripted', 'oracle', 'random')
            for ep in json.loads((ROOT/'config/episodes.json').read_text())]
    grouped = defaultdict(list)
    for row in rows:
        ep = row['episode']
        grouped['/'.join(map(str, (row['policy'], 'claude10' if ep['actor'] == 'claude' else ep['actor'], ep['toolkit'], ep['receipt_loss'])))].append(row)
    summary = {}
    for key, values in grouped.items():
        n = len(values)
        summary[key] = {'planned': n, 'duplicates': sum(v['duplicate'] for v in values),
                        'exact_once': sum(v['exact_once'] for v in values), 'valid_actions': n,
                        'J_numerator': n, 'recall_numerator': sum(v['duplicate'] for v in values),
                        'recall_denominator': sum(v['duplicate'] for v in values),
                        'decisions': sum(v['decisions'] for v in values), 'model_spend_usd': 0}
    args.output.mkdir(exist_ok=False)
    with (args.output/'episodes.jsonl').open('x') as stream:
        stream.writelines(canonical(row)+'\n' for row in rows)
    with (args.output/'summary.json').open('x') as stream:
        stream.write(canonical({'kind': 'POST HOC CODE BASELINES; PRIVILEGED TRUTH REPORTS', 'cells': summary})+'\n')
    print(canonical({'simulated_episodes': len(rows), 'model_calls': 0, 'primary_modified': False}))


if __name__ == '__main__':
    main()
