# human_thriving v10 candidate (adj4) — the gate bar, written BEFORE any training

**2026-09-26. RULED: the owner chose the bar below ("Recall up, spec held", an option the assistant wrote), before any training.**
No adj4 model exists; nothing has trained. v9's numbers below are from the 2026-09-25 gate
(`../2026-09-25-v8-adj-retrain-gate/README.md`), seen before writing, and disclosed here.

## What adj4 is
`datasets/training/human_thriving_v8_adj4/` (gitignored; built by
`../2026-09-26-thriving-ge7-pool/build_adj4.py`, staged on b650 with matching md5s) = v9's training
data (adj3) + the ≥ 7 pool's **177** oracle-labelled positives + **471** capped hard negatives,
each set split 80/10/10 separately. Labels ≥ 4.5: train 257 → **380**, val 34 → 50, test 33 → 48.
It is the volume lever the owner chose for v9 instead of a lower cut-off.

## Arms and protocol (unchanged from the v9 gate)
**v9** (deployed adapter, RE-DUMPED in the same session) vs **adj4**, on **v8's 660 test ids**, b650
RTX 5090 CUDA, `dump_student_scores.py --require-device cuda`, calibrated arm, `ground_truth_gate.py
--recompute-model-wa`, op-point 4.5, gatekeeper cap 3.0, noise floor 0.16. Training: v8/v9 settings
(`--epochs 6 --batch-size 8 --seed 42 --select-metric recall_medium`), one seed. adj4 gets its own
`calibration.json` fitted on its own val split. Primary labels: ADJUDICATED
(`human_thriving_v8_adj1/test.jsonl`), 23 positives / 637 negatives.

## Why the v9 bar cannot be reused (proved before choosing)
v9's bar demanded **specificity distinguishably better**. v9 sits at 1 FP of 637, spec band
[0.9984, 0.9984]. adj4's spec `lo` would have to exceed 0.9984, meaning 0 FPs and 0 indeterminate
negatives. That is effectively unreachable, and it tests the wrong thing: the pool's purpose is
volume, not fewer FPs.

## Proposed bar — recall is the target, specificity may not get worse (ADR-023 order kept)
adj4 **WINS** only if, under adjudicated labels, BOTH hold:
1. **Recall distinguishably better:** adj4 recall `lo` > v9 recall `hi` (0.348). In counts, at
   least **9 of 23** true positives with every indeterminate row landing the wrong way.
2. **Specificity not distinguishably worse:** adj4 spec `hi` ≥ v9 spec `lo` (0.9984). In counts,
   at most **1 false positive** of 637 with every indeterminate row landing the right way.
**LOSES** if spec `hi` < v9 spec `lo`, or recall `hi` < v9 recall `lo` (0.261).
**NOT DISTINGUISHABLE** otherwise, and nothing is concluded.

**Stated now:** with 23 positives the recall clause has little power (one TP is 0.043), and
clause 2 allows no added false positive at all. **NOT DISTINGUISHABLE or LOSE (on clause 2) are
the likely outcomes**; either is a finding. A WIN would be one draw clearing the band (one seed).

## Secondary (reported, not gating)
- **The pool's own held-out rows** (adj4 test additions: 18 positives, 47 hard negatives; neither
  model trained on them): TP and FP for both arms. This is where more power is. These rows are
  design-weighted toward production ≥ 7 articles, so they are not a production rate.
- Oracle labels on the 660; flip count at 4.5 by determinate/indeterminate; never max |Δ|.

## What each outcome does next
- **WIN** → live audit of adj4 vs v9 on a production week (the v9 protocol), then the owner.
- **NOT DISTINGUISHABLE / LOSE** → report. ⏸️ The owner decides; v9 stays live either way.

## Before training
1. ✅ Bar ruled by the owner, 2026-09-26.
2. ⏸️ The GPU — owner: "Wait; I'll free it". Check it is free before starting; do not assume. At setup, a `roofvision` process holds 24.5 of 32.6 GB (0% utilisation at 2026-09-26 ~17:30).
