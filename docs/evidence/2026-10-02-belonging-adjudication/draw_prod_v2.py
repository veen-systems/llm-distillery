"""Belonging pilot v2: draw the production stratum (run on sadalsuud).

    python3 draw_prod_v2.py exclude_ids.txt exclude_urls.txt > prod_rows.jsonl

Pool: every `stage2` row with raw >= 4.0 (belonging v1's op-point) in data/filtered/belonging/ files stamped
20260926 or later. Excludes news.google.com, content < 300 chars, the given ids and urls, and repeat content_hash
(first occurrence kept). Seed fixed. Prints the pool size to stderr; every row carries n_in_stratum."""
import glob, json, os, random, sys

N = 30
D = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging/')
ex_ids = set(open(sys.argv[1]).read().split())
ex_urls = set(open(sys.argv[2]).read().split())
pool, seen_ids, seen_hash = [], set(), set()
for f in sorted(glob.glob(D + 'filtered_*.jsonl')):
    if os.path.basename(f)[9:17] < '20260926':
        continue
    for line in open(f):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        a = r['nexus_mind_attributes']['belonging']
        if a.get('stage_used') != 'stage2' or (a.get('raw_weighted_average') or 0) < 4.0:
            continue
        url, content, h = r.get('url') or '', r.get('content') or '', r.get('content_hash')
        if ('news.google.com' in url or len(content) < 300 or r['id'] in ex_ids or url in ex_urls
                or r['id'] in seen_ids or (h and h in seen_hash)):
            continue
        seen_ids.add(r['id'])
        if h:
            seen_hash.add(h)
        pool.append(dict(id=r['id'], title=r.get('title'), url=url, source=r.get('source'), content=content,
                         raw=round(a['raw_weighted_average'], 4), file=os.path.basename(f)))
pool.sort(key=lambda r: r['id'])
for r in random.Random(20261003).sample(pool, N):
    print(json.dumps(dict(r, stratum='prod', n_in_stratum=len(pool)), ensure_ascii=False))
print(len(pool), file=sys.stderr)
