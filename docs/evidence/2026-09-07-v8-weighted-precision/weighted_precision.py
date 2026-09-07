#!/usr/bin/env python3
"""human_thriving v8 (EXP-027, epoch 5) — precision under the PRODUCTION MIX.

WHY THIS EXISTS
    `ground_truth_gate.json` reports precision 0.550 on the 660-row test split.
    That split is a design-weighted draw (span 25.1x): its unweighted positive
    rate is 5.3030%, the design-weighted rate is 3.1638%. Precision is
    base-rate dependent, so 0.550 is NOT the number a reader experiences.
    Specificity and recall are conditional on the true class and move much less.

    `phase_c_outcome.py` (2026-09-04) already prints a Horvitz-Thompson arm, but
    (a) it predates the retrain and describes the SUPERSEDED epoch-4 checkpoint,
    and (b) it reports junk-removed / good-kept / recall / specificity and
    NEVER precision — the one quantity that is base-rate dependent and therefore
    the one the weighting actually changes.

METHOD
    Truth, predictions, the scoring spec, the gatekeeper cap and the op-point all
    come from the SHIPPED gate module (scripts/gate/ground_truth_gate.py) — not
    reimplemented here — so the only thing this script adds is the weighting.
    w = 1 / inclusion_probability, read from the corpus manifest.

CONTROL (the reason to believe the weighted number)
    The unweighted arm computed here must reproduce the committed
    ground_truth_gate.json cell-for-cell. If it does not, the join or the spec is
    wrong and the weighted number is meaningless — the script exits non-zero.

PREDICTED RANGE, recorded BEFORE running (working rule: predict the range first)
    Weighted positive rate ~3.16% (known from the manifest, not a prediction).
    Weighted precision 0.40-0.60. Two effects fight: the lower base rate pushes
    precision DOWN (naive arithmetic at unchanged recall/spec gives 0.416), while
    on the epoch-4 sweep the weighting RAISED specificity at 4.5 (0.9856 ->
    0.9932) and lowered recall (0.486 -> 0.429), which pushes it back UP (~0.57).
    A result outside 0.40-0.60 means check the instrument, not the model.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from scripts.gate.ground_truth_gate import (  # noqa: E402
    load_labels, load_medium_threshold, load_scores, load_scoring_spec, evaluate,
)

NOISE_FLOOR = 0.16


def load_weights(path):
    """w = 1/p from the corpus manifest. Refuses anything that is not a design
    weight: a missing, zero, negative or >1 inclusion probability makes 1/p
    meaningless and a partially-weighted table is worse than an unweighted one."""
    w = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        p = r.get("inclusion_probability")
        if p is None:
            raise SystemExit(f"row {r.get('id')!r} has no inclusion_probability; "
                             "refusing to publish a partially-weighted table")
        p = float(p)
        if not (0.0 < p <= 1.0):
            raise SystemExit(f"row {r.get('id')!r} has inclusion_probability {p}: "
                             "1/p is not a design weight")
        w[r["id"]] = 1.0 / p
    return w


def weighted_cells(truth, pred, weights, cut, medium, noise_floor=NOISE_FLOOR):
    """Horvitz-Thompson confusion cells + the #95 indeterminate cells, weighted."""
    ids = [i for i in pred if i in truth]
    missing = [i for i in ids if i not in weights]
    if missing:
        raise SystemExit(f"{len(missing)} joined rows carry no design weight "
                         f"(e.g. {missing[:3]}); refusing a partially-weighted table")
    cells = {"tp": 0.0, "fn": 0.0, "fp": 0.0, "tn": 0.0}
    ind = {"tp": 0.0, "fn": 0.0, "fp": 0.0, "tn": 0.0}
    for i in ids:
        w = weights[i]
        pos_truth, pos_pred = truth[i] >= cut, pred[i] >= medium
        cell = "tp" if (pos_truth and pos_pred) else \
               "fn" if (pos_truth and not pos_pred) else \
               "fp" if pos_pred else "tn"
        cells[cell] += w
        if abs(pred[i] - medium) < noise_floor:
            ind[cell] += w
    return cells, ind, len(ids)


def prf(tp, fn, fp, tn):
    pos, neg = tp + fn, tn + fp
    recall = tp / pos if pos else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    spec = tn / neg if neg else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"recall": recall, "precision": precision, "specificity": spec, "f1": f1,
            "positive_rate": pos / (pos + neg) if (pos + neg) else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="datasets/training/human_thriving_v8/test.jsonl")
    ap.add_argument("--config", default="filters/human_thriving/v8/config.yaml")
    ap.add_argument("--corpus", default="datasets/scored/human_thriving_v8/corpus.jsonl")
    ap.add_argument("--gate-json", default="filters/human_thriving/v8/ground_truth_gate.json",
                    help="the committed gate report; the unweighted arm must reproduce it")
    ap.add_argument("--model", action="append", required=True, metavar="NAME=PATH")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    spec = load_scoring_spec(args.config)
    if spec is None:
        raise SystemExit(f"{args.config} has no scoring.dimensions block; refusing to "
                         "fall back to another filter's constants")
    medium = load_medium_threshold(args.config)
    truth = load_labels(args.labels, spec=spec)
    weights = load_weights(args.corpus)
    committed = json.loads(Path(args.gate_json).read_text(encoding="utf-8"))

    print(f"op-point {medium} (from {args.config}); truth cut {medium}; "
          f"noise floor {NOISE_FLOOR} (#95)")
    print(f"weights: 1/inclusion_probability over {len(weights)} corpus rows, "
          f"span {max(weights.values()) / min(weights.values()):.1f}x\n")

    report = {"op_point": medium, "noise_floor": NOISE_FLOOR,
              "weight_source": args.corpus, "models": {}}
    failures = []

    for m in args.model:
        name, path = m.split("=", 1)
        pred = load_scores(path, spec=spec)
        unw = evaluate(truth, pred, medium=medium, noise_floor=NOISE_FLOOR,
                       truth_threshold=medium)

        # --- CONTROL: reproduce the committed gate cell-for-cell -------------
        ref = committed["models"].get(name)
        if ref is None:
            failures.append(f"{name}: no such arm in {args.gate_json}")
        else:
            for k in ("n", "positives", "tp", "fn", "fp", "tn"):
                if unw[k] != ref[k]:
                    failures.append(f"{name}.{k}: recomputed {unw[k]} != committed {ref[k]}")
            for k in ("recall", "precision", "specificity"):
                if abs(unw[k] - ref[k]) > 1e-9:
                    failures.append(f"{name}.{k}: recomputed {unw[k]:.6f} != "
                                    f"committed {ref[k]:.6f}")

        cells, ind, n = weighted_cells(truth, pred, weights, medium, medium)
        wtd = prf(**cells)
        # #95 band, weighted: worst case every borderline positive falls out and
        # every borderline negative falls in; best case the mirror image.
        lo = prf(cells["tp"] - ind["tp"], cells["fn"] + ind["tp"],
                 cells["fp"] + ind["tn"], cells["tn"] - ind["tn"])
        hi = prf(cells["tp"] + ind["fn"], cells["fn"] - ind["fn"],
                 cells["fp"] - ind["fp"], cells["tn"] + ind["fp"])

        report["models"][name] = {
            "n_joined": n,
            "unweighted": {k: unw[k] for k in
                           ("n", "positives", "tp", "fn", "fp", "tn", "recall",
                            "precision", "specificity", "f1", "precision_band",
                            "specificity_band")},
            "weighted_cells": cells,
            "weighted": wtd,
            "weighted_band": {"precision": [lo["precision"], hi["precision"]],
                              "recall": [lo["recall"], hi["recall"]],
                              "specificity": [lo["specificity"], hi["specificity"]]},
            "scores_path": path,
        }

        print(f"=== {name} ===  joined {n} rows")
        print(f"  {'':22} {'unweighted':>12} {'design-weighted':>16}")
        print(f"  {'positive rate':22} {unw['positives'] / unw['n']:12.4%} "
              f"{wtd['positive_rate']:16.4%}")
        print(f"  {'PRECISION':22} {unw['precision']:12.4f} {wtd['precision']:16.4f}"
              f"   band [{lo['precision']:.4f}, {hi['precision']:.4f}]")
        print(f"  {'specificity':22} {unw['specificity']:12.4f} {wtd['specificity']:16.4f}"
              f"   band [{lo['specificity']:.4f}, {hi['specificity']:.4f}]")
        print(f"  {'recall':22} {unw['recall']:12.4f} {wtd['recall']:16.4f}"
              f"   band [{lo['recall']:.4f}, {hi['recall']:.4f}]")
        print(f"  {'f1':22} {unw['f1']:12.4f} {wtd['f1']:16.4f}")
        print(f"  cells  unweighted tp {unw['tp']} fp {unw['fp']} fn {unw['fn']} tn {unw['tn']}")
        print(f"         weighted   tp {cells['tp']:.1f} fp {cells['fp']:.1f} "
              f"fn {cells['fn']:.1f} tn {cells['tn']:.1f}\n")

    if failures:
        print("CONTROL FAILED — the unweighted arm does not reproduce the committed gate:")
        for f in failures:
            print("  " + f)
        print("The weighted numbers above are NOT trustworthy: same join, same spec, "
              "same op-point is the only thing that makes them comparable.")
        return 1
    print("CONTROL PASSED: the unweighted arm reproduces "
          f"{args.gate_json} cell-for-cell for every model.")

    if args.report:
        report["control"] = {"reproduces": args.gate_json, "passed": True}
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
