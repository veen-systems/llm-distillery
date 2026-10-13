# belonging v3: how much the top-30 personal count moves from day to day (pre-registration, 2026-10-13)

*Written and committed BEFORE any population is built or any tag is read. Template:
`experiments/PREREGISTRATION.template.md`. Context: `docs/TODO.md` item 0a; the instrument is
`../2026-10-13-belonging-site-ranking/` (`site_rank.py`, `replay.py`).*

## 0. What is under test, and the decision it feeds

- **Under test:** day-to-day variation in the count of `personal` stories among the top 30 of ovr.news's Belonging
  page, with v3 scoring and the site's CURRENT ranking. The owner's one count (10/30 on the 2026-10-12 page) is a
  single day. The site-ranking evidence showed the top 30 is about one day's fresh passes, so it can move.
- **Decision fed: none directly.** This is a baseline. It tells the owner how far one day's count can be trusted
  against the bar of ≤ 6/30 (`docs/decisions/2026-10-10-belonging-personal-story-bar.md`), and it is the "before"
  for any later candidate or ranking change. It cannot pass or fail v3, and it starts no rollback.
- **Authority:** the owner asked Claude to "continue the work you can do without me" (2026-10-13). This baseline was
  proposed to the owner earlier that day and not ruled on. It costs $0 and reads production data only.

## 1. Population (computed by the pipeline's own formula, not chosen by hand)

- **Builds:** 2026-10-09, 10-10, 10-11 and 10-12, each at 14:30Z, the reconstructed time of the owner-labelled page.
  Each is rebuilt with `site_order()` from sadalsuud's ovr.db (read-only):
  - the build query, anchored at the build date;
  - only rows whose summary existed by then;
  - rows the 10-13 build population held but its page did not show are dropped, assuming a removal is sticky.
    Measured on 10-12, this assumption puts about 2 of 30 rows wrong.

  Plus 2026-10-13 06:55:18Z, the live page's own cards (no approximation; `lenses_20261013/belonging.json`).
- **Version filter:** join each id to NexusMind's `belonging.version` stamp (belonging `filtered_*.jsonl` on
  sadalsuud, newest file per id). Keep `"3.0"` only, and take the first 30 v3 rows in site order. v1 rows are
  skipped and counted. If fewer than 30 v3 rows rank inside the page's top 60, the build is reported with N < 30 and
  left out of the range.
- **Text:** title + content from the same NexusMind row (the same input the 10-12 tagger saw).

## 2. Instrument

- qwen3.8:27b on b650, `focus` tag, with the 10-12 run's `system.txt` and `tag_qwen.py` copied unchanged
  (`~/ld-lab/experiments/2026-10-12-belonging-c2c/focus-tag/`): temperature 0, seed 42.
- **A qwen count is a FLOOR.** On the corrected 10-12 page qwen counted 7 where the owner counted 10. Every number
  below is reported as a qwen count, never as the owner's count.
- For 10-12, the owner's labels exist for the page's own 30 and are reported beside qwen's, for calibration only.
- ⛔ Runs only after ovr.news releases b650 (their C2 speed runs need the card to themselves).

## 3. What is reported

Per build: N, v1 rows skipped, the qwen personal count, and the number of rows tagged `None` (unparsed).
Across builds: min, max, and the range.

## 4. Predictions (scored after)

- Per-build qwen count: **4–10** (the 10-12 page gave 7).
- Range across the five builds: **≥ 3**. That is, a single day is not a stable estimate.
- 10-09: **at least 5 v1 rows skipped** in its top 60, since v3 went live in the early hours of 10-09 CEST.

## 5. Known limits

- ovr.db holds each row's CURRENT score; the rebuilds use that score, not the one on the day.
- Real builds happen several times a day; 14:30Z is one sample per day.
- Five builds is a small sample. The range is descriptive, not an interval.
