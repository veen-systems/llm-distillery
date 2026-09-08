"""Recompute every number in this directory's README from the committed artifacts.

Run:  PYTHONPATH=. python3 docs/evidence/2026-09-08-v8-live-panel/decompose.py

THE CONTROL IS THE POINT. The DeepSeek full-prompt arm's in_scope count and its weighted
averages are recomputed here from the per-article dimension scores using the SHIPPED
scripts/gate/ground_truth_gate.py::_wa and the SHIPPED config.yaml — not from a stored
summary. If the aggregation in either repo drifts, this stops reproducing and says so.
"""
import json, math, collections, statistics, importlib.util
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]

s = importlib.util.spec_from_file_location("gtg", ROOT / "scripts/gate/ground_truth_gate.py")
gtg = importlib.util.module_from_spec(s); s.loader.exec_module(gtg)
SPEC = gtg.load_scoring_spec(ROOT / "filters/human_thriving/v8/config.yaml")
OP = gtg.load_medium_threshold(ROOT / "filters/human_thriving/v8/config.yaml")


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0., c - h), min(1., c + h)


def newcombe(k1, n1, k2, n2, z=1.96):
    l1, u1 = wilson(k1, n1, z); l2, u2 = wilson(k2, n2, z); d = k1 / n1 - k2 / n2
    return (d - math.sqrt((k1/n1 - l1)**2 + (u2 - k2/n2)**2),
            d + math.sqrt((u1 - k1/n1)**2 + (k2/n2 - l2)**2))


def mcnemar_exact(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n)


manifest = {json.loads(l)["id"]: json.loads(l) for l in open(HERE / "panel_manifest.jsonl")}
A = json.load(open(HERE / "deepseek_full_prompt_k6.json"))
B = {r["id"]: r["verdict"] for r in json.load(open(HERE / "deepseek_rubric_fulltext.json"))}
C = {r["id"]: r["verdict"] for r in json.load(open(HERE / "deepseek_rubric_trunc4000.json"))}
ids = sorted(A)
N = len(ids)

# --- CONTROL: the deployed weighted average must equal the gate's _wa on the same dims ---
drift = max(abs(gtg._wa(manifest[i]["scores"], SPEC) - manifest[i]["raw_weighted_average"])
            for i in ids)
assert drift < 1e-6, f"AGGREGATION DRIFT: gate _wa vs deployed raw differs by {drift}"
norm = max(abs(manifest[i]["weighted_average"] - manifest[i]["raw_weighted_average"]) for i in ids)

print(f"op-point {OP}   panel n={N} (63rd row dropped: GN + sub-300, see README)")
print(f"CONTROL  gate _wa(dims) vs deployed raw_weighted_average : max |diff| {drift:.9f}  PASS")
print(f"CONTROL  weighted_average == raw (no normalization.json)  : max |diff| {norm:.9f}\n")

insc = lambda d, i: d[i] == "in_scope"
kA = sum(1 for i in ids if A[i]["verdict"] == "in_scope")
kB = sum(1 for i in ids if insc(B, i)); kC = sum(1 for i in ids if insc(C, i))
scoreA = sum(1 for i in ids if A[i]["oracle_mean"] >= OP)

print("ARMS (all DeepSeek, deepseek-chat, prompt-v8-4.md sha256[:12]=c4705408c477 for A)")
for nm, k in [("A  full oracle prompt, full text (k=6)", kA),
              ("B  README rubric,      full text (k=1)", kB),
              ("C  README rubric,      4000 chars (k=1)", kC)]:
    lo, hi = wilson(k, N)
    print(f"  {nm:<40} {k}/{N} = {k/N:.4f}  Wilson [{lo:.3f}, {hi:.3f}]")
lo, hi = wilson(scoreA, N)
print(f"  A  score precision (k=6 mean >= {OP})        {scoreA}/{N} = {scoreA/N:.4f}  Wilson [{lo:.3f}, {hi:.3f}]")

print("\nPAIRED CONTRASTS (McNemar exact, same articles)")
for nm, X, Y in [("PROMPT      A vs B (text fixed)", {i: A[i]["verdict"] == "in_scope" for i in ids}, {i: insc(B, i) for i in ids}),
                 ("TRUNCATION  B vs C (prompt fixed)", {i: insc(B, i) for i in ids}, {i: insc(C, i) for i in ids})]:
    b = sum(1 for i in ids if X[i] and not Y[i]); c = sum(1 for i in ids if Y[i] and not X[i])
    print(f"  {nm:<34} b={b:2} c={c:2}  delta {sum(X.values())/N - sum(Y.values())/N:+.4f}  exact p = {mcnemar_exact(b,c):.4f}")

print("\nUNPAIRED (family; rubric+truncation fixed) vs NexusMind's judges on the same panel")
for nm, k2, n2 in [("Gemini 2.5 Flash", 51, 62), ("Claude", 41, 63)]:
    lo, hi = newcombe(kC, N, k2, n2)
    print(f"  DeepSeek(C) {kC}/{N} vs {nm:<18} {k2}/{n2}   diff {kC/N - k2/n2:+.4f}  Newcombe [{lo:+.4f}, {hi:+.4f}]")

print("\nBAND (student raw score at the op-point)")
band = lambda x: "[4.5,5.0)" if x < 5.0 else "[5.0,5.591]" if x <= 5.591 else "(5.591,6.129]"
for bnd in ["[4.5,5.0)", "[5.0,5.591]", "(5.591,6.129]"]:
    sel = [i for i in ids if band(A[i]["student_raw"]) == bnd]
    sc = sum(1 for i in sel if A[i]["oracle_mean"] >= OP)
    sp = sum(1 for i in sel if A[i]["verdict"] == "in_scope")
    print(f"  {bnd:<15} n={len(sel):2}   scope {sp:2}/{len(sel):2} = {sp/len(sel):.3f}   score {sc:2}/{len(sel):2} = {sc/len(sel):.3f}")

flips = [i for i in ids if A[i]["verdict"] == "in_scope" and not insc(B, i)]
print(f"\nPROMPT FLIPS ({len(flips)}): full oracle prompt says in_scope, README rubric does not")
for v, c in collections.Counter(B[i] for i in flips).most_common():
    print(f"    {c:3}  {v}")
print(f"  band: {dict(collections.Counter(band(A[i]['student_raw']) for i in flips))}")
print(f"  raw-score span of the 5 out_of_scope flips: "
      f"{min(A[i]['student_raw'] for i in flips if B[i]=='out_of_scope'):.3f}"
      f"-{max(A[i]['student_raw'] for i in flips if B[i]=='out_of_scope'):.3f}")

print("\nVS THE DEPLOY GATE (ADR-021, ground_truth_gate.json: scope 17/20, score 11/20)")
for nm, k, kg, ng in [("scope", kA, 17, 20), ("score", scoreA, 11, 20)]:
    lo, hi = newcombe(k, N, kg, ng)
    print(f"  {nm} precision  prod {k}/{N}={k/N:.4f}  gate {kg}/{ng}={kg/ng:.3f}  "
          f"Newcombe [{lo:+.3f}, {hi:+.3f}]  NOT DISTINGUISHABLE")
print("\nTHREE JUDGES, ONE PANEL  (spread 0.651 to 0.968)")
print("  Claude   k=1 README rubric  41/63 = 0.6508")
print("  Gemini   k=1 README rubric  51/62 = 0.8226")
print("  DeepSeek k=6 full prompt    60/62 = 0.9677")

sds = [A[i]["oracle_sd"] for i in ids]
print(f"\nk=6 STABILITY  rows with sd>1.0: {sum(1 for x in sds if x > 1.0)}   "
      f"max sd {max(sds):.3f}   median sd {statistics.median(sds):.3f}")
