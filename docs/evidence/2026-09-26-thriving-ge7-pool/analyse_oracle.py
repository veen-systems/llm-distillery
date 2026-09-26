#!/usr/bin/env python3
"""Apply the two rules fixed in PLAN.md before any oracle call, and report dimension coverage.

1. Alias control (#157): d = median(now - 2026-09-24 V4.1 label) of the weighted average over 50 seeded more-positives rows.
   |d| <= 0.30 -> new rows may be mixed into train/val/test; otherwise TEST ONLY.
2. A Claude-in_scope row whose oracle k=3 majority verdict is not in_scope is EXCLUDED.

Weighted averages use adverse_suite_gate.weighted_average, the same function the gates use.
Writes new_labels.jsonl (kept rows: id, labels in dimension order, per-run spread). Exit 3 on plumbing.
"""
import collections
import json
import statistics
import sys
from pathlib import Path

X = Path(__file__).resolve().parent
REPO = X.parents[2]
sys.path.insert(0, str(REPO / "scripts" / "gate"))
import adverse_suite_gate as G  # noqa: E402

NAMES = {"human_wellbeing_impact": "Wellbeing", "social_cohesion_impact": "Connection",
         "justice_rights_impact": "Justice", "evidence_level": "Evidence",
         "benefit_distribution": "Reach", "change_durability": "Durability"}


def runs(prefix, n_expected):
    per = collections.defaultdict(list)
    for k in (1, 2, 3):
        p = X / "runs" / f"{prefix}_{k}.jsonl"
        if not p.is_file():
            G.fatal(f"FATAL: {p.name} missing")
        seen = set()
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if "human_thriving_analysis" not in r:
                continue  # failed attempt; the resume wrote the scored row
            if r["id"] in seen:
                G.fatal(f"FATAL: {p.name}: {r['id']} scored twice")
            seen.add(r["id"])
            a = r["human_thriving_analysis"]
            if a.get("prompt_hash") != "c4705408c477":
                G.fatal(f"FATAL: {p.name}: prompt hash {a.get('prompt_hash')}")
            per[r["id"]].append(a)
    bad = {i: len(v) for i, v in per.items() if len(v) != 3}
    if len(per) != n_expected or bad:
        G.fatal(f"FATAL: {prefix}: {len(per)} ids (expected {n_expected}); ragged k: {list(bad.items())[:3]}")
    return per


def main():
    ctrl = runs("control", 50)
    v4 = json.load(open(X / "control_prev_labels.json"))
    deltas = []
    for i, rs in ctrl.items():
        wa = statistics.fmean(G.weighted_average({d: a[d]["score"] for d in G.DIMS}) for a in rs)
        deltas.append(wa - v4[i])
    d = statistics.median(deltas)
    mix = abs(d) <= 0.30
    print(f"CONTROL (n=50, same prompt v8-4, deepseek-chat alias 2026-09-24 -> 2026-09-26): median delta {d:+.3f}, "
          f"mean {statistics.fmean(deltas):+.3f}, IQR "
          f"[{statistics.quantiles(deltas, n=4)[0]:+.3f}, {statistics.quantiles(deltas, n=4)[2]:+.3f}]"
          f" -> {'MIX new rows into train/val/test' if mix else 'new rows TEST ONLY'} (rule |d| <= 0.30)")

    new = runs("new", 183)
    kept, excluded = [], 0
    for i, rs in sorted(new.items()):
        votes = collections.Counter(a.get("scope_verdict") for a in rs)
        if votes["in_scope"] < 2:
            excluded += 1
            continue
        dims = [statistics.fmean(float(a[d]["score"]) for a in rs) for d in G.DIMS]
        kept.append({"id": i, "labels": dims, "dimension_names": list(G.DIMS),
                     "in_scope_votes": votes["in_scope"],
                     "weighted": G.weighted_average(dict(zip(G.DIMS, dims)))})
    with open(X / "new_labels.jsonl", "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")
    print(f"NEW: {len(kept)} kept, {excluded} excluded (oracle majority not in_scope)")
    w = [r["weighted"] for r in kept]
    print(f"  weighted >= 4.5: {sum(x >= 4.5 for x in w)}   >= 6: {sum(x >= 6 for x in w)}   >= 7: {sum(x >= 7 for x in w)}   >= 8: {sum(x >= 8 for x in w)}   max {max(w):.2f}")
    print("  per dimension (new kept rows):   >=6   >=8")
    for k, dname in enumerate(G.DIMS):
        print(f"    {NAMES[dname]:11} {sum(r['labels'][k] >= 6 for r in kept):5} {sum(r['labels'][k] >= 8 for r in kept):5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
