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

## Owner correction (after the result, 2026-10-12)

Asked about pos 25, the owner answered: **"Slip: it's personal"**. Corrected owner count: **10 of 30**. With the
correction: judge A 26/30 (count 8), judge B 26/30 (count 10), both-say 26/30 (count 8), qwen 27/30 (count 7);
all pass rule 2. This is a post-hoc correction of the reference, reported beside the pre-registered result above,
which stands as recorded (`tags.tsv` keeps the original label). Either way, v3 does not meet the bar.

## Next (owner, 2026-10-12)

No paid oracle. qwen on b650 tags the high-scoring rows of v3's training data (`datasets/training/belonging_c2b`);
rows tagged `personal` get their targets scaled so the weighted score lands just above the op-point (owner chose
"just above op-point": ~4.3–4.5, so they still pass but rank below community stories); then retrain v3's recipe on b650.

## Candidate c2c: the composition check (amendment B, 2026-10-12)

Run on b650 (RTX 5090, `venv-prodparity`, one device term). Both seeds trained and calibrated with exit 0 (best val
MAE s42 0.407, s43 0.398). All lab files are cited in `MANIFEST.json` (`inbox/b650-gpu/2026-10-12/`: `focus-tag-comp`,
`belonging_comp_scores`, `v1_c2c_s42`, `v1_c2c_s43`, `c2c-logs`). The draw has 33,393 rows, 28,384 at stage 2 for
every model. qwen tagged the 340 distinct ids (each model's top 30 plus v3's 340 passes; every top-30 id was already
a v3 pass): 275 group, 64 personal, 1 unparsed (a v3 pass outside every top 30).

| measure | v3 | c2c s42 | c2c s43 | pre-registered rule | prediction |
|---|---|---|---|---|---|
| personal in top 30 (qwen) | **5** | 2 | 1 | ≤ 6; v3 must be > 6 | v3 8–14: **miss**; c2c 5–10: **miss (lower)** |
| recall guard: v3's group passes kept at 4.0 | | **222/275 = 0.807** | **237/275 = 0.862** | ≥ 0.9 per seed | 0.92–0.99: **miss** |

Personal in top 30 (qwen): v3 5, s42 2, s43 1.

**Verdict per amendment B: c2c FAILS.** The recall guard fails on both seeds ("below that, the nudge costs
community stories and c2c fails"). The composition half is UNDECIDABLE, because v3 is already ≤ 6 on this draw.
⚠️ `comp_check.py evaluate` prints `CHECK: UNDECIDABLE`, because it tests the baseline condition before the guard.
The pre-registered text decides, and the script's last line is not changed after the fact.

**Post-hoc diagnostics (not pre-registered; for reading only):**
- Passes at 4.0 on the draw: v3 340, s42 271, s43 461. s43 passes 186 rows that v3 does not, and those are untagged
  and unjudged, so their cost to specificity is unknown. The two seeds move in opposite directions on volume. That is
  the seed band, not the nudge.
- Mean raw shift vs v3 on v3's passes: s42 group −0.24, personal −0.82; s43 group −0.47, personal −1.16. The nudge
  pushes personal stories down 2–3× harder than group ones. But it also pulls community stories under the op-point.
- **Why v3 shows only 5 here:** the draw ranks the raw score over 12 files. The page fetched at 14:58 is ranked by the
  site (normalized score, recency, editor), and there the same tagger counted 7 and the owner 10. So the page's top
  is not the raw-score top. GUESS, not measured: part of the page's personal-story excess comes from the site's
  ranking, which this instrument cannot see. A future check needs the site's ranking, or the owner's count, not a
  raw top 30.

**Incident (no effect on the result):** the c2c packages were copies of `v1_c2b`, and their `.py` files imported
`filters.belonging.v1_c2b.*`, so they loaded c2b's model. `gate.assert_loads_from` refused both before any score
was written. The imports were rewritten to each package's own name on b650 (`.py` files only), then rescored.
The first scoring attempt had also failed at `import gate` (script copied to the wrong path on b650; nothing written).
