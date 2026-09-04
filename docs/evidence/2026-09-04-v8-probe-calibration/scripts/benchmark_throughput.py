"""Per-article throughput of a probe configuration, model load excluded.

Measured 2026-09-04 on b650-gpu over the 660-row test split:

    e5-small  GPU     3.74 ms/article      e5-small  CPU    47.2 ms
    e5-large  GPU    26.79 ms/article      e5-large  CPU   511.2 ms
    student   GPU    43.70 ms/article      student   CPU  ~1455 ms

⚠️ These corrected an earlier claim in this directory that the two-stage design "saves
nothing" — that comparison had the probe on CPU and the student on GPU. On GPU the probe is
11.7x cheaper than the student.

⚠️ The screen still saves only ~2.5% at the ADOPTED threshold, because routing is ~89%:
3.74 + 0.89*43.70 = 42.6 ms against 43.70 for student-on-everything. At the probe's own
selected 2.825 (routing ~52%) it would be ~26.5 ms.

⚠️ b650-gpu is not gpu-server. Ratios should travel; absolute numbers may not.

    PYTHONPATH=. python benchmark_throughput.py <hf-model> <cpu|cuda> <probe.pkl>
"""
import json, time, sys
sys.path.insert(0, ".")
arts = [json.loads(l) for l in open("datasets/training/human_thriving_v8/test.jsonl", encoding="utf-8")]
N = len(arts)
from filters.common.embedding_stage import EmbeddingStage
from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer as C
model, device, pth = sys.argv[1], sys.argv[2], sys.argv[3]
st = EmbeddingStage(embedding_model_name=model, probe_path=pth, threshold=1.75,
                    dimension_weights=C.DIMENSION_WEIGHTS,
                    dimension_names=C.DIMENSION_NAMES, device=device)
st.screen_batch(arts[:32])
t = time.perf_counter(); st.screen_batch(arts, batch_size=64); d = time.perf_counter()-t
print("RESULT %-22s %8.1f s / %d = %7.2f ms/article" % (model.split("-")[-1]+" "+device, d, N, 1000*d/N))
