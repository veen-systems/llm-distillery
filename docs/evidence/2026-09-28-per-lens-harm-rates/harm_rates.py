import json, glob, math, os, sys
OP = {'uplifting':4.5,'human_thriving':4.5,'solutions':2.25,'belonging':4.0,'nature_recovery':3.75,'cultural_discovery':4.0006}
TH = [0.3,0.5,0.7,0.8,0.9]
N_CYC = int(sys.argv[1]) if len(sys.argv)>1 else 12
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h,c+h
base=os.path.expanduser('~/local_dev/NexusMind/data/filtered')
for lens,op in OP.items():
    files=sorted(glob.glob(f'{base}/{lens}/filtered_*.jsonl'))[-N_CYC:]
    rows={}; s1_above=0; nostage=0
    for f in files:
        for line in open(f):
            try: r=json.loads(line)
            except Exception: continue
            a=r.get('nexus_mind_attributes',{}).get(lens)
            if not a: continue
            raw=a.get('raw_weighted_average')
            if raw is None or raw<op: continue
            st=a.get('stage_used')
            if st=='stage1_low': s1_above+=1; continue
            if st is None: nostage+=1
            rows[r['id']]=r.get('_harm_is_subject_score')
    n=len(rows); scored=[v for v in rows.values() if v is not None]
    print(f"{lens:18s} op>={op} window {os.path.basename(files[0])[9:24]}..{os.path.basename(files[-1])[9:24]} ({len(files)} files) "
          f"n_above={n} harm_present={len(scored)} ({100*len(scored)/max(n,1):.1f}%) stage1_low_above_op={s1_above} no_stage={nostage}")
    for t in TH:
        k=sum(v>=t for v in scored); lo,hi=wilson(k,len(scored))
        print(f"   harm>={t}: {k:5d}/{len(scored)} = {100*k/max(len(scored),1):5.1f}%  [{100*lo:.1f}, {100*hi:.1f}]")
