# Probe-split retraining: iterative improvement of deployed LLM-distilled classifiers

**Status:** OBSERVATION — captured for future article drafts (blog / augmented-engineering
cross-repo evidence). Not a build task; a documented technique that emerged from the
solutions v6 retrain (2026-07-26).
**Origin:** solutions v6 probe-split retrain — dropped MAE 0.564→0.476, improved gate
recall 0.559→0.671, gate F1 0.647→0.739.

## Article seeds

Two distinct pieces:

1. **"The cheap screen pays for the expensive label."** — *audience: ML engineers / distillation practitioners.*
   Hook: *Once you've deployed a classifier, improving it doesn't mean starting over. The
   probe you already have tells you where to spend your oracle budget.* The technique:
   score the full production corpus → zero out probe-negatives (free) → re-label only the
   ambiguous mid-range → retrain. Result: better precision AND better recall, for ~$3 in
   oracle cost.

2. **"Your model learned to shout because the room was noisy."** — *audience: broader ML.*
   Hook: *Retrained models on cleaned corpora produce compressed scores (max ~5 instead of
   10), and that's a feature, not a bug.* The old model inflated scores to distinguish
   signal from noise. Remove the noise, and the scores relax into a more honest range. Don't
   stretch them back — the compression is the signal that the cleaning worked.

## The technique

1. **Score the full production corpus** with the current probe + model. Every article now
   has a probe score and a model score.
2. **Zero out probe-negatives in training.** Articles the probe correctly screened out are
   non-solutions — set their oracle labels to all-zero. These cost nothing (no oracle
   re-scoring needed).
3. **Re-score the mid-range.** Articles where the probe passes but the model score is in
   the ambiguous band (~raw 1.5–4.5) are the ones worth re-labeling. Use a tightened
   oracle prompt — same dimensions, sharper critical-filters, closing the blind spots you
   found in production. These cost oracle money (~$0.001/article) but are a small fraction
   of the corpus.
4. **Keep probe-high + model-high articles as-is** — the model already gets them right.
5. **Retrain on the cleaned corpus.** The combination of zeroed noise + re-scored mid-range
   + kept high-quality positives produces a model with better precision AND recall.

## Quantified evidence (solutions v6)

| Metric | v4/v5 (before) | v6 (after) |
|--------|---------------|------------|
| Val MAE | 0.564 | **0.476** |
| Gate recall | 0.559 | **0.671** |
| Gate precision | 0.768 | **0.824** |
| Gate F1 | 0.647 | **0.739** |
| False positives in training | — | 702 dropped |
| Articles re-scored | — | 2,401 |
| Oracle re-label cost | — | $2.96 |
| Production score distribution | bimodal (median 0.0, spike at 7–10) | continuous (median 0.17, gradual taper) |

## Why it matters

- **It's cheap.** The probe (a 0.5MB pickle file, ~1ms per article) partitions the corpus
  for free. Oracle budget only goes to the ambiguous cases — where the model and probe
  disagree. This is the efficient frontier: you can't get more information per dollar than
  labeling the cases your current system is uncertain about.
- **It improves both precision AND recall simultaneously.** Normally there's a trade-off.
  Here, zeroing out probe-negatives removes false positives, while re-scoring the mid-range
  with a tightened prompt catches false negatives. Both directions improve at once.
- **The score compression is a honesty signal.** The old model's inflated scores (max ~10)
  came from training on noise — it learned to shout. The retrained model's compressed scores
  (max ~5) reflect a cleaner signal. This is counterintuitive (shouldn't a better model use
  more of the scale?) but correct: the scale was being used to express *noise rejection*,
  not *quality.* Remove the noise, and the quiet honest score is more informative.
- **It generalizes.** Any deployed classifier with a probe/screener stage can use this.
  The pattern is: cheap screen → identify disagreement band → spend budget there → retrain.
  It's active learning with the probe as the uncertainty oracle.

## For augmented-engineering

This isn't one of the four core patterns (verification, context-architecture,
reproduce-don't-assess, LLM-behavioral). It's adjacent: a **methodology pattern** — a
human-designed workflow that composes AI components (probe, model, oracle) in a novel
configuration to achieve something none of them could alone. The probe screens cheaply, the
oracle labels expensively but precisely, and the model learns from the combination. The
human's role is designing the loop — deciding what to zero, what to re-label, and how to
tighten the prompt.

This is the kind of thing that becomes obvious in retrospect but wasn't in the initial
design. The initial design treats the probe as a runtime optimization; the improvement
loop reveals it as a *training data partitioner* — a role it was never designed for but
excels at.
