#!/usr/bin/env python3
"""Trace one article's content length across every cycle it appears in.

Settles whether a scoring-vs-publication length gap means "the content changed
downstream" or "the same article was seen twice at different times". Those imply
opposite gate placements.
"""
import glob
import json
import os
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "global_news_euronews_0111e7cdda7d"
NM = os.path.expanduser("~/local_dev/NexusMind")

hits = []
for path in glob.glob(os.path.join(NM, "data/filtered", "*", "filtered_*.jsonl")):
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        continue
    with fh:
        for line in fh:
            if TARGET not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("id") != TARGET:
                continue
            lens = os.path.basename(os.path.dirname(path))
            batch = os.path.basename(path)
            a = (r.get("nexus_mind_attributes") or {}).get(lens) or {}
            hits.append((batch, lens, len(r.get("content") or ""),
                         a.get("content_length"), a.get("raw_weighted_average")))

hits.sort()
print(f"{TARGET}: {len(hits)} appearance(s)\n")
print(f"  {'batch':<34}{'lens':<20}{'len(content)':>13}{'stamp':>8}{'raw':>8}")
for batch, lens, blen, stamp, raw in hits:
    raw_s = f"{raw:.2f}" if isinstance(raw, (int, float)) else "-"
    print(f"  {batch:<34}{lens:<20}{blen:>13}{str(stamp):>8}{raw_s:>8}")
