---
name: violence-promotion-v1-hypotheses
description: Hypotheses confirmed and open questions from violence_promotion v1 build and shadow deploy
metadata:
  type: project
---

# Violence Promotion v1 — Hypotheses

**Date:** 2026-07-28

## Confirmed 1–4 · Settled 2026-08-01 (NM#281) 9–12 — MOVED to [`archive/violence-promotion-v1-hypotheses-archive.md`](archive/violence-promotion-v1-hypotheses-archive.md) (2026-10-12)

The binary-prefilter recipe transfers; the prompt boundary holds; DeepSeek labels 2,000 articles for ~$0.45; shadow first.
The enforcement path is a default-off config flip; fail-open is an explicit decision; the first gate could not fire; three
run modes skip stamping (NM#286).

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

## Settled 2026-08-23 — enforcement ON at 0.95 (NexusMind `25d0ae2`), Q5/Q6/Q9/Q10 answered — MOVED to [`archive/violence-promotion-v1-hypotheses-archive.md`](archive/violence-promotion-v1-hypotheses-archive.md) (2026-10-12)

- Precision at 0.95 is 71–86%, below #82's 0.90 bar, measured on the wrong population: 99.6% of flags never reach an
  op-point (21 of 5,882). ⛔ **Do not "optimise" the threshold later** — among the 21 that surface, scores interleave
  completely. Enforcement is net-positive under ADR-023, ~1 article/day either way.
- Four FP classes, all inside v1's declared negative class (de-mining, disarmament/base closure, arms registration,
  repatriation). ⭐ Mine the SURFACING set for hard negatives — keyword harvesting was 92% wrong.
- ⛔ Turning a gate on makes it unobservable (positives dropped before persistence); the block ledger is the fix.

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
