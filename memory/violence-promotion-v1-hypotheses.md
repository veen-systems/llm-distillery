---
name: violence-promotion-v1-hypotheses
description: Hypotheses confirmed and open questions from violence_promotion v1 build and shadow deploy
metadata:
  type: project
---

# Violence Promotion v1 — Hypotheses

**Date:** 2026-07-28

## Confirmed

1. **The binary-preinfilter recipe transfers cleanly.** Same frozen-embedder + MLP architecture (mpnet-base-v2 → StandardScaler → MLP(256,128)) that worked for commerce_prefilter and obituary_detector works for violence_promotion too. Inference code, oracle.py, calibration_report, CHANGE_REQUEST — the template is mature and reproducible.

2. **The prompt boundary holds on smoke tests.** The oracle prompt's core discriminator — "does this article make violence seem normal, acceptable, desirable, or a source of progress?" — produces correct classifications on the 5 canonical test cases (combat=0.997, recovery=0.035, weapons-as-progress=0.989, peace=0.000, borderline-economic-framing=0.721).

3. **DeepSeek is cost-effective for binary labeling.** 2,000 articles ≈ $0.45 total. The JSON response format with temp=0 produces clean parseable scores. Same pattern validated on obituary_detector.

4. **Shadow-deploy is the correct first step for prefilter classifiers.** The model has known gaps (recall 0.55, only 1,957 training samples) but shadow mode costs nothing in content loss. Production data will reveal which error classes actually matter.

## Settled 2026-08-01 (NM#281)

9. **The enforcement path now exists, default-off, and is a config flip.**
   `pipeline.violence_promotion.enforce: false` → `_enforce_violence_promotion()`
   in NexusMind's `scripts/main.py`. Flipping it after LD#82 needs no new mechanism and no
   deploy. **Caveat carried in the config comment:** at recall 0.55, enforcing
   gates roughly half of true positives — precision-first by construction, so
   question 5 below becomes an owner decision, not a modelling one.

10. **Fail-open is now an explicit decision, not an accident.** If the detector
    errors, articles are unstamped and **admitted**. Correct for a
    precision-first gate — fail-closed would empty the corpus on any model
    failure — but it means a silent model failure admits everything, with only
    an ERROR line as signal. `_enforce_violence_promotion` keys on `is True`
    (not truthiness) so unstamped and non-bool values can never cause a drop.

11. **The first gate implementation could not fire** (found by adversarial
    review the same day, before any flip). It was placed in `_is_duplicate`,
    which runs *before* violence stamping — `enforce: true` would have dropped
    zero while logging `0 violence`. Fixed in `b85a467`. **Lesson for whoever
    flips it: verify from the `Violence promotion ENFORCED: dropped N` line,
    not from `filtered_*.jsonl`,** which only ever contains survivors.

12. **Three run modes silently skip stamping entirely** (NM#286): single-filter
    runs, `--no-dedup`, and a shared-dedup exception all leave `_article_cache`
    empty, so the detector never runs. Combined with fail-open, those modes
    admit everything. Fix before enforcing.

## Open questions

**Measured 2026-08-03 — shadow flag rate, four consecutive cycles.** 95/2,172
(4.4%), 61/2,082 (2.9%), 58/2,627 (2.2%), 53/2,626 (2.0%). Stamps present on
**100%** of live rows (`_violence_model: v1`), so the detector is running
everywhere it should in the scheduled path.

Worth noting against question 5: the calibration scan put prevalence at 8.7%,
and 8.7% × 0.55 recall ≈ **4.8% expected flag rate**. The observed rate sits at
or below that (4.4% falling to 2.0%), which is *consistent* with the recall
estimate rather than contradicting it. **Do not read the decline across cycles
as a trend** — corpus composition differs per cycle and n is 4. What this does
give #82 is a concrete prior: expect to audit ~50–95 articles per cycle, and
expect roughly as many true positives again to be sitting unflagged.

5. **How low can recall go before it matters?** At 0.55 recall, ~45% of violence-promoting content leaks through. For a stamp-only prefilter, this is invisible to users (no content dropped). But when ovr.news starts excluding stamped articles, the false-negative rate determines how much off-brand content reaches the lens. The calibration scan found 8.7% of pipeline articles are violence-promoting — at 55% recall, ~3.9% would still reach ovr.news. Acceptable?

6. **Is the single calibration FP (Korean Su-57 crash) a class or an outlier?** The independent calibration found 1 FP at 0.95 — a Korean article about an Su-57 fighter jet crash. Is this "weapons system in headline but framed as news reporting" a recurring pattern? Shadow data will tell us.

7. **Does the small training set (1,957) cover the violence-promotion spectrum?** With only 211 positive examples, the model has seen a limited range of violence-promoting language. Production shadow will reveal whether the recall gap is concentrated in specific domains (defense industry, state violence, armed groups) or evenly distributed.

8. **Does the weapons-manufacturing-as-progress framing generalize across languages?** The prompt explicitly targets domestic arms production framed as achievement/growth/innovation — a framing common in state media. The multilingual embedder should handle this, but we haven't validated on non-English weapons-industry content.

## Design decisions (not yet tested)

9. **ADR-004 stamp-only approach pushes the enforcement decision to consumers.** ovr.news excludes stamped articles at selection; investment_risk and resilience keep them. This is correct in theory, but means the "did we get it right?" feedback loop requires cross-repo coordination. A violence-promoting article flagged by the prefilter that investment_risk would have scored highly is invisible unless someone explicitly checks.

10. **The 0.95 threshold was chosen for precision, not recall.** At 0.90: precision 0.896, recall 0.611 (OOF). At 0.80: precision 0.890, recall 0.687. If shadow data shows the model is too conservative, lowering the threshold is cheaper than retraining — but precision degrades quickly below 0.95.

---

## Settled 2026-08-23 — the audit ran, enforcement is ON and verified

**#82 closed as measured.** Full detail in `docs/BINARY_GATE_STANDARD.md` and #82's comments.
NexusMind `25d0ae2`: `enforce: true`, `threshold: 0.95`.

### ⭐⭐ Q5 and Q10 are both answered, and the frame was wrong

**Precision at 0.95 is 71–86%** (deepseek / qwen2.5, population-weighted over 3,200 flags;
judges agree on only 60/75 so treat it as a band). That is **below #82's own 0.90 bar** — and
enforcing anyway was correct, because **the bar was measured on the wrong population.**

⛔ **99.6% of flagged articles never reach a lens operating point** — 21 of 5,882, against 7.8%
for articles generally. A precision figure over all flags describes articles no reader could see.

⛔ **Q10's premise is refuted for this gate: raising the threshold does NOT buy usable
precision.** Across all flags it does (86% → 93% at 0.99), but among the 21 that *surface* the
scores interleave completely — the top scorer (**0.9988**) is a POW-exchange false positive and a
true positive sits at **0.9546**. Raising to 0.99 blocks 3 of the 21: 1 wrong, 2 right.
**Do not "optimise" the threshold later; the config comment says so.**

**What enforcement actually trades** (my adjudication of all 21, not a panel): ~10 correctly
removed (India's *"Big milestone: 1st 100% indigenous AK-203"* — in **`solutions`**; Ethiopia's
Air Force *"technological muscle"* at `uplifting` **5.31**; Air Assault Forces listing 26
liberated villages at **4.66**) against ~10 wrongly removed (UN clearing unexploded ordnance
*to protect civilians* at **5.39**; Syria–Russia ending military use of two bases at **5.21**;
Iraq's 6M-weapon registry at **5.34**; repatriation of bodies and 103 POWs). **Net-positive under
ADR-023**, and ~1 article/day either way.

### Q6 answered: it is a CLASS, not an outlier — and there are four

The Su-57-crash shape generalised. The FP classes, all inside v1's **own declared negative
class**: **de-mining / UXO clearance**, **disarmament and base-closure deals**, **weapons
registration / arms control**, **repatriation of remains and POWs**. Criterion 2 of #82 ("no new
FP classes") therefore **passes** — it fails at edges it already knew about.

`datasets/adverse/violence_promotion_hard_negatives.jsonl` — **8 confirmed** (both judges).
⛔ **Keyword harvesting was 92% wrong**: 244 candidates → 100 judged → 8 kept. Most POW/remains
matches are war roundups that genuinely *are* violence. ⭐ **Mine the SURFACING set instead** —
FPs run ~50% there vs ~8% among keyword matches. That is the v2 corpus strategy.

### ⭐ Q9 answered by accident, and it is the finding with the longest reach

Enforcing **removed the gate from the record**. `_is_violence_promotion` had 2 distinct values
only because it ran in shadow; from the next cycle it is **constant-`False`**, exactly like
`_is_commerce` and `_is_obituary` — which are constant across 25,122 rows not because they are
broken but because each gate's positives are dropped before persistence.
⛔ **Turning a gate on makes it unobservable.** The block ledger (`docs/BLOCK_LEDGER_SPEC.md`) is
the fix, and this is what makes it time-sensitive.

## Settled 2026-08-26 — the shadow log has a WINDOW, and it changes the headline number

The gate's flagged-but-KEPT share is the quantity every threshold argument rests on, and
it had only ever been measured on **one cycle** (90.6%, 2026-08-25). Joined across every
cycle where the shadow log and the block ledger **both** exist — the ledger starts
2026-08-24, so that is the whole observable window, not a sample of a longer one:

| | flagged | in ledger | kept | kept % |
|---|---|---|---|---|
| pooled, 12 cycles (08-24 .. 08-26) | 4,801 | 561 | 4,240 | **88.3%** |
| per-cycle range | | | | **72.5% – 92.9%** |
| ⛔ ledger seeding flush (excluded) | 239 | 239 | 0 | 0.0% |

⛔ **90.6% was the second-highest of twelve** and had been copied into five documents.
The conclusion is unchanged — the shadow log is not redundant with the ledger, and that
argument rests on the **worst** cycle, not the pooled one — but quote the pooled figure
with its window, or better, re-run it:
`NexusMind/scripts/research/measure_shadow_kept_share.py`.

Two instrument rules the wider window produced, both now in the script:

- **A newly-deployed ledger's first run is a backlog flush, not a cycle** (239 flagged,
  239 blocked). Pooling it in drags the share to 84.1%. It is printed and labelled rather
  than dropped — a run excluded without being shown is indistinguishable from one that was
  never there.
- **A flagged run whose ledger file has aged out is NOT "0 blocked" — it is unobservable.**
  Counting those as zero manufactures a 100% kept share out of retention alone, and in the
  flattering direction.

### New open question — Q11: flagged VOLUME is rising and nobody has attributed it

Per-cycle flagged counts over the same 12 cycles: 280, 284, 315, 338, 373, 402, 414, 460,
485, 495, 490, 465 — **roughly +66% across three days**, then a plateau. ⚠️ **Not yet a
finding.** The obvious confound is corpus size (each cycle's scored population also grew),
and the rate has never been expressed per-article — which is the same denominator error
this project has made repeatedly. **Divide by the cycle's own scored count before reading
anything into the trend**; a raw count is not a rate, and both numbers are in the pipeline's
own log lines. Until then this is an observation, not drift.

### Still open

- **Q7/Q8 untouched** — training-set coverage and cross-language weapons-industry framing.
- **~29% of article placements reach the enforcement step UNSTAMPED and fail open**
  (6,570 of 22,353). Documented behaviour, not a regression, but the gate covers ~71% of what
  reaches the lenses. With recall 0.55 the honest description is **judges ~71%, catches ~half
  within that.**
- ⚠️ **My judge prompt likely UNDER-calls the weapons-as-progress branch** — both judges justified
  `not_violence` with *"not active violence"*, and my decisive test leads with *mass* violence.
  Real precision is probably at or above the top of the 71–86% band. **Reword before quoting a
  tighter number.**
- ⛔ **`qwen3:14b` is not a usable panel lab** — unparseable on 74 of 75 (2nd failure in two days).
