"""Score a rows file with one belonging package on b650 (PREREGISTRATION.md sections 2-3). comp_check.py's `score`,
with the rows file and output path as arguments (its output path is fixed, and v3's file there is c2c's).

    PYTHONPATH=. HF_HUB_OFFLINE=1 venv-prodparity/bin/python docs/evidence/2026-10-15-belonging-c2d/score_rows.py \
        ROWS.jsonl filters/belonging/<pkg> OUT.jsonl

Output: a meta line (package, fingerprint, n, device), then id, stage_used, raw per row, in the rows file's order.
"""
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-03-belonging-heldout"))
import torch
import gate

rows_path, package, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
if not torch.cuda.is_available():
    raise SystemExit("REFUSED: no CUDA (every package is scored on b650 GPU)")
if out.exists():
    raise SystemExit(f"REFUSED: {out} exists")
rows = [json.loads(l) for l in open(rows_path, encoding="utf-8") if l.strip()]
if len({r["id"] for r in rows}) != len(rows):
    raise SystemExit("REFUSED: duplicate ids")
pkg = (ROOT / package).resolve()
scorer = gate.scorer_for(pkg)(use_prefilter=False)
gate.assert_loads_from(pkg, scorer)
res = scorer.score_batch([dict(id=r["id"], title=r["title"], content=r["content"], url=r.get("url"),
                               source=r.get("source")) for r in rows])
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as f:
    f.write(json.dumps(dict(meta=dict(package=package, fingerprint=gate.pkg_fingerprint(pkg)[0], n=len(rows),
                                      device=torch.cuda.get_device_name(0)))) + "\n")
    for r, s in zip(rows, res):
        f.write(json.dumps(dict(id=r["id"], stage_used=s.get("stage_used"), raw=s.get("weighted_average"))) + "\n")
print(f"wrote {out}: {Counter(s.get('stage_used') for s in res)}")
