import ast
from pathlib import Path
import unittest
from ps_core import ROOT, sha
from ps_io import read


class A1AuditTests(unittest.TestCase):
    def test_inventory_covers_every_explicit_raise_and_fatal_control(self):
        current=[]
        for p in sorted(ROOT.glob('ps*.py')):
            for n in ast.walk(ast.parse(p.read_text())):
                if isinstance(n,ast.Raise): current.append((p.name,n.lineno,ast.unparse(n.exc) if n.exc else 'reraise'))
                if p.name=='ps_collect.py' and isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fatal' for t in n.targets) and not (isinstance(n.value,ast.Constant) and n.value.value is False):
                    current.append((p.name,n.lineno,'fatal control: '+p.read_text().splitlines()[n.lineno-1].strip()))
        report=read(ROOT/'revisions/a1/audit-paths.json')
        self.assertEqual(sorted(current),sorted((r['file'],r['line'],r['expression']) for r in report['final']))
        self.assertEqual(report['counts']['audited_original_sites'],135)
        self.assertEqual((report['counts']['fixed'],report['counts']['already_right']),(9,126))
        self.assertTrue(all(r['class'] and r['reason'] for r in report['original']+report['final']))

    def test_scientific_functions_unchanged(self):
        def functions(text): return {n.name:ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        before=functions((ROOT/'revisions/a1/original/ps_analysis.py').read_text());after=functions((ROOT/'ps_analysis.py').read_text())
        for name in set(before)-{'score','audit_accounting'}:
            with self.subTest(name=name): self.assertEqual(ast.dump(ast.parse(before[name])),ast.dump(ast.parse(after[name])))
        score=after['score'].replace("env,_=provider_envelope(raw['stdout'],ep['actor'])", "env=__import__('ps_core').strict_load(raw['stdout'])")
        self.assertEqual(score,before['score'])
        self.assertEqual(before['audit_accounting'].split('    contract_path=')[0],after['audit_accounting'].split('    contract_path=')[0])
        self.assertEqual(before['audit_accounting'].split('    active={}')[1],after['audit_accounting'].split('    active={}')[1])
        original=read(ROOT/'freeze.json')['files']
        for name in ('ps_core.py','ps_baselines.py','config/prompts.json','config/design.json','config/act-schema.json','config/write-schema.json','config/sizing.json','config/episodes.json','config/worlds.json','PROTOCOL.md'):
            with self.subTest(name=name): self.assertEqual(sha((ROOT/name).read_bytes()),original[name])
