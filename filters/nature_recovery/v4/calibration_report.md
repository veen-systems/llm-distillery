# nature_recovery v4 — Calibration Report

Per-dimension isotonic regression (ADR-008), fit on the val set, evaluated on the held-out
test set (n=391). Deployed model = seed-42 scale-2.0/Recall@20 checkpoint.

**Overall test MAE: 0.7695 → 0.5990 (+22.2%)**

| Dimension | MAE before | MAE after | Δ |
|-----------|-----------|-----------|---|
| recovery_evidence | 0.7231 | 0.5636 | +0.1595 |
| measurable_outcomes | 0.7467 | 0.6331 | +0.1136 |
| ecological_significance | 0.8512 | 0.6366 | +0.2146 |
| restoration_scale | 0.7199 | 0.5364 | +0.1835 |
| human_agency | 0.9280 | 0.7115 | +0.2165 |
| protection_durability | 0.6482 | 0.5129 | +0.1353 |

**Tier distribution (test):** oracle high 5 / medium 53 / low 333; calibrated 0 / 44 / 347.
The calibrated ceiling (~6.8 on recovery_evidence) leaves the HIGH tier (≥7) unreachable —
only 2 training articles score 8–10 (documented top-band limit; clip, don't extrapolate).

Raw curve anchors: `calibration.json`. Full evidence: `docs/articles/nature_recovery_v4_evidence/calibration.json`.
