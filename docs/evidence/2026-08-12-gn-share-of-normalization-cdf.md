# Google News mass in the normalization CDF — measured, six filters

**Date:** 2026-08-12
**Issue:** #106 (owner ruling: *measure the CDF residue, then rule*)
**Reproduce:** `PYTHONPATH=. python scripts/research/gn_normalization_cdf_share.py --ssh sadalsuud`
**Source:** `sadalsuud:/home/jeroen/local_dev/NexusMind/data/filtered/*/filtered_*.jsonl`, 85 cycle files per lens

## The question

#106 was re-scoped once ovr#311 closed the reader-facing half: `belonging` gave
normalized **7.26 / tier high** to a 131-char Google News headline, and that
score still feeds cross-lens ranking and the **normalization CDF**. Closing the
issue assumed the CDF residue was negligible. Nobody had measured it.

Google News is 25.7% of the production corpus and **100.0% sub-300-char headline
echoes** that **NexusMind's `pre_enrich`** cannot enrich (NM#310 — 35,229 attempts, 0 replacements, because NexusMind has no GN resolver). ⚠️ Scoped 2026-08-12: the unqualified form "can never be enriched" is REFUTED — ovr.news resolves these URLs via Google's `batchexecute` and enriched 74 of 103. Always name the fetcher. Normalization is fitted at
`raw_weighted_average >= the filter's operating point`, so GN rows that clear
the op-point enter the CDF that maps every real article's rank.

## Method

The fit population was traversed with a **mirror of
`fit_normalization.py::load_weighted_averages_ssh`** — same nesting, same
raw-vs-fallback rule, same threshold comparison — so the counted rows *are* the
fit population rather than an approximation. GN was matched on
`'news.google.com' in url`, **never on a `gn_` source-key prefix**, which
identifies only the country-proxy population and under-counts total GN roughly
5:1 (`memory/google-news-corpus-hypotheses.md`).

The repo's own `filters.common.score_normalization.fit_normalization` was then
run **twice per filter** on the same population — once as-is, once with GN rows
removed — with the same `anchor_min`. Both mappings were applied to the
**non-GN** articles, which is what a reader sees ranked. GN presence is
therefore the only variable.

## Result

| filter | op-point | n_fit | GN in fit | GN % of fit | max Δ | median Δ | share moving ≥0.5 |
|---|---|---|---|---|---|---|---|
| `uplifting v7` | 4.5 | 15,863 | 542 | 3.4% | 0.077 | 0.058 | **0.0%** |
| `investment_risk v6` | 4.25 | 38,957 | 3,537 | 9.1% | 0.048 | 0.018 | **0.0%** |
| `cultural_discovery v5` | 4.0 | 3,799 | 106 | 2.8% | 0.077 | 0.049 | **0.0%** |
| `belonging v1` | 4.0 | 5,534 | 187 | 3.4% | 0.128 | 0.085 | **0.0%** |
| `nature_recovery v4` | 3.75 | 397 | 48 | 12.1% | **0.367** | 0.141 | **0.0%** |
| `solutions v6` | 2.25 | 8,884 | 1,464 | 16.5% | 0.234 | 0.120 | **0.0%** |

Δ is the absolute change in a non-GN article's **normalized** (0–10) score when
the GN mass is removed from the fit.

**The op-point already de-selects GN in four of six filters.** GN is ~24% of the
scored passers in each lens directory but only 2.8–3.4% of the `uplifting`,
`cultural_discovery` and `belonging` fit populations — the models are scoring
the stubs below the op-point, which is the correct behaviour. The three filters
carrying a material GN share are the ones with the lowest or least selective
op-points (`solutions` at 2.25, `nature_recovery` at 3.75) plus
`investment_risk`, whose GN median score (5.242) sits almost exactly on its fit
median (5.274).

## Direction, and the one consumer that changes an outcome

A normalized score **cannot move visibility** — visibility is `raw >= op-point`
(ADR-022), and normalized is rank/badge only. The single consumer where a
normalized shift changes an outcome is NexusMind's
`pipeline.enrichment.min_score` = **4.0** (`config/app.yaml`), which reads the
**normalized** score (NM#319).

| filter | non-GN articles | crossing normalized 4.0 | share | direction |
|---|---|---|---|---|
| `uplifting v7` | 15,321 | 119 | 0.78% | 119 would fall **under** / 0 rise over |
| `investment_risk v6` | 35,420 | 101 | 0.28% | 101 under / 0 over |
| `cultural_discovery v5` | 3,693 | 23 | 0.62% | 23 under / 0 over |
| `belonging v1` | 5,347 | 60 | 1.12% | 60 under / 0 over |
| `nature_recovery v4` | 349 | 3 | 0.86% | 3 under / 0 over |
| `solutions v6` | 7,420 | 84 | 1.13% | 84 under / 0 over |

**The direction is uniform and one-way.** GN rows sit at the low end of every
fit population (GN median score below the fit median in five of six filters), so
their presence *inflates* the percentile of everything above them. Removing GN
would push 0.28–1.13% of real articles **below** the enrichment gate; not one
article anywhere moves the other way.

So the residue's effect is **more enrichment, not less**, and it cannot surface
anything — under ADR-023 that is the cheap direction, not the expensive one.

## What this does not establish

- **Not** that GN mass is harmless in general — this measures the CDF channel
  only. The cross-lens *ranking* channel is closed separately, by ovr#311
  refusing to summarize a stub, and `getArticlesForBuild` inner-joining
  `summaries`.
- **Not** a claim about already-published items. ovr#311's guard is prospective;
  324 previously-published expanded summaries are untouched (ovr#311, "what is
  left"), which may still include the Kačanik article that opened #106.
- **Not** a re-derivation of the deployed `normalization.json` files. Those were
  fitted at earlier times on smaller populations (`nature_recovery v4`'s
  committed file records n=272; the population is now 397). Both arms of this
  comparison were fitted on the *same* current population, which is what isolates
  GN as the variable — the absolute mappings here are not the deployed ones.
- **Source exclusions:** `filtered_*.jsonl` holds only prefilter passers and
  drops source-type-excluded rows. That is the correct source here because it is
  the same source the fitter reads, but it is **not** the production corpus, so
  the ~24% GN share of these directories is not comparable to the corpus-wide
  25.7%.

## Consequence for #106

The premise the "close it" option rested on is now measured rather than assumed,
and it holds: with publication blocked upstream, the residual cost of
`belonging` mis-scoring stubs is a ≤0.13 normalized shift on that filter,
pointing toward more enrichment.

The largest residue in the set is **`nature_recovery v4` at 0.367**, and it is
not a `belonging` problem at all — it is a small-fit problem. Its fit population
is 397 rows against a `MIN_NORMALIZATION_ARTICLES` floor of 200, with 12.1% GN.
That is worth carrying into #71 (`nature_recovery v5`) as a refit note, not
worth a change on its own.
