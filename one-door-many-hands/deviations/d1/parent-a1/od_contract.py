"""Pure frozen request literals; no provider imports."""
from od_core import PINS,MODEL,SYSTEM,SCHEMA_TEXT

CLAUDE_BIN='<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude'
OPTIONS={'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192}

def controls():
    return {'CLAUDE_CODE_MAX_OUTPUT_TOKENS':'512','CLAUDE_CODE_MAX_RETRIES':'0','MAX_STRUCTURED_OUTPUT_RETRIES':'0',
     'CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES':'0','CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','CLAUDE_CODE_NO_MODEL_FALLBACK':'1','DISABLE_AUTOUPDATER':'1'}

def claude_command(binary,budget):
    return [str(binary),'--print','--safe-mode','--restricted','--strict-mcp-config','--mcp-config','{"mcpServers":{}}',
     '--tools','','--disable-slash-commands','--no-chrome','--no-session-persistence','--setting-sources','',
     '--settings','{"disableAllHooks":true}','--output-format','json','--json-schema',SCHEMA_TEXT,
     '--model',MODEL,'--effort','medium','--system-prompt',SYSTEM,'--max-turns','1','--max-budget-usd',format(budget/1000000,'.6f')]

def request(ep,prompt,bound,binary=CLAUDE_BIN):
    if ep['actor']=='claude': return {'stdin_utf8':prompt,'argv':claude_command(binary,bound['micro_usd']),'environment_controls':controls(),'timeout_seconds':300,'seed_supported':False}
    return {'model':PINS[ep['actor']][0],'prompt':prompt,'system':SYSTEM,'format':'json','stream':False,'options':dict(OPTIONS,seed=ep['block'])}

