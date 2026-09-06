"""CPU vs CUDA device term for human_thriving v8, on the 660-row test split.

Reuses ground_truth_gate's OWN loader (load_scores with the config spec) so the
quantity compared is the one the gate thresholds, not a reimplementation of it.
"""
import sys, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec_ = importlib.util.spec_from_file_location("gt_gate", ROOT/"scripts/gate/ground_truth_gate.py")
g = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(g)

spec = g.load_scoring_spec(ROOT/"filters/human_thriving/v8/config.yaml")
thr = g.load_medium_threshold(ROOT/"filters/human_thriving/v8/config.yaml")
print(f"threshold={thr}  gk_cap={spec['gk_cap']}")

for arm in ("scores_calibrated", "scores_raw"):
    cpu = g.load_scores(ROOT/f"datasets/gate/ht_v8_test_cpu/{arm}.jsonl", spec)
    cud = g.load_scores(ROOT/f"datasets/gate/ht_v8_test_cuda/{arm}.jsonl", spec)
    ids = sorted(set(cpu) & set(cud))
    assert len(ids) == 660 == len(cpu) == len(cud), (len(ids), len(cpu), len(cud))
    d = sorted(abs(cpu[i] - cud[i]) for i in ids)
    identical = sum(1 for x in d if x == 0.0)
    flips = [i for i in ids if (cpu[i] >= thr) != (cud[i] >= thr)]
    def q(p): return d[min(len(d)-1, int(p*len(d)))]
    print(f"\n{arm}:  bit-identical {identical}/660 ({identical/6.60:.1f}%)")
    print(f"  |delta| p50 {q(.50):.4f}  p90 {q(.90):.4f}  p99 {q(.99):.4f}  MAX {d[-1]:.4f}")
    print(f"  verdict flips at {thr}: {len(flips)}  {flips}")
    surf_cpu = sum(1 for i in ids if cpu[i] >= thr)
    surf_cud = sum(1 for i in ids if cud[i] >= thr)
    print(f"  surfaced: cpu {surf_cpu}  cuda {surf_cud}")
