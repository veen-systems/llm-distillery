"""Belonging retrieval: extract the production corpus for embedding screening (run on sadalsuud).

    python3 extract_corpus_v3.py exclude_ids.txt exclude_urls.txt > corpus.jsonl

Every distinct `stage2` belonging row in every retained data/filtered/belonging/ file (first occurrence kept by id
and content_hash). Excludes news.google.com, content < 300 chars, and the given ids/urls. Content is cut to 4,000
characters to keep the transfer small (the screener embeds the first 1,024). Counts go to stderr."""
import glob, json, os, sys

D = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging/')
ex_ids = set(open(sys.argv[1]).read().split())
ex_urls = set(open(sys.argv[2]).read().split())
seen_ids, seen_hash = set(), set()
n = dict(rows=0, stage2=0, kept=0, gn=0, short=0, excluded=0, dup=0, bad=0)
for f in sorted(glob.glob(D + 'filtered_*.jsonl')):
    for line in open(f):
        n['rows'] += 1
        try:
            r = json.loads(line)
        except ValueError:
            n['bad'] += 1
            continue
        a = r['nexus_mind_attributes']['belonging']
        if a.get('stage_used') != 'stage2':
            continue
        n['stage2'] += 1
        url, content, h = r.get('url') or '', r.get('content') or '', r.get('content_hash')
        if r['id'] in seen_ids or (h and h in seen_hash):
            n['dup'] += 1
            continue
        seen_ids.add(r['id'])
        if h:
            seen_hash.add(h)
        if 'news.google.com' in url:
            n['gn'] += 1
            continue
        if len(content) < 300:
            n['short'] += 1
            continue
        if r['id'] in ex_ids or url in ex_urls:
            n['excluded'] += 1
            continue
        n['kept'] += 1
        print(json.dumps(dict(id=r['id'], title=r.get('title'), url=url, source=r.get('source'),
                              source_type=r.get('source_type'), content=content[:4000],
                              raw=a.get('raw_weighted_average'), file=os.path.basename(f)), ensure_ascii=False))
print(n, file=sys.stderr)
