# v8 prompt order probe — the cache fix works, and it found a bigger problem

**2026-08-28. Spend: $0.12** (DeepSeek off-peak, 90 calls, 0 errors). Nothing deployed, no
model trained, no threshold moved. The reordered prompt is **written but not adopted** —
adoption is an owner call, and §4 says why.

## Why this ran

`filters/human_thriving/v8/prompt-candidate.md` puts the article at char **617 of 42,406**,
so its prefix-cache ceiling is **1.5% — the lowest of the 17 prompts in this repo**
(solutions v6 is 35.7%). Everything after the article, i.e. the whole rubric, cannot be a
shared prefix. The v8 shape is also the most input-heavy we run (I/O 42.8), so input price
dominates. Question: does moving the article to the end recover it, and does it change the
labels?

## The arms

`filters/human_thriving/v8/prompt-candidate-tail.md` is the same file with the
`**INPUT DATA:**` line relocated to just before `## 7. Critical Reminders` — so the whole
rubric caches while the JSON-format instruction still comes last. **Content-preserving:**
the non-blank line multiset differs by exactly one `---` separator (+5 chars). Ceiling
**1.5% → 95.8%**, measured by `scripts/analysis/oracle_cost.py`, not by hand.

**Cohort:** 30 articles drawn on sadalsuud from the 6 most recent `filtered_*` cycles
(19,713 rows → 12,463 eligible), stratified across the v7 score range. Exclusions are the
plan's, not chosen here: `news.google.com` (**4,346 = 22.0%**, an independent match to the
22.1% on record), content < 300 chars (1,731), `stage_used != stage2` (1,173). 7 languages,
322–65,589 chars. Script: `draw30.py`. ⛔ The cohort itself is **not** committed — full
article text at scale is the #97 hazard.

Three runs, all through the real call site (`scripts/score_deepseek_production.py`), never a
substitute:

| arm | prompt | purpose |
|---|---|---|
| control | `prompt-candidate.md` | baseline |
| **null** | `prompt-candidate.md` **again** | isolates decoder noise at temperature 0.3 |
| treatment | `prompt-candidate-tail.md` | the reorder |

## 1. The cache fix works

| | cache hit | cost, 30 rows |
|---|---|---|
| control (article at char 617) | **0.0%** — 30 of 30 rows at zero | $0.08 |
| **treatment (article last)** | **76.0% overall; median 90.2% on the 26 warm rows** | **$0.03** |

The 4 cold rows are the concurrency-4 warm-up and vanish at corpus scale. The 95.8% ceiling
is very nearly realised, so this is not a vendor claim — it is a rate **this code path
obtained**, which is the half #103 never checked.

⛔ **The null arm read 99.4% and that number must never be quoted as a cache result.** It
re-sent the *same 30 articles*, so the entire prompt matched, not just the prefix. A corpus
run sends distinct articles. Its cache number is an artifact of the experiment's design; its
*scores* are still valid, which is what it was for.

## 2. The reorder does not detectably change the labels — and that is a weak statement

Weighted average under v7's weights (v8 changes no weights).

| comparison | sd | rows moving >0.16 (#95 band) | op-point (4.5) crossings |
|---|---|---|---|
| **null** — control vs control | 1.440 | 16/30 | **5** |
| treatment — control run1 vs tail | 1.571 | 16/30 | 3 |
| treatment — control run2 vs tail | 1.907 | 21/30 | 6 |

**The treatment sits inside its own null arm.** Two identical runs of the *same* prompt
disagree as much as the reorder does, and flip *more* rows across the op-point than
treatment-vs-run1 does. So at n=30, k=1 the honest conclusion is **"no effect detectable
above noise"**, not "no effect" — the instrument cannot resolve one.

⭐ **The null arm is the whole result.** Without it, the treatment's 16/30 and 3 op-point
crossings read as a damning parity failure, and the reorder would have been abandoned on a
number that measures the oracle, not the change.

## 3. ⛔⛔ The finding that outranks the one we came for

**This prompt is unstable run-to-run, and the mechanism is its own scope gate.**

Between two runs of the identical prompt on the identical articles:

| | value |
|---|---|
| rows crossing the op-point | **5 / 30 (17%)** |
| rows where the scope gate (all six dimensions ≤ 2) flips | **4 / 30 (13%)** |
| median \|Δ\| on **gate-stable** rows | **0.100** |
| median \|Δ\| on **gate-flipped** rows | **3.750** |
| of the 5 rows moving \|Δ\| > 1.0, how many were gate flips | **4** |
| of the 25 rows moving \|Δ\| ≤ 1.0, how many were gate flips | **0** |

The instability is **not** gradual decoder jitter. On gate-stable rows the prompt is
excellent — median 0.100, comfortably inside the #95 band of 0.16. The variance is a **step
function**: `scope_verdict` is a binary the prompt turns into "ALL six dimensions 0–2", so a
marginal verdict landing either way swings the weighted average by ~3.75 in one jump.

That is a property of Phase A steps 1 + 2b as drafted, not of the reorder — and **Gate A
never saw it**, because Gate A ran k=3 and averaged over exactly this.

**Consequence for the plan:** a single-run oracle label on v8 carries a ~13% chance of a
gate coin-flip. On a 6,590-row re-score that is roughly **860 rows labelled by the toss**,
concentrated at the boundary, which is where ADR-023 says the expensive error lives. **The
v8 re-score needs k ≥ 3 with aggregation, not k = 1.**

## 4. What this makes affordable — the two findings are the same decision

| plan | $/article | 6,590 rows |
|---|---|---|
| k=1, current prompt (article at char 617) | 0.002732 | **$18.00** |
| **k=3, reordered prompt (90% cache)** | 0.000514 ×3 | **$10.16** |

**Three labels per row for 56% of the price of one.** The reorder does not merely save
money; it pays for the k=3 that §3 shows the prompt requires. The plan's "≈$12" was an
estimate against a single run at the old shape.

## 5. What is still open — do not skip this

1. ⛔ **Parity is UNPROVEN, not proven.** §2 says the effect is smaller than the noise, and
   the noise is large. Establishing parity needs k≥3 per arm — which §4 now makes cheap.
   **Adopt the reordered prompt for the Phase A k=3 calibration run, where parity gets
   settled properly. Do not adopt it into a re-score on this probe alone.**
2. The scope-gate instability may itself be reducible — a verdict rubric that is less
   knife-edge, or a k=3 majority vote on `scope_verdict` specifically rather than a mean
   over dimensions. Not tested.
3. `scope_verdict` and `dominant_subject` are **not persisted** by
   `score_deepseek_production.py` — §3 had to infer the gate from "all six dimensions ≤ 2".
   That inference is sound here (0 of 25 small movers, 4 of 5 large ones) but it is an
   inference. Persist the two fields before the calibration run.
4. Rates are as of 2026-08-24 and DeepSeek raised prices on 2026-08-16. Re-read before the
   real spend.

## Reproduce

```bash
PYTHONPATH=. python3 scripts/analysis/oracle_cost.py          # both ceilings, 1.5% and 95.8%
ssh sadalsuud 'python3 draw30.py > /tmp/probe30.jsonl'        # the cohort
PYTHONPATH=. python3 scripts/score_deepseek_production.py \
   --input <cohort> --output <out> --config filters/uplifting/v7/config.yaml \
   --prompt filters/human_thriving/v8/prompt-candidate-tail.md --concurrency 4
```

Per-row `usage` is now written by that script (added today) — the aggregate it printed
before could not separate a cold prefix from a warm one, and a short run's cache rate is
dominated by warm-up.
