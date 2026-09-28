import json, glob, os, random, sys
OP = {'uplifting':4.5,'human_thriving':4.5,'solutions':2.25,'belonging':4.0,'nature_recovery':3.75,'cultural_discovery':4.0006}
base=os.path.expanduser('~/local_dev/NexusMind/data/filtered')
random.seed(0)
for lens in sys.argv[1:]:
    op=OP[lens]; rows={}
    for f in sorted(glob.glob(f'{base}/{lens}/filtered_*.jsonl'))[-12:]:
        for line in open(f):
            try: r=json.loads(line)
            except Exception: continue
            a=r.get('nexus_mind_attributes',{}).get(lens) or {}
            raw=a.get('raw_weighted_average')
            if raw is None or raw<op or a.get('stage_used')=='stage1_low': continue
            h=r.get('_harm_is_subject_score')
            if h is not None and h>=0.7: rows[r['id']]=(h,raw,(r.get('title') or '')[:110])
    s=random.sample(sorted(rows.values()),min(12,len(rows)))
    print(f'== {lens}: {len(rows)} rows with harm>=0.7; random 12')
    for h,raw,t in sorted(s,reverse=True): print(f'  h={h:.2f} raw={raw:.2f}  {t}')
