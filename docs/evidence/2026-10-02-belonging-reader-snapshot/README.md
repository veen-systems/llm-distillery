# Belonging: what readers get, and where an external curator's picks land (2026-10-02)

This is the evidence behind the belonging retrain plan (`docs/TODO.md` ▶ START HERE item 0). It answers the
question that started the belonging work: **why ovr.news reads less engaging than an external human-curated
selection.** In ovr EXP-025 Belonging was ovr's weakest lens (1.33); in EXP-005, readers want Belonging more than any
other lens. The curator is not named in this repo, by owner instruction; its data is local-only in
`datasets/external_curator/` (gitignored).

Everything here was collected read-only. Oracle cost: $0. GPU: none.

## 1. Volume (measured)

`bel_month.py`, run on sadalsuud over every retained `data/filtered/belonging/filtered_*.jsonl`. That is 159 cycles,
**2026-09-03 → 2026-10-02**; no file exists for 09-29 (the gpu-server reachability gap). Per-cycle counts are in
`per_cycle_counts.tsv` (the script's stderr, renamed). It has no header; the columns are file stamp, rows, stage2
rows, stage2 rows at raw ≥ 4.0, and repeat ids.

- **The window:** 569,769 scored rows, of which 457,605 were `stage2`.
- **Passing belonging:** 14,850 distinct articles had `stage2` and raw ≥ 4.0. That is **~500/day, 2.5–4.4% of
  stage2 per day** (1.75–5.7% per cycle), steady across the month. 10-01 is double (1,062); "caught up after the gap"
  is a guess.
- **Raw bands and language mix of the passers:** `passer_bands.txt`, from `passer_bands.py`. 70% sit below raw 5.77
  and 4.4% at 7+. en 49%, es 12%, fr 9%, de 5%, nl 5%, 39 languages in all.
- ⚠️ `bel_month.py` is kept exactly as run. Its `or -1` writes a real harm score of 0.0 as −1 in the per-row file,
  and it skips malformed lines without counting them. No number here depends on either.
- **The window is part of the source:** the files rotate. Nothing before 09-03 is visible here.

## 2. What readers could see (measured population, my verdicts)

The population comes from sadalsuud `ovr.news/data/ovr.db`, using the site's own build query (`getArticlesForBuild`).
The query, verbatim except for the window:

```sql
SELECT ... FROM article_filter_scores afs JOIN articles a ON a.id=afs.article_id JOIN summaries s ON s.article_id=a.id
WHERE afs.filter='belonging' AND afs.weighted_average>=4.5
  AND date(a.published_date) BETWEEN '2026-09-03' AND '2026-10-01'   -- the build uses the last 10 days
ORDER BY random() LIMIT 200;
```

- **Size:** **2,368 articles** (~80/day over 29 days). **783 were eligible at the time of the read** (the 10-day window).
- ⛔ **The 4.5 predicate is not the binding gate.** `ovr.db` holds only articles that won a slot in ovr's
  **top-50-per-lens cap**, a competition per run (ovr.news `memory/project_session_2026_09_28.md:19`). All 2,375
  belonging rows stored for that window (the same query without the `summaries` join, so 7 more) have normalized ≥ 6.20 and raw ≥ 5.62; the sample's minimum is raw 5.77.
  "Reached readers" therefore means **winning the cap**, not passing belonging (raw ≥ 4.0). About 80 of ~500 passers a
  day make it.
- **What it excludes:** the build's Chief Editor step can still remove articles, and that was not applied here. The
  normalized score is percentile-based (ADR-014), so the numbers are not raw scores.

**`reader_sample_200.tsv`** holds 200 rows drawn by `ORDER BY random()` from those 2,368. Columns: ids, scores, source,
language and ovr's English title. No bodies (public-repo rule).

**The verdicts are Claude's, from ovr's English title and summary, read once. The owner has not checked them.**
The yardstick is the 2026-10-02 middle ruling, *before* the "doing" test was added.

Shares are n/200, rounded.

| verdict | n | share | median normalized score | share ≥ 9.5 |
|---|---|---|---|---|
| fits | 33 | 16% | 9.13 | 33% |
| borderline | 35 | 18% | 9.36 | 29% |
| official ceremony / gift / institution | 40 | 20% | 8.84 | 25% |
| harm, grievance, war, politics | 34 | 17% | 9.13 | 29% |
| one person or one family | 28 | 14% | 8.73 | 0% |
| culture topic only | 16 | 8% | 9.14 | 38% |
| other off-lens | 14 | 7% | 8.64 | 7% |

**Reading:**
- About two-thirds is off-lens under the ruling. The off-lens share is not concentrated in the #130 grievance shape:
  ceremonies, gifts, single-person stories and culture-only topics are each as large a slice.
- **The score does not rank them** (Claude's verdicts, n=33 and 34, no noise band): fits and grievances share a median
  of 9.13. A higher threshold or a reorder would not separate them on this sample.
- **Caveats:**
  - One reader.
  - The summaries are written to read constructively, so some rows may read worse in the original.
  - The "doing" test (ruled after this read) would move some fits (festivals, traditions) to borderline or out.

## 3. Where belonging v1's training positives come from (measured count, my read)

On b650-gpu, `~/llm-distillery/datasets/training/belonging_v1/{train,val,test}.jsonl` holds 7,370 rows (5,894/738/738).
With v1's weights `[.25,.25,.10,.15,.15,.10]` and its `community_fabric` gatekeeper (< 3 caps the score at 3.42),
**794 rows (10.8%) are positives at ≥ 4.0** (631 train, 78 val, 85 test).

A seeded random 60 of them (seed 7, titles only) read mostly as Upworthy / The Better India feel-good stories: a dad's
poem, a woman cricket coach, a Kerala avocado industry, medRxiv protocols. By Claude's count **about 10 of 60 fit the
ruling.** The training population is positive-news feeds; production is world news in 39 languages.

## 4. The external curator's picks against our corpus (measured; data local-only)

- **Picks and match:** the curator's recent picks were matched against every retained belonging file (all scored
  rows, not only passers), on normalised `url` / `resolved_url`. Script, picks and per-story table are local-only in
  `datasets/external_curator/` (gitignored, by owner instruction).
- **Coverage:** **46 distinct picks reached belonging scoring.** Coverage of in-window picks is partial. Never-collected
  is not separated from url mismatch.
- **Scores (raw):**
  - The 29 picks the student fails all score ≤ 2.4. By title they are health, energy and policy stories, so that is correct.
  - The **17 it passes score 4.09–6.72.** By title these are the community- and volunteer-action stories.
  - Against the reader population (§2):
    - **6 of the 17 score below 5.62**, the lowest belonging score `ovr.db` stored all window, so they could not have
      won a cap slot.
    - The best of them (6.59–6.72) only reach the reader sample's median (6.59).
    - **Not checked:** whether any of the 17 actually won a slot.

**Reading:** belonging does not mostly *miss* the curator-shaped stories that reach it. It scores them no higher than
ceremonies, gifts and grievances: 6 of the 17 cannot win a cap slot at all, and the rest sit at or below the reader
median. That is a
ranking problem rooted in the training data. So the plan is the human_thriving v9 recipe (adjudicated positives plus
hard negatives), not more prompt rules.

## Rebuild

```bash
scp bel_month.py sadalsuud:/tmp/ && ssh sadalsuud 'python3 /tmp/bel_month.py 2>/tmp/bel_per.tsv'   # ~5 min; bel_per.tsv = per_cycle_counts.tsv
scp sadalsuud:/tmp/bel_month.tsv /tmp/ && python3 passer_bands.py /tmp/bel_month.tsv > passer_bands.txt
# reader sample: getArticlesForBuild's WHERE clause with ORDER BY random() LIMIT 200 (not reproducible row-for-row)
# curator match: see datasets/external_curator/ (local only)
```
⚠️ The files rotate, so a re-run after 2026-10-02 sees a different window.
