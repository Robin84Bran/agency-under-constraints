"""D3 harness-only lineage, immutable evidence and audit seal. No model calls."""
from pathlib import Path, PurePosixPath

from bob_core import canonical,sha
from bob_collect import Stop,read,save,now

CHANGED={'bob.py','bob_freeze.py','bob_collect.py','bob_audit.py','bob_d2.py',
         'DEVIATIONS.md','RUN.md','tests/test_collect.py','tests/test_d1.py','tests/test_d2.py'}
ADDED={'bob_d3.py','bob_validation.py','tests/test_d3.py','RUN-d3.md','PROJECT_STATE-d3.md',
       'deviations/d3/preserved.json','deviations/d3/real-claude-envelope.json',
       'deviations/d3/raise-audit.json'}
PRESERVED='deviations/d3/preserved.json'
LEDGERS={'collection/cost.jsonl','collection/local-time.jsonl','collection/frontier-time.jsonl'}


def protected_path(root,name):
    rel=PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts:
        raise Stop('unsafe preserved path')
    path=Path(root)/name
    if any((Path(root)/Path(*rel.parts[:i])).is_symlink() for i in range(1,len(rel.parts)+1)):
        raise Stop('symlink in preserved evidence')
    return path


def preserved(root):
    root=Path(root)
    data=read(root/PRESERVED)
    for name,digest in data['parents'].items():
        path=protected_path(root,name)
        if sha(path.read_bytes())!=digest:
            raise Stop('D3 parent freeze changed: '+name)
    for name,item in data['collection'].items():
        path=protected_path(root,name)
        raw=path.read_bytes()
        if item['mode']=='prefix' and name in LEDGERS:
            if len(raw)<item['bytes'] or not raw.endswith(b'\n') or not raw[:item['bytes']].endswith(b'\n'):
                raise Stop('shortened/torn preserved ledger: '+name)
            raw=raw[:item['bytes']]
        elif item['mode']!='exact' or len(raw)!=item['bytes']:
            raise Stop('invalid preservation descriptor/length: '+name)
        if sha(raw)!=item['sha256']:
            raise Stop('D3 existing evidence changed: '+name)
    # Frozen terminal ids/call ids cannot gain evidence after the amendment.
    old_episodes={Path(n).stem for n in data['collection'] if n.startswith('collection/episodes/')}
    old_calls={Path(n).stem for n in data['collection'] if n.startswith('collection/calls/')}
    for folder in ('episodes','episode-starts','calls','starts','requests','raw'):
        for p in (root/'collection'/folder).glob('*'):
            rel=p.relative_to(root).as_posix()
            ids=old_episodes if folder in ('episodes','episode-starts') else old_calls
            if p.stem in ids and rel not in data['collection']:
                raise Stop('new evidence on historical terminal/call')
    return data


def scope(root,files):
    root=Path(root)
    data=preserved(root)
    parent=read(root/'freeze-d2.json')
    if parent.get('deviation')!='D2' or parent['parent_freeze_sha256']!=data['parents']['freeze-d1.json']:
        raise Stop('D3 parent lineage mismatch')
    extras=ADDED|{'deviations/d3/original/'+n for n in CHANGED}
    if set(files)!=set(parent['files'])|extras:
        raise Stop('D3 inventory outside declared harness amendment')
    for name,digest in parent['files'].items():
        target='deviations/d3/original/'+name if name in CHANGED else name
        if files.get(target)!=digest:
            raise Stop('D3 scientific/original bytes changed: '+name)
    from bob_d2 import _unaffected,identity,validate_disposition
    # Freeze science, requests, accounting and timer mechanics in the collector.
    allowed={'LocalAdapter.generate','frontier_gate','payload','run_episode','collect'}
    def normalized(raw):
        import ast
        tree=ast.parse(raw)
        # Only new imports and local envelope guard are allowed additions here.
        tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='bob_validation') and
                   not (isinstance(n,ast.Import) and any(a.name=='urllib.error' for a in n.names)) and
                   not (isinstance(n,ast.FunctionDef) and n.name=='local_contract')]
        return _unaffected(ast.unparse(tree),allowed)
    if normalized((root/'deviations/d3/original/bob_collect.py').read_bytes())!=normalized((root/'bob_collect.py').read_bytes()):
        raise Stop('D3 changed unrelated collector accounting/request mechanism')
    if not (root/'DEVIATIONS.md').read_bytes().startswith((root/'deviations/d3/original/DEVIATIONS.md').read_bytes()):
        raise Stop('deviation history must remain append-only')
    identity(root);validate_disposition(root)
    return parent,data


def verify_d3(root,record):
    root=Path(root)
    from bob_freeze import TRANSPORT_POLICY
    parent,data=scope(root,record['files'])
    if (record.get('deviation')!='D3' or record.get('parents')!=data['parents'] or
        record.get('parent_freeze_sha256')!=data['parents']['freeze-d2.json'] or
        record.get('preserved_sha256')!=sha((root/PRESERVED).read_bytes()) or
        record.get('transport_policy')!=TRANSPORT_POLICY):
        raise Stop('invalid D3 binding/policy')
    for key in ('format','local_episodes','frontier_episodes','maximum_generations','new_model_calls','new_usd',
                'frontier_reservation_micro_usd','protected_reserve_micro_usd'):
        if record.get(key)!=parent[key]:
            raise Stop('D3 changed scientific/budget metadata: '+key)
    if (root/'freeze-a1.json').exists() or (root/'freeze-a1.json').is_symlink():
        verify_a1(root,record)
    return record


def freeze_d3(root):
    from bob_freeze import inventory,verify,push_gate
    from bob_audit import audit_episode,reconcile_ledger
    root=Path(root)
    if (root/'freeze-d3.json').exists() or (root/'freeze-d3.json').is_symlink():
        raise Stop('D3 freeze exists; never overwrite')
    files=inventory(root)
    parent,data=scope(root,files)
    check_historical_pushes(root,data)
    plan=read(root/'config/order.json')
    records={p.stem:read(p) for p in (root/'collection/episodes').glob('*.json')}
    expected={e['id'] for e in plan if e['model']!='claude'}
    if set(records)!=expected or any(read(p)['episode']['model']=='claude' for p in (root/'collection/episode-starts').glob('*.json')):
        raise Stop('D3 requires exactly complete local cohort and no Claude starts')
    for ep in plan:
        if ep['id'] in records:
            audit_episode(root,ep,records[ep['id']],data['parents']['freeze.json'])
    report=read(root/'build/test-report-d3.json')
    if report.get('status')!='PASS' or report.get('tests',0)<1 or report.get('source_sha256')!=sha(canonical(files).encode()):
        raise Stop('passing tests must bind exact D3 source')
    record=dict(parent,files=files,content_sha256=sha(canonical(files).encode()),deviation='D3',
                parent_freeze_sha256=data['parents']['freeze-d2.json'],parents=data['parents'],
                preserved_sha256=sha((root/PRESERVED).read_bytes()),frozen_utc=now(),
                tests=report['tests'],test_counts=dict(python=report['python_tests'],toy=report['toy_tests']),
                unresolved=['fresh D3 activity API push attestation','live first Claude call compatibility/actual usage',
                            'rates and hard hidden-token bounds remain UNKNOWN'])
    save(root/'freeze-d3.json',record)
    # The D2 resume event already validates the active D3 seal when replayed.
    verify(root)
    if reconcile_ledger(root,records)['status']!='PASS':
        raise Stop('D3 requires fully reconciled historical accounting')
    return dict(freeze_file='freeze-d3.json',freeze_sha256=sha((root/'freeze-d3.json').read_bytes()),tests=report['tests'])


def freeze_a1(root):
    from bob_freeze import verify,inventory
    root=Path(root)
    record=verify(root)
    if record.get('deviation')!='D3':
        raise Stop('A1 requires D3')
    report=read(root/'build/test-report-d3.json')
    if report.get('status')!='PASS' or report.get('source_sha256')!=sha(canonical(inventory(root)).encode()):
        raise Stop('A1 requires source-bound passing audit tests')
    seal=dict(format=1,audit='A1',deviation='D3',frozen_utc=now(),
              parent_freeze_sha256=sha((root/'freeze-d3.json').read_bytes()),parents=record['parents'],
              content_sha256=record['content_sha256'],tests=report,
              raise_audit_sha256=sha((root/'deviations/d3/raise-audit.json').read_bytes()))
    save(root/'freeze-a1.json',seal)
    verify_a1(root,record)
    return dict(freeze_file='freeze-a1.json',freeze_sha256=sha((root/'freeze-a1.json').read_bytes()))


def verify_a1(root,record):
    root=Path(root)
    path=root/'freeze-a1.json'
    if path.is_symlink():
        raise Stop('symlink A1 seal')
    seal=read(path)
    if (seal.get('audit')!='A1' or seal.get('parent_freeze_sha256')!=sha((root/'freeze-d3.json').read_bytes()) or
        seal.get('parents')!=record['parents'] or seal.get('content_sha256')!=record['content_sha256'] or
        seal.get('raise_audit_sha256')!=sha((root/'deviations/d3/raise-audit.json').read_bytes()) or
        seal.get('tests',{}).get('status')!='PASS' or seal['tests'].get('source_sha256')!=record['content_sha256']):
        raise Stop('A1 audit seal mismatch')
    return seal


def check_historical_pushes(root,data):
    from bob_d2 import check_d2_push
    return check_d2_push(Path(root),read(Path(root)/'freeze-d2.json'),read(Path(root)/'collection/push-d2.json'),
                         historical_starts=set(data['collection']))


def check_d3_push(root,freeze,push):
    from bob_freeze import push_record,parsed_time,REPOSITORY
    root=Path(root)
    data=preserved(root)
    verify_a1(root,freeze)
    check_historical_pushes(root,data)
    if (push.get('freeze_file')!='freeze-d3.json' or push.get('freeze_sha256')!=sha((root/'freeze-d3.json').read_bytes()) or
        push.get('parents')!=data['parents'] or push.get('audit_freeze_sha256')!=sha((root/'freeze-a1.json').read_bytes()) or
        push.get('repo')!=REPOSITORY or push.get('evidence_file')!='collection/push-d3-event.json'):
        raise Stop('push does not bind D3/A1 and all parents')
    path=protected_path(root,'collection/push-d3-event.json')
    raw=path.read_bytes()
    if sha(raw)!=push.get('evidence_sha256'):
        raise Stop('D3 activity evidence changed')
    supplied=push_record(read(path),push.get('commit'))
    if supplied['source_api']!='/repos/'+REPOSITORY+'/activity' or any(push.get(k)!=v for k,v in supplied.items()):
        raise Stop('D3 requires matching raw activity API evidence')
    pushed=parsed_time(push['github_time'])
    if pushed<max(parsed_time(freeze['frozen_utc']),parsed_time(read(root/'freeze-a1.json')['frozen_utc'])):
        raise Stop('push must follow both D3 and A1 freezes')
    for folder in ('starts','episode-starts'):
        for p in (root/'collection'/folder).glob('*.json'):
            if p.relative_to(root).as_posix() in data['collection']:
                continue
            value=read(p)
            if (value.get('deviation')!='D3' or value.get('amendment_freeze_sha256')!=push['freeze_sha256'] or
                parsed_time(value['started'])<max(pushed,parsed_time(push['recorded_utc']))):
                raise Stop('D3 push/attestation must precede and bind every new start')
    return push


AUDIT_FILES=('bob_collect.py','bob_core.py','bob_audit.py','bob_freeze.py','bob_d2.py','bob_analysis.py',
             'bob_validation.py','bob_d3.py')


def audit_sites(root,before=False):
    """Enumerate every explicit raise plus non-raise failure-routing decisions."""
    import ast
    root=Path(root)
    rows=[]
    fixed={
        ('bob_collect.py','nonnegative_int','missing/invalid '),
        ('bob_collect.py','payload','Claude internal turn count mismatch/UNKNOWN'),
        ('bob_collect.py','payload','local identity/incomplete envelope'),
        ('bob_collect.py','payload','local output truncation or unknown stop reason'),
        ('bob_collect.py','run_episode','Claude failed/unfinished envelope'),
        ('bob_collect.py','run_episode','missing object structured_output; no fallback'),
        ('bob_audit.py','audit_episode','Claude identity/turn/stop mismatch'),
    }
    for name in AUDIT_FILES:
        if before and name in ('bob_validation.py','bob_d3.py'):
            continue
        path=root/'deviations/d3/original'/name if before and name in CHANGED else root/name
        tree=ast.parse(path.read_bytes())
        class Visitor(ast.NodeVisitor):
            def __init__(self):self.stack=[]
            def visit_FunctionDef(self,node):
                self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
            visit_AsyncFunctionDef=visit_FunctionDef
            def visit_ClassDef(self,node):
                self.stack.append(node.name);self.generic_visit(node);self.stack.pop()
            def record(self,node,kind,expr):
                function='.'.join(self.stack)
                text=ast.unparse(expr) if expr is not None else 're-raise'
                literals=[v.value for v in ast.walk(expr) if isinstance(v,ast.Constant) and isinstance(v.value,str)] if expr else []
                corrected=before and ((name,function,next(iter(literals),'')) in fixed or
                                      kind in ('fatal route','transport route','outer parser route'))
                category='Fatal harness/integrity/identity/accounting'
                reason='Reject inconsistent harness, configuration, saved evidence, provenance or resource state.'
                if name=='bob_core.py' and function.split('.')[0] in ('action','report','strict_load'):
                    category='Model content in payload / Fatal in evidence'
                    reason='Strict model validation ends one episode; the same failure in saved/configured data is fatal.'
                if name=='bob_validation.py' and (function.startswith('envelope') or function=='decode'):
                    category='Contextual parser/transport'
                    reason='Bad designated payload is model content; unreadable local envelope is episode transport; unverifiable Claude metadata/accounting is fatal.'
                if 'ModelFailure(' in text:
                    category='Episode model content';reason='Frozen technical failure; no further call in this episode; cohort continues.'
                if 'EpisodeTransport(' in text:
                    category='Episode local transport / durable pause at three';reason='No resend; retain null usage where unavailable; count once toward persistent streak.'
                if function=='nonnegative_int':
                    category='Fatal paid accounting / local transport via guard'
                    reason='Unknown paid counts retain holds and stop. Local missing counts are intercepted as episode transport.'
                if before and (name,function,next(iter(literals),'')) in fixed:
                    category='Episode content/transport or permitted reply; formerly fatal'
                    reason='Split model/local-transport failures from fatal metadata, or accept valid two-turn schema-tool replies.'
                if kind=='fatal route':
                    category='Failure routing';reason='Only typed model/local-transport failures are nonfatal; unknown paid accounting and unexpected exceptions are fatal.'
                if kind=='transport route':
                    category='Failure streak routing';reason='Count typed local transport failures, not model content failures, once per episode.'
                if kind=='outer parser route':
                    category='Payload/metadata parser boundary';reason='Preserve valid usage and identity when structured_output alone has duplicate/nonfinite content.'
                if kind=='integrity return':
                    category='Fatal identity signal';reason='Preserve generation bytes while reporting post-generation runtime/context uncertainty.'
                if kind=='content return':
                    category='Episode model content signal';reason='Recognized schema rejection or length stop is consumed as ModelFailure after fatal metadata/accounting guards.'
                if kind=='durable budget route':
                    category='Fatal accounting';reason='Full settlement/exposure is retained; block dispatch on a measured cap or reservation overrun.'
                rows.append(dict(file=name,line=node.lineno,function=function,kind=kind,expression=text,
                                 classification=category,reason=reason,
                                 disposition=('fixed' if corrected else 'already right') if before else 'current'))
            def visit_Raise(self,node):
                self.record(node,'raise',node.exc);self.generic_visit(node)
            def visit_Assign(self,node):
                if self.stack==['run_episode'] and not isinstance(node.value,ast.Constant):
                    targets={t.id for t in node.targets if isinstance(t,ast.Name)}
                    for variable,kind in (('fatal','fatal route'),('transport_failure','transport route')):
                        if variable in targets:self.record(node,kind,node.value)
                    if before and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='strict_load':
                        if any(isinstance(t,ast.Name) and t.id=='envelope' for t in node.targets):
                            self.record(node,'outer parser route',node.value)
                self.generic_visit(node)
            def visit_AugAssign(self,node):
                if isinstance(node.target,ast.Attribute) and node.target.attr=='blocked':
                    self.record(node,'durable budget route',node.value)
                self.generic_visit(node)
            def visit_Return(self,node):
                if self.stack==['LocalAdapter','generate'] and node.value is not None and 'integrity_error' in ast.unparse(node.value):
                    self.record(node,'integrity return',node.value)
                if self.stack==['claude_contract'] and node.value is not None and 'Claude ' in ast.unparse(node.value):
                    self.record(node,'content return',node.value)
                self.generic_visit(node)
        Visitor().visit(tree)
    return sorted(rows,key=lambda x:(x['file'],x['line'],x['kind']))
