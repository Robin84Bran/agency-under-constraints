"""Generate the reviewable A1 raise/fatal inventory; never dispatch or touch Git."""
import ast
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from ps_io import read, save

ROOT=Path(__file__).resolve().parents[2]
FIXED={('ps_transport.py',124):'Local unreadable envelopes are transport episodes; invalid designated Claude payload JSON preserves strict metadata and settles known usage.',
       ('ps_transport.py',125):'Local nonobject envelopes are transport episodes; paid nonobject metadata remains fatal.',
       ('ps_transport.py',133):'Completed Claude length/schema-tool exhaustion is model content; other envelope/turn mismatches stay fatal.',
       ('ps_transport.py',141):'Missing/nonobject structured_output ends only the episode, including first paid call.',
       ('ps_transport.py',145):'Missing local input usage is UNKNOWN transport evidence; no zero substitution.',
       ('ps_transport.py',155):'Content validator errors stay episode-local; unknown harness phase is now rejected before this wrapper.',
       ('ps_analysis.py',204):'Contract binds earliest accepted frontier payload after any prior failed model episodes.',
       ('ps_analysis.py',205):'An earlier model-content failure cannot require a contract marker; first accepted payload still must have one.',
       ('ps_collect.py',56):'Removed first-paid promotion of EpisodeFailure to fatal; integrity/accounting still takes precedence.'}


def category(file,expression):
    if file=='ps_core.py':
        if any(x in expression for x in ('unknown world','label collision','episode ended','unknown phase')):
            return 'Fatal harness','Frozen generator/phase/state guard; not generated action content.'
        if any(x in expression for x in ('duplicate key','nonfinite','JSON text')):
            return 'Contextual strict parsing','Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting.'
        return 'Episode model content','Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal.'
    if 'TransportFailure' in expression or 'Stop if paid else' in expression:
        return 'Local transport episode / paid fatal' if 'Stop if paid else' in expression else 'Local transport episode','No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal.'
    if expression.startswith('EpisodeFailure'):
        return 'Episode model content','Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort.'
    if file=='ps_transport.py' and expression.startswith('ValueError'):
        return 'Contextual envelope parsing','Invalid designated structured_output is isolated as episode content; invalid provider metadata is fatal (local unreadable envelope -> transport episode).'
    if file=='ps_analysis.py': return 'Fatal retained-evidence integrity','Independent replay/accounting mismatch; never a model-content rejection route.'
    if file=='ps_freeze.py': return 'Fatal provenance/integrity','Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate.'
    if file=='ps_io.py': return 'Fatal ledger/storage/resource','Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity.'
    if file=='ps_offline.py': return 'Fatal offline evidence preservation','Refuse overwriting an existing synthetic output directory.'
    if file=='ps_collect.py': return 'Fatal harness/integrity','Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception.'
    return 'Fatal identity/transport/accounting','Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata.'


def raises():
    result=[]
    for p in sorted(ROOT.glob('ps*.py')):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Raise):
                expression=ast.unparse(node.exc) if node.exc else 'reraise'
                cls,reason=category(p.name,expression)
                result.append({'file':p.name,'line':node.lineno,'expression':expression,'class':cls,'reason':reason})
    return sorted(result,key=lambda r:(r['file'],r['line']))


def fatal_sites(path):
    return sorted(n.lineno for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.Assign) and
                  any(isinstance(t,ast.Name) and t.id=='fatal' for t in n.targets) and
                  not (isinstance(n.value,ast.Constant) and n.value.value is False))


def main():
    original=read(ROOT/'revisions/a1/original-raise-sites.json')
    original += [{'file':'ps_collect.py','line':n,'expression':'fatal control: '+ROOT.joinpath('revisions/a1/original/ps_collect.py').read_text().splitlines()[n-1].strip()} for n in fatal_sites(ROOT/'revisions/a1/original/ps_collect.py')]
    for row in original:
        row['disposition']='fixed' if (row['file'],row['line']) in FIXED else 'already right'
        row['class'],row['reason']=category(row['file'],row['expression'])
        if row['disposition']=='fixed':
            row['reason']=FIXED[row['file'],row['line']]
            row['class']={124:'Contextual payload content / metadata integrity',125:'Local transport episode / paid fatal',
                          133:'Episode model content / fatal envelope metadata',141:'Episode model content',
                          145:'Local transport episode',155:'Episode model content / fatal harness phase',
                          204:'Fatal retained-evidence integrity; corrected scope',205:'Fatal retained-evidence integrity; corrected scope',
                          56:'Episode model content / fatal integrity precedence'}[row['line']]
    original.sort(key=lambda r:(r['file'],r['line']))
    final=raises()
    for n in fatal_sites(ROOT/'ps_collect.py'):
        final.append({'file':'ps_collect.py','line':n,'expression':'fatal control: '+ROOT.joinpath('ps_collect.py').read_text().splitlines()[n-1].strip(),
                      'class':'Fatal accounting / typed integrity precedence','reason':'Unknown paid usage, measured overrun or accounting failure is fatal; typed content/transport failures alone are not promoted.'})
    final.sort(key=lambda r:(r['file'],r['line']))
    counts={'original_raise_sites':131,'original_fatal_control_sites':4,'audited_original_sites':len(original),
            'fixed':sum(r['disposition']=='fixed' for r in original),'already_right':sum(r['disposition']=='already right' for r in original),
            'final_raise_sites':len(raises()),'final_fatal_control_sites':len(fatal_sites(ROOT/'ps_collect.py'))}
    save(ROOT/'revisions/a1/audit-paths.json',{'counts':counts,'original':original,'final':final})
    with (ROOT/'DEVIATIONS.md').open('a') as f:
        f.write('\n## Exhaustive Stop/raise/fatal audit\n\n')
        f.write('Counts use source sites, not unique bug causes: **'+str(counts['fixed'])+' fixed / '+str(counts['already_right'])+' already right**, covering 131 original explicit raises and four direct fatal controls. The two replay contract sites implement the same first-content-failure correction as the collector. New guards are additional protections, not retroactively counted as original sites.\n\n')
        f.write('The tables include every explicit raise in all `ps*.py` modules, including core validators, journal/readers, freeze/provenance validators, independent replay and offline output protection. Built-in parser/OS/subprocess exceptions are routed as described below. `revisions/a1/audit-paths.json` is the machine-readable inventory; regression checks compare it against the AST. Original locations refer to the preserved baseline.\n\n')
        for title,rows in (('Original sites and disposition',original),('Final sites and failure scope',final)):
            f.write('### '+title+'\n\n| Site | Expression | Classification | Disposition / reason |\n|---|---|---|---|\n')
            for r in rows:
                safe=lambda s:s.replace('|','&#124;').replace('\n',' ')
                f.write('| `'+r['file']+':'+str(r['line'])+'` | `'+safe(r['expression'])+'` | '+r['class']+' | '+r.get('disposition','Current')+': '+safe(r['reason'])+' |\n')
            f.write('\n')
    print(counts)

if __name__=='__main__': main()
