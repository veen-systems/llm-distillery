"""Fetch the article rows behind labels.tsv. Run ON sadalsuud (NexusMind data lives there):

    python3 fetch_rows.py labels.tsv > rows.jsonl

Three sources, each a different window, so each row records where it came from:
  1. live filtered files  ~/local_dev/NexusMind/data/filtered/belonging/filtered_*.jsonl
     (hand-check, EXP-025 and random strata; retention-bounded, so a re-run after the
     files rotate out finds nothing — that is the archive's job, source 2)
  2. monthly raw archives ~/local_dev/NexusMind/data/archived/raw_2026-0{7,8}.tar.gz
     (the #130 worked examples, 2026-08-21..24; the two owner-labelled adverse rows,
     2026-07-27..29 and 2026-08-05..08). PRE-enrichment text: shorter than what the
     scorer saw in production (Charleville 149 chars here vs 2,794 enriched).
Raises if any labelled url is not found — a missing row must never shrink the set silently.

The random stratum was DRAWN by this rule (kept here so the draw is auditable; the
labels file, not a re-draw, is the set): stage-2 belonging rows with raw_weighted_average
>= 4.0 in the last 12 files dated before 2026-10-01 (filtered_20260927_050818 ..
filtered_20260930_212945, 1,521 distinct ids, url not already in another stratum),
random.Random("belonging-v2-random").sample(sorted(ids), 40)."""
import glob, json, os, sys, tarfile

labels = [l.rstrip('\n').split('\t') for l in open(sys.argv[1])][1:]
want = {row[1]: row[0] for row in labels}
base = os.path.expanduser('~/local_dev/NexusMind/data')
found = {}

def keep(r, origin):
    if r.get('url') in want and r['url'] not in found:
        a = (r.get('nexus_mind_attributes') or {}).get('belonging') or {}
        found[r['url']] = dict(id=r.get('id'), url=r['url'], title=r.get('title'),
                               source=r.get('source'), content=r.get('content'),
                               observed_raw=a.get('raw_weighted_average'),
                               observed_stage=a.get('stage_used'),
                               observed_harm=r.get('_harm_is_subject_score'), origin=origin)

for f in sorted(glob.glob(f'{base}/filtered/belonging/filtered_*.jsonl')):
    for line in open(f):
        if '"url"' in line:
            try: keep(json.loads(line), os.path.basename(f))
            except json.JSONDecodeError: pass

ARCHIVES = {'raw_2026-07.tar.gz': ('content_items_2026072',),
            'raw_2026-08.tar.gz': ('content_items_2026080', 'content_items_2026082')}
for name, prefixes in ARCHIVES.items():
    if all(u in found for u in want): break
    with tarfile.open(f'{base}/archived/{name}') as tar:
        for m in tar:
            if not any(os.path.basename(m.name).startswith(p) for p in prefixes): continue
            for line in tar.extractfile(m):
                try: keep(json.loads(line), f'{name}:{os.path.basename(m.name)}')
                except json.JSONDecodeError: pass

missing = [u for u in want if u not in found]
if missing:
    raise SystemExit(f'{len(missing)} labelled urls not found: {missing}')
for u in want:
    print(json.dumps(found[u], ensure_ascii=False))
