# belonging v3: day-to-day top-30 personal count (2026-10-13)

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
5. qwen `focus` tags on the 121 distinct rows, run on b650 after ovr.news released it (lab `tag/`, cited).
6. `count.py > count_result.txt`.

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

## Result (`count_result.txt`)

| build | N | qwen personal (a FLOOR) | owner, on the rows they labelled |
|---|---|---|---|
| 10-11 14:30Z | 30 | **4** | none labelled |
| 10-12 14:30Z | 30 | **8** | 10 personal of 28 labelled; qwen says 7 on those 28 |
| 10-13 06:55Z (live page) | 30 | **5** | 0 of 6 labelled |
| 10-09 14:30Z (out of range) | 14 | 6 | none |
| 10-10 14:30Z (out of range) | 26 | 8 | none |

In-range builds: qwen min 4, max 8, **range 4**. 0 unparsed.

**Predictions (§4):** per-build qwen 4–10: **hit** (4, 8, 5). Range ≥ 3: **hit** (4). 10-09 ≥ 5 v1 skipped: **hit** (46).

**Reading:**
- MEASURED: one day's qwen count moves by 4 across three consecutive days. So a single day's count, including the
  owner's 10 on 10-12, is one draw, not v3's level.
- MEASURED: on the 28 rows of the 10-12 page the owner labelled, qwen finds 7 personal where the owner finds 10. qwen
  is a floor, as on 10-12.
- GUESS, not measured: scaling qwen by the 10-12 ratio (10/7) puts 10-11 near 6 and 10-13 near 7. If so, v3 sits
  near or just above the ≤ 6 bar on most days, with spikes like 10-12. Only the owner's own count on those days can
  confirm it.
- Three builds is small, and the range is descriptive.
