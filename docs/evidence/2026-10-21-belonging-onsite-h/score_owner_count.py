"""Score the owner's blind P/G letters for the 10-18 page against the three taggers (qwen, Fable, Mistral).
usage: python3 score_owner_count.py <lab experiments/2026-10-21-belonging-onsite-h>"""
import json, re, sys, os
E = sys.argv[1]
sheet = open(os.path.join(E, "owner_count_20261018.md")).read()
rows = re.findall(r"^\| (\d+) \| ([PG]) \| .*?artikel/(\S+?) \|", sheet, flags=re.M)
assert len(rows) == 30, len(rows)
sel = json.load(open(os.path.join(E, "selection/selection.json")))["20261018"]["top30"]
assert [r[2] for r in rows] == sel, "sheet order differs from the 10-18 top 30"
own = {i: ("personal" if c == "P" else "group") for _, c, i in rows}
def load(p): return {json.loads(l)["id"]: json.loads(l)["focus"] for l in open(os.path.join(E, p))}
qwen = {k: v["focus"] for k, v in json.load(open(os.path.join(E, "selection/reused.json"))).items()}
qwen.update(load("run/tag/out.jsonl"))
tags = {"qwen": qwen, "fable": load("run/tag-fable/out.jsonl"), "mistral": load("run/tag-mistral/out.jsonl")}
print("owner letters:", "".join(c for _, c, _ in rows))
print(f"owner personal: {sum(v == 'personal' for v in own.values())} of 30")
missed = {}
for m, t in tags.items():
    fn = [int(n) for n, _, i in rows if own[i] == "personal" and t[i] == "group"]
    fp = [int(n) for n, _, i in rows if own[i] == "group" and t[i] == "personal"]
    missed[m] = set(fn)
    print(f"{m}: personal {sum(t[i] == 'personal' for i in sel)}; agree {sum(t[i] == own[i] for i in sel)}/30; "
          f"owner P, {m} G: rows {fn}; owner G, {m} P: rows {fp}")
common = sorted(set.intersection(*missed.values()))
print(f"owner P rows that all three taggers call G: {len(common)}, rows {common}")
