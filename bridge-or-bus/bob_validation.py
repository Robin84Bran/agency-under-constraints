"""Strict provider metadata and episode-local model failure boundaries."""
import json
import math


class ModelFailure(ValueError):
    """Rejected model content; no repair, effect, retry or cohort stop."""


class EpisodeTransport(ValueError):
    """Local incomplete/unreadable generation; ends one episode, counts for pause."""


class _Pairs(list):
    pass


def envelope(raw):
    """Keep usage/identity when only structured_output is invalid (e.g. duplicates)."""
    # Parsing pairs first prevents duplicate payload keys from erasing accounting.
    tree=json.loads(raw,object_pairs_hook=_Pairs,
                    parse_constant=lambda value:float(value))
    def convert(value):
        if isinstance(value,_Pairs):
            out={}
            for k,v in value:
                if k in out:
                    raise ValueError('duplicate key: '+k)
                out[k]=convert(v)
            return out
        if isinstance(value,list):
            return [convert(v) for v in value]
        if type(value) is float and not math.isfinite(value):
            raise ValueError('nonfinite JSON number')
        return value
    if not isinstance(tree,_Pairs):
        raise ValueError('provider envelope must be object')
    result={}; problem=None
    for k,v in tree:
        if k in result:
            raise ValueError('duplicate envelope key: '+k)
        if k=='structured_output':
            try:
                result[k]=convert(v)
            except ValueError as exc:
                result[k]=None
                problem=str(exc)
        else:
            result[k]=convert(v)
    return result,problem


def claude_contract(env):
    """Metadata only. Content failure cannot mask identity or actual tool use."""
    from bob_collect import Stop
    models=env.get('modelUsage')
    if type(models) is not dict or set(models)!={'claude-opus-5-5'}:
        raise Stop('Claude returned identity mismatch/UNKNOWN')
    if env.get('effort') not in (None,'medium'):
        raise Stop('Claude returned effort mismatch')
    turns=env.get('num_turns')
    stop=env.get('stop_reason')
    if type(turns) is not int or turns not in (1,2) or (turns==2 and stop!='tool_use'):
        raise Stop('Claude internal turn count mismatch/UNKNOWN')
    if stop not in (None,'end_turn','tool_use','max_tokens'):
        raise Stop('Claude unknown stop reason')
    # Historical one-turn fixtures omit stop_reason; two-turn replies must prove
    # the CLI schema-tool stop. A schema tool is not a real external tool.
    def positive(value):
        if type(value) is dict:
            return any(positive(v) for v in value.values())
        if type(value) is list:
            return any(positive(v) for v in value)
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise Stop('invalid Claude activity statistics')
        return value>0
    if env.get('permission_denials'):
        raise Stop('Claude permission denial/tool contract failure')
    if positive(env.get('subagent_stats',{})) or positive(env.get('usage',{}).get('server_tool_use',{})):
        raise Stop('Claude real tool/subagent activity')
    if positive(env.get('safety_stops',0)):
        raise Stop('Claude safety stop')
    for model in models.values():
        if type(model) is not dict:
            raise Stop('invalid Claude model metadata')
        if positive(model.get('webSearchRequests',0)):
            raise Stop('Claude real tool activity')
    if env.get('type')!='result':
        raise Stop('Claude unknown envelope type')
    if env.get('subtype')=='error_max_structured_output_retries':
        if env.get('is_error') is not True:
            raise Stop('inconsistent Claude schema rejection metadata')
        return 'Claude rejected model structured output'
    if env.get('subtype')!='success' or env.get('is_error') is not False:
        raise Stop('Claude failed/unfinished envelope')
    return 'Claude model output length' if stop=='max_tokens' else None


def decode(raw,model):
    from bob_collect import Stop
    try:
        return envelope(raw)
    except (ValueError,UnicodeError,TypeError,OverflowError,RecursionError) as exc:
        if model!='claude':
            raise EpisodeTransport('unreadable local envelope: '+str(exc)) from exc
        raise Stop('unreadable Claude envelope/accounting UNKNOWN: '+str(exc)) from exc
