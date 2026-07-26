#!/usr/bin/env python3
"""Backtest violence_promotion v1 MLP against Phase 1 calibration set."""
import sys, json
sys.path.insert(0, ".")
from filters.common.violence_promotion.v1.inference import ViolencePromotionFilterV1

# Load calibration set
cal = []
with open("/tmp/calibration_scored_v2.jsonl") as f:
    for line in f:
        if line.strip():
            cal.append(json.loads(line))

valid = [a for a in cal if a.get("label") in ("positive", "negative")]
n_pos = sum(1 for a in valid if a["label"] == "positive")
n_neg = sum(1 for a in valid if a["label"] == "negative")
print(f"Calibration: {len(valid)} valid (pos={n_pos}, neg={n_neg})")

detector = ViolencePromotionFilterV1(threshold=0.95, device="cpu")
results = detector.batch_predict(valid, batch_size=32)

tp = fp = tn = fn = 0
for article, result in zip(valid, results):
    true_pos = article["label"] == "positive"
    pred_pos = result["is_violence_promotion"]
    if true_pos and pred_pos:
        tp += 1
    elif true_pos and not pred_pos:
        fn += 1
    elif not true_pos and pred_pos:
        fp += 1
    else:
        tn += 1

total = tp + fp + tn + fn
acc = (tp + tn) / total if total else 0
prec = tp / (tp + fp) if (tp + fp) else 0
rec = tp / (tp + fn) if (tp + fn) else 0
f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0

print(f"\n=== Backtest (threshold=0.95) ===")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}")
print(f"Recall:    {rec:.4f}")
print(f"F1:        {f1:.4f}")
print(f"TP={tp} FP={fp} TN={tn} FN={fn}")

# Score distribution
scores = [r["score"] for r in results]
BAR = "█"
print(f"\nScore distribution:")
buckets = [(0.0, 0.1, "0.0-0.1"), (0.1, 0.5, "0.1-0.5"), (0.5, 0.9, "0.5-0.9"),
           (0.9, 0.95, "0.9-0.95"), (0.95, 1.01, "0.95-1.0")]
for lo, hi, label in buckets:
    count = sum(1 for s in scores if lo <= s < hi)
    bar = BAR * max(1, count // 2) if count else ""
    print(f"  {label}: {count:>4} {bar}")

# False positives
print(f"\n=== False Positives (MLP=violence, oracle=not) ===")
fp_shown = 0
for article, result in zip(valid, results):
    if result["is_violence_promotion"] and article["label"] == "negative":
        print(f"  [{result['score']:.4f}] {article.get('title', '')[:120]}")
        fp_shown += 1
if fp_shown == 0:
    print("  (none)")

# False negatives
print(f"\n=== False Negatives (MLP=not, oracle=violence) ===")
fn_shown = 0
for article, result in zip(valid, results):
    if not result["is_violence_promotion"] and article["label"] == "positive":
        print(f"  [{result['score']:.4f}] {article.get('title', '')[:120]}")
        fn_shown += 1
if fn_shown == 0:
    print("  (none)")

print("\nDone.")
