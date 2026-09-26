# Session 2026-07-26 (evening) — solutions v6 train

## What we did

1. **Deployed solutions v5**: e5 probe + v4 model → hybrid scorer running in production. 1,608 articles scored, 62 medium+, ~20 false positives.

2. **Investigated concreteness inflation**: Found `solution_concreteness` median 0.50 vs next dimension median 0.26 — 3x higher. Root cause: v5 used v4-trained model which learned inflation from v4 oracle prompt.

3. **Validated probe quality**: Probe correctly passes all 62 medium+ (0 false negatives, calibrated with `--target-fn 0.02`). Probe screens ~96% of production at Stage 1.

4. **Tightened oracle prompt**: Three blind-spot fixes in prompt-compressed.md:
   - Science/research: "discovery, lab result, or dataset is not a solution" with deployment test
   - Product reviews: expanded to include AI model reviews, benchmark comparisons
   - Regulatory enforcement: explicit fine/sanction language

5. **Rescored 62 medium+ articles**: Oracle correctly dropped 19 false positives (32% reduction). Validated prompt direction. Inter-run variance ~31% at temp=0.3 — chasing noise past this point.

6. **Built v6 training corpus**: Probe-split approach — 4,702 probe-negative zeroed (free), 3,194 kept v4 scores, 2,401 mid-range rescored with v5 prompt ($2.96). 702 false positives dropped from corpus, 28 real solutions promoted.

7. **Trained v6 model**: Gemma-3-1B + LoRA, 3 epochs, 8,236 articles. Val MAE **0.476** (vs v4's 0.564). Epochs: MAE 0.58→0.49→0.48.

8. **Calibrated**: Per-dim isotonic on val set. Calibration marginal (model already well-fit).

## Key insight: probe as binary labeler

The e5 probe eliminates the need for full oracle rescore. For any retrain:
- Run probe inference on corpus (free)
- Probe-negative → all dims = 0 (no oracle needed)
- Probe-positive → rescore with oracle (only 10-50% of corpus)
- Cost: ~$3 instead of ~$12

## State

- **v5**: Deployed and running in production
- **v6**: Trained + calibrated. Gate pending (scored test set, gate script format mismatch needs debug). Model in filters/solutions/v6/model/.
- **Prompt**: Tightened in v5/v6 prompt-compressed.md

## Next session

1. Fix gate script format match → run ADR-021 gate on v6
2. If gate passes: deploy v6 (copy to gpu-server + NexusMind, upload Hub)
3. Measure v6 production quality vs v5 baseline
4. Standing items: commerce v2 regression (#80), calibration crush (#76), nr v4 normalization (#72), obituary detector v4 retrain
