#!/usr/bin/env python3
"""Extract the solutions v6 short/long DiD candidate pool from production cycles.

Emits one compact JSON record per scored solutions v6 row, so sampling and
threshold choices can be made offline without re-reading 1.4G.

STEP 1 of 3 in the LD#92 short-content harness. Run on sadalsuud:

    python3 scripts/diagnostics/ld92_build_pool.py      # -> ~/solutions_v6_pool.jsonl
    python3 scripts/diagnostics/ld92_sample_designs.py  # -> ~/ld92_articles.jsonl + design
    # then, from llm-distillery with the DeepSeek key:
    PYTHONPATH=. python scripts/score_deepseek_production.py \
        --input ld92_articles.jsonl --output ld92_scored.jsonl \
        --config filters/solutions/v6/config.yaml --concurrency 15
    python3 scripts/diagnostics/ld92_analyze_did.py \
        --design ld92_design.json --scored ld92_scored.jsonl

This exists because the original n=15 and n=60 harnesses were NOT committed, so
neither result could be re-derived and the 2026-08-05 re-run had to rebuild the
sampling half from scratch. Commit the harness with the finding.

Population note: `data/filtered/solutions/*.jsonl` is 100% `passed_prefilter`
rows AND drops source-type-excluded rows post-scoring (see
memory/nexusmind-data-sources.md). Both arms are drawn from it, so the exclusion
is common to the comparison rather than differencing into it — but the estimand
is "articles that can actually surface", which is the right population for a cap
decision and the wrong one for a corpus-wide rate.
"""
import glob
import json
import os
import sys

SRC = os.path.expanduser("~/local_dev/NexusMind/data/filtered/solutions")
OUT = os.path.expanduser("~/solutions_v6_pool.jsonl")
VERSION = "6.0"

files = sorted(glob.glob(os.path.join(SRC, "*.jsonl")))
kept = 0
seen_ids = set()
dupes = 0
wrong_version = 0

with open(OUT, "w") as out:
    for path in files:
        cycle = os.path.basename(path)
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    a = json.loads(line)
                except json.JSONDecodeError:
                    continue
                attrs = (a.get("nexus_mind_attributes") or {}).get("solutions")
                if not attrs:
                    continue
                if str(attrs.get("version")) != VERSION:
                    wrong_version += 1
                    continue
                raw = attrs.get("raw_weighted_average")
                if raw is None:
                    continue
                aid = a.get("id")
                # An article recurs across cycles; keep its first appearance so
                # the pool is one row per article, not one per scoring event.
                if aid in seen_ids:
                    dupes += 1
                    continue
                seen_ids.add(aid)
                content = a.get("content") or ""
                out.write(json.dumps({
                    "id": aid,
                    "cycle": cycle,
                    "title": a.get("title") or "",
                    "content": content,
                    "content_length": len(content),
                    "source": a.get("source") or "",
                    "language": a.get("language") or "",
                    "raw": float(raw),
                    "tier": attrs.get("tier"),
                    "gatekeeper_applied": attrs.get("gatekeeper_applied"),
                    "published_date": a.get("published_date"),
                }) + "\n")
                kept += 1

print(f"files={len(files)} kept={kept} dup_article_rows_skipped={dupes} wrong_version={wrong_version}")
print(f"wrote {OUT}")
