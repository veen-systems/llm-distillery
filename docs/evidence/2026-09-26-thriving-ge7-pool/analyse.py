"""Step 1 of PLAN.md: validate every out_* against its input, drift check A vs B (stop < 0.90),
tie rule (A/B split -> not in scope), in-scope yield per filter set (design-weighted; never pooled)."""
import json, glob, collections, sys
V = {"in_scope", "out_of_scope", "harm_is_subject", "response_to_harm", "no_person_benefits", "cannot_judge"}
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
problems = []
verdict = {"A": {}, "B": {}}
for inp in sorted(glob.glob("input_[AB]*.jsonl")):
    out = inp.replace("input_", "out_")
    ins, outs = load(inp), load(out)
    if [r["id"] for r in ins] != [r["id"] for r in outs]:
        problems.append(f"{out}: ids/order differ from input"); continue
    for i, o in zip(ins, outs):
        if set(o) != {"id", "verdict", "quote", "reason"}: problems.append(f"{out} {o['id']}: keys {sorted(o)}")
        if o["verdict"] not in V: problems.append(f"{out} {o['id']}: verdict {o['verdict']}")
        q = o["quote"]
        if o["verdict"] != "cannot_judge" and (not q or (q not in i["content"] and q not in (i["title"] or ""))):
            problems.append(f"{out} {o['id']}: quote not in article")
        verdict[inp[6]][o["id"]] = o["verdict"]
print("validation problems:", len(problems)); [print("  ", p) for p in problems]
B = verdict["B"]; A = verdict["A"]
agree = sum((A[i] == "in_scope") == (B[i] == "in_scope") for i in B)
drift = agree / len(B)
print(f"pass A rows {len(A)} | drift A vs B (binary) {agree}/{len(B)} = {drift:.3f}  (stop below 0.90) -> {'PASS' if drift >= 0.90 else 'STOP'}")
final = {i: ("in_scope" if v == "in_scope" and B.get(i, "in_scope") == "in_scope" else ("split" if v == "in_scope" or B.get(i) == "in_scope" else v)) for i, v in A.items()}
print("A/B splits (tie rule -> not in scope):", sum(v == "split" for v in final.values()))
pool = {json.loads(l)["id"]: json.loads(l) for l in open("pool.jsonl")}
by = collections.defaultdict(lambda: [0, 0])
for i, v in final.items():
    k = "+".join(sorted(pool[i]["hits"])); by[k][1] += 1; by[k][0] += v == "in_scope"
for k, (a, n) in sorted(by.items()): print(f"  {k:22s} {a:3d} / {n:3d} = {a/n:.1%}")
ins_ = sorted(i for i, v in final.items() if v == "in_scope")
print("in scope total:", len(ins_), "| verdicts:", dict(collections.Counter(final.values())))
json.dump(ins_, open("in_scope_ids.json", "w"), indent=0)
