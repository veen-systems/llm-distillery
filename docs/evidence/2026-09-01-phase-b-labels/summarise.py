"""Phase B label summary — what the 6,586 labels actually look like.

Reads the AGGREGATED file written by scripts/oracle/aggregate_k_runs.py, so the scope verdicts
and per-run values are still present (average_oracle_runs.py deletes them, which is why it is
not used here).

⛔ Every population is named. The corpus is GROUPED BY DESIGN CELL and its first 47 rows are the
class-A supplement, so `head -N` is not a sample and no figure here is computed over one.

Usage: PYTHONPATH=. python3 summarise.py <labels.jsonl> <corpus.jsonl>
"""
import collections, json, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
FIELD = "human_thriving_analysis"

labels = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
corpus = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[2], encoding="utf-8")}
print(f"labels {len(labels):,}   corpus {len(corpus):,}   op-point {OP} (imported)")
missing = len(corpus) - len(labels)
print(f"⛔ rows in the corpus with NO label: {missing} "
      f"(scrape-junk skips; the labelled corpus is {len(labels):,}, not {len(corpus):,})\n")

wa = [r[FIELD]["weighted_mean_all"] for r in labels]
flip = [r for r in labels if r[FIELD]["scope_flipped"]]
verd = collections.Counter(r[FIELD]["scope_verdict"] for r in labels)
per_run = collections.Counter(v for r in labels for v in r[FIELD]["scope_verdicts_per_run"])

print("== scope gate ==")
print(f"  rows whose k=3 runs DISAGREED on scope_verdict: {len(flip):,}/{len(labels):,} "
      f"= {100*len(flip)/len(labels):.2f}%")
print(f"  majority verdicts : {dict(verd.most_common())}")
print(f"  all run-rows      : {dict(per_run.most_common())}")
if flip:
    d = sorted(abs(r[FIELD]["weighted_mean_all"] - r[FIELD]["weighted_mean_major"]) for r in flip)
    print(f"  |mean_all - mean_major| on flipped rows: median {statistics.median(d):.3f}  "
          f"p90 {d[int(.9*len(d))]:.3f}  max {d[-1]:.3f}")
    cross = [r for r in flip
             if (r[FIELD]["weighted_mean_all"] >= OP) != (r[FIELD]["weighted_mean_major"] >= OP)]
    print(f"  ⛔ rows where the AGGREGATION RULE decides which side of {OP} the label lands: "
          f"{len(cross):,} ({100*len(cross)/len(labels):.2f}% of the corpus)")

print("\n== score distribution (weighted_mean_all) ==")
q = statistics.quantiles(wa, n=100)
print(f"  min {min(wa):.2f}  p25 {q[24]:.2f}  median {statistics.median(wa):.2f}  "
      f"p75 {q[74]:.2f}  p90 {q[89]:.2f}  p99 {q[98]:.2f}  max {max(wa):.2f}")
above = sum(1 for x in wa if x >= OP)
print(f"  at or above the op-point {OP}: {above:,} = {100*above/len(wa):.2f}%")
print(f"  ⚠️ this is the CORPUS's positive rate, and the corpus was drawn to a ruled shape — "
      f"it is NOT production's base rate and must not be quoted as one.")

print("\n== by design cell (the population the draw actually built) ==")
cell = collections.defaultdict(list)
for r in labels:
    cell[corpus[r["id"]]["design_cell"]].append(r[FIELD]["weighted_mean_all"])
for c, xs in sorted(cell.items(), key=lambda kv: -len(kv[1])):
    a = sum(1 for x in xs if x >= OP)
    print(f"  {c:<28} n={len(xs):>5}  median {statistics.median(xs):5.2f}  "
          f"≥op {a:>5} = {100*a/len(xs):5.1f}%")

print("\n== the 47-row class-A supplement (rows 1-47 of the corpus file) ==")
ca = [r for r in labels if "classA" in corpus[r["id"]]["design_cell"]]
sup = [r for r in ca if corpus[r["id"]]["design_cell"].startswith("pos_")]
for name, rows in (("all classA cells", ca), ("the pos_* supplement", sup)):
    if not rows:
        continue
    xs = [r[FIELD]["weighted_mean_all"] for r in rows]
    f = sum(1 for r in rows if r[FIELD]["scope_flipped"])
    a = sum(1 for x in xs if x >= OP)
    print(f"  {name:<22} n={len(rows):>3}  median {statistics.median(xs):5.2f}  "
          f"≥op {a:>3} ({100*a/len(rows):4.1f}%)  gate-flipped {f} ({100*f/len(rows):4.1f}%)")
print("  ⚠️ a class-A row scoring BELOW the op-point is correct behaviour, not a miss — it is a "
      "harm-lexicon row the prompt caught. Do not read this block as a TP:FP ratio.")
