#!/usr/bin/env python3
"""WHICH LENGTH DO YOU CHECK? Does content change between scoring and publication?

NexusMind stamps content_length at scoring time (after its own pre_enrich).
ovr.news runs its own enrichment before summarising. If the two disagree, a gate
written against one stage is silently measuring the other.

Uses EVERY filtered batch (not just the latest) so the overlap with ovr.db is
large enough to answer the question rather than gesture at it.
"""
import glob
import json
import os
import sqlite3
from collections import Counter

NM = os.path.expanduser("~/local_dev/NexusMind")
OVR = os.path.expanduser("~/local_dev/ovr.news")
LENSES = ("uplifting", "investment_risk", "nature_recovery", "solutions",
          "belonging", "cultural_discovery")

scored = {}       # id -> content_length stamped at scoring time
stamp_missing = 0
for lens in LENSES:
    for path in sorted(glob.glob(os.path.join(NM, "data/filtered", lens, "filtered_*.jsonl"))):
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                rid = r.get("id")
                if not rid:
                    continue
                a = (r.get("nexus_mind_attributes") or {}).get(lens) or {}
                cl = a.get("content_length")
                if cl is None:
                    # pre-2026-08-08 rows: fall back to the row's own content
                    body = r.get("content")
                    if body is None:
                        stamp_missing += 1
                        continue
                    cl = len(body)
                # keep the most recent observation for an id
                scored[rid] = cl

print(f"distinct scored ids collected : {len(scored)}")
print(f"rows skipped (no stamp, no body): {stamp_missing}")

db = sqlite3.connect(os.path.join(OVR, "data/ovr.db"))
published = {r[0] for r in db.execute("SELECT id FROM live_articles")}

ids = list(scored)
same = diff = 0
grew = shrank = 0
grew_pub = shrank_pub = 0
examples = []
crossings = Counter()   # short at one stage, not the other
for i in range(0, len(ids), 900):
    chunk = ids[i:i + 900]
    q = ",".join("?" * len(chunk))
    for rid, ovrlen in db.execute(
        f"SELECT id, LENGTH(content) FROM articles WHERE id IN ({q})", chunk
    ):
        s = scored[rid]
        if ovrlen is None:
            continue
        if ovrlen == s:
            same += 1
        else:
            diff += 1
            if ovrlen > s:
                grew += 1
                if rid in published:
                    grew_pub += 1
            else:
                shrank += 1
                if rid in published:
                    shrank_pub += 1
            if len(examples) < 8:
                examples.append((rid, s, ovrlen, rid in published))
        # would a 300-char gate disagree between the two stages?
        if (s < 300) != (ovrlen < 300):
            crossings[("short at scoring, long at publish") if s < 300
                      else ("long at scoring, short at publish")] += 1

matched = same + diff
print(f"matched into ovr.db           : {matched}")
if matched:
    print(f"  identical length at both    : {same}  ({100*same/matched:.1f}%)")
    print(f"  DIFFERENT                   : {diff}  ({100*diff/matched:.1f}%)"
          f"   grew {grew} (published {grew_pub}), shrank {shrank} (published {shrank_pub})")
print()
print("--- would a 300-char gate give a different answer depending on stage? ---")
if not crossings:
    print("  NO crossings: every matched article is on the same side of 300 at both stages")
for k, v in crossings.items():
    print(f"  {k}: {v}")
print()
for rid, s, o, pub in examples:
    print(f"  {rid[:44]:<46} scoring={s:<7} ovr.db={o:<7} {'PUBLISHED' if pub else ''}")
