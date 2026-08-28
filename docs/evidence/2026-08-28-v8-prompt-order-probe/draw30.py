"""Draw a 30-article probe cohort from the uplifting archive, on the box that holds it.

Exclusions are the plan's, not chosen here:
  - news.google.com  (sub-300-char headline echoes; never oracle-re-score -- CLAUDE.md)
  - content < 300 chars (the oracle floor, ground_truth.batch_scorer, #93)
  - stage_used != stage2 (a stage1_low score is an e5 PROBE estimate, not a Gemma score)
Stratified across the v7 score range so a label-parity check has rows where a
disagreement would actually change a decision, not only easy ones.
"""
import json, glob, random, re, sys
from collections import defaultdict

FILES = sorted(glob.glob("/home/jeroen/local_dev/NexusMind/data/filtered/uplifting/filtered_*.jsonl"))[-6:]
BANDS = [(0.0,2.5,6),(2.5,4.0,6),(4.0,4.5,4),(4.5,5.5,8),(5.5,10.1,6)]   # 30, weighted to the op-point
rng = random.Random(20260828)

def domain(u):
    m = re.match(r"https?://([^/]+)", u or "")
    return m.group(1).lower().replace("www.","") if m else ""

pool = defaultdict(list); seen = set(); stats = defaultdict(int)
for fp in FILES:
    for line in open(fp, encoding="utf-8"):
        try: r = json.loads(line)
        except Exception: stats["unparsable"] += 1; continue
        stats["rows"] += 1
        if r.get("id") in seen: stats["dup_id"] += 1; continue
        if domain(r.get("url")) == "news.google.com": stats["excl_gn"] += 1; continue
        if len(r.get("content") or "") < 300: stats["excl_short"] += 1; continue
        # NOT top-level: the scorer's output is nested per lens. Reading these off the
        # row root returns None for every article and the draw silently empties.
        u = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
        if not u: stats["excl_no_lens_block"] += 1; continue
        if u.get("stage_used") != "stage2": stats["excl_stage1"] += 1; continue
        wa = u.get("raw_weighted_average")
        if wa is None: stats["excl_no_score"] += 1; continue
        seen.add(r["id"])
        r["_v7_wa"], r["_v7_stage"] = wa, u.get("stage_used")
        for lo, hi, _ in BANDS:
            if lo <= wa < hi: pool[(lo,hi)].append(r); break
        stats["eligible"] += 1

out = []
for lo, hi, n in BANDS:
    have = pool[(lo,hi)]
    if len(have) < n:
        print(json.dumps({"stats": dict(stats),
                          "band_pool": {f"{a}-{b}": len(pool[(a,b)]) for a,b,_ in BANDS}}),
              file=sys.stderr)
        print(f"FATAL: band {lo}-{hi} has {len(have)} eligible, need {n}", file=sys.stderr)
        raise SystemExit(2)          # missing case RAISES, never returns a short draw
    out += rng.sample(have, n)

print(json.dumps({"files": len(FILES), "window": [FILES[0].split('/')[-1], FILES[-1].split('/')[-1]],
                  "stats": dict(stats),
                  "band_pool": {f"{lo}-{hi}": len(pool[(lo,hi)]) for lo,hi,_ in BANDS},
                  "drawn": len(out)}), file=sys.stderr)
for r in out:
    print(json.dumps({k: r.get(k) for k in
        ("id","title","content","url","source","published_date","language")}
        | {"v7_raw_weighted_average": r["_v7_wa"],
           "v7_stage_used": r["_v7_stage"]}, ensure_ascii=False))
