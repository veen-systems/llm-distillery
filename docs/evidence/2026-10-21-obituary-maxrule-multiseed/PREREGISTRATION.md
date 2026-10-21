# Does `max(title, full)` survive a change of seed? (#159, H-DET5) — pre-registration, 2026-10-21

*Written and committed BEFORE the run. #159's own condition: "Before anything ships, re-measure across a seed set":
EXP-035 measured the rules on ONE model at ONE seed, and #158's seed band on this metric (0.127) is wider than the
effect (+0.049 recall).*

## Design (EXP-034's protocol, with EXP-035's rules on top)

- **Model:** obituary v5's head, retrained from `v5_train_seed.jsonl` (n = 11,329) at each seed in
  `filters/common/detector_seeds.py` `SEED_SET` = (42, 7, 13, 101, 2026). Embedder, window (128), hidden sizes
  (256, 128) and `early_stopping` all as in EXP-034's `multiseed.py`.
- **Eval:** the obituary heldout minus every row that appears in the v3, v4 or v5 training corpus. This is EXP-034's
  leak-free set, computed rather than listed.
- **Rules, each at the live 0.85:**
  1. `full`: the full text, as now;
  2. `max(title, full)`;
  3. `max(title@0.99, full)`, where the title counts only when ≥ 0.99.
- **Reported:**
  - per seed: recall, specificity and FP for each rule;
  - per rule: the BAND (min–max over the seeds);
  - per seed: the PAIRED difference against `full` (Δrecall, Δspecificity, ΔFP). The paired difference is the
    quantity #159 asks about; a band overlap between rules is NOT evidence of no effect when the pairs all point
    one way.
- **Positive control:** the refit at seed 42 is compared with the SHIPPED v5's recorded `v5_score` (the correlation,
  and the flips at 0.85). EXP-034 got 0.9952.

## Predictions

1. Plain max raises recall at EVERY seed, by +0.03 to +0.07.
2. Plain max lowers specificity at every seed, by 0.005 to 0.02.
3. The 0.99 gate's Δrecall is positive at ≥ 4 of 5 seeds and smaller than plain max's at every seed.

## Not decided here

Which rule ships is the owner's call (#159: recall-first vs ADR-023). This only replaces the single-seed numbers
with paired bands. No config, threshold or package changes. $0: local compute on b650 (daytime).
