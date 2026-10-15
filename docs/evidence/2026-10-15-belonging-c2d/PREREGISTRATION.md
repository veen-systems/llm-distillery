# belonging c2d: cap-aware lowering of personal training rows, judged on ranking H (pre-registration, 2026-10-15)

*Written and committed BEFORE any c2d model exists, any population is scored, or any tag is read. Template:
`experiments/PREREGISTRATION.template.md`. Context: `docs/TODO.md` item 0a; H-BB6, H-BB8; EXP-048 (c2c), EXP-049
(the H replay this reuses).*

## 0. What is under test, and the decision it feeds

- **Candidate c2d** = v3's recipe on `datasets/training/belonging_c2d` (`build_c2d.py`, this directory): the
  personal-tagged rows whose EFFECTIVE score exceeds 4.4 are lowered to exactly 4.4, holding community_fabric at or
  above the gatekeeper's 3.0 (c2c ignored the gatekeeper, H-BB8). `--check` before this file: **41 rows changed**
  (31 train / 3 val / 7 test), 10 of them with community_fabric held at 3.0. Mutation-tested: dropping the floor,
  dropping the effective-score assert, or selecting on weighted instead of effective score all fail the build.
- **Decision fed:** whether c2d is worth a GATE (a fresh held-out set and the owner's go; all three held-out sets
  are spent). This check does not switch anything. Owner ruling 2026-10-14: "prepare now, judge on H".
- **Bar context:** ≤ 6 single-person stories of 30 as a weekly average
  (`docs/decisions/2026-10-10-belonging-personal-story-bar.md`).

## 1. Training

- b650 (RTX 5090), `venv-prodparity`, checkout fast-forwarded to `origin/main` first (it sits at `4e3a2aa`; tracked
  files clean). Package template and command exactly as c2c (`~/ld-lab/experiments/2026-10-12-belonging-c2c/c2c-logs/c2c_remote.sh`),
  with `belonging_c2d` and `v1_c2d_s{42,43}`: `--epochs 6 --batch-size 8 --select-metric last --medium-threshold 4.0
  --use-head-tail --head-tokens 256 --tail-tokens 256`, then `fit_calibration.py --no-config-update`.
- Seeds 42 and 43. One seed cannot separate a 41-row change from the seed band (c2c's seeds passed 271 vs 461).

## 2. Check A: the recall guard (unchanged from c2c, amendment B)

- c2c's composition draw (lab `datasets/belonging_comp_draw/v1/belonging_comp_rows.jsonl`, 33,393 rows), scored
  with v3, c2d-s42 and c2d-s43 on b650 with `comp_check.py score` (v3 RESCORED, so all three share one code version
  and device).
- Of the draw's rows with v3 raw ≥ 4.0 that qwen tags `group`, the share each seed still passes at 4.0. Tags reused
  from c2c's `focus-tag-comp`; any v3 pass without a tag is tagged with the same instrument (section 4).
- **Bar: ≥ 0.9 per seed.** Below that, c2d fails.

## 3. Check B: the top-30 personal count on H

- **Population:** every id in the belonging `filtered_*.jsonl` files on sadalsuud from `filtered_20260929` on, with
  `published_date` ≥ 2026-09-29, newest file's text. **Screen:** rows whose production belonging stamp is
  `stage2` with raw ≥ 2.0 (counted 2026-10-15: 23,710 of 331,306 ids). The screen uses a production raw, from v1 or v3
  depending on the date.
- **Screen safety sample:** 1,000 below-screen `stage2` rows and 1,000 `stage1_low` rows, chosen with
  `random.Random(0)` from the sorted ids, scored like the rest. **Safe if no sampled row reaches raw ≥ 5.0 under any
  of the three packages.** Otherwise Check B is reported as provisional, with the estimated number of missed rows
  (rate × stratum size).
- **Scoring:** v3, c2d-s42, c2d-s43 on b650, all on the same rows. A `stage1_low` result is excluded (a probe
  estimate, not a model output). **Normalized** = `filters.common.score_normalization.apply_normalization(raw,
  filters/belonging/v3/normalization.json)` for all three, so the ranking differs only by raw.
- **Builds:** EXP-049's seven (10-09 to 10-14 at 14:30Z, 10-15 at 06:37:16Z). Per build: rows first seen in a
  filtered file at or before the build (file timestamp from its name), published within the 10 days before it,
  normalized ≥ 4.5, minus EXP-049's **dated** removals (10-13 removals for builds through 10-13, 10-15 removals
  after). H order (`replay.py` `order("H hybrid")`), top 30. No version filter: every row is rescored by every arm.
  A top-30 row that no observed build covers is counted as "removal status unknown".
- **Measure:** qwen `personal` count per build, the weekly mean over the 7 builds, the worst day.
- **Bar for "worth a gate":** BOTH seeds' weekly mean ≤ the v3 arm's weekly mean − 1.0 (one fewer personal story
  per day on the floor), AND Check A passes. Whether a mean is ≤ 6 is reported, but under the floor it is
  undetermined (EXP-049's rule).

## 4. Instrument and controls

- qwen3.8:27b on b650, EXP-049's tagger unchanged (temperature 0, seed 42). Reuse rule and determinism control as
  EXP-049 (10 reused ids re-tagged, ≥ 9/10 must match). A qwen count is a FLOOR.
- **Normalization control:** for production rows stamped v3, `apply_normalization(raw)` reproduces the stamped
  normalized `weighted_average` within 0.01 on ≥ 99% of them. Otherwise stop: the ranking input is wrong.
- **Rebuild control:** the v3 arm's top 30 vs EXP-049's dated H selection, 10-11 to 10-15, overlap per build.
  Reported, no bar: they differ by device term, availability time (file vs summary) and rescoring.
- **Presence control:** the v3 arm counts ≥ 1 personal on at least one build.

## 5. Predictions (scored after)

1. Check A: recall guard 0.85–0.97 per seed.
2. Check B: each seed's weekly mean is 0–2 below the v3 arm's. I would not be surprised by "no difference beyond the
   seed band".
3. v3 arm weekly mean (qwen): 4–7.
4. Rebuild control: 18–28 of 30 per build.
5. Normalization control passes; screen safety sample: 0 rows ≥ 5.0.

## 6. Data and limits

- Text stays in the lab: extraction on sadalsuud, scoring and tagging on b650, `lab.py pull` into
  `~/ld-lab/experiments/2026-10-15-belonging-c2d/`, cited in `MANIFEST.json`. $0 oracle; b650 GPU only.
- Limits: availability by NexusMind file time, not ovr's summary time; removals observed on two builds only; rows
  c2d passes but v3 never did have no removal history; one build per day; qwen is a floor.
