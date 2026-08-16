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

## CONFIRMED

**NexusMind's `pre_enrich` CANNOT enrich GN, and here is the nine-day
confirmation: 35,229 attempts, 0 replacements, 100.0% not 99.9%
(2026-07-31..08-08).** State it as mechanism + measurement, never as a bare
number — the two were derived independently, from opposite ends, and agree
exactly. ⚠️ **NAME THE FETCHER.** The unqualified form ("GN cannot enrich") is
**REFUTED** — see the block below: ovr.news resolves these URLs via Google's
`batchexecute` and enriched **74 of 103**. The mechanism is that *NexusMind has no
GN resolver*, not that the URL scheme forbids resolution.

- **Mechanism, pre-registered by FluxusSource before the gate** (their
  `docs/GN-REPLACEMENT-PLAN.md` § H4): a GN `ContentItem.url` is an opaque
  `news.google.com/rss/articles/…` **redirect**, not the publisher canonical, so
  `pre_enrich` fetching it receives a Google interstitial and never an article
  body. Predicted from the URL scheme alone.
- **Measurement**, the H4 run, now ours alone since FS#120 closed 2026-08-08 as
  moot under ADR-007. `C` = still under 500 chars among rows `pre_enrich`
  **actually attempted** — denominator is attempts, not arrivals: `gn_proxy`
  **35,229/35,229 = 100.0%** (CI 100.0–100.0) against `gdelt_constructive` 0.7%
  and `gnews_eval` 7.1%. *(`newsdata_eval` 20.3% — **pooling falsified by the
  script's own diagnostic, do not quote.**)*

**Consequence: the number will not drift *for this fetcher*.** Nothing NexusMind
changes about enrichment tuning moves it off 100%, because NexusMind has no GN
resolution at all — verified 2026-08-12:
`grep -rniE "batchexecute|data-n-a-sg|resolve.*google.?news" src/ scripts/`
returns **nothing**, so `pre_enrich` fetches the `news.google.com` URL directly and
receives the interstitial. It is also ruled out as an artefact from our side:
`SKIP_DOMAINS` is empty, `pre_enrich` receives the same list about to be scored,
and replacement needs ≥300 fetched chars while the longest GN row in the window is
277 — the flag and the length agree. This is the hard number behind NM#310.

⚠️ **REFUTED 2026-08-12 by the ovr.news session: "a property of the URL scheme, so
no fetcher change moves it" was an over-generalization from one fetcher to the
scheme, and it is false.** A resolver change is exactly what moves it. ovr.news
resolves these URLs and has since before June: `src/lib/google-news.ts:106-107`
scrapes the per-article `data-n-a-sg`/`data-n-a-ts` signature off the stub, posts
it to Google's private `batchexecute` endpoint (`:43`), and then fetches the
**publisher** URL. Measured on ovr's live DB: **74 of 103 GN rows enriched
successfully**, median 95 chars in → 3,074 out, most recent success 2026-08-12
06:58 — live, not historical. (Scope that number when quoting it: `article_enrichments`
is written only on success and ovr's `articles` table holds post-scoring survivors,
so 74/103 is a success rate on GN rows that *reached* ovr, not a resolver success
rate on the GN population.)

**Two measurements, both correct, one bad inference on top of mine.** The rule that
survives: state the fetcher. NexusMind's `pre_enrich` cannot resolve GN; ovr's
enrichment can. **The damage this did before it was caught:** it licensed a "do not
fix the GN resolver" recommendation which, acted on, would have retired a working
capability carrying 22 of ovr's 38 GN-derived published articles — and it had
already propagated into ovr.news#312 line 20 (*"Per NexusMind#310 these URLs can
never resolve"*) as a premise about a resolver it does not describe. This is the
[[feedback-rate-needs-population]] shape applied to a mechanism instead of a rate:
the measurement had a population and the generalization dropped it.

**Consequence for the consolidation question:** moving enrichment upstream to
NexusMind would *lose* GN resolution entirely, since there is no resolver there to
move it to. That is a live argument in the deferred *should ovr.news enrich* call,
not a tidiness preference.

⚠️ **Do NOT recruit this into an argument for FS#145.** #145 recovers the native
publisher *domain* from `entry.source.href` for attribution and filtering; it does
**not** yield a fetchable canonical article URL, so it cannot rescue a single one
of the 35,229. Unrelated levers. What it does sharpen is ADR-007 D1's migration
case **on stub grounds specifically**: every GN row is a *permanent* stub, not a
badly-enriched one. That coexists with the CDF finding rather than contradicting
it — a permanent stub floor that barely moves normalized scores is precisely a
slow structural win rather than a fire.

The window cannot be extended — from 08-09 the eval arms are source-type-excluded
and from 2026-08-11T14:06Z they stop upstream.
<!-- verify: manual — ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && python3 - --start 2026-07-31 --end 2026-08-08' < scripts/gate/measure_enrichable_rate.py -->

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
url. ⚠️ **Population caveat added 2026-08-16: `live_articles` is a legacy view, off
ovr's build path** (the site reads `getArticlesForBuild`), so "published" here means
*in that view*, not *served to a reader*. The ratios are between two quantities
measured the same way and are unaffected; the word "published" is what is loose.
See `memory/nexusmind-data-sources.md` for the corrected source. Attenuation from surfacing to published is **1.5×–20.8×**, not uniform:
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

**The GN-removal experiment is an UPPER BOUND on the phase-out, and the phase-out
lands without incident downstream (2026-08-12).** The CDF residue measurement fits
each filter's normalization twice on the same population, once with all GN rows
*deleted*. Forecast: max normalized Δ **0.367** (`nature_recovery v4`; `belonging`
0.128), **0.0%** of articles move ≥0.5, and every crossing of NexusMind's
normalized-4.0 enrichment gate is **downward** (0.28–1.13% per filter, zero the
other way). No refit emergency, no surfacing change — a normalized score cannot
move visibility (ADR-022) — and slightly *less* enrichment volume. This is what
closed #106. Evidence: `docs/evidence/2026-08-12-gn-share-of-normalization-cdf.md`.
<!-- verify: manual — PYTHONPATH=. python scripts/research/gn_normalization_cdf_share.py --ssh sadalsuud -->

⚠️ **The arm deletes ALL GN; ADR-007 retires population A ONLY — say which
population, always** (corrected by the FluxusSource session the same evening, my
error). A = 55–59 enabled country proxies. **B (230 enabled) is not in scope and is
hard by construction** — those keys were repointed to GN *because* the native feed
died. **C (13 topic queries) can never be migrated at all**, having no `site:`
operator and so no publisher to return to, so even a perfect A+B programme leaves a
**permanent GN floor**. The decided deletion is strictly smaller than the one
measured, so the *safety* claim is conservative in the right direction and holds;
nothing else transfers. **There is no target date and no rate, by design** —
ADR-007 Decision 1 retires a proxy only behind a native replacement verified
collecting in production, so it arrives as many small unscheduled per-country
batches. **Do not infer a curve from the 6-feed Africa batch. FS#145 is an
attribution instrument, not a migration lever** — do not cite it as the phase-out;
ADR-007 is.

⚠️ **0.367 is a FLOOR, not a ceiling — and this is arithmetic, not measurement.**
The experiment measured *deletion*; migration is *replacement*. The 6 feeds
migrated 2026-08-08 went median 89 → 326 chars, sub-300 100% → 47%, landing
*above* the non-GN baseline — those rows re-enter the CDF at higher scores rather
than vanishing, which pushes percentiles down further than deletion does. **Second
term, pointing the other way: some retirements behave as DELETIONS** — ADR-007's
own example is a native feed yielding 0 items against a GN twin yielding 169, so a
"migrated" country can arrive with a replacement that delivers no mass. Both terms
unmeasured. Carried on #71 §3. **Consequence: trigger any refit on a measured GN
share crossing a threshold in our own fit population, never on an upstream
retirement event** — their events are many, small and unscheduled, and our
instrument already reads the quantity that matters.

**"GN gone" is NOT "stubs gone", and "GN gone" is not even a decided outcome.**
Measured on `belonging`'s 17:04 filtered file 2026-08-12, n=3,242: sub-300-char
content is **932 rows (28.7%)**, of which **65.2% is GN** (608 rows). Deleting
**all** GN leaves **324 rows = 10.0%** still sub-300. ⚠️ **That two-thirds
shrinkage is the ALL-GN figure and does not describe the decided scope** — 65.2%
is A+B+C and only A is decided. The nearest split anyone holds (NexusMind, 8
cycles, 2026-08-08, short rows surviving to surfacing on `solutions`: A 13.6/cycle,
B 5.4, C+other non-GN 2.6) puts A at ~63% of GN-attributable short rows, so the
decided scope removes nearer **~40%** of stubs. **Do not quote the 40%** — different
lens, metric and date, composing two separately-measured populations; it is an
order-of-magnitude caution. The durable point needs none of the arithmetic:
**do not budget for a GN phase-out, and never let one be sold as a fix for
short-content scoring.** The ADR-023 specificity question survives at reduced size.
<!-- verify: manual — recount sub-300 and GN share on the latest data/filtered/belonging/filtered_*.jsonl on sadalsuud; content_length lives at nexus_mind_attributes.<lens>.content_length, NOT analysis.* -->

⚠️ **That 18.8% GN share of one lens's scored rows is NOT comparable to the
corpus-wide 25.7%** — different denominators (post-dedup, post-prefilter, one lens
vs `data/raw` over 17 cycles). Do not read the difference as a decline. As of
2026-08-12 there is still **no detectable decline**: pooled 24.83% → 23.69% across
the two halves of a 15-day window, daily range 19.8–29.5%, 6 of ~59 proxy feeds
moved.

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
repointing with FluxusSource's `scripts/gn_to_native_upgrade.py`. **Two levers, not one.**

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
excludes rotated-out items **and is a legacy view off the build path — it is not the
reader population** (corrected 2026-08-16, see `memory/nexusmind-data-sources.md`).

## Related

- [[prefilter-length-floor-hypotheses]] — #93, the length floor and its re-measure
- [[nexusmind-data-sources]] — which source excludes what
- [[cross-repo-prioritization]] — where the GN work sits against everything else
- #105, #106, #107 · FluxusSource#144, #145 · NexusMind#188, #310
