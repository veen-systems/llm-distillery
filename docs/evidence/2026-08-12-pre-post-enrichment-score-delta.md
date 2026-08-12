# Pre- vs post-enrichment score delta — is NM#310 a compute story or a quality story?

**Date:** 2026-08-12
**Assigned:** owner, 2026-08-12 (relayed via the NexusMind session)
**Answers:** ducroq/NexusMind#310, and feeds ovr.news#312's ordering argument
**Status:** **COMPLETE (pilot, n=300 units).** Reproduction control **PASSED**.
**Reproduce:**
```
PYTHONPATH=. python3 scripts/research/enrich_delta_sample.py --index <index> --out-dir <d>
# on b650-gpu, venv-prodparity, CPU:
PYTHONPATH=. HF_HUB_OFFLINE=1 python3 scripts/research/enrich_delta_score.py \
    --design <d>/pilot_design.json --texts <d>/texts.jsonl --out <d>/scored.jsonl --device cpu
PYTHONPATH=. python3 scripts/research/enrich_delta_analyze.py --scored <d>/scored.jsonl
```
**Source:** NexusMind's own persisted `original_content` on
`sadalsuud:~/local_dev/NexusMind/data/filtered/*/filtered_*.jsonl`. Article text
stayed in a session scratchpad; none entered this repo (#97).

## The answer

**Much closer to a compute story than a quality story, with a small and bounded
quality component — and the band structure points the same way for the population
this cannot reach.**

Scoring an article on its pre-enrichment stub instead of its enriched body costs
**median +0.112** of raw score (mean +0.270), and moves **10 of 280 articles
(3.6%)** across their filter's raw operating point, **7 of 280 (2.5%)** across the
normalized 4.0 enrichment gate. **Zero articles move down.** 94% never come near a
gate from either side.

## The control, first, because nothing below is readable without it

Re-scored the **post**-enrichment text on one box and compared it against
production's persisted `raw_weighted_average`:

| population | n | median \|Δ\| | mean | max | within 0.16 |
|---|---|---|---|---|---|
| `stage_used == stage2` | **231** | **0.0000** | 0.0077 | 0.1356 | **231/231** |
| `stage_used == stage1_low` | 69 | 0.2038 | 0.3439 | 3.0457 | 28/69 |

**On every row where production ran the full model, this box reproduces it
exactly.** So the delta below is production-anchored, not a bare reproduction.

**The stage1 rows are not a reproduction failure — they are a different
instrument.** A `stage1_low` row's persisted `raw_weighted_average` is a Stage-1 e5
**probe estimate** (ADR-006 hybrid inference), so comparing it to a full-model
score compares two instruments rather than two boxes. This generalises well beyond
this study: **any analysis treating `raw_weighted_average` as a model output must
condition on `stage_used`**, or it silently mixes probe estimates into a
model-score distribution. Here that would have been **23% of rows**.

It also incidentally clears a warning that appears on every model load —
`score.weight | MISSING | newly initialized`. A randomly-initialised head cannot
reproduce production to 0.0000, so the warning is emitted during base-model load
before the adapter supplies the head. Benign, and now checked rather than assumed.

### This population's batch-composition floor is 0.0000

Measured, not inherited: `score_batch` run twice under different orderings gave
**identical** scores on all 300 units (max \|Δ\| 0.000000), and `score_batch` and
`score_article` agree to 0.000000 as well.

So **#95's \|0.16\| band does not apply to this measurement.** That band is real on
`uplifting v7` held-out rows and it is the wrong instrument here — a different
population and a different length regime. Every delta reported below is signal
rather than composition noise. This is the third distinct noise floor measured
today and the third different value; picking one by magnitude is not a method.

## The delta

n = 280 scoreable units (300 minus 20 empty stubs).

| statistic | value |
|---|---|
| mean | **+0.2697** |
| median | **+0.1115** |
| st. dev. | 0.5783 |
| share **negative** | **26.4%** |
| share within ±0.1 | **39.3%** |

Percentiles: p1 −0.542 · p5 −0.215 · p25 −0.004 · **p50 +0.112** · p75 +0.355 ·
p90 +0.841 · p95 +1.452 · p99 +2.318.

The distribution is what matters and is why a central estimate was never the
deliverable: **the median is small, a quarter of articles score *lower* after
enrichment, and the effect lives in a long right tail** — the top 5% gain more
than +1.45.

### By filter

| filter | n | mean | median | share negative |
|---|---|---|---|---|
| `cultural_discovery v5` | 47 | +0.409 | +0.361 | 8.5% |
| `uplifting v7` | 48 | +0.428 | +0.101 | 39.6% |
| `belonging v1` | 45 | +0.296 | +0.170 | 13.3% |
| `investment_risk v6` | 46 | +0.289 | +0.139 | 17.4% |
| `solutions v6` | 46 | +0.174 | +0.005 | 39.1% |
| `nature_recovery v4` | 48 | **+0.023** | +0.033 | 39.6% |

`nature_recovery v4` is indistinguishable from zero. `uplifting v7` has the
largest mean but a small median and 39.6% negatives — its effect is entirely tail.

### By stub length — and this is the finding that travels

| stub band | n | mean | median |
|---|---|---|---|
| 0–150 chars | 113 | **+0.216** | +0.092 |
| 150–300 chars | 120 | +0.258 | +0.089 |
| 300–600 chars | 47 | **+0.426** | +0.257 |

**The shortest stubs gain the LEAST.** That is counter-intuitive and it is the
slope that lets the un-measurable population be reasoned about instead of assumed:
Google News stubs are median **89 characters**, squarely in the 0–150 band — the
band with the *smallest* delta. So the honest extrapolation predicts GN's
never-enriched rows would gain **less** than this corpus average, not more. It
points against #310 being a quality story, from the one direction the design
cannot measure directly.

## Gate crossings — the number that decides #310

| | gained | lost | both above | both below |
|---|---|---|---|---|
| raw op-point (per filter) | **10** | **0** | 7 | 263 |
| normalized 4.0 (`pipeline.enrichment.min_score`) | **7** | **0** | 4 | 269 |

By filter, raw: `uplifting` 4, `investment_risk` 3, `solutions` 3, and **zero** for
`belonging`, `cultural_discovery`, `nature_recovery`.

Both thresholds are reported because they are different quantities: raw op-points
come from each filter's runtime `TIER_THRESHOLDS` (4.5 / 4.25 / 4.0 / 4.0 / 3.75 /
2.25), while NexusMind's enrichment gate reads the **normalized** score
(`production_scorer.py:698` assigns `weighted_average = normalized`). Both sides of
every comparison share one fitted mapping — re-fitting per side would have reported
the refit rather than the enrichment.

**3.6% raw / 2.5% normalized, all upward.** Under ADR-023 the direction matters:
enrichment cannot let junk through here, it can only surface something that was
already there.

## Three failure modes, not one — and #310 names only the first

1. **Scored on a blurb rather than a body.** Measured above: median +0.112, 3.6%
   of gate crossings, all upward.
2. **Would not have been scored at all.** **Empty** pre-enrichment bodies are
   **7.71%** of the full population (9,455 units, 1,582 articles; 20 in this
   pilot). `_validate_article` rejects empty content and always has — "empty is not
   short" (#93) — so production could not have scored these either. For them
   enrichment is not improving a score, it is the difference between the article
   existing and being dropped. A score delta cannot express that value, so they are
   reported here rather than folded in. Roughly 790 of the 9,455 reach ≥4
   post-enrichment corpus-wide (0 of 20 in this pilot, consistent at that n).
3. **Scored by the probe, not the model.** 23% of pilot rows carry
   `stage_used == stage1_low`, so the number that decided the article's fate was an
   e5 estimate rather than a model score.

## What this cannot see, and it is not fixable within the design

- **Google News is 0.0% of the paired population — 0 of 122,557.** Per NM#310 the
  redirect never resolves, so no enriched body exists to pair a GN stub against.
  **Absent by construction, not by sampling.** A corpus-wide delta from this work
  must never be applied to GN's ~25.7% of the corpus. The stub-length slope above is
  the only legitimate bridge, and it points *down*.
- **Survivorship, avoided rather than solved.** This uses the **pre-scoring**
  `pre_enrich` path, which does no scoring and no `min_score` filtering (its
  docstring, `article_fetcher.py:1081`), so it is ungated. The post-scoring
  `enrich_articles` path only considers articles that already cleared `min_score`
  *on the stub*, making it structurally blind to #310's alleged harm — and it is 3
  rows across the last 40 cycle files.
- **A 6-day window.** `original_content` is retained 2026-08-07..08-12, ~3.5K
  articles/day, not the archive. This is a recent-window result.
- **A pilot.** 300 units, 50 per filter. Adequate for the crossing question, which
  is a proportion near 3%; **not** adequate for per-filter tail claims, where n=48
  and the effect is entirely in the top decile.

## What follows

- **#310's own framing was right**: skip the fetch, count it as its own stat. The
  quality case for repairing GN enrichment is weak from this direction, and the
  stub-length slope says it would be weaker still for GN specifically.
- **The `nature_recovery v4` zero (+0.023) is worth a second look** — either
  enrichment genuinely does nothing for that lens, or its thin normalization fit
  (397 rows, #71) is doing something. Unresolved.
- **Scaling this pilot buys tail precision, not a different answer.** The crossing
  proportion is what the decision turns on and it is already 0 downward out of 280.
