"""Belonging held-out set (PREREGISTRATION.md): stratified random draw from production, run on sadalsuud.

    python3 draw_heldout.py exclude_ids.txt > heldout_rows.jsonl     # counts and pool sizes go to stderr

Population: every distinct `stage2` belonging row in every retained data/filtered/belonging/ file. Excludes
news.google.com, content < 300 chars and the given ids. Exclusion runs BEFORE deduplication (by id, then content_hash;
first occurrence kept). Bands on the student's raw_weighted_average (stage2, so a model output): hi >= 5.6,
mid 4.0-5.6, near 2.5-4.0; rows below 2.5 are not in the population. 400 per band, seed 20261003. Each row carries
its band, the band's pool size and its design weight (pool / n drawn). Content is cut at 4,000 chars (as pilot v3)."""
import glob, json, os, random, sys

D = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging/')
N, SEED = 400, 20261003
BANDS = (('hi', 5.6, 99), ('mid', 4.0, 5.6), ('near', 2.5, 4.0))
ex = set(open(sys.argv[1]).read().split())
seen_ids, seen_hash, pool = set(), set(), {b[0]: [] for b in BANDS}
n = dict(rows=0, bad=0, stage2=0, gn=0, short=0, excluded=0, dup=0, below=0, kept=0)
files = sorted(glob.glob(D + 'filtered_*.jsonl'))
for fi, f in enumerate(files):
    with open(f) as fh:
        for ln, line in enumerate(fh):
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
            raw = a.get('raw_weighted_average')
            band = next((b for b, lo, hi in BANDS if raw is not None and lo <= raw < hi), None)
            if band is None:
                n['below'] += 1; continue
            n['kept'] += 1
            pool[band].append((r['id'], fi, ln))
rng = random.Random(SEED)
want = {}
for b, _, _ in BANDS:
    p = sorted(pool[b])
    for rid, fi, ln in rng.sample(p, N):
        want.setdefault(fi, {})[ln] = dict(band=b, n_in_band=len(p), weight=len(p) / N)
out = 0
for fi, lines in want.items():
    with open(files[fi]) as fh:
        for ln, line in enumerate(fh):
            if ln in lines:
                r = json.loads(line)
                print(json.dumps(dict(id=r['id'], title=r.get('title'), url=r.get('url'), source=r.get('source'),
                                      content=(r.get('content') or '')[:4000],
                                      raw=r['nexus_mind_attributes']['belonging'].get('raw_weighted_average'),
                                      file=os.path.basename(files[fi]), **lines[ln]), ensure_ascii=False))
                out += 1
n.update(out=out, window=f"{os.path.basename(files[0])} .. {os.path.basename(files[-1])}", files=len(files),
         pools={b: len(p) for b, p in pool.items()})
print(json.dumps(n), file=sys.stderr)
