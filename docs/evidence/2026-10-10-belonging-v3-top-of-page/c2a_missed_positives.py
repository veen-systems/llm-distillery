"""0a step 1 (2026-10-12): which held-out set-2 positives c2a missed at op 4.0.

Uses gate2.py's OWN labelled()/load_scores()/is_in(), so the population is the gate's, and the c2a score
files from the lab pull of b650 (2026-10-10). Run from the repo root with .venv/bin/python. Output:
c2a_missed_positives.txt beside this file.
"""
import sys, json, importlib.util, os
EV = "docs/evidence/2026-10-08-belonging-heldout2"
sys.path.insert(0, EV); sys.path.insert(0, ".")
spec = importlib.util.spec_from_file_location("gate2", f"{EV}/gate2.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
lab = g.labelled()
SD = os.path.expanduser("~/lab/llm-distillery/inbox/b650-gpu/2026-10-10/llm-distillery/datasets/belonging_gate2")
out = {}
for order in ("forward", "reversed"):
    _, c = g.load_scores(f"{SD}/v1_c2a_{order}.jsonl", order, lab)
    out[order] = c
pos = [i for i, x in lab.items() if x["label"] == "pos"]
rows = {r["id"]: r for r in g.H.rows()}
cf = out["forward"]
caught = [i for i in pos if g.is_in(cf[i], 4.0)]
missed = [i for i in pos if not g.is_in(cf[i], 4.0)]
print(f"pos {len(pos)}  caught {len(caught)}  missed {len(missed)}  (gate said k=43/63)")
agree = all(g.is_in(cf[i], 4.0) == g.is_in(out["reversed"][i], 4.0) for i in pos)
print("forward/reversed agree on every positive:", agree)
for i in sorted(missed, key=lambda i: cf[i]["weighted_average"]):
    r = rows[i]
    print(f"{cf[i]['stage_used']:10s} {cf[i]['weighted_average']:5.2f}  {r.get('band','?'):4s}  {(r.get('title') or '')[:110]}")
