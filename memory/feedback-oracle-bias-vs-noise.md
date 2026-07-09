---
name: feedback-oracle-bias-vs-noise
description: Oracle NOISE (self-consistency) and BIAS (alignment with our editorial judgment) are orthogonal — never recommend switching oracles to cut noise; bias is the primary criterion and switching changes it
metadata:
  type: feedback
---

When evaluating or switching an oracle, separate two axes and treat them differently:

- **Noise** = self-consistency (how much the oracle disagrees *with itself* across
  re-runs). Measurable by re-scoring the same articles twice.
- **Bias** = how the oracle's scores sit relative to *our editorial judgment* of what
  the score should be. NOT measurable by self-consistency — needs a reference judgment
  (inspect the disagreement set and rule which oracle is editorially right).

**The rule: bias is the primary selection criterion; do NOT recommend an oracle switch
on the strength of lower noise alone.** Switching oracle changes the bias, and bias is
the expensive-to-detect axis — a low-noise oracle with the wrong bias produces clean,
consistent, *wrong* labels that the student faithfully learns.

**Why (the concrete case, nature_recovery v4, 2026-07-09):** v4 was flipped from Gemini
to DeepSeek deliberately for **bias** — DeepSeek's conservative scoring matched the
editorial line (keeps promo profiles / how-to listicles / travel pieces / human-interest
legacies OUT; rewards documented recovery). A 65-article bake-off showed Gemini is 2.2×
*less noisy* (self-MAE 0.17 vs 0.38) — but scored higher on 45/65 articles and surfaced
exactly the junk DeepSeek correctly demoted: "Sustainability Changemaker showcase"
DeepSeek 0.0 → Gemini 5.6; "Soil Restoration Made Simple: 6 Practices" 1.0 → 5.6;
"Looking for Meaningful Travel? 5 Indian Trips" 3.2 → 5.1. Recommending the switch to cut
noise would have re-labeled the whole corpus toward a generous bias that over-surfaces —
the opposite of what the filter was tuned for.

**Cost of getting this wrong:** the engineer flagged this same bias-vs-noise conflation
has cost **$100–200** in prior wasted re-labeling. High-value to get right.

**How to apply:**
1. When an oracle looks better on self-consistency, STOP — that's noise, not bias.
   Build the disagreement set (articles where the two oracles differ most) and judge
   editorially which is right. This is the [[feedback-oracle-selection-criteria]]
   ADR-020 method; the judging step measures bias, the re-score step measures noise.
2. To reduce noise WITHOUT changing bias, **average k runs of the SAME (correctly-biased)
   oracle** (noise ~ σ/√k), don't switch oracles.
3. But first ask *how much the noise actually matters* — if the articles the student
   fails have STABLE labels across runs, noise isn't the cause and averaging won't fix it
   ([[feedback-oracle-not-ground-truth]]).

Related: [[feedback-conservative-oracle-better]] (the conservative-bias preference this
protects), [[feedback-oracle-selection-criteria]], [[feedback-oracle-not-ground-truth]].
