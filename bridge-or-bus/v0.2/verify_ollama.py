"""Read installed package bytes only; never invoke Ollama or its HTTP API."""
import hashlib
import json
from pathlib import Path


def inspect():
    package=Path('/opt/homebrew/Cellar/ollama/0.33.3')
    probes={
        'libexec/ollama':[
            'mod\tgithub.com/ollama/ollama\tv0.33.3+dirty',
            'invalid format: expected "json" or a valid JSON Schema object',
            'github.com/ollama/ollama/server.(*Server).GenerateHandler',
            'github.com/ollama/ollama/llm.(*llamaServerRunner).Completion',
            'github.com/ollama/ollama/llm.llamaServerChatResponseFormat',
            'schema must be a JSON object'],
        'libexec/lib/ollama/llama-server':['json_schema_to_grammar','anyOf','enum','additionalProperties','maxLength']}
    records=[]
    for name,needles in probes.items():
        path=package/name;raw=path.read_bytes();snippets=[]
        for needle in needles:
            offset=raw.find(needle.encode())
            if offset<0:raise ValueError('missing evidence '+needle)
            snippets.append(dict(text=needle,offset=offset,hex=needle.encode().hex()))
        records.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),snippets=snippets))
    path=package/'.brew/ollama.rb';raw=path.read_bytes()
    assert b'v0.33.3' in raw and b'b79067b0db7417f20108363bc22adb97f35c966a' in raw
    return dict(status='VERIFIED',version='0.33.3',method='offline installed-binary byte probes and formula tag/revision; no execution or network',model_calls=0,network_requests=0,sources=records,formula=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),tag='v0.33.3',revision='b79067b0db7417f20108363bc22adb97f35c966a'),conclusion='format accepts a schema object; JSON-Schema-to-grammar implementation including anyOf is present',live_schema_compilation_status='UNKNOWN',limits='Not a runtime-generation test or proof that every keyword is perfectly enforced. Independent validator remains authoritative.')

if __name__=='__main__':
    print(json.dumps(inspect(),sort_keys=True,indent=2))
