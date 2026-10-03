# Belonging held-out screen measurement: results (2026-10-03)

**Pre-registration:** `PREREGISTRATION.md`, committed in `433aabd` BEFORE the draw. **Code:** `draw_heldout.py`
(sadalsuud) and `heldout.py` (`check`, `gemini`, `build-judges`, `analyse`). **Full output:** `result.txt`.
**Rows:** gitignored `datasets/belonging_heldout/`.

## What was measured

- **Population:** distinct `stage2` belonging rows in sadalsuud's 159 retained files, **`filtered_20260904_220817` ..
  `filtered_20261003_084553`**. Excluded: news.google.com, content under 300 characters, 7,967 excluded tokens (7,964 ids; the extra 3 were the filenames `train/val/test.jsonl` from an `ls`, harmless), and
  duplicates.
- **Bands** (student raw): `hi` ≥ 5.6 (pool 4,991), `mid` 4.0–5.6 (8,820), `near` 2.5–4.0 (13,728), 27,539 in all.
  The 314,075 rows below 2.5 are outside the population.
- **The draw:** 400 per band, seed 20261003. The 1,200 ids are now in `belonging_exclusions.py`
  (mutation-tested: a held-out id in a draw exits 1).
- **Stage A:** Gemini 2.5 Flash on frozen rubric v2.2 (sha `d450b79510418cf7`, prompt sha `9a245a9dc5ee64eb`).
  - 1,198 verdicts. 2 rows came back EMPTY twice (0 output tokens, probably a safety block) and are counted as
    not-in (`no_reply`).
  - 3,370,485 in / 124,366 out tokens = **$1.322 at list price**; billing unchecked.
- **Stage B:** 2 blind Claude Opus 5.5 judge passes on 295 rows: all 145 Gemini-ins plus 50 sampled Gemini-outs per
  band. 1,331,112 subagent tokens.
  - A/B binary agreement 282/295, with 13 splits.

## Results (judge-relative; `both` = both judges say in)

| band | Gemini says in | of those, judged in (`both`) | misses among 50 sampled outs | in-rate (`both`) | in-rate (`either`) | specificity |
|---|---|---|---|---|---|---|
| `hi` | 92/400 | 35 = **0.38** | 0 | **0.087** (~437 rows) | 0.113 | 0.844 |
| `mid` | 44/400 | 9 = **0.20** | 0 | **0.022** (~198 rows) | 0.028 | 0.910 |
| `near` | 9/400 | 0 | 0 (`either`: 1 split) | **0.000** | 0.020 (that 1 row × 7.82) | 0.978 |
| weighted, 27,539 rows | ~2,427 | 0.26 | — | **0.023 (~635 rows)** | 0.039 | 0.933 |

- **Recall:** 0 misses among 150 sampled outs under `both`. The rule-of-three lower bounds are `hi` ≥ 0.65 and
  `mid` ≥ 0.30, **too wide to claim high recall**. Under `either`, the single `near` split row is weighted ×7.82 and
  then ×34 to the band, which drives population recall to 0.75. One row; fragile.
- **Predictions vs measured** (`both`):

  | band | predicted | measured | |
  |---|---|---|---|
  | `hi` | 3–8% | 8.7% | just above |
  | `mid` | 1–4% | 2.2% | inside |
  | `near` | 0–2% | 0% | inside |

  "Gemini in ≈ in-rate + 5–8 points" was **wrong for `hi`**: 23% against 8.7% + 14 points.

## The owner check (`owner_check_owner.tsv`, key in `owner_check_key.tsv`; seed 20261005)

| judges | owner in | unsure | out |
|---|---|---|---|
| both in (4) | 3 | 1 | **0** |
| split (3) | 2 | 0 | **1** |
| both out, Gemini in (3) | **1** | 2 | 0 |

**The pre-registered bar for "either judge says in" FAILS on both conditions:**
- the owner said out on a split row (an Indigenous food summit announcement)
- the owner said in on a both-out row (a youth movement's 75th-anniversary weekend camp-out, aged 5–79)

On that second row the judges applied the rubric's restored Q1 OUT example, *"an anniversary of a group"*. The
owner's call is that a participatory reunion is in. **That is a line conflict for the owner, NOT a rubric change
here:** any edit to v2.2 means a new held-out set (pre-registration).

`both` stays clean on this check: 0 owner-outs among 4. n is small throughout.
