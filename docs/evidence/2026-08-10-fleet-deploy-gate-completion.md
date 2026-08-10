# The fleet, measured — three deployed filters had no accuracy number at all

**Measured 2026-08-10. ADR-021 deploy gate, all six deployed filters.**

## One-line answer

**#102's premise survives the completed comparison set: `uplifting v7` really is
the specificity outlier, at 1.79× the next worst.** And the set was worth
completing — `investment_risk v6`, never measured before today, comes in
**second worst at 4.5% FPR**, three times `belonging v1`.

## Why this was run

Before today, **3 of 6 deployed filters had ever been measured**. `belonging v1`,
`cultural_discovery v5` and `investment_risk v6` were live, scoring production
articles, with no recall, no specificity, no number of any kind. So llm-distillery#102's
headline — *"`uplifting v7` is the specificity outlier, 8.1% FPR vs 2–3%"* — was
a claim over half the population, compared against the only two filters that
happened to have gates.

It became cheap the same day: `b650:~/llm-distillery/venv-prodparity` on **CPU**
was measured **bit-identical to gpu-server's serving venv** (660/660 rows, 0
verdict flips at every threshold), so threshold work no longer waits for a gap
between pipeline cycles.

## The fleet, at each filter's own 4.0 op-point

| filter | recall | specificity | **FPR** | n | split positive rate |
|---|---|---|---|---|---|
| **uplifting v7** | 0.736 | **0.919** | **8.1%** | 660 | 32.7% |
| **investment_risk v6** ⭐ | **0.761** | 0.955 | **4.5%** | 1045 | 15.6% |
| solutions v6 | 0.671 | 0.972 | 2.8% | 1032 | 16.2% |
| nature_recovery v4 | 0.650 | 0.979 | 2.1% | 391 | 15.3% |
| **cultural_discovery v5** ⭐ | 0.587 | 0.980 | 2.0% | 857 | 8.8% |
| **belonging v1** ⭐ | 0.600 | **0.985** | **1.5%** | 738 | 11.5% |

⭐ = first measurement ever.

**Read recall and specificity only.** They are conditional on the true class, so
the split's positive rate does not distort them. Precision, MAE and F1 are
base-rate dependent and are not comparable across these rows (ADR-023).

## What it establishes

1. **`uplifting v7` is genuinely the outlier.** 8.1% FPR against a fleet that
   otherwise runs 1.5–4.5%: **1.79× the next worst** and **5.4× the best**. #102
   stands, now on the full population rather than half of it.
2. **`investment_risk v6` is the new second concern** — 4.5% FPR, three times
   `belonging v1`'s, and nobody knew because nobody had looked. It also has the
   fleet's **best recall** (0.761), so it is not simply a loose filter; it sits
   at a different point on the same trade.
3. **`belonging v1` and `cultural_discovery v5` are conservative**, not broken —
   lowest FPR *and* lowest recall (0.600, 0.587). Whether that recall is
   acceptable is an editorial question nobody has been able to ask until now.

## Caveats that bind these numbers

- **All CPU. Production serves on GPU.** CPU-vs-CUDA is worth 1 verdict flip at
  a 4.0 op-point on `uplifting v7`; unquantified for these three. llm-distillery#104.
- **The three older gate files carry no #95 band** — they predate the specificity
  band added this morning. The three new ones have it. `belonging v1`'s is
  degenerate ([0.985, 0.985]: only 7 indeterminate rows, none in the TN/FP cells).
- **`cultural_discovery v5` has no `tiers` block** (pre-ADR-014, still on
  `score_scale_factor`); its 4.0 op-point was supplied explicitly and
  cross-checked against `normalization.json` `raw_min` = 4.0006.
- **`cultural_discovery v5`'s gatekeeper binds 0 times in 857 rows** —
  `evidence_quality` < 3 capping at 4.0, flagged inline rather than in a
  `gatekeepers:` block. That is the llm-distillery#94 shape (an inert gatekeeper) and
  deserves its own look; it does not affect this measurement.
- Adapter weights were **md5-verified against production's own copies** before
  scoring. `investment_risk v6`'s live weights were found under NexusMind's
  `filters/` tree — gpu-server's llm-distillery checkout carries it under the
  **hyphenated** `investment-risk`, which is a naming drift worth fixing.

## Reproduce

```bash
# on b650, CPU + venv-prodparity, per filter
bash /tmp/gate3.sh          # see this commit's scratchpad form

PYTHONPATH=. python scripts/verification/parity_dump_to_gate_input.py \
    --dump datasets/parity/<filter>_test_b650cpu-prodstack_2026-08-10.jsonl \
    --calibration filters/<filter>/calibration.json --out /tmp/gi.jsonl
PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
    --labels datasets/training/<split>/test.jsonl \
    --config filters/<filter>/config.yaml --recompute-model-wa --threshold 4.0 \
    --model <name>=/tmp/gi.jsonl --report filters/<filter>/ground_truth_gate.json
```
