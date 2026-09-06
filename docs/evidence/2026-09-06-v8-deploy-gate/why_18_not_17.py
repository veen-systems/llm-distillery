"""Is EXP-015's 18 TP vs the gate's 17 a DEVICE difference, as STATUS.md says?"""

# design-weights: NOT READ, and the finding does not need them. The claim this script
# supports is "0 rows move across 4.5" -- between devices, and between the plain dot product
# and the gatekeepered, clamped one. Whether a given row crosses a threshold is a property of
# that row, so it is invariant under any reweighting: a weight can change how much a flip
# COUNTS, and there are none to count. ⛔ The confusion counts printed alongside are SAMPLE
# counts on a 25.1x design-weighted split (weights in
# datasets/scored/human_thriving_v8/corpus.jsonl) and are not population estimates -- they are
# here to show the two arms landing on the same matrix, not to be quoted as rates. The gate
# report states the same caveat for the rates it publishes.
import json, importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
s_ = importlib.util.spec_from_file_location("g", ROOT/"scripts/gate/ground_truth_gate.py")
g = importlib.util.module_from_spec(s_); s_.loader.exec_module(g)
spec = g.load_scoring_spec(ROOT/"filters/human_thriving/v8/config.yaml")
dims = spec["dims"]; W = spec["weights"]
print("dims", dims); print("gatekeeper", spec["gk_dim"], spec["gk_min"], spec["gk_cap"])

truth = g.load_labels(ROOT/"datasets/training/human_thriving_v8/test.jsonl", spec=spec)

def confusion(pred, thr=4.5):
    ids = sorted(set(truth) & set(pred))
    tp = sum(1 for i in ids if pred[i] >= thr and truth[i] >= thr)
    fp = sum(1 for i in ids if pred[i] >= thr and truth[i] < thr)
    fn = sum(1 for i in ids if pred[i] < thr and truth[i] >= thr)
    tn = len(ids) - tp - fp - fn
    return tp, fp, fn, tn

for device in ("cuda", "cpu"):
    rows = [json.loads(l) for l in open(ROOT/f"datasets/gate/ht_v8_test_{device}/scores_raw.jsonl")]
    plain = {r["id"]: sum(r["scores"][d]*W[d] for d in dims) for r in rows}          # EXP-015's dot product
    gated = g.load_scores(ROOT/f"datasets/gate/ht_v8_test_{device}/scores_raw.jsonl", spec=spec)  # the gate's
    print(f"\n{device}: plain dot product      TP {confusion(plain)[0]} FP {confusion(plain)[1]} "
          f"FN {confusion(plain)[2]} TN {confusion(plain)[3]}")
    print(f"{device}: with gatekeeper+clamp  TP {confusion(gated)[0]} FP {confusion(gated)[1]} "
          f"FN {confusion(gated)[2]} TN {confusion(gated)[3]}")
    moved = [i for i in plain if (plain[i] >= 4.5) != (gated[i] >= 4.5)]
    print(f"{device}: rows the gatekeeper moves across 4.5: {len(moved)} {moved}")
    for i in moved:
        r = next(x for x in rows if x["id"] == i)
        print(f"   {i}: plain {plain[i]:.4f} gated {gated[i]:.4f} evidence_level "
              f"{r['scores'][spec['gk_dim']]:.4f} truth {truth[i]:.4f}")
