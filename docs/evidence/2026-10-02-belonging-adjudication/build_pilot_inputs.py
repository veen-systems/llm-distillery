"""Belonging adjudication pilot: build the four blind judge inputs and the key.

    python3 docs/evidence/2026-10-02-belonging-adjudication/build_pilot_inputs.py pilot_rows.jsonl

pilot_rows.jsonl is draw_pilot.py's output (b650). Controls come from the gitignored
datasets/belonging_adjudication/exemplars_full.jsonl. Writes:
  docs/evidence/2026-10-02-belonging-adjudication/key.jsonl   id, stratum, n_in_stratum, oracle_wa, expected (committed)
  datasets/belonging_adjudication/pilot/{A1,A2,B1,B2}/input.jsonl   full text, gitignored; one dir per judge
Judges see id, title, url, source, content only. Pass A and pass B get different shuffles."""
import json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CONTROLS = {'british_irish_guardian_uk_3243001d4d87': 'in_scope',
            'pan_african_alwihda_info_4f54e2c1d59c': 'in_scope',
            'west_african_punch_ng_09d36ee26016': 'out',
            'east_african_lexpress_madagascar_b156bebd2863': 'out'}
rows = [json.loads(l) for l in open(sys.argv[1])]
ex = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(ROOT, 'datasets/belonging_adjudication/exemplars_full.jsonl'))}
items, key = [], []
for r in rows:
    items.append(dict(id=r['id'], title=r['title'], url=r['url'], source=r.get('source') or re.sub(r'_[0-9a-f]{12}$', '', r['id']),
                      content=r['content']))
    key.append(dict(id=r['id'], stratum=r['stratum'], n_in_stratum=r['n_in_stratum'], oracle_wa=r['oracle_wa'], split=r['split']))
for i, expected in CONTROLS.items():
    e = ex[i]
    items.append(dict(id=i, title=e['title'], url=e['url'], source=e['source'], content=e['content']))
    key.append(dict(id=i, stratum='control', expected=expected))
ids = [k['id'] for k in key]
if len(ids) != 100 or len(set(ids)) != 100:
    raise SystemExit(f'expected 100 distinct ids, got {len(ids)} / {len(set(ids))}')
with open(os.path.join(HERE, 'key.jsonl'), 'w') as f:
    for k in key:
        f.write(json.dumps(k) + '\n')
for p, seed in (('A', 1), ('B', 2)):
    order = sorted(items, key=lambda x: x['id'])
    random.Random(seed).shuffle(order)
    for part, chunk in ((1, order[:50]), (2, order[50:])):
        d = os.path.join(ROOT, 'datasets/belonging_adjudication/pilot', f'{p}{part}')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'input.jsonl'), 'w') as f:
            for x in chunk:
                f.write(json.dumps(x, ensure_ascii=False) + '\n')
print('key.jsonl + 4 inputs of 50')
