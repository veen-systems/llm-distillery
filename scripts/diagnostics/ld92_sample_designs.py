#!/usr/bin/env python3
"""Draw the three LD#92 discriminating designs from the solutions v6 pool.

The n=60 harness behind LD#92's replication comment was never committed, so this
rebuilds the sampling half. The question it answers is the one the adversarial
review left open: is the -1.13 DiD a real length effect, or the selection
artifact that the review showed can fully reproduce it?

PRE-REGISTERED (written before any oracle call):

  D1  replication      short/long both at raw >= 2.25   (arm depth ratio 0.50)
  D2  second op-point  short/long both at raw >= 4.00   (arm depth ratio 0.19)
  D3  matched pctile   top 2.3% WITHIN each arm         (arm depth ratio 1.00)

  Selection artifact  => D2 MORE negative than D1 (depth diverges further),
                         D3 collapses toward 0 (depth equalised by construction).
  Real length effect  => D1 ~= D2 ~= D3 ~= -1.13.

D3 is the identification fix; D2 is the stability check. They fail differently,
which is why both are drawn.
"""
import json
import os
import random

POOL = os.path.expanduser("~/solutions_v6_pool.jsonl")
OUT_ARTICLES = os.path.expanduser("~/ld92_articles.jsonl")
OUT_DESIGN = os.path.expanduser("~/ld92_design.json")

SEED = 20260805
N_PER_ARM = 80  # oversampled from 60: is_scrape_junk drops the short arm harder
SHORT_MAX = 300

rows = [json.loads(l) for l in open(POOL)]
short_all = [r for r in rows if r["content_length"] < SHORT_MAX]
long_all = [r for r in rows if r["content_length"] >= SHORT_MAX]


def pctile_cut(vals, q):
    s = sorted(vals)
    return s[int(len(s) * (1 - q))]


# Hoisted: calling pctile_cut inside a comprehension's condition re-sorts the
# whole arm once per element.
CUT_SHORT_P23 = pctile_cut([x["raw"] for x in short_all], 0.023)
CUT_LONG_P23 = pctile_cut([x["raw"] for x in long_all], 0.023)
print(f"matched-percentile cuts (top 2.3% of each arm): short>={CUT_SHORT_P23:.3f} long>={CUT_LONG_P23:.3f}")

designs = {
    "D1_op2.25": {
        "short": [r for r in short_all if r["raw"] >= 2.25],
        "long": [r for r in long_all if r["raw"] >= 2.25],
        "note": "replication of the original design at solutions' deployed op-point",
    },
    "D2_op4.00": {
        "short": [r for r in short_all if r["raw"] >= 4.00],
        "long": [r for r in long_all if r["raw"] >= 4.00],
        "note": "second op-point; artifact predicts MORE negative here",
    },
    "D3_pct2.3": {
        "short": [r for r in short_all if r["raw"] >= CUT_SHORT_P23],
        "long": [r for r in long_all if r["raw"] >= CUT_LONG_P23],
        "note": "matched percentile depth; artifact predicts collapse toward 0",
    },
}

rng = random.Random(SEED)
membership = {}
chosen = {}
for dname, d in designs.items():
    chosen[dname] = {}
    for arm in ("short", "long"):
        pool = d[arm]
        take = rng.sample(pool, min(N_PER_ARM, len(pool)))
        chosen[dname][arm] = [r["id"] for r in take]
        for r in take:
            membership.setdefault(r["id"], r)
        print(f"{dname:11} {arm:5} pool={len(pool):6} drawn={len(take):3} "
              f"mean_raw={sum(x['raw'] for x in take)/len(take):.3f} "
              f"mean_len={sum(x['content_length'] for x in take)/len(take):7.1f}")

with open(OUT_ARTICLES, "w") as f:
    for r in membership.values():
        f.write(json.dumps({
            "id": r["id"], "title": r["title"], "content": r["content"],
            "source": r["source"], "published_date": r["published_date"],
            "language": r["language"],
        }, ensure_ascii=False) + "\n")

with open(OUT_DESIGN, "w") as f:
    json.dump({
        "seed": SEED, "n_per_arm": N_PER_ARM, "short_max_chars": SHORT_MAX,
        "designs": {k: {"note": v["note"], "pool_sizes": {a: len(v[a]) for a in ("short", "long")}}
                    for k, v in designs.items()},
        "membership": chosen,
        "meta": {r["id"]: {"raw": r["raw"], "content_length": r["content_length"],
                           "source": r["source"], "language": r["language"],
                           "cycle": r["cycle"]}
                 for r in membership.values()},
    }, f)

print(f"\nunique articles to score: {len(membership)}")
print(f"wrote {OUT_ARTICLES} and {OUT_DESIGN}")
