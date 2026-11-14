"""r5 provider-only schema projection; strict local contracts remain authoritative."""
from rg_core import schema_for


def claude_schema(phase, toolkit='plain'):
    if phase != 'action':
        return schema_for(phase, toolkit)
    if toolkit not in ('plain', 'keyed', 'check'):
        raise ValueError('toolkit')
    key = {'type':'null'}
    if toolkit == 'keyed':
        key = {'type':['string','null'], 'minLength':1, 'maxLength':16,
               'pattern':'^[A-Za-z0-9_-]+$'}
    return {'type':'object', 'additionalProperties':False,
            'required':['op','job','key'], 'properties':{
                'op':{'enum':['send','status','finish'] if toolkit == 'check' else ['send','finish']},
                'job':{'type':['integer','null'], 'minimum':1, 'maximum':4}, 'key':key}}


def revised_request(original, toolkit):
    """The sole allowed change on a rejected request is its provider schema."""
    if original['schema'] != schema_for(original['phase'], toolkit):
        raise ValueError('rejected request local schema mismatch')
    return {**original, 'schema':claude_schema(original['phase'], toolkit)}
