"""Belonging adjudication pilot v3 (enriched): build the four blind judge inputs and the key.

    python3 docs/evidence/2026-10-02-belonging-adjudication/build_pilot_inputs_v3.py pilot3_rows.jsonl

Input: draw_pilot_v3.py output (b650). Controls come from the gitignored
datasets/belonging_adjudication/exemplars_v2_full.jsonl. Writes:
  docs/evidence/2026-10-02-belonging-adjudication/key_v3.jsonl  id, stratum, n_in_stratum, student raw, maxsim, oracle_in, expected
  datasets/belonging_adjudication/pilot3/{A1,A2,B1,B2}/input.jsonl  (+ an empty scratch/ per judge), gitignored
Raises unless there are 104 distinct ids, none of them in either earlier pilot's key."""
import json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CONTROLS = {'arabic_khaleej_times_96980715085f': 'in_scope',
            'spanish_eldiario_1292add7258e': 'in_scope',
            'south_american_cuba_headlines_d8011b247ea7': 'out',
            'australian_abc_au_fb9f91573d7b': 'out'}
ex = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(ROOT, 'datasets/belonging_adjudication/exemplars_v2_full.jsonl'))}
items, key = [], []
for line in open(sys.argv[1]):
    r = json.loads(line)
    items.append(dict(id=r['id'], title=r['title'], url=r['url'],
                      source=r.get('source') or re.sub(r'_[0-9a-f]{12}$', '', r['id']), content=r['content']))
    key.append(dict(id=r['id'], stratum=r['stratum'], n_in_stratum=r['n_in_stratum'], score=r['raw'],
                    score_kind='student_raw', maxsim=r['maxsim'], oracle_in=(r['raw'] or 0) >= 4.0))
for i, expected in CONTROLS.items():
    e = ex[i]
    items.append(dict(id=i, title=e['title'], url=e['url'], source=e['source'], content=e['content']))
    key.append(dict(id=i, stratum='control', expected=expected))
ids = [k['id'] for k in key]
first = {json.loads(l)['id'] for f in ('key.jsonl', 'key_v2.jsonl') for l in open(os.path.join(HERE, f))}
if len(ids) != 104 or len(set(ids)) != 104:
    raise SystemExit(f'expected 104 distinct ids, got {len(ids)} / {len(set(ids))}')
if (set(ids) - set(CONTROLS)) & first:
    raise SystemExit(f'rows from the first pilot: {sorted((set(ids) - set(CONTROLS)) & first)}')
with open(os.path.join(HERE, 'key_v3.jsonl'), 'w') as f:
    for k in key:
        f.write(json.dumps(k) + '\n')
for p, seed in (('A', 21), ('B', 22)):
    order = sorted(items, key=lambda x: x['id'])
    random.Random(seed).shuffle(order)
    for part, chunk in ((1, order[:52]), (2, order[52:])):
        d = os.path.join(ROOT, 'datasets/belonging_adjudication/pilot3', f'{p}{part}')
        os.makedirs(os.path.join(d, 'scratch'), exist_ok=True)
        with open(os.path.join(d, 'input.jsonl'), 'w') as f:
            for x in chunk:
                f.write(json.dumps(x, ensure_ascii=False) + '\n')
print('key_v3.jsonl + 4 inputs of 52')
