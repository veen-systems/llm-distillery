"""Belonging harvest round 1 (README.md): every eligible `hi`-band row, run on sadalsuud.

    python3 extract_hi.py exclude_ids.txt > harvest_r1_rows.jsonl     # counts go to stderr

The population and filters are those of ../2026-10-03-belonging-heldout/draw_heldout.py (same files, stage2 only,
no news.google.com, content >= 300 chars, exclusion BEFORE dedup by id then content_hash), restricted to the
owner-ruled band: student raw_weighted_average >= 5.6. Content is cut at 4,000 chars, as in the held-out run."""
import glob, json, os, sys

D = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging/')
LAST = 'filtered_20261003_084553.jsonl'  # the held-out window's last file: same window, so its rates apply
ex = set(open(sys.argv[1]).read().split())
seen_ids, seen_hash = set(), set()
n = dict(rows=0, bad=0, stage2=0, gn=0, short=0, excluded=0, dup=0, not_hi=0, kept=0)
files = [f for f in sorted(glob.glob(D + 'filtered_*.jsonl')) if os.path.basename(f) <= LAST]
for f in files:
    for line in open(f):
        n['rows'] += 1
        try:
            r = json.loads(line)
        except ValueError:
            n['bad'] += 1; continue
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
        if raw is None or raw < 5.6:
            n['not_hi'] += 1; continue
        n['kept'] += 1
        print(json.dumps(dict(id=r['id'], title=r.get('title'), url=url, source=r.get('source'), content=content[:4000],
                              raw=raw, file=os.path.basename(f)), ensure_ascii=False))
n.update(files=len(files), window=f"{os.path.basename(files[0])} .. {os.path.basename(files[-1])}")
print(json.dumps(n), file=sys.stderr)
