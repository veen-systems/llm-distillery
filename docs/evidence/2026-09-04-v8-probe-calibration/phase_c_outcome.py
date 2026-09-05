"""Did Phase C produce a filter that does the thing v8 exists to do?

⛔ THE QUESTION THIS FILE REPLACES. Every recall figure reported during Phase C was set
beside the deployed fleet's 0.59-0.72 — "v8's recall is below all six". That comparison is
VOID, and this script is what establishes it: v8 and v7 do not have the same positive
class. On the same 660 test rows, v7 calls 117 rows positive and v8 calls 35; they agree on
30. Jaccard 0.246. v8 keeps 25.6% of what v7 called positive.

Recall is conditional on the true class, which is exactly why it survives a change of base
RATE — and exactly why it does NOT survive a change of DEFINITION. Two recalls of two
different classes are two different quantities with the same name. (`memory/` records the
weaker version of this correction already: recall survives a change of rate, not of mix.
A changed definition is stronger than either.)

WHAT IS ACTUALLY MEASURABLE, and what this script measures instead. v8 exists to stop
`uplifting v7` surfacing harm-answered-only and institution-beneficiary content (#107, the
class-A rulings). So partition the rows v7 SURFACED by what the v8 oracle says about them:

    "junk"  v7 >= 4.5 and v8 oracle <  4.5   -> v8 says v7 was wrong to surface it
    "good"  v7 >= 4.5 and v8 oracle >= 4.5   -> both definitions agree it belongs

Then ask two things of the trained student, at a sweep of operating points:
  * how much of the junk does it remove?      (the purpose)
  * how much of the good does it keep?        (the cost)

And one control, which is the one that matters: **AUC on those rows only**, against v7's own
score as the baseline. A student that merely scored everything lower would move both
quantities together and show no AUC gain. A student that learned the distinction separates
them.

⛔ ADDED 2026-09-05: THE DESIGN-WEIGHTED ARM, and why the first version's numbers were
sample quantities. The v8 test split is drawn from a stratified design spanning 25.1x in
`inclusion_probability`, defined by the draw in `docs/evidence/2026-08-29-v8-corpus-draw/`, so an
unweighted share describes the 660 rows drawn, not the corpus they were drawn from. EXP-024
hit exactly this on the same rows and its weighted arm did not say the same thing as its
unweighted one. ⚠️ The 25.1x span and its 16 cells are properties of THESE 660 TEST ROWS
(`../2026-09-05-adr023-op-point-table/README.md` §5); the draw as a whole spans 26.0x over 17
non-empty cells -- do not attribute the split's numbers to the corpus draw. Every sweep below is therefore printed TWICE -- unweighted (kept verbatim,
so the numbers published on 2026-09-04 still reproduce) and Horvitz-Thompson weighted at
w = 1 / inclusion_probability. ⚠️ Neither arm carries a confidence band; the junk/good
partition is 87 + 30 rows.

⚠️ SCOPE. This shows whether v8 implements the definition the owner chose. It does NOT show
v8 is "better than v7" in any absolute sense — v7 is being judged against a target it was
never trained on, so its score here is a baseline, not a verdict on v7. Whether the new
definition is the right one is an editorial judgement (#107), not a measurement.

    .venv/bin/python docs/evidence/2026-09-04-v8-probe-calibration/phase_c_outcome.py \
        --dump-dir <dir with scores_raw.jsonl / scores_calibrated.jsonl> \
        --labels datasets/training/human_thriving_v8/test.jsonl \
        --corpus datasets/scored/human_thriving_v8/corpus.jsonl
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

# human_thriving v8, frozen here on purpose: this is an evidence artifact and must keep
# reproducing the numbers published beside it after the filter's constants move.
WEIGHTS = {
    "human_wellbeing_impact": 0.30, "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15, "evidence_level": 0.10,
    "benefit_distribution": 0.10, "change_durability": 0.15,
}
DIMS = list(WEIGHTS)
GK_DIM, GK_MIN, GK_CAP = "evidence_level", 3.0, 3.0
MEDIUM = 4.5
BARS = (3.0, 3.5, 3.75, 4.0, 4.25, 4.5, 5.0)


def weighted_avg(scores: dict) -> float:
    v = sum(scores[d] * WEIGHTS[d] for d in DIMS)
    return GK_CAP if (scores[GK_DIM] < GK_MIN and v > GK_CAP) else v


def load_scores(path: Path) -> dict:
    return {r["id"]: weighted_avg(r["scores"])
            for r in (json.loads(l) for l in open(path, encoding="utf-8") if l.strip())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    corpus = {r["id"]: r for r in
              (json.loads(l) for l in open(args.corpus, encoding="utf-8") if l.strip())}
    oracle, v7 = {}, {}
    for line in open(args.labels, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        oracle[r["id"]] = weighted_avg(dict(zip(r.get("dimension_names", DIMS), r["labels"])))
        c = corpus.get(r["id"])
        if c is None:
            raise SystemExit(f"id {r['id']} absent from {args.corpus} — cannot read its v7 score")
        if c.get("v7_score") is None:
            raise SystemExit(f"id {r['id']} has no v7_score; the v7/v8 comparison needs one on "
                             f"every row, or the partition below is silently incomplete")
        v7[r["id"]] = float(c["v7_score"])

    # Horvitz-Thompson weights. ⛔ REFUSE A PARTIALLY-WEIGHTED TABLE: a row without an
    # inclusion probability silently gets no vote, which is a different estimator, not a
    # slightly noisier one. Same rule as adr023_op_point_table.py.
    #
    # ⛔ AND REFUSE AN INVALID ONE. The first version tested `if p_incl:`, which conflates
    # absent / None / 0 / 0.0 and accepts a negative or an out-of-range value silently --
    # a negative weight makes a "share" negative or greater than one and it is printed as
    # a percentage either way. Found by review, 2026-09-05, together with the case that
    # matters most: if EVERY row carried 0.0 the dict came out empty and the script
    # announced "NO DESIGN WEIGHTS in the corpus", which would be false.
    present = {i: corpus[i].get("inclusion_probability") for i in oracle}
    have = {i: v for i, v in present.items() if v is not None}
    bad = {i: v for i, v in have.items()
           if not isinstance(v, (int, float)) or isinstance(v, bool)
           or not (0.0 < float(v) <= 1.0)}
    if bad:
        i, v = next(iter(bad.items()))
        raise SystemExit(f"{len(bad)} of {len(have)} rows carry an "
                         f"`inclusion_probability` outside (0, 1] -- e.g. {i} = {v!r}. "
                         f"Refusing to publish: 1/p is then not a design weight, and the "
                         f"shares below would still print as percentages.")
    if have and len(have) != len(oracle):
        raise SystemExit(f"{len(oracle) - len(have)} of {len(oracle)} rows lack "
                         f"`inclusion_probability`; refusing to publish a partially-"
                         f"weighted table")
    ht = {i: 1.0 / float(v) for i, v in have.items()}

    ids = sorted(oracle)
    junk = [i for i in ids if v7[i] >= MEDIUM and oracle[i] < MEDIUM]
    good = [i for i in ids if v7[i] >= MEDIUM and oracle[i] >= MEDIUM]
    v8_only = [i for i in ids if v7[i] < MEDIUM and oracle[i] >= MEDIUM]
    if not junk or not good:
        raise SystemExit("one side of the partition is empty — the comparison would be "
                         "vacuous and any AUC below undefined")
    # The sweep also divides by the WHOLE-SPLIT positive and negative counts, which the
    # partition guard above does not cover. Review, 2026-09-05.
    if not [i for i in ids if oracle[i] >= MEDIUM] or \
            not [i for i in ids if oracle[i] < MEDIUM]:
        raise SystemExit("the split has no positives or no negatives at the op-point — "
                         "recall and specificity below would divide by zero")

    inter = len(good)
    union = len(good) + len(junk) + len(v8_only)
    report = {
        "n": len(ids),
        "v7_positives": len(good) + len(junk),
        "v8_positives": len(good) + len(v8_only),
        "agree_positive": len(good),
        "v8_demotes": len(junk),
        "v8_only_positive": len(v8_only),
        "jaccard": inter / union,
        "share_of_v7_positives_v8_keeps": len(good) / (len(good) + len(junk)),
        "arms": {},
    }

    print(f"n={report['n']}   v7 positives {report['v7_positives']}   "
          f"v8 positives {report['v8_positives']}   agreed {report['agree_positive']}")
    print(f"Jaccard of the two positive classes: {report['jaccard']:.3f}  "
          f"— v8 keeps {report['share_of_v7_positives_v8_keeps']:.1%} of v7's positives")
    print("⛔ Two recalls of two different classes are not comparable numbers.\n")

    if ht:
        w_junk, w_good = sum(ht[i] for i in junk), sum(ht[i] for i in good)
        report["design_weights"] = {
            "field": "inclusion_probability",
            "source": str(args.corpus),
            "weight_span": max(ht.values()) / min(ht.values()),
            "unweighted_v8_positive_rate": sum(
                1 for i in ids if oracle[i] >= MEDIUM) / len(ids),
            "design_weighted_v8_positive_rate": sum(
                ht[i] for i in ids if oracle[i] >= MEDIUM) / sum(ht.values()),
        }
        print(f"DESIGN WEIGHTS: span {report['design_weights']['weight_span']:.1f}x; "
              f"v8 positive rate unweighted "
              f"{report['design_weights']['unweighted_v8_positive_rate']:.4%} vs weighted "
              f"{report['design_weights']['design_weighted_v8_positive_rate']:.4%}\n")
    else:
        print("⚠️ NO DESIGN WEIGHTS in the corpus — every share below is a SAMPLE "
              "quantity and the weighted arm is absent.\n")

    y = np.array([1 if i in set(good) else 0 for i in junk + good])
    for arm, fname in (("raw", "scores_raw.jsonl"), ("calibrated", "scores_calibrated.jsonl")):
        sc = load_scores(args.dump_dir / fname)
        rows = []
        for bar in BARS:
            removed = sum(1 for i in junk if sc[i] < bar)
            kept = sum(1 for i in good if sc[i] >= bar)
            pos = [i for i in ids if oracle[i] >= MEDIUM]
            neg = [i for i in ids if oracle[i] < MEDIUM]
            rows.append({
                "bar": bar,
                "junk_removed": removed, "junk_total": len(junk),
                "junk_removed_share": removed / len(junk),
                "good_kept": kept, "good_total": len(good),
                "good_kept_share": kept / len(good),
                "recall_all_v8_positives": sum(1 for i in pos if sc[i] >= bar) / len(pos),
                "specificity": sum(1 for i in neg if sc[i] < bar) / len(neg),
            })
            if ht:
                rows[-1].update({
                    "junk_removed_share_weighted":
                        sum(ht[i] for i in junk if sc[i] < bar) / w_junk,
                    "good_kept_share_weighted":
                        sum(ht[i] for i in good if sc[i] >= bar) / w_good,
                    "recall_all_v8_positives_weighted":
                        sum(ht[i] for i in pos if sc[i] >= bar)
                        / sum(ht[i] for i in pos),
                    "specificity_weighted":
                        sum(ht[i] for i in neg if sc[i] < bar)
                        / sum(ht[i] for i in neg),
                })
        auc = float(roc_auc_score(y, np.array([sc[i] for i in junk + good])))
        report["arms"][arm] = {"auc_on_disputed_rows": auc, "sweep": rows}
        print(f"=== {arm} ===   AUC on the {len(junk)+len(good)} rows v7 surfaced: {auc:.4f}")
        print(f"  {'bar':>5} {'junk removed':>16} {'good kept':>14} {'recall':>8} {'spec':>8}")
        for r in rows:
            print(f"  {r['bar']:5.2f} {r['junk_removed']:>7}/{r['junk_total']} "
                  f"{r['junk_removed_share']:6.1%} {r['good_kept']:>4}/{r['good_total']} "
                  f"{r['good_kept_share']:6.1%} {r['recall_all_v8_positives']:8.3f} "
                  f"{r['specificity']:8.4f}")
        if ht:
            print(f"  -- design-weighted (HT, w = 1/inclusion_probability) --")
            print(f"  {'bar':>5} {'junk removed':>13} {'good kept':>11} "
                  f"{'recall':>8} {'spec':>8}")
            for r in rows:
                print(f"  {r['bar']:5.2f} {r['junk_removed_share_weighted']:12.1%} "
                      f"{r['good_kept_share_weighted']:11.1%} "
                      f"{r['recall_all_v8_positives_weighted']:8.3f} "
                      f"{r['specificity_weighted']:8.4f}")
        print()

    base = float(roc_auc_score(y, np.array([v7[i] for i in junk + good])))
    report["v7_auc_on_disputed_rows"] = base
    print(f"BASELINE — v7's own score on the same rows: AUC {base:.4f}")
    print("A student that merely scored everything lower would move junk-removed and "
          "good-kept together and show NO AUC gain over this.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
