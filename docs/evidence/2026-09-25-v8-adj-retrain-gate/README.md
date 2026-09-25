# human_thriving v8 retrained on adjudicated labels — gate RESULT (2026-09-25)

**All three retrains WIN the pre-registered bar** (`PREREGISTRATION.md`, committed `79013c9`
before any retrain score; applied mechanically by `verdict.py`, committed `7e1d16b`, also before).
By the pre-registered preference (higher spec `lo`), **adj3 is the candidate.** Nothing is
deployed; the next step is a live audit (below).

## What ran
- Training on b650 (RTX 5090), commit `bbf99b5` clean, v8's settings (6 epochs, batch 8, seed 42,
  `--select-metric recall_medium`). Selected epochs: adj1 **5**, adj3 **5**, adj2 **6**.
- Each retrain got its own `calibration.json` fitted on its own val split (658 / 720 / 676 rows).
- All four arms dumped on **CUDA** (`device: declared=cuda parameters=cuda:0`), one pass each,
  on v8's 660 test ids. **v8 was re-dumped on the 5090**; it gives the same TP/FP as the stored
  Ampere dump (9 / 11 under adjudicated labels) and 8 indeterminate rows instead of 9.
- Adapters: v8 `074209ff572c` (the deployed one), adj1 `cef2bc85ac7b`, adj3 `4f4feac2ed6e`,
  adj2 `0ead6a92fed9`. Staged on b650 as `filters/human_thriving/v8_adj{1,3,2}/` (untracked,
  b650 only). Dumps: `datasets/gate/ht_v8_adj_2026-09-25/` (gitignored, local).

## Result — `verdict.py` output, adjudicated labels (PRIMARY)

| arm | pos | TP | FP | spec | spec band | recall | recall band | indet |
|---|---|---|---|---|---|---|---|---|
| v8 | 23 | 9 | 11 | 0.9827 | [0.9812, 0.9890] | 0.391 | [0.348, 0.478] | 8 |
| adj1 | 23 | 7 | 5 | 0.9922 | [0.9906, 0.9937] | 0.304 | [0.261, 0.348] | 4 |
| **adj3** | 23 | 8 | **1** | **0.9984** | [0.9984, 0.9984] | 0.348 | [0.261, 0.348] | 2 |
| adj2 (diagnostic) | 23 | 8 | 1 | 0.9984 | [0.9969, 0.9984] | 0.348 | [0.348, 0.435] | 3 |

Oracle labels (SECONDARY, not gating), same rows: v8 TP 11 / FP 9, spec [0.9840, 0.9920];
adj3 TP 8 / FP **1**, spec [0.9984, 0.9984]; recall 0.314 → 0.229. Full tables: `gate_*.txt`.

## Read these before quoting the win
1. ⚠️ **The recall clause passed with ZERO margin.** Both adj1 and adj3 have recall `hi` = 0.348,
   exactly v8's `lo`. The rule is `≥`, so it passes, but one more lost positive would have made it
   a LOSE. In counts: adj3 drops 2 of v8's true positives and adds 1 (net 9 → 8 of 23).
2. ⭐ **The specificity gain does not depend on the adjudicated labels.** Under the ORACLE's own
   labels, adj3's FPs also fall 9 → 1 and the spec bands do not overlap. Of the 10 v8 false
   positives adj3 removes, only 2 are rows the adjudication moved out; the rest were negatives
   under both label sets. The model got stricter, not just re-aligned to Claude's rubric.
3. ⚠️ **Oracle-label recall is distinguishably lower** (adj3 `hi` 0.229 < v8 `lo` 0.286). This was
   expected and pre-registered as not gating: 2 of the 3 oracle positives adj3 loses were moved out
   by the adjudication. The "rows positive under both label sets" check in the pre-registration
   turned out to BE the primary recall clause: the adjudication only moved in → out and left kept
   rows' labels unchanged, so the 23 adjudicated positives are exactly those rows.
4. **Circularity:** the adjudicated labels and adj3's training labels come from the same Claude
   rubric, and a Claude session scored this gate. Point 2 is the part that escapes that; the live
   audit is the independent test.
5. **One seed, 23 positives, 660 design-weighted rows.** Every figure is an unweighted sample
   quantity (25.1× design span), paired on identical rows. No production rate is implied.
6. **adj2 ≈ adj3 here:** the 439 hard negatives add nothing measurable on this test set beyond the
   186 new positives (same TP/FP; adj3 has a tighter band). The pre-registered preference still
   picks adj3 on spec `lo`.

Row-level changes vs v8 (every flip, determinate or not, and the remaining FPs): `flips.txt`,
from `flips.py`, which uses the gate's own loaders and asserts its FP counts equal the gate's.
adj3's one remaining FP: a Kočani blood-drive article, adjudicated label 4.33, just under 4.5.

## Next (TODO −2 step 5) — needs the owner
A **live audit of adj3's passers** on production data before the cutover question (#151): score a
recent production window with adj3 and v8 side by side on b650, and have the owner (or blind
adjudication, then owner spot-check) judge what adj3 would publish. Not started: it needs a plan,
and the audit's sample and judge are the owner's call.
