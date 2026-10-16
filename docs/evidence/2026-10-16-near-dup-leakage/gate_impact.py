"""Do A1's leaked rows touch human_thriving v9's gate verdicts? (#176, PREREGISTRATION.md § Reading the pairs)

    .venv/bin/python docs/evidence/2026-10-16-near-dup-leakage/gate_impact.py > .../gate_impact.txt

For each LEAK (classes a/b, read 2026-10-16 in README.md): the adjudicated label's weighted average (the gate's
PRIMARY labels, human_thriving_v8_adj1/test.jsonl) and v9's calibrated weighted score (the gate's own per-row output,
datasets/gate/ht_v8_adj_2026-09-25/adj3/scores_calibrated.jsonl), both against the 4.5 op-point. A leak that is a
true negative on both sides changes no TP/FP. Gatekeepers are not applied: they only lower a score, so they cannot
turn a below-op row positive. A leak id missing from either file RAISES.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
OP = 4.5
LEAKS = {  # id -> class (README.md)
    "community_social_hackernews_front_277debae3939": "b (syndicated, text 0.99)",
    "east_asian_japan_today_7c585120c422": "b (wire copy, text 0.91)",
    "east_asian_yonhap_en_8e7f2a520a1a": "b (agency rewrite, text 0.88)",
    "science_helmholtz_23e36b84ee95": "b? (press release vs repost, text 0.28)",
}
dims = yaml.safe_load(open(ROOT / "filters/human_thriving/v9/config.yaml"))["scoring"]["dimensions"]
w = {d: dims[d]["weight"] for d in dims}


def rows(p):
    return {r["id"]: r for r in map(json.loads, open(ROOT / p)) if r["id"] in LEAKS}


lab = rows("datasets/training/human_thriving_v8_adj1/test.jsonl")
sco = rows("datasets/gate/ht_v8_adj_2026-09-25/adj3/scores_calibrated.jsonl")
miss = [i for i in LEAKS if i not in lab or i not in sco]
if miss:
    raise SystemExit(f"FATAL: leak ids missing from the gate files: {miss}")
changed = 0
print(f"op-point {OP}; weighted averages, weights from filters/human_thriving/v9/config.yaml")
for i, c in LEAKS.items():
    y = sum(v * w[d] for v, d in zip(lab[i]["labels"], lab[i]["dimension_names"]))
    s = sum(sco[i]["scores"][d] * w[d] for d in w)
    cell = ("TP" if s >= OP else "FN") if y >= OP else ("FP" if s >= OP else "TN")
    changed += cell != "TN"
    print(f"  {i}  class {c}  label {y:.2f}  v9 {s:.2f}  -> {cell}")
print(f"leaks that are not true negatives: {changed} of {len(LEAKS)}")
