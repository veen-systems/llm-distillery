# Belonging adjudication PILOT v3, the enriched pilot: pre-registration (before the draw and before any judging)

> ⚠️ **Rubric pointer (2026-10-02 close):** "rubric_belonging_v2.md" below meant **v2.0** (`rubric_belonging_v2_0.md`). **Corrections:** pilot v2's owner check was 7/10, which does NOT meet its bar ("aligned" overstated it). This file was committed together with its results, and its addendum came after the draw. **Result:** the bar was **not met**; item 2 was NOT EVALUATED and item 3 never ran (`README.md` § *Review corrections*).


**2026-10-02.** Pilot v2 aligned the line: the owner agreed 7, disagreed 0, was unsure on 3.
- **What v2 could not test** was the in-scope side. Random samples held ~1 in-scope row in 100, so κ was unreachable.
- **This pilot** tests the judges on candidates RETRIEVED as likely positives. It also measures how much retrieval
  lifts the in-scope rate, which matters because phase 4 must retrieve positives rather than sample them.

**Definition:** `rubric_belonging_v2.md`, approved and unchanged. **Judge instructions:** `judge_instructions_v2.md`,
unchanged.

## Retrieval (`extract_corpus_v3.py`, `retrieve_v3.py`; run before this file was written)

**Corpus:** every distinct `stage2` belonging row in sadalsuud's retained files, 09-03 → 10-02.
- That is 578,121 rows in total, of which 464,493 were `stage2`. 344,855 were kept.
- Excluded: news.google.com, content under 300 characters, and every pilot, test, exemplar and reader id.

**Seeds:** 18 (`seeds_v3.jsonl`, local).
- the 13 P exemplars from `exemplars_v2.tsv`
- 5 consensus-in rows from the two pilots

**Score:** multilingual-e5-small, using `embedding_screener.py`'s text recipe and OFF_LENS mask.
- **Nearest-seed (max) cosine similarity.** The screener's centroid ranking was tried first and looked worse: its top
  500 holds floods and a mine collapse. That was judged by eye on titles, not measured.

## Strata (seed 20261004, `draw_pilot_v3.py`, run on b650)

The candidate set is the top 2,000 non-off-lens rows by nearest-seed similarity.

| stratum | n | pool |
|---|---|---|
| `retrieved_hi`: candidates with student raw ≥ 4.0 | 50 | 753 |
| `retrieved_lo`: candidates with raw < 4.0 (missed positives?) | 20 | 1,247 |
| `random_pass`: random stage2 rows with raw ≥ 4.0, outside the top 2,000. The same instrument as `retrieved_hi`, so the lift is a like-for-like comparison | 30 | |
| controls: the same 4 as pilot v2, from `exemplars_v2.tsv` | 4 | |

Every row carries `n_in_stratum`, and rates are not pooled.

**As drawn:** the pools came out as `retrieved_hi` 752, `retrieved_lo` 1,248 and `random_pass` 13,024. The table's
753 / 1,247 came from an exploratory run that broke similarity ties differently. The sample is the drawn one.

## Passes

Pass A and pass B each run as two subagents of 52 rows, on different shuffles. Every judge is blind and has its own
directory and scratch directory.

## Bar: all must hold before phase 3

1. **Controls:** 4/4 in each pass.
2. **Self-consistency:** A vs B binary agreement ≥ 0.90 and κ ≥ 0.75.
   - **Reachability, checked first:** at an in-scope prevalence of 0.25, one disagreement in 100 gives κ ≈ 0.97, and
     5 disagreements give κ ≈ 0.87.
   - **Below 10 consensus-in rows,** κ is reported but not judged. The failure that then counts is retrieval's,
     not the judges'.
3. **Owner spot-check: ≥ 9 of 10 agree with the consensus**, unsure counting as not agreeing.
   - **The rows:** 5 consensus `in_scope` rows and 5 consensus-out rows.
     - At least 2 of the in rows come from `retrieved_hi`.
     - At least 1 of the out rows comes from `retrieved_hi`, as a near-miss check.
     - The rest are random.
   - **What the owner reads:** the title and the article's own opening ~600 characters. Claude adds a gloss only for
     non-English text, marked as a gloss.
4. **Presence:** the consensus disagrees with the student (raw ≥ 4.0 as "in") on at least 1 row.

## Predicted (before the draw)

Consensus `in_scope` rate per stratum:
- **`retrieved_hi`:** 25–50%, from Claude's title read of 15 rows (4–6 looked in).
- **`retrieved_lo`:** 0–15%.
- **`random_pass`:** 0–10%. Pilot v2 measured 0/30.

**Lift** = `retrieved_hi` divided by `random_pass`. It is reported with its interval. ⚠️ Both arms come from Claude's
judges, so the lift is a judge-relative measure.

⚠️ Claude chose the seeds, predicts the rates and runs the judges. The owner's spot-check is the independent check.
