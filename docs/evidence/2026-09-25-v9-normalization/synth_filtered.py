#!/usr/bin/env python3
"""Write adj3's (= v9's) week of production scores in NexusMind's filtered_*.jsonl shape, so
fit_normalization.py --data-dir can fit v9's CDF before go-live (FILTER_PLAYBOOK §6: fit at deploy
from a production-representative rescore, not the enriched training set).

Source: b650 RTX 5090 dumps of every stage2 id in sadalsuud's human_thriving filtered files
filtered_20260918_145649 -> filtered_20260925_093350 (42 cycles), minus the live audit's training-
overlap exclusions (same rule as its build_panel.py). raw_weighted_average = the gate's own
load_scores(spec=...) on the calibrated per-dim scores: the computation whose v8 passer set matched
production v8 on all but 2 of 1,351 (docs/evidence/2026-09-25-v8-adj3-live-audit/groups.json).
"""
# design-weights: NOT APPLICABLE. This is the production week itself, not a design-weighted draw;
# it publishes no rate, only rows for the CDF fit.
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from scripts.gate.ground_truth_gate import load_scores, load_scoring_spec  # noqa: E402

D = REPO / "datasets/audit/ht_2026-09-25"
OUT = D / "v9_synth_filtered"
spec = load_scoring_spec(REPO / "filters/human_thriving/v9/config.yaml")
if spec is None:
    raise SystemExit("config spec failed to load")
sc = {}
for p in sorted(D.glob("scores/v8_adj3/*/scores_calibrated.jsonl")):
    sc.update(load_scores(p, spec=spec))
excl = set()
for d in ["human_thriving_v8", "human_thriving_v8_adj1", "human_thriving_v8_adj2", "human_thriving_v8_adj3"]:
    for s in ["train", "val", "test"]:
        excl |= {json.loads(l)["id"] for l in open(REPO / f"datasets/training/{d}/{s}.jsonl")}
excl |= {json.loads(l)["id"] for l in open(REPO / "docs/evidence/2026-09-24-thriving-more-positives/sample.jsonl")}
ids = sorted(i for i in sc if i not in excl)
live = json.loads((REPO / "docs/evidence/2026-09-25-v8-adj3-live-audit/groups.json").read_text())
if len(ids) != live["audit_ids"]:
    raise SystemExit(f"{len(ids)} ids != live audit's {live['audit_ids']}")
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "filtered_v9week_20260918_20260925.jsonl", "w") as w:
    for i in ids:
        v = sc[i]
        w.write(json.dumps({"id": i, "nexus_mind_attributes": {"human_thriving": {
            "version": "9.0", "weighted_average": v, "raw_weighted_average": v, "stage_used": "stage2"}}}) + "\n")
print(f"{len(ids)} rows, {sum(sc[i] >= 4.5 for i in ids)} at >= 4.5 -> {OUT}")
