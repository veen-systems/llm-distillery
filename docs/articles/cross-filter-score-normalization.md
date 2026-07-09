# Cross-filter score normalization for distilled regression scorers

**Claim.** When you ship multiple distilled scorers as a portfolio (Solutions, Belonging, Nature Recovery, …), their raw 0-10 outputs are not comparable — each filter's score distribution is shaped by oracle behaviour, training distribution, and calibration choices. We propose per-dimension isotonic calibration (ADR-008) followed by cross-filter percentile normalization from production CDFs (ADR-014), and show this lets a downstream consumer (ovr.news tabs, NexusMind) compose filters without a per-filter threshold table.

**Evidence we already have.**
- ADR-008 isotonic calibration shipped for all 6 production filters.
- ADR-014 normalization shipped, replacing `score_scale_factor`.
- NexusMind#111 documents the consumer-side problem the normalization solves.
- We can show before/after CDFs across the portfolio.

**What's novel.** Score calibration is well studied within a single model. The contribution is the *two-stage* recipe (isotonic for monotone correctness + CDF percentile for cross-filter comparability) and the production-deployment evidence across a heterogeneous filter portfolio.

**Risk / what's needed before writing.**
- Novelty check — Platt scaling, isotonic regression, and percentile normalization are all old. The pitch is the composition + the deployment evidence, not the math. Has anyone published exactly this recipe for distilled regression scorers? Lit search needed.
- Need a baseline: raw scorer outputs + a per-filter threshold table, vs. our normalized portfolio. Show the downstream task (tab ranking, threshold selection) is materially easier under our recipe.

**Venue.** arXiv tech report. Methods paper. ~6-8 pages.
