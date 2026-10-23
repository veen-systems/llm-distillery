"""EXP-061 ($0): can a lower Mistral threshold, or a per-dimension remap, reproduce Gemini's pass/fail calls on belonging?
Fitted IN-SAMPLE on the canary set (Mistral M1-M3 mean vs Gemini's 6-run mean), which is the most favourable case: a
held-out set can only do worse in expectation. Bar: Gemini single run vs single run (B1-B6, all 15 pairs).
Usage (from the checkout): .venv/bin/python remap_check.py MISTRAL_RAW_DIR GEMINI_RUNS_DIR > remap_result.txt"""
import itertools, json, statistics as st, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from ground_truth import oracle_canary as oc  # noqa: E402

mraw, graw = Path(sys.argv[1]), Path(sys.argv[2])
b = json.load(open(ROOT / "config/canary/belonging.baseline.json"))
spec, op, g = oc.spec_for(ROOT / b["config"]), b["op"], oc._gate_module()
D = list(spec["dims"])


def dims(p):
    return {r["id"]: {d: (r["belonging_analysis"][d]["score"] if isinstance(r["belonging_analysis"][d], dict)
                          else r["belonging_analysis"][d]) for d in D}
            for r in map(json.loads, open(p)) if r.get("belonging_analysis")}


Ms = [dims(mraw / f"M{i}.jsonl") for i in (1, 2, 3)]
Bs = [dims(graw / f"B{i}.jsonl") for i in range(1, 7)]
ids = sorted(set.intersection(*(set(x) for x in Ms + Bs)))
M = {i: {d: st.fmean(x[i][d] for x in Ms) for d in D} for i in ids}
G = {i: {d: st.fmean(x[i][d] for x in Bs) for d in D} for i in ids}
Gwa = b["items"]

Bwa = [{i: g._wa(x[i], spec) for i in ids} for x in Bs]
pf = sorted(oc.compare(x, y, op)["flips"] for x, y in itertools.combinations(Bwa, 2))
print(f"items {len(ids)}; bar: Gemini single run vs single run, 15 pairs: flips max {max(pf)} mean {st.fmean(pf):.2f}")


def sweep(name, W):
    rs = sorted((sum((W[i] >= k / 100) != (Gwa[i] >= op) for i in ids), -k / 100) for k in range(100, 601, 5))
    f, t = rs[0][0], -rs[0][1]
    fp = sum(W[i] >= t and Gwa[i] < op for i in ids); fn = sum(W[i] < t and Gwa[i] >= op for i in ids)
    print(f"{name}: best threshold {t:.2f} (ties to the higher, ADR-023)  flips {f}  "
          f"(Mistral passes / Gemini blocks {fp}; Mistral blocks / Gemini passes {fn})")


sweep("plain threshold on Mistral's weighted average", {i: g._wa(M[i], spec) for i in ids})
maps = {}
for d in D:
    x = np.array([M[i][d] for i in ids]); y = np.array([G[i][d] for i in ids])
    maps[d] = np.linalg.lstsq(np.vstack([x, np.ones_like(x)]).T, y, rcond=None)[0]
sweep("per-dimension linear remap, then threshold",
      {i: g._wa({d: min(10, max(0, maps[d][0] * M[i][d] + maps[d][1])) for d in D}, spec) for i in ids})
print("remap slope/intercept per dimension: " + ", ".join(f"{d} {maps[d][0]:.2f}/{maps[d][1]:+.2f}" for d in D))
