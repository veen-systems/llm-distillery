"""Belonging adj1: ~800 'easy negatives', a uniform random draw from production (owner 2026-10-07), run on sadalsuud.
    python3 draw_easy_negatives.py exclude_ids.txt > easyneg_rows.jsonl     # counts and the window go to stderr
Why: in the planned build, articles over 2,000 chars were 12-21% positive vs ~2-9% in production (all enriched),
which would bias the student toward 'in'. These rows put production-like long articles on the negative side.
Population: every distinct belonging row (ANY stage, any score: this is the production distribution, labelled by
the oracle afterwards, not by the student) in every retained data/filtered/belonging/ file. Excludes news.google.com
(never oracle-re-score a GN row), content < 300 chars and the given ids. Exclusion runs before deduplication (by id,
then content_hash; first occurrence kept). FULL text (no cut). n = 800, seed 20261007."""
import glob, json, os, random, sys
D = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging/')
N, SEED = 800, 20261007
ex = set(open(sys.argv[1]).read().split())
seen_ids, seen_hash, pool = set(), set(), []
n = dict(rows=0, bad=0, gn=0, short=0, excluded=0, dup=0, kept=0)
files = sorted(glob.glob(D + 'filtered_*.jsonl'))
for fi, f in enumerate(files):
    with open(f) as fh:
        for ln, line in enumerate(fh):
            n['rows'] += 1
            try:
                r = json.loads(line)
            except ValueError:
                n['bad'] += 1; continue
            url, content, h = r.get('url') or '', r.get('content') or '', r.get('content_hash')
            if 'news.google.com' in url:
                n['gn'] += 1; continue
            if len(content) < 300:
                n['short'] += 1; continue
            if r['id'] in ex:
                n['excluded'] += 1; continue
            if r['id'] in seen_ids or (h and h in seen_hash):
                n['dup'] += 1; continue
            seen_ids.add(r['id'])
            if h:
                seen_hash.add(h)
            n['kept'] += 1
            pool.append((r['id'], fi, ln))
pick = random.Random(SEED).sample(sorted(pool), N)
want = {}
for rid, fi, ln in pick:
    want.setdefault(fi, set()).add(ln)
out = 0
for fi, lines in want.items():
    with open(files[fi]) as fh:
        for ln, line in enumerate(fh):
            if ln in lines:
                r = json.loads(line)
                a = (r.get('nexus_mind_attributes') or {}).get('belonging') or {}
                print(json.dumps(dict(id=r['id'], title=r.get('title'), url=r.get('url'), source=r.get('source'),
                                      content=r.get('content'), stage_used=a.get('stage_used'),
                                      raw=a.get('raw_weighted_average'), file=os.path.basename(files[fi])),
                                 ensure_ascii=False))
                out += 1
n.update(out=out, pool=len(pool), window=f"{os.path.basename(files[0])} .. {os.path.basename(files[-1])}", files=len(files))
print(json.dumps(n), file=sys.stderr)
