# belonging v3 on ranking H: seven daily top-30 personal counts, replayed offline (pre-registration, 2026-10-15)

*Written and committed BEFORE any population is built, any page is read for removals, or any tag is read. Template:
`experiments/PREREGISTRATION.template.md`. Context: `docs/TODO.md` item 0a ("Before H ships, the same can be
replayed offline on H over the last 7 days. That is $0, needs no owner"). Method reused from
`../2026-10-13-belonging-daily-baseline/` (its scripts, its instrument), with H's order from
`../2026-10-13-belonging-site-ranking/replay.py` `order("H hybrid")`.*

## 0. What is under test, and the decision it feeds

- **Under test:** the count of `personal` stories among the top 30 v3-scored rows of ovr.news's Belonging page, if
  the page were ordered by **H** (owner ruling 2026-10-14: the 5 highest normalized scores under 24 h first, then
  score within age bands < 72 h / 72 h–7 d / older; ovr.news#391, not shipped). The current ranking ("control") is
  replayed on the same populations, as the paired comparison.
- **Bar:** ≤ 6 of 30 as a WEEKLY AVERAGE (`docs/decisions/2026-10-10-belonging-personal-story-bar.md`, ruled
  2026-10-14).
- **Decision fed: none directly.** It is the H "before" for candidate c2d (TODO 0a, "judge on H") and an early read
  of v3 on H. ⚠️ The instrument is a FLOOR (qwen undercounts personal; 7 vs the owner's 10 on 10-12), so only one
  direction is conclusive: **a qwen weekly mean above 6 means v3 fails the bar on H; a mean ≤ 6 leaves it
  undetermined.** It starts no rollback (over 6 is the owner's call, TODO 0).
- **Authority:** owner, 2026-10-15: "continue" (TODO 0a names this as no-owner, $0 work).

## 1. Population (the pipeline's own formula, not chosen by hand)

- **Builds (7):** 2026-10-09, 10-10, 10-11, 10-12, 10-13, 10-14 at 14:30Z (the reconstructed time of the
  owner-labelled page), plus 2026-10-15 at the live page's own build time (read from the page, step 2).
- **Rows:** sadalsuud's ovr.db (read-only), the same query as the baseline README step 1, with the date floor moved
  to 10 days before 2026-10-09 and no upper bound. Per build: summary created at or before the build, published at
  or before the build, published within the 10 days before it (UTC dates, as SQLite `date()`).
- **Removals (editor, canonical lens, dedup):** a row is dropped as removed if it was in a build population but not
  on that build's live page, for either of two observed builds: 2026-10-13 06:43Z (the committed
  `build_pop_20261013.json` minus `page_ids_20261013.txt`) or today's live page (fetched in step 2, against the
  population anchored at its build time). ASSUMPTION, as in the baseline: a removal is sticky. Rows observed by
  neither are kept, and their count is reported per build ("removal status unknown").
- **Version filter:** each id joined to NexusMind's `belonging.version` stamp (newest belonging `filtered_*.jsonl`
  holding it, the baseline's `extract_rows.py` unchanged). Keep `"3.0"`; take the first 30 v3 rows in each order;
  skipped rows are counted by stamp. **If fewer than 30 v3 rows rank in that order's top 60, the build is reported
  with N < 30 and left out of the weekly mean** (baseline rule, unchanged).

## 2. Instrument

- qwen3.8:27b on b650 via ollama, `focus` tag, the baseline's lab `system.txt` and `tag_qwen.py` copied unchanged
  (`~/ld-lab/experiments/2026-10-13-belonging-daily-baseline/tag/`): temperature 0, seed 42, num_ctx 16384.
  b650: confirmed free by ovr.news 2026-10-15.
- **Tag reuse:** an id already tagged in the baseline's `tag/out.jsonl` or the two 10-12 lab tag files keeps its
  tag; only new ids are tagged. **Determinism control:** 10 reused ids (chosen with `random.Random(0)` from the
  sorted reused set) are re-tagged in the same run. If fewer than 9 of 10 match, reuse is abandoned and every row
  is re-tagged, and that is reported.
- **Presence control:** the 10-12 build's control top 30 must contain qwen `personal` rows (the baseline counted
  8); a replay that counts 0 there is an instrument failure, not a result.
- Every count is a **qwen count (a floor)**, never the owner's.

## 3. What is reported

Per build and per order (H, control): N, in range, v1 rows skipped, removal status unknown, qwen personal / group
/ unparsed, and the number of top-30 rows under 24 h old. Across in-range builds, per order: the **weekly mean**,
the worst day, and the per-build paired difference H − control. Also: the control order's v3 top 30 for 10-11 and
10-12 compared with the baseline's `selection.json` (overlap, out of 30), as a check of the rebuild.

## 4. Predictions (scored after)

1. H per-build qwen personal: **2–8**.
2. H weekly mean **≤ control weekly mean** (10-12 replay: H's top 30 is mostly 1–3-day-old, higher-scored rows).
3. H top 30 holds **≤ 10 rows under 24 h** on every in-range build (10-12 / 10-13 replays: 5 and 7).
4. At least **4 of 7** builds are in range under H. (v1 rows were still draining through 10-10, and H reaches
   further back in age than control, so its early builds may fall short.)
5. Control rebuild vs baseline selection, 10-11 and 10-12: overlap **≥ 26 of 30** each (current scores and the new
   removal set can move a few rows).

## 5. Known limits

- ovr.db holds each row's CURRENT score, not the score on the day.
- One build per day at 14:30Z; real builds run several times a day.
- H is replayed as ovr.news specified it on 2026-10-13; the shipped H may differ (ovr.news#391). If it does,
  this replay is rerun on the shipped formula, not reinterpreted.
- Seven builds; the mean is descriptive, not an interval.
- qwen is a floor. See section 0 for what that allows.

## 6. Data

Inputs and outputs go through the lab: extraction on sadalsuud and tagging on b650 write under `ld-scratch/`, then
`scripts/lab/lab.py pull` into `~/ld-lab/experiments/2026-10-15-belonging-h-replay/`, cited in `MANIFEST.json`.
Article text stays in the lab; this directory holds ids, dates, scores and counts only.
