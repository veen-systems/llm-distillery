#!/usr/bin/env python3
"""Within ONE cycle, does the same article reach different lenses at different lengths?

The euronews case: 294 chars for five lenses, 14,963 for uplifting -- the one lens
that scored it above the 4.0 post-scoring enrichment threshold. If that generalises,
five of six lenses are scoring a stub of an article that is actually full-length,
and the length a gate reads depends on WHICH LENS wrote the row.
"""
import glob
import json
import os
import re
from collections import defaultdict

NM = os.path.expanduser("~/local_dev/NexusMind")

# group batches into cycles by their timestamp prefix (same date, within ~30 min)
by_cycle = defaultdict(dict)   # cycle_key -> {(lens): path}
for path in glob.glob(os.path.join(NM, "data/filtered", "*", "filtered_*.jsonl")):
    m = re.search(r"filtered_(\d{8})_(\d{2})(\d{2})(\d{2})\.jsonl$", path)
    if not m:
        continue
    day, hh, mm, _ = m.groups()
    # bucket to the hour; a cycle's lens batches land within minutes
    key = f"{day}_{hh}"
    lens = os.path.basename(os.path.dirname(path))
    by_cycle[key][lens] = path

multi = {k: v for k, v in by_cycle.items() if len(v) >= 4}
print(f"cycles with >=4 lens batches: {len(multi)}")

tot_articles = tot_multi = tot_disagree = 0
big_gaps = []
for key in sorted(multi)[-8:]:                     # last 8 cycles
    lens_paths = multi[key]
    lengths = defaultdict(dict)                    # id -> {lens: len}
    for lens, path in lens_paths.items():
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
                if rid:
                    lengths[rid][lens] = len(r.get("content") or "")
    seen = [v for v in lengths.values() if len(v) >= 2]
    disagree = [v for v in seen if len(set(v.values())) > 1]
    tot_articles += len(lengths)
    tot_multi += len(seen)
    tot_disagree += len(disagree)
    for v in disagree:
        lo, hi = min(v.values()), max(v.values())
        if hi - lo > 1000:
            big_gaps.append((key, lo, hi, v))
    print(f"  cycle {key}: {len(lens_paths)} lenses, {len(seen)} articles in >=2 lenses, "
          f"{len(disagree)} with DIFFERENT lengths ({100*len(disagree)/max(len(seen),1):.1f}%)")

print()
print(f"TOTAL over those cycles: {tot_multi} articles seen by >=2 lenses, "
      f"{tot_disagree} disagree ({100*tot_disagree/max(tot_multi,1):.1f}%)")
print(f"of which gap > 1000 chars: {len(big_gaps)}")
for key, lo, hi, v in big_gaps[:5]:
    print(f"  cycle {key}: {lo} -> {hi}   {v}")
