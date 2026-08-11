#!/usr/bin/env python3
"""Why did ovr.news never enrich the two stubs, when both are far under its 500 threshold?

ovr enriches only when content < 500 AND NOT wasEnrichedUpstream(article).
Hypothesis: NexusMind's pre_enrich ran, "succeeded" by fetching the Google consent
stub (60-100 chars), set an enriched flag, and ovr then yielded to it. If so, a
successful-looking enrichment that produced nothing is what suppressed the retry.
"""
import glob
import json
import os

NM = os.path.expanduser("~/local_dev/NexusMind")
TARGETS = {
    "gn_europe_gn_serbia_a38e949e1d30": "Kacanik (131 chars)",
    "gn_asia_gn_cambodia_eedfba43e99e": "Cambodia (106 chars)",
}

found = {t: [] for t in TARGETS}
for path in glob.glob(os.path.join(NM, "data/filtered", "*", "filtered_*.jsonl")):
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        continue
    with fh:
        for line in fh:
            hit = next((t for t in TARGETS if t in line), None)
            if not hit:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("id") != hit:
                continue
            lens = os.path.basename(os.path.dirname(path))
            flags = {k: v for k, v in r.items()
                     if "enrich" in k.lower() or k in ("pre_enriched", "enriched")}
            # per-scorer attributes too -- that is where wasEnrichedUpstream may look
            attrs = (r.get("nexus_mind_attributes") or {}).get(lens) or {}
            aflags = {k: v for k, v in attrs.items() if "enrich" in k.lower()}
            found[hit].append((os.path.basename(path), lens,
                               len(r.get("content") or ""), flags, aflags))

for t, label in TARGETS.items():
    print(f"=== {label} — {t}")
    if not found[t]:
        print("   NOT FOUND in any NexusMind filtered batch")
    for batch, lens, blen, flags, aflags in sorted(found[t]):
        print(f"   {batch:<34} {lens:<20} len={blen}")
        print(f"      top-level enrich keys : {flags if flags else '{}  <-- NONE'}")
        print(f"      per-lens enrich keys  : {aflags if aflags else '{}  <-- NONE'}")
    print()
