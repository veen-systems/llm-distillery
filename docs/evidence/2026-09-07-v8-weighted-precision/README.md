# human_thriving v8 — precision under the production mix (2026-09-07)

**Answer: weighted precision is 0.6073, band [0.5524, 0.8159] — above the
split's 0.550, whose own band is [0.500, 0.7368].** The two bands overlap, so
this is not a distinguishable *difference*; what is solid is that the weighted
band's low end (0.5524) sits above the unweighted point estimate, i.e. the
weighting does not make the reader-facing number worse. The design weighting
was expected to hurt precision (rarer positives) and did not, because it raises
specificity more than it lowers recall.

Run: `EXP-028`. Shipped checkpoint (EXP-027, epoch 5), calibrated arm, op-point
4.50, the same 660 held-out rows and the same dumps the deploy gate used
(`scores_calibrated.jsonl` sha256 `d30f12bc…`, `scores_raw.jsonl` `f370b719…` —
both match `ground_truth_gate.json`'s `inputs` block).

## Why the gate's precision is not the reader's precision

The test split is a design-weighted draw, span **25.1×**: rare cells were
over-sampled on purpose so the model could be measured where it is hard, not
where the corpus is dense. Its unweighted positive rate is **5.3030%**; the
design-weighted rate is **3.1638%**. Recall and specificity are conditional on
the true class and survive that reweighting; **precision does not** — it is a
property of the mix. So `ground_truth_gate.json`'s 0.550 describes the panel,
not the feed.

`phase_c_outcome.py` (2026-09-04) already prints a Horvitz-Thompson arm, but it
reports junk-removed / good-kept / recall / specificity and **never precision** —
the one quantity the weighting actually changes — and it describes the
superseded epoch-4 checkpoint.

## Result — calibrated arm (the one that ships)

| | unweighted (the panel) | design-weighted (the feed) |
|---|---|---|
| positive rate | 5.3030% | 3.1638% |
| **precision** | **0.5500** | **0.6073**  band [0.5524, 0.8159] |
| specificity | 0.9856 | 0.9941  band [0.9933, 0.9974] |
| recall | 0.3143 | 0.2779  band [0.2531, 0.3535] |
| F1 | 0.4000 | 0.3814 |

Weighted cells: TP 138.0 · FP 89.2 · FN 358.4 · TN 15103.7.

**The whole weighted precision band sits at or above the unweighted point
estimate** — its low end, 0.5524, is above 0.550.

Raw arm, for comparison: precision 0.5862 → **0.5776**, specificity 0.9808 →
0.9898, recall 0.4857 → 0.4286.

⭐ **Under the production mix the calibrated arm is ahead of the raw arm on both
ADR-023 criteria, and ONE of the two orderings survives its band.** Specificity
0.9941 [0.9933, 0.9974] vs 0.9898 [0.9865, 0.9915] — **disjoint, so that
ordering holds**. Precision 0.6073 [0.5524, 0.8159] vs 0.5776 [0.4618, 0.6711] —
**overlapping, so NOT distinguishable**; the point estimate favours calibrated
and that is a direction, not an effect. ⚠️ Both arms come from ONE forward pass
on the same rows, so #95's batch-composition mechanism is held fixed between
them and the band is a conservative envelope here rather than the right
instrument for an arm-vs-arm comparison — it is used because it is the bar the
project applies, not because it is tight. Either way this is invisible in
`calibration_report.md`, whose verdict ("calibration does not improve held-out
MAE, −3.6%") is stated in the one metric ADR-023 ranks nothing on. Calibration
still ships for the reason already recorded; the specificity ordering is a
second, independent argument for it on the criterion that governs.

## Why it moved the way it did

Two effects fight. The lower base rate pushes precision down; at unchanged
recall and specificity the arithmetic gives 0.416. But the weighting also
**raises specificity** (0.9856 → 0.9941, i.e. the false-positive rate falls from
1.44% to 0.59%) while lowering recall (0.3143 → 0.2779). The specificity gain
wins. The same fight on the epoch-4 sweep resolved the same direction.

⚠️ **Predicted range, recorded in the script before the run: 0.40–0.60. The
result landed at 0.6073, just above the top of it.** The miss is small and the
direction was the one predicted, but the range was stated too narrow: the
instrument was checked afterwards rather than the number being accepted on
arrival — weighted cells reproduce the point estimates exactly
(138.0 / (138.0 + 89.2) = 0.6073) and the base rate matches the manifest's
3.1638% independently.

## The control

The script computes the **unweighted** arm through the same join, spec,
gatekeeper cap and op-point, and refuses to publish unless it reproduces the
committed `ground_truth_gate.json` **cell-for-cell** (n, positives, tp, fn, fp,
tn, recall, precision, specificity) for every arm. It passes. Without that, a
weighted number is just a number: the weighting is the only thing this script is
allowed to add.

Truth, predictions, the scoring spec and the op-point all come from the shipped
`scripts/gate/ground_truth_gate.py`, not reimplemented here. Weights are
`1 / inclusion_probability` from `datasets/scored/human_thriving_v8/corpus.jsonl`
(6,590 rows, all present); the loader **refuses a partially-weighted table** and
refuses any `p` outside `(0, 1]`.

## What this does NOT establish

- **It is still the oracle's opinion, not a reader's.** Every "false positive"
  here is a row the DeepSeek oracle scored under 4.5; 6 of the 9 unweighted FPs
  are rows the oracle itself labels `in_scope`.
- **It is still a 660-row sample**, reweighted — not production traffic. The
  weighted TN count of 15,103 is an estimate of a population, not 15,103
  observed articles.
- **It says nothing about v8 on live NexusMind data**, which has a different
  source mix, a different language mix and enrichment applied. The hand-audit of
  the first ~50 surfaced production articles is still the measurement that
  matters.

## Reproduce

```bash
.venv/bin/python docs/evidence/2026-09-07-v8-weighted-precision/weighted_precision.py \
  --model calibrated=datasets/gate/ht_v8_test_cuda_retrain/scores_calibrated.jsonl \
  --model raw=datasets/gate/ht_v8_test_cuda_retrain/scores_raw.jsonl \
  --report docs/evidence/2026-09-07-v8-weighted-precision/weighted_precision.json
```

⚠️ The dumps are gitignored (`datasets/*`). Source of record:
`b650-gpu:~/llm-distillery/ht_v8_test_dump_cuda_retrain/`; verify by sha256
against `ground_truth_gate.json`'s `inputs` block before using them.
