import json,glob,os,sys
D=os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging')
out=open('/tmp/bel_month.tsv','w')
per=[]
seen=set()
for f in sorted(glob.glob(D+'/filtered_*.jsonl')):
    n=s2=surf=dup=0
    for l in open(f):
        try: r=json.loads(l)
        except: continue
        a=r.get('nexus_mind_attributes',{}).get('belonging',{})
        n+=1
        st=a.get('stage_used'); raw=a.get('raw_weighted_average') or 0
        if st=='stage2': s2+=1
        if st=='stage2' and raw>=4.0:
            surf+=1
            if r['id'] in seen: dup+=1; continue
            seen.add(r['id'])
            sc=a.get('scores',{})
            out.write('\t'.join(map(str,[os.path.basename(f)[9:22],r['id'],r.get('source'),r.get('source_group'),r.get('language'),
              round(raw,2),round(a.get('weighted_average') or 0,2),round(r.get('_harm_is_subject_score') or -1,3),
              (r.get('metadata',{}).get('quality',{}) or {}).get('type_classification'),
              json.dumps({k:round(v,1) for k,v in sc.items()}),
              (r.get('title') or '').replace('\t',' ').replace('\n',' ')[:160], r.get('url')]))+'\n')
    per.append((os.path.basename(f)[9:22],n,s2,surf,dup))
for p in per: print(*p,sep='\t',file=sys.stderr)
