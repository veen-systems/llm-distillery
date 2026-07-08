"""Agreement gate for nature_recovery v4 (blocks deploy — plan §E, NM#229).

Dual-scores the FROZEN gate cohorts with the v2 student (baseline) and the v4
student (candidate), then computes NM#229's 4 acceptance metrics. Emits a report
and an overall PASS/FAIL. This is the deploy gate: v4 ships only if it passes.

INPUTS (produced by scoring each cohort with each student — see RUNBOOK):
  --v2-scored  JSONL: {id, nature_recovery_analysis|weighted_average} from v2 student
  --v4-scored  JSONL: same, from v4 student
  --gate-dir   datasets/gate (frozen cohorts)
Scores are compared on the surfacing signal = weighted average WITH the
recovery_evidence gatekeeper, thresholded at the medium/surfacing boundary (4.0).

METRICS:
  1. probe-demotion    — decline probes fall BELOW surfacing under v4
                         (Wilson 95% CI lower bound on the demotion rate).
  2. over-demotion      — high_band_shift ≤ 0.05 on Source-A (fraction that
                         surfaced under v2 but drop below under v4).
  3. protection-accept  — delivered-protection probes SURFACE under v4 (#70).
  4. agreement          — Spearman(v2 WA, v4 WA) on Source-A.

⚠️ CAVEATS (documented, surfaced in the report):
  - Source-A is NOT independent: 144/154 of it is in the v4 training set, so
    metrics 2/4 measure partly memorization, not generalization. Treat as a
    guard against gross over-demotion, not a clean generalization test.
  - No delivered-protection probe cohort was frozen pre-augmentation (#70
    postdates the freeze). Metric 3 requires --protection-probes (curate from
    the §A.5 pilot's genuine delivered-protection set + more, held out of
    training). If absent, metric 3 is reported as SKIPPED, not PASS.
  - display_ranking.calculate_display_rank (NexusMind) is the production
    surfacing signal; this uses the WA+gatekeeper proxy. Vendoring the exact
    ranker (point-in-time copy, frozen `now`) is a refinement (plan §E).

Runtime verification PENDING: needs the v2 student from HF Hub (huggingface_token)
+ gpu-server to produce the two scored files. The statistics below are unit-tested.
"""
import argparse
import json
import math
from pathlib import Path

MEDIUM = 4.0
GATEKEEPER_MIN, GATEKEEPER_CAP = 3.0, 3.5
WEIGHTS = {"recovery_evidence": .25, "measurable_outcomes": .20,
           "ecological_significance": .20, "restoration_scale": .15,
           "human_agency": .10, "protection_durability": .10}


def surfacing_score(rec):
    """Weighted average with the recovery_evidence gatekeeper (base_scorer)."""
    if "weighted_average" in rec:
        return float(rec["weighted_average"])
    a = rec.get("nature_recovery_analysis", rec)
    def s(d):
        v = a[d]
        return float(v["score"] if isinstance(v, dict) else v)
    wa = sum(s(d) * w for d, w in WEIGHTS.items())
    if s("recovery_evidence") < GATEKEEPER_MIN and wa > GATEKEEPER_CAP:
        wa = GATEKEEPER_CAP
    return wa


def wilson_lower(k, n, z=1.96):
    """Wilson score interval lower bound for a proportion k/n."""
    if n == 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - margin) / denom


def spearman(xs, ys):
    """Spearman rank correlation (average-rank ties)."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    vx = math.sqrt(sum((r - mx) ** 2 for r in rx))
    vy = math.sqrt(sum((r - my) ** 2 for r in ry))
    return cov / (vx * vy) if vx and vy else 0.0


def _load(p):
    out = {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            r = json.loads(line)
            rid = r.get("id") or r.get("article_id")
            if rid:
                out[rid] = r
    return out


def _cohort_ids(gate_dir, fname, txt=False):
    p = gate_dir / fname
    if not p.exists():
        return set()
    if txt:
        return {l.strip() for l in open(p) if l.strip()}
    return {(json.loads(l).get("id") or json.loads(l).get("article_id"))
            for l in open(p) if l.strip()}


def run_gate(v2, v4, gate_dir, protection_probes=None):
    report = {"metrics": {}, "warnings": []}

    # cohorts
    decline = _cohort_ids(gate_dir, "nr_v4_heldout_ids.txt", txt=True)
    sourceA = _cohort_ids(gate_dir, "nr_v4_sourceA_reference.jsonl")

    def v4_surface(ids):
        return [surfacing_score(v4[i]) >= MEDIUM for i in ids if i in v4]

    # 1. probe-demotion: decline probes should NOT surface under v4
    dem = [not s for s in v4_surface(decline)]
    k, n = sum(dem), len(dem)
    lo = wilson_lower(k, n)
    report["metrics"]["probe_demotion"] = {
        "demoted": k, "n": n, "rate": (k / n if n else 0.0),
        "wilson_lower": lo, "pass": lo >= 0.90}

    # 2. over-demotion guard on Source-A: high_band_shift <= 0.05
    shifted = kept = 0
    for i in sourceA:
        if i in v2 and i in v4:
            if surfacing_score(v2[i]) >= MEDIUM:
                kept += 1
                if surfacing_score(v4[i]) < MEDIUM:
                    shifted += 1
    shift = shifted / kept if kept else 0.0
    report["metrics"]["over_demotion"] = {
        "high_band_shift": shift, "n_v2_high": kept, "pass": shift <= 0.05}

    # 3. protection-acceptance (#70): delivered-protection probes surface
    if protection_probes:
        prot = _cohort_ids(Path(protection_probes).parent, Path(protection_probes).name)
        surf = v4_surface(prot)
        ps, pn = sum(surf), len(surf)
        report["metrics"]["protection_acceptance"] = {
            "surfaced": ps, "n": pn, "rate": (ps / pn if pn else 0.0),
            "pass": (ps / pn if pn else 0.0) >= 0.70}
    else:
        report["metrics"]["protection_acceptance"] = {"pass": None, "status": "SKIPPED — no protection-probe cohort"}
        report["warnings"].append("Metric 3 SKIPPED: curate a delivered-protection probe set (--protection-probes); #70 postdates the frozen snapshot.")

    # 4. agreement (Spearman) on Source-A
    xs, ys = [], []
    for i in sourceA:
        if i in v2 and i in v4:
            xs.append(surfacing_score(v2[i])); ys.append(surfacing_score(v4[i]))
    rho = spearman(xs, ys)
    report["metrics"]["agreement_spearman"] = {"rho": rho, "n": len(xs), "pass": rho >= 0.6}

    if len(sourceA & set(v4)) > 10:  # Source-A largely in training
        report["warnings"].append("Source-A is ~93% inside the v4 training set — metrics 2/4 partly reflect memorization, not generalization.")

    passes = [m["pass"] for m in report["metrics"].values() if m.get("pass") is not None]
    report["overall_pass"] = all(passes) if passes else False
    return report


def main():
    ap = argparse.ArgumentParser(description="nature_recovery v4 agreement gate (NM#229)")
    ap.add_argument("--v2-scored", required=True)
    ap.add_argument("--v4-scored", required=True)
    ap.add_argument("--gate-dir", default="datasets/gate")
    ap.add_argument("--protection-probes", default=None)
    ap.add_argument("--report", default="filters/nature_recovery/v4/gate_report.json")
    args = ap.parse_args()

    rep = run_gate(_load(args.v2_scored), _load(args.v4_scored),
                   Path(args.gate_dir), args.protection_probes)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    print("\n" + ("GATE PASS" if rep["overall_pass"] else "GATE FAIL — do not deploy"))
    for w in rep["warnings"]:
        print("  ⚠️ " + w)


if __name__ == "__main__":
    main()
