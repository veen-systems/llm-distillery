# belonging v3 on the LIVE H page: seven daily top-30 personal counts (EXP-056, pre-registration, 2026-10-21)

*Written and committed BEFORE any page's top-30 ids are tagged or any tag is read. Source: `docs/TODO.md` item 0a,
"the on-site re-baseline of v3 on the LIVE H page". Method: EXP-049's (`../2026-10-15-belonging-h-replay/`) with the
offline replay replaced by the pages themselves, since H has been live since 2026-10-15 07:40:42Z.*

## 0. Under test, and the decision it feeds

- **Under test:** the count of `personal` stories among the top 30 v3-scored cards of https://ovr.news/en/belonging/,
  as SERVED under ranking H, on each of 7 daily builds.
- **Bar:** ≤ 6 of 30 as a WEEKLY AVERAGE (`docs/decisions/2026-10-10-belonging-personal-story-bar.md`, ruled
  2026-10-14).
- **The instrument is a FLOOR.** qwen undercounts `personal`: 7 against the owner's 10 on 10-12. So only one direction
  is conclusive:
  - a qwen weekly mean **> 6** means v3 FAILS the bar on the live page;
  - a mean **≤ 6** is **UNDETERMINED**, and the owner's own count is the stronger instrument (offer it).
- **Decision fed:** ducroq/ovr.news#391 closes on this count (ovr EXP-060). Over 6 is NOT an automatic rollback: that
  is the owner's call (TODO 0).

## 1. Population (the page itself, not a replay)

- **Pages:** the daily capture `belonging_<UTC>.html` at 14:30Z, 2026-10-15 to 2026-10-21 (7 files), moved from
  `~/lab/llm-distillery/inbox/ovr-lens-pages/` into this experiment's lab tree with `lab.py move`. The two hand
  captures from the morning of 10-15 (T0750Z, T0755Z) are NOT in the series.
- **Card order:** `data-article-id` attributes in document order, de-duplicated with the first occurrence kept.
  - Parser check (done before this file, no tags read): on the 10-15 T0750Z capture it finds 520 unique cards. 495
    of them are among EXP-049's 521 cards, which were fetched at 07:01Z, BEFORE H went live.
  - The top-30 overlap with that list is 6 of 30. That is expected: the order changed, the set did not.
- **Version filter:** each page's top-60 ids are joined to NexusMind's `belonging.version` stamp with EXP-049's
  baseline `extract_rows.py`, unchanged (on sadalsuud, read-only). The first 30 rows stamped `"3.0"` in page order are
  kept; rows skipped are counted by stamp. **Fewer than 30 v3 rows in a page's top 60: that build is reported with
  N < 30 and left out of the weekly mean** (baseline rule).

## 2. Instrument (EXP-049's, unchanged)

- **Tagger:** `qwen3.8:27b` on b650 via ollama, `focus` tag. Lab `system.txt` + `tag_qwen.py` are copied byte for byte
  from `experiments/2026-10-15-belonging-h-replay/tag/tag/` and run on b650 (localhost ollama): temperature 0, seed
  42, num_ctx 16384, think off.
- **b650:** daytime only (infra's SovereignStack holds 00:00–07:00). Before loading, `api/ps` must show no model we
  did not load.
- **Tag reuse:** an id already tagged in any earlier belonging tag file in the lab keeps its tag; only new ids are
  tagged.
- **Determinism control:** 10 reused ids (`random.Random(0)` over the sorted reused set) are re-tagged in the same
  run. Below 9 of 10 matching, reuse is abandoned, everything is re-tagged, and that is reported.
- **Presence control:** across the 7 builds the tagger must label at least one top-30 row `personal`. A week of zeros
  is an instrument failure, not a result.
- **Unparsed tags** (`focus` = None) are reported per build and counted as NOT personal. That is the floor direction,
  stated.

## 3. Reported

- **Per build:** N, v1/other rows skipped, qwen personal / group / unparsed, and how many of the top-30 rows are
  under 24 h old (from the page if it shows a date; otherwise not reported).
- **Across the in-range builds:** the **weekly mean**, the worst day, and the best day.

## 4. Predictions (scored after)

1. **Weekly qwen mean in [4, 7].** Basis: EXP-049's dated replay of H gave 5.20, and the owner's 10-12 count was 10 on
   the old ranking.
2. **P(mean > 6) is about 0.35**, so the most likely verdict is UNDETERMINED.
3. **At least one day > 6** (the worst day). Daily counts in EXP-049 ranged up to 8.
4. **All 7 builds in range** (N = 30): v1 rows aged out of the 10-day window by about 10-19, and the 10-15 page had
   v1 cards.

## 5. Spend and authority

$0 (local qwen). Authority: owner 2026-10-21, "pls continue"; TODO 0a names this as no-owner work at $0.
