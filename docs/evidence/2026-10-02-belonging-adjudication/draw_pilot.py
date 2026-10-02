"""Belonging adjudication pilot: draw the sample from v1's training labels (run on b650-gpu).

    python3 draw_pilot.py exclude_ids.txt > pilot_rows.jsonl

Pool: every row of ~/llm-distillery/datasets/training/belonging_v1/{train,val,test}.jsonl whose v1 weighted
average is >= 3.5, with v1's weights and community_fabric gatekeeper (filters/belonging/v1/base_scorer.py:
< 3.0 caps the score at 3.42). Strata: `near` [3.5, 4.0) and `above` >= 4.0. Equal-ish sizes, NOT
proportional: every row carries `n_in_stratum` so pooled rates can be reweighted.
exclude_ids.txt: ids that must never be drawn (the v2 test set). Seed fixed."""
import json, os, random, sys

W = {'intergenerational_bonds': .25, 'community_fabric': .25, 'reciprocal_care': .10,
     'rootedness': .15, 'purpose_beyond_self': .15, 'slow_presence': .10}
N = {'near': 30, 'above': 66}
D = os.path.expanduser('~/llm-distillery/datasets/training/belonging_v1/')
exclude = set(open(sys.argv[1]).read().split())
pool = {'near': [], 'above': []}
for split in ('train', 'val', 'test'):
    for line in open(D + split + '.jsonl'):
        r = json.loads(line)
        lab = dict(zip(r['dimension_names'], r['labels']))
        if set(lab) != set(W):
            raise SystemExit(f'unexpected dimensions {sorted(lab)}')
        wa = sum(W[k] * v for k, v in lab.items())
        if lab['community_fabric'] < 3.0:
            wa = min(wa, 3.42)
        if wa < 3.5 or r['id'] in exclude:
            continue
        pool['near' if wa < 4.0 else 'above'].append(dict(id=r['id'], split=split, oracle_wa=round(wa, 4),
                                                          title=r.get('title'), url=r.get('url'),
                                                          source=r.get('source'), content=r.get('content')))
rng = random.Random(20261002)
for s in ('near', 'above'):
    pool[s].sort(key=lambda r: r['id'])
    for r in rng.sample(pool[s], N[s]):
        print(json.dumps(dict(r, stratum=s, n_in_stratum=len(pool[s])), ensure_ascii=False))
print({s: len(p) for s, p in pool.items()}, file=sys.stderr)
