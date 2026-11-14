"""Provider projection proof plus finite cross-field and validator agreement."""
import copy
import itertools
import unittest

from bob_claude_schema import CLAUDE_SCHEMAS
from bob_collect import claude_command
from bob_core import SCHEMAS,action,report,canonical,reserve,P
from test_v02 import matches


def projection(leaves):
    """Exact union of these frozen scalar domains, without cross-field constraints."""
    nullable=any(s.get('type')=='null' for s in leaves)
    leaves=[s for s in leaves if s.get('type')!='null']
    if all('enum' in s for s in leaves):
        values={canonical(v):v for s in leaves for v in s['enum']}
        values=list(values.values())
        kind={str:'string',int:'integer',bool:'boolean'}[type(values[0])]
        return dict(type=[kind,'null'] if nullable else kind,enum=values+([None] if nullable else []))
    # All non-null branches share the exact same bounds/pattern/type.
    assert all(s==leaves[0] for s in leaves)
    spec=copy.deepcopy(leaves[0])
    if nullable:spec['type']=[spec['type'],'null']
    return spec


class ClaudeSchemaR3Tests(unittest.TestCase):
    def test_exact_scalar_projection_proves_universal_local_subset(self):
        # Local branches are products of scalar domains with identical key sets.
        # The provider is the product of their exact fieldwise unions; therefore
        # every local branch, for ALL its values, is included in the provider.
        for phase,local in SCHEMAS.items():
            provider=CLAUDE_SCHEMAS[phase]
            self.assertEqual(provider['type'],'object')
            self.assertFalse({'anyOf','oneOf','allOf'} & provider.keys())
            self.assertIs(provider['additionalProperties'],False)
            branches=local['anyOf']
            keys=set(provider['properties'])
            self.assertEqual(set(provider['required']),keys)
            for b in branches:
                self.assertEqual(b['type'],'object')
                self.assertEqual(set(b['properties']),keys)
                self.assertEqual(set(b['required']),keys)
                self.assertIs(b['additionalProperties'],False)
            for key in keys:
                projected=projection([b['properties'][key] for b in branches])
                actual=copy.deepcopy(provider['properties'][key])
                if 'enum' in actual:
                    self.assertEqual({canonical(v) for v in actual.pop('enum')},{canonical(v) for v in projected.pop('enum')})
                self.assertEqual(actual,projected,(phase,key))

    def test_finite_action_space_local_provider_and_strict_branch_legality(self):
        domains={
            'op':['lookup','convert','submit','describe','finish','unknown',None],
            'item':[None,'a','z'*12,'item-000000','', 'UPPER','a'*13,7],
            'grams':[None,0,1250,999999999,-1,1000000000,True,1.5],
            'mass_g':[None,0,999999999,-1,True],
            'revision':[None,1,0,2,True],
            'target':[None,'lookup','convert','submit','finish',1],
        }
        counts=dict(local=0,provider=0,cross_field_only=0)
        for row in itertools.product(*domains.values()):
            value=dict(zip(domains,row))
            local=matches(value,SCHEMAS['action'])
            provider=matches(value,CLAUDE_SCHEMAS['action'])
            self.assertFalse(local and not provider,value)
            used={k for k in domains if k!='op' and value[k] is not None}
            op=value['op']
            shape=(op=='lookup' and used=={'item'} or
                   op=='convert' and used in ({'grams'},{'mass_g'}) or
                   op=='submit' and used in ({'grams'},{'grams','revision'}) or
                   op=='describe' and used=={'target'} or op=='finish' and not used)
            self.assertEqual(local,provider and bool(shape),value)
            for arm in ('registry','stale'):
                try:action(value,arm);accepted=True
                except ValueError:accepted=False
                self.assertEqual(accepted,local and (arm=='registry' or op!='describe'),(arm,value))
            counts['local']+=local;counts['provider']+=provider
            counts['cross_field_only']+=provider and not local
        self.assertGreater(counts['local'],0)
        self.assertGreater(counts['cross_field_only'],0)

    def test_report_domains_omissions_extras_and_claude_argv(self):
        for value in (None,True,False,0,1,'true',[],{}):
            obj={'submitted':value}
            local=matches(obj,SCHEMAS['report'])
            self.assertEqual(local,matches(obj,CLAUDE_SCHEMAS['report']))
            try:report(obj);accepted=True
            except ValueError:accepted=False
            self.assertEqual(local,accepted)
        for phase,schema in CLAUDE_SCHEMAS.items():
            value=({'op':'finish','item':None,'grams':None,'mass_g':None,'revision':None,'target':None}
                   if phase=='action' else {'submitted':None})
            for key in value:
                omitted=dict(value);del omitted[key]
                self.assertFalse(matches(omitted,schema))
                wrong=dict(value);wrong[key]=[]
                self.assertFalse(matches(wrong,schema))
            self.assertFalse(matches(dict(value,extra=None),schema))
            argv=claude_command('FAKE_NOT_EXECUTED',phase,30000)
            self.assertEqual(argv[argv.index('--json-schema')+1],canonical(schema))
            # Keep frozen r2 reservations: the shorter Claude schemas fit them.
            self.assertLessEqual(len(canonical(schema)),len(canonical(SCHEMAS[phase])))
            self.assertGreater(reserve('fixture',phase)['input_tokens'],0)
