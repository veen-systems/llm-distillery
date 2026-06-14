#!/usr/bin/env python3
"""Roll up the multi-model blind panel vs the obituary model's prediction."""
import json, collections
from pathlib import Path

HERE = Path(__file__).parent
ws = {json.loads(l)["id"]: json.loads(l) for l in open(HERE / "worksheet_obit.jsonl", encoding="utf-8")}
grades = [json.loads(l) for l in open(HERE / "grades_panel_obit.jsonl", encoding="utf-8")]

MODELS = ["gemma3:27b", "qwen3:14b", "phi4:14b", "gemini-2.5-flash"]
by_article = collections.defaultdict(dict)
for g in grades:
    by_article[g["id"]][g["model"]] = g

def majority(verdicts):
    # map borderline -> not_obituary's neighbor? keep 3-way, tie => 'split'
    c = collections.Counter(verdicts)
    top, n = c.most_common(1)[0]
    if list(c.values()).count(n) > 1:  # tie
        # obituary breaks toward caution only if it's among the tied-top
        return "split"
    return top

# per-model tally
print("=== per-model verdict tally ===")
for m in MODELS:
    c = collections.Counter(by_article[i].get(m, {}).get("verdict", "missing") for i in ws)
    print(f"  {m:<18} {dict(c)}")

# per-article rollup
rows = []
for i, w in ws.items():
    vs = [by_article[i].get(m, {}).get("verdict", "missing") for m in MODELS]
    maj = majority(vs)
    n_obit = vs.count("obituary")
    rows.append({"id": i, "bucket": w["bucket"], "lens": w.get("filter"),
                 "obit_score": w["obit_score"], "title": w.get("title"),
                 "verdicts": dict(zip(MODELS, vs)), "majority": maj, "n_obituary_votes": n_obit})

# block precision: of model-flagged (block bucket), how many panel-majority = obituary
block = [r for r in rows if r["bucket"] == "block"]
block_obit = [r for r in block if r["majority"] == "obituary"]
block_split = [r for r in block if r["majority"] == "split"]
print(f"\n=== BLOCK bucket (model score >=0.90 -> model says OBITUARY), n={len(block)} ===")
print(f"  panel majority = obituary   : {len(block_obit)}  (true positives)")
print(f"  panel majority = not/border : {len(block)-len(block_obit)-len(block_split)}  (FALSE POSITIVES)")
print(f"  panel split (tie)           : {len(block_split)}")
if block:
    print(f"  >>> block precision (lower bound) = {len(block_obit)}/{len(block)} = {len(block_obit)/len(block):.0%}")

# recall check
rc = [r for r in rows if r["bucket"] == "recall_chk"]
rc_obit = [r for r in rc if r["majority"] == "obituary"]
print(f"\n=== RECALL-CHECK bucket (model score <0.70 -> model says NOT, but death-adjacent), n={len(rc)} ===")
print(f"  panel majority = obituary   : {len(rc_obit)}  (FALSE NEGATIVES the model missed)")

# unanimity
unanimous = sum(1 for r in rows if len(set(r['verdicts'].values()))==1)
print(f"\n=== panel cohesion: {unanimous}/{len(rows)} articles unanimous across 4 models ===")

# disagreement set for interactive adjudication: model-vs-panel conflict OR panel split
adjudicate = []
for r in rows:
    model_says_obit = r["bucket"] == "block"
    panel_obit = r["majority"] == "obituary"
    conflict = (model_says_obit != panel_obit) or (r["majority"] == "split") or (0 < r["n_obituary_votes"] < 4)
    if conflict:
        adjudicate.append(r)
print(f"\n=== {len(adjudicate)} articles need adjudication (model<->panel conflict or panel not unanimous) ===")

json.dump({"rows": rows, "adjudicate_ids": [r["id"] for r in adjudicate],
           "block_precision_lb": (len(block_obit)/len(block) if block else None)},
          open(HERE / "rollup_obit.json", "w"), indent=2, ensure_ascii=False)
print(f"\nwrote rollup_obit.json")
