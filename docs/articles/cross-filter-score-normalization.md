# Cross-filter score normalization for distilled regression scorers

**Claim.** When you ship multiple distilled scorers as a portfolio (Solutions, Belonging, Nature Recovery, …), their raw 0-10 outputs are not comparable — each filter's score distribution is shaped by oracle behaviour, training distribution, and calibration choices. We propose per-dimension isotonic calibration (ADR-008) followed by cross-filter percentile normalization from production CDFs (ADR-014), and show this lets a downstream consumer (ovr.news tabs, NexusMind) compose filters without a per-filter threshold table.

**Canonical method write-up:** `docs/NORMALIZATION_METHOD.md` — the complete final method
(op-point-anchored CDF, fit convention, guard architecture, incident evidence) with every
number sourced from production or committed artifacts. The article should be drafted FROM that
document; don't re-derive.

**Evidence we already have.**
- ADR-008 isotonic calibration shipped for all 6 production filters.
- ADR-014 normalization shipped, replacing `score_scale_factor`.
- NexusMind#111 documents the consumer-side problem the normalization solves.
- We can show before/after CDFs across the portfolio.
- **Two production incidents that are both *reference-population* errors, not model errors**
  (the strongest article material): #161 — fit floor 1.5 vs op-point 4.0 mapped correctly-scored
  doom (raw 2.2–3.3) to 5.2–8.3 on the Recovery lens, was misdiagnosed as a model failure, and
  spawned a keyword cap that took 14 months to retire; #205 — a biased fit population (lowest
  article 5.01) clipped visible articles to ~0 (raw 4.60 → 0.02).
- **The final construction makes the fit convention hold by construction** (2026-07-16): the
  CDF's lower edge is anchored to the filter's operating point (prepended `(op_point, 0.0)`
  breakpoint → `raw_min == op_point` deterministically, provably inert above the sample
  minimum), the bias signal moves to an explicit `sample_min` statistic, and one contract is
  enforced at four layers (fitter pre-fit / fitter post-fit / commit-time invariant test /
  load-time guards). Measured context: 6 days of reference-window drift moves the curve 44×
  more than the anchor's maximum effect.
- Verification-methodology angle (overlaps the augmented-engineering material): 6 consecutive
  review rounds each found defects in the prior round's fixes, including a regression created
  by the root fix itself (anchoring silently disabled the incidental biased-sample detection).

**What's novel.** Score calibration is well studied within a single model. The contribution is
(1) the *two-stage* recipe — isotonic for monotone correctness + CDF percentile for cross-filter
comparability; (2) the observation that **percentile normalization is exactly as good as its
reference population**, that both production failures were population errors in opposite
directions, and the anchored-CDF construction + guard architecture that pins the population by
construction; (3) production-deployment evidence across a heterogeneous portfolio (pass rates
0.3%–62.8%).

**Risk / what's needed before writing.**
- Novelty check — Platt scaling, isotonic regression, and percentile normalization are all old. The pitch is the composition + the population-pinning construction + the deployment evidence, not the math. Has anyone published exactly this recipe for distilled regression scorers? Lit search needed.
- Need a baseline: raw scorer outputs + a per-filter threshold table, vs. our normalized portfolio. Show the downstream task (tab ranking, threshold selection) is materially easier under our recipe.

**Venue.** arXiv tech report. Methods paper. ~6-8 pages.
