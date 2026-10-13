# belonging v3: day-to-day top-30 personal count (2026-10-13) — IN PROGRESS

Pre-registered in `PREREGISTRATION.md` (`3b6bd6e`, before any population was built). $0 oracle.

## Steps and files

1. `ovr_db_rows.json`: ids, dates and scores only, from sadalsuud's ovr.db, read-only:
   `SELECT a.id, a.published_date, a.language, afs.weighted_average, afs.raw_weighted_average, s.created_at AS s_created
   FROM article_filter_scores afs JOIN articles a ON afs.article_id=a.id JOIN summaries s ON a.id=s.article_id
   WHERE afs.filter='belonging' AND afs.weighted_average >= 4.5 AND date(a.published_date) >= date('2026-10-09','-10 days')`
2. `build_population.py ovr_db_rows.json > builds.json`: each build's top 60 in site order.
3. `extract_rows.py` (run on sadalsuud): the version stamp plus text for those ids. The output lives in the lab,
   `experiments/2026-10-13-belonging-daily-baseline/extract/`, cited in `MANIFEST.json`.
4. `select_v3.py > selection.json`: the first 30 v3 rows per build, with every skipped row counted by its stamp.
5. ⏸ qwen `focus` tags on the 121 distinct rows. This waits for ovr.news to release b650.

## So far (no tag read yet)

| build | v3 rows in top 60 | in the range? | rows skipped (stamp) |
|---|---|---|---|
| 10-09 14:30Z | 14 | no (N < 30) | 46 × v1 |
| 10-10 14:30Z | 26 | no (N < 30) | 34 × v1 |
| 10-11 14:30Z | 56 | yes | 0 before the 30th v3 row |
| 10-12 14:30Z | 60 | yes | 0 |
| 10-13 06:55Z (live page) | 60 | yes | 0 |

Prediction §4, "10-09: at least 5 v1 rows skipped": **hit** (46). Only three builds enter the range, not five,
because v1 rows were still draining through 10-10. A first version of `selection.json` recorded the skip count only
for builds in the range. Review caught it, and it was rebuilt by the committed `select_v3.py`.
