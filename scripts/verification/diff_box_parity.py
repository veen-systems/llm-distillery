#!/usr/bin/env python3
"""Diff two box_parity.py prediction dumps.

Reports, in increasing order of what actually matters:

  1. how many rows are bit-identical, and max |Δ| per raw dimension
  2. the CALIBRATED weighted-score |Δ|, against the #95 |0.16| noise floor
  3. verdict flips at the op-point(s) — the only thing that changes a decision —
     plus recall/specificity recomputed per box against the oracle labels

Reading the output
------------------
A small mean |Δ| proves nothing on its own. What decides whether a box is usable
for a given question is the flip count AT THE THRESHOLD YOU CARE ABOUT. On
2026-08-09 uplifting v7 had 0 flips at 4.0 and 3 flips at 4.5 from the same pair
of dumps: gpu-server vs b650. A box is cleared at a threshold, never in general.

Raw logits come out bf16-quantised (~0.03 granularity at these magnitudes), so
per-row deltas are discrete: exactly zero, or a step. "Small but nonzero" is not
an available answer, and a median of 0.0000 does NOT mean the stacks agree.

Two ways to define the positive class, and they answer different questions:
  --truth-threshold fixed (default, = 4.0)  what "on-lens" means stays put while
      the student's bar sweeps. This is the ADR-023 question: does raising the
      bar keep out more junk, and at what recall cost?
  --truth-follows-threshold                 truth and prediction move together,
      so the positive count changes with the threshold (216 -> 193 on uplifting
      v7 between 4.0 and 4.5). Do not compare its recall across thresholds.

Matching is by EXACT article id — never index, never source prefix (there are
duplicate source prefixes in this corpus).

Usage
-----
    PYTHONPATH=. python scripts/verification/diff_box_parity.py \
        --a preds-gpuserver.jsonl --b preds-b650.jsonl \
        --labels datasets/training/uplifting_v7/test.jsonl \
        --calibration filters/uplifting/v7/calibration.json \
        --repo-root . --threshold 4.0 --alt-threshold 4.5
"""

import argparse
import json
import sys


def load_preds(path):
    meta = None
    rows = {}
    with open(path) as f:
        for line in f:
            o = json.loads(line)
            if "_meta" in o:
                meta = o
                continue
            rows[o["id"]] = o
    return meta, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="dump A (put the SERVING box here)")
    ap.add_argument("--b", required=True)
    ap.add_argument("--labels", required=True, help="split with id + labels + dimension_names")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--threshold", type=float, default=4.0)
    ap.add_argument("--alt-threshold", type=float, default=4.5)
    ap.add_argument("--truth-threshold", type=float, default=None,
                    help="fixed oracle cut defining on-lens (default: --threshold)")
    ap.add_argument("--truth-follows-threshold", action="store_true",
                    help="move the truth cut with the student bar (changes the positive set)")
    ap.add_argument("--noise-floor", type=float, default=0.16)
    args = ap.parse_args()

    sys.path.insert(0, args.repo_root)
    import numpy as np
    from filters.common.score_calibration import load_calibration, apply_calibration

    cal = load_calibration(args.calibration)
    meta_a, A = load_preds(args.a)
    meta_b, B = load_preds(args.b)
    dims = meta_a["dims"]
    weights = meta_a["weights"]
    assert dims == meta_b["dims"], "dimension order differs — refusing to compare"

    labels = {}
    with open(args.labels) as f:
        for line in f:
            o = json.loads(line)
            labels[o["id"]] = dict(zip(o["dimension_names"], o["labels"]))

    shared = sorted(set(A) & set(B))
    for tag, m in (("A", meta_a), ("B", meta_b)):
        e = m["_meta"]
        print(f"box {tag}: {e['host']}  py {e['python']}  torch {e['torch']}  "
              f"transformers {e['transformers']}  peft {e['peft']}  device={m.get('device')}")
    print(f"matched by exact id: {len(shared)} of {len(A)} / {len(B)}")
    if len(shared) != len(A) or len(shared) != len(B):
        print("!! id sets differ — investigate before reading anything below")

    def calibrated_wavg(row):
        # np.ndarray, matching what filter_base_scorer passes: apply_calibration
        # calls .copy() and assigns np.interp results back into it.
        raw = np.asarray([row["raw"][d] for d in dims], dtype=float)
        cs = apply_calibration(raw, cal, dims) if cal else raw
        return sum(max(0.0, min(10.0, float(v))) * float(weights.get(d, 0))
                   for v, d in zip(cs, dims))

    per_dim_max = {d: 0.0 for d in dims}
    bitwise_identical = 0
    detail = []
    for aid in shared:
        ra, rb = A[aid], B[aid]
        for d in dims:
            per_dim_max[d] = max(per_dim_max[d], abs(ra["raw"][d] - rb["raw"][d]))
        if all(ra["raw"][d] == rb["raw"][d] for d in dims):
            bitwise_identical += 1
        detail.append((aid, calibrated_wavg(ra), calibrated_wavg(rb)))

    deltas = np.array([abs(ca - cb) for _, ca, cb in detail])
    signed = np.array([cb - ca for _, ca, cb in detail])

    print(f"\nbit-identical on every dimension: {bitwise_identical}/{len(shared)} "
          f"({100*bitwise_identical/len(shared):.1f}%)")
    print("\nmax |delta| per raw dimension:")
    for d in dims:
        print(f"  {d:28s} {per_dim_max[d]:.6f}")
    print(f"\ncalibrated wavg |delta|: p50={np.percentile(deltas,50):.4f} "
          f"p90={np.percentile(deltas,90):.4f} p99={np.percentile(deltas,99):.4f} "
          f"max={deltas.max():.4f}")
    over = [(aid, ca, cb) for (aid, ca, cb), dl in zip(detail, deltas) if dl > args.noise_floor]
    print(f"rows exceeding the #95 floor ({args.noise_floor}): {len(over)} "
          f"({100*len(over)/len(shared):.2f}%)")
    for aid, ca, cb in over[:10]:
        print(f"   {aid:45s} A={ca:.4f} B={cb:.4f}")
    print(f"signed mean (B - A): {signed.mean():+.5f}  "
          f"-> {'systematic shift' if abs(signed.mean()) > 0.01 else 'noise, not a shift'}")

    for thr in (args.threshold, args.alt_threshold):
        truth_cut = thr if args.truth_follows_threshold else (
            args.truth_threshold if args.truth_threshold is not None else args.threshold)
        flips = [(aid, ca, cb) for aid, ca, cb in detail if (ca >= thr) != (cb >= thr)]
        print(f"\n--- student op-point {thr}  (on-lens := oracle >= {truth_cut}) ---")
        print(f"verdict flips between boxes: {len(flips)} of {len(shared)} "
              f"({100*len(flips)/len(shared):.2f}%)")
        for aid, ca, cb in flips[:15]:
            print(f"  {aid:45s} A={ca:.4f} B={cb:.4f}")

        for name, meta, idx in (("A", meta_a, 1), ("B", meta_b, 2)):
            tp = fn = fp = tn = 0
            for row in detail:
                aid, s = row[0], row[idx]
                lab = labels.get(aid)
                if lab is None:
                    continue
                truth = sum(lab[d] * float(weights.get(d, 0)) for d in dims) >= truth_cut
                pred = s >= thr
                if truth and pred: tp += 1
                elif truth: fn += 1
                elif pred: fp += 1
                else: tn += 1
            rec = tp / (tp + fn) if tp + fn else float("nan")
            spec = tn / (tn + fp) if tn + fp else float("nan")
            prec = tp / (tp + fp) if tp + fp else float("nan")
            print(f"  {name} ({meta['_meta']['host']:22s}) tp={tp:3d} fn={fn:3d} fp={fp:3d} "
                  f"tn={tn:3d}  recall={rec:.4f} spec={spec:.4f} prec={prec:.4f} FPR={1-spec:.4f}")


if __name__ == "__main__":
    main()
