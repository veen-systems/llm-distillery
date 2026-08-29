#!/usr/bin/env python3
"""Extract and EXECUTE every `<!-- verify: -->` annotation in the context layer.

An annotation is a mechanism, not a comment. This project's own working rule is on
its 14th recorded occurrence of shipping a mechanism that never ran, and one of
those occurrences *was* a twelve-line verify annotation that could not be extracted.
Until 2026-08-16 nothing in this repo ran these: 42 annotations sat in the live
topic files with no runner, and the two in CLAUDE.md had only ever been executed by
hand.

    python3 scripts/verification/run_verify_annotations.py            # local only
    python3 scripts/verification/run_verify_annotations.py --remote   # include ssh
    python3 scripts/verification/run_verify_annotations.py --sessions # include logs

Exit 0 if every executed block passed, 1 if any failed or errored, 2 if the
population itself is empty (see below).

Three findings from building it, each of which shapes the code:

  * ⚠️ A BLOCK THAT EXITS NON-ZERO MUST NOT HALT THE RUN. Executing the four
    CLAUDE.md annotations as one concatenated script stopped at the first `exit 1`
    and silently never reached the last two. Each block gets its own subprocess.

  * ⚠️ COUNTING ANNOTATIONS IS NOT COUNTING MECHANISMS. Of 42 in the live topic
    files, 21 are executable; the rest are `manual — …` notes, empty spans, `...`,
    or idiom templates (`curl https://endpoint | grep expected`). They are SKIPPED
    AND COUNTED, never dropped — a silent skip reads exactly like a pass.

  * ⛔ A BLOCK THAT PRINTS A NUMBER AND ASSERTS NOTHING IS NOT A CHECK. Eight blocks
    in `cross-repo-prioritization.md` print issue counts with nothing comparing them
    to what the document claims, so they cannot fail. They are reported separately
    as NO-ASSERTION rather than counted as passes.

⚠️ KNOWN LIMITATION, STATED RATHER THAN HIDDEN: `classify()` judges a block by its
SPELLING — regexes over the annotation text. That is the weaker method. pipeline-atlas
built the same gate independently (its #19/#24, #32) and found that its first draft
was an instance of the defect it was written against: it re-implemented `grep` to
decide whether a branch could match, and returned four false verdicts on live input
because `-l` prints filenames, `-n` prefixes `path:lineno:`, and BRE parens are
literal. **An instrument that re-implements the thing it is judging agrees with its
author.** Their fix is the right one and is not implemented here: decide from the
command's OUTPUT by re-running it with the asserted token swapped, so the real tool
does the matching.

Until that exists, the obligation is manual and non-negotiable: **when you add or
change a `<!-- verify: -->` block, MUTATION-TEST IT IN THREE DIRECTIONS before
trusting a PASS.**

    1. present        -> must PASS
    2. absent         -> must FAIL
    3. MENTIONED BUT NOT PRESENT -> must FAIL

⛔ **Direction 3 matters MOST for a PRESENCE check, and the costs are asymmetric.** An
absence check fooled by prose over-claims — it reports a problem that is not there, and
someone investigates and finds nothing. A presence check fooled by prose says the
mechanism is live **when it has been deleted**, and *nobody investigates a green*. Same
requirement, opposite consequence. (pipeline-atlas, who then found the shape in their
own convention page's worked EXAMPLE — the one line most likely to be copied.)

⛔ **Direction 3 is the one that gets skipped and the one that catches real defects.**
A `grep` cannot separate an invocation from a mention, and restricting the file type
does not help. On 2026-08-16 two sessions in this estate each shipped a green probe
measuring the wrong object within the same hour: here, a probe that read the second
ordinal in the whole file (13) where the answer on its own rule was 8; in NexusMind,
`grep -q "superseded_reprocessed" scripts/main.py` on a word appearing **9 times in
that file including a docstring**, which stayed green with the feature forced off.

⚠️ Both were written *immediately after* the two sessions had told each other that a
mechanism must be the thing that fails. That is not carelessness twice; it is a
property of the activity — **articulating a principle produces the feeling of having
applied it**, so the check is least likely to happen exactly when you have just been
most articulate about needing it. Direction 3 is cheap. Run it anyway. Especially
then.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLOCK = re.compile(r"<!--\s*verify:\s*(.*?)-->", re.S)
REMOTE = re.compile(r"\bssh\b|sadalsuud|b650|gpu-server|situla")
# A verdict word the block itself prints. Without one, an INLINE block cannot fail.
ASSERTS = re.compile(r"\bPASS\b|\bFAIL\b|CANNOT VERIFY|\bexit 1\b")
# ⚠️ …but a block that DELEGATES to a project script asserts through that script's
# exit code, and the verdict word lives in the script rather than the annotation.
# Classifying on the annotation text alone put `bash scripts/verification/
# check_prod_filters_table.sh` in NO-ASSERTION — a script whose header comment
# reads "Prints exactly one word: PASS or FAIL". The classifier was reading the
# wrong object, which is the same error it exists to catch.
# A verdict word at the START of a line. See the comment at the call site: the
# verdict is not reliably the last line of the output.
VERDICT_LINE = re.compile(r"\s*(FAIL|CANNOT VERIFY)\b")
DELEGATES = re.compile(r"(^|[|;&(]\s*|\bPYTHONPATH=\S+\s+)(bash|sh|python3?|\./)\s")

TIMEOUT = int(os.environ.get("VERIFY_TIMEOUT", "120"))


def classify(cmd):
    """Return (kind, reason). Only 'run' is executed."""
    c = cmd.strip()
    if not c:
        return "skip", "empty span"
    if c.startswith("manual"):
        return "skip", "declared manual"
    if c.startswith("...") or c == "…":
        return "skip", "elision"
    if "https://endpoint" in c:
        return "skip", "idiom template, not a real command"
    if REMOTE.search(c):
        return "remote", "needs a remote host"
    if not ASSERTS.search(c) and not DELEGATES.search(c):
        return "noassert", "inline, prints a value, asserts nothing — cannot fail"
    return "run", ""


def docs(include_sessions):
    out = ["CLAUDE.md"]
    for f in sorted(glob.glob(os.path.join(ROOT, "memory", "*.md"))):
        rel = os.path.relpath(f, ROOT)
        if "project_session_" in rel and not include_sessions:
            continue
        out.append(rel)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", action="store_true", help="also run blocks needing ssh")
    ap.add_argument("--sessions", action="store_true", help="also scan session records")
    ap.add_argument("--quiet", action="store_true", help="only print non-PASS results")
    args = ap.parse_args()

    tally = dict(passed=0, failed=0, errored=0, skipped=0, remote=0, noassert=0)
    failures = []
    total_blocks = 0

    for doc in docs(args.sessions):
        path = os.path.join(ROOT, doc)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as exc:
            print(f"  {doc}: UNREADABLE ({exc})")
            tally["errored"] += 1
            continue
        for i, cmd in enumerate(BLOCK.findall(text), 1):
            total_blocks += 1
            kind, reason = classify(cmd)
            if kind == "remote" and not args.remote:
                tally["remote"] += 1
                continue
            if kind == "skip":
                tally["skipped"] += 1
                continue
            if kind == "noassert":
                tally["noassert"] += 1
                if not args.quiet:
                    print(f"  NO-ASSERTION  {doc} #{i}  ({reason})")
                continue
            try:
                r = subprocess.run(["bash", "-c", cmd.strip()], cwd=ROOT,
                                   capture_output=True, text=True, timeout=TIMEOUT)
                out = (r.stdout + r.stderr).strip().splitlines()
                last = out[-1] if out else "(no output)"
                # ⚠️ A VERDICT IS EMITTED ON ITS OWN LINE, NOT NECESSARILY THE LAST
                # ONE. A guard that prints "FAIL:" and then lists the offending rows
                # leaves a data row last, so classifying on `last` alone reads the
                # failure as a pass. `check_prod_filters_table.sh` had been printing
                # FAIL for four days and being tallied `pass` when /audit-context
                # found it on 2026-08-29. Anchor on line-initial verdict words rather
                # than searching the whole blob, or explanatory prose containing the word
                # "FAIL" would classify a healthy check as broken.
                # ⚠️ NOT every guard emits a line-initial verdict, and this anchor does
                # not reach the ones that do not: check_content_length_populated.sh
                # asserts only through its exit code, and oracle_cost.py prints
                # "... MISMATCH" mid-line while its annotation pipes into `grep`,
                # discarding the non-zero exit -- so that block cannot fail under
                # either the old or the new classifier. Anchoring is a partial fix.
                verdict = next((l for l in out if VERDICT_LINE.match(l)), None)
            except subprocess.TimeoutExpired:
                tally["errored"] += 1
                failures.append((doc, i, f"TIMEOUT after {TIMEOUT}s"))
                print(f"  TIMEOUT       {doc} #{i}  (VERIFY_TIMEOUT={TIMEOUT})")
                continue
            # Report the verdict line when there is one; `last` is only a fallback
            # for a check that asserts through its exit code alone.
            shown = verdict or last
            # `or "FAIL" in last` is the PRE-2026-08-29 test, kept so this change is
            # strictly additive on the FAIL path. Anchoring only on line-initial verdicts
            # silently lost a block whose sole verdict is mid-line on the last line
            # ("check X: FAIL"), so the old clause stays; it costs only the
            # false-positive surface that already existed.
            # ⚠️ DO NOT cite "0 of N blocks emit that shape" as evidence here. Today
            # `failed=0`, so NO block emits a FAIL-bearing line at all and that zero is
            # vacuous -- the instrument could not have said yes. (Block counts also
            # depend on flags: 23 run by default, 33 with --sessions.) The argument for
            # the fallback is that the loss is real, not that it is currently unobserved.
            if (r.returncode != 0
                    or (verdict and verdict.lstrip().startswith("FAIL"))
                    or "FAIL" in last):
                tally["failed"] += 1
                failures.append((doc, i, shown))
                print(f"  FAIL          {doc} #{i}  {shown}")
            elif ((verdict and verdict.lstrip().startswith("CANNOT VERIFY"))
                    or "CANNOT VERIFY" in last):
                tally["errored"] += 1
                failures.append((doc, i, shown))
                print(f"  CANNOT VERIFY {doc} #{i}  {shown}")
            else:
                tally["passed"] += 1
                if not args.quiet:
                    print(f"  pass          {doc} #{i}  {last[:90]}")

    print()
    print(f"blocks found: {total_blocks}  |  " + "  ".join(
        f"{k}={v}" for k, v in tally.items()))

    # ⛔ An empty population must never read as success. A renamed directory, a
    # changed comment idiom or a broken regex would otherwise print a clean
    # summary over nothing at all — the same defect this repo found in its own
    # Contract A smoke test on 2026-08-16, which reported CLEAN over 0 rows.
    if total_blocks == 0:
        print("ABORT: 0 annotations found. That is a broken extractor or a moved "
              "directory, NOT a clean result.")
        return 2
    if tally["passed"] == 0 and not args.quiet:
        print("WARNING: nothing was executed — every block was skipped or remote.")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
