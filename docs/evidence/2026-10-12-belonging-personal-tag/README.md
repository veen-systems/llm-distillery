# belonging v3: the `focus` tag, first count (2026-10-12)

Pre-registered in `PREREGISTRATION.md` (committed `a4b2d48`, amendment A `739e104`, both before the draw).
Per-row table: `tags.tsv` (ids, v3 raw score, owner label, each arm's tag, title). $0 oracle.

## Population

`https://ovr.news/en/belonging/` fetched 2026-10-12T14:58:38Z, feed cards in `data-index` order (531 cards).
The top 30 are all stamped `belonging.version "3.0"` in NexusMind's belonging `filtered_*.jsonl` files
(newest file per id, `filtered_20261002_090933` … `filtered_20261012_132735`). 0 rows skipped as v1, 0 not found.

## Results

| measure | value | pre-registered rule | verdict | prediction |
|---|---|---|---|---|
| **Owner count of `personal`** | **9 of 30** (pos 4, 7, 9, 10, 15, 18, 19, 21, 24) | ≤ 6 meets the bar | **v3 does NOT meet the bar** | 10–18: a MISS, low by 1; "does not meet": hit |
| judge A (Claude) | 25/30 agree, count 8 | ≥ 26/30 and count ±2 | FAIL by one row | 22–28: hit |
| judge B (Claude) | 25/30 agree, count 10 | same | FAIL by one row | |
| both-say (A and B) | 25/30 agree, count 8 | same | FAIL by one row | |
| **qwen3.8:27b on b650** (arm 3) | **26/30 agree, count 7** | same | **PASS, exactly at the bar** | 20–27: hit; "weaker than the Claude judges": not supported (one row apart, within noise at n = 30) |

Disagreements with the owner (owner / A / B / qwen):
- pos 3 couple feeding ~30 stray cats: group / personal / personal / group
- pos 4 mother rides a camel for her son: personal / personal / personal / group
- pos 9 women launch a platform for seniors: personal / group / group / group
- pos 16 restaurant popular on TikTok: group / group / personal / group
- pos 19 Yudu county, one family's income tripled: personal / group / group / group
- pos 21 couple returns to care for Low Isles: personal / group / personal / personal
- pos 25 family celebrates parents' 30 years of marriage: **group** / personal / personal / personal

## Reading it

- **v3 vs the bar:** 9 of the top 30 are personal by the owner's own labels, so v3 does not meet the bar. That
  is the case for the next candidate. It is not an automatic rollback (`filters/belonging/v3/STATUS.md`).
- **The tagger:** qwen passes at the bar's edge on n = 30. Its 4 misses are 13%. Usable to tag TRAINING rows
  (where a wrong tag softens one label), not yet as the sole judge of a gate.
- ⚠️ **pos 25 (post-hoc, not changed):** all three arms say personal and the owner said group, and the bar's
  own example class includes "couple celebrates 75 years". It may be a slip. Asked the owner. Per rule 3 the
  table is not edited. If the owner corrects it, the count becomes 10 and every arm passes (A, B and both-say
  26/30, qwen 27/30), and that is reported as a correction, not as the pre-registered result.
