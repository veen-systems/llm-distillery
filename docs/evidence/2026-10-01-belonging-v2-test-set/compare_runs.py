"""Score oracle runs on the belonging v2 test set against its labels.

    PYTHONPATH=. .venv/bin/python docs/evidence/2026-10-01-belonging-v2-test-set/compare_runs.py \
        v1=datasets/scored/belonging_v1_control_20261001/belonging \
        v2=datasets/scored/belonging_v2_draft1_20261001/belonging

Weighted average = BaseBelongingScorer (v1) weights + its community_fabric gatekeeper, the scoring code
both prompts feed. Rows are joined on url; a run missing any scorable row of the set raises.
Prints, per run: P rows >= op-point (recall side) and F rows >= op-point (the specificity failures), by
stratum; then every row whose verdict differs between the runs."""
import collections, glob, importlib.util, json, sys

OP = 4.0
spec = importlib.util.spec_from_file_location('bs', 'filters/belonging/v1/base_scorer.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
C = mod.BaseBelongingScorer
W, G, GMIN, GCAP = C.DIMENSION_WEIGHTS, C.GATEKEEPER_DIMENSION, C.GATEKEEPER_MIN, C.GATEKEEPER_CAP

def wa(analysis):
    s = {d: float(analysis[d]['score']) for d in W}
    v = sum(s[d] * W[d] for d in W)
    return min(v, GCAP) if s[G] < GMIN else v

test = {json.loads(l)['url']: json.loads(l) for l in open('datasets/belonging_v2_test/test_set_full.jsonl')}
scorable = {u for u, r in test.items() if r['content_length'] >= 300}
runs = {}
for arg in sys.argv[1:]:
    name, path = arg.split('=', 1)
    rows = [json.loads(l) for f in sorted(glob.glob(f'{path}/scored_batch_*.jsonl')) for l in open(f)]
    got = {r['url']: wa(r['belonging_analysis']) for r in rows if r['url'] in test}
    if scorable - set(got):
        raise SystemExit(f'{name}: {len(scorable - set(got))} scorable rows not scored')
    runs[name] = got

for name, got in runs.items():
    print(f'== {name}  (op-point {OP}; n = scorable rows)')
    for lab in 'PFB':
        us = [u for u in scorable if test[u]['label'] == lab]
        print(f'  {lab}: {sum(got[u] >= OP for u in us)}/{len(us)} at or above op-point')
    by = collections.defaultdict(list)
    for u in scorable:
        if test[u]['label'] == 'F':
            by[test[u]['stratum']].append(got[u] >= OP)
    print('  F above op-point by stratum: ' + ', '.join(f'{k} {sum(v)}/{len(v)}' for k, v in sorted(by.items())))

names = list(runs)
if len(names) == 2:
    a, b = names
    print(f'\n== verdict changes {a} -> {b} (label | {a} | {b} | title)')
    for u in sorted(scorable, key=lambda u: (test[u]['label'], -runs[b][u])):
        if (runs[a][u] >= OP) != (runs[b][u] >= OP):
            print(f"  {test[u]['label']} | {runs[a][u]:5.2f} | {runs[b][u]:5.2f} | {test[u]['title'][:80]}")
    print(f'\n== {b}: F rows still at or above op-point')
    for u in sorted(scorable, key=lambda u: -runs[b][u]):
        if test[u]['label'] == 'F' and runs[b][u] >= OP:
            print(f"  {runs[b][u]:5.2f} | {test[u]['stratum'][:14]} | {test[u]['title'][:80]}")
    print(f'\n== {b}: P rows below op-point')
    for u in scorable:
        if test[u]['label'] == 'P' and runs[b][u] < OP:
            print(f"  {runs[b][u]:5.2f} | {test[u]['title'][:80]}")
