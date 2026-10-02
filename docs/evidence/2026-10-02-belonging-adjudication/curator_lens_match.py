import json,glob,os,re,sys
def norm(u):
    u=re.sub(r'^https?://(www\.)?','',(u or '').split('?')[0].split('#')[0]).rstrip('/').lower()
    return re.sub(r'\.amp$','',u.replace('bbc.co.uk','bbc.com'))
S=json.load(open('/tmp/curator_stories.json'))
want={norm(s['url']) for s in S}
out={}
base=os.path.expanduser('~/local_dev/NexusMind/data/filtered/')
for lens in ('belonging','cultural_discovery','human_thriving','nature_recovery','solutions','uplifting'):
    for f in sorted(glob.glob(base+lens+'/filtered_*.jsonl')):
        for l in open(f):
            if 'http' not in l: continue
            try: r=json.loads(l)
            except: continue
            for u in (r.get('url'),r.get('resolved_url')):
                k=norm(u)
                if k in want and (k,lens) not in out:
                    a=r['nexus_mind_attributes'][lens]
                    out[(k,lens)]=dict(stage=a.get('stage_used'),raw=a.get('raw_weighted_average'))
json.dump([[k,l,v] for (k,l),v in out.items()],open('/tmp/cur_lens.json','w'))
print(len(want),len(out))
