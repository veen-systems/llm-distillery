# Which tab should a multi-lens article go to? A benchmark against the owner (pre-registered 2026-09-26)

**Owner, 2026-09-26:** likes rule ideas 1 and 3, asked about a dedicated model, and said "yes pls" to measuring
first. ovr.news today collapses each article to the lens with the highest NORMALIZED score
(`ovr.news/src/lib/data/canonical-lens.ts`). Percentile normalization is healthy per lens (this week's normalized
quartiles are ~2.5/5/7.5 in all five lenses), but it answers "how exceptional within its lens", not "which lens is
it about": on the 133 NR+Solutions articles, NR raw median 5.05 → 5.61 normalized, Solutions raw 4.44 → 9.29.

## Population
Articles passing ≥ 2 of the five reader-facing lenses in the production week `filtered_20260918_14*` →
`filtered_20260925_10*` (stage2, raw ≥ each lens's runtime op-point: Thriving = uplifting v7 4.5, Belonging 4.0,
Cultural discovery 4.0, Nature recovery 3.75, Solutions 2.25): **5,543**.

## Sample (seed 20261001): 100, stratified. Rates are reported per stratum and re-weighted by N
| stratum | N | drawn |
|---|---|---|
| any combination with Nature recovery | ~161 | 25 |
| with Cultural discovery (no NR) | ~828 | 20 |
| Solutions + Thriving | 3,022 | 20 |
| Belonging + Thriving | 881 | 15 |
| Belonging + Solutions + Thriving | 626 | 15 |
| Belonging + Solutions | 25 | 5 |
(N is recounted by the builder and must match to within the rows the strata above leave out, which are reported.)

## The benchmark: the OWNER, judging first
For each article, shown as title + faithful translated text, the owner answers: **which tab should it be on?**
Choices: the lenses it passed, "none" (junk on every tab), or two tabs ("truly both"). Blind: no scores, no rule
outputs, no judge verdicts. Two independent blind Claude passes answer the same question (A and B); they measure
whether an automated labeller could produce training data for a dedicated model. They do not change the benchmark.

## Rules scored against the owner (computed from stored scores; nothing new is run)
- **R0, today:** highest normalized `weighted_average`.
- **R1, narrow lens first:** the fixed order Nature recovery > Cultural discovery > Belonging > Solutions > Thriving,
  which is ascending weekly pass volume (174 / 2,594 / 3,778 / 5,814 / 11,135), fixed now.
- **R3, margin above its own cut-off:** highest (raw − op-point). **R3b** (secondary): highest (raw − op) / (10 − op).
A rule scores a hit when it picks the owner's tab, or either of the owner's two. "None" rows are excluded from rule
accuracy and reported separately; they are junk that reached the site through every lens it passed.

## Reported
Per stratum and N-weighted: hit rate of R0, R1, R3 and R3b with Wilson 95%; owner-vs-judge agreement; the count of
"truly both". **No bar and no decision here.** The owner chooses the rule, or the model route, from the numbers.
A rule is "not distinguishable" from another when their paired intervals overlap.
