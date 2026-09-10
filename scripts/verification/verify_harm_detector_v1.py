"""Contract check for harm detector v1 — run it wherever the detector is served.

Three claims, all easy to assume and NONE of them proven by the build succeeding:
  (a) the shipped inference class recomputes what `build_v1.py` computed in-process —
      "I tidied the script into a module" produces a DIFFERENT program, and the tidy-up
      feels cosmetic so it never gets re-run;
  (b) the score does not depend on the device it is served on — the Gemma student's
      CPU->CUDA term is 0.1956, so this cannot be assumed, it has to be measured HERE;
  (c) the stamp carries no verdict key — a threshold creeping into the artifact is how
      "stamp only" quietly becomes "blocks things".

⚠️ `panel_probs_ensemble` is stored rounded to 6 decimals, so a |Δ| of ~1e-6 against the
builder is STORAGE PRECISION, not a model difference. Bit-identity is not the bar; verdict
flips at plausible gates are.

Needs `datasets/panel/panel_content.jsonl` (gitignored) and a built
`filters/common/harm_detector/v1/models/`. Requires GPU only for the cuda arm.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from filters.common.harm_detector.v1.inference import HarmDetectorV1

report = json.loads(Path("filters/common/harm_detector/v1/calibration_report.json").read_text())
built = report["panel_probs_ensemble"]
rows = {json.loads(l)["id"]: json.loads(l)
        for l in open("datasets/panel/panel_content.jsonl", encoding="utf-8")}
ids = list(built.keys())
arts = [rows[i] for i in ids]

print("provenance:", report["provenance"]["commit"][:12], report["provenance"]["worktree"])
for device in ("cuda", "cpu"):
    d = HarmDetectorV1(device=device)
    got = d.batch_score(arts)
    diffs = [abs(g - built[i]) for g, i in zip(got, ids)]
    mx = max(diffs)
    n_exact = sum(1 for x in diffs if x == 0.0)
    print(f"{device:4}  max |Δ| vs builder {mx:.3e}   bit-identical {n_exact}/{len(ids)}")
    if device == "cuda":
        cuda_scores = got
    else:
        dev = [abs(a - b) for a, b in zip(cuda_scores, got)]
        print(f"      CPU vs CUDA: max |Δ| {max(dev):.3e}   bit-identical "
              f"{sum(1 for x in dev if x == 0.0)}/{len(ids)}")
        # Does the device change any decision at any plausible gate?
        for t in (0.30, 0.50, 0.70, 0.85):
            fc = sum(1 for s in cuda_scores if s >= t); fp = sum(1 for s in got if s >= t)
            flips = sum(1 for a, b in zip(cuda_scores, got) if (a >= t) != (b >= t))
            print(f"      gate {t:.2f}: cuda flags {fc}, cpu flags {fp}, verdict flips {flips}")
    # stamp shape
    st = d.stamp(arts[0])
    assert set(st) == {"harm_is_subject_score", "harm_detector_version"}, st
    assert "verdict" not in json.dumps(st) and "is_harm" not in json.dumps(st)
print("stamp shape OK: score + version only, no verdict key")
