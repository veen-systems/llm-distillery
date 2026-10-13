# belonging: how ovr.news ranks the page, reproduced offline (2026-10-13)

H-BB7 (`memory/hypothesis-ledger.md`): the page's top is not v3's raw top. `docs/TODO.md` item 0a, option 1, chosen
by the owner on 2026-10-13 ("pls do that"): rebuild the top-of-page check on the site's own ranking before any
retrain. $0 oracle, no model run. ⚠️ **Not pre-registered.** This is an instrument check: it asks whether a
deterministic formula reproduces a page. It is not a test of any model, and it moves no bar.

Run: `python3 docs/evidence/2026-10-13-belonging-site-ranking/site_rank.py` → `result.txt`. The inputs are in
this directory: ids, dates and scores only, no article text. The script's docstring says where each came from.

## The formula, read from ovr.news `c4aa42a3`

`rank = weighted_average (NORMALIZED) × 0.85^age_days × 1.3 if age < 24 h` (`src/lib/ranking.ts`, constants in
`src/lib/config.ts` `ranking`; the language boost is 1.0). The population is `getArticlesForBuild('belonging', 4.5,
10)`: summarised rows with a normalized score ≥ 4.5 that are at most 10 days old.

The Chief Editor runs after the first sort, but `pipeline.ts` then RE-SORTS each lens by the cached `_displayRank`.
So the two editor rules that only reorder (`corroboration-boost`, `source-diversity`) leave no trace on the page.
The rules that remove rows (editorial gate, obituary, canonical lens, cluster dedup) do. A comment in
`editor/index.ts` already notes the re-sort. Whether the lost boosts were intended is a question for ovr.news;
nothing here depends on the answer.

## Measured

| test | result |
|---|---|
| **1. live page**, built 2026-10-13T06:43:02Z, 507 cards | **507/507 positions reproduced.** All 507 cards are in the build population (710). The 203 not shown were removed after the sort |
| **2. the owner-labelled page** of 2026-10-12 (`../2026-10-12-belonging-personal-tag/tags.tsv`) | **30/30 positions reproduced** at build times 14:30–14:50Z. The build time is unknown, so it was scanned on a 10-minute grid and only those 3 slots match, which makes this a FIT. 1 row ranked above #30 was not shown (removed) |
| top 30 published < 24 h before the build | **30/30** (10-13); **29/30** (10-12, the oldest at 24.1 h) |
| 10-12: rows in the 10-day window / rows < 24 h old | 758 / **43** |
| 10-12: page top 30 that are also in the top 30 by normalized score alone | **0** |

## What it means (inference from the measurements; nothing below was measured on its own)

- **The reorderer in H-BB7 is recency, not an editor.** The 1.3× boost for < 24 h, together with 0.85/day decay,
  puts essentially the last day's passes on top. The top 30 is about the best 30 of a day's ~43 fresh passes.
  That explains why the c2c composition check (raw top 30 over a 12-file draw: 5 personal by qwen) and the page
  (7 by qwen, 10 by the owner) disagreed: they were different populations.
- **So the owner's bar, "≤ 6 of the top 30", is close to a bar on the personal SHARE of one day's passes.** It is
  one day, n ≈ 30, so it will move from day to day. The 10-12 count of 10 is one draw from that distribution.
- **A candidate check can now be built on the site's ranking.** For each daily build time across a draw window,
  take the candidate's passes, apply `rank()`, take the top 30 and count personal, then report the distribution
  over days. The script's `site_order()` is that ranking. Two inputs are still missing:
  (a) a normalized score for a candidate, which needs its own `normalization.json`, or v3's mapping applied to
  the candidate's raw score as an approximation;
  (b) the editor's removals, which are known only for rows ovr.news actually processed.
  The set of rows in a day's top 30 depends mainly on which rows PASS. Their order depends on the normalization.
- **For a candidate that only lowers personal stories to just above the op-point** (the c2c design), the
  recency term means a fresh personal pass still competes for a top-30 slot. It loses only to fresh passes that
  score higher, and about 30 of ~43 fresh rows make the cut. A GUESS, not measured: such a candidate would remove
  some personal stories from the top, not most. Only a row that falls below the op-point leaves the page for sure.

## Formula replay for ovr.news (2026-10-13, later)

The ovr.news session asked for this on the owner's behalf. Nothing ships from it. Formulas as they specified: A half-life
2 d, B half-life 3 d (neither has the 24 h boost), C score-first within age bands (< 72 h, 72 h–7 d, older), and the
current formula as the control. `replay.py` → `replay_result.txt`. The 10-13 inputs are each lens's live cards (build
06:55:18Z, ids/dates/scores only) in `lenses_20261013/`. The qwen tags are the two 10-12 lab files cited in
`MANIFEST.json`.

**Measured (from `replay_result.txt`):**
- **Overlap with today's top 30**, A / B / C: belonging 23 / 21 / 7, thriving 27 / 26 / 18, solutions 28 / 28 / 13,
  discovery 26 / 28 / 10, recovery 29 / 29 / 25. A and B are close to the current order. C replaces most of it.
- **Lowest normalized score in the top 30**, control → C: belonging 6.08 → 7.34, solutions 8.91 → 9.79 (raw 4.32 →
  4.84), discovery 8.39 → 9.59. A and B barely move the floor.
- **Age of the top 30 under C:** 7–16 under 24 h, the rest 1–3 days. Nothing older than 3 days, because band 0 holds
  more than 30 rows in every lens except recovery.
- **Normalized-score saturation, cards with s ≥ 9.5:** solutions 232/505, discovery 86/536, belonging 71/507,
  thriving 33/326, recovery 7/121. Where most of the top is near 10, the score cannot order it, so A and B fall
  back to age.
- **Belonging personal count, 10-12 labelled page:** control 9 owner-personal of 28 labelled (+1 of 2 by qwen);
  A 9 of 26 (+0 of 4); B 9 of 25 (+0 of 5); C 2 of 6 labelled (+2 of 19 by qwen, a floor) with 5 untagged.
  C's count is therefore NOT known. The 10-13 page is mostly untagged (control 24 of 30).
- **Rebuilding the 10-12 population** with "a removal is sticky for a day" gives 27/30 positions (28/30 overlap)
  for the control, against 30/30 without that step. So the approximation adds about 2 rows the page did not show.

**Reading (inference):** A and B change little anywhere, because recency still dominates and the normalized
scores saturate. C is the only option that raises the floor at the top, by roughly +1.2 normalized on belonging.
It does so by trading away same-day freshness. Whether C changes the share of personal stories cannot be told
from these labels. It needs qwen tags on C's untagged rows (b650, $0) and, for a real answer, the owner's eye.
The saturation is ovr.news ADR-050's point: until the score is re-normalized, a "score-first" default can only
partly rank by quality.
