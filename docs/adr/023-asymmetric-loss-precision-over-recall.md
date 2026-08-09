---
status: Accepted
date: 2026-08-09
deciders: [Jeroen Veen]
superseded_by:
---

# ADR-023: Asymmetric Loss — a False Positive Costs a Reader, a False Negative Costs Nothing Visible

## Decision

Every filter in this repo optimises **specificity / precision at its operating
point**. Recall is a *constraint to satisfy*, never a target to maximise. When
an op-point choice is genuinely balanced, take the tighter one.

And: **never rank or compare filters on MAE.**

## Context

Owner, 2026-08-09, in as many words: *"letting junk through is way worse than
not catching positives. Junk kills readers; positives they don't know about
don't hurt them."*

Followed by: *"that always was the target, but apparently not clear enough."*
It wasn't written down anywhere, and on the same day an agent produced a
six-filter quality ranking on mean absolute error and recommended a
calibration change on it. Hence this ADR — the decision is not new, the record
is.

The economics are not symmetric and never were:

- **A false positive reaches a reader.** They open a story that does not belong
  in the lens. It costs trust in the outlet, and one bad item in a short feed
  is a large fraction of what that reader saw.
- **A false negative is invisible.** The reader never learns the story existed.
  Supply exceeds shelf space by orders of magnitude — measured 2026-08-09,
  `nature_recovery` surfaces ~5 articles per cycle from ~2,150, `uplifting`
  ~200. Missing one good story costs a slot that is immediately refilled.
- ovr.news is pre-launch. The failure that stops a launch is a reader seeing
  a riot in a constructive-news tab, not a reader not seeing a river cleanup.

## Rationale — why MAE is the wrong instrument here, specifically

MAE is averaged over **every** article, and in needle-in-haystack filtering the
corpus is ~97% negatives sitting near zero. Two independent problems follow:

1. **It is dominated by the wrong population.** A filter can post an excellent
   MAE by predicting ~0 everywhere and be useless. The decision quality lives
   entirely in the thin band around the op-point, which MAE barely weights.
2. **It is not comparable across filters.** Each filter's test split has its
   own positive rate — measured 2026-08-09: `uplifting v7` **32.7%**,
   `solutions v6` **16.2%**, `nature_recovery v4` **15.3%**. Positives use more
   of the 0–10 range, so a more enriched split carries mechanically larger
   per-article error *for identical model quality*. Ranking filters on MAE
   compares six populations through one number.

The same trap one level down: **precision is base-rate dependent too.** A
filter tested on a 33%-positive split will out-score one tested on a
15%-positive split at equal quality. Only **recall** and **specificity** are
conditional on the true class and therefore comparable across splits.

## Consequences

**The comparison metric.** Report recall AND specificity at each filter's own
op-point, always with the split's positive rate stated. Precision may be
reported but never compared across splits without reweighting. MAE may be
recorded as a training diagnostic; it may not carry a quality claim.

**Active learning samples above the gate.** The expensive errors are the ones
that reach readers, so a labelling batch starts in the surfacing band —
heaviest at the margin just above the op-point, where junk concentrates — not
in the band below it. Sampling below the gate hunts recall, which is the cheap
error. A thin below-gate stratum for op-point calibration is fine; making it
the batch is not.

**Op-point selection.** Where recall and specificity trade against each other
within the #95 noise band, take the specificity. "Two models whose bands
overlap are not distinguishable" (ADR-022 / #95) still binds; this decides the
tie.

**What this immediately implicates.** Measured 2026-08-09 on held-out oracle
test splits:

| filter | positive rate | recall | specificity | FPR on true negatives |
|---|---|---|---|---|
| `uplifting v7` | 32.7% | 0.7361 | 0.9189 | **8.1%** |
| `solutions v6` | 16.2% | 0.6707 | 0.9723 | 2.8% |
| `nature_recovery v4` | 15.3% | 0.6500 | 0.9789 | 2.1% |

`uplifting v7` has the best recall and by far the worst specificity — it fires
more, catching more real positives and 3–4× more junk per true negative. Under
this ADR that is the wrong side of the trade, and it is the first thing to fix
in the "bring the other scorers up to solutions/nature_recovery" programme.
It is also mechanism, not coincidence, for ducroq/NexusMind#306: corrupted
article bodies cross the gate at **38.3%** vs a 3.5% control, **concentrated
entirely in uplifting** — the loosest gate is where an off-topic body that
reads vaguely positive gets promoted.

**Retracted by this ADR**, both from 2026-08-09 and both artifacts of MAE:
the six-filter quality ranking, and "uplifting's calibration is a net negative,
refit or drop it" (on the decision it is indistinguishable — 5 articles of 660
change side, inside the 37-row indeterminate band).

## What this ADR does NOT say

- Not "recall does not matter". A filter that surfaces nothing is not safe, it
  is broken. Recall is a floor to clear (the ADR-021 gate reports it), not a
  quantity to trade freely away.
- Not "raise every threshold". Op-points are set on held-out oracle ground
  truth per ADR-021, not by preference. This decides ties and sets the
  objective; it does not license moving a gate without measuring.
- Not applicable to the Stage-1 e5 probe, which is a **recall-safe screen** by
  design: it decides only what reaches Stage 2, and an article it drops is
  never seen by the student at all. There the FN is the expensive error, which
  is why `train_probe.py --objective recall --target-fn 0.02` exists. Measured
  2026-08-09: all six deployed probe thresholds sit at val FN 0.000.

## References

- Owner decision, 2026-08-09 (this session)
- ADR-021 — ground-truth deploy gate; the instrument this ADR sets the objective for
- ADR-016 / ADR-022 — pass/block + continuous score; visibility is `raw >= op-point`
- `memory/score-batch-shape-noise.md` (#95) — the ±0.16 band that bounds every threshold metric
- `filters/uplifting/v7/ground_truth_gate.json` — measurement and retractions
- `docs/TODO.md`, 2026-08-09 — the audit these numbers came from
- ducroq/NexusMind#306 — corrupted bodies, 38.3% crossing, concentrated in the loosest gate
