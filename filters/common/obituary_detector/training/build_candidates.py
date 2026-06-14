#!/usr/bin/env python3
"""
Phase 1 — extract death-adjacent obituary CANDIDATES from the RAW FluxusSource
ingest stream (NM#185 / llm-distillery#51, build-plan Phase 1).

Why raw ingest, not the warm DB: the editorial gate filters obituaries out
*early*, so the post-scoring DB is depleted of real positives (v2 recall ~33%).
The raw content_items_*.jsonl stream — FluxusSource output BEFORE any filtering —
is where obituaries are plentiful. We over-select with a broad multilingual death
regex, then hand the candidates to the gemini oracle (relabel_candidates.py) and
the Ollama panel for the actual obituary/not_obituary judgments.

Dedups by content id across all collection files. Output is gitignored
(contains article content). Reversible: read-only over the ingest, writes one file.

Usage (local, reads Windows FluxusSource data):
    python build_candidates.py \
        --glob "C:/local_dev/FluxusSource/data/content_items_*.jsonl" \
        --out  ../validation/artifacts/raw_candidates_corpus.jsonl

Add more sources by repeating --glob (e.g. sadalsuud-pulled recent collections).
"""
import argparse, json, glob, re
from collections import Counter

# Broad multilingual death-adjacent net — intentionally high-recall. The point is
# to NOT miss obituaries; precision is the oracle's job downstream. Same vocabulary
# as make_obit_worksheet.py / the validation harness, kept in sync deliberately.
DEATH_RE = re.compile(
    # \b-anchored: bare substrings false-match ("distributed"->tribute,
    # "studied"->died, "deathless" is fine). Anchoring kills the science/AI noise.
    r"\bobituar|\bdied\b|\bdeath|passed away|\bfuneral|\bmemorial|\bremembrance|"
    r"laid to rest|\bdies\b|in memoriam|\btribute|\bmourn|\beulog|\bcondolen|"
    r"\boverled|\boverlijden|\bgestorven|\buitvaart|"          # nl
    r"\bverstorben|\bgestorben|\bnachruf|\btrauer|"            # de
    r"\bfalleci|\bdeceso|\bóbito|\besquela|"                   # es/pt
    r"\bdécès|\bobsèques|\bdisparition|\bhommage",             # fr
    re.IGNORECASE,
)

ap = argparse.ArgumentParser()
ap.add_argument("--glob", action="append", required=True,
                help="glob of content_items_*.jsonl (repeatable)")
ap.add_argument("--out", required=True)
ap.add_argument("--min-content-chars", type=int, default=0,
                help="drop candidates whose content is shorter than this")
args = ap.parse_args()

files = []
for g in args.glob:
    files.extend(glob.glob(g))
files = sorted(set(files))
print(f"reading {len(files)} ingest files ...")

seen = {}            # id -> candidate (last write wins; dedups re-collected items)
total = 0
matched = 0
lang_counter = Counter()
src_counter = Counter()

for fn in files:
    try:
        fh = open(fn, encoding="utf-8")
    except OSError as e:
        print(f"  skip {fn}: {e}")
        continue
    for line in fh:
        if not line.strip():
            continue
        total += 1
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        title = r.get("title") or ""
        content = r.get("content") or ""
        blob = f"{title} {content}"
        if not DEATH_RE.search(blob):
            continue
        if len(content) < args.min_content_chars:
            continue
        cid = r.get("id")
        if not cid:
            continue
        matched += 1
        meta = r.get("metadata") or {}
        seen[cid] = {
            "id": cid,
            "title": title,
            "content": content,
            "source": r.get("source"),
            "source_category": meta.get("source_category"),
            "published_date": r.get("published_date"),
            "language": r.get("language"),
            "content_len": len(content),
        }

# tally after dedup
for c in seen.values():
    lang_counter[c.get("language") or "?"] += 1
    src_counter[c.get("source_category") or "?"] += 1

with open(args.out, "w", encoding="utf-8") as f:
    for c in seen.values():
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"\ntotal ingest records scanned : {total}")
print(f"death-adjacent matches       : {matched}")
print(f"unique candidates (deduped)  : {len(seen)}  -> {args.out}")
print(f"\ntop languages : {dict(lang_counter.most_common(8))}")
print(f"top categories: {dict(src_counter.most_common(12))}")
