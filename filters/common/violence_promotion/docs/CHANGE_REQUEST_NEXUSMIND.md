# Change Request: Violence Promotion Prefilter Integration

**CR ID:** CR-2026-002
**Date:** 2026-07-26
**Requested by:** LLM Distillery Team (LD#73)
**Target System:** NexusMind (NM#274)
**Priority:** P1 (active build)
**Estimated Effort:** 2-3 hours

---

## Summary

Add a violence promotion binary prefilter to the NexusMind pipeline. This ML-based classifier flags articles that promote or normalise mass violence — active combat, weapons manufacturing as progress, military force as solution, state violence against citizens. Stamp-only per ADR-004: ovr.news excludes stamped articles at selection; other consumers (investment_risk, resilience) keep them.

**Violence is not constructive.**

## Problem Statement

The calibration scan (300 articles) found 8.7% of pipeline articles contain violence-promoting content. The training corpus (2000 oracle-labeled articles) confirms ~10.8% positive rate. Without a prefilter:
1. ovr.news may surface articles that normalise instruments of violence as "constructive"
2. No programmatic boundary exists between "conflict reported" and "violence promoted"
3. Editorial gate has no violence-awareness signal to act on

## Proposed Solution

Integrate a pre-trained MLP classifier (frozen `paraphrase-multilingual-mpnet-base-v2` → StandardScaler → sklearn MLPClassifier) that detects violence promotion with:
- **93.6% precision** (OOF CV), **94.1%** on held-out calibration
- **55% recall** (OOF CV), **61.5%** on held-out calibration
- **~90ms inference** per article on CPU
- **Multilingual support** (50+ languages via mpnet-base-v2)
- **1 false positive / 268 negatives** on independent calibration set

### Pipeline Change

```
BEFORE:
RSS → Enrich → [Domain Filters] → Output

AFTER:
RSS → Enrich → [Violence Promotion Prefilter] → [Domain Filters] → Output
                         ↓
                  prefiltered_out/violence_promotion/
```

## Technical Specification

### 1. New Module

**Source:** `llm-distillery/filters/common/violence_promotion/v1/`
**Destination:** `NexusMind/filters/common/violence_promotion/v1/`

Files to copy:
```
violence_promotion/
├── __init__.py
└── v1/
    ├── __init__.py
    ├── inference.py              # ViolencePromotionFilterV1 class
    ├── config.yaml               # Threshold, embedder, batch settings
    └── models/
        ├── mlp_classifier.pkl    # Trained MLP (~2.7 MB)
        ├── scaler.pkl            # StandardScaler (~19 KB)
        └── training_config.json  # Embedder, dimensions, CV metrics
```

### 2. Pipeline Integration

**File:** `scripts/main.py`
**Location:** After enrichment, before domain filters

#### Add global singleton

```python
from filters.common.violence_promotion.v1.inference import ViolencePromotionFilterV1

_violence_promotion_detector = None

def _get_violence_promotion_detector():
    global _violence_promotion_detector
    if _violence_promotion_detector is None:
        _violence_promotion_detector = ViolencePromotionFilterV1(
            threshold=0.95,
            device="cpu",
        )
    return _violence_promotion_detector
```

#### Add prefilter step

```python
def _prefilter_violence_promotion(articles: list) -> tuple[list, list]:
    """Split articles into clean and violence-promotion sets."""
    detector = _get_violence_promotion_detector()
    results = detector.batch_predict(articles)
    clean, flagged = [], []
    for article, result in zip(articles, results):
        article['_is_violence_promotion'] = result['is_violence_promotion']
        article['_violence_promotion_score'] = result['score']
        if result['is_violence_promotion']:
            flagged.append(article)
        else:
            clean.append(article)
    return clean, flagged
```

### 3. Output

Flagged articles saved to `data/prefiltered_out/violence_promotion/` following the same pattern as `commerce/` and `obituary/`.

### 4. Field Contract

Each article passing through gets two metadata fields:

| Field                        | Type    | Description                      |
| ---------------------------- | ------- | -------------------------------- |
| `_is_violence_promotion`     | boolean | True if score ≥ threshold (0.95) |
| `_violence_promotion_score`  | float   | Raw MLP probability (0–1)        |

Consumers (ovr.news) check `_is_violence_promotion` at selection time — a cheap boolean check, not an inference call.

## Calibration Report

### Threshold Sweep (5-fold OOF, n=1957)

| Threshold | Precision | Recall | TP  | FP | FN  | TN   |
| --------- | --------- | ------ | --- | -- | --- | ---- |
| 0.5       | 0.8763    | 0.8057 | 170 | 24 | 41  | 1722 |
| 0.8       | 0.8896    | 0.6872 | 145 | 18 | 66  | 1728 |
| 0.9       | 0.8958    | 0.6114 | 129 | 15 | 82  | 1731 |
| **0.95**  | **0.9355**| **0.5498** | **116** | **8** | **95** | **1738** |
| 0.97      | 0.9623    | 0.4834 | 102 | 4  | 109 | 1742 |
| 0.99      | 0.9747    | 0.3649 | 77  | 2  | 134 | 1744 |

### Independent Calibration (n=294, held-out from Phase 1)

| Metric    | Value   |
| --------- | ------- |
| Accuracy  | 96.26%  |
| Precision | 94.12%  |
| Recall    | 61.54%  |
| F1        | 0.7442  |
| False Pos | 1 / 268 |

### Boundary Filters (risk of over-block)

At threshold 0.95: **8 of 1746 true negatives flagged**. Filter-level breakdown unavailable (articles weren't filter-tagged in the corpus), but the single calibration FP was a Korean article about an Su-57 fighter jet crash — a legitimate borderline case (weapons system in headline, but article framed as news reporting).

## Dependencies

- `sentence-transformers` (already in NexusMind's dependencies — used by existing filters)
- `scikit-learn` (already in NexusMind's dependencies)
- No GPU required — inference runs on CPU (~90ms/article)

## Rollback

Remove the prefilter call from `main.py` and delete the `violence_promotion/` module directory. No database migration, no schema change.

## Acceptance Criteria

1. [ ] `violence_promotion/` module copied to NexusMind
2. [ ] Prefilter step integrated in `main.py` (after enrichment, before domain filters)
3. [ ] Flagged articles written to `data/prefiltered_out/violence_promotion/`
4. [ ] `_is_violence_promotion` and `_violence_promotion_score` fields present on all articles
5. [ ] Shadow-mode run: 1 pipeline cycle, verify score distribution matches calibration
6. [ ] ovr.news reads `_is_violence_promotion` at selection (separate ovr.news CR)
