# human_thriving v8 retrained on adjudicated labels — the gate bar, written BEFORE any retrain result

**Written 2026-09-25 ~10:40, while `adj1` was in epoch 2 on b650. No retrain score existed.**
*Correction, same morning: `adj1` was in **epoch 1**, not 2 (the log's progress bar restarts each
epoch; I misread it). The claim that matters, that no retrain score existed, is unaffected.
`verdict.py` applies the bar below mechanically; it was committed, and mutation-tested in five
directions, before any retrain finished.*
The bar is the **assistant's proposal**; the owner asked for the work to continue (TODO item −2)
and did not rule on a bar. Anything below that turns out to need the owner is flagged ⏸️.

⚠️ **What was seen before writing this:** v8's own numbers, from its STORED Ampere dump
(`datasets/gate/ht_v8_test_cuda_retrain/scores_calibrated.jsonl`), under both label sets. Those
are the baseline this bar is written against, so seeing them is disclosed here, not hidden:

| label set on v8's 660 test ids | positives (≥ 4.5) | v8 TP | v8 FP | v8 spec | v8 recall | indeterminate (±0.16) |
|---|---|---|---|---|---|---|
| oracle (`human_thriving_v8/test.jsonl`) | 35 | 11 | 9 | 0.986 | 0.314 | 9 |
| adjudicated (`human_thriving_v8_adj1/test.jsonl`) | 23 | 9 | 11 | 0.983 | 0.391 | 9 |

## Arms
Every arm is scored on **the same 660 v8 test ids**, on **b650's RTX 5090 (CUDA)**, with
`dump_student_scores.py --require-device cuda`, calibrated arm, `ground_truth_gate.py
--recompute-model-wa`, op-point 4.5, gatekeeper cap 3.0, noise floor 0.16.

- **v8** — the deployed adapter, RE-DUMPED on the 5090 (the stored dump is an Ampere artefact
  and is not diffed against 5090 dumps).
- **adj1** — adjudicated labels only (moved-out rows capped at 2.0), v8's split ids.
- **adj3** — adj1 + 186 new positives + 439 capped production hard negatives.
- **adj2** — adj1 + new positives, no negatives. **Diagnostic only**: it separates the positives'
  effect from the negatives'. It cannot win the gate on its own.

Each retrain gets its OWN `calibration.json`, fitted on its own val split
(`fit_calibration.py --no-config-update`), exactly as the playbook requires after any training run.
Training: v8's settings (`--epochs 6 --batch-size 8 --seed 42 --select-metric recall_medium`),
one seed per arm.

## Primary label set: ADJUDICATED
It is the relabel this work exists to test. ⚠️ It is Claude's judgment under a written rubric,
owner-checked 10/10 on the pilot — not independent human truth — and the assistant scoring the
gate is the same model family that produced the labels.

## The bar — ADR-023: specificity first, recall a constraint; the #95 band decides
Let a model's **pessimistic** figure be its band edge with every indeterminate row (predicted
within 0.16 of 4.5) landing the wrong way, and its **optimistic** figure the other edge.
These are the `[lo, hi]` ranges `ground_truth_gate.py` already prints.

A retrain (adj1 or adj3) **WINS** only if, under ADJUDICATED labels, BOTH hold:
1. **Specificity is distinguishably better:** retrain spec `lo` > v8 spec `hi`.
2. **Recall is not distinguishably worse:** retrain recall `hi` ≥ v8 recall `lo`.

**LOSES** if its spec `hi` < v8 spec `lo`, or its recall `hi` < v8 recall `lo`.
**NOT DISTINGUISHABLE** otherwise — and then nothing is concluded, per the Hard Constraint
("two models whose bands overlap are NOT DISTINGUISHABLE whatever their point estimates say").
If both adj1 and adj3 win, the higher spec `lo` is preferred; a tie inside the band goes to adj1
(fewer new ingredients).

**Stated before the result, so it cannot be argued afterwards:** at n = 637 adjudicated
negatives, v8's spec band spans ~6 rows. Clause 1 therefore needs roughly **7 or more fewer
false positives** than v8 at the pessimistic edge. NOT DISTINGUISHABLE is the likely outcome
unless the relabel moved the student a lot. That is a finding, not a failure of the run.

## Secondary checks (reported, not gating)
- **Oracle labels, same 660 rows.** Expected: the retrain's oracle-label recall DROPS, because it
  was taught to reject the 12 oracle positives the adjudication moved out. The check is WHERE
  the drop lands: among the 23 rows positive under BOTH label sets, retrain recall must not be
  distinguishably below v8's (same band rule). A drop there is a real loss, not the relabel working.
- **Flip count at 4.5** vs v8, split by determinate / indeterminate rows. Max |Δ| is not
  reported as evidence of anything.
- **Design weights:** the 660 rows are a 25.1× design-weighted draw. Every figure above is an
  unweighted SAMPLE quantity, as in v8's own 2026-09-06 gate. The comparison is paired on
  identical rows. No figure is quoted as a production rate.

## Limits, stated now
- One seed per arm. The 2026-09-06 retrain showed same-seed runs differ (EXP-015); no seed
  band exists. A WIN is therefore "one draw cleared the band", and the next step (a live audit
  of passers, TODO −2 step 5) is where it is tested again.
- adj2/adj3's own test splits carry extra rows (679/723). They are NOT used; every arm is judged
  on v8's 660.

## What each outcome does next
- **WIN** → live audit of the winner's passers on production data, then the cutover question
  (#151). No deploy follows from this gate alone.
- **NOT DISTINGUISHABLE / LOSE** → report, and ⏸️ the owner decides whether the ≥ 7 pool
  (TODO −2's open question) is worth adding to the positives before another run.
