"""Held-out production sample for the v2 prompt (FILTER_PLAYBOOK §1b). Run ON sadalsuud:

    python3 fetch_prod_sample.py > prod_sample.jsonl

Population: every stage-2 belonging row the LIVE STUDENT surfaces (raw_weighted_average >= 4.0) in the
filtered files dated 2026-10-01, i.e. after every test-set row was drawn and unseen while the prompt
was written, with content >= 300 chars (the labelling floor the oracle path applies anyway).
Draw: random.Random("belonging-v2-prod-heldout").sample(sorted(ids), 150). Prints the population size
and window to stderr so the denominator travels with the sample."""
import glob, json, os, random, sys

base = os.path.expanduser('~/local_dev/NexusMind/data/filtered/belonging')
files = sorted(glob.glob(f'{base}/filtered_20261001_*.jsonl'))
if not files:
    raise SystemExit('no filtered_20261001_* files')
rows = {}
for f in files:
    for line in open(f):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        a = (r.get('nexus_mind_attributes') or {}).get('belonging') or {}
        raw = a.get('raw_weighted_average')
        if raw is None or raw < 4.0 or a.get('stage_used') == 'stage1_low':
            continue
        if len(r.get('content') or '') < 300:
            continue
        rows[r['id']] = dict(id=r['id'], url=r.get('url'), title=r.get('title'), source=r.get('source'),
                             content=r.get('content'), observed_raw=raw, observed_stage=a.get('stage_used'),
                             observed_harm=r.get('_harm_is_subject_score'), origin=os.path.basename(f))
pick = random.Random('belonging-v2-prod-heldout').sample(sorted(rows), 150)
print(f'population {len(rows)} rows; window {os.path.basename(files[0])}..{os.path.basename(files[-1])}',
      file=sys.stderr)
for i in pick:
    print(json.dumps(rows[i], ensure_ascii=False))
