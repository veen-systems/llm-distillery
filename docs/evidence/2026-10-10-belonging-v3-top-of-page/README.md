# belonging v3: single-person stories at the top of ovr.news's Belonging page (2026-10-10)

**An observation, not a test.** The owner saw that "the top stories on https://ovr.news/en/belonging/ show
at least half personal stories" the morning after belonging v3 went live (2026-10-09, NexusMind run
`bd00dad6`), and linked seven. The open hypothesis is ledger row **H-BB6** (`memory/hypothesis-ledger.md`);
its test is the top-of-page composition check in `experiments/README.md` § *Protocol*.

## Measured

**The seven linked stories are all v3-scored.** Joined to NexusMind's version stamp
(`nexus_mind_attributes.belonging.version`) in the v3 files `filtered_20261009_012040` … `filtered_20261010_090728`
on sadalsuud:~/local_dev/NexusMind/data/filtered/belonging/:

| ovr.news article id | NexusMind file | version | raw | normalized (ovr.db) |
|---|---|---|---|---|
| `west_african_legit_ng_b34ac7abc55b` ("Husband reveals secret deal to care for wife") | 20261010_053504 | 3.0 | 6.19 | 8.06 |
| `australian_the_west_australian_87cd554aed1f` | 20261010_053504 | 3.0 | 6.05 | 7.65 |
| `dutch_news_nieuwe_oogst_b6ce335c32cd` | 20261009_171306 | 3.0 | 5.98 | 7.44 |
| `greek_ta_nea_e7ad7352988f` | 20261010_015938 | 3.0 | 5.87 | 7.11 |
| `west_african_legit_ng_ae910ecc6b39` | 20261009_133451 | 3.0 | 5.90 | 7.21 |
| `baltic_lrt_6866a24b0fce` | 20261010_053504 | 3.0 | 5.80 | 6.85 |
| `west_african_legit_ng_a53f99dec4d0` | 20261010_053504 | 3.0 | 5.75 | 6.70 |

**community_fabric is capped.** v3's isotonic calibration tops out at **6.3335**
(`filters/belonging/v3/calibration.json`, max of the dimension's `y` thresholds). Over all **194** v3 passes
(raw ≥ 4.0) in those 8 files it runs **3.60–6.33** (`scores.community_fabric`). "Husband reveals secret
deal" scores reciprocal_care 6.97 and slow_presence 6.78 against community_fabric 5.67 (ovr.db `scores`).

**3 of the 7 come from one source** (legit.ng).

## Not measured

- **The share of personal stories.** "About half" this morning, against roughly one in six for v1 on
  2026-10-07, is Claude's reading of titles. No judge classified them.
- **Whether the cap matters for ranking.** community_fabric still takes many distinct values below 6.33, so
  it does help rank passes; whether the cap is why communal stories lose the top is untested.
  (slow_presence is capped too, at 6.78.)
- **Why.** Two candidate causes, neither tested: v3's 135 new hard negatives were all
  `out_gift_official` / `out_harm_is_story`, and the 121 `out_one_moment` ones were left out (owner ruling
  2026-10-08); and the community_fabric cap above. c2a (EXP-046) had the 121 and failed recall by 2
  (k = 43/63 against a bar of 45). Which positives it missed has not been checked.

## Queries

```bash
# the seven, from ovr.db (production data on sadalsuud: ~/local_dev/ovr.news/data/ovr.db, read-only)
ssh sadalsuud 'sqlite3 -readonly ~/local_dev/ovr.news/data/ovr.db "SELECT article_id, raw_weighted_average,
  weighted_average, scores FROM article_filter_scores WHERE filter=\"belonging\" AND article_id IN (...);"'
# version stamp and the community_fabric range over v3 passes: python over the 8 filtered_*.jsonl files,
# keeping rows with nexus_mind_attributes.belonging.version == "3.0" and raw_weighted_average >= 4.0
```

⚠️ ovr.db has no version column, and rows the previous version scored keep draining for days. Join to the
NexusMind stamp, as above, before reading a version off ovr.db.
