"""Signal or Silence v0.2: offline preparation and version-isolated adapters.

The frozen transport and numerical analysis functions are reused unchanged.
The versioned serial collector adds the reviewed usage-limit non-start exception.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))
import sos_collect as base
import sos_analysis as analysis
import usage_limit
import usage_deviation
from sos_collect import CollectionStop, D, SYSTEM, canonical, read_json, save_new, sha, utcnow

SENTENCE = 'Reply with only the JSON object, no other text.'
VERSION = 'v0.2'
OPERATIONAL = D('39')
ABSOLUTE = D('40')


def require(ok, reason):
    if not ok:
        raise CollectionStop(reason)


def digest(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'missing/symlink input: ' + str(path))
    return sha(path.read_bytes())


def reconcile(path):
    """Replay the original append-only format, retaining all unknown reserves."""
    ledger = base.CostLedger(path)
    require(ledger.total <= OPERATIONAL, 'cumulative operational stop exceeded')
    return {'accounted_usd': str(ledger.total),
            'settled_usd': str(sum((ledger.amounts[k] for k in ledger.settled), D(0))),
            'outstanding_usd': str(sum((v for k, v in ledger.amounts.items() if k not in ledger.settled), D(0))),
            'reserves': len(ledger.reserved), 'settlements': len(ledger.settled),
            'sha256': digest(path)}


def allowance(job):
    b = len(job['prompt'].encode('utf-8')) + len(SYSTEM.encode('utf-8')) + 826
    tin = ((b * 110 + 6399) // 6400) * 64
    return {'input_tokens': tin, 'output_tokens': 448,
            'usd': str((tin * D(4) + D(448) * 20) / 1000000),
            'basis': 'v0.2 rolling gate; D1 UTF-8 bytes + 826, 10% rounded to 64; empirical allowances, not token caps'}


def transform(project):
    project = Path(project)
    instructions = read_json(project / 'config/instructions.json')
    original = read_json(project / 'config/requests.json')
    jobs = []
    for old in original['jobs']:
        if old['model'] != 'claude':
            continue
        job = copy.deepcopy(old)
        prefix = instructions[old['instruction']] + '\nInput:\n'
        require(old['prompt'].startswith(prefix), 'original instruction/separator drift')
        payload = old['prompt'][len(prefix):]
        job['prompt'] = instructions[old['instruction']] + ' ' + SENTENCE + '\nInput:\n' + payload
        job['request']['prompt'] = job['prompt']
        job.update(version=VERSION, original_id=old['id'],
                   id='v02-' + sha((VERSION + '|' + old['id']).encode()),
                   prompt_sha256=sha(job['prompt'].encode()),
                   request_sha256=sha(canonical(job['request']).encode()))
        estimate = allowance(job)
        job.update(reservation_usd=estimate['usd'], reservation_input_tokens=estimate['input_tokens'],
                   reservation_output_tokens=estimate['output_tokens'])
        jobs.append(job)
    require(len(jobs) == 1868 and len({j['id'] for j in jobs}) == 1868, 'incorrect unique Claude schedule')
    require(all(sum(j['instruction'] == i for j in jobs) == 934 for i in instructions), 'instruction assignment drift')
    return {'format': 1, 'version': VERSION, 'shuffle_seed': original['shuffle_seed'], 'jobs': jobs}


def budget_plan(jobs, prior):
    total = sum((D(allowance(j)['usd']) for j in jobs), D(0))
    return {'version': VERSION, 'prior': prior, 'operational_stop_usd': '39', 'absolute_cap_usd': '40',
            'new_reservations_usd': str(total),
            'all_reservations_plus_prior_usd': str(total + D(prior['accounted_usd'])),
            'all_reservations_plus_prior_plus_cushion_usd': str(total + D(prior['accounted_usd']) + 5),
            'initial_operational_remaining_usd': str(OPERATIONAL - D(prior['accounted_usd'])),
            'max_input_tokens': {i: max(allowance(j)['input_tokens'] for j in jobs if j['instruction'] == i)
                                 for i in ('plain', 'explicit')},
            'output_tokens': 448, 'system_utf8_bytes': len(SYSTEM.encode()),
            'historical_input_usd_per_million': '4', 'historical_output_usd_per_million': '20',
            'current_invoiced_cost_status': 'UNKNOWN', 'subscription_opportunity_cost_usd': None,
            'amendment': 'Rolling settled/conservatively charged spend + open reserves + proposed reserve <= USD39 across both versions. Full-plan plus USD5 feasibility test is relaxed by explicit agreement; may stop incomplete. No cap increase.',
            'empirical_allowances_are_hard_limits': False, 'one_call_in_flight': True,
            'mean_cost_forecast_new_usd': '11.053392', 'forecast_project_usd': '22.106784',
            'planning_1_5x_new_usd': '16.580088', 'planning_project_plus_cushion_usd': '32.633480'}


def prepare(root=HERE):
    root = Path(root).resolve()
    require(not (root / 'freeze.json').exists(), 'already frozen')
    project = root.parent
    from sos_freeze import verify_freeze
    verify_freeze(project)
    prior = reconcile(project / 'collection/cost.jsonl')
    require(prior['settled_usd'] == '11.053392' and prior['outstanding_usd'] == '0', 'v0.1 ledger differs from agreed baseline')
    require(prior['reserves'] == prior['settlements'] == 1868, 'v0.1 accounting incomplete')
    requests = transform(project)
    old_config = read_json(project / 'config/collector.json')
    config = {k: copy.deepcopy(old_config[k]) for k in ('format', 'claude_transport', 'cost')}
    config.update(version=VERSION, models={'claude': old_config['models']['claude']},
                  requests_file='config/requests.json', preflight_inference_jobs=0,
                  runtime_identity_status='UNKNOWN', timeout_seconds=420)
    config['cost'].update(cap_usd='39', absolute_cap_usd='40', input_usd_per_million=4,
                          output_usd_per_million=20, mechanism='v0.2 rolling cumulative reservation gate')
    inputs = {'config/requests.json': requests,
              'config/instructions.json': {k: v + ' ' + SENTENCE for k, v in read_json(project / 'config/instructions.json').items()},
              'config/collector.json': config,
              'config/budget.json': budget_plan(requests['jobs'], prior),
              'config/forecasts.json': {
                  'V2-P1': 'Validity >=0.95 in every F/T/R x instruction cell, both weightings',
                  'V2-P2': 'T abstention >=0.90; F and R abstention <=0.10, each instruction and weighting',
                  'V2-P3': 'Primary: plain-plus-format complete joint pass, both weightings',
                  'V2-P4': 'Secondary: explicit-plus-format complete joint pass, both weightings; cannot rescue primary',
                  'V2-P5': 'Receipt trajectory: plain W abstention <=0.10, explicit W >=0.70, explicit-minus-plain >=0.60'}}
    for name, value in inputs.items():
        save_new(root / name, value)
    return budget_plan(requests['jobs'], prior)


class RollingLedger(base.CostLedger):
    """Reuse append-only entries; add immutable prior spend to each gate."""
    def __init__(self, path, cap='39', prior='0'):
        self.prior = D(str(prior))
        require(self.prior.is_finite() and self.prior >= 0, 'invalid prior spend')
        super().__init__(path, cap)
        require(self.total <= self.cap, 'cumulative operational stop exceeded')

    @property
    def total(self):
        return self.prior + super().total


def collector(root, prior):
    """An isolated module namespace avoids mutating v0.1 collector globals."""
    spec = importlib.util.spec_from_file_location('_sos_v02_collector', Path(root).parent / 'sos_collect.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CollectionStop = CollectionStop
    module.TransportError = base.TransportError
    module.CostLedger = lambda path, cap='39': RollingLedger(path, cap, prior=prior)
    original_check = module.check_job
    def check_versioned_job(job, cfg):
        require(re.fullmatch(r'v02-[0-9a-f]{64}', job['id']) is not None, 'unsafe v0.2 job ID')
        # The original ID validator accepts hexadecimal IDs only. Validate our
        # fixed version prefix here, then reuse every original request check.
        original_check(dict(job, id=job['id'][4:]), cfg)
    module.check_job = check_versioned_job
    def checked(job, config):
        require(config['cost']['input_usd_per_million'] == 4 and config['cost']['output_usd_per_million'] == 20,
                'historical accounting rate drift')
        expected = allowance(job)
        require(job['reservation_usd'] == expected['usd'] and job['reservation_input_tokens'] == expected['input_tokens']
                and job['reservation_output_tokens'] == 448, 'reservation drift')
        return expected
    module.dispatch_reservation = checked
    module._collect = lambda *args, **kwargs: usage_limit.collect(module, *args, **kwargs)
    return module


def check_integrity(root=HERE):
    """Rebuild witnesses, truth and selection without writing v0.1 inputs."""
    from sos_design import candidate, select_primary, select_receipts
    root = Path(root)
    project = root.parent
    from sos_freeze import verify_freeze
    verify_freeze(project)
    data = read_json(project / 'imported/dataset.json')
    rebuilt = [candidate(item) for item in data['items']]
    require(rebuilt == read_json(project / 'config/all_certificates.json'), 'certificate/truth drift')
    design = read_json(project / 'config/design.json')
    require(select_primary(rebuilt) == design['primary_ids'], 'primary selection drift')
    require(select_receipts(rebuilt) == design['receipt_ids'], 'receipt selection drift')
    index = {item['id']: item for item in rebuilt}
    for episode in design['episodes']:
        original = index[episode['id']]
        for key in ('source', 'seed', 'breach'):
            require(episode[key] == original[key], 'episode assignment drift')
        for view, payload in episode['views'].items():
            require(payload == original['views'][view], 'payload drift')
            require(episode['certificates'][view] == original['certificates'][view], 'witness/mask drift')
    prior = reconcile(project / 'collection/cost.jsonl')
    plan = budget_plan(transform(project)['jobs'], prior)
    require(plan['new_reservations_usd'] == '33.520640'
            and plan['all_reservations_plus_prior_usd'] == '44.574032', 'budget census drift')
    return {'status': 'PASS', 'source_episodes': len(rebuilt), 'primary_episodes': len(design['primary_ids']),
            'receipt_episodes': len(design['receipt_ids']), 'truth_certificates_masks_and_selections': 'PASS',
            'v01_freezes_verified': True, 'prior_accounting': prior, 'reservation_census': plan,
            'new_model_calls': 0}


def frozen_inputs(root):
    """Only v0.2 code, config, agreements and build evidence are freeze inputs."""
    root = Path(root)
    paths = [root / 'PROTOCOL.md', root / 'RUN.md', root / 'PROJECT_STATE.md', root / 'sos_v02.py']
    for folder in ('config', 'tests', 'evidence'):
        paths.extend(p for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend(p for p in (root / 'build').glob('*.json') if not p.name.startswith('postfreeze-'))
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def verify(root=HERE, record=None):
    root = Path(root).resolve()
    deviation = record is None and (root / usage_deviation.FREEZE).exists()
    record = usage_deviation.verify(root) if deviation else (read_json(root / 'freeze.json') if record is None else record)
    require(record['version'] == VERSION and record['format_sentence'] == SENTENCE, 'freeze identity/format drift')
    if not deviation:
        files = frozen_inputs(root)
        require(files == record['files'] and sha(canonical(files).encode()) == record['content_sha256'], 'v0.2 freeze drift')
    inherited = read_json(root / 'evidence/inherited-inputs.json')['files']
    require(sha(canonical(inherited).encode()) == record['inherited_content_sha256'], 'inherited manifest drift')
    for name, expected in inherited.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe inherited path')
        require(digest(root.parent / name) == expected, 'v0.1 input drift: ' + name)
    requests = read_json(root / 'config/requests.json')
    require(requests == transform(root.parent), 'request transform/order drift')
    plan = read_json(root / 'config/budget.json')
    require(plan == budget_plan(requests['jobs'], reconcile(root.parent / 'collection/cost.jsonl')), 'cumulative baseline/budget drift')
    return record


def freeze(root=HERE):
    root = Path(root).resolve()
    require(not (root / 'freeze.json').exists(), 'freeze already exists; never replace')
    report = read_json(root / 'build/test-report.json')
    require(report['status'] == 'PASS' and report['tests_run'] > 0 and report['skipped'] == 0, 'offline tests required')
    require(report['adapter_sha256'] == digest(root / 'sos_v02.py'), 'test report predates adapter changes')
    require(report['test_sources'] == {p.name: digest(p) for p in (root / 'tests').glob('*.py')}, 'test sources changed after tests')
    for kind in ('dry-run', 'integrity'):
        reports = [read_json(p) for p in (root / 'build').glob('*' + kind + '*.json')]
        require(any(r.get('status') == 'PASS' and r.get('adapter_sha256') == digest(root / 'sos_v02.py') for r in reports),
                'current offline ' + kind + ' check required')
    files = frozen_inputs(root)
    inherited = read_json(root / 'evidence/inherited-inputs.json')['files']
    record = {'format': 1, 'version': VERSION, 'status': 'FROZEN_OFFLINE_NO_INFERENCE', 'frozen_utc': utcnow(),
              'format_sentence': SENTENCE, 'files': files, 'content_sha256': sha(canonical(files).encode()),
              'inherited_content_sha256': sha(canonical(inherited).encode()), 'primary_episodes': 240,
              'receipt_episodes': 120, 'scheduled_calls': 1868, 'new_calls': 0, 'new_usd': '0',
              'push_status': 'UNKNOWN', 'runtime_identity_status': 'UNKNOWN', 'project_acceptance': 'UNKNOWN',
              'authority': 'Historical v0.2 builder scope; Claude is the reviewer/operator.'}
    verify(root, record=record)
    save_new(root / 'freeze.json', record)
    verify(root)
    return {'freeze_sha256': digest(root / 'freeze.json'), 'files': len(files)}


def push_gate(root, record):
    push = read_json(root / 'collection/push.json')
    require(push['freeze_sha256'] == digest(root / 'freeze.json'), 'wrong push freeze')
    pushed = base._recovery_time(push['github_time'])
    require(base._recovery_time(record['frozen_utc']) <= pushed <= dt.datetime.now(dt.timezone.utc), 'push must follow freeze')
    require(re.fullmatch('[0-9a-f]{40}', push['commit']) is not None, 'invalid commit')
    require(bool(push['remote'].strip()) and bool(push['server_timestamp_source'].strip()), 'real push evidence required')
    for path in (root / 'collection/starts').glob('*.json'):
        start = read_json(path)
        require(start['freeze_sha256'] == push['freeze_sha256'] and pushed <= base._recovery_time(start['started']), 'push/start provenance drift')
    return push['freeze_sha256']


def output_boundary(root):
    collection = Path(root) / 'collection'
    require(not collection.is_symlink(), 'versioned collection cannot be a symlink')
    if collection.exists():
        require(not any(p.is_symlink() for p in collection.rglob('*')), 'collection contains a symlink')


def record_push(root, github_time, commit, remote, source):
    root = Path(root)
    record = verify(root)
    output_boundary(root)
    pushed = base._recovery_time(github_time)
    require(base._recovery_time(record['frozen_utc']) <= pushed <= dt.datetime.now(dt.timezone.utc), 'invalid push time')
    require(re.fullmatch('[0-9a-f]{40}', commit) is not None, 'expected 40-character pushed commit')
    require(bool(remote.strip()) and bool(source.strip()), 'real GitHub evidence required')
    require(not list((root / 'collection/starts').glob('*.json')), 'attestation must precede all starts')
    value = {'version': VERSION, 'freeze_sha256': digest(root / 'freeze.json'), 'github_time': github_time,
             'commit': commit, 'remote': remote, 'server_timestamp_source': source, 'attested_utc': utcnow()}
    save_new(root / 'collection/push.json', value)
    return value


def validate_history(root, jobs, frozen_hash, prior):
    """Reject orphans and drift before any transport/authentication setup."""
    collection = root / 'collection'
    schedule = {j['id']: j for j in jobs}
    ledger = RollingLedger(collection / 'cost.jsonl', prior=prior)
    analysis.read_calls(root, jobs)  # retain inherited identity/hash diagnostics
    usage_limit.history(collection, jobs, frozen_hash, ledger)
    return ledger


def run_collection(root=HERE, transport=None):
    root = Path(root).resolve()
    record = verify(root)
    output_boundary(root)
    frozen_hash = push_gate(root, record)
    if (root / usage_deviation.FREEZE).exists():
        usage_deviation.gate(root)
    config = read_json(root / 'config/collector.json')
    require(config['requests_file'] == 'config/requests.json', 'versioned request path required')
    jobs = read_json(root / config['requests_file'])['jobs']
    prior = reconcile(root.parent / 'collection/cost.jsonl')['accounted_usd']
    module = collector(root, prior)
    for job in jobs:
        require(job['model'] == 'claude' and job['version'] == VERSION, 'Claude-only version scope required')
        module.check_job(job, module.model_config(config, 'claude'))
        module.dispatch_reservation(job, config)
    collection = root / 'collection'
    collection.mkdir(exist_ok=True)
    lock = collection / 'collector.lock'
    save_new(lock, {'pid': os.getpid(), 'time': utcnow(), 'freeze_sha256': frozen_hash})
    try:
        validate_history(root, jobs, frozen_hash, prior)
        return module._collect(root, collection, jobs, config, {'claude'}, transport, frozen_hash)
    finally:
        lock.unlink()
        base.fsync_dir(collection)


def recover(root, reason):
    root = Path(root)
    verify(root)
    output_boundary(root)
    require(reason.strip(), 'concrete offline diagnosis required')
    require(not (root / 'collection/collector.lock').exists(), 'collector must be idle')
    jobs = read_json(root / 'config/requests.json')['jobs']
    prior = reconcile(root.parent / 'collection/cost.jsonl')['accounted_usd']
    ledger = RollingLedger(root / 'collection/cost.jsonl', prior=prior)
    attempts = usage_limit.history(root / 'collection', jobs, digest(root / 'freeze.json'), ledger)
    calls = {k: rs[-1][4] for k, rs in attempts.items() if rs and rs[-1][4] and not rs[-1][3]}
    paths = {k: rs[-1][1] for k, rs in attempts.items() if k in calls}
    tail = base._failure_tail(calls)
    require(len(tail) >= 3, 'no three-failure stop')
    path = root / 'collection/recoveries' / (base.uuid.uuid4().hex + '.json')
    save_new(path, {'reason': reason.strip(), 'diagnosed_at': utcnow(), 'last_failure_ids': [k for k, _ in tail],
                    'receipt_sha256': {k: digest(paths[k]) for k, _ in tail},
                    'receipt_paths': {k: str(paths[k].relative_to(root)) for k, _ in tail}})
    return str(path)


class FakeTransport:
    """Offline fixture; never instantiates DefaultTransport or a subprocess."""
    def __init__(self):
        self.ids = []

    def preflight(self, model, cfg):
        return {'transport': 'OFFLINE FAKE; no provider contacted', 'model': cfg['tag'], 'effort': cfg['effort']}

    def generate(self, job, cfg):
        self.ids.append(job['id'])
        return {'text': '{"violation":null}', 'raw_reply': '{"fixture":true}',
                'returned_model': cfg['tag'], 'returned_effort': None, 'requested_effort': cfg['effort'],
                'input_tokens': 100, 'output_tokens': 7,
                'usage': {'input_tokens': 100, 'output_tokens': 7}, 'stop_reason': 'fixture'}


def dry_run(root=HERE):
    root = Path(root)
    jobs = read_json(root / 'config/requests.json')['jobs']
    config = read_json(root / 'config/collector.json')
    prior = read_json(root / 'config/budget.json')['prior']['accounted_usd']
    with tempfile.TemporaryDirectory(prefix='sos-v02-offline-') as directory:
        fixture = Path(directory)
        (fixture / 'collection').mkdir()
        fake = FakeTransport()
        module = collector(root, prior)
        for job in jobs:
            module.check_job(job, module.model_config(config, 'claude'))
            module.dispatch_reservation(job, config)
        with patch('socket.socket', side_effect=AssertionError('offline sockets forbidden')), \
             patch('subprocess.run', side_effect=AssertionError('offline subprocess forbidden')), \
             patch('subprocess.check_output', side_effect=AssertionError('offline subprocess forbidden')):
            first = module._collect(fixture, fixture / 'collection', jobs, config, {'claude'}, fake, 'OFFLINE_FIXTURE')
            second = module._collect(fixture, fixture / 'collection', jobs, config, {'claude'}, fake, 'OFFLINE_FIXTURE')
        require(first['completed'] == 1868 and len(fake.ids) == 1868 and second['already_saved'] == 1868, 'offline dry-run/resume failed')
        return {'status': 'PASS', 'scope': 'isolated temporary fixture only; not scientific collection',
                'fixture_calls': len(fake.ids), 'resumed_new_calls': second['completed'],
                'cumulative_fixture_accounted_usd': first['accounted_usd'], 'real_model_calls': 0,
                'network_or_model_subprocesses': 0, 'versioned_ids': True}


def lenient_calls(calls):
    """Post hoc diagnostic: recover exactly one legal verdict object plus prose.

    Strict parser and integrity overrides are unchanged. Multiple objects, key
    duplicates, malformed objects and unrecognized values remain failures.
    """
    output = copy.deepcopy(calls)
    counts = {'strict_valid_raw_texts': 0, 'recovered_raw_texts': 0, 'unrecovered_raw_texts': 0}
    for call in output.values():
        raw = call.get('text')
        if analysis.parse_response(raw)['status'] != analysis.FAILURE:
            counts['strict_valid_raw_texts'] += 1
            continue
        candidates = re.findall(r'\{[^{}]*\}', raw or '')
        if (len(candidates) == 1 and raw.count('{') == raw.count('}') == 1
                and analysis.parse_response(candidates[0])['status'] != analysis.FAILURE):
            call['text'] = candidates[0]
            counts['recovered_raw_texts'] += 1
        else:
            counts['unrecovered_raw_texts'] += 1
    return output, counts


def score_version(design, jobs, calls, replicates=10000):
    rows = {i: analysis.primary_rows(design, jobs, calls, 'claude', i) for i in analysis.INSTRUCTIONS}
    return {'model': 'claude', 'primary': {i: analysis.replay_policy(r) for i, r in rows.items()},
            'diversity': {i: analysis.diversity(r) for i, r in rows.items()},
            'instruction_contrasts': analysis.paired_contrasts(rows['plain'], rows['explicit']),
            'bootstrap': analysis.primary_bootstrap(rows['plain'], rows['explicit'], replicates),
            'receipt_replication': {i: analysis.score_receipts(analysis.receipt_rows(design, jobs, calls, 'claude', i), replicates)
                                    for i in analysis.INSTRUCTIONS},
            'scheduled_calls': len(jobs), 'saved_calls': len(calls), 'missing_calls': len(jobs) - len(calls)}


def usage_accounting(root, jobs, calls, ledger):
    """Include all attempt holds; keep operational refusals outside outcomes."""
    def aggregate(field):
        values = [r.get(field) for r in calls.values()]
        known = sum((D(str(v)) for v in values if v is not None), D(0))
        return {'total': None if any(v is None for v in values) else float(known),
                'known_total': float(known), 'unavailable_calls': sum(v is None for v in values)}
    pending = ledger.reserved.keys() - ledger.settled
    starts = list((root / 'collection/starts').glob('*.json'))
    starts += list((root / 'collection/continuations').rglob('*.start.json'))
    result = {field: aggregate(field) for field in ('actual_usd', 'accounted_usd', 'seconds', 'input_tokens', 'output_tokens')}
    result['accounted_usd_receipts'] = result.pop('accounted_usd')
    result.update(attempted_starts=len(starts),
                  transport_failures=sum(r.get('status') == 'transport_failure' for r in calls.values()),
                  integrity_failures=sum(bool(r.get('integrity_failure')) for r in calls.values()),
                  outstanding_reserved_ids=sorted(pending),
                  outstanding_reservations_usd=str(sum((ledger.amounts[k] for k in pending), D(0))),
                  ledger_accounted_usd=str(ledger.total - ledger.prior),
                  note='All attempt reservations included; zero-usage refusals are operational events. Pending scheduled outcomes remain missing.')
    return result


def forecasts(scores):
    primary = scores['primary']
    result = {}
    ge = lambda value, threshold: value is not None and value + 1e-12 >= threshold
    le = lambda value, threshold: value is not None and value <= threshold + 1e-12
    for pid in ('V2-P1', 'V2-P2'):
        components = {}
        for i in analysis.INSTRUCTIONS:
            for w, cell in primary[i]['scores'].items():
                if pid == 'V2-P1':
                    components[i + '/' + w] = {v: ge(cell['views'][v]['validity'], .95) for v in analysis.VIEWS}
                else:
                    components[i + '/' + w] = {v: ge(cell['views'][v]['abstention'], .90) if v == 'T' else le(cell['views'][v]['abstention'], .10) for v in analysis.VIEWS}
        complete = all(primary[i]['complete'] for i in analysis.INSTRUCTIONS)
        result[pid] = {'status': 'PASS' if all(all(c.values()) for c in components.values()) else 'FAIL', 'components': components} if complete else {'status': 'UNKNOWN', 'reason': 'incomplete collection'}
    for pid, instruction in (('V2-P3', 'plain'), ('V2-P4', 'explicit')):
        cell = primary[instruction]
        result[pid] = {'status': ('PASS' if cell['pass'] else 'FAIL') if cell['complete'] else 'UNKNOWN',
                       'components': {w: c['components'] for w, c in cell['scores'].items()}}
    receipts = scores['receipt_replication']
    if all(receipts[i]['status'] == 'COMPLETE' for i in analysis.INSTRUCTIONS):
        p, e = [receipts[i]['scores']['trajectory']['W']['abstention'] for i in analysis.INSTRUCTIONS]
        checks = {'plain_W_le_0.10': le(p, .10), 'explicit_W_ge_0.70': ge(e, .70), 'difference_ge_0.60': ge(e - p, .60)}
        result['V2-P5'] = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'components': checks, 'explicit_minus_plain_W': e - p}
    else:
        result['V2-P5'] = {'status': 'UNKNOWN', 'reason': 'receipt collection incomplete'}
    return result


def run_analysis(root=HERE, output=None):
    root = Path(root).resolve()
    verify(root)
    design = read_json(root.parent / 'config/design.json')
    jobs = read_json(root / 'config/requests.json')['jobs']
    old_jobs = [j for j in read_json(root.parent / 'config/requests.json')['jobs'] if j['model'] == 'claude']
    old_calls = analysis.read_calls(root.parent, old_jobs)
    prior = reconcile(root.parent / 'collection/cost.jsonl')['accounted_usd']
    ledger = RollingLedger(root / 'collection/cost.jsonl', prior=prior)
    frozen_hash = digest(root / 'freeze.json') if (root / 'freeze.json').exists() else ''
    calls, operational_events = usage_limit.effective_calls(root, jobs, ledger, frozen_hash)
    diagnostic, counts = lenient_calls(old_calls)
    scores = score_version(design, jobs, calls)
    result = {'version': VERSION, 'status': 'COMPLETE' if len(calls) == 1868 else 'INCOMPLETE',
              'project_acceptance': 'UNKNOWN', 'acceptance_reason': 'Independent review, fresh-clone rebuild, integrity and delivery gates remain required. v0.1 failed validity; v0.2 cannot change that historical failure.',
              'v0.1_strict': score_version(design, old_jobs, old_calls), 'v0.2_strict': scores,
              'post_hoc_v0.1_lenient': {'role': 'post hoc diagnostic; no registered-pass label', 'counts': counts,
                  'method': 'Exactly one legal verdict object plus prose; original scheduled denominators, weights and integrity flags preserved.',
                  'endpoints': score_version(design, old_jobs, diagnostic)},
              'forecasts': forecasts(scores), 'v0.2_accounting': usage_accounting(root, jobs, calls, ledger),
              'operational_events': {'usage_limit_refusals': len(operational_events),
                   'events': operational_events,
                   're_dispositioned_transport_failures': sum(e['recorded_from_saved_status'] == 'transport_failure' for e in operational_events),
                   'model_behavior_or_technical_failures': False},
              'v0.1_accounting': reconcile(root.parent / 'collection/cost.jsonl'),
              'retrospective_census_reference': '../analysis/results.json#/retrospective',
              'uncertainty': {'bootstrap_replicates': 10000, 'seed': 20261112, 'wilson': 'nominal descriptive only; dependent benchmark',
                   'small_support_and_null_resamples': 'Unchanged sos_stats.bootstrap_endpoints policy'},
              'limitations': ['Post hoc follow-up selected after v0.1 exposure; familiar tasks, no new holdout.',
                   'Receipt withholding is a post hoc twist; outcomes are consistent with evidence sufficiency, not proof of an internal mechanism.',
                   'Claude-only rerun; no new local outcomes or cross-family claim. No causal removal claim across separate stochastic runs.',
                   'One attempt only; no v0.3. Failed forecasts are retained. Negative scientific results can be accepted; incomplete runs cannot.']}
    # A diagnostic table never receives a registered pass label.
    def strip_pass(value):
        if isinstance(value, dict):
            return {k: strip_pass(v) for k, v in value.items() if k not in ('pass', 'checks', 'components')}
        if isinstance(value, list):
            return [strip_pass(v) for v in value]
        return value
    result['post_hoc_v0.1_lenient']['endpoints'] = strip_pass(result['post_hoc_v0.1_lenient']['endpoints'])
    ledger = RollingLedger(root / 'collection/cost.jsonl', prior=result['v0.1_accounting']['accounted_usd'])
    result['cumulative_accounted_usd'] = str(ledger.total)
    target = root / 'analysis' if output is None else (root / output).resolve()
    require(target.is_relative_to(root) and target != root, 'analysis output must be under v0.2')
    target.mkdir(parents=True, exist_ok=False)
    save_new(target / 'results.json', result)
    lines = ['# Signal or Silence v0.2', '', 'Claude only; plain-plus-format is primary. Project acceptance: UNKNOWN.', '',
             '| Version / interpretation | Instruction | Weighting | Joint pass | F validity | T validity | R validity |',
             '|---|---|---|---|---|---|---|']
    for label, version in [('v0.1 strict', result['v0.1_strict']), ('v0.2 strict', scores),
                           ('v0.1 lenient (post hoc)', result['post_hoc_v0.1_lenient']['endpoints'])]:
        for i, cell in version['primary'].items():
            for w, score in cell['scores'].items():
                decision = score.get('pass', 'diagnostic only') if cell['complete'] else 'UNKNOWN (incomplete)'
                values = ' | '.join(f"{score['views'][v]['validity']:.4f}" for v in analysis.VIEWS)
                lines.append(f'| {label} | {i} | {w} | {decision} | {values} |')
    lines += ['', f"Operational usage-limit refusals: {len(operational_events)}; historical transport failures re-dispositioned: {result['operational_events']['re_dispositioned_transport_failures']}. These are definite non-starts, excluded from model behavior and technical-failure counts. Pending jobs remain missing in scheduled denominators.", '', 'v0.1 failed its registered validity criterion. All endpoints, denominators, component failures, receipt results and forecasts are in results.json.', '',
              *result['limitations'], '', 'Receipt-withholding results are consistent with evidence sufficiency on this fixed synthetic benchmark.']
    with (target / 'RESULTS.md').open('x') as stream:
        stream.write('\n'.join(lines) + '\n')
    return {'output': str(target), 'status': result['status'], 'project_acceptance': 'UNKNOWN'}


def run_tests(root=HERE):
    stream = io.StringIO()
    with patch('socket.socket', side_effect=AssertionError('offline sockets forbidden')):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover(str(Path(root) / 'tests')))
    print(stream.getvalue())
    report = {'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'tested_utc': utcnow(),
              'adapter_sha256': digest(Path(__file__)), 'deviation_sources': usage_deviation.source_hashes(Path(root)),
              'test_sources': {p.name: digest(p) for p in (Path(root) / 'tests').glob('*.py')}}
    name = 'postfreeze-test-' + dt.datetime.now().strftime('%H%M%S%f') + '.json' if (Path(root) / 'freeze.json').exists() else 'test-report.json'
    save_new(Path(root) / 'build' / name, report)
    return report


def save_check(root, name, value):
    """Rechecks get a new report; the registered build evidence is immutable."""
    root = Path(root)
    value.update(checked_utc=utcnow(), adapter_sha256=digest(Path(__file__)),
                 deviation_sources=usage_deviation.source_hashes(HERE))
    if (root / 'freeze.json').exists() or (root / 'build' / name).exists():
        prefix = 'postfreeze-' if (root / 'freeze.json').exists() else 'recheck-'
        name = prefix + Path(name).stem + '-' + dt.datetime.now().strftime('%H%M%S%f') + '.json'
    save_new(root / 'build' / name, value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'test', 'integrity', 'dry-run', 'freeze', 'verify', 'collect', 'freeze-usage-limit', 'clear-usage-limit'):
        sub.add_parser(name)
    att = sub.add_parser('attest-usage-limit'); att.add_argument('--freeze-sha256', required=True)
    a = sub.add_parser('analyze'); a.add_argument('--output', type=Path)
    p = sub.add_parser('record-push')
    for field in ('github-time', 'commit', 'remote', 'source'):
        p.add_argument('--' + field, required=True)
    r = sub.add_parser('recover'); r.add_argument('--reason', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'freeze-usage-limit':
            output = usage_deviation.freeze(HERE, sys.modules[__name__])
        elif args.command == 'clear-usage-limit':
            output = usage_deviation.clear(HERE, sys.modules[__name__])
        elif args.command == 'attest-usage-limit':
            output = usage_deviation.attest(HERE, args.freeze_sha256)
        elif args.command == 'record-push':
            output = record_push(HERE, args.github_time, args.commit, args.remote, args.source)
        elif args.command == 'recover':
            output = recover(HERE, args.reason)
        elif args.command == 'analyze':
            output = run_analysis(HERE, args.output)
        elif args.command == 'dry-run':
            output = dry_run(HERE)
            save_check(HERE, 'dry-run.json', output)
        elif args.command == 'integrity':
            output = check_integrity(HERE)
            save_check(HERE, 'integrity.json', output)
        else:
            output = {'prepare': prepare, 'test': run_tests, 'freeze': freeze, 'verify': verify, 'collect': run_collection}[args.command](HERE)
        if args.command == 'verify':
            output = {k: v for k, v in output.items() if k != 'files'}
        print(json.dumps(output, indent=2))
        return int(output.get('status') == 'FAIL')
    except (CollectionStop, OSError, ValueError, KeyError) as exc:
        parser.exit(1, 'STOP: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
