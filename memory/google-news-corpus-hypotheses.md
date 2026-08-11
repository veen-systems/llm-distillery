# Google News in the corpus — what is confirmed, refuted, untested

Created 2026-08-11. Google News is the largest single population in the corpus and
touches training labels, scoring, dedup and publication. This file exists so the
next session does not re-derive it — and does not repeat the four denominator
errors that were made deriving it.

**Read this before quoting any GN number.**

---

## The three populations — never conflate them

| pop | definition | items | % of corpus | % of GN |
|---|---|---|---|---|
| **A** | `gn_*` country proxies (59 feeds) | 8,302 | **14.9%** | **57.8%** |
| **B** | publisher-named feeds repointed to GN, `site:` queries (243 feeds) | 6,055 | 10.8% | 42.2% |
| C | `google_news_*` topic queries | folded into B by source name | — | — |

Measured on NexusMind `data/raw`, 17 cycles from `20260808_1710`, 55,848 items.

**Match GN on `'news.google.com' in url`, never on a `gn_` key prefix** — the prefix
identifies only population A and under-counts total GN roughly 5:1 in config.

**A is 5.6× more productive per feed than B** (141 vs 25 items). This kills the
inference "59 feeds is a fifth of 302, so A can't be the mass" — feed count says
nothing about item mass. That inference was made and retracted 2026-08-11.

---

## CONFIRMED

**Every GN item is a sub-300-char headline echo. 100.0%, both populations.**
A: n=8,302, median **89**, max **277**. B: n=6,055, median **83**, max **283**.
Neither population contains a single item reaching 300 characters. Content is the
title plus the outlet name. Combined with NexusMind#310 (the redirect URL is
unrecoverable, so enrichment can never succeed), GN rows are **content-free at
collection and unfixable downstream**.

**Training corpora are 0–4.9% GN; production is 25.3–25.5%.**
`solutions v6` 4.9%, `investment_risk v6` 2.5%, `uplifting v7` 1.1%, and
`nature_recovery v4` / `belonging v1` / `cultural_discovery v5` are **0.0%** — three
filters score a quarter of the firehose having never seen it in training.

**The oracle scored GN blurbs differently per filter, and the ordering reproduces
in production.** GN÷long mean-label ratio vs GN share of surfacing ÷ share of
corpus: `investment_risk` 1.79× → 0.90, `solutions` 1.13× → 0.65, `uplifting`
0.55× → 0.16. Monotone across all three. n=3 filters — an ordering, not a fit.

**GN reaches readers at 1.1% overall but 8.2% of `nature_recovery`.**
39 of 3,529 published (ovr.news `live_articles`), cross-checked by `source` and by
url. Attenuation from surfacing to published is **1.5×–20.8×**, not uniform:
nature_recovery 1.5×, solutions 3.0×, cultural_discovery 3.5×, uplifting 5.1×,
belonging 20.8×. **Nobody has explained the 14× spread**; dedup + the publication
window is a guess.

**Published GN scores are mostly defensible; the publishing is not.** Judging all
39 (complete population, not a sample): ~33 headlines genuinely support their
score. Two real problems — see #106 (Kačanik, ethno-national framing under
`belonging`) and #107 (Cambodia, a ruling not a defect).

**Half of `nature_recovery`'s published GN output is duplicate stories.** 19
articles → **9** distinct stories; Nepal's tiger census published **six times**,
all through `gn_asia_gn_nepal`, six outlets' headlines, different bytes. Posted to
NexusMind#188.

**FluxusSource#144's mis-stamp had exactly one live consumer.**
`type_classification` is read only by `src/scoring/source_filter.py` (NM#189);
`metadata.primary_literature` has **zero** readers in NexusMind `src/`.
`investment_risk v6` is the only deployed filter excluding `academic`.
Population A was **100.0%** stamped `academic` (4,034/4,034); B is heterogeneous.
The discriminator is the **`site:` operator**, not the population — a GN feed with
no `site:` cannot resolve to a publisher and falls through to `google.com`.

---

## REFUTED

**"~96% of GN surfacing rows are removed downstream."** My denominator error —
`solutions`' 16.5% surfacing share compared against the **all-filter** 1.1%
published share. Real attenuation is 1.5×–20.8×. There is no single 96%-effective
filter to lose.

**"GN production rows will score like their GN training labels."** Withdrawn.
`investment_risk v6`'s GN training rows have mean oracle label **4.207** against a
4.25 op-point, which implied ~half would surface. **Measured: 20.2%** (n=2,835 GN
rows v6 already scores) against **23.1%** for non-GN — GN surfaces *less*, not
more. The student did not inherit the oracle's generosity; the label level does not
transfer, only the ordering. Recorded on #92.

**"A Nepal story arrived through a Zambia proxy" (would have been FluxusSource#133).**
A grouping artifact — crude ≥3-shared-token matching merged "Endangered Wild Dogs
Return to Malawi's Kasungu National Park" into the Nepal tiger cluster on words
like *return*, *population*, *national*, *park*, and also merged the Kazakhstan
rewilding story in. All six Nepal copies come through **one** feed. The finding is
story-level clustering (NM#188), **not** content-hash dedup (FS#133).

**"ADR-007's native migration closes the 25%/5% gap."** Overstated. Retiring
population A closes **14.9 of 25.7 points — 58%**. Population B is 10.8% of the
corpus with the identical defect and ADR-007 does not cover it; it needs bulk
repointing with `scripts/gn_to_native_upgrade.py`. **Two levers, not one.**

**"ADR-007 has stalled."** No. GN share is 24.1% before the first migration batch
vs 25.1% after (67 vs 18 cycles, 301k items), but that is what a 6-feed batch
against 311 remaining GN URLs predicts. The 6 African feeds did land. The `202`
gn_* count in `20260808_120948` reads as a migration step and is ordinary cycle
variance — that was also the day's smallest cycle, and gn_* was 846 three days
later.

---

## CONFIRMED BY MIGRATION — native feeds fix the text

The 6 feeds migrated 2026-08-08, collection stage, 17 cycles:

| | n | median | sub-300 |
|---|---|---|---|
| 6 migrated feeds, native URL | 166 | **326** | **47.0%** |
| A: `gn_*` proxies | 8,302 | 89 | 100.0% |
| C: non-GN baseline | 41,325 | 188 | 69.2% |

Median **89 → 326**, sub-300 **100% → 47%**, landing *above* the non-GN baseline.
Migration replaces a headline echo with real body text — it fixes the mismatch
rather than relabelling it. n=166 is modest; a share moving off exactly 100.0%
cannot be sampling.

---

## UNTESTED — the open questions

1. **Are the refused rows mislabelled?** #105 shows today's labelling gate refuses
   51.6% of `investment_risk v6`'s training corpus and 52.2% of
   `cultural_discovery v5`'s. Whether a refused row carries a *bad label* is
   unmeasured. This separates "the rule tightened" from "the corpus was
   contaminated" and gates any retrain.
2. **Why does attenuation vary 14× across filters?** Guess: dedup + publication
   window. Not measured.
3. **Do headline-only items cluster?** Hypothesis for NM#188: 79–126 chars is too
   little text for an embedding matcher. Cheap discriminator — compare
   cluster-assignment rates for sub-300 vs ≥300 items over one window.
4. **Is the training GN population A or B?** Unknown, and it is the alternative
   explanation for the 4.207-vs-2.71 gap. Classify training GN rows by `site:`
   presence; cheap, not done.

---

## THE INSTRUMENT TRAP — read before measuring

**Do not oracle-re-score GN rows.** The 300-char labelling floor exists *because*
short content makes the LLM analyse the evaluation framework instead of the article
(`ground_truth.batch_scorer.make_oracle_prefilter` docstring, #93). Median GN
content is 89 chars. Re-scoring runs the instrument outside the range its own guard
defines. The valid substitute is a judge panel asking *"does the headline support
the score?"* — and note a pass makes this a **product** question (should
headline-only items publish at all), not a scorer defect.

**Four denominator errors were made in one day deriving this file** — two mine, two
the FluxusSource session's, each caught by the other. Every rate here carries its
denominator for that reason. `filtered_*.jsonl` is 100% prefilter passers and drops
source-type-excluded rows; `data/raw/` is pre-enrichment; ovr.db `live_articles`
excludes rotated-out items.

## Related

- [[prefilter-length-floor-hypotheses]] — #93, the length floor and its re-measure
- [[nexusmind-data-sources]] — which source excludes what
- [[cross-repo-prioritization]] — where the GN work sits against everything else
- #105, #106, #107 · FluxusSource#144, #145 · NexusMind#188, #310
