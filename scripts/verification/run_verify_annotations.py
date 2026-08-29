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
# ⚠️ CASE-INSENSITIVE since #137: `echo "fail: 2 rows"` asserted nothing under an
# uppercase-only pattern and was silently downgraded to NO-ASSERTION — never run.
#
# ⛔ AND NO LEADING `\b` ON THE VERDICT WORDS. This is #137's shape 1 one stage
# EARLIER than the issue describes it — not in reading the output, but in deciding
# whether to run the block at all. `printf '\033[31mFAIL: ...'` and a UTF-8 BOM
# both put a WORD character (`m`, `\xbf`'s tail) immediately before `FAIL`, so
# `\bFAIL\b` did not match and the block was classified NO-ASSERTION: never
# executed, no output line, exit 0. Found 2026-08-29 by the seeded fixture for
# shape 1, which is the point of seeding them.
#
# ⚠️ THE ASYMMETRY IS DELIBERATE. Over-matching here costs a block being RUN that
# asserts nothing — visible, cheap, self-correcting. Under-matching costs a real
# check never running and reporting nothing at all. Bias this pattern loose.
ASSERTS = re.compile(r"PASS\b|FAIL\b|CANNOT VERIFY|\bexit 1\b", re.I)

# ---------------------------------------------------------------- normalisation
# llm-distillery#137. A verdict word is only findable if nothing sits in front of
# it, and this repo writes its guards with exactly the things that do: `⛔ FAIL:`,
# `✗ FAIL`, `- FAIL`, `**FAIL**`, a UTF-8 BOM, and ANSI colour. All six were
# reproduced as fail-open — a genuinely failing block tallied `pass`, exit 0.
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# Anything that is not a letter, digit or underscore, stripped from the left. This
# deliberately also eats `- `, `* `, `> `, `#` and quotes.
LEAD_DECOR = re.compile(r"^[^\w]+")


def normalise(line):
    """A line reduced to what a verdict matcher should see.

    ⚠️ THE ORDER MATTERS: BOM, then ANSI, then leading decoration — an ANSI escape
    begins with ESC `[`, which `LEAD_DECOR` would happily eat halfway, leaving
    `31mFAIL` and no match. Strip the structured things before the unstructured one.
    """
    return LEAD_DECOR.sub("", ANSI.sub("", line.lstrip("\ufeff")).strip())


def strip_comments(cmd):
    """`cmd` with shell comments removed, for CLASSIFICATION ONLY — never for
    execution.

    ⛔ #137 shape 4: `REMOTE` matched the whole annotation text, so
    `... exit 1 # baseline measured on b650` was reclassified as a remote check and
    printed NO LINE AT ALL. A word in a trailing comment removed a failing local
    check from the report. Quote-aware because `echo "# not a comment"` is not one.
    """
    out, quote = [], None
    for ch in cmd:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out)


def _unterminated_quote(cmd):
    """The quote character the command ends inside, or None.

    ⚠️ COUNTING QUOTES IS THE WRONG TEST, and it is the one written first here:
    `echo "it's fine"` has ONE apostrophe and would have been refused as severed.
    A quote inside the other kind of quote is not a quote — track the state. Same
    reasoning as `strip_comments`, which is why neither may become a character count.
    """
    quote = None
    for ch in cmd:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
    return quote


def looks_truncated(cmd):
    """True when the extracted command cannot be the whole command.

    ⛔ #137 shape 6: `BLOCK` is non-greedy, so a `-->` INSIDE the command ends the
    match early and the runner executes a fragment — `echo "count 3 --> expected 5"`
    became `echo "count 3 `, which exits 0 and reports pass. Widening the regex is
    not the fix (it would swallow the next annotation whole); refusing to run an
    obviously-severed command is. Ending INSIDE a quote is the signature.

    ⚠️ A false TRUNCATED silences a healthy annotation, so this errs toward running.
    """
    return _unterminated_quote(cmd) is not None
# ⚠️ …but a block that DELEGATES to a project script asserts through that script's
# exit code, and the verdict word lives in the script rather than the annotation.
# Classifying on the annotation text alone put `bash scripts/verification/
# check_prod_filters_table.sh` in NO-ASSERTION — a script whose header comment
# reads "Prints exactly one word: PASS or FAIL". The classifier was reading the
# wrong object, which is the same error it exists to catch.
def _verdict_re(word):
    """Where a verdict word actually means a verdict.

    Three shapes, and only three: it opens the line (`FAIL: 2 rows disagree`), it
    introduces a detail (`prod-filters: FAIL: ...`), or it closes one
    (`check X: FAIL`). ⛔ Anything looser matches healthy output — "0 FAILures",
    "no FAIL lines found" — and a check that cries wolf gets ignored, which is how
    a real failure ends up unread.
    """
    w = re.escape(word)
    return re.compile(rf"^{w}\b|\b{w}:|\b{w}\s*[.!]?$")


VERDICT_HIT = {w: _verdict_re(w) for w in ("FAIL", "CANNOT VERIFY")}


def _first_verdict(word, raw_lines, norm_lines):
    """The first RAW line whose NORMALISED form carries `word` as a verdict.

    Raw is what gets reported (the reader wants the glyphs and colour the guard
    actually printed); normalised is what gets matched.
    """
    return next((raw for raw, n in zip(raw_lines, norm_lines)
                 if VERDICT_HIT[word].search(n)), None)
# ⚠️ EVERY INVOCATION SHAPE THIS REPO ACTUALLY USES, not the ones it used in
# February. #137 shape 5: `.venv/bin/python scripts/x.py` was NO-ASSERTION — and
# `memory/`'s own instruction is to prefer the venv python over `python3`, so
# following this repo's advice DISABLED the annotation. `pytest`, and a bare
# relative path with no `./`, had the same problem.
DELEGATES = re.compile(
    r"(^|[|;&(]\s*|\b[A-Z_]+=\S+\s+)"
    r"((\./|[\w./-]*/)?(bash|sh|python3?|pytest)\b|\./|"
    r"(scripts|tests|training|ground_truth)/\S+\.(py|sh))")

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
    if looks_truncated(c):
        return "truncated", ("unbalanced quote — a `-->` inside the command ended "
                             "the match early; the runner would execute a fragment")
    # ⚠️ CLASSIFY ON THE COMMAND WITHOUT ITS COMMENTS. See strip_comments.
    c = strip_comments(c) or c
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

    tally = dict(passed=0, failed=0, errored=0, skipped=0, remote=0, noassert=0,
                 truncated=0)
    failures = []
    empties = []
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
            # ⚠️ PROSE ABOUT AN ANNOTATION IS NOT AN ANNOTATION. `BLOCK` matches any
            # `<!-- verify: ... -->`, including the empty one that appears when a
            # memory file QUOTES the idiom -- `memory/working-rules.md` names it
            # twice while explaining a rule about it. Those were counted in
            # `blocks found` and in `skipped`, inflating the denominator of a report
            # whose whole job is to say how much was checked. Found 2026-08-29 when
            # adding a third made the count move for no reason.
            #
            # ⛔ THEY ARE COUNTED AND NAMED, NOT DROPPED. An EMPTY annotation may
            # also be one someone opened and never filled, which is a real defect
            # and must not vanish into a silent skip.
            if not cmd.strip():
                empties.append(f"{doc} #{i}")
                continue
            total_blocks += 1
            kind, reason = classify(cmd)
            if kind == "remote" and not args.remote:
                tally["remote"] += 1
                continue
            if kind == "skip":
                tally["skipped"] += 1
                continue
            # ⛔ A SEVERED COMMAND IS A DEFECT, NOT A SKIP. Running the fragment is
            # what made #137 shape 6 fail open; skipping it silently would be the
            # same result with better manners. It counts as a failure.
            if kind == "truncated":
                tally["truncated"] += 1
                failures.append((doc, i, reason))
                print(f"  TRUNCATED     {doc} #{i}  {reason}")
                continue
            if kind == "noassert":
                tally["noassert"] += 1
                if not args.quiet:
                    print(f"  NO-ASSERTION  {doc} #{i}  ({reason})")
                continue
            try:
                r = subprocess.run(["bash", "-c", cmd.strip()], cwd=ROOT,
                                   capture_output=True, text=True, timeout=TIMEOUT)
                # ⛔ #137 shape 3: `r.stdout + r.stderr` glued the first stderr
                # line onto a stdout tail with no trailing newline —
                # `ok` + `FAIL: regressed` became `okFAIL: regressed`, and the
                # verdict was no longer at the start of any line.
                # `check_content_length_populated.sh` already writes its failure
                # sentence to stderr, so this was live, not theoretical.
                out = (r.stdout.splitlines() + r.stderr.splitlines())
                out = [l for l in out if l.strip()]
                last = out[-1] if out else "(no output)"
                # ⚠️ A VERDICT IS EMITTED ON ITS OWN LINE, NOT NECESSARILY THE
                # LAST ONE. A guard that prints "FAIL:" and then lists the offending
                # rows leaves a data row last, so reading `last` alone calls the
                # failure a pass: `check_prod_filters_table.sh` had been printing
                # FAIL for four days and being tallied `pass` when /audit-context
                # found it on 2026-08-29.
                #
                # ⚠️ BUT A BARE SUBSTRING SEARCH IS THE OPPOSITE ERROR — "0 FAILures"
                # and "no FAIL lines found" are healthy output. `VERDICT_HIT` takes
                # the verdict word only where a verdict actually appears: opening the
                # line, followed by a colon, or closing the line ("check X: FAIL").
                #
                # ⚠️ NORMALISE FIRST (#137 shape 1). `⛔ FAIL:`, `**FAIL**`, `- FAIL`,
                # a UTF-8 BOM and `\033[31m` all sit in front of the verdict word,
                # and this repo writes its guards with exactly those glyphs. All six
                # were reproduced as fail-open: a genuinely failing block, exit 0,
                # tallied `pass`.
                norm = [normalise(l) for l in out]
                # ⚠️ FAIL BEATS CANNOT VERIFY (#137 shape 9). A single `next()` over
                # both words took whichever came first, so a real FAIL under an
                # earlier CANNOT VERIFY line was downgraded to "could not check".
                fail_line = _first_verdict("FAIL", out, norm)
                cv_line = _first_verdict("CANNOT VERIFY", out, norm)
            except subprocess.TimeoutExpired:
                tally["errored"] += 1
                failures.append((doc, i, f"TIMEOUT after {TIMEOUT}s"))
                print(f"  TIMEOUT       {doc} #{i}  (VERIFY_TIMEOUT={TIMEOUT})")
                continue
            # Report the verdict line when there is one; `last` is only a fallback
            # for a check that asserts through its exit code alone.
            shown = fail_line or cv_line or last
            # ⚠️ DO NOT cite "0 of N blocks emit that shape" as evidence for any of
            # this. `failed=0` today, so no block emits a FAIL-bearing line at all
            # and that zero is vacuous — the instrument could not have said yes.
            # (Counts are flag-dependent too.) Every shape handled here was
            # reproduced against a fixture in tests/unit/test_verify_annotation_runner.py,
            # which is what "it fires" means; the live run proves only no regression.
            # ⛔ #137 shape 8 — CANNOT VERIFY IS TESTED FIRST, AND THAT IS THE
            # WHOLE POINT OF THE ARM. `r.returncode != 0` came first, so every
            # guard that returns a non-zero exit WITH a "CANNOT VERIFY" line —
            # `check_index_budget.py` does in five branches,
            # `check_content_length_populated.sh` exits 2 on an unreachable host —
            # was reported as a broken invariant. An unreachable box read as a
            # regression, which is the expensive direction to be wrong in: it sends
            # someone hunting a defect that does not exist and teaches them the
            # report cries wolf.
            if cv_line and not fail_line:
                tally["errored"] += 1
                failures.append((doc, i, cv_line))
                print(f"  CANNOT VERIFY {doc} #{i}  {cv_line}")
                continue
            if r.returncode != 0 or fail_line:
                tally["failed"] += 1
                failures.append((doc, i, shown))
                print(f"  FAIL          {doc} #{i}  {shown}")
            else:
                tally["passed"] += 1
                if not args.quiet:
                    # ⚠️ #137 shape 7: a block that printed NOTHING and exited 0
                    # was reported as `pass  (no output)`, indistinguishable from a
                    # guard that said PASS. It is still a pass — the exit code is
                    # the assertion for the scripts that work that way — but it must
                    # not look like a verdict. Say which one you are reading.
                    note = "" if out else "  [no output — exit code only]"
                    print(f"  pass          {doc} #{i}  {last[:90]}{note}")

    print()
    if empties:
        print(f"  NOTE: {len(empties)} empty `verify:` comment(s), not executed and "
              f"not counted below — prose quoting the idiom, or an annotation left "
              f"unfilled: {', '.join(empties)}")
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
