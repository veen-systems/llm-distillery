"""
Ground-truth deploy gate for nature_recovery (corrected methodology, 2026-07-09).

WHY THIS EXISTS — the flaw in agreement_gate.py it replaces:
  agreement_gate.py judged v4 against the *v2 student* as the baseline
  (`over_demotion` = "articles v2 surfaced but v4 didn't") and drew its Source-A
  cohort from `nr_v4_sourceA_reference.jsonl`, which carries a `_v2_split` field
  and turned out to be **v2-era Gemini labels** — systematically +1.775 higher
  than the DeepSeek labels v4 was trained on. So a DeepSeek-trained (deliberately
  conservative) student was scored against a generous Gemini baseline, and its
  correct demotions of Gemini-inflated content counted as failures. See
  augmented-engineering#25 (reproduce-don't-assess) + memory/feedback-oracle-bias-vs-noise.

THE CORRECTION: judge each model against **held-out oracle ground truth** (the
same oracle the model was trained on = the chosen editorial line), not against
the previous model. A model is deployable if it matches the intended oracle's
surfacing decisions on data it never trained on — and we compare candidate vs
incumbent on that same footing.

Metrics per model, at the MEDIUM surfacing threshold (4.0), vs oracle labels:
  - recall      : of true MEDIUM+ articles, fraction the model surfaces
  - precision   : of surfaced articles, fraction truly MEDIUM+
  - specificity : of true-LOW articles, fraction correctly kept out
  - f1          : harmonic mean of precision/recall
  - spearman    : rank agreement with the oracle weighted average

Usage:
    PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
        --labels datasets/training/nature_recovery_v4/test.jsonl \
        --model v4=datasets/gate/nr_v4_test_scored_by_v4.jsonl \
        --model v2=datasets/gate/nr_v4_test_scored_by_v2.jsonl
"""
import argparse
import json
import math
from pathlib import Path

MEDIUM = 4.0
GATEKEEPER_MIN, GATEKEEPER_CAP = 3.0, 3.5
WEIGHTS = {"recovery_evidence": .25, "measurable_outcomes": .20,
           "ecological_significance": .20, "restoration_scale": .15,
           "human_agency": .10, "protection_durability": .10}
DIMS = list(WEIGHTS)


def label_wa(labels):
    """Gatekeepered weighted average from a 6-vector of oracle scores."""
    d = dict(zip(DIMS, labels))
    wa = sum(d[k] * WEIGHTS[k] for k in DIMS)
    if d["recovery_evidence"] < GATEKEEPER_MIN and wa > GATEKEEPER_CAP:
        wa = GATEKEEPER_CAP
    return wa


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    if len(xs) < 2:
        return 0.0
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    vx = math.sqrt(sum((r - mx) ** 2 for r in rx))
    vy = math.sqrt(sum((r - my) ** 2 for r in ry))
    return cov / (vx * vy) if vx and vy else 0.0


def load_labels(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            out[r["id"]] = label_wa(r["labels"])
    return out


def load_scores(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            rid = r.get("id") or r.get("article_id")
            if rid is not None and r.get("weighted_average") is not None:
                out[rid] = float(r["weighted_average"])
    return out


def load_medium_threshold(config_path):
    """Read tiers.medium.threshold from a filter config.yaml so the gate ALWAYS
    evaluates at the operating point the filter actually deploys. Without this the
    gate silently drifts from production (found 2026-07-10: gate hardcoded 4.0 while
    the deployed op-point was 3.75, so the committed gate could not reproduce the
    recall/precision numbers cited for the deploy). Falls back to MEDIUM on any miss."""
    try:
        import yaml
        cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        # tiers live under scoring: in this schema; tolerate top-level too.
        tiers = cfg.get("scoring", {}).get("tiers") or cfg.get("tiers")
        return float(tiers["medium"]["threshold"])
    except Exception:
        return MEDIUM


def evaluate(truth, pred, medium=MEDIUM):
    ids = [i for i in pred if i in truth]
    tp = sum(1 for i in ids if truth[i] >= medium and pred[i] >= medium)
    fn = sum(1 for i in ids if truth[i] >= medium and pred[i] < medium)
    fp = sum(1 for i in ids if truth[i] < medium and pred[i] >= medium)
    tn = sum(1 for i in ids if truth[i] < medium and pred[i] < medium)
    pos = tp + fn
    recall = tp / pos if pos else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    rho = spearman([truth[i] for i in ids], [pred[i] for i in ids])
    mae = sum(abs(pred[i] - truth[i]) for i in ids) / len(ids) if ids else 0.0
    return {"n": len(ids), "positives": pos, "recall": recall, "precision": precision,
            "specificity": specificity, "f1": f1, "spearman": rho, "mae": mae,
            "tp": tp, "fn": fn, "fp": fp, "tn": tn}


def main():
    ap = argparse.ArgumentParser(description="nature_recovery ground-truth deploy gate")
    ap.add_argument("--labels", required=True, help="held-out oracle-labeled JSONL (id + labels)")
    ap.add_argument("--model", action="append", required=True,
                    help="name=scored.jsonl (repeatable; e.g. v4=..., v2=...)")
    ap.add_argument("--report", default="filters/nature_recovery/v4/ground_truth_gate.json")
    ap.add_argument("--config", default="filters/nature_recovery/v4/config.yaml",
                    help="filter config.yaml; the MEDIUM threshold defaults to its "
                         "tiers.medium.threshold so the gate matches what deploys")
    ap.add_argument("--threshold", type=float, default=None,
                    help="override the MEDIUM surfacing threshold (default: read from --config)")
    args = ap.parse_args()

    medium = args.threshold if args.threshold is not None else load_medium_threshold(args.config)
    truth = load_labels(args.labels)
    report = {"threshold": medium, "n_labeled": len(truth), "models": {}}
    for spec in args.model:
        name, path = spec.split("=", 1)
        report["models"][name] = evaluate(truth, load_scores(path), medium)

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2))

    hdr = f"{'model':6} {'recall':>7} {'prec':>7} {'spec':>7} {'f1':>7} {'spearman':>9} {'mae':>6}"
    print(f"\nGround-truth gate vs held-out oracle labels (threshold {medium}, n={len(truth)})")
    print(hdr)
    print("-" * len(hdr))
    for name, m in report["models"].items():
        print(f"{name:6} {m['recall']:7.3f} {m['precision']:7.3f} {m['specificity']:7.3f} "
              f"{m['f1']:7.3f} {m['spearman']:9.3f} {m['mae']:6.3f}")
    print(f"\nReport: {args.report}")


if __name__ == "__main__":
    main()
