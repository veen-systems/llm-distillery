"""Diff two gate_verdicts.py outputs into gate_verdicts_summary.json (counts only).

Usage: python summarize.py BEFORE.json AFTER.json OUT.json
"""
import collections
import json
import sys

before, after, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
b = json.load(open(before))
a = json.load(open(after))
if b["n_rows"] != a["n_rows"]:
    raise SystemExit("before/after ran on different files")
out = {
    "source": {
        "host": "sadalsuud",
        "path": "/home/jeroen/local_dev/NexusMind/data/raw/content_items_20261001_080513.jsonl",
        "sha256": "3b1efcc7414bcb7deec3ead327cf56f68a5e64da96f62bbfbba1eabf292dc784",
        "rows": b["n_rows"],
        "stage": "pre-enrichment (NexusMind data/raw)",
        "cycle": "2026-10-01 08:05 CEST collection",
    },
    "packages": {},
}
for p in b["packages"]:
    B, A = b["packages"][p], a["packages"][p]
    if B["ids"] != A["ids"]:
        raise SystemExit(f"{p}: row order differs between runs")
    out["packages"][p] = {
        "before_has_lens_object": B["has_prefilter_obj"],
        "after_has_lens_object": A["has_prefilter_obj"],
        "floor_and_valid_pass": sum(B["floor_and_valid"]),
        "before_pass": sum(B["verdicts"]),
        "after_pass": sum(A["verdicts"]),
        "newly_pass": sum(1 for x, y in zip(B["verdicts"], A["verdicts"]) if not x and y),
        "newly_block": sum(1 for x, y in zip(B["verdicts"], A["verdicts"]) if x and not y),
        "floor_verdicts_identical": B["floor_and_valid"] == A["floor_and_valid"],
        "before_lens_block_reasons": dict(collections.Counter(
            r for r, v, f in zip(B["reasons"], B["verdicts"], B["floor_and_valid"]) if f and not v
        ).most_common()),
    }
json.dump(out, open(out_path, "w"), indent=1)
