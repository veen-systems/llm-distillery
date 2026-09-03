"""Does the v8.1 prompt fix Gate B-A without moving the no-regression set?

Weights, the gatekeeper and the cap are IMPORTED from the production scorer. Each row's bar
is read off the row (`max_acceptable_wa` / `assertion`), never typed here.

Baselines are the ADOPTED v8 prompt (`prompt-candidate-tail.md`, hash 003cd35a5122):
  class A        docs/evidence/2026-09-01-v8-oracle-choice/runs/ds_{1,2,3}.jsonl
  no-regression  docs/evidence/2026-08-31-v8-no-regression-gate/runs/nr_A{1,2,3}.jsonl   (arm A)

⛔ Every arm asserts k == 3 per row. A silent k=1 is the 2026-08-23 defect.
⚠️ Baseline and treatment are DIFFERENT RUNS, so every delta carries oracle run-to-run noise.
   The relevant floor for this population is §1f's 0.82 mean / 2.25 max, NOT #95's 0.16.
"""
import json, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
# ⛔ The 2026-08-31 baseline ran with `--config filters/uplifting/v7/config.yaml`, so its
# analysis field is `uplifting_analysis`. Same six dimensions, different key. Resolve per row
# and RAISE when neither is present -- never fall back to an empty dict.
FIELDS = ("human_thriving_analysis", "uplifting_analysis")


def analysis(row, path):
    for f in FIELDS:
        if f in row:
            return row[f]
    raise SystemExit(f"FATAL: {path.name} row {row.get('id')!r} has none of {FIELDS}")

NOISE_MEAN, NOISE_MAX = 0.82, 2.25          # §1f, this population, oracle decoder

ROLES = json.load(open(HERE / "gate_roles.json", encoding="utf-8"))


def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


def load(paths, label):
    out = defaultdict(list)
    hashes = set()
    for p in paths:
        if not p.exists():
            sys.exit(f"FATAL: {label} baseline missing: {p}")
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            a = analysis(r, p)
            hashes.add(a.get("prompt_hash", "__absent__"))
            out[r["id"]].append((wavg({d: a[d]["score"] for d in DIMS}),
                                 a.get("scope_verdict", "__absent__")))
    for rid, runs in out.items():
        if len(runs) != 3:
            sys.exit(f"FATAL: {label} {rid}: k={len(runs)}, not 3 — a silent k=1 is the 08-23 defect")
    return out, hashes


ARM = sys.argv[1] if len(sys.argv) > 1 else "v81b"
treat, t_hash = load([HERE / "runs" / f"{ARM}_{i}.jsonl" for i in (1, 2, 3)], ARM)
base_a, ba_hash = load([REPO / "docs/evidence/2026-09-01-v8-oracle-choice/runs" / f"ds_{i}.jsonl"
                        for i in (1, 2, 3)], "class-A v8")
base_n, bn_hash = load([REPO / "docs/evidence/2026-08-31-v8-no-regression-gate/runs" / f"nr_A{i}.jsonl"
                        for i in (1, 2, 3)], "no-regression v8 arm A")

print(f"treatment prompt_hash {sorted(t_hash)}   baseline hashes {sorted(ba_hash | bn_hash)}")
if len(t_hash) != 1:
    sys.exit(f"FATAL: treatment mixes prompt hashes: {t_hash}")
print(f"rows scored {len(treat)}   k=3 asserted on every arm\n")

base = {**base_a, **base_n}
missing = [i for i in treat if i not in base]
if missing:
    sys.exit(f"FATAL: {len(missing)} treatment row(s) have no baseline: {missing}")

results = {"classA": [], "no_regression": []}
for rid, runs in sorted(treat.items(), key=lambda kv: ROLES[kv[0]]["role"]):
    role = ROLES[rid]["role"]
    m = statistics.fmean(w for w, _ in runs)
    b = statistics.fmean(w for w, _ in base[rid])
    results[role].append((rid, b, m, runs, base[rid]))

print("=" * 108)
print("GATE B-A — class A, every row must score BELOW its own editorial bar (a k=3 mean)")
print("=" * 108)
npass = nbase = 0
for rid, b, m, runs, bruns in results["classA"]:
    bar = float(ROLES[rid]["bar"])
    ok, okb = m < bar, b < bar
    npass += ok; nbase += okb
    moved = "" if abs(m - b) < NOISE_MEAN else ("  ↓MOVED" if m < b else "  ↑MOVED")
    print(f"  {'PASS' if ok else 'FAIL'}  v8.1 {m:5.3f} (v8 {b:5.3f}, Δ {m-b:+.3f}){moved}  bar {bar}")
    print(f"        runs {' '.join(f'{w:5.2f}' for w, _ in runs)}  "
          f"{'/'.join(v[:9] for _, v in runs):34} {ROLES[rid]['title'][:46]}")
print(f"\n  -> Gate B-A under v8.1: {npass}/{len(results['classA'])}     under v8: {nbase}/{len(results['classA'])}")

print("\n" + "=" * 108)
print("NEGATIVE CONTROL — the no-regression set must NOT move")
print("=" * 108)
for rid, b, m, runs, bruns in results["no_regression"]:
    d = m - b
    flag = "ok" if abs(d) < NOISE_MEAN else "⛔ MOVED BEYOND THE DECODER FLOOR"
    print(f"  v8.1 {m:5.3f} (v8 {b:5.3f}, Δ {d:+.3f})  {flag}")
    print(f"        runs {' '.join(f'{w:5.2f}' for w, _ in runs)}  "
          f"{'/'.join(v[:9] for _, v in runs):34} {ROLES[rid]['title'][:46]}")
    if ROLES[rid].get("assertion"):
        print(f"        assertion: {ROLES[rid]['assertion'][:88]}")

vc = Counter(v for _, runs, in [(0, r) for r in [x[3] for x in results['classA']]] for _, v in runs)
print(f"\nclass-A verdicts under v8.1: {dict(vc)}")
print(f"⚠️ Δ carries oracle run-to-run noise: {NOISE_MEAN} mean / {NOISE_MAX} max for this population (§1f).")
