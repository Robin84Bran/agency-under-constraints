"""Generated boundary properties for every decoder branch, independent of action()."""
import copy
import unittest

from bob_core import SCHEMAS,action,report,canonical,strict_load
from test_v02 import matches


def endpoint(spec, maximum):
    if 'enum' in spec:
        return sorted(spec['enum'],key=canonical)[-1 if maximum else 0]
    kind=spec['type']
    if kind=='null':return None
    if kind=='boolean':return maximum
    if kind=='integer':return spec['maximum' if maximum else 'minimum']
    if kind=='string':return ('z' if maximum else '0')*spec['maxLength' if maximum else 'minLength']
    raise AssertionError('unhandled schema type: '+str(kind))


class SchemaBranchProperties(unittest.TestCase):
    def test_generated_minimal_maximal_instances_and_all_missing_keys(self):
        for phase,schema in SCHEMAS.items():
            for i,branch in enumerate(schema.get('anyOf',[schema])):
                with self.subTest(phase=phase,branch=i):
                    self.assertEqual(branch['type'],'object')
                    self.assertEqual(set(branch['required']),set(branch['properties']))
                    self.assertIs(branch['additionalProperties'],False)
                for maximum in (False,True):
                    value=strict_load(canonical({k:endpoint(s,maximum) for k,s in branch['properties'].items()}))
                    with self.subTest(phase=phase,branch=i,maximum=maximum):
                        self.assertTrue(matches(value,branch))
                        self.assertTrue(matches(value,schema))
                        # Registry permits describe; world permissions remain independent.
                        self.assertEqual(action(value,'registry') if phase=='action' else report(value),value)
                        for key in value:
                            missing=copy.deepcopy(value);del missing[key]
                            self.assertFalse(matches(missing,branch),(phase,i,key))
                            self.assertFalse(matches(missing,schema),(phase,i,key))
                            wrong=copy.deepcopy(value);wrong[key]=[]
                            self.assertFalse(matches(wrong,branch),(phase,i,key))
                            self.assertFalse(matches(wrong,schema),(phase,i,key))
                        extra=dict(value,unexpected=None)
                        self.assertFalse(matches(extra,branch))
                        self.assertFalse(matches(extra,schema))

    def test_saved_partial_object_is_rejected_by_every_decoder_branch(self):
        partial={'op':'lookup','target':None}
        self.assertFalse(matches(partial,SCHEMAS['action']))
        for branch in SCHEMAS['action']['anyOf']:
            self.assertFalse(matches(partial,branch))
        # Reproduce the old branch grammar bug even though the old root rejected it.
        old=copy.deepcopy(SCHEMAS['action']['anyOf'][0])
        del old['required'];del old['additionalProperties']
        self.assertTrue(matches(partial,old))
