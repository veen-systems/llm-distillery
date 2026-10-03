# Belonging v1 label adjudication: results (2026-10-03). NOT APPLIED, pending the owner

**Rules:** `PLAN.md`, committed in `28d5a06` before judging. **Code:** `adjudicate.py`. **Verdicts:** gitignored
`datasets/belonging_v1_adj/verdicts.jsonl`.

## Judges (2 blind passes, frozen v2.2, ~3.4M subagent tokens)

**A/B binary agreement 849/859.**

| split | kept in (both) | moved out (both out) | split | cannot_judge |
|---|---|---|---|---|
| train | 30 | 638 | 9 | 7 |
| val | 4 | 82 | 1 | 0 |
| test | 3 | 84 | 0 | 1 |
| **total** | **37** | **804 (93.6%)** | 10 | 8 |

**Moved-out classes** (pass A):

| class | rows |
|---|---|
| `out_other` | 306 |
| `out_one_moment` | 253 |
| `out_harm_is_story` | 112 |
| `out_culture_topic` | 75 |
| `out_gift_official` | 48 |
| `out_event_spectated` | 10 |

Of v1's 794 positives (≥ 4.0), 37 are kept in by both judges.

## Owner check (seed 20261007; `owner_check_owner.tsv`, key `owner_check_key.tsv`)

5 moved-out and 5 kept-in rows, blind, with Claude's neutral summaries and an in and an out reading spelled out.

| judges | owner in (first read) | owner out | unsure |
|---|---|---|---|
| kept in (5) | 2 | **2** (the Shipibo film interview; a man adopting 10 sons) | 1 |
| moved out (5) | **3** (a St Martin's lantern-festival column; solar backpacks for homeless people; a town petition saving its cobbler) | 2 | 0 |

**Owner–judge agreement: 4 of 9 decided rows** (first read; after the backpacks revision, 5 of 9). The earlier checks agreed far better: 10/10 on harvest positives,
8/8 on calibration in/out.

## What this means (Claude's reading; n = 10)

- **On v1's own positives, the judges and the owner draw different lines, in both directions.**
  - The judges demote community, tradition and kindness stories the owner would keep: `out_culture_topic`,
    `out_gift_official`, and `out_harm_is_story` for a petition.
  - The judges keep single-person or film stories the owner would drop.
- **3 of 5 sampled moved-out rows are owner-in.** Applying the 804 demotions as hard negatives (≤ 2.0) could teach
  the student against stories the owner wants. The interval on 3/5 is wide: Wilson ≈ [0.23, 0.88].
- **Not applied.** The labels in `datasets/belonging_v1_adj/` are untouched; only verdicts are recorded.
- ⚠️ **Phase 6 gates on v1's test ids**, and only 3 of the 88 judged test rows are kept in. A recall gate there
  would rest on ~3 positives, so the gate set needs rethinking. The held-out set (`../2026-10-03-belonging-heldout/`)
  is a candidate.

## Second owner check: 20 more moved-out rows (seed 20261008; `owner_check2_owner.tsv`, key `owner_check2_key.tsv`)

- **First check revised:** after Claude pointed at ruling 3 (one-way gifts are out), the owner changed the solar
  backpacks to out (`owner_first_read` keeps the first answer). That makes the first check 2 of 5 moved-out rows
  owner-in.
- **This check: the owner would keep 11 of 20.** Combined: **13 of 25 ≈ 52%**, Wilson ≈ [0.33, 0.70].

**By judge class** (pass A verdict; owner keep / demote):

| judge class | owner keep | owner demote |
|---|---|---|
| `out_one_moment` | **0** | **6** |
| `out_other` | 6 | 1 |
| `out_harm_is_story` | 3 | 1 |
| `out_gift_official` | 1 | 0 |
| `out_culture_topic` | 1 | 0 |
| `out_event_spectated` | 0 | 1 |

**Asked what "keep" meant** (on the tab, or just "not junk"), the owner said they were not sure: several rows are
genuinely hard.

## Ruling (owner, 2026-10-03): treat by agreement, act only where it is clear

⚠️ **Review (2026-10-03 close):**
- The demote rule's evidence is **0 of 5** both-judge `out_one_moment` rows. The sixth row was A `out_one_moment`,
  B `out_other`. The Wilson 95% upper bound on the owner-keep rate is ~0.43: consistent, not proven.
- "Drop 566" removes most hard negatives near the op-point except the one-moment class. That cuts against the
  specificity priority, so decide hard negatives before the build (TODO item 0).
- The executable form is `adjudicate.py ruling` → `treatment.jsonl`, which asserts 238/566/55. **Never read
  `verdicts.jsonl`'s `outcome`:** it holds PLAN.md's superseded rule.

⚠️ **This rule was chosen AFTER seeing the results.** It replaces PLAN.md's "both out → demote" rule. It is derived
from n=25 owner reads and is reversible: nothing is written to labels until the retrain build.

| rows | treatment | train | val | test | total |
|---|---|---|---|---|---|
| moved out, BOTH judges `out_one_moment` | **demote** (every dim → min(label, 2.0)) | 186 | 27 | 25 | **238** |
| other moved out | **drop from training** (neither positive nor negative) | 452 | 55 | 59 | **566** |
| kept in / split / cannot_judge | v1 labels unchanged | 46 | 5 | 4 | **55** |

⚠️ **The test split loses 59 rows to "drop"**, and only 3 kept-in positives remain there. A gate on v1's test ids
cannot measure recall; the gate set is an open decision (the held-out set is a candidate).
