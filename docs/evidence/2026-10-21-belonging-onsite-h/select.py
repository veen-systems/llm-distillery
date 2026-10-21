"""EXP-056 step 3: per build, the first 30 v3 cards in page order; split ids into REUSED (an earlier lab belonging
tag exists) and NEW; draw the 10-id determinism control with random.Random(0) over the sorted reused set.

    python3 select.py <top60.json> <rows.jsonl> <outdir>

Writes <outdir>/selection.json, <outdir>/tag/input.jsonl (new ids), <outdir>/tag-control/input.jsonl (10 reused),
<outdir>/reused.json (id -> earlier tag record, with its source file). Prints counts only, never a tag.
"""
import glob, json, os, random, sys
top60, rows_path, out = sys.argv[1:4]
LAB = os.path.expanduser("~/lab/llm-distillery/experiments")
pages = json.load(open(top60))
rows = {r["id"]: r for r in map(json.loads, open(rows_path))}
sel = {}
for b, ids in sorted(pages.items()):
    v3 = [i for i in ids if (rows.get(i) or {}).get("version") == "3.0"]
    cut = ids.index(v3[29]) + 1 if len(v3) >= 30 else len(ids)     # page positions the top 30 v3 rows span
    skipped = {}
    for i in ids[:cut]:
        v = (rows.get(i) or {}).get("version")
        if v != "3.0":
            skipped[str(v)] = skipped.get(str(v), 0) + 1
    sel[b] = {"top30": v3[:30], "N": min(30, len(v3)), "skipped": skipped}
want = sorted({i for s in sel.values() for i in s["top30"]})
earlier = {}
for f in sorted(glob.glob(f"{LAB}/*belonging*/**/out.jsonl", recursive=True)):
    if "2026-10-21-belonging-onsite-h" in f:
        continue
    for r in map(json.loads, open(f)):
        earlier.setdefault(r["id"], dict(r, _file=os.path.relpath(f, LAB)))
reused = {i: earlier[i] for i in want if i in earlier}
new = [i for i in want if i not in earlier]
control = random.Random(0).sample(sorted(reused), min(10, len(reused)))
os.makedirs(f"{out}/tag", exist_ok=True); os.makedirs(f"{out}/tag-control", exist_ok=True)
def dump(path, ids):
    with open(path, "w") as fh:
        for i in ids:
            fh.write(json.dumps({"id": i, "title": rows[i]["title"], "content": rows[i]["content"]}, ensure_ascii=False) + "\n")
dump(f"{out}/tag/input.jsonl", new); dump(f"{out}/tag-control/input.jsonl", control)
json.dump(sel, open(f"{out}/selection.json", "w"), indent=1)
json.dump(reused, open(f"{out}/reused.json", "w"), indent=1, ensure_ascii=False)
print(f"builds {len(sel)}, N per build {[s['N'] for s in sel.values()]}; top-30 ids {len(want)}: reused {len(reused)}, new {len(new)}; control {len(control)}")
