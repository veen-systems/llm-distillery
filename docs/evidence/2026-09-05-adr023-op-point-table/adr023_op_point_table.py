"""ADR-023 op-point table: recall + SPECIFICITY at matched surfacing volume, per arm.

WHY THIS EXISTS. Every probe-vs-student comparison this project had made (EXP-018,
EXP-019, EXP-020) ranked arms on AUC or average precision. ADR-023 says rank on
SPECIFICITY AT THE OPERATING POINT, because a false positive reaches a reader and a
false negative refills the slot. Nobody had computed that. This does, on the 660-row
human_thriving v8 test split, from per-row dumps that already exist -- no GPU, no oracle.

THREE THINGS IT SEPARATES THAT NO PRIOR ARTIFACT DID

1. MATCHED FLAG COUNT. At a fixed surfaced volume k, FP = k - TP identically, so a lost
   true positive IS a gained false positive, one for one. This removes the scale
   difference between arms (the recall probes are inflated ~+2 on the weighted average),
   which a fixed 4.5 bar cannot.

2. THE GATEKEEPER. `base_scorer.py` applies `evidence_level < 3.0 -> cap the weighted
   average at 3.0`. `filters/common/embedding_stage.py:243 _compute_weighted_avg` does
   NOT. A probe-only architecture therefore drops that FP-control mechanism by accident.
   Probe arms are reported BOTH ways so the gate's own contribution is separable.

3. THE CASCADES, END TO END. In a two-stage arch a screened-out row publishes the GATE's
   score, not stage 2's. Composing the arms by hand is the only way that mixing appears
   in the number instead of being argued around.

INPUTS ARE NOT IN GIT. Both are gitignored (`.gitignore:76 datasets/*`, and #97 for the
weights that produced the dumps). Fetch the dumps from the training box:

    scp b650-gpu:'~/llm-distillery/ht_v8_test_dump/*.jsonl' <dump-dir>/

Run:

    .venv/bin/python docs/evidence/2026-09-05-adr023-op-point-table/adr023_op_point_table.py \
        --dump-dir <dump-dir> \
        --labels datasets/training/human_thriving_v8/test.jsonl \
        --out docs/evidence/2026-09-05-adr023-op-point-table/adr023_op_point_table.json

CONTROL. The script recomputes each arm's whole-split AUC and asserts it reproduces the
value published in `experiments/registry.jsonl` (EXP-018/EXP-019) and
`../2026-09-04-v8-probe-calibration/arms_as_rankers.json`. If the control fails the run
aborts: a new number from an instrument that cannot reproduce a known one is worthless.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

# human_thriving v8, from filters/human_thriving/v8/base_scorer.py. Hardcoded on purpose:
# this is a frozen evidence artifact and must keep reproducing the numbers published
# beside it even after the filter's constants change.
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
OP = 4.5
STAGE1_THRESHOLD = 1.75  # filters/human_thriving/v8/config.yaml hybrid_inference.stage1
KS = [17, 20, 26, 30, 35, 43, 50, 60]
N_BOOT = 10000
BOOT_SEED = 42

ARMS = {
    "student_raw": ("scores_raw.jsonl", False),
    "student_calibrated": ("scores_calibrated.jsonl", False),
    "probe_recall_small": ("probe_scores.jsonl", True),
    "probe_recall_large": ("probe_scores_e5large.jsonl", True),
    "probe_reg_small": ("probe_scores_reg_small.jsonl", True),
    "probe_reg_large": ("probe_scores_reg_large.jsonl", True),
}

# EXP-018 / EXP-019 metrics, and arms_as_rankers.json for the two student arms.
PUBLISHED_AUC = {
    "student_raw": 0.94736,
    "student_calibrated": 0.9488,
    "probe_recall_small [ungated]": 0.8710,
    "probe_recall_large [ungated]": 0.9016,
    "probe_reg_small [ungated]": 0.9035,
    "probe_reg_large [ungated]": 0.9021,
}
CONTROL_TOL = 5e-4


def weighted_avg(scores: dict, gate: bool = True) -> float:
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    if gate and scores[GK_DIM] < GK_MIN and v > GK_CAP:
        v = GK_CAP
    return v


def load_scores(path: Path) -> dict:
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["id"]] = r["scores"]
    return out


def top_k_mask(scores: np.ndarray, k: int) -> np.ndarray:
    order = np.argsort(-scores, kind="stable")
    m = np.zeros(len(scores), bool)
    m[order[:k]] = True
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, default=None,
                    help="datasets/scored/human_thriving_v8/corpus.jsonl, for the "
                         "Horvitz-Thompson design weights. Without it the weighted arm "
                         "is skipped and every figure here is UNWEIGHTED.")
    args = ap.parse_args()

    rng = np.random.default_rng(BOOT_SEED)

    truth = {}
    for line in open(args.labels, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            truth[r["id"]] = weighted_avg(dict(zip(r["dimension_names"], r["labels"])), True)

    raw = {name: load_scores(args.dump_dir / fn) for name, (fn, _) in ARMS.items()}
    ids = sorted(set.intersection(*[set(v) for v in raw.values()]) & set(truth))
    if len(ids) != 660:
        raise SystemExit(f"id intersection is {len(ids)}, expected the 660-row test split")

    y = np.array([truth[i] >= OP for i in ids])
    n_pos, n_neg = int(y.sum()), int((~y).sum())

    # Production-faithful score per arm: the student is gated, a probe is not.
    faithful = {n: np.array([weighted_avg(raw[n][i], not is_probe) for i in ids])
                for n, (_, is_probe) in ARMS.items()}
    # Both-ways view, for isolating the gatekeeper's own contribution.
    both = {}
    for name, (_, is_probe) in ARMS.items():
        if is_probe:
            both[f"{name} [gated]"] = np.array([weighted_avg(raw[name][i], True) for i in ids])
            both[f"{name} [ungated]"] = faithful[name]
        else:
            both[name] = faithful[name]

    out = {
        "n": len(ids), "positives": n_pos, "negatives": n_neg,
        "positive_rate": n_pos / len(ids), "op_point": OP,
        "matched_flag_counts": KS, "bootstrap": {"resamples": N_BOOT, "seed": BOOT_SEED},
    }

    # ---- CONTROL ----
    print(f"n={len(ids)}  positives={n_pos}  negatives={n_neg}  "
          f"positive_rate={n_pos/len(ids):.4%}  op-point={OP}\n")
    print("CONTROL - recomputed AUC vs published (abort on mismatch)")
    control = {}
    failures = []
    for key, pub in PUBLISHED_AUC.items():
        got = float(roc_auc_score(y, both[key]))
        d = abs(got - pub)
        control[key] = {"recomputed": got, "published": pub, "abs_delta": d}
        if d >= CONTROL_TOL:
            failures.append(key)
        print(f"  {'OK ' if d < CONTROL_TOL else 'MISMATCH'} {key:34s} "
              f"recomputed {got:.4f}  published {pub:.4f}  d={d:.4f}")
    out["control_auc"] = control
    out["control_passes"] = not failures
    if failures:
        raise SystemExit(f"CONTROL FAILED for {failures}; refusing to publish new numbers")
    print("  => control PASSES\n")

    # ---- deployability ----
    print("DEPLOYABILITY - can the arm reach the literal 4.5 bar?")
    print(f"{'arm':22s} {'min':>7s} {'median':>8s} {'p99':>7s} {'max':>7s} {'flagged@4.5':>12s}")
    out["deployability"] = {}
    for n, v in faithful.items():
        rec = {"min": float(v.min()), "median": float(np.median(v)),
               "p99": float(np.percentile(v, 99)), "max": float(v.max()),
               "flagged_at_op": int((v >= OP).sum())}
        out["deployability"][n] = rec
        print(f"{n:22s} {rec['min']:7.3f} {rec['median']:8.3f} {rec['p99']:7.3f} "
              f"{rec['max']:7.3f} {rec['flagged_at_op']:12d}")

    # ---- matched flag count ----
    print("\nRECALL / SPECIFICITY at MATCHED FLAG COUNT k  (FP = k - TP identically)")
    print(f"{'arm':34s} " + " ".join(f"{'k='+str(k):>13s}" for k in KS))
    out["matched_flag_count"] = {}
    for name, sc in both.items():
        cells, rec = [], {}
        for k in KS:
            tp = int((top_k_mask(sc, k) & y).sum())
            rec[str(k)] = {"tp": tp, "fp": k - tp, "recall": tp / n_pos,
                           "specificity": 1 - (k - tp) / n_neg, "precision": tp / k}
            cells.append(f"{tp:3d} {100*rec[str(k)]['specificity']:8.3f}")
        out["matched_flag_count"][name] = rec
        print(f"{name:34s} " + " ".join(f"{c:>13s}" for c in cells))

    # ---- ranking metrics (for the record; NOT the ADR-023 criterion) ----
    out["auc"] = {n: float(roc_auc_score(y, v)) for n, v in both.items()}
    out["average_precision"] = {n: float(average_precision_score(y, v)) for n, v in both.items()}

    # ⛔ The AUC ORDERING between the two regression arms was published as a finding
    # ("AUC would have picked the wrong arm"). It is a coin flip and must carry its band:
    # CLAUDE.md -- two models whose bands overlap are NOT DISTINGUISHABLE whatever their
    # point estimates say. Same test for AP, which does separate them.
    def paired_metric_ci(fn, a, b, n_boot=N_BOOT):
        obs = float(fn(y, a) - fn(y, b))
        ds = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(ids), len(ids))
            if y[idx].sum() == 0 or (~y[idx]).sum() == 0:
                continue
            ds.append(fn(y[idx], a[idx]) - fn(y[idx], b[idx]))
        ds = np.array(ds)
        return {"observed": obs, "ci_low": float(np.percentile(ds, 2.5)),
                "ci_high": float(np.percentile(ds, 97.5)),
                "p_first_greater": float(np.mean(ds > 0)), "n_replicates": int(len(ds))}

    sm, lg = both["probe_reg_small [ungated]"], both["probe_reg_large [ungated]"]
    st = both["student_calibrated"]
    out["ranking_metric_deltas"] = {
        "auc_reg_small_minus_reg_large": paired_metric_ci(roc_auc_score, sm, lg),
        "ap_reg_small_minus_reg_large": paired_metric_ci(average_precision_score, sm, lg),
        "auc_student_minus_reg_large": paired_metric_ci(roc_auc_score, st, lg),
    }
    print("\nRANKING-METRIC DELTAS with bands (the ordering is NOT a finding on its own)")
    for kk, vv in out["ranking_metric_deltas"].items():
        print(f"  {kk:36s} {vv['observed']:+.4f} "
              f"[{vv['ci_low']:+.4f},{vv['ci_high']:+.4f}]  P={vv['p_first_greater']:.3f}")

    # ---- paired RE-SELECTION bootstrap vs student_calibrated ----
    # ⛔ The top-k mask is RECOMPUTED INSIDE each replicate. A first version of this
    # script froze the two masks on the full sample and resampled only the row indices;
    # that is a McNemar discordant-pair interval on a FIXED classifier, and top-k is
    # sample-dependent. It reported a zero-width 95% CI ([+0,+0]) wherever two arms had
    # no discordant rows, which is proof an interval is not about sampling variability.
    # It also violated the design's own premise: measured, 90.6% of replicates did not
    # surface k rows. Re-selection propagates the ranking's variability, which is the
    # thing being tested.
    def reselect_ci(arm_scores, k, n_boot=N_BOOT):
        base_s, n = faithful["student_calibrated"], len(ids)
        obs = int((top_k_mask(base_s, k) & y).sum() - (top_k_mask(arm_scores, k) & y).sum())
        ds = np.empty(n_boot, dtype=int)
        for b in range(n_boot):
            idx = rng.integers(0, n, n)
            yy = y[idx]
            ds[b] = ((top_k_mask(base_s[idx], k) & yy).sum()
                     - (top_k_mask(arm_scores[idx], k) & yy).sum())
        lo, hi = (float(x) for x in np.percentile(ds, [2.5, 97.5]))
        return obs, lo, hi

    print(f"\nPAIRED RE-SELECTION BOOTSTRAP on (student_calibrated TP - arm TP), "
          f"{N_BOOT} resamples")
    print(f"{'arm':22s} " + " ".join(f"{'k='+str(k):>16s}" for k in KS))
    out["bootstrap_vs_student_calibrated"] = {}
    for name in ["probe_reg_large", "probe_reg_small", "probe_recall_large",
                 "probe_recall_small", "student_raw"]:
        cells, rec = [], {}
        for k in KS:
            obs, lo, hi = reselect_ci(faithful[name], k)
            excl = not (lo <= 0 <= hi)
            rec[str(k)] = {"observed": obs, "ci_low": lo, "ci_high": hi,
                           "ci_excludes_zero": excl}
            cells.append(f"{obs:+d} [{lo:+.0f},{hi:+.0f}]{'*' if excl else ''}")
        out["bootstrap_vs_student_calibrated"][name] = rec
        print(f"{name:22s} " + " ".join(f"{c:>16s}" for c in cells))
    print("  * = 95% CI excludes zero (distinguishable from student_calibrated at that k)")

    # NULL CONTROL: an arm against ITSELF must give exactly [0,0]. Without this the
    # interval above cannot be told from one that is broken in the conservative direction.
    null_obs, null_lo, null_hi = reselect_ci(faithful["student_calibrated"], 26, 2000)
    out["bootstrap_null_control"] = {"k": 26, "observed": null_obs,
                                     "ci_low": null_lo, "ci_high": null_hi,
                                     "passes": (null_obs, null_lo, null_hi) == (0, 0.0, 0.0)}
    print(f"  NULL CONTROL (student_calibrated vs itself, k=26): "
          f"{null_obs:+d} [{null_lo:+.0f},{null_hi:+.0f}] -> "
          f"{'PASS' if out['bootstrap_null_control']['passes'] else 'FAIL'}")

    # ---- cascades, composed end to end ----
    g1 = np.array([weighted_avg(raw["probe_recall_small"][i], False) for i in ids])
    routed = g1 >= STAGE1_THRESHOLD
    out["stage1"] = {"threshold": STAGE1_THRESHOLD, "routing_rate": float(routed.mean()),
                     "positives_screened_out": int((~routed & y).sum())}
    print(f"\nCASCADES (stage-1 = shipped recall e5-small probe @{STAGE1_THRESHOLD}; a screened row"
          f"\npublishes the PROBE's score, a routed row the stage-2 arm's) -- TP / specificity%")
    print(f"  stage-1 routes {routed.mean():.1%} onward; "
          f"positives screened out: {int((~routed & y).sum())}/{n_pos}")
    comps = {
        "A_gate_to_student_calibrated": np.where(routed, faithful["student_calibrated"], g1),
        "B_gate_to_probe_reg_large": np.where(routed, faithful["probe_reg_large"], g1),
        "C_probe_reg_large_alone": faithful["probe_reg_large"],
        "D_probe_reg_small_alone": faithful["probe_reg_small"],
    }
    print(f"{'composition':36s} " + " ".join(f"{'k='+str(k):>13s}" for k in KS))
    out["cascades"] = {}
    for name, sc in comps.items():
        cells, rec = [], {}
        for k in KS:
            tp = int((top_k_mask(sc, k) & y).sum())
            rec[str(k)] = {"tp": tp, "fp": k - tp, "recall": tp / n_pos,
                           "specificity": 1 - (k - tp) / n_neg}
            cells.append(f"{tp:3d} {100*rec[str(k)]['specificity']:8.3f}")
        out["cascades"][name] = rec
        print(f"{name:36s} " + " ".join(f"{c:>13s}" for c in cells))
    out["cascade_B_equals_C"] = all(
        out["cascades"]["B_gate_to_probe_reg_large"][str(k)]["tp"]
        == out["cascades"]["C_probe_reg_large_alone"][str(k)]["tp"] for k in KS)

    # ⛔ REACHABILITY OF THAT COMPARISON. B and C can only differ once a SCREENED row
    # outranks the k-th highest stage-2 score. If that k is past the end of the grid the
    # equality was forced before the data were read and carries NO information -- this
    # repo's first working rule. Report the smallest such k beside the verdict, always.
    stage2 = faithful["probe_reg_large"]
    max_screened = float(stage2[~routed].max())
    desc = np.sort(stage2)[::-1]
    k_first = int(np.searchsorted(-desc, -max_screened) + 1)
    out["cascade_B_equals_C_reachability"] = {
        "max_stage2_score_among_screened_rows": max_screened,
        "kth_highest_score_at_max_k": float(desc[max(KS) - 1]),
        "smallest_k_at_which_B_could_differ_from_C": k_first,
        "max_k_in_grid": max(KS),
        "comparison_could_have_differed": k_first <= max(KS),
    }
    print(f"  B==C: {out['cascade_B_equals_C']}   ⛔ but the smallest k at which B COULD "
          f"differ from C is {k_first} (grid stops at {max(KS)}) -> "
          f"{'informative' if k_first <= max(KS) else 'FORCED, carries no information'}")

    # ---- design-weighted arm (Horvitz-Thompson) ----
    if args.corpus:
        ip = {}
        for line in open(args.corpus, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r["id"] in truth and r.get("inclusion_probability"):
                    ip[r["id"]] = r["inclusion_probability"]
        missing = [i for i in ids if i not in ip]
        if missing:
            raise SystemExit(f"{len(missing)} test ids lack inclusion_probability; "
                             f"refusing to publish a partially-weighted table")
        w = np.array([1.0 / ip[i] for i in ids])
        Wtot, Wpos, Wneg = w.sum(), w[y].sum(), w[~y].sum()
        shares = [round(Wpos / Wtot * m, 6) for m in (0.5, 0.75, 1.0, 1.5, 2.0)]
        wt = {"unweighted_positive_rate": float(y.mean()),
              "design_weighted_positive_rate": float(Wpos / Wtot),
              "ht_weight_min": float(w.min()), "ht_weight_max": float(w.max()),
              "design_weighted_stage1_routing": float(w[routed].sum() / Wtot),
              "matched_weighted_share": {}}
        print(f"\nDESIGN-WEIGHTED (Horvitz-Thompson). unweighted positive rate "
              f"{y.mean():.4%} vs weighted {Wpos/Wtot:.4%}; HT weights "
              f"{w.min():.2f}..{w.max():.2f}; stage-1 routing weighted "
              f"{w[routed].sum()/Wtot:.4%} against unweighted {routed.mean():.4%}")
        print(f"{'arm':22s} " + " ".join(f"{'share='+format(t,'.4f'):>22s}" for t in shares))
        for name in ["student_calibrated", "student_raw", "probe_reg_large", "probe_reg_small"]:
            sc = faithful[name]
            order = np.argsort(-sc, kind="stable")
            cum = np.cumsum(w[order])
            cells, rec = [], {}
            for t in shares:
                kk = int(np.searchsorted(cum, t * Wtot) + 1)
                m = np.zeros(len(ids), bool)
                m[order[:kk]] = True
                wtp, wfp = w[m & y].sum(), w[m & ~y].sum()
                rec[str(t)] = {"rows_surfaced": kk,
                               "weighted_recall": float(wtp / Wpos),
                               "weighted_specificity": float(1 - wfp / Wneg)}
                cells.append(f"{wtp/Wpos:6.3f} / {1-wfp/Wneg:8.5f}")
            wt["matched_weighted_share"][name] = rec
            print(f"{name:22s} " + " ".join(f"{c:>22s}" for c in cells))
        out["design_weighted"] = wt
    else:
        out["design_weighted"] = None
        print("\n⚠️  --corpus not given: every figure above is UNWEIGHTED.")

    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
