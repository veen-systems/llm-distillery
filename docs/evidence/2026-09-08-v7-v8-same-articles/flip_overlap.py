"""Are EXP-029's 12 prompt flips what separates v8 from v7, or what they agree on?

Reads the sibling evidence directory's arm files and this one's union manifest. No API calls.

    python3 docs/evidence/2026-09-08-v7-v8-same-articles/flip_overlap.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(os.path.dirname(HERE), "2026-09-08-v8-live-panel")

A = json.load(open(os.path.join(PANEL, "deepseek_full_prompt_k6.json")))
B = {r["id"]: r for r in json.load(open(os.path.join(PANEL, "deepseek_rubric_fulltext.json")))}
man = {}
for line in open(os.path.join(HERE, "union_manifest.jsonl")):
    r = json.loads(line)
    assert r["id"] not in man, f"id {r['id']} appears twice in the manifest"
    man[r["id"]] = r

flips = [i for i in A if A[i]["verdict"] == "in_scope" and B.get(i, {}).get("verdict") != "in_scope"]
assert len(flips) == 12, f"EXP-029 recorded 12 prompt flips, recomputed {len(flips)}"

panel_cycle = "c1"  # filtered_20260907_180414 == the EXP-029 panel
by_set = {}
for i in flips:
    r = man.get(i)
    by_set.setdefault(r["set"] if r else "not_surfaced_by_either", []).append(i)

print(f"EXP-029 prompt flips (arm A in_scope, arm B not): {len(flips)}")
for s in sorted(by_set):
    print(f"  {s}: {len(by_set[s])}")
    if s == "not_surfaced_by_either":
        print(f"    (not in the manifest, so no scores to print: {sorted(by_set[s])})")
        continue
    for i in sorted(by_set[s], key=lambda i: -man[i]["v8_raw"]):
        r = man[i]
        print(f"    v8 {r['v8_raw']:.3f} / v7 {r['v7_raw']:.3f}  {r['title'][:66]}")

v8only_all = [i for i, r in man.items() if r["set"] == "v8_only"]
# ⛔ The denominators are PANEL membership, not manifest membership. A flip is only defined for
# a row the panel judged, and the panel is 62 of the cycle's 63 passers (one Google News row was
# dropped, #93). Using the manifest's 57 `both` rows instead of the panel's 56 silently mixes a
# judged population with an unjudged one.
v8only_c1 = [i for i in v8only_all if man[i]["cycle"] == panel_cycle and i in A]
both_c1 = [i for i, r in man.items()
           if r["set"] == "both" and r["cycle"] == panel_cycle and i in A]
assert len(v8only_c1) + len(both_c1) == len(A), (
    f"panel is {len(A)} rows but the manifest accounts for "
    f"{len(v8only_c1)} + {len(both_c1)} of them")
hit = sorted(set(flips) & set(v8only_all))
print(f"\nv8-only rows overall: {len(v8only_all)}; in the panel cycle {panel_cycle}: {len(v8only_c1)}")
print(f"v8-only rows that are prompt flips: {len(hit)} -> {hit}")
print(f"prompt flips in the 'both' set (v7 surfaces them too): {len(by_set.get('both', []))} of 12")

# ⛔ THE COUNTS ARE NOT THE COMPARISON. The panel is 62 rows, ALL in the panel cycle, and the two
# sets it splits into have wildly different sizes -- so "10 in both vs 2 in v8-only" is a
# statement about set sizes, not about which set flips more. The first version of this file drew
# a conclusion from the counts; on RATES the point estimate points the other way and n cannot
# settle it. Review, 2026-09-08.
n_v8, n_both = len(v8only_c1), len(both_c1)
f_v8, f_both = len(hit), len(by_set.get("both", []))
print(f"\nRATES within the panel cycle (the counts above are NOT comparable -- different denominators):")
print(f"  v8-only: {f_v8}/{n_v8} = {f_v8/n_v8*100:.1f}%")
print(f"  both:    {f_both}/{n_both} = {f_both/n_both*100:.1f}%")
print(f"  ratio {(f_v8/n_v8)/(f_both/n_both):.2f}x -- flips are ENRICHED among v8-only rows, the")
print(f"  OPPOSITE of what the raw counts suggest, and n={n_v8} cannot establish it either way.")
try:
    from scipy.stats import fisher_exact
    p = fisher_exact([[f_v8, n_v8 - f_v8], [f_both, n_both - f_both]])[1]
    print(f"  Fisher exact two-sided p = {p:.3f} -- not distinguishable.")
except ImportError:
    print("  (scipy absent; Fisher test skipped)")
print("\nReading, corrected: the panel CANNOT say whether the owed prompt work is what separates"
      "\nthe lenses -- 6 v8-only rows is too few. What it does establish is that 10 of the 12 flips"
      "\nare articles v7 surfaces too, so a corrected scope in a v8.1 would remove rows from v8's"
      "\npasser set that v7 keeps until cutover: the supply gap widens. Direction only; no retrain"
      "\nhas been run, and the rate comparison above is underpowered.")
