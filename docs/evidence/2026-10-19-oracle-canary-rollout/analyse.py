"""#177 rollout (EXP-053): every figure in README.md, recomputed from the lab copies under the pre-registered rule.

    PYTHONPATH=. python docs/evidence/2026-10-19-oracle-canary-rollout/analyse.py > docs/evidence/2026-10-19-oracle-canary-rollout/result.txt
"""
import json
import os
from pathlib import Path

from ground_truth import oracle_canary as oc

LAB = Path(os.environ.get("LD_LAB", Path.home() / "lab" / "llm-distillery")).expanduser()
X = LAB / "experiments/2026-10-19-oracle-canary-rollout"
FILTERS = ["cultural_discovery", "nature_recovery", "solutions", "belonging"]

for f in FILTERS:
    b = json.load(open(oc.CONFIG_DIR / f"{f}.baseline.json"))
    spec, op = oc.spec_for(b["config"]), b["op"]
    field = next(k for k in json.loads(open(X / f"runs/{f}/B1.jsonl").readline()) if k.endswith("_analysis"))
    runs, stamps = {}, {}
    for r in ["B1", "B2", "B3", "B4", "B5", "B6", "P1", "P2", "P3"]:
        runs[r], stamps[r] = oc.run_scores(X / f"runs/{f}/{r}.jsonl", spec, field)
    B = [runs[f"B{i}"] for i in range(1, 7)]
    nz, base = oc.noise(B, op), oc.mean_scores(B)
    assert {i: round(s, 4) for i, s in base.items()} == b["items"], f"{f}: lab runs do not reproduce the baseline"
    print(f"== {f}  op {op}  oracle {b['oracle']}  served {b['served_model']}")
    print(f"   items scored per run {[len(runs[r]) for r in runs]}")
    print(f"   served per run {[sorted({m for _, m in stamps[r]}) for r in runs]}")
    print(f"   B prompt {sorted({s for s, _ in set().union(*(stamps[f'B{i}'] for i in range(1, 7)))})}")
    print(f"   P prompt {sorted({s for s, _ in set().union(*(stamps[f'P{i}'] for i in range(1, 4)))})}")
    print(f"   baseline items >= op {sum(v >= op for v in base.values())}/100, within 0.5 of op "
          f"{sum(abs(v - op) < 0.5 for v in base.values())}")
    for k in ("k1", "k3"):
        print(f"   noise {k}: F={nz[k]['F']} S={nz[k]['S']:.4f}  each "
              + " ".join(f"{c['flips']}/{c['shift']:+.4f}" for c in nz[k]["each"]))
    bar1, bar3 = nz["k1"], nz["k3"]
    print(f"   k=1 FAIL bar: flips > {bar1['F'] + oc.FLIP_MARGIN} or |shift| > {bar1['S'] + oc.SHIFT_MARGIN:.4f}")
    print(f"   k=3 FAIL bar: flips > {bar3['F'] + oc.FLIP_MARGIN} or |shift| > {bar3['S'] + oc.SHIFT_MARGIN:.4f}")
    v1 = []
    for r in ("P1", "P2", "P3"):
        c = oc.compare(runs[r], base, op)
        v1.append(oc.verdict(c, bar1))
        why = [w for w, hit in (("flips", c["flips"] > bar1["F"] + oc.FLIP_MARGIN),
                                ("shift", abs(c["shift"]) > bar1["S"] + oc.SHIFT_MARGIN)) if hit]
        print(f"   {r}: flips {c['flips']} shift {c['shift']:+.4f} -> {v1[-1]} on {'+'.join(why) or '-'}")
    c3 = oc.compare(oc.mean_scores([runs[r] for r in ("P1", "P2", "P3")]), base, op)
    v3 = oc.verdict(c3, nz["k3"])
    print(f"   P triple: flips {c3['flips']} shift {c3['shift']:+.4f} -> k3 {v3}")
    smallest = min(abs(oc.compare(runs[r], base, op)["shift"]) for r in ("P1", "P2", "P3"))
    print(f"   margin: smallest |P shift| / k=1 shift bar = {smallest / (bar1['S'] + oc.SHIFT_MARGIN):.2f}; "
          f"k=1 shift bar / |P triple shift| = {(bar1['S'] + oc.SHIFT_MARGIN) / abs(c3['shift']):.2f}")
    ship = 1 if v1 == ["FAIL"] * 3 else 3 if v3 == "FAIL" else None
    print(f"   rule: k = {ship} ships (None = nothing ships); baseline k_ship {b['k_ship']}")
    rec = [json.load(open(p)) for p in sorted((X / "l1").glob(f"{b['prompt_sha256'][:16]}_*.json"))]
    for r in rec:
        print(f"   L1 record {r.get('verdict')} flips {r.get('flips')} shift {r.get('shift')} k {r.get('k')}")
