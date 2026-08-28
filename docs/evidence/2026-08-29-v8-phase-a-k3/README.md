# Phase A k=3 — the reorder is not label-neutral, and the flip rate is smaller than the probe said

**2026-08-29. Spend: $0.85** (DeepSeek off-peak, 1,200 calls, **0 errors**). No model
trained, no threshold moved, nothing in `filters/` changed, nothing deployed.

Design fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) **before the draw and before any
call** — committed in `ff88b56`, one commit ahead of these results, and unchanged between
the two. Four of its seven predicted ranges were missed (§6), which is the cheapest
available evidence that the numbers were not chosen after the fact.

## Headline

1. ⛔⛔ **H-V8-3 is RESOLVED and the answer reverses the plan's assumption: moving the
   article to the end of the prompt CHANGES THE LABELS.** Mean(reordered − as-is) =
   **−0.239** on the production-mix stratum (95% CI [−0.409, −0.080]) and **−0.443** on
   the boundary stratum ([−0.764, −0.138]). The reordered prompt puts **8/150 vs 11/150**
   and **7/50 vs 12/50** rows above the 4.5 op-point. It is a **stricter oracle**, not a
   cheaper copy of the same one.
2. ⭐ **The effect is not just the scope gate.** On the 41 rows where *both* arms said
   `in_scope` on *all three* runs, the reordered prompt still scores **−0.235**
   ([−0.389, −0.075]), and the shift is present on **all six dimensions** (largest:
   `social_cohesion_impact` −0.366, `human_wellbeing_impact` −0.293). Position changes the
   scoring, not only the gate.
3. **The flip rate is real but smaller than the probe's 13%.** Per-pair scope-binary
   disagreement: **5.3%** production-mix ([2.7%, 8.4%]), **9.3% / 6.7%** at the boundary.
   Non-unanimity at k=3: **8.0%** production-mix, **14.0% / 10.0%** boundary.
4. **The old "all six dims ≤ 2" inference was 98.8% right** over 1,200 now-recorded
   labels — good, but it hid the 1.2% and could never have shown the verdict *mix*.

## Why the 2026-08-28 probe could not see finding 1

Not sample size alone. The probe's null arm was **a second run of the control**, compared
against the treatment as a whole. This run measures the null **on the same rows, at the
same pair level**: 6 within-arm pairs and 9 between-arm pairs per row, row-clustered
bootstrap on the difference. The treatment no longer "sits inside its own null" because the
null is now an estimate with an interval rather than a single alternative number.

| stratum R (n=150) | within-arm (null) | between-arm | diff, 95% CI |
|---|---|---|---|
| share of pairs moving > 0.16 (#95 band) | 34.9% | **52.4%** | [12.4%, 22.7%] |
| mean \|Δ\| | 0.312 | **0.630** | [0.196, 0.459] |
| op-point crossing rate | 2.4% | **4.2%** | [0.2%, 4.0%] |

| stratum B (n=50) | within-arm (null) | between-arm | diff, 95% CI |
|---|---|---|---|
| share of pairs moving > 0.16 | 39.3% | **52.9%** | [6.4%, 21.7%] |
| mean \|Δ\| | 0.421 | **0.767** | [0.141, 0.590] |
| op-point crossing rate | 12.7% | 16.2% | [−0.4%, 8.9%] — **not established** |

The one cell that does not clear its null is the boundary op-point crossing rate at n=50.
Reported as not established, not as absent.

## Two controls, run before believing any of it

- **Time drift.** Arm A ran ~1 minute before arm B in every round, so a vendor-side drift
  would land entirely on A. Per-run cohort means: **A 1.524 / 1.566 / 1.537**, **B 1.809 /
  1.843 / 1.845**. The ~0.28 gap is present in all three rounds and there is no within-arm
  trend that approaches it. It is the prompt, not the clock.
- **Prompt identity.** Re-verified here rather than inherited: **42,406 → 42,411 chars**,
  non-blank line multiset differs by exactly one `---`, article offset **617 → 40,626**.
  Content-preserving; the only change is position.

## The cost picture, and the half of it this run did not test

Per-article, **from run 1 of each arm only** — runs 2 and 3 re-send byte-identical prompts
and their 99.4% cache is the artifact the pre-registration named.

| | cache hit, run 1 | $/article, run 1 |
|---|---|---|
| arm A, article last | **89.2%** (ceiling 95.8%) | **$0.00050** |
| arm B, as-is | **0.0%** | **$0.00275** |

⚠️ **The k=3 repeat discount is UNPROVEN at corpus scale.** Runs 2–3 cost $0.00025/article
here because the identical prompt came back ~1 minute later. A 6,590-row pass takes ~30
minutes, so on the corpus the repeat arrives ~30 minutes after the original, and **nothing
in this run measured DeepSeek's cache TTL**. Two consequences: any k=3 corpus estimate
below carries that assumption, and **scheduling k=3 as three back-to-back calls per article
rather than three passes over the corpus** would remove the assumption entirely.

Corpus k=3 on 6,590 rows, *if* the repeat discount holds: **reordered ≈ $6.6, as-is ≈ $21.4**.
Without the discount: reordered ≈ $9.9, as-is ≈ $54.4.

## What this makes into an owner decision

The reorder is **~5.5× cheaper on the paying call and a different labelling function**. So
it cannot be adopted as a cost optimisation — it has to be chosen as a scoring change:

- It is **stricter**: fewer `in_scope` (28.7% vs 32.8% of labels), more `out_of_scope`
  (239 vs 194 in stratum R), lower on every dimension, ~35% fewer rows above the op-point.
- ADR-023 wants specificity, so *stricter is not obviously wrong* — but the v8 prompt was
  adjudicated in its **as-is** form, and this shifts what it labels.
- The ~$15 difference on the corpus is small against the adjudication time the plan already
  calls "the real cost".

**Not adopted here.** The reordered prompt remains written, not adopted.

## §6 — predictions vs outcomes

| quantity | predicted | measured | |
|---|---|---|---|
| stratum B flip rate | 15–35% | **6.7–9.3%** | ⛔ miss, low |
| stratum R flip rate | 4–15% | 5.3% | ✅ |
| rows non-unanimous at k=3, stratum B | 20–45% | **10–14%** | ⛔ miss, low |
| median between-arm \|Δ\| | < 0.20 | 0.217 (R) / 0.192 (B) | ⚠️ borderline |
| median within-arm \|Δ\| (null) | 0.05–0.20 | **0.000 (R)** / 0.100 (B) | ⛔ miss, low |
| cache hit, arm A run 1 | 85–94% | 89.2% | ✅ |
| total spend | $1.0–2.2 | **$0.85** | ⛔ miss, low |

⭐ **Four misses, all the same direction: I over-predicted variability and cost**, having
anchored on a 30-row op-point-weighted panel. An anchor drawn from a design-weighted sample
biases the *prediction* too, not only the estimate it came from.

## Two deviations from the pre-registration, reported not substituted

1. The pre-registered parity rule — *median between-arm |Δ| on k=3 means ≤ 1.5 × median
   within-arm |Δ| on run pairs* — is **biased and unusable**. Biased because a k=3 mean is
   less noisy by construction, so it favours "parity holds". Unusable because the within-arm
   median is **0.000** in stratum R (most rows are identical run to run), so the ratio
   divides by zero. **A bar that cannot be evaluated is not a bar.** Replaced by the matched
   pair-level test above, whose null is measured rather than assumed.
2. The pre-registered op-point rule — *between-arm count inside the range of the two
   within-arm counts* — had **no error bar**: at counts of 3–8 out of 150, Poisson noise
   alone spans that range. Replaced by the same row-clustered bootstrap.

Both replacements were written after seeing that the original rules were unevaluable, and
before reading the parity result. Recorded here so the substitution is visible.

## Reproduce

```bash
# Draw (runs on sadalsuud, which holds the archive; window re-enumerated at draw time)
python3 draw200.py > cohort200.jsonl 2> cohort_manifest.json

# Six passes, interleaved A1 B1 A2 B2 A3 B3, through the real call site
PYTHONPATH=. python3 scripts/score_deepseek_production.py \
  --input cohort200.jsonl --output phaseA_<arm><run>.jsonl \
  --config filters/uplifting/v7/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate{-tail,}.md \
  --concurrency 8

PYTHONPATH=. python3 analyse.py <dir-holding-the-six-outputs>
```

⛔ **The cohort is not committed** — full article text at scale is the #97 hazard. The
manifest (`cohort_manifest.json`) records the window, the pool sizes and the design weights,
which is what a re-draw needs. `results.txt` is the analysis output verbatim.

**Population:** `sadalsuud:~/local_dev/NexusMind/data/filtered/uplifting/`, window
`filtered_20260814_165416` → `filtered_20260828_131614`, **83 files, 232,564 rows**.
Excluded per the plan: `news.google.com` 53,793 (23.1%), content < 300 chars 21,345,
`stage_used != stage2` 15,052, duplicate id 1 → **142,373 eligible**, of which **10,738**
in the [4.0, 5.0) band. ⚠️ **Both strata therefore describe the stage-2 population**; no
claim here transfers to stage-1 rows. The window rolls — a draw next week is a different
population.
