#!/usr/bin/env python3
"""Re-score a saved refcheck.py `--docs` log under TODAY's tier rule.

llm-distillery#134 step 2. The drift comparison in
`docs/decisions/2026-09-17-refcheck-docs-tier.md` needs the 2026-08-28 run scored the
same way as the current one, and the 2026-08-28 run is a stored log, not a re-runnable
state of the tree. Without this the historical side of the comparison is hand-derived —
and a hand-built population is what every measurement error this project has made turned
out to be.

⚠️ WHAT THIS CANNOT DO. It re-tiers what the OLD instrument reported; it cannot re-run
the old instrument. Between the two runs rung 3 left the STALE `resolves` disjunction
(`ad32356`), which can only REMOVE findings, so a delta computed across them is a LOWER
BOUND. And the routed-into override is applied against TODAY's `CLAUDE.md` and
`memory/MEMORY.md`, because the old run's copies are not in the log: a file routed into
today but not in August is scored live on both sides. Both biases are stated beside any
number this produces.

⛔ It reads the FINDINGS section only. The resolved/placeholder/skipped sections are
dispositions, not findings, and counting them would silently change the quantity.

    python3 scripts/analysis/refcheck_tier_reparse.py \\
        docs/evidence/2026-08-28-refcheck-docs/refcheck_docs_run.log
"""
import argparse
import collections
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FINDING_RE = re.compile(r"^  (\S+)\s+(\S+)\s+(\S.*)$")

sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures", "reference-integrity"))


def _tier_rule():
    """Import the LIVE tier rule from refcheck.py rather than restating it.

    ⛔ A second copy of the rule is the whole defect this script exists to avoid. The
    module runs its report at import, so it is read and exec'd with the report stripped —
    ugly, and still better than a duplicate that drifts.
    """
    path = os.path.join(ROOT, "tests", "fixtures", "reference-integrity", "refcheck.py")
    src = open(path).read()
    cut = src.index('print("="*96); print("STEP 4')
    # `__file__` is how refcheck.py finds ROOT, and exec() does not supply one.
    # `for doc in []` stops it reading the scan set; the report is already cut off.
    ns = {"__name__": "_refcheck_rule", "__file__": path}
    # ⚠️ argv is hidden from it. refcheck.py's argument guard runs at module level and
    # rejects anything that is not one of its own flags — including THIS script's log
    # path, which it saw as a positional argument on the first run. The guard working is
    # the reason this line exists.
    saved = sys.argv
    sys.argv = [saved[0]]
    try:
        exec(compile(src[:cut].replace("for doc in DOCS:", "for doc in []:"),
                     path, "exec"), ns)
    finally:
        sys.argv = saved
    return ns["_tier_of_doc"], ns["_routed_targets"]()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="a saved `refcheck.py --docs` run")
    args = ap.parse_args()

    tier_of, routed = _tier_rule()
    text = open(args.log).read()
    if "### FINDINGS" not in text:
        raise SystemExit(f"{args.log}: no ### FINDINGS section — not a refcheck log")
    body = text.split("### FINDINGS", 1)[1].split("### RESOLVED", 1)[0]

    header = re.search(r"### FINDINGS \((\d+) unique", "### FINDINGS" + body)
    counts, hits, seen = collections.Counter(), collections.defaultdict(set), set()
    for line in body.splitlines()[1:]:
        m = FINDING_RE.match(line)
        if not m:
            continue
        key = m.groups()
        if key in seen:
            continue
        seen.add(key)
        doc = m.group(1)
        if not doc.startswith("docs/"):
            counts["non-docs"] += 1
            continue
        t = tier_of(doc, routed)
        counts[t] += 1
        hits[t].add(doc)

    # ⛔ WHICH TIERS THE LOG COULD CONTAIN. A tier the run never scanned must print
    # "not scanned", never 0 — the same rule refcheck.py's own report follows, and the
    # first version of THIS script broke it in the commit that added the rule there: on a
    # `--docs-live` log it printed `FROZEN 0`, a verdict over a population with no frozen
    # files in it, and on a default-run log it printed 0 for both.
    flags = re.search(r"^docs scanned:.*?flags: (.*?)   ", text, re.M)
    if not flags:
        raise SystemExit(f"{args.log}: no `flags:` line in the header, so which tiers "
                         f"this run scanned is unknown — refusing to print a tier count. "
                         f"Logs written before 2026-09-17 omit it on the default branch.")
    words = flags.group(1).split()
    scanned = {"live": "--docs" in words or "--docs-live" in words,
               "frozen": "--docs" in words or "--docs-frozen" in words}

    total = sum(counts.values())
    print(f"{args.log}")
    print(f"  flags in effect: {flags.group(1).strip()}")
    print(f"  parsed {total} unique findings"
          + (f" (the log's own header says {header.group(1)})" if header else ""))
    for t in ("live", "frozen"):
        if not scanned[t]:
            print(f"  {t.upper():9s} not scanned")
            continue
        print(f"  {t.upper():9s} {counts[t]:4d} in {len(hits[t])} file(s) with findings")
    if counts["non-docs"]:
        print(f"  NON-DOCS  {counts['non-docs']:4d}")
    # ⛔ The reconciliation is the point: buckets that sum to the total are guaranteed by
    # construction, so this checks them against the log's OWN header, an independent
    # counter written by the instrument that produced the lines.
    #
    # ⛔ AND IT MUST BE ABLE TO SAY NO. The first version guarded the mismatch with
    # `if header and ...` and printed "reconciles" unconditionally — so on a log with no
    # header (a trimmed excerpt, a grep-filtered file, upstream's checker) it claimed a
    # reconciliation it had not performed. An instrument that cannot fail cannot confirm.
    if not header:
        raise SystemExit("  NO `### FINDINGS (N unique` HEADER — nothing independent to "
                         "reconcile against. Do not quote these counts.")
    if total != int(header.group(1)):
        raise SystemExit(f"  MISMATCH: buckets sum to {total}, the log header says "
                         f"{header.group(1)} — do not quote either number")
    print("  reconciles against the log's own header")


if __name__ == "__main__":
    main()
