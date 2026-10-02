"""Belonging pilot v3 (enriched): draw the strata from retrieve_v3.py's scores (run on b650).

    python3 draw_pilot_v3.py /tmp/ret_v3/scores.jsonl /tmp/bel_corpus.jsonl > pilot3_rows.jsonl

Candidates = the top 2,000 non-off-lens rows by nearest-seed similarity. Strata (PREREGISTRATION_v3.md):
retrieved_hi (raw >= 4.0) 50, retrieved_lo (raw < 4.0) 20, random_pass (raw >= 4.0, outside the candidates) 30.
Every row carries n_in_stratum. Seed fixed. Pool sizes go to stderr."""
import json, random, sys

N = {'retrieved_hi': 50, 'retrieved_lo': 20, 'random_pass': 30}
scores = [json.loads(l) for l in open(sys.argv[1])]
ok = sorted((s for s in scores if not s['off_lens']), key=lambda s: (-s['maxsim'], s['id']))
cand = ok[:2000]
cand_ids = {s['id'] for s in cand}
pool = {'retrieved_hi': [s for s in cand if (s['raw'] or 0) >= 4.0],
        'retrieved_lo': [s for s in cand if (s['raw'] or 0) < 4.0],
        'random_pass': [s for s in ok if s['id'] not in cand_ids and (s['raw'] or 0) >= 4.0]}
rng = random.Random(20261004)
picked = {}
for name in ('retrieved_hi', 'retrieved_lo', 'random_pass'):
    p = sorted(pool[name], key=lambda s: s['id'])
    for s in rng.sample(p, N[name]):
        picked[s['id']] = dict(stratum=name, n_in_stratum=len(p), maxsim=s['maxsim'], raw=s['raw'])
for line in open(sys.argv[2]):
    r = json.loads(line)
    if r['id'] in picked:
        print(json.dumps(dict(id=r['id'], title=r['title'], url=r['url'], source=r['source'], content=r['content'],
                              **picked[r['id']]), ensure_ascii=False))
print({k: len(v) for k, v in pool.items()}, file=sys.stderr)
