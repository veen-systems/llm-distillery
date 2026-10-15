# belonging c2d on ranking H: NOT worth a gate (Check A fails on seed 43)

Pre-registered in `PREREGISTRATION.md` (`9e748c5`, before any c2d model existed or any score or tag was read). $0
oracle; b650 GPU only; qwen3.8:27b tags (a FLOOR). Registry: EXP-050. Context: `docs/TODO.md` item 0a; H-BB6, H-BB8;
EXP-048 (c2c), EXP-049 (the H replay reused here).

## Verdict

**WORTH A GATE: False** (`result.txt`). The pre-registered rule needs both checks. Check B passes on qwen's count,
the same instrument that chose the training rows; Check A fails on one seed.

| | v3 arm | c2d s42 | c2d s43 | bar |
|---|---|---|---|---|
| Check A: recall guard (qwen `group` rows v3 passes at 4.0, kept at 4.0) | | 249/276 = 0.902 PASS | 222/276 = 0.804 FAIL | ≥ 0.9 per seed |
| Check A: comp-draw passes at 4.0 (33,393 rows) | 340 | 312 | 396 | reported |
| Check B: H top-30 qwen personal, weekly mean of 7 builds | 6.14 | 1.29 | 1.29 | both seeds ≤ v3 − 1.0 |
| Check B: worst day | 8 | 3 | 3 | reported |
| Check B: display-eligible rows on 10-09 (normalized ≥ 4.5) | 814 | 571 | 339 | reported |

- s42's pass is one row above the bar: 249/276 is the smallest passing count (248/276 = 0.899).
- **Cap-aware lowering did not remove c2c's recall cost:** seed mean 0.853 here vs 0.835 for c2c (0.807 / 0.862,
  EXP-048). Two lowering builds now land near 0.85.
- **s43 passes at least 110 rows v3 does not pass** (396 − 222 kept `group` − at most 64 other v3 passes), i.e.
  ≥ 32% more passes than v3, none tagged, none labelled. Under ADR-023 new passes at the op-point are where false
  positives come from: a likely specificity cost, unmeasured.
- **c2d thins the page, not only the top.** The display cut (normalized 4.5 = raw 5.15 under v3's curve, `diagnose.txt` §4) sits
  above the 4.4 training target, so a row c2d recognises as personal falls off the page instead of moving down. The
  display-eligible population is 0.66–0.70 (s42) / 0.38–0.42 (s43) of v3's per build (`diagnose.txt` §4). ~21
  qwen-personal rows cannot account for that. Check A measures recall at raw 4.0, so **recall at the display cut is
  unmeasured.** This geometry (a moderate shift next to a cut just above the target) also explains part of the large
  count drop without blaming the instrument.
- Whether a mean is ≤ 6 is undetermined on a floor (EXP-049's rule). 1.29 is a floor too.

### Sensitivity (all derived from `result.txt` unless noted; none changes the verdict)

- **One v3 pass is untaggable:** `portuguese_observador_8e7ee891bb52` (85,459 characters) is `null` in
  `focus-tag-comp`, and re-tagging it with the same instrument returns `null` again (lab `tag-fill/`): the prompt is
  truncated (8,194 prompt tokens) and qwen answers as a Portuguese chat reply with no `focus` field. Both seeds pass it.
  Counted `group`: s42 250/277 = 0.903, s43 223/277 = 0.805. Counted `personal`: unchanged.
- **One tag disagreement between sources:** `southeast_asian_free_malaysia_fbc629ac1f5a` is `group` in the
  daily-baseline and `focus-tag` sets and `personal` in `focus-tag-comp`. The first source wins (`tags()`, same
  precedence as EXP-049's `count.py`), so it counts `group`. Under the other precedence (reviewer's computation):
  Check A s42 248/275 = 0.902, s43 221/275 = 0.804; Check B v3 6.43, s42 1.57, s43 1.29.
- **The two weakest builds:** 10-09 and 10-10 carry the most removal-unknown rows (13 / 7 in the v3 arm) and are
  outside the rebuild control. Without them the means are 5.6 (v3), 1.4 (s42), 0.8 (s43).

## Controls (`result.txt`)

- Determinism: 10/10 reused ids re-tagged identically. PASS.
- Normalization: 103968/103968 production v3 rows reproduce their stamped normalized score within 0.01. PASS.
- Presence: the v3 arm counts ≥ 1 personal on some build. PASS.
- Rebuild (no bar): the v3 arm's top 30 overlaps EXP-049's dated H selection 29, 29, 28, 27, 27 of 30 (10-11..10-15).
- Screen safety sample: 0 sampled rows reach raw ≥ 5.0 under any package. Only the **below-screen** half is a real
  test (highest sampled raw 4.10, one row ≥ 4.0 under s43; the lowest raw in any top 30 is 5.72; `diagnose.txt` §4).
  The `stage1_low` half could not fire: all three packages share v3's probe files, so every sampled `stage1_low` row
  stays `stage1_low` under every arm (1000/1000, `diagnose.txt` §4) and never gets a model raw. Its 0 holds by construction.
- Reviewer's mutation tests: removal sets, availability time and the display filter all change the output (live).
  Reading file names as UTC instead of CEST leaves `result.txt` unchanged (a +3 h shift does change it), so the
  result does not depend on the time-zone conversion.

## Predictions, scored

1. Recall guard 0.85–0.97 per seed: **hit** on s42 (0.902), **missed** on s43 (0.804).
2. Each seed 0–2 below the v3 arm: **missed**, both are 4.86 below. Far outside the range; see below.
3. v3 arm weekly mean 4–7: **hit** (6.14).
4. Rebuild control 18–28 per build: **missed** on 10-11 and 10-12 (29 each); higher than predicted, not lower.
5. Normalization control passes and safety sample 0: **hit** (the `stage1_low` half by construction, see Controls).

## ⚠️ The Check B effect is measured by the instrument that defined the target

`build_c2d.py` chose which training rows to lower with qwen's own `personal` tags (c2c's `focus-tag-train`), and
qwen counts the result. **Guessed, direction unknown:** the drop the owner would see may be SMALLER (stories qwen
misses were not lowered in training, and the student may have learned qwen's quirks) or LARGER in absolute terms
(qwen undercounts the baseline: owner 10 vs qwen 7 on 10-12, EXP-049; the student learns meaning from 31 rows and may
also lower stories qwen misses). A prediction miss of this size is a signal about the instrument and about the page
geometry above, not only about the model.

What holds without trusting qwen's absolute count (`diagnose.txt`, POST HOC):

- The shift is targeted. Over v3's weekly top-30 rows, the median raw shift is −0.65 for qwen-personal vs −0.15
  for qwen-group (s42), and −1.12 vs +0.00 (s43). That separation still rests on qwen's tags. The per-row sizes are
  close to c2c's (−0.82 / −1.16, H-BB8).
- The two seeds are not the same model. Their top 30s share 17–20 rows per build; the identical 1.29 means (9
  personal over 7 builds each) appear coincidental.

## Deviations and incidents

- **Scoring script:** section 2 names `comp_check.py score`; both populations were scored with `score_rows.py`
  (`db6a640`, committed before any score existed). `diagnose.txt` §3: this run's v3 comp scores equal c2c's
  `comp_check.py` scores on all 33,393 rows (max |raw delta| 0.0, 0 stage differences).
- **Template imports (caught by the load guard):** the packages were copied from `filters/belonging/v1_c2b` as in
  c2c's `c2c_remote.sh`. Their `inference*.py` still imported `filters.belonging.v1_c2b`, so the hybrid scorer would
  have scored c2b's model. `score_rows.py`'s load check refused both packages (`scores/failed_run1/` in the lab);
  `v1_c2b` was rewritten to the package's own name in the three `inference*.py` files and only the c2d scoring was
  re-run (`score_chain2.sh`). c2c's packages carry the same rewrite, but `c2c_remote.sh` does not record it.
  Calibration was unaffected: `fit_calibration.py` loads the plain `inference.py`, and its log names
  `v1_c2d_s{42,43}/model`.
- **Start commit:** `training_metadata.json` records `9e748c5` for s42 and `db6a640` for s43 (the checkout was
  fast-forwarded while s42 trained). The two commits differ only by `extract_population.py` and `score_rows.py`,
  which training does not import.

## Reproduce

```bash
python3 analyse.py report > result.txt     # needs the lab files in MANIFEST.json
python3 diagnose.py > diagnose.txt         # post hoc (§1-4)
```

Data: `MANIFEST.json` (lab `experiments/2026-10-15-belonging-c2d/{population,scores,tag,tag-fill}`, plus the reused tags and
the comp draw). Scripts: `build_c2d.py`, `extract_population.py` (sadalsuud), `score_rows.py` (b650), `analyse.py`,
`diagnose.py`. The trained packages are in the lab at `experiments/2026-10-15-belonging-c2d/v1_c2d_s{42,43}` (with the import rewrite), not in the repo.
