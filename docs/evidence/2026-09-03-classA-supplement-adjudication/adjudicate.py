#!/usr/bin/env python3
"""Adjudication instruments for the 47-row class-A supplement, plus a
self-contradiction scan over every above-op row.

Two questions:
  1. What did v8 do to the 47 rows v7 scored above the op-point on harm titles?
  2. Where does the oracle name a disqualifier in its OWN `dominant_subject`
     and score the row above the op-point anyway?

(2) needs no lexicon over article text: it reads the oracle's own summary of
what the article is about against the oracle's own score. A hit is the label
contradicting itself inside one JSON object.

Usage:
    PYTHONPATH=. python3 docs/evidence/2026-09-03-classA-supplement-adjudication/adjudicate.py

⚠️ SOURCE EXCLUDES: `labels_k3.jsonl` is 6,586 rows (4 scrape-junk skips) against
`corpus.jsonl`'s 6,590. The supplement is the 47 class-A rows in the two ABOVE-op
design cells (`pos_clear`, `pos_marginal`); the other 35 class-A rows sit below the
op-point and are neither TP nor FP under the 2026-08-30 ruling.

⚠️ Every count here is a CANDIDATE population. Adjudication is reading, not matching.
"""
import json
import re
import sys
from collections import Counter, defaultdict

OP_POINT = 4.5
CORPUS = "datasets/scored/human_thriving_v8/corpus.jsonl"
LABELS = "datasets/scored/human_thriving_v8/labels_k3.jsonl"

# Read against the oracle's own `dominant_subject`, never against article text.
FAMILIES = {
    "proposal / not yet enacted": r"\b(proposal|proposed|draft|mulls|bill|considering)\b",
    "announcement / pledge / plan": r"\b(announce\w*|pledge\w*|plan\w*|promise\w*|vow\w*|unveil\w*|preparations?)\b",
    "funding committed": r"\b(funding|investment|allocat\w*|budget|grant)\b",
    "call for / demand / appeal": r"\b(call(?:s|ing)? for|demand\w*|urg\w*|plea)\b",
    "harm as the subject": r"\b(kill\w*|murder\w*|death|died|attack\w*|abuse\w*|rape|assault\w*|crash|disaster|crisis|war|violence)\b",
    "benefit reaches no person (§3)": r"\b(reputation|market|index|shares|stock|jurisdiction|designation|sanctions?)\b",
}


def load():
    labels = {}
    for line in open(LABELS):
        d = json.loads(line)
        labels[d["id"]] = d["human_thriving_analysis"]
    corpus = [json.loads(line) for line in open(CORPUS)]
    return corpus, labels


def main():
    corpus, labels = load()
    print(f"corpus rows {len(corpus)}   labelled {len(labels)}   "
          f"(difference = scrape-junk skips: {len(corpus) - len(labels)})")
    print()

    supp = [c for c in corpus if c["design_cell"].endswith("|classA")
            and c["design_cell"].split("|")[0] in ("pos_clear", "pos_marginal")]
    below = [c for c in corpus if c["design_cell"].endswith("|classA")
             and c["design_cell"].split("|")[0] not in ("pos_clear", "pos_marginal")]
    if len(supp) != 47:
        sys.exit(f"FATAL: supplement is {len(supp)} rows, manifest declares 47")
    unlabelled = [c["id"] for c in supp if c["id"] not in labels]
    if unlabelled:
        sys.exit(f"FATAL: {len(unlabelled)} supplement rows have no label")

    kept = [c for c in supp if labels[c["id"]]["weighted_mean_all"] >= OP_POINT]
    flipped = sum(1 for c in supp if labels[c["id"]].get("scope_flipped"))
    print("-- 1. THE 47-ROW SUPPLEMENT (v7 scored these above the op-point on a harm title) --")
    print(f"supplement rows                      47   (below-op class-A rows, not adjudicable: {len(below)})")
    print(f"v8 DEMOTES below the op-point        {47 - len(kept)}  ({(47-len(kept))/47:.1%})")
    print(f"v8 KEEPS above the op-point          {len(kept)}  ({len(kept)/47:.1%})")
    print(f"verdict-flipped                      {flipped}  ({flipped/47:.1%} against the corpus's 15.35%)")
    print(f"verdicts {dict(Counter(labels[c['id']]['scope_verdict'] for c in supp).most_common())}")
    print()

    # distinct events among the survivors: collapse near-identical titles
    STOP = set("the a an of to in on for and or as at by from with is are was were be us u.s".split())
    def toks(t):
        return frozenset(w for w in re.findall(r"[a-z0-9']+", t.lower())
                         if w not in STOP and len(w) > 2)
    groups = []
    for c in sorted(kept, key=lambda c: -labels[c["id"]]["weighted_mean_all"]):
        t = toks(c["title"])
        for g in groups:
            if any(len(t & toks(m["title"])) / max(len(t | toks(m["title"])), 1) >= 0.34 for m in g):
                g.append(c)
                break
        else:
            groups.append([c])
    print(f"the {len(kept)} survivors are {len(groups)} DISTINCT EVENTS:")
    for g in groups:
        top = labels[g[0]["id"]]["weighted_mean_all"]
        tag = f"  [x{len(g)} near-duplicates]" if len(g) > 1 else ""
        print(f"  {top:.2f}  {g[0]['title'][:66]}{tag}")
    print()

    print("-- 2. SELF-CONTRADICTION SCAN (all above-op rows, oracle's own dominant_subject) --")
    above = [c for c in corpus if c["id"] in labels
             and labels[c["id"]]["weighted_mean_all"] >= OP_POINT]
    per = defaultdict(list)
    for c in above:
        ds = labels[c["id"]].get("dominant_subject") or ""
        for fam, pat in FAMILIES.items():
            if re.search(pat, ds, re.I):
                per[fam].append((labels[c["id"]]["weighted_mean_all"], c["title"], ds))
    print(f"above-op rows                        {len(above)}  ({len(above)/len(labels):.2%} of labelled)")
    for fam in FAMILIES:
        print(f"  {fam:32s} {len(per[fam]):3d}  ({len(per[fam])/len(above):5.1%})")
    print()
    print("⚠️ 'harm as the subject' hits are mostly §1's GUARD WORKING (harm as setting,")
    print("   outcome as occasion) -- read before treating any of them as a defect.")
    print()
    for fam in ("proposal / not yet enacted", "announcement / pledge / plan",
                "benefit reaches no person (§3)"):
        print(f"--- {fam} ---")
        for score, title, ds in sorted(per[fam], reverse=True)[:8]:
            print(f"  {score:.2f}  {title[:64]}")
            print(f"        dominant_subject={ds[:76]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
