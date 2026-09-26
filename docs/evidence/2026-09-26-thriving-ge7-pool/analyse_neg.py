"""Hard negatives (PLAN.md § Hard negatives, fixed before any call): 473 not-in-scope pool rows,
k=3 oracle with prompt-v8-4; every dimension capped at 2.0 whatever the oracle says. Reports the
oracle's own leak: k=3 majority in_scope, and uncapped weighted >= 4.5. Writes neg_labels.jsonl."""
import collections, json, statistics, sys
from pathlib import Path
X = Path(__file__).resolve().parent
sys.path.insert(0, str(X.parents[2] / "scripts" / "gate"))
import adverse_suite_gate as G  # noqa: E402
ids = [json.loads(l)["id"] for l in open(X / "oracle_neg_input.jsonl")]
per = collections.defaultdict(list)
for k in (1, 2, 3):
    seen = set()
    for line in open(X / "runs" / f"neg_{k}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if "human_thriving_analysis" not in r:
            continue
        if r["id"] in seen:
            G.fatal(f"FATAL: neg_{k}: {r['id']} twice")
        seen.add(r["id"]); a = r["human_thriving_analysis"]
        if a.get("prompt_hash") != "c4705408c477":
            G.fatal(f"FATAL: prompt hash {a.get('prompt_hash')}")
        per[r["id"]].append(a)
missing = [i for i in ids if len(per.get(i, [])) != 3]
kept, leak, leak45 = [], 0, 0
for i in ids:
    if i in missing:
        continue
    rs = per[i]
    votes = collections.Counter(a.get("scope_verdict") for a in rs)
    raw = [statistics.fmean(float(a[d]["score"]) for a in rs) for d in G.DIMS]
    w = G.weighted_average(dict(zip(G.DIMS, raw)))
    leak += votes["in_scope"] >= 2; leak45 += w >= 4.5
    kept.append({"id": i, "labels": [min(v, 2.0) for v in raw], "dimension_names": list(G.DIMS),
                 "uncapped_weighted": w, "oracle_in_scope_votes": votes["in_scope"]})
with open(X / "neg_labels.jsonl", "w") as f:
    for r in kept:
        f.write(json.dumps(r) + "\n")
n = len(kept)
print(f"HARD NEGATIVES: {n} labelled (capped at 2.0), {len(missing)} excluded (not scored k=3)")
print(f"  oracle k=3 majority in_scope: {leak} ({leak/n:.1%}); uncapped weighted >= 4.5: {leak45} ({leak45/n:.1%})")
