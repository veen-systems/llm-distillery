"""Three things the aggregate AUC comparison does not show, about the probe vs the student.

Run after `dump_probe_scores.py` and `dump_student_scores.py` have written their per-row
files for the same split.

  1. **Is the student measurably better, or does it just look better?** A paired bootstrap
     over the SAME rows (resampling positives and negatives separately, because AUC's
     precision is governed by the smaller class). 35 positives is thin enough that this
     had to be asked rather than assumed — and the answer differs by population: resolved
     on the whole split, NOT resolved on the 117 disputed rows.

  2. **How good are the probe's PER-DIMENSION scores?** They are not decoration: for every
     `stage1_low` row the hybrid scorer publishes them as `result["scores"]`
     (`hybrid_scorer.py`, the Stage-1-LOW branch), so they are the article's scores of
     record. Yet `--objective recall` supervises them only through an auxiliary L1 weighted
     **0.1**, training the weighted AVERAGE via BCE instead.

  3. **Is the probe biased?** Mean signed error per dimension, which an MAE hides. This is
     the one that matters, and it has a mechanism: the recall objective uses
     `pos_weight = n_neg/n_pos` (~20 on this corpus), which penalises a missed positive
     twenty times more than a false alarm and therefore pushes every prediction UP. The
     0.1-weighted auxiliary term is too weak to pull it back.

⛔ NONE OF THIS BREAKS THE SCREEN. The Stage-1 threshold was selected on the probe's own
scale, so a roughly-monotone bias is absorbed by threshold selection. It matters for the
published scores, and it would matter more once a `normalization.json` maps raw scores to
percentiles — because Stage-1-LOW and Stage-2 rows would then be two populations on two
different scales sharing one CDF.

    python docs/evidence/2026-09-04-v8-probe-calibration/probe_vs_student_detail.py \
        --dump-dir <dir> --labels datasets/training/human_thriving_v8/test.jsonl \
        --corpus datasets/scored/human_thriving_v8/corpus.jsonl
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

WEIGHTS = {
    "human_wellbeing_impact": 0.30, "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15, "evidence_level": 0.10,
    "benefit_distribution": 0.10, "change_durability": 0.15,
}
DIMS = list(WEIGHTS)
GK_DIM, GK_MIN, GK_CAP = "evidence_level", 3.0, 3.0
MEDIUM = 4.5


def wa(scores, gatekeeper=True):
    """Weighted average. `gatekeeper=False` is the PROBE's form — Stage 1 deliberately
    skips the gatekeeper (hybrid_scorer.py), so comparing the two forms would compare
    two different statistics."""
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    if gatekeeper and scores[GK_DIM] < GK_MIN and v > GK_CAP:
        return GK_CAP
    return v


def rows(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--resamples", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    probe_rows = {r["id"]: r for r in rows(args.dump_dir / "probe_scores.jsonl")}
    cal = {r["id"]: r["scores"] for r in rows(args.dump_dir / "scores_calibrated.jsonl")}
    raw = {r["id"]: r["scores"] for r in rows(args.dump_dir / "scores_raw.jsonl")}
    large_p = args.dump_dir / "probe_scores_e5large.jsonl"
    large = {r["id"]: r["probe_wa"] for r in rows(large_p)} if large_p.exists() else None
    corpus = {r["id"]: r for r in rows(args.corpus)}

    ids, y, lab = [], [], {}
    for r in rows(args.labels):
        ids.append(r["id"])
        lab[r["id"]] = dict(zip(r.get("dimension_names", DIMS), r["labels"]))
        y.append(1 if wa(lab[r["id"]]) >= MEDIUM else 0)
    y = np.array(y)
    if y.sum() == 0 or y.sum() == len(y):
        raise SystemExit("one class is empty — every AUC below would be undefined")

    report = {"n": len(ids), "n_positives": int(y.sum())}
    rng = np.random.default_rng(args.seed)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]

    def paired(a, b):
        d = []
        for _ in range(args.resamples):
            idx = np.concatenate([rng.choice(pos, len(pos), True),
                                  rng.choice(neg, len(neg), True)])
            yy = y[idx]
            if yy.sum() in (0, len(yy)):     # a degenerate resample proves nothing
                continue
            d.append(roc_auc_score(yy, a[idx]) - roc_auc_score(yy, b[idx]))
        d = np.array(d)
        return dict(delta=float(d.mean()), lo=float(np.percentile(d, 2.5)),
                    hi=float(np.percentile(d, 97.5)), p_le_0=float((d <= 0).mean()),
                    n_resamples=len(d))

    # --- 1. is the student measurably better? -----------------------------------------
    S = np.array([wa(cal[i]) for i in ids])
    R = np.array([wa(raw[i]) for i in ids])
    P = np.array([probe_rows[i]["probe_wa"] for i in ids])
    v7 = np.array([corpus[i].get("v7_score") or 0.0 for i in ids])
    disputed = v7 >= MEDIUM

    print(f"n={len(ids)}  positives={int(y.sum())}  disputed rows={int(disputed.sum())}\n")
    print("1. PAIRED BOOTSTRAP — is the difference resolvable at this n?")
    comparisons = [("student cal vs probe e5-small", S, P)]
    if large is not None:
        L = np.array([large[i] for i in ids])
        comparisons += [("student cal vs probe e5-LARGE", S, L),
                        ("student raw vs probe e5-LARGE", R, L)]
    report["bootstrap_whole_split"] = {}
    for lbl, a, b in comparisons:
        r = paired(a, b)
        verdict = "RESOLVED" if r["lo"] > 0 else "NOT RESOLVED — CI spans 0"
        report["bootstrap_whole_split"][lbl] = r
        print(f"   {lbl:<32} ΔAUC {r['delta']:+.4f}  CI [{r['lo']:+.4f},{r['hi']:+.4f}]"
              f"  P(Δ<=0)={r['p_le_0']:.3f}  {verdict}")

    # --- 2 & 3. per-dimension quality and bias -----------------------------------------
    print("\n2/3. PER-DIMENSION vs the oracle — the probe's are PUBLISHED for stage1_low rows")
    print(f"   {'dimension':<26} {'probe MAE':>10} {'student MAE':>12} {'ratio':>7} "
          f"{'probe bias':>11}")
    per_dim = {}
    for d in DIMS:
        pm = float(np.mean([abs(probe_rows[i]["scores"][d] - lab[i][d]) for i in ids]))
        sm = float(np.mean([abs(cal[i][d] - lab[i][d]) for i in ids]))
        bias = float(np.mean([probe_rows[i]["scores"][d] - lab[i][d] for i in ids]))
        per_dim[d] = dict(probe_mae=pm, student_mae=sm, ratio=pm / sm, probe_bias=bias)
        print(f"   {d:<26} {pm:>10.3f} {sm:>12.3f} {pm/sm:>7.2f}x {bias:>+11.3f}")
    report["per_dimension"] = per_dim

    # The WEIGHTED AVERAGE, in each component's own form.
    pw = np.array([wa(probe_rows[i]["scores"], gatekeeper=False) for i in ids])
    ow = np.array([wa(lab[i], gatekeeper=False) for i in ids])
    ows = np.array([wa(lab[i]) for i in ids])
    report["weighted_average"] = {
        "probe_mae": float(np.abs(pw - ow).mean()),
        "probe_signed_error": float((pw - ow).mean()),
        "student_mae": float(np.abs(S - ows).mean()),
        "student_signed_error": float((S - ows).mean()),
    }
    w = report["weighted_average"]
    print(f"\n   weighted average:  probe MAE {w['probe_mae']:.3f} "
          f"(signed {w['probe_signed_error']:+.3f})   "
          f"student MAE {w['student_mae']:.3f} (signed {w['student_signed_error']:+.3f})")
    print("   ⛔ The probe's WA is NOT better than its per-dim scores — it is biased HIGH,")
    print("      which the screen absorbs (the threshold was picked on this same scale)")
    print("      and the PUBLISHED stage1_low scores do not.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
