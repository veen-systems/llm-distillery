"""#95 — does batch-shape score noise change a DECISION?

The first measurement (120 articles) found 0 tier flips, but it also found 0
articles within 0.05 of the op-point, so it could not have found one. This one
goes looking where a flip is possible: score a wide corpus once, keep the band
around each filter's op-point, then re-score ONLY that band at several batch
sizes and count how often the op-point verdict and the tier change.

Reported per filter:
  - flip rate among near-boundary articles (the honest denominator)
  - flip rate over the whole corpus (the production-relevant denominator)
  - the width of the band where flips actually occur

Run: <venv>/bin/python measure_95.py <root> <corpus.jsonl> <filter> <op_point>
"""
import importlib
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
corpus = Path(sys.argv[2])
filter_key = sys.argv[3]           # e.g. solutions/v6
op_point = float(sys.argv[4])

SCORERS = {
    "solutions/v6": ("filters.solutions.v6.inference", "SolutionsScorer"),
    "uplifting/v7": ("filters.uplifting.v7.inference", "UpliftingScorer"),
}
mod_name, cls_name = SCORERS[filter_key]
scorer_cls = getattr(importlib.import_module(mod_name), cls_name)

articles = []
for line in corpus.open(encoding="utf-8"):
    try:
        a = json.loads(line)
    except json.JSONDecodeError:
        continue
    c = a.get("content") or a.get("text") or ""
    t = a.get("title") or ""
    if c.strip() and t.strip():
        articles.append({"title": t, "content": c, "url": a.get("url", ""),
                         "source": a.get("source", "")})

print(f"filter={filter_key}  op_point={op_point}  corpus={len(articles)}", flush=True)

scorer = scorer_cls(use_prefilter=True)
print(f"device={scorer.device}", flush=True)

BAND = 0.30  # generous: max observed batch noise was 0.162

print("Pass 1: scoring the full corpus at batch_size=8 to locate the band...", flush=True)
base = scorer.score_batch(articles, batch_size=8)
scored = [(i, r["weighted_average"]) for i, r in enumerate(base)
          if r["weighted_average"] is not None]
print(f"  scored {len(scored)}; "
      f"above op-point: {sum(1 for _, s in scored if s >= op_point)}", flush=True)

band_idx = [i for i, s in scored if abs(s - op_point) <= BAND]
print(f"  within +/-{BAND} of the op-point: {len(band_idx)}", flush=True)
if not band_idx:
    print("\nNO ARTICLES NEAR THE OP-POINT — this corpus cannot answer the question.")
    sys.exit(0)

band_articles = [articles[i] for i in band_idx]

print(f"\nPass 2: re-scoring the {len(band_articles)} band articles at 4 batch sizes...",
      flush=True)
runs = {}
for bs in (1, 4, 8, 16):
    runs[bs] = scorer.score_batch(band_articles, batch_size=bs)
    print(f"  batch_size={bs} done", flush=True)

ref = runs[1]
print(f"\n{'batch':>6} {'op-point flips':>15} {'tier flips':>11} {'max|delta|':>12}")
all_flip_idx = set()
for bs, res in runs.items():
    op_flips = [j for j in range(len(band_articles))
                if ref[j]["weighted_average"] is not None
                and res[j]["weighted_average"] is not None
                and (ref[j]["weighted_average"] >= op_point)
                != (res[j]["weighted_average"] >= op_point)]
    tier_flips = [j for j in range(len(band_articles))
                  if ref[j]["tier"] != res[j]["tier"]]
    deltas = [abs(ref[j]["weighted_average"] - res[j]["weighted_average"])
              for j in range(len(band_articles))
              if ref[j]["weighted_average"] is not None
              and res[j]["weighted_average"] is not None]
    all_flip_idx.update(op_flips)
    all_flip_idx.update(tier_flips)
    print(f"{bs:>6} {len(op_flips):>15} {len(tier_flips):>11} {max(deltas):>12.3e}")

n_band = len(band_articles)
n_corpus = len(scored)
print(f"\nany-batch-size flip (op-point or tier): {len(all_flip_idx)}")
print(f"  as a share of near-boundary articles: {len(all_flip_idx)}/{n_band} "
      f"= {len(all_flip_idx) / n_band:.1%}")
print(f"  as a share of the whole corpus:       {len(all_flip_idx)}/{n_corpus} "
      f"= {len(all_flip_idx) / n_corpus:.2%}")

if all_flip_idx:
    dists = [abs(ref[j]["weighted_average"] - op_point) for j in sorted(all_flip_idx)
             if ref[j]["weighted_average"] is not None]
    print(f"  flips occur within {max(dists):.3f} of the op-point "
          f"(median {statistics.median(dists):.3f})")
    print("\n  examples:")
    for j in sorted(all_flip_idx)[:6]:
        vals = {bs: runs[bs][j]["weighted_average"] for bs in runs}
        tiers = {bs: runs[bs][j]["tier"] for bs in runs}
        print(f"    [{j}] " + "  ".join(f"bs{bs}={v:.4f}({tiers[bs]})"
                                        for bs, v in vals.items()))
else:
    print("  NO FLIPS — with articles present in the band, this is now informative.")
