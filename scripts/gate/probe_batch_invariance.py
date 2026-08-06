"""Does the probe's score depend on the batch an article lands in? (#95 analogue)

If it does, every A/B number in cd v6's STATUS.md has an uncharacterised noise
floor and per-article decisions near the threshold are not reproducible.
"""
import json
import random

from filters.common.embedding_stage import EmbeddingStage
from filters.cultural_discovery.v6.base_scorer import BaseCulturalDiscoveryScorer as S

st = EmbeddingStage(
    "intfloat/multilingual-e5-small",
    "filters/cultural_discovery/v6/probe/embedding_probe_e5small.pkl",
    2.50, S.DIMENSION_WEIGHTS, S.DIMENSION_NAMES,
)

rows = [json.loads(l) for l in open("datasets/training/cultural-discovery_v5/test.jsonl")]
arts = [{"title": r["title"], "content": r["content"]} for r in rows]

# Arrangement A: the harness's own chunking (256-article chunks, encode batch 64)
a = []
for i in range(0, len(arts), 256):
    a.extend(st.screen_batch(arts[i:i + 256], batch_size=64))

# Arrangement B: different chunk size, different encode batch, shuffled order,
# then mapped back to original positions.
idx = list(range(len(arts)))
random.Random(7).shuffle(idx)
shuffled = [arts[i] for i in idx]
b_sh = []
for i in range(0, len(shuffled), 97):
    b_sh.extend(st.screen_batch(shuffled[i:i + 97], batch_size=13))
b = [None] * len(arts)
for pos, orig in enumerate(idx):
    b[orig] = b_sh[pos]

# Arrangement C: one article at a time — batch of size 1, no neighbours at all.
c = [st.screen_batch([x], batch_size=1)[0] for x in arts[:120]]

dab = [abs(x.weighted_avg - y.weighted_avg) for x, y in zip(a, b)]
dac = [abs(a[i].weighted_avg - c[i].weighted_avg) for i in range(len(c))]

flip_ab = sum((x.weighted_avg >= 2.50) != (y.weighted_avg >= 2.50) for x, y in zip(a, b))
flip_ac = sum((a[i].weighted_avg >= 2.50) != (c[i].weighted_avg >= 2.50) for i in range(len(c)))

print(f"n = {len(arts)}")
print(f"A vs B (shuffled, chunk 97, encode batch 13):")
print(f"  max |delta| = {max(dab):.6f}   mean = {sum(dab)/len(dab):.8f}")
print(f"  threshold flips at 2.50: {flip_ab}")
print(f"A vs C (batch of 1, first 120):")
print(f"  max |delta| = {max(dac):.6f}   mean = {sum(dac)/len(dac):.8f}")
print(f"  threshold flips at 2.50: {flip_ac}")

near = sum(1 for x in a if abs(x.weighted_avg - 2.50) <= max(max(dab), max(dac)))
print(f"articles within max|delta| of the threshold: {near}")
