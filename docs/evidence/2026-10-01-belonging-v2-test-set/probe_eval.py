"""Score the 49-row oracle probe (the v2-draft2 held-out passers Claude read as fits/junk) against those verdicts.
    PYTHONPATH=. .venv/bin/python docs/evidence/2026-10-01-belonging-v2-test-set/probe_eval.py <scored_dir> cap|nocap
`cap` applies the probe-A code cap: community_fabric <= 2.5 when the oracle answers cohesion_shown = no."""
import json,glob,sys,importlib.util,collections
spec=importlib.util.spec_from_file_location('bs','filters/belonging/v1/base_scorer.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
C=m.BaseBelongingScorer; W=C.DIMENSION_WEIGHTS
def wa(a,code_cap):
    s={d:float(a[d]['score']) for d in W}
    if code_cap and str((a.get('cohesion_shown') or {}).get('answer','')).lower().startswith('no'):
        s['community_fabric']=min(s['community_fabric'],2.5)
    v=sum(s[d]*W[d] for d in W)
    return min(v,C.GATEKEEPER_CAP) if s[C.GATEKEEPER_DIMENSION]<C.GATEKEEPER_MIN else v
truth={json.loads(l)['url']:json.loads(l)['claude_verdict'] for l in open('datasets/belonging_v2_test/oracle_probe_49.jsonl')}
d,cap=sys.argv[1],sys.argv[2]=='cap'
rows={}
for f in sorted(glob.glob(d+'/scored_batch_*.jsonl')):
    for l in open(f): r=json.loads(l); rows[r['url']]=r
print('unique scored',len(rows),'of',len(truth))
c=collections.Counter()
for u,r in rows.items():
    a=r['belonging_analysis']; c[(truth[u], wa(a,cap)>=4.0)]+=1
    if cap: c[('cohesion_shown',truth[u],str((a.get('cohesion_shown') or {}).get('answer')))]+=1
for k in sorted(c,key=str): print(k,c[k])
