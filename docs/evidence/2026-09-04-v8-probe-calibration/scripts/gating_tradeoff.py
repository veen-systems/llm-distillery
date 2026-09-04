"""What does harder Stage-1 gating actually cost, and what does it buy?

Two questions the adopted hold-near-pass-through ruling (2026-08-28) leaves open once
someone asks "89% pass-through does not sound like a needle filter":

  1. **How hard CAN the screen go at a given FN budget?** Selecting the threshold on VAL
     and evaluating on TEST — never on the same split, because a threshold chosen where it
     is evaluated is not a measurement.
  2. **At what routing rate does the two-stage design stop paying for itself?** A closed
     form, since the cost is linear in the routing rate.

⛔ WHAT MAKES (1) WORTH RUNNING RATHER THAN REASONING ABOUT. A better-ranking probe does
NOT automatically buy safer screening: measured 2026-09-04, the regression-objective
e5-small ranks far better than the shipped recall probe (AUC 0.9035 vs 0.8710) and lands on
essentially the same screen (55.3% routing / 1 FN vs 56.5% / 1 FN). Ranking quality and
screen safety are different properties.

⛔ AND THE OTHER DIRECTION IS WORSE. Regression e5-LARGE screens hardest of all (30.3%) and
drops 6 of 35 positives — 17% of the needles. That is ADR-011's floor-collapse warning
happening exactly as written, in the SCREEN role. The same probe is a fine SCORER. Do not
carry a verdict from one role to the other.

⚠️ A threshold giving 0 FN on val gave 1-6 FN on test for EVERY probe tested. Threshold
selection does not generalise reliably at 31/35 positives; treat any tightening as
provisional until there are more positives (llm-distillery#141).

    python docs/evidence/2026-09-04-v8-probe-calibration/scripts/gating_tradeoff.py
"""

import argparse
import json
from pathlib import Path

import numpy as np

WEIGHTS = {
    "human_wellbeing_impact": 0.30, "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15, "evidence_level": 0.10,
    "benefit_distribution": 0.10, "change_durability": 0.15,
}
DIMS = list(WEIGHTS)
GK_DIM, GK_MIN, GK_CAP = "evidence_level", 3.0, 3.0
MEDIUM = 4.5

# ms/article, measured on b650-gpu over the 660-row test split, model load excluded.
# ⚠️ b650 is not gpu-server; ratios should travel, absolute numbers may not.
MS = {"e5-small GPU": 3.74, "e5-large GPU": 26.79, "student GPU": 43.70}


def wa(scores, gatekeeper=True):
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    if gatekeeper and scores[GK_DIM] < GK_MIN and v > GK_CAP:
        return GK_CAP
    return v


def probe_scores(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        # a recall dump carries probe_wa; a regression dump carries the 6 dims
        out[r["id"]] = r["probe_wa"] if "probe_wa" in r else wa(r["scores"], gatekeeper=False)
    return out


def truth(path):
    y = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        y[r["id"]] = 1 if wa(dict(zip(r.get("dimension_names", DIMS), r["labels"]))) >= MEDIUM else 0
    return y


def select_on_val(val_scores, val_y, budget):
    """train_probe.py's own rule: the HIGHEST threshold whose val FN-rate <= budget.
    FN-rate is monotone non-decreasing in the threshold, so the scan can stop early."""
    pos = [i for i in val_scores if val_y[i] == 1]
    if not pos:
        raise SystemExit("no positives in val — a threshold chosen here would mean nothing")
    best = 0.0
    for t in np.arange(0, 8.001, 0.025):
        if sum(1 for i in pos if val_scores[i] < t) / len(pos) <= budget:
            best = float(t)
        else:
            break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path,
                    default=Path("datasets/training/human_thriving_v8"))
    ap.add_argument("--corpus", type=Path,
                    default=Path("datasets/scored/human_thriving_v8/corpus.jsonl"))
    ap.add_argument("--budgets", type=float, nargs="*", default=[0.0, 0.02])
    args = ap.parse_args()

    corpus = {json.loads(l)["id"]: json.loads(l)
              for l in open(args.corpus, encoding="utf-8") if l.strip()}
    yv = truth(args.data_dir / "val.jsonl")
    yt = truth(args.data_dir / "test.jsonl")

    arms = {
        "recall  e5-small (SHIPPED)": ("val_rec_small.jsonl", "probe_scores.jsonl"),
        "recall  e5-large":           ("val_rec_large.jsonl", "probe_scores_e5large.jsonl"),
        "regress e5-small":           ("val_reg_small.jsonl", "probe_scores_reg_small.jsonl"),
        "regress e5-large":           ("val_reg_large.jsonl", "probe_scores_reg_large.jsonl"),
    }

    def weighted_routing(ts, thr):
        num = den = 0.0
        for i, s in ts.items():
            w = 1.0 / corpus[i]["inclusion_probability"]
            den += w
            if s >= thr:
                num += w
        return num / den

    for budget in args.budgets:
        print(f"\nThreshold selected on VAL at an FN budget of {budget:.0%}, "
              f"evaluated on TEST")
        print(f"  {'probe':<26} {'thr':>6} {'TEST routing':>13} {'TEST FN':>9} "
              f"{'wtd routing':>12}")
        for name, (vf, tf) in arms.items():
            vp, tp = probe_scores(args.dump_dir / vf), probe_scores(args.dump_dir / tf)
            thr = select_on_val(vp, yv, budget)
            pos = [i for i in tp if yt[i] == 1]
            fn = sum(1 for i in pos if tp[i] < thr)
            route = sum(1 for i in tp if tp[i] >= thr) / len(tp)
            print(f"  {name:<26} {thr:>6.3f} {route:>12.1%} {fn:>4}/{len(pos):<4} "
                  f"{weighted_routing(tp, thr):>11.1%}")
        print("  ⚠️ 0 FN on val became 1-6 FN on test for every probe — threshold "
              "selection\n     does not generalise at this many positives (#141).")

    # --- the closed form: when does two-stage stop paying? -----------------------------
    p, s = MS["e5-small GPU"], MS["student GPU"]
    big = MS["e5-large GPU"]
    print(f"\nCOST, GPU ms/article.  two-stage = {p} + r*{s};  e5-large alone = {big}")
    print(f"  {'routing r':>10} {'two-stage':>11} {'winner':>26}")
    for r in (1.00, 0.89, 0.75, 0.61, 0.52, 0.40, 0.25):
        ts_cost = p + r * s
        w = (f"e5-large, {ts_cost/big:.2f}x" if ts_cost > big
             else f"two-stage, {big/ts_cost:.2f}x")
        print(f"  {r:>10.0%} {ts_cost:>9.2f}ms {w:>26}")
    print(f"  break-even r* = ({big} - {p}) / {s} = {(big-p)/s:.3f}")
    print("  ⚠️ The ADOPTED threshold routes 89%, well above break-even — which is what "
          "makes\n     e5-large-alone competitive at all. Tighten the screen and that "
          "stops being true.")

    print("\n⛔ THE COST OF TIGHTENING THAT IS NOT COMPUTE: a screened-out row does not "
          "just\n   skip the student — the probe's numbers become its PUBLISHED scores and "
          "tier\n   (hybrid_scorer.py, the Stage-1-LOW branch). At 89% routing that is 11% "
          "of the\n   corpus; at 52% it would be 48%. The shipped recall probe's scores are "
          "inflated\n   +1.98 on the weighted average and 3.4x worse per-dimension than the "
          "student's, so\n   tightening the screen also multiplies how much of the corpus "
          "carries them.")


if __name__ == "__main__":
    main()
