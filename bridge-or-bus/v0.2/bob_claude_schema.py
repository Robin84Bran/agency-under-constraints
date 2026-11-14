"""Claude-only object-root contracts. Local grammar and strict validators stay frozen."""
import json
from bob_core import ROOT

CLAUDE_SCHEMAS = {
    phase: json.loads((ROOT / f'config/claude-{phase}-schema.json').read_text())
    for phase in ('action', 'report')
}
