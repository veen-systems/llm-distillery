"""Build the >=7 pool (run ON sadalsuud, read-only): production articles that a production
model scored raw >= 7 at stage 2, 2026-09-02 -> 2026-09-24 inclusive (by filename date).

Filters read: uplifting, belonging, solutions, human_thriving (the four named when the pool was
proposed, TODO-archive 'OPEN OWNER QUESTION -- the >= 7 pool'). Exclusions, as in the
more-positives run: news.google.com urls, content < 300 chars, ids already in the v8 corpus /
training dirs / any earlier adjudication input (EXCLUDE file), duplicate content_hash.
Writes pool.jsonl (blind fields + provenance) to stdout."""
import json, glob, sys, hashlib
BASE = "/home/jeroen/local_dev/NexusMind/data/filtered"
FILTERS = ["uplifting", "belonging", "solutions", "human_thriving"]
exclude = set(json.load(open("/tmp/ge7_exclude_ids.json")))
rows, seen_hash, stats = {}, set(), {}
for flt in FILTERS:
    for f in sorted(glob.glob(f"{BASE}/{flt}/filtered_*.jsonl")):
        day = f.rsplit("filtered_", 1)[1][:8]
        if not ("20260902" <= day <= "20260924"):
            continue
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            a = r.get("nexus_mind_attributes", {}).get(flt, {})
            raw = a.get("raw_weighted_average")
            if raw is None or raw < 7.0 or a.get("stage_used") != "stage2":
                continue
            i = r["id"]
            if i in rows:
                rows[i]["hits"][flt] = max(rows[i]["hits"].get(flt, 0), round(raw, 3))
                continue
            content = r.get("content") or ""
            reason = None
            if "news.google.com" in (r.get("url") or ""): reason = "google_news"
            elif len(content) < 300: reason = "short"
            elif i in exclude: reason = "already_labelled"
            else:
                h = r.get("content_hash") or hashlib.sha1(content.encode()).hexdigest()
                if h in seen_hash: reason = "dup_content"
                else: seen_hash.add(h)
            if reason:
                stats[reason] = stats.get(reason, 0) + 1
                continue
            rows[i] = {"id": i, "title": r.get("title"), "url": r.get("url"), "source": r.get("source"),
                       "content": content, "hits": {flt: round(raw, 3)}, "first_file": f.rsplit("/", 1)[1]}
for r in rows.values():
    sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
by = {}
for r in rows.values():
    k = "+".join(sorted(r["hits"]))
    by[k] = by.get(k, 0) + 1
print(json.dumps({"kept": len(rows), "excluded": stats, "by_filter_set": by}), file=sys.stderr)
