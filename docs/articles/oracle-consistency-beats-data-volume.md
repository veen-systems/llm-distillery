# Oracle consistency beats data volume

**Claim.** For LLM-as-judge distillation, prompt precision predicts student MAE better than training set size. Doubling data with a noisy oracle prompt is worse than halving data with a sharp one.

**Evidence we already have.**
- 6 production filters, dataset sizes 3.5K–10.6K, MAEs 0.47–0.75 (see CLAUDE.md table).
- Belonging v1: 7.4K articles, MAE 0.49 — sharper prompt, smaller dataset than several worse-MAE peers. ADR-010 cites it as the template.
- Foresight v1 vs. investment-risk v6: similar architecture, different prompt discipline, different MAE.
- Nature recovery v1 → v2: same data scale, different oracle behaviour + sample weighting, MAE went from "no discrimination" (#41) to 0.53.

**What's novel.** The "scale data" reflex is the default reading of distillation literature. We have a cross-filter natural experiment that says prompt design dominates within the 3K–10K range we operate in.

**Measured consistency numbers (nature_recovery, 2026-07-09).** We finally have the "oracle agreement on held-out items" metric this note asked for. Re-scoring the same 65 articles twice with each oracle (identical prompt): weighted-average **self-MAE 0.38 for DeepSeek vs 0.17 for Gemini**. The student's own held-out MAE (0.48) sits just above the DeepSeek floor — consistent with the claim that oracle self-consistency, not data volume, sets the ceiling.

**Critical refinement — consistency is necessary, not sufficient. Noise ≠ bias.** This note's "consistency" is *noise* (self-disagreement). There is an orthogonal axis, *bias* — where the oracle sits relative to the editorial target — that self-consistency cannot see, and that dominates the deploy decision. Same experiment: Gemini was 2.2× *less* noisy yet systematically *more generous*, surfacing a corporate "sustainability changemaker" profile at 5.6 and a how-to listicle at 5.6 — exactly the content the filter rejects. Picking the low-noise oracle to "improve the labels" would have distilled the wrong judgment. So the sharpened claim is: **prompt/oracle precision beats data volume for noise, but choose the oracle for bias first (per filter), and cut noise by averaging k runs of the correctly-biased oracle — never by switching to a cleaner-but-differently-biased one.** A clean, consistent, wrong labeler looks like progress and isn't. (See memory/feedback-oracle-bias-vs-noise, augmented-engineering#26; and note MAE itself is misleading for the needle filters here — the deploy metric is ranking/recall-precision, not MAE.)

**Risk / what's needed before writing.**
- Confounding by task difficulty and distribution skew — needle filters are harder, period. Need to argue this away, probably with the sample-weighting work as a within-filter controlled comparison.
- A clean "prompt precision" metric. Right now it's intuition + per-filter retrospectives. Could we score prompts on something measurable (length-normalized constraint count, oracle agreement on held-out items, etc.)?
- One ablation: same dataset, two prompts, two trained students. Have we done this anywhere? If not, one filter worth ~1 week to add.

**Venue.** arXiv tech report. ~4-6 pages.
