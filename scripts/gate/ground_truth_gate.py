#!/usr/bin/env python3
"""
Ground-truth deploy gate (ADR-021).

Judge each candidate model against held-out ORACLE ground truth (the chosen
editorial line) at the MEDIUM surfacing threshold — recall / precision /
specificity / F1 / Spearman — NOT against the prior deployed model.

Filter-agnostic: the dimensions, weights, gatekeeper, and surfacing threshold are
read from the filter's config.yaml via --config. When --config lacks a
scoring.dimensions block (or is omitted), the gate falls back to the
nature_recovery v4 constants below, so the existing unit tests and prior
invocations reproduce exactly.

Usage:
    # nature_recovery (defaults reproduce the original behavior)
    PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
        --labels datasets/gate/nr_v4_test_labels.jsonl \
        --config filters/nature_recovery/v4/config.yaml \
        --model v4=datasets/gate/nr_v4_test_scored_by_v4.jsonl \
        --model v2=datasets/gate/nr_v4_test_scored_by_v2.jsonl

    # any other filter — dims/weights/gatekeeper come from its config
    PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
        --labels datasets/training/solutions_v4/test.jsonl \
        --config filters/solutions/v4/config.yaml \
        --model v4=datasets/gate/solutions_v4_test_scored.jsonl

    # sweep the gatekeeper cap (demote-vs-exclude); recompute is auto-enabled so
    # the model side uses the same cap as the oracle side.
    ... --gatekeeper-cap 2.9
"""
import argparse
import json
import math
from pathlib import Path

# --- nature_recovery v4 defaults (kept so the unit tests + prior runs are
#     unchanged when no scoring spec is supplied via --config) ---
MEDIUM = 4.0
GATEKEEPER_MIN, GATEKEEPER_CAP = 3.0, 3.5
GATEKEEPER_DIM = "recovery_evidence"
WEIGHTS = {"recovery_evidence": .25, "measurable_outcomes": .20,
           "ecological_significance": .20, "restoration_scale": .15,
           "human_agency": .10, "protection_durability": .10}
DIMS = list(WEIGHTS)


def _spec(dims=None, weights=None, gk_dim=None, gk_min=None, gk_cap=None):
    """A scoring spec (dims / weights / gatekeeper); unset fields fall back to the
    nature_recovery defaults above."""
    return {
        "dims": dims if dims is not None else DIMS,
        "weights": weights if weights is not None else WEIGHTS,
        "gk_dim": gk_dim if gk_dim is not None else GATEKEEPER_DIM,
        "gk_min": gk_min if gk_min is not None else GATEKEEPER_MIN,
        "gk_cap": gk_cap if gk_cap is not None else GATEKEEPER_CAP,
    }


def _wa(dim_scores, spec):
    """Gatekeepered weighted average from a {dim: score} mapping."""
    weights = spec["weights"]
    wa = sum(dim_scores[k] * weights[k] for k in weights)
    gk = spec["gk_dim"]
    if gk is not None and gk in dim_scores and dim_scores[gk] < spec["gk_min"] and wa > spec["gk_cap"]:
        wa = spec["gk_cap"]
    return wa


def label_wa(labels, spec=None, dim_names=None):
    """Gatekeepered weighted average from an oracle label vector.

    labels: per-dim oracle scores. dim_names: the order of `labels` (defaults to
    the spec's dims). spec defaults to the nature_recovery constants.
    """
    spec = spec or _spec()
    names = dim_names if dim_names is not None else spec["dims"]
    return _wa(dict(zip(names, labels)), spec)


def load_scoring_spec(config_path):
    """Build a scoring spec from a filter config.yaml, or None if the config has no
    scoring.dimensions block (→ caller uses the nature_recovery defaults).

    Gatekeeper is read from scoring.gatekeepers.<first> (dimension / threshold /
    max_score), falling back to a dimension flagged `gatekeeper: true`.
    """
    try:
        import yaml
        cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        scoring = cfg.get("scoring", {})
        dim_cfg = scoring.get("dimensions")
        if not dim_cfg:
            return None
        dims = list(dim_cfg.keys())
        weights = {d: float(dim_cfg[d].get("weight", 0.0)) for d in dims}
        gk_dim = gk_min = gk_cap = None
        gks = scoring.get("gatekeepers") or {}
        if gks:
            g = next(iter(gks.values()))
            gk_dim = g.get("dimension")
            if g.get("threshold") is not None:
                gk_min = float(g["threshold"])
            if g.get("max_score") is not None:
                gk_cap = float(g["max_score"])
        else:
            for d in dims:
                if dim_cfg[d].get("gatekeeper"):
                    gk_dim = d
                    gk_min = float(dim_cfg[d].get("gatekeeper_threshold", 0))
                    gk_cap = float(dim_cfg[d].get("gatekeeper_max_score", 0))
                    break
        return _spec(dims=dims, weights=weights, gk_dim=gk_dim, gk_min=gk_min, gk_cap=gk_cap)
    except Exception:
        return None


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


def load_labels(path, spec=None):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            # Use the record's own dimension order if present (robust to any
            # config/label ordering drift); else the spec's dims.
            names = r.get("dimension_names")
            out[r["id"]] = label_wa(r["labels"], spec=spec, dim_names=names)
    return out


def load_scores(path, spec=None):
    """Read model predictions. With a spec (and per-dim `scores` in the record),
    recompute the gatekeepered weighted average so the model side uses the same
    weights + gatekeeper cap as the oracle side (needed when sweeping the cap).
    Otherwise read the stored `weighted_average` (the original behavior)."""
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        rid = r.get("id") or r.get("article_id")
        if rid is None:
            continue
        if spec is not None and isinstance(r.get("scores"), dict) and all(
            d in r["scores"] for d in spec["weights"]
        ):
            out[rid] = _wa(r["scores"], spec)
        elif r.get("weighted_average") is not None:
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
    ap = argparse.ArgumentParser(description="filter-agnostic ground-truth deploy gate (ADR-021)")
    ap.add_argument("--labels", required=True, help="held-out oracle-labeled JSONL (id + labels)")
    ap.add_argument("--model", action="append", required=True,
                    help="name=path.jsonl of model-scored articles (repeatable)")
    ap.add_argument("--report", default="filters/nature_recovery/v4/ground_truth_gate.json")
    ap.add_argument("--config", default="filters/nature_recovery/v4/config.yaml",
                    help="filter config.yaml; dims/weights/gatekeeper AND the MEDIUM "
                         "threshold default to its scoring block so the gate matches "
                         "what deploys")
    ap.add_argument("--threshold", type=float, default=None,
                    help="override the MEDIUM surfacing threshold (default: read from --config)")
    ap.add_argument("--gatekeeper-cap", type=float, default=None,
                    help="override the gatekeeper cap (sweep the demote-vs-exclude boundary); "
                         "auto-enables --recompute-model-wa so model+oracle use the same cap")
    ap.add_argument("--recompute-model-wa", action="store_true",
                    help="recompute each model's weighted_average from its per-dim scores using "
                         "the config spec (instead of the stored weighted_average)")
    args = ap.parse_args()

    spec = load_scoring_spec(args.config)
    if spec is not None and args.gatekeeper_cap is not None:
        spec = dict(spec)
        spec["gk_cap"] = args.gatekeeper_cap
    recompute = args.recompute_model_wa or (args.gatekeeper_cap is not None)

    medium = args.threshold if args.threshold is not None else load_medium_threshold(args.config)
    truth = load_labels(args.labels, spec=spec)
    report = {"threshold": medium,
              "gatekeeper_cap": (spec or _spec())["gk_cap"],
              "n_labeled": len(truth), "models": {}}
    for model_arg in args.model:
        name, path = model_arg.split("=", 1)
        model_spec = spec if recompute else None
        report["models"][name] = evaluate(truth, load_scores(path, spec=model_spec), medium)

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2))

    hdr = f"{'model':6} {'recall':>7} {'prec':>7} {'spec':>7} {'f1':>7} {'spearman':>9} {'mae':>6}"
    print(f"\nGround-truth gate vs held-out oracle labels "
          f"(threshold {medium}, gatekeeper_cap {report['gatekeeper_cap']}, n={len(truth)})")
    print(hdr)
    print("-" * len(hdr))
    for name, m in report["models"].items():
        print(f"{name:6} {m['recall']:7.3f} {m['precision']:7.3f} {m['specificity']:7.3f} "
              f"{m['f1']:7.3f} {m['spearman']:9.3f} {m['mae']:6.3f}")
    print(f"\nReport: {args.report}")


if __name__ == "__main__":
    main()
