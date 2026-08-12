#!/usr/bin/env python3
"""Enrichment-failure rate per source family (was: FluxusSource#120 / ADR-007 H4).

Answers H4 — do eval-source articles convert better than Google News proxies
because enrichment never has to go through `batchexecute`?

⚠️ **FS#120 IS CLOSED (2026-08-08T06:54Z), six days early, on ADR-007.** Its
`docs/GN-REPLACEMENT-PLAN.md` records the 08-14 funnel readout as cancelled and
H4 as *"Not read, and moot"* — H4 asked whether a canonical URL is worth *paying*
for, and native-first pays for nothing. **No arm data is owed to any FluxusSource
decision, and nothing upstream is waiting on this script.**

It is kept because H4 retains value for **this repo's** short-content problem
(#92/#93): it is the hard measurement behind "a Google News row can never be
enriched" (NexusMind#310). Read it as our own instrument, not as a gate.

**The only complete window is 2026-07-31..2026-08-08** and it cannot be extended.
From 2026-08-09 all six live filters exclude `eval_aggregator` so the arms enter
no lens store (see --lens help), and the arms stopped upstream at
2026-08-11T14:06Z under ADR-007 D2/D3. `shadow_mode: true` would NOT recover this:
it stamps forward-only, and there is no future arm data to stamp. Confirmed with
FluxusSource 2026-08-12 — **do not propose that change.**

Run on sadalsuud from the NexusMind repo root. It writes nothing, so it can be
piped in over ssh rather than copied:

    ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && python3 - \
        --start 2026-07-31 --end 2026-08-08' < scripts/gate/measure_enrichable_rate.py

The instrument
--------------
FS#120's original spec was "still <300 chars after pre_enrich ÷ all rows from
that source that reached scoring". That denominator confounds enrichment success
with how long a source's articles are natively: arxiv and pubmed are essentially
never short, so a source like that posts a perfect rate without enrichment having
done anything. H4's claim is about enrichment *working*, so the denominator has
to be the rows enrichment actually attempted. Agreed with FluxusSource
2026-08-06; three columns are reported and **C is the one that answers H4**.

    A   still <300 after pre_enrich  /  all rows reaching scoring
    B   still <500 after pre_enrich  /  all rows reaching scoring
    C   still <500 after pre_enrich  /  rows that ENTERED pre_enrich     <-- H4

300 vs 500: `pre_enrich` fires below **500**
(`NexusMind/config/app.yaml:171`, `content_threshold: 500`; `needs_enrichment()`
is `len(content) < content_threshold`). 300 is the separate labelling-time floor
(llm-distillery#93) and is reported only because A is what LD#93 step 4 will want.

Deriving "entered pre_enrich" without a stamp for it
----------------------------------------------------
Pre-enrichment runs BEFORE scoring, so `len(content)` on the persisted row is the
POST-enrich length. Two fields carry the before-state:

    pre_enriched              True when content was replaced
    original_content_length   pre-enrich length, present iff pre_enriched

    entered   = pre_enriched OR len(content) < 500
                (a row still under 500 and not enriched was a candidate whose
                 fetch failed, or whose domain is skipped, or which had no url)
    succeeded = entered AND len(content) >= 500

Note replacement only requires the fetched text to beat 300 chars and be longer
than the original (`article_fetcher.py:503`), so an ENRICHED row can still sit
under 500 and correctly counts as a failure for C.

Do NOT use `content_length` for any window ending on or before 2026-08-08 — the
llm-distillery#93 scoring-time stamp was computed and then lost before persistence
(0 of 50,605 rows; ducroq/NexusMind#300). **That is FIXED as of the 2026-08-08
17:10 cycle** and the stamp now populates 100% of rows in all six filters
(re-verified 2026-08-12: 3,242/3,242 on `belonging`). Rows written before that
cycle still have it absent, so the derivation above remains the portable one.
It lives at `nexus_mind_attributes.<lens>.content_length`, never `analysis.*`.

Unit of analysis
----------------
**Pooled by family is the verdict.** H4's mechanism (canonical URL vs a
`batchexecute` redirect) has no country term, so country is a nuisance variable
and pooling is the correct unit rather than a power compromise. The per-country
split is printed as a **diagnostic on that pooling assumption**: if rates within
a family diverge beyond noise, pooling is falsified and that is a finding to
report BEFORE the pooled number, not a footnote after it.

Usage:
    python3 measure_enrichable_rate.py --start 2026-07-31 --end 2026-08-08  # THE window
    python3 measure_enrichable_rate.py --start 2026-08-03 --end 2026-08-06   # dry run

    (the pre-2026-08-12 example read `--end 2026-08-14`, aimed at a gate that
     closed on 08-08 and at rows that stop existing on 08-09)
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
from collections import defaultdict

SHORT_LABEL, ENRICH_THRESHOLD = 300, 500

FAMILIES = ("gnews_eval", "newsdata_eval", "gdelt_constructive")


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def arm_of(source: str, url: str):
    """(family, country) for an eval arm, ('gn_proxy', None) for the baseline, else None."""
    for fam in FAMILIES:
        if source.startswith(fam):
            tail = source[len(fam):].lstrip("_")
            return fam, (tail or "?")
    if "news.google.com" in (url or ""):
        return "gn_proxy", None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lens", default="solutions",
                    help="which filtered/<lens>/ store to walk. ⚠️ THE ORIGINAL "
                         "RATIONALE FOR THIS DEFAULT EXPIRED ON 2026-08-08. It was "
                         "'solutions' excluded_source_types match nothing that "
                         "exists, so its store drops no rows (measured 2026-08-06)'. "
                         "Since 2026-08-08 07:43 all six live filters exclude "
                         "eval_aggregator (NexusMind 9fb441a), which is exactly the "
                         "type_classification carried by this script's three "
                         "treatment arms — so from 2026-08-09 they are scored and "
                         "then dropped, and NO lens store contains them. Changing "
                         "--lens does not recover them; see the empty-arm banner.")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD inclusive")
    ap.add_argument("--drop-eval-query", default="Chad",
                    help="exact eval_query value to exclude (the poisoned English "
                         "batch); the French 'Tchad' is kept")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    s, e = args.start.replace("-", ""), args.end.replace("-", "")
    files = [f for f in sorted(glob.glob(f"data/filtered/{args.lens}/filtered_2026*.jsonl"))
             if s <= re.search(r"_(\d{8})_", f).group(1) <= e]
    if not files:
        raise SystemExit(f"no cycle files in {args.start}..{args.end}")

    # stats[(family, country)] -> counters
    st = defaultdict(lambda: dict(rows=0, entered=0, fail_c=0, fail_a=0, fail_b=0,
                                  eq_present=0, dropped=0))
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                arm = arm_of(r.get("source") or "", r.get("url") or "")
                if not arm:
                    continue
                fam, country = arm

                md = r.get("metadata") or {}
                eq = r.get("eval_query", md.get("eval_query"))
                key = (fam, country)
                if eq is not None:
                    st[key]["eq_present"] += 1
                    if eq == args.drop_eval_query:
                        st[key]["dropped"] += 1
                        continue

                a = (r.get("nexus_mind_attributes") or {}).get(args.lens) or {}
                n_now = len(r.get("content") or "")
                enriched = bool(a.get("pre_enriched"))

                d = st[key]
                d["rows"] += 1
                d["fail_a"] += n_now < SHORT_LABEL
                d["fail_b"] += n_now < ENRICH_THRESHOLD
                if enriched or n_now < ENRICH_THRESHOLD:
                    d["entered"] += 1
                    d["fail_c"] += n_now < ENRICH_THRESHOLD

    # ---- fail loud when an eval arm has silently emptied ----
    # arm_of() prefix-matches FAMILIES against `source`; anything unmatched returns
    # None and is skipped, and `fams` below is built from what was FOUND. So when an
    # arm stops appearing, the harness drops it, prints the baseline alone and exits
    # 0 — nothing separates "the treatment is gone" from "the treatment measured
    # nothing". Diagnosed 2026-08-12 with the FluxusSource session; the two known
    # causes are ordered below by which one is confirmed.
    # `rows > 0`, NOT key presence: `st` is a defaultdict and the eval_query cut
    # above touches st[key]["eq_present"] BEFORE its `continue`, so an arm whose
    # every row in the window was dropped as --drop-eval-query exists as a key
    # with rows=0. Keying on presence would leave the guard silent in exactly the
    # case it exists for, and the pooled table would print a 0-row arm as if it
    # were a measurement. Caught by this repo's own review battery, 2026-08-12.
    present_fams = {f for (f, _), d in st.items() if d["rows"] > 0}
    missing = [f for f in FAMILIES if f not in present_fams]
    if missing:
        print("=" * 74)
        print("EVAL ARM(S) EMPTY — read this before any number below")
        print("=" * 74)
        for f in missing:
            print(f"  {f}: 0 rows in {args.start}..{args.end}")
        print("\nAn empty arm and a dropped arm are indistinguishable in this store.")
        print("Two known causes, most likely first:")
        print("  1. CONFIRMED, and it is not upstream. Since 2026-08-08 07:43 all six")
        print("     live filters exclude `eval_aggregator` (NexusMind 9fb441a), which")
        print("     is these arms' type_classification. They are collected, they reach")
        print("     data/raw (verified 08-09..08-11), they are SCORED — and then the")
        print("     NM#189 source filter drops them, so they never enter any lens")
        print("     store. Changing --lens does not help.")
        print("  2. ADR-007 Decisions 2/3 retire all three at the source (`eda28eb`,")
        print("     reported by FluxusSource as reaching production 2026-08-11 16:56")
        print("     CEST — their verification, not re-checked here). After that they")
        print("     are gone upstream too, and no NexusMind change recovers them.")
        print("\nTHERE IS NO REMEDY FOR A WINDOW AFTER 2026-08-08 — do not go looking.")
        print("  data/raw is PRE-enrichment, so it cannot answer a question whose")
        print("  subject is what enrichment did. `source_filter shadow_mode` stamps")
        print("  forward-only and cannot recover already-dropped rows, and there is")
        print("  no future arm data to stamp. Both were considered and rejected with")
        print("  FluxusSource on 2026-08-12; see the module docstring.")
        print("\nFluxusSource confirmed collection ran continuously to the last arm")
        print("yield at 2026-08-11T14:06Z, so a window in 08-09..08-11 distinguishes")
        print("the two: rows present in data/raw and absent here means cause 1.")
        if len(missing) == len(FAMILIES):
            print("\nAll eval arms are empty: there is nothing to compare the gn_proxy")
            print("baseline against. Refusing to print a comparison. (exit 2)")
            raise SystemExit(2)
        print("\nContinuing with a PARTIAL comparison — the pooled figures below")
        print("cover only the arms that are present.\n")

    print(f"window {args.start}..{args.end}   {len(files)} cycles   lens={args.lens}")
    print(f"excluded eval_query == {args.drop_eval_query!r} (Tchad kept)\n")

    def agg(keys):
        t = dict(rows=0, entered=0, fail_c=0, fail_a=0, fail_b=0, eq_present=0, dropped=0)
        for k in keys:
            for f in t:
                t[f] += st[k][f]
        return t

    fams = [f for f in (*FAMILIES, "gn_proxy") if any(k[0] == f for k in st)]

    # ---- diagnostic FIRST: does pooling hold within each family? ----
    print("=" * 74)
    print("POOLING DIAGNOSTIC — do countries within a family agree within noise?")
    print("(if they diverge, pooling is falsified and the pooled figure below is void)")
    print("=" * 74)
    verdict = {}
    for fam in fams:
        keys = sorted(k for k in st if k[0] == fam)
        if fam == "gn_proxy" or len(keys) < 2:
            continue
        print(f"\n{fam}")
        ivs = []
        for k in keys:
            d = st[k]
            if not d["entered"]:
                print(f"   {k[1]:>4}  entered=0  — no signal")
                continue
            p = d["fail_c"] / d["entered"]
            lo, hi = wilson(d["fail_c"], d["entered"])
            flag = "  [diagnostic-only, n<40]" if d["entered"] < 40 else ""
            print(f"   {k[1]:>4}  C={p:6.1%}  n={d['entered']:4}  95% CI {lo:5.1%}-{hi:5.1%}{flag}")
            if d["entered"] >= 40:
                ivs.append((k[1], lo, hi))
        if len(ivs) >= 2:
            overlap = max(l for _, l, _ in ivs) <= min(h for _, _, h in ivs)
            verdict[fam] = overlap
            print(f"   -> intervals {'OVERLAP — pooling holds' if overlap else 'DISJOINT — POOLING FALSIFIED'}")
        else:
            verdict[fam] = None
            print("   -> fewer than 2 countries with n>=40; pooling untestable here")

    # ---- the verdict number ----
    print("\n" + "=" * 74)
    print("POOLED BY FAMILY — this is the H4 number for ADR-007")
    print("=" * 74)
    print(f"{'arm':<20}{'rows':>7}{'entered':>9}{'C fail':>9}{'C':>8}   95% CI        A       B")
    out = {}
    for fam in fams:
        d = agg([k for k in st if k[0] == fam])
        if not d["rows"]:
            continue
        c = d["fail_c"] / d["entered"] if d["entered"] else float("nan")
        lo, hi = wilson(d["fail_c"], d["entered"])
        a = d["fail_a"] / d["rows"]
        b = d["fail_b"] / d["rows"]
        note = ""
        if verdict.get(fam) is False:
            note = "   <-- POOLING FALSIFIED, do not quote"
        elif d["entered"] < 40:
            note = "   <-- diagnostic only"
        print(f"{fam:<20}{d['rows']:>7}{d['entered']:>9}{d['fail_c']:>9}{c:>8.1%}"
              f"   {lo:5.1%}-{hi:5.1%}  {a:6.1%}  {b:6.1%}{note}")
        out[fam] = dict(d, C=c, C_lo=lo, C_hi=hi, A=a, B=b,
                        pooling_holds=verdict.get(fam))

    print("\nC = still <500 chars after pre_enrich, among rows pre_enrich attempted. "
          "LOWER IS BETTER.")
    print("A = still <300 / all scored rows.  B = still <500 / all scored rows.")

    # ---- provenance coverage, so the Chad cut isn't overclaimed ----
    print("\n" + "=" * 74)
    print("eval_query COVERAGE (the Chad/Tchad cut is only exact where this is 100%)")
    print("=" * 74)
    for fam in fams:
        if fam == "gn_proxy":
            continue
        d = agg([k for k in st if k[0] == fam])
        tot = d["rows"] + d["dropped"]
        cov = d["eq_present"] / tot if tot else 0.0
        print(f"   {fam:<20} stamped {d['eq_present']:>4}/{tot:<5} ({cov:5.1%})   "
              f"dropped as {args.drop_eval_query!r}: {d['dropped']}")
    print("   newsdata_eval / gdelt_constructive only carry eval_query from "
          "FluxusSource d78f4f8 (2026-08-06 ~13:10 UTC) forward.")

    print("\nCAVEATS FOR THE READOUT")
    print("  - gdelt_constructive is clock phase-locked (FluxusSource#132): per-country")
    print("    VOLUME is unreadable and time-of-day composition is suspect. Rates here")
    print("    are per-row within an arm, which is fine; do not read counts as volume.")
    print("  - denominator is 'reached scoring AND not source-type-excluded'. Measured")
    print("    2026-08-06: no GN proxy and no eval arm carries an excluded type, so")
    print("    nothing is dropped on that account for this comparison. ⚠️ THAT HOLDS")
    print("    ONLY FOR WINDOWS ENDING ON OR BEFORE 2026-08-08. From 08-09 the eval")
    print("    arms ARE source-type-excluded in all six filters (NexusMind 9fb441a),")
    print("    which is why they read zero here rather than reading a worse rate.")
    print("  - a 100% C for gn_proxy is NOT an artifact of enrichment skipping GN.")
    print("    Verified 2026-08-06: SKIP_DOMAINS is empty ('we try fetching everything")
    print("    now', article_fetcher.py:293), pre_enrich() receives the same article")
    print("    list about to be scored (main.py:873), and GN rows are all <500 chars,")
    print("    so they are candidates by construction. Independent confirmation that")
    print("    none was ever replaced: replacement requires the fetched text to be")
    print("    >=300 chars (article_fetcher.py:503), and the LONGEST GN row in the")
    print("    dry-run window is 277 chars. The flag and the length agree.")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"window": [args.start, args.end], "cycles": len(files),
                       "lens": args.lens, "families": out,
                       "per_country": {f"{k[0]}/{k[1]}": v for k, v in st.items()}},
                      fh, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
