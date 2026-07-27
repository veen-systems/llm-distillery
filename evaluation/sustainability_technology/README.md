# Sustainability Technology Filter - Evaluation

Cross-version evaluation and ground truth data for the sustainability_technology filter.

## Key Results

| Metric | Value |
|--------|-------|
| **Prefilter v2.1 FP Block Rate** | 88.2% |
| **Prefilter v2.1 TP Pass Rate** | 89.0% |
| **Remaining FPs for Oracle** | 32 (12%) |

## Contents

| Item | Description |
|------|-------------|
| `PREFILTER_EVALUATION_REPORT.md` | Full evaluation report with methodology |
| `V1_VS_V2_COMPARISON.md` | Historical v1 vs v2 comparison |
| `compare_prefilters.py` | A/B test script for prefilter versions |
| `ground_truth/` | 271 manually reviewed false positives |
| `true_positives/` | 300 frozen true positives for testing |

## Summary

The v2.1 prefilter achieves a good balance:
- Blocks 88% of false positives at the keyword level
- Passes 89% of true positives to the scoring model
- The remaining 12% FPs require oracle judgment (semantic ambiguity)

Attempts to improve FP blocking further (v2.2 with more AI/ML patterns) caused unacceptable TP regression (-12.7%) without improving FP block rate.

## Running Tests

```bash
cd llm-distillery
python evaluation/sustainability_technology/compare_prefilters.py
```

## Related Documentation

- **Filter reports:** [`filters/sustainability_technology/v3/reports/`](../../filters/sustainability_technology/v3/reports/)
- **Prefilter source:** [`filters/sustainability_technology/v3/prefilter.py`](../../filters/sustainability_technology/v3/prefilter.py)
