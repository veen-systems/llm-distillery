#!/usr/bin/env python3
"""Merge the pilot and full-run adjudications into labels_adjudicated_v1.jsonl (PLAN.md).

Order of operations is the pre-registration's:
  1. validate every out_* file against its input (ids, order, verdict set, quote in text);
  2. the DRIFT CHECK: A vs B binary agreement on the 20% sample >= 0.90, else STOP (exit 1,
     nothing written) -- the plan says the run is then reported, not repaired;
  3. write the merged file. A/B split on in/out -> not in scope (ADR-023 tie rule).

Dimension scores are NOT changed here; the retrain rule for corrected rows is decided separately.
Exit 0 written, 1 drift stop, 3 plumbing.
"""
import collections
import json
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
P = F.parent / "2026-09-24-thriving-adjudication-pilot"
REPO = F.parents[2]
SRC = REPO / "datasets/scored/human_thriving_v8/labels_v84_merged.jsonl"
OUT = REPO / "datasets/scored/human_thriving_v8/labels_adjudicated_v1.jsonl"
VERDICTS = {"in_scope", "out_of_scope", "harm_is_subject", "response_to_harm", "no_person_benefits"}


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def read_checked(inp, out):
    if not out.is_file():
        fatal(f"FATAL: {out.name} missing")
    art = [json.loads(l) for l in open(inp, encoding="utf-8")]
    res = [json.loads(l) for l in open(out, encoding="utf-8")]
    if [a["id"] for a in art] != [r["id"] for r in res]:
        fatal(f"FATAL: {out.name}: ids/order differ from {inp.name}")
    for a, r in zip(art, res):
        if r["verdict"] not in VERDICTS:
            fatal(f"FATAL: {out.name}: {r['id']} verdict {r['verdict']!r}")
        if r["quote"] not in (a.get("content") or "") + (a.get("title") or ""):
            fatal(f"FATAL: {out.name}: {r['id']} quote not in article")
    return {r["id"]: r for r in res}


def load(dirp, prefix):
    out = {}
    for inp in sorted(dirp.glob(f"input_{prefix}*.jsonl")):
        got = read_checked(inp, dirp / inp.name.replace("input_", "out_"))
        if set(got) & set(out):
            fatal(f"FATAL: {inp.name} repeats ids")
        out.update(got)
    return out


def main():
    FA, FB = load(F, "A"), load(F, "B")
    PA, PB = load(P, "A"), load(P, "B")
    pilot_key = {json.loads(l)["id"]: json.loads(l) for l in open(P / "key.jsonl")}
    controls = {i for i, k in pilot_key.items() if k["stratum"] == "control"}

    ins = lambda r: r["verdict"] == "in_scope"
    if not set(FB) <= set(FA):
        fatal("FATAL: B sample ids not all in pass A")
    agree = sum(ins(FA[i]) == ins(FB[i]) for i in FB) / len(FB)
    print(f"drift check: A vs B binary agreement on the {len(FB)}-row sample = {agree:.3f} (stop below 0.90)")
    if agree < 0.90:
        print("STOP: drift check failed -- nothing written (PLAN.md)")
        return 1

    decided = {}
    for i, a in FA.items():
        b = FB.get(i)
        if b is None:
            decided[i] = (a["verdict"], "A", a)
        elif ins(a) == ins(b):
            decided[i] = (a["verdict"], "A+B", a)
        else:
            decided[i] = (a["verdict"] if not ins(a) else b["verdict"], "A/B split -> out", a)
    for i in set(PA) - controls:
        a, b = PA[i], PB[i]
        if ins(a) == ins(b):
            decided[i] = (a["verdict"], "pilot A+B", a)
        else:
            decided[i] = (a["verdict"] if not ins(a) else b["verdict"], "pilot A/B split -> out", a)

    n_rows, n_adj, moved = 0, 0, collections.Counter()
    with open(OUT, "w", encoding="utf-8") as fo:
        for line in open(SRC, encoding="utf-8"):
            r = json.loads(line)
            an = r["human_thriving_analysis"]
            label = float(an["weighted_mean_all"])
            if r["id"] in decided:
                v, src, rec = decided[r["id"]]
                r["adjudication"] = {"status": "adjudicated", "verdict": v, "decided_by": src,
                                     "quote": rec["quote"], "reason": rec["reason"],
                                     "oracle_verdict": an["scope_verdict"], "oracle_label": label,
                                     "rulings": "docs/decisions/2026-09-24-thriving-scope-rulings.md"}
                n_adj += 1
                moved[(an["scope_verdict"] == "in_scope", v == "in_scope")] += 1
            else:
                if label >= 3.5:
                    fatal(f"FATAL: {r['id']} labelled {label} >= 3.5 but not adjudicated")
                r["adjudication"] = {"status": "not_adjudicated", "reason": "label < 3.5"}
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
            n_rows += 1
    print(f"wrote {OUT.relative_to(REPO)}: {n_rows} rows, {n_adj} adjudicated")
    print(f"oracle in -> adjudicated in {moved[(True, True)]}, in -> OUT {moved[(True, False)]}, "
          f"out -> IN {moved[(False, True)]}, out -> out {moved[(False, False)]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
