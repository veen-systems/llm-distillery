"""Oracle-path gate verdict per (package, row), via batch_scorer's OWN loader + wrapper.

Decision 0 (NexusMind#284) evidence. Run once on a tree WITH the per-lens prefilters
(`git worktree add /tmp/ld-before fe6c018`) and once on a tree without them, same RAW
file, then diff the two outputs. Writes per-row verdicts (no article text).

Usage (from the repo root of the tree under test):
    PYTHONPATH=. .venv/bin/python <this file> RAW.jsonl OUT.json
"""
import json
import sys
from pathlib import Path

from ground_truth.batch_scorer import load_filter_package, make_oracle_prefilter
from filters.common.base_prefilter import BasePreFilter

PACKAGES = [
    "filters/uplifting/v7",
    "filters/cultural_discovery/v5",
    "filters/cultural_discovery/v6",
    "filters/belonging/v1",
    "filters/nature_recovery/v4",
    "filters/solutions/v6",
    "filters/investment_risk/v6",
    "filters/human_thriving/v9",  # control: never had a prefilter.py
]

raw, out = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(raw, encoding="utf-8") if l.strip()]
res = {"n_rows": len(rows), "packages": {}}
for pkg in PACKAGES:
    obj, _, _ = load_filter_package(Path(pkg))
    gate = make_oracle_prefilter(obj)
    verdicts, reasons = [], []
    for a in rows:
        verdicts.append(bool(gate(a)))
        # why: the lens reason if a lens object exists, else the base checks
        if obj is not None:
            reasons.append(obj.apply_filter(a)[1])
        else:
            reasons.append(None)
    floor = [bool(BasePreFilter.check_content_length(a)[0] and BasePreFilter.validate_article(a)[0]) for a in rows]
    res["packages"][pkg] = {
        "has_prefilter_obj": obj is not None,
        "verdicts": verdicts,
        "reasons": reasons,
        "floor_and_valid": floor,
        "ids": [a.get("id") for a in rows],
    }
    print(pkg, "obj" if obj else "none", "pass", sum(verdicts), "/", len(rows))
json.dump(res, open(out, "w"))
