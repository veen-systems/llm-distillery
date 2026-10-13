"""Step 1c of PREREGISTRATION.md: per build, the first 30 v3-stamped rows in site order, and every skipped row
counted by its stamp. Reads builds.json and the lab file extract/rows.jsonl (cited in MANIFEST.json).

    python3 docs/evidence/2026-10-13-belonging-daily-baseline/select_v3.py > .../selection.json
"""
import collections, json, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()
ROWS = LAB / "experiments/2026-10-13-belonging-daily-baseline/extract/rows.jsonl"
rows = {json.loads(l)["id"]: json.loads(l) for l in ROWS.read_text(encoding="utf-8").splitlines() if l.strip()}
out = {}
for build, ids in json.loads((HERE / "builds.json").read_text()).items():
    v3 = [i for i in ids if rows[i]["version"] == "3.0"]
    end = ids.index(v3[29]) + 1 if len(v3) >= 30 else len(ids)      # through the 30th v3 row, else the whole top 60
    skipped = collections.Counter(str(rows[i]["version"]) for i in ids[:end] if rows[i]["version"] != "3.0")
    out[build] = {"n": min(30, len(v3)), "in_range": len(v3) >= 30, "v3_in_top60": len(v3),
                  "skipped_by_stamp": dict(sorted(skipped.items())),
                  "skipped_scope": "through the 30th v3 row" if len(v3) >= 30 else "whole top 60 (fewer than 30 v3)",
                  "top30_v3": v3[:30]}
print(json.dumps(out, indent=1))
