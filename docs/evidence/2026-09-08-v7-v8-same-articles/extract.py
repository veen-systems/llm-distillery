"""Extract compact per-article scoring records from NexusMind filtered_*.jsonl.

Runs ON sadalsuud. Emits one JSON line per (cycle, filter, article) with only the
fields the v7-vs-v8 comparison needs. Raises on a missing filter block rather than
returning None (working rule: make the missing case raise).
"""
import json
import os
import sys

BASE = "/home/jeroen/local_dev/NexusMind/data/filtered"

# (cycle_label, uplifting_file, human_thriving_file) — paired by collection cycle,
# NOT by filename timestamp: each filter stamps the moment IT finished.
PAIRS = [
    ("c1", "filtered_20260907_175421.jsonl", "filtered_20260907_180414.jsonl"),
    ("c2", "filtered_20260907_212528.jsonl", "filtered_20260907_213122.jsonl"),
    ("c3", "filtered_20260908_012236.jsonl", "filtered_20260908_012812.jsonl"),
    ("c4", "filtered_20260908_052700.jsonl", "filtered_20260908_053231.jsonl"),
]

KEEP_ATTR = (
    "version passed_prefilter prefilter_reason weighted_average raw_weighted_average "
    "normalization_method tier stage_used stage1_estimate gatekeeper_applied cap_applied "
    "content_length"
).split()


def emit(path, filt, cycle, out):
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            attrs = d.get("nexus_mind_attributes")
            if attrs is None:
                raise KeyError(f"{path}: row {d.get('id')} has no nexus_mind_attributes")
            if filt not in attrs:
                raise KeyError(f"{path}: row {d.get('id')} has no '{filt}' block; keys={sorted(attrs)}")
            a = attrs[filt]
            rec = {
                "cycle": cycle,
                "filter": filt,
                "id": d["id"],
                "title": d.get("title"),
                "source": d.get("source"),
                "source_group": d.get("source_group"),
                "language": d.get("language"),
                "url": d.get("url"),
                "len_content": len(d.get("content") or ""),
                "disposition": (d.get("nexusmind") or {}).get("disposition", {}).get("status"),
                "scores": a.get("scores"),
            }
            for k in KEEP_ATTR:
                # Raise, never silently None: `.get()` here made every downstream control
                # blind to a renamed or dropped attribute (review, 2026-09-08). Two fields are
                # legitimately null on some rows and are listed rather than defaulted.
                if k not in a and k not in ("prefilter_reason", "cap_applied", "stage1_estimate"):
                    raise KeyError(f"{path}: row {d.get('id')} has no '{filt}.{k}'")
                rec[k] = a.get(k)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    dest = sys.argv[1]
    counts = {}
    with open(dest, "w") as out:
        for cycle, up_f, ht_f in PAIRS:
            for filt, fn in (("uplifting", up_f), ("human_thriving", ht_f)):
                p = os.path.join(BASE, filt, fn)
                counts[(cycle, filt)] = emit(p, filt, cycle, out)
    for k in sorted(counts):
        print(f"{k[0]}\t{k[1]}\t{counts[k]}")


if __name__ == "__main__":
    main()
