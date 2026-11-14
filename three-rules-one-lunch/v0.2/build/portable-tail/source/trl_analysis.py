"""Offline v0.2 locals + unchanged v0.1 Claude; unchanged v0.1 estimators/baselines."""
import argparse
from collections import Counter
import csv
import io
from pathlib import Path
from legacy_analysis import score, summarize, export_tables
from trl_core import ROOT, REGIMES, baseline, canonical, sha
from trl_io import Stop, read, save, save_text
from trl_replay import inspect


def replay(ep,directory):
    d=Path(directory);terminal=read(d/'episode.json') if (d/'episode.json').exists() else None
    if not d.exists():
        return {'episode':ep,'status':'UNKNOWN','reason':'scheduled episode unstarted'}
    sim,calls,next_,used=inspect(ep,d)
    if used!={p.parent for p in (d/'calls').rglob('request.json')}:
        raise Stop('unexpected post-terminal/extra calls')
    generated=[c for c in calls if c['classification']!='DEFINITE_NON_START']
    if terminal is None:
        if next_ and next_[-1]:
            return {'episode':ep,'status':'UNKNOWN','reason':'definite non-start pause; no model penalty',
                'operational_non_starts':sum(c['classification']=='DEFINITE_NON_START' for c in calls)}
        raise Stop('nonterminal/uncertain saved evidence')
    if next_ is not None or (terminal['episode']!=ep or terminal['events']!=sim.events or terminal['receipts']!=sim.receipts or
        terminal['attempted_calls']!=len(generated) or terminal['complete']!=all(c['error'] is None for c in generated) or
        terminal['non_start_attempts']!=len(calls)-len(generated) or terminal['error']!=generated[-1]['error'] or
        any(c['evidence_kind']!=terminal['kind'] for c in calls) or
        terminal['classification']!=generated[-1]['classification'] or terminal['fatal']!=(generated[-1]['classification']=='INTEGRITY_FAILURE')):
        raise Stop('terminal episode differs from raw replay')
    row=score(ep['seed'],ep['regime'],sim.events,terminal['complete'],bool(generated))
    known=all(c['usage'] is not None for c in generated)
    row.update(episode=ep,kind=terminal['kind'],calls=len(generated),
        input_tokens=sum(c['usage']['input'] for c in generated) if known else None,
        output_tokens=sum(c['usage']['output'] for c in generated) if known else None,
        cache_read_tokens=sum(c['usage']['cache_read'] for c in generated) if known else None,
        cache_creation_tokens=sum(c['usage']['cache_creation'] for c in generated) if known else None,
        unknown_usage_calls=sum(c['usage'] is None for c in generated),
        elapsed_seconds=sum(c['elapsed_seconds'] for c in generated),classification=terminal['classification'],
        operational_non_starts=len(calls)-len(generated),source_version='v0.2',
        non_start_reasons=dict(Counter(c['non_start'] for c in calls if c['classification']=='DEFINITE_NON_START')))
    return row


def reused_rows(root):
    rows=[r for r in read(Path(root)/'reuse/v01-episodes.json') if r['episode']['actor']=='claude']
    expected=[e for e in read(Path(root)/'config/v01-episodes.json') if e['actor']=='claude']
    if [r['episode'] for r in rows]!=expected or len(rows)!=60 or any(r['kind']!='MODEL' for r in rows):
        raise Stop('reused Claude population mismatch')
    return [dict(r,source_version='v0.1-reused') for r in rows]


def controls(summary,out):
    stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\n')
    w.writerow(['seeds','policy','n','Y','H','post_Y'])
    for n in (100,20):
        for policy in ('greedy-shared','greedy-private','uniform','oracle','greedy-central','all-null'):
            regime='private' if policy=='greedy-private' else ('central' if policy in ('oracle','greedy-central') else 'shared')
            rows=[score(s,regime,baseline(s,policy).events,True,False) for s in range(n)]
            w.writerow([f'0-{n-1}',policy,n,*[sum(r[k] for r in rows)/n for k in ('Y','H','post_Y')]])
    save_text(Path(out)/'baselines.csv',stream.getvalue())
    # Publication-ready static figure generated from saved means, no extra analysis.
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1050" viewBox="0 0 1000 1050">',
        '<rect width="1000" height="1050" fill="white"/>',
        '<g font-family="sans-serif" font-size="15" fill="#17212b">',
        '<text x="24" y="30">Three Rules, One Lunch: mean reward / 1000 (all twelve opportunities)</text>',
        '<text x="24" y="54">'+summary['kind']+'; local v0.2, Claude v0.1 reused; code controls on same seeds</text>']
    y=85
    for actor,c in summary['cohorts'].items():
        lines.append(f'<text x="24" y="{y}">{actor} ({20 if actor=="claude" else 100} seeds)</text>');y+=24
        entries=[(r,c['regimes'][r]['Y'],'#246883') for r in REGIMES]
        entries += [(p,c['same_seed_baseline_mean_Y'][p],'#8799a3') for p in ('greedy-shared','greedy-private','uniform','oracle')]
        for label,v,color in entries:
            lines.extend([f'<text x="32" y="{y+14}">{label}</text>',
                f'<rect x="190" y="{y}" width="{600*v:.3f}" height="18" fill="{color}"/>',
                f'<text x="{800}" y="{y+14}">{v:.4f}</text>']);y+=27
        y+=18
    lines+=['</g></svg>'];save_text(Path(out)/'headline.svg','\n'.join(lines)+'\n')


def analyze(root,base,out,reuse_check=True):
    root,base,out=Path(root),Path(base),Path(out);out.mkdir(parents=True,exist_ok=False)
    from trl_reuse import rebuild
    if reuse_check: rebuild(root,out/'v01-rebuild')
    rows=[replay(e,base/'episodes'/e['id']) for e in read(root/'config/episodes.json')]+reused_rows(root)
    pending=[r['episode']['id'] for r in rows if r.get('status')=='UNKNOWN']
    save(out/'episodes.json',rows)
    if pending:
        result={'status':'UNKNOWN','reason':'v0.2 collection pending; non-starts are not model failures',
            'pending_episodes':pending,'new_frontier_calls':0}
    else:
        result=summarize(rows)
        result['source_versions']={'local':'v0.2','claude':'v0.1-reused','claude_rerun':False}
        result['operational_events']={'definite_non_starts':sum(r.get('operational_non_starts',0) for r in rows),
            'usage_limit_refusals':sum(r.get('operational_usage_limit_refusals',0)+r.get('non_start_reasons',{}).get('USAGE_LIMIT',0) for r in rows),
            'dns_non_starts':sum(r.get('non_start_reasons',{}).get('DNS',0) for r in rows),
            'classification':'proven non-starts excluded from model behaviour and model-failure counts'}
        result['local_active_time']=[__import__('trl_core').strict_load(line) for line in (base/'time-local.jsonl').read_text().splitlines()] if (base/'time-local.jsonl').exists() else None
        result['new_frontier_calls']=0
        result['reused_v01_accounting']=read(root/'reuse/v01-summary.json')['accounting']
        export_tables(result,out);controls(result,out)
    save(out/'summary.json',result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--base',type=Path)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    from trl_freeze import verify, push_gate
    verify(a.root);push_gate(a.root)
    # Verify journal/evidence before interpreting any local MODEL results.
    from trl_audit import evidence_gate
    evidence_gate(a.root)
    analyze(a.root,a.base or a.root/'collection',a.out)

if __name__=='__main__': main()
