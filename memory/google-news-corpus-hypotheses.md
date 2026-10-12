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

**Match GN on `'news.google.com' in url`, never on a source-key prefix** — a key
prefix identifies only population A and under-counts total GN roughly 5:1 in config.

⚠️ **The undercount factor is DIFFERENT for feeds, rows and items — which is why a
sanity check does not catch it.** Derived from the table above, on its own numbers:
a `gn_` prefix catches 59 of 302 feeds (**5.1×** low) but 8,302 of 14,357 GN items
(**1.73×** low). So the same wrong matcher reads *plainly broken* at feed level and
*roughly right* at item level — an analyst who spot-checks the item share sees 57.8%,
calls it plausible for "most of GN", and ships a feed population off five-fold.
**Check the unit your conclusion is denominated in, not the one that is easiest to
count.** This is the mechanism behind two of the four denominator errors below.

**Sharpened 2026-08-11 by the FluxusSource session, which hit the same defect from
the other side.** The rule above was stated too narrowly. Emitted `source` keys are
**category-prefixed** — `ai_google_news_ai_engineering`, not
`google_news_ai_engineering` — so `startswith("google_news_")` silently misfiles the
entire topic-query population into the publisher-named bucket, and `startswith("gn_")`
works only by accident of prefix. FS reported a population-C count of **zero** from
exactly this before catching it. **Classify against the configured feed URL —
`site:` present or absent — not the key.** Two independent occurrences of one
defect, in two repos, within days.

**A is 5.6× more productive per feed than B** (141 vs 25 items). This kills the
inference "59 feeds is a fifth of 302, so A can't be the mass" — feed count says
nothing about item mass. That inference was made and retracted 2026-08-11.

---

## CONFIRMED · REFUTED · CONFIRMED BY MIGRATION — MOVED to [`archive/google-news-corpus-hypotheses-archive.md`](archive/google-news-corpus-hypotheses-archive.md) (2026-10-12)

- **NexusMind's `pre_enrich` cannot enrich GN**: 35,229/35,229 attempts stay under 500 chars (2026-07-31..08-08), because
  the GN url is a redirect and NexusMind has no resolver. ⚠️ **NAME THE FETCHER** — ovr.news resolves them via
  `batchexecute` and enriched 74 of 103, so the unqualified "GN cannot enrich" is REFUTED.
- Every GN item is a sub-300-char headline echo (100.0%); training corpora are 0–4.9% GN against 25.3–25.5% in
  production; GN reaches readers at 1.1% overall but 8.2% of `nature_recovery`, half of it duplicate stories.
- The GN-removal experiment is an UPPER BOUND on the phase-out (ADR-007 retires population A only); "GN gone" is not
  "stubs gone" — do not budget for a GN phase-out as a stub fix.
- REFUTED: "~96% of GN surfacing rows are removed downstream" (attenuation is 1.5×–20.8×); "GN rows score like their GN
  labels" (20.2% vs 23.1% non-GN); "ADR-007 closes the gap" (A closes 14.9 of 25.7 points; B needs repointing);
  "ADR-007 has stalled" (no).
- CONFIRMED BY MIGRATION: 6 native feeds took median length 89 → 326 and sub-300 100% → 47% (n=166).

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
excludes rotated-out items **and is a legacy view off the build path — it is not the
reader population** (corrected 2026-08-16, see `memory/nexusmind-data-sources.md`).

## Related

- [[prefilter-length-floor-hypotheses]] — #93, the length floor and its re-measure
- [[nexusmind-data-sources]] — which source excludes what
- [[cross-repo-prioritization]] — where the GN work sits against everything else
- #105, #106, #107 · FluxusSource#144, #145 · NexusMind#188, #310
