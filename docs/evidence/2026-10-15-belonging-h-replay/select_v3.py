"""Step 3 of PREREGISTRATION.md: per build and per order (H, control), the first 30 v3-stamped rows, every skipped
row counted by its stamp. The baseline's select_v3.py rule, applied to both orders. Reads builds.json and the lab
file extract/rows.jsonl (cited in MANIFEST.json).

    python3 docs/evidence/2026-10-15-belonging-h-replay/select_v3.py > .../selection.json
    python3 docs/evidence/2026-10-15-belonging-h-replay/select_v3.py --dated > .../selection_dated.json  (deviation)
"""
import collections, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()
ROWS = LAB / "experiments/2026-10-15-belonging-h-replay/extract/rows.jsonl"
DATED = "--dated" in sys.argv
rows = {}
for f in [ROWS] + ([ROWS.parent.parent / "extract-dated/rows.jsonl"] if DATED else []):
    for l in f.read_text(encoding="utf-8").splitlines():
        if l.strip():
            rows.setdefault(json.loads(l)["id"], json.loads(l))
out = {}
for build, b in json.loads((HERE / ("builds_dated.json" if DATED else "builds.json")).read_text()).items():
    if build == "_meta":
        continue
    out[build] = {"population": b["population"], "removal_unknown": b["removal_unknown"]}
    for name in ("H", "control"):
        ids = b[name]
        v3 = [i for i in ids if rows[i]["version"] == "3.0"]
        end = ids.index(v3[29]) + 1 if len(v3) >= 30 else len(ids)
        skipped = collections.Counter(str(rows[i]["version"]) for i in ids[:end] if rows[i]["version"] != "3.0")
        top = v3[:30]
        out[build][name] = {"n": len(top), "in_range": len(v3) >= 30, "v3_in_top60": len(v3),
                            "skipped_by_stamp": dict(sorted(skipped.items())),
                            "under_24h": sum(i in set(b["under_24h"]) for i in top),
                            "top30_v3": top}
print(json.dumps(out, indent=1))
