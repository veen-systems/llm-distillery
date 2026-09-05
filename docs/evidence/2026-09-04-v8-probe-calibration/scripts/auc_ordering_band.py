"""The band under GATING_DECISION.md's one quantified ordering.

⛔ WHY THIS EXISTS. `GATING_DECISION.md` published *"Regression e5-small ranks far
better than the shipped probe (AUC 0.9035 vs 0.8710)"* with no band. EXP-024 had
already shown what that shape costs: *"AUC would have picked the wrong arm"* was a
coin flip (Δ = +0.0014, P = 0.523). Found 2026-09-05 by
`scripts/verification/check_claim_shapes.py --check ordering-needs-band`, which is
the check that exists for exactly this.

CONTROL FIRST: both published AUCs must reproduce off the dumps before any
interval is believed. They do, to four decimals.

Paired bootstrap over the SAME rows, resampling positives and negatives
separately (AUC's precision is governed by the smaller class; 35 positives).

    .venv/bin/python docs/evidence/2026-09-04-v8-probe-calibration/scripts/auc_ordering_band.py \
        --dump-dir /tmp/dump  --labels datasets/training/human_thriving_v8/test.jsonl

⛔ `.venv/bin/python`, not `python3` — the system interpreter has no sklearn, and
this repo has previously mis-diagnosed that exact failure as "the environment".

"""

# design-weights: NOT READ. This is a paired comparison of two arms on identical rows, so
# the design weights cancel in the ORDERING even though they would move each arm's
# absolute AUC. ⛔ That is an argument, not a measurement: no weighted arm has been run,
# and the CI printed below is the unweighted one.
# ⚠️ THIS COMMENT SAT INSIDE THE DOCSTRING ABOVE UNTIL 2026-09-05 and the check did not
# see it -- correctly: `_declaration` reads COMMENT tokens, because a regex over the file
# text exempted a declaration written inside a string literal. A declaration that is not
# a comment is not a declaration.

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
OP = 4.5
# The values GATING_DECISION.md publishes. The run aborts unless it reproduces
# them: an interval around numbers that are not the document's numbers is worse
# than no interval.
PUBLISHED = {"regression e5-small": 0.9035, "shipped recall e5-small": 0.8710}
TOL = 5e-4


def weighted_avg(scores, gate=False):
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    return GK_CAP if (gate and scores[GK_DIM] < GK_MIN and v > GK_CAP) else v


def load(path):
    return {r["id"]: weighted_avg(r["scores"])
            for r in (json.loads(l) for l in open(path, encoding="utf-8") if l.strip())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--resamples", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    truth = {}
    for line in open(args.labels, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            truth[r["id"]] = weighted_avg(
                dict(zip(r.get("dimension_names", DIMS), r["labels"])))
    arms = {"regression e5-small": load(args.dump_dir / "probe_scores_reg_small.jsonl"),
            "shipped recall e5-small": load(args.dump_dir / "probe_scores.jsonl")}
    ids = sorted(set(truth) & set(arms["regression e5-small"])
                 & set(arms["shipped recall e5-small"]))
    if len(ids) != 660:
        raise SystemExit(f"expected the 660-row test split, got {len(ids)} — "
                         f"refusing to publish an interval over the wrong population")
    y = np.array([truth[i] >= OP for i in ids])
    a = np.array([arms["regression e5-small"][i] for i in ids])
    b = np.array([arms["shipped recall e5-small"][i] for i in ids])

    for name, vec in (("regression e5-small", a), ("shipped recall e5-small", b)):
        got = float(roc_auc_score(y, vec))
        if abs(got - PUBLISHED[name]) > TOL:
            raise SystemExit(f"CONTROL FAILED: {name} AUC {got:.4f} against the "
                             f"published {PUBLISHED[name]:.4f} — the dumps are not "
                             f"the ones GATING_DECISION.md was written from")
        print(f"control  {name:26s} AUC {got:.4f}  == published {PUBLISHED[name]}")

    delta = float(roc_auc_score(y, a) - roc_auc_score(y, b))
    rng = np.random.default_rng(args.seed)
    pos, neg = np.where(y)[0], np.where(~y)[0]
    reps = []
    for _ in range(args.resamples):
        idx = np.concatenate([rng.choice(pos, len(pos), True),
                              rng.choice(neg, len(neg), True)])
        yy = y[idx]
        if yy.all() or not yy.any():
            continue
        reps.append(roc_auc_score(yy, a[idx]) - roc_auc_score(yy, b[idx]))
    reps = np.array(reps)
    lo, hi = np.percentile(reps, [2.5, 97.5])
    p = 2 * min((reps <= 0).mean(), (reps >= 0).mean())
    print(f"\nn={len(ids)}  positives={int(y.sum())}  replicates={len(reps)}")
    print(f"delta AUC (regression - shipped) = {delta:+.4f}")
    print(f"95% CI [{lo:+.4f}, {hi:+.4f}]   P = {p:.3f}")
    print("CI includes zero -> NOT DISTINGUISHABLE" if lo <= 0 <= hi
          else "CI excludes zero -> distinguishable")


if __name__ == "__main__":
    main()
