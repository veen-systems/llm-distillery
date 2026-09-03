#!/usr/bin/env python3
"""Blast radius of the v8.1 §2 qualifier fix, measured on the Phase B labels.

Answers one question: if the "policy change made after the fact" clause is
bounded so that a NOT-YET-COMMENCED policy change cannot be read as delivered,
how many rows move, and how many of those reach a reader?

Two scopings are measured separately because they differ by ~4x:
  §2-bounded  the clause fires only inside "harm answered is not harm undone"
  §1-global   the clause extends the money-committed rule to every article

Usage:
    PYTHONPATH=. python3 docs/evidence/2026-09-03-v8-1-qualifier-blast-radius/blast_radius.py \
        datasets/scored/human_thriving_v8/labels_k3.jsonl

⚠️ SOURCE EXCLUDES: labels_k3.jsonl holds 6,586 rows, not the 6,590 drawn --
four scrape-junk skips. It holds no adverse and no no-regression row (asserted
below), so the nursery row that motivates the fix is NOT in this population and
its 4.400 is not comparable to a corpus figure.

⚠️ The regex is a CANDIDATE GENERATOR, not the finding. Every count it produces
is an upper bound on a population that still needs adjudication by reading.
"""
import json
import re
import sys
from collections import Counter

OP_POINT = 4.5          # human_thriving v8, inherited from #102
CRIT1_BAR = 3.85        # acceptance criterion 1's editorial upper bound

# Not-yet-commenced / future-tense policy language, looked for in the OCCASION
# (title + first 1200 chars) because STEP 1 locates the occasion in the headline
# and first two paragraphs.
FUTURE = re.compile(r"""
   will\s+(?:be\s+)?(?:ban|banned|require|introduce|introduced|come\s+into
                      |take\s+effect|begin|start|launch|receive|rise|increase
                      |triple|double|provide|open)
 | (?:comes?|coming)\s+into\s+(?:force|effect)
 | takes?\s+effect
 | due\s+to\s+(?:take|come|begin|start|open)
 | (?:is|are)\s+(?:set|expected|due)\s+to
 | from\s+(?:January|February|March|April|May|June|July|August|September
            |October|November|December)\b
 | as\s+of\s+(?:January|February|March|April|May|June|July|August|September
               |October|November|December)\b
 | plans?\s+to\s+(?:introduce|launch|build|open|provide|ban)
 | has\s+(?:pledged|announced|unveiled|proposed)
 | would\s+(?:be\s+)?(?:require|ban|introduce|provide)
""", re.I | re.X)


OCCASION_WINDOW = 1200   # STEP 1: headline + first two paragraphs


def occasion(row, window=OCCASION_WINDOW):
    return (row.get("title") or "") + "\n" + (row.get("content") or "")[:window]


def main(path):
    rows = [json.loads(line) for line in open(path)]
    n = len(rows)

    guard_ids = set()
    for f in ("datasets/adverse/uplifting.jsonl",
              "datasets/adverse/uplifting_no_regression.jsonl"):
        try:
            guard_ids |= {json.loads(l)["id"] for l in open(f)}
        except FileNotFoundError:
            sys.exit(f"FATAL: guard set {f} missing -- cannot assert disjointness")
    present = sorted(r["id"] for r in rows if r["id"] in guard_ids)
    if present:
        sys.exit(f"FATAL: {len(present)} guard row(s) inside the labelled corpus: {present}")

    verdicts, flipped, above = Counter(), [], []
    nursery_shape = []
    for r in rows:
        a = r["human_thriving_analysis"]
        verdicts[a["scope_verdict"]] += 1
        per_run = set(a.get("scope_verdicts_per_run") or [])
        if a.get("scope_flipped"):
            flipped.append((r, a))
        if a["weighted_mean_all"] >= OP_POINT:
            above.append((r, a))
        if {"in_scope", "response_to_harm"} <= per_run:
            nursery_shape.append((r, a))

    print(f"rows                                 {n}")
    print(f"guard rows present                   0  (asserted, {len(guard_ids)} declared)")
    print(f"verdict distribution                 {dict(verdicts.most_common())}")
    print()

    fmax = max(a["weighted_mean_all"] for _, a in flipped)
    fmaj = sum(1 for _, a in flipped if a["weighted_mean_major"] >= OP_POINT)
    band = sum(1 for _, a in flipped if CRIT1_BAR <= a["weighted_mean_all"] < OP_POINT)
    print("-- CEILING: can a verdict-flipped row reach a reader? --")
    print(f"verdict-flipped rows                 {len(flipped)}  ({len(flipped)/n:.2%})")
    print(f"  max weighted_mean_all              {fmax:.4f}   (op-point {OP_POINT})")
    print(f"  above op-point under 'all'         {sum(1 for _, a in flipped if a['weighted_mean_all'] >= OP_POINT)}")
    print(f"  above op-point under 'majority'    {fmaj}")
    print(f"  in the {CRIT1_BAR}-{OP_POINT} band (fail crit 1, invisible)  {band}")
    print("  NB empirical, NOT mathematical: one capped run (<=2.0) with two at")
    print("     10.0 yields 7.33 under 'all', so nothing forbids a flipped row")
    print("     from crossing. The corpus simply contains none.")
    print()

    ns_fut = sum(1 for r, _ in nursery_shape if FUTURE.search(occasion(r)))
    ns_above = sum(1 for _, a in nursery_shape if a["weighted_mean_all"] >= OP_POINT)
    ns_maj = sum(1 for _, a in nursery_shape if a["weighted_mean_major"] >= OP_POINT)
    print("-- SCOPING A: clause bounded inside §2 (post-harm responses only) --")
    print(f"nursery-shape rows                   {len(nursery_shape)}  ({len(nursery_shape)/n:.2%})")
    print(f"  (runs split in_scope / response_to_harm)")
    print(f"  showing not-yet-commenced language {ns_fut}  ({ns_fut/max(len(nursery_shape),1):.1%} -- tense is NOT the dominant mechanism)")
    sens = {w: sum(1 for r, _ in nursery_shape if FUTURE.search(occasion(r, w)))
            for w in (800, 1200, 1500, 2500)}
    print(f"    window sensitivity (chars -> hits) {sens}")
    print("    ^ the count moves with the window, so it is a magnitude, not a figure")
    print(f"  above op-point under 'all'         {ns_above}")
    print(f"  above op-point under 'majority'    {ns_maj}")
    print()

    ab_fut = [(r, a) for r, a in above if FUTURE.search(occasion(r))]
    print("-- SCOPING B: clause extended globally into §1 (money-committed family) --")
    print(f"above-op rows                        {len(above)}  ({len(above)/n:.2%})")
    print(f"  showing not-yet-commenced language {len(ab_fut)}  ({len(ab_fut)/max(len(above),1):.1%})")
    print(f"  all above-op verdicts unanimous?   {all(a['scope_verdict'] == 'in_scope' for _, a in above)}")
    print("  candidates a global clause would demote, highest first:")
    for r, a in sorted(ab_fut, key=lambda x: -x[1]["weighted_mean_all"])[:15]:
        print(f"    {a['weighted_mean_all']:.2f}  {r.get('language','??'):3s}  {r.get('title','')[:72]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "datasets/scored/human_thriving_v8/labels_k3.jsonl"))
