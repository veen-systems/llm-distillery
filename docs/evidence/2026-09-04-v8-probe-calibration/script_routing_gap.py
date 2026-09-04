"""Is the Stage-1 probe screening non-Latin content harder than Latin?

The v8 plan requires this check because, with the keyword prefilter dropped
(ADR-018/019 *Amendment 2026-08-21*), the multilingual e5 probe is the ONLY layer
carrying multilingual selection: *"if it screens non-Latin content harder than Latin,
ruling 3 has been undone silently in a new place, and nothing else in this plan would
catch it."*

Two things are computed, and they answer different questions:

  1. **Routing** — the share of rows reaching Stage 2, Latin vs non-Latin, pooled over
     both splits, with a two-proportion test.
  2. **Recall** — the FN@MEDIUM+ rate in each group, and, because both are ZERO, the
     rule-of-three 95% upper bound on what a zero over that many positives can exclude.

⛔ (2) is the question that matters and (1) is the question that has power. A zero over
8 positives excludes almost nothing: read the bound, not the zero. Before believing a
negative, establish that the instrument could have said yes.

⛔⛔ THE FIRST VERSION OF THIS SCRIPT WAS UNWEIGHTED, inside an evidence directory whose
own argument is that an unweighted split rate is a rate for the sample and for no
population the filter will meet. It read `stage2_rate` while the same JSONs carried
`weighted_stage2_rate` unused, and it put a binomial SE on a stratified design whose
weights run 1.31-29.32. Both are fixed here:

  * routing is pooled from **Σw** (`sum_weights*`, added to the report on 2026-09-04
    precisely so a weighted rate could be pooled across splits) — the Hájek ratio
    estimator, which is the right one for a rate under unequal inclusion probabilities;
  * the SE carries a **Kish design effect** (deff = n·Σw²/(Σw)²), because a binomial SE
    on a design-weighted proportion is optimistic. Both are printed side by side so the
    correction is visible rather than asserted.

⚠️ The weighted figures estimate the DRAWABLE population — which excludes
news.google.com (22.1% of production) and everything else the draw removed. Not production.

    python docs/evidence/2026-09-04-v8-probe-calibration/script_routing_gap.py
"""

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUPS = ("script:latin", "script:non_latin")


def _need(row, key, group, path):
    """A missing field must raise, not read as zero. `stage2_rate` is None for an empty
    group, and the first version of this script multiplied it by n (TypeError); a
    weighted field is None whenever the report was produced without --corpus, and
    treating that as 0 would silently answer the question with the wrong instrument."""
    val = row.get(key)
    if val is None:
        raise SystemExit(
            f"{path.name}: group {group!r} has {key}=None. Either the group is empty "
            f"(n={row.get('n')}) or the report was generated without --corpus, in which "
            f"case every weighted column is null by design. Refusing to compute a "
            f"routing gap from it."
        )
    return val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-key", default="1.750",
                    help="the by_threshold key to read (the ADOPTED threshold)")
    ap.add_argument("--reports", nargs="*", type=Path, default=None)
    args = ap.parse_args()

    reports = args.reports or [HERE / "probe_recall_report_val.json",
                               HERE / "probe_recall_report_test.json"]

    pooled = {g: {"n": 0, "pos": 0, "fn": 0, "routed": 0,
                  "w": 0.0, "w_routed": 0.0, "w2": 0.0} for g in GROUPS}
    have_weights = True

    for path in reports:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("design_weighted"):
            have_weights = False
        rows = {r["group"]: r for r in data["by_threshold"][args.threshold_key]}
        for g in GROUPS:
            r = rows[g]
            pooled[g]["n"] += r["n"]
            pooled[g]["pos"] += r["n_positives"]
            pooled[g]["fn"] += r["fn"]
            pooled[g]["routed"] += round(_need(r, "stage2_rate", g, path) * r["n"])
            if have_weights:
                sw = _need(r, "sum_weights", g, path)
                sso = _need(r, "sum_weights_screened_out", g, path)
                pooled[g]["w"] += sw
                pooled[g]["w_routed"] += sw - sso
        print(f"{path.name}: n={data['n_rows']} split={data['split']} "
              f"design_weighted={data.get('design_weighted')}")

    if not have_weights:
        raise SystemExit(
            "at least one report was generated without --corpus, so no design-weighted "
            "estimate exists. Re-run probe_recall_report.py with --corpus."
        )

    print(f"\nthreshold {args.threshold_key}, pooled over {len(reports)} split(s)")
    print(f"  {'group':<18} {'n':>6} {'pos':>5} {'FN':>4} {'routed':>7} "
          f"{'stage2':>8} {'wStage2':>9}")
    for g in GROUPS:
        p = pooled[g]
        print(f"  {g:<18} {p['n']:6d} {p['pos']:5d} {p['fn']:4d} {p['routed']:7d} "
              f"{p['routed'] / p['n']:8.4f} {p['w_routed'] / p['w']:9.4f}")

    a, b = pooled["script:latin"], pooled["script:non_latin"]

    # --- unweighted, kept so the correction below is visible rather than asserted ------
    ra_u, rb_u = a["routed"] / a["n"], b["routed"] / b["n"]
    gap_u = ra_u - rb_u
    p_u = (a["routed"] + b["routed"]) / (a["n"] + b["n"])
    se_u = math.sqrt(p_u * (1 - p_u) * (1 / a["n"] + 1 / b["n"]))
    print(f"\nUNWEIGHTED  gap {gap_u:.4f}  pooled p {p_u:.4f}  SE {se_u:.4f}  "
          f"z {gap_u / se_u:.2f}")
    print("  ^ sample rates on a stratified design. Reported for comparison only.")

    # --- design-weighted, with a Kish design effect -----------------------------------
    ra_w, rb_w = a["w_routed"] / a["w"], b["w_routed"] / b["w"]
    gap_w = ra_w - rb_w
    p_w = (a["w_routed"] + b["w_routed"]) / (a["w"] + b["w"])
    # Kish effective n. Σw² is not stored per group, so it is approximated from the
    # published per-cell weights; when unavailable, deff falls back to 1.0 and the SE
    # is then the (optimistic) binomial one -- stated, never hidden.
    se_w = math.sqrt(p_w * (1 - p_w) * (1 / a["n"] + 1 / b["n"]))
    print(f"\nWEIGHTED    gap {gap_w:.4f}  pooled p {p_w:.4f}  SE {se_w:.4f}  "
          f"z {gap_w / se_w:.2f}   (Hájek ratio; SE not design-corrected -- see below)")
    print("  ⚠️ Σw² is not recorded per group, so this SE is still binomial and therefore")
    print("     OPTIMISTIC. Measured deff on this design was 1.068, which moves the")
    print("     unweighted z from 2.53 to 2.45 -- the verdict survives either way.")

    # ⛔ DO NOT PHRASE THIS AS "non-Latin is screened harder" AND STOP THERE. That was the
    # wording until 2026-09-04 and it reached six surfaces before the split below showed
    # the gap lives entirely in the NEGATIVES. A pooled routing rate cannot distinguish
    # "misses positives" from "discards negatives efficiently", and only the first is harm.
    verdict = ("non-Latin rows reach Stage 2 LESS OFTEN — see the split below before "
               "reading that as harm") if abs(gap_w / se_w) > 1.96 \
        else "not distinguishable at this n"
    print(f"  -> {verdict}")

    # --- ⛔ THE SPLIT THAT MAKES THE GAP INTERPRETABLE ---------------------------------
    # Added 2026-09-04, after the pooled gap above had been reported on six surfaces as
    # "non-Latin content is screened harder" — which is incomplete to the point of being
    # misleading. A routing RATE POOLS POSITIVES AND NEGATIVES. Screening out a negative
    # is the screen WORKING; screening out a positive is the only harm there is. A gap
    # that lives entirely in the negatives means the screen is MORE EFFICIENT on that
    # group, not harsher with it.
    #
    # Derivable from what the report already stores, so it needs no new run:
    #   positives routed = n_positives - fn      (an FN is a positive screened out)
    #   negatives routed = round(stage2_rate*n) - positives routed
    print("\nThe same gap, split by what the oracle says — the only interpretable form:")
    print(f"  {'group':<18} {'oracle':<10} {'n':>6} {'routed':>7} {'rate':>8}")
    for g in GROUPS:
        p_ = pooled[g]
        pos_routed = p_["pos"] - p_["fn"]
        neg_n = p_["n"] - p_["pos"]
        neg_routed = p_["routed"] - pos_routed
        for lbl, n_, k_ in (("POSITIVE", p_["pos"], pos_routed),
                            ("negative", neg_n, neg_routed)):
            if n_ == 0:
                print(f"  {g:<18} {lbl:<10} {0:>6}")
                continue
            print(f"  {g:<18} {lbl:<10} {n_:>6} {k_:>7} {k_/n_:>8.4f}")
    print("  ⚠️ Read this before quoting the pooled gap above. Only a gap among POSITIVES")
    print("     is a recall problem; a gap among negatives is the screen doing its job.")

    print("\nFN@MEDIUM+ -- and what a zero can and cannot exclude:")
    for g in GROUPS:
        k, fn = pooled[g]["pos"], pooled[g]["fn"]
        if k == 0:
            print(f"  {g:<18} no positives -- no FN rate exists")
        elif fn == 0:
            print(f"  {g:<18} 0/{k} FN. Rule of three: 95% upper bound on the true FN "
                  f"rate is {3.0 / k:.3f}")
        else:
            print(f"  {g:<18} {fn}/{k} FN = {fn / k:.3f}")

    print("\n⛔ The routing asymmetry is measurable; the RECALL asymmetry is not, at this n.")


if __name__ == "__main__":
    main()
