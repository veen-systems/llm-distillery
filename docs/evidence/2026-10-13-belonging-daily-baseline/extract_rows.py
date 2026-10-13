"""Step 1b (runs ON sadalsuud, read-only on NexusMind's files): version stamp + text for the ids in ids.txt.

    python3 extract_rows.py ids.txt > rows.jsonl

Newest belonging filtered_*.jsonl (from 2026-09-29 on) holding each id wins, as in the 10-12 pre-registration.
Output per id: id, version (nexus_mind_attributes.belonging.version), title, content, file. Article text: lab only.
"""
import glob, json, os, sys

want = {l.strip() for l in open(sys.argv[1]) if l.strip()}
files = sorted(f for f in glob.glob(os.path.expanduser("~/local_dev/NexusMind/data/filtered/belonging/filtered_*.jsonl"))
               if os.path.basename(f) >= "filtered_20260929")
found = {}
for p in reversed(files):
    for line in open(p, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r["id"] in want and r["id"] not in found:
            v = ((r.get("nexus_mind_attributes") or {}).get("belonging") or {}).get("version")
            found[r["id"]] = dict(id=r["id"], version=v, title=r.get("title"), content=r.get("content"),
                                  file=os.path.basename(p))
for i in sorted(want):
    print(json.dumps(found.get(i, dict(id=i, version=None, title=None, content=None, file=None)), ensure_ascii=False))
print(f"{len(found)}/{len(want)} ids found in {len(files)} files", file=sys.stderr)
