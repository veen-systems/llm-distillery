"""Are the raw and calibrated arms different MODELS, or the same model on a different scale?

`ground_truth_gate.py` compares two score sets at a FIXED bar (4.5). That is the right
question for "what ships today" and the wrong question for "did calibration help": per-
dimension isotonic regression is monotone in each dimension, so it mostly relabels the
scale rather than reordering articles. A recall drop at a fixed bar is then a threshold
effect wearing a model effect's clothes.

This asks the scale-free version:

  * rank agreement between the arms (Spearman + share of discordant pairs)
  * recall at MATCHED POSITIVE COUNT -- flag the k highest-scoring rows in each arm, so
    both arms surface the same volume and only the ordering can differ
  * AUC and average precision

Reads the two gate-input files from `dump_student_scores.py` (one forward pass, so no #95
batch-composition term sits between the arms) and the labelled split.

    python docs/evidence/2026-09-04-v8-probe-calibration/compare_arms_as_rankers.py \
        --dump-dir <dir with scores_raw.jsonl / scores_calibrated.jsonl> \
        --labels datasets/training/human_thriving_v8/test.jsonl \
        --out docs/evidence/2026-09-04-v8-probe-calibration/arms_as_rankers.json
"""

# design-weights: NOT READ. Every statistic here -- Spearman, discordant-pair share,
# AUC, average precision, recall at matched flag count -- is an UNWEIGHTED sample
# quantity over the 660 design-weighted test rows (25.1x span; the weights live in
# datasets/scored/human_thriving_v8/corpus.jsonl, not in the split file). ⚠️ The
# comparison is PAIRED on identical rows, so a reweighting moves both arms together and
# is unlikely to reverse the ordering -- but that is an argument, not a measurement, and
# the absolute AUCs published from here are sample values. Weighted arm on the same rows:
# phase_c_outcome.py.

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

# human_thriving v8, from filters/human_thriving/v8/base_scorer.py. Hardcoded here on
# purpose: this file is a frozen evidence artifact and must keep reproducing the numbers
# published beside it even after the filter's constants change.
WEIGHTS = {
    "human_wellbeing_impact": 0.30,
    "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15,
    "evidence_level": 0.10,
    "benefit_distribution": 0.10,
    "change_durability": 0.15,
}
DIMS = list(WEIGHTS)
GK_DIM, GK_MIN, GK_CAP = "evidence_level", 3.0, 3.0
MEDIUM = 4.5


def weighted_avg(scores: dict) -> float:
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    if scores[GK_DIM] < GK_MIN and v > GK_CAP:
        v = GK_CAP
    return v


def load_scores(path: Path) -> dict:
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["id"]] = weighted_avg(r["scores"])
    return out


def load_truth(path: Path) -> dict:
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            scores = dict(zip(r.get("dimension_names", DIMS), r["labels"]))
            out[r["id"]] = 1 if weighted_avg(scores) >= MEDIUM else 0
    return out


def recall_at_k(scores: np.ndarray, y: np.ndarray, ks) -> dict:
    """Recall when the k highest-scoring rows are flagged.

    ⛔ REFUSES k >= n. `sel[order[:k]]` silently flags everything once k reaches n, so
    recall is identically 1.0 and the comparison becomes vacuous while still printing a
    number. That is llm-distillery#144's exact shape -- `recall_at_k` clamped with
    `min(k, n)` was identically 1.0 whenever n <= k, and it pinned checkpoint selection to
    epoch 1 for every small-val run. A guard, not a clamp: a clamp is what produced the
    defect.

    ⚠️ Ties are broken by index (`np.argsort` is not stable here and ids are sorted
    lexicographically), and the calibrated arm is the compressed, more tie-prone one, so a
    ±1-article difference at a given k is not shown to be tie-stable. Read the pattern
    across k, never a single cell.
    """
    n = len(scores)
    n_pos = int(y.sum())
    if n_pos == 0:
        raise ValueError("no positives -- recall is undefined")
    bad = [int(k) for k in ks if int(k) >= n]
    if bad:
        raise ValueError(
            f"k values {bad} are >= n ({n}); every row would be flagged and recall would "
            f"be identically 1.0. See llm-distillery#144."
        )
    order = np.argsort(-scores)
    out = {}
    for k in ks:
        sel = np.zeros(n, dtype=bool)
        sel[order[:k]] = True
        out[int(k)] = int((sel & (y == 1)).sum()) / n_pos
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=0,
                    help="seed for the discordant-pair sample (it is a sample, not a census)")
    args = ap.parse_args()

    raw = load_scores(args.dump_dir / "scores_raw.jsonl")
    cal = load_scores(args.dump_dir / "scores_calibrated.jsonl")
    truth = load_truth(args.labels)

    missing = sorted(set(raw) - set(truth))
    if missing:
        raise SystemExit(f"{len(missing)} scored ids absent from labels (e.g. {missing[:3]})")
    if set(raw) != set(cal):
        raise SystemExit("the two arms cover different id sets")

    ids = sorted(raw)
    y = np.array([truth[i] for i in ids])
    R = np.array([raw[i] for i in ids])
    C = np.array([cal[i] for i in ids])

    rng = np.random.default_rng(args.seed)
    idx = rng.integers(0, len(ids), (200_000, 2))
    keep = idx[:, 0] != idx[:, 1]
    a, b = idx[keep, 0], idx[keep, 1]
    discordant = float(((R[a] - R[b]) * (C[a] - C[b]) < 0).mean())

    ks = [17, 20, 26, 30, 35, 43, 50, 60]
    report = {
        "n": len(ids),
        "n_positives": int(y.sum()),
        "positive_rate": float(y.mean()),
        "medium_threshold": MEDIUM,
        "arm_rank_agreement": {
            "spearman_raw_vs_calibrated": float(spearmanr(R, C).statistic),
            # ⚠️ A LOWER BOUND: a tied pair (product == 0) counts as concordant, and the
            # calibrated arm is the more tie-prone one, so true discordance is >= this.
            "discordant_pair_share": discordant,
            "discordant_pair_share_is_lower_bound": True,
            "discordant_pairs_sampled": int(keep.sum()),
            "tied_pair_share": float(((R[a] - R[b]) * (C[a] - C[b]) == 0).mean()),
        },
        "auc": {"raw": float(roc_auc_score(y, R)), "calibrated": float(roc_auc_score(y, C))},
        "average_precision": {"raw": float(average_precision_score(y, R)),
                              "calibrated": float(average_precision_score(y, C))},
        "recall_at_matched_flag_count": {
            "raw": recall_at_k(R, y, ks),
            "calibrated": recall_at_k(C, y, ks),
        },
    }

    print(json.dumps(report, indent=2))
    print(f"\nn={report['n']}, {report['n_positives']} positives "
          f"({report['positive_rate']:.4f})")
    print(f"raw-vs-calibrated Spearman {report['arm_rank_agreement']['spearman_raw_vs_calibrated']:.6f}, "
          f"{discordant:.2%} of sampled pairs discordant")
    print(f"AUC raw {report['auc']['raw']:.4f} vs calibrated {report['auc']['calibrated']:.4f}")
    print(f"AP  raw {report['average_precision']['raw']:.4f} vs "
          f"calibrated {report['average_precision']['calibrated']:.4f}")
    print("\nrecall at matched flag count (same surfaced VOLUME, only ordering differs):")
    for k in ks:
        r = report["recall_at_matched_flag_count"]["raw"][k]
        c = report["recall_at_matched_flag_count"]["calibrated"][k]
        print(f"  k={k:3d}  raw {r:.3f}  calibrated {c:.3f}  "
              f"({int(round((c - r) * report['n_positives'])):+d} articles)")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
