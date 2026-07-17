"""Calibration-batch analysis for sustainability_technology v4 (solutions broadening, #43).

Evaluates the 350-article calibration batch (top-100 ST v3 + top-100 foresight v1
+ 100 raw stream + 50 belonging community) against config.yaml ::
calibration_batch.decision_criteria, for each oracle scored. ADR-020 validation
case: also computes cross-oracle agreement and emits the disagreement set for
agent judging.

Usage:
    PYTHONPATH=. python scripts/calibration_solutions_v4.py \
        --sample datasets/calibration/solutions_v4_calibration_350.jsonl \
        --scored deepseek=datasets/calibration/solutions_v4_calib350_deepseek.jsonl \
        --scored gemini=datasets/calibration/solutions_v4_calib350_gemini.jsonl \
        --disagreement-out datasets/calibration/solutions_v4_disagreement.jsonl
"""

import argparse
import json
from collections import Counter
from pathlib import Path

DIMS = [
    "solution_concreteness", "systemic_impact", "evidence_strength",
    "governance_intervention_strength", "community_practice_strength",
    "equity_access", "economic_viability",
]
WEIGHTS = {  # config.yaml scoring weights
    "solution_concreteness": 0.20, "systemic_impact": 0.20, "evidence_strength": 0.15,
    "governance_intervention_strength": 0.15, "community_practice_strength": 0.10,
    "equity_access": 0.10, "economic_viability": 0.10,
}
# Alternative weight vectors evaluated on the same labels (weights are
# analysis-side; the oracle never sees them).
ALT_WEIGHTS = {
    "config": WEIGHTS,
    "tech_rebalanced": {  # config decision-criteria note: raise concreteness+systemic
        "solution_concreteness": 0.25, "systemic_impact": 0.25, "evidence_strength": 0.15,
        "governance_intervention_strength": 0.10, "community_practice_strength": 0.05,
        "equity_access": 0.10, "economic_viability": 0.10,
    },
}
FLAG_CAPS = {
    "crisis_reporting_no_solution": 4.0,
    "rhetoric_only": 5.0,
    "corporate_pr_unverifiable": 5.0,
}
ANALYSIS_FIELD = "sustainability_technology_analysis"
GATEKEEPER_DIM, GATEKEEPER_MIN, GATEKEEPER_CAP = "solution_concreteness", 3.0, 3.0


def wavg(dims, weights):
    return sum(dims[d] * weights[d] for d in DIMS)


def wavg_typed_renorm(dims, weights, solution_type):
    """Per-type renormalized weighted average: divide by the weight mass of
    dims applicable to the type (tech excludes gov+comm, governance excludes
    comm...). Candidate fix for the type-ceiling asymmetry."""
    excluded = {
        "tech": {"governance_intervention_strength", "community_practice_strength"},
        "governance": {"community_practice_strength"},
        "community": set(),  # governance scored on merits per 2026-07-17 prompt
        "hybrid": set(),
    }.get(solution_type, set())
    mass = sum(w for d, w in weights.items() if d not in excluded)
    return sum(dims[d] * weights[d] for d in DIMS if d not in excluded) / mass


def apply_gatekeeper(dims, wa):
    return min(wa, GATEKEEPER_CAP) if dims[GATEKEEPER_DIM] < GATEKEEPER_MIN else wa


def hist(vals, edges=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10.01)):
    buckets = [0] * (len(edges) - 1)
    for v in vals:
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1]:
                buckets[i] += 1
                break
    return buckets


def bar(buckets, width=40):
    total = max(sum(buckets), 1)
    return " ".join(f"{100*b/total:.0f}" for b in buckets)


def load_scored(path):
    out = {}
    errors = 0
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if "error" in r:
            errors += 1
            continue
        a = r[ANALYSIS_FIELD]
        dims = {d: float(a[d]["score"]) for d in DIMS}
        out[r["id"]] = {
            "dims": dims,
            "content_type": a.get("content_type", "unknown"),
            "solution_type": a.get("solution_type"),
            "evidence": {d: a[d].get("evidence", "") for d in DIMS},
        }
    return out, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--scored", action="append", required=True,
                    help="name=path, repeatable")
    ap.add_argument("--disagreement-out")
    ap.add_argument("--disagreement-n", type=int, default=30)
    args = ap.parse_args()

    sample = {}
    for line in open(args.sample, encoding="utf-8"):
        r = json.loads(line)
        sample[r["id"]] = r

    oracles = {}
    for spec in args.scored:
        name, path = spec.split("=", 1)
        scored, errors = load_scored(path)
        oracles[name] = scored
        print(f"[{name}] {len(scored)} scored, {errors} error rows")

    for name, scored in oracles.items():
        print(f"\n{'='*72}\nORACLE: {name}\n{'='*72}")
        joined = [(sample[i], s) for i, s in scored.items() if i in sample]
        passed = [(r, s) for r, s in joined if s["content_type"] != "not_a_solution"]
        print(f"scored={len(joined)}  passed_step1={len(passed)}  "
              f"step1_killed={len(joined)-len(passed)}")

        # --- per-dim distributions (passed-Step-1 population) ---
        print("\nPer-dim histograms, passed-Step-1 population (% per 1-pt bin 0..10):")
        for d in DIMS:
            vals = [s["dims"][d] for _, s in passed]
            b = hist(vals)
            mid = sum(1 for v in vals if 3.0 <= v <= 5.0)
            print(f"  {d:34s} {bar(b)}   mid(3-5)={100*mid/max(len(vals),1):.0f}%")

        # --- content types / solution types ---
        print("\ncontent_type:", dict(Counter(s["content_type"] for _, s in joined)))
        print("solution_type (passed):", dict(Counter(s["solution_type"] for _, s in passed)))

        # --- per bucket ---
        for bucket in ["st_v3_top100", "foresight_v1_top100", "raw_stream_random",
                       "belonging_top50_community"]:
            rows = [(r, s) for r, s in joined if r["calibration_bucket"] == bucket]
            if not rows:
                continue
            killed = sum(1 for _, s in rows if s["content_type"] == "not_a_solution")
            live = [(r, s) for r, s in rows if s["content_type"] != "not_a_solution"]
            was = [apply_gatekeeper(s["dims"], wavg(s["dims"], WEIGHTS)) for _, s in live]
            print(f"\n  bucket {bucket}: n={len(rows)} step1_killed={killed} "
                  f"({100*killed/len(rows):.0f}%)")
            if was:
                was_sorted = sorted(was)
                print(f"    wa(config weights): min={was_sorted[0]:.2f} "
                      f"median={was_sorted[len(was)//2]:.2f} max={was_sorted[-1]:.2f}  "
                      f">=4.5: {sum(1 for w in was if w >= 4.5)}/{len(was)}  "
                      f">=7.0: {sum(1 for w in was if w >= 7.0)}/{len(was)}")
                for wname, wv in ALT_WEIGHTS.items():
                    if wname == "config":
                        continue
                    alt = [apply_gatekeeper(s["dims"], wavg(s["dims"], wv)) for _, s in live]
                    print(f"    wa({wname}): >=4.5: {sum(1 for w in alt if w >= 4.5)}/{len(alt)}  "
                          f">=7.0: {sum(1 for w in alt if w >= 7.0)}/{len(alt)}")
                ren = [apply_gatekeeper(s["dims"],
                                        wavg_typed_renorm(s["dims"], WEIGHTS,
                                                          s["solution_type"]))
                       for _, s in live]
                print(f"    wa(type-renormalized): >=4.5: {sum(1 for w in ren if w >= 4.5)}/{len(ren)}  "
                      f">=7.0: {sum(1 for w in ren if w >= 7.0)}/{len(ren)}")

        # --- decision criteria ---
        raw_rows = [(r, s) for r, s in joined if r["calibration_bucket"] == "raw_stream_random"]
        raw_killed = sum(1 for _, s in raw_rows if s["content_type"] == "not_a_solution")
        print(f"\n  CRITERION step1>50% raw stream: {100*raw_killed/max(len(raw_rows),1):.0f}% "
              f"-> {'PASS' if raw_killed > len(raw_rows)/2 else 'FAIL'}")

        # cap adherence
        violations = []
        for r, s in joined:
            cap = FLAG_CAPS.get(s["content_type"])
            if cap is None:
                continue
            for d in DIMS:
                if s["dims"][d] > cap + 1e-9:
                    violations.append((r["id"], s["content_type"], d, s["dims"][d]))
        print(f"  CRITERION cap adherence: {len(violations)} violations "
              f"-> {'PASS' if not violations else 'FAIL'}")
        for v in violations[:10]:
            print(f"    {v}")

        # type distribution among solutions
        types = Counter(s["solution_type"] for _, s in passed
                        if s["content_type"] == "solution")
        print(f"  type distribution (solutions only): {dict(types)}")

    # --- cross-oracle agreement (first two oracles) ---
    names = list(oracles)
    if len(names) >= 2:
        a, b = names[0], names[1]
        common = [i for i in oracles[a] if i in oracles[b] and i in sample]
        print(f"\n{'='*72}\nCROSS-ORACLE: {a} vs {b} (n={len(common)})\n{'='*72}")
        for d in DIMS:
            xs = [oracles[a][i]["dims"][d] for i in common]
            ys = [oracles[b][i]["dims"][d] for i in common]
            n = len(xs)
            mx, my = sum(xs)/n, sum(ys)/n
            num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
            dx = (sum((x-mx)**2 for x in xs))**0.5
            dy = (sum((y-my)**2 for y in ys))**0.5
            r_ = num/(dx*dy) if dx and dy else float("nan")
            mae = sum(abs(x-y) for x, y in zip(xs, ys))/n
            print(f"  {d:34s} pearson={r_:.3f}  MAE={mae:.2f}  "
                  f"mean {a}={mx:.2f} {b}={my:.2f}")
        deltas = []
        for i in common:
            wa_a = apply_gatekeeper(oracles[a][i]["dims"], wavg(oracles[a][i]["dims"], WEIGHTS))
            wa_b = apply_gatekeeper(oracles[b][i]["dims"], wavg(oracles[b][i]["dims"], WEIGHTS))
            deltas.append((abs(wa_a - wa_b), i, wa_a, wa_b))
        deltas.sort(reverse=True)
        mae_wa = sum(d[0] for d in deltas)/len(deltas)
        step1_disagree = sum(
            1 for i in common
            if (oracles[a][i]["content_type"] == "not_a_solution")
            != (oracles[b][i]["content_type"] == "not_a_solution"))
        print(f"\n  weighted-average MAE: {mae_wa:.2f}   Step-1 disagreements: "
              f"{step1_disagree}/{len(common)}")
        if args.disagreement_out:
            with open(args.disagreement_out, "w", encoding="utf-8") as fh:
                for delta, i, wa_a, wa_b in deltas[:args.disagreement_n]:
                    rec = dict(sample[i])
                    rec["disagreement"] = {
                        a: {"wa": round(wa_a, 2), **oracles[a][i]},
                        b: {"wa": round(wa_b, 2), **oracles[b][i]},
                        "delta_wa": round(delta, 2),
                    }
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"  wrote top-{args.disagreement_n} disagreement set -> {args.disagreement_out}")


if __name__ == "__main__":
    main()
