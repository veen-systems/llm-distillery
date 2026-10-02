import json,glob,os,re,sys
def norm(u):
    u=re.sub(r'^https?://(www\.)?','',(u or '').split('?')[0].split('#')[0]).rstrip('/').lower()
    return re.sub(r'\.amp$','',u.replace('bbc.co.uk','bbc.com'))
ids=set(open('/tmp/want_ids.txt').read().split()); urls={norm(u) for u in open('/tmp/want_urls.txt').read().split()}
got={}
D=os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging')
for f in sorted(glob.glob(D+'/filtered_*.jsonl')):
    for l in open(f):
        try: r=json.loads(l)
        except: continue
        i=r.get('id'); u1,u2=norm(r.get('url')),norm(r.get('resolved_url'))
        key=None
        if i in ids: key=('reader',i)
        elif u1 in urls or u2 in urls: key=('curator',u1 if u1 in urls else u2)
        if key and key not in got:
            a=r['nexus_mind_attributes']['belonging']
            got[key]=dict(src=key[0],id=i,url=r.get('url'),title=r.get('title'),source=r.get('source'),lang=r.get('language'),
               raw=a.get('raw_weighted_average'),stage=a.get('stage_used'),scores=a.get('scores'),content=r.get('content'),file=os.path.basename(f))
for v in got.values(): print(json.dumps(v,ensure_ascii=False))
print(len(got),file=sys.stderr)
