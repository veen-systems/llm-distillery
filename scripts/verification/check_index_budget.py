#!/usr/bin/env python3
"""Budget guard for `memory/MEMORY.md`, with a SOFT stage (llm-distillery#123).

Called from the `<!-- verify: -->` block at the head of `memory/MEMORY.md`, which
`scripts/verification/run_verify_annotations.py` executes. That runner classifies a
block delegating to `python3 scripts/...` as `run` and takes the verdict from this
script's exit code, so the annotation itself stays one line.

⚠️ WHY THE LOGIC IS NOT INLINE IN THE FILE IT MEASURES. It used to be: a 364-char
`<!-- verify: -->` one-liner in `memory/MEMORY.md` itself. That has two defects, and
the second is the one that bit.

  * A guard that lives inside its own subject SPENDS the budget it is policing.
    On 2026-08-17 the file stood at 29,998 of 30,000 chars — two characters — and
    adding the soft stage inline would have pushed it over on landing. The fix
    would have tripped the guard.
  * The message could not carry its own history without paying for it in chars,
    so the only thing the file could afford to say was the verdict.

Moving it here made the annotation 67 chars and this file free to be as explicit as
it needs to be.

⛔ WHAT #123 IS ABOUT — read before raising SOFT or removing this stage. The guard
was hard-FAIL only. A session's `/curate` entry that arrives when the file is full
does not get written somewhere visible; it goes somewhere else, silently, and the
index stops being the thing that knows what happened. That is not hypothetical:
`bdfc4e1` and `bf3aa60` (both 2026-08-17) between them spent 1,165 chars the same
day an `/audit-context` trim had bought 1,144, so the file was back at the wall
within twenty-four hours of being cleared. SOFT exists to make that visible while
there is still room to act.

⚠️ SOFT AND HARD ARE NOT THE SAME KIND OF NUMBER. HARD is a real ceiling — above it
the index is too big to be a navigational layer. SOFT is a runway: it is set so the
warning fires while several more entries still fit, because a warning that fires at
the wall is the hard FAIL with extra steps. Entries here measure 400-1,200 chars, so
3,000 chars of runway is roughly three sessions of notice.

⚠️ THE BUDGET IS IN SIZE, NOT LINES, AND THAT IS LOAD-BEARING. The file
reached 54,808 chars in 91 lines on 2026-08-15 — up 69% in three days — because
entries grow by LENGTHENING, not by multiplying. Every line-count heuristic passed
throughout. Do not add one back as the primary check.

⚠️ THE UNIT IS BYTES. Every file here is read `"rb"` and every ceiling is compared
against a byte count, while the numbers were originally reasoned about as
characters. Bytes >= characters, so the guard errs strictly toward failing early —
but say BYTES when quoting it. Reporting a byte headroom as a character headroom is
a mistake this project has already published once (2026-08-26; the 449 above).

    python3 scripts/verification/check_index_budget.py

⚠️ TWO TARGETS SINCE 2026-08-26 (`/audit-context`). The guard covered
`memory/MEMORY.md` only, while the file actually at the wall was `CLAUDE.md` —
39,955 of 40,000 bytes, 449 to spare, with nothing watching it. That is the same
shape #123 fixed here: a budget nobody measures is discovered by crossing it.

⛔ AND THE SAME SHAPE AGAIN ON 2026-08-29 (#138), ONE LAYER OUT. Those two targets
were `CLAUDE.md` — auto-loaded — and `memory/MEMORY.md` — NOT auto-loaded, reached
by a pointer row — while 19,488 B that IS auto-loaded, the USER auto-memory index
at `~/.claude/projects/<slug>/memory/MEMORY.md`, belonged to no target at all. The
guard was wrong by the size of a file it had never heard of, and it had been
measuring a shrinking share of the real quantity ever since. Hence `--target
loaded`, whose subject is the LAYER rather than any one file.

⚠️ OWNER CALL 2026-08-29: THE TOTAL GOVERNS, THE PER-FILE LINES ATTRIBUTE. Do not
read `--target project`'s 40,000 as a competing budget — that is Claude Code's own
wall for that file, the tool's property, not a number chosen here. `--target index`
is likewise not part of the layer; it bounds a navigational file and carries the
#123 session-entry rotation, which is why it survives its subject not being loaded.

⚠️ A BYTE BUDGET IS AN ALARM, NOT THE MECHANISM. #133 measured `CLAUDE.md` growing
~486 B/day against a ceiling that trimming could not outrun, and the thing that
actually held was a CAP PER POINTER ROW (`--target pointers`) — a capped table
cannot grow, which is the property no total ever has. H-CX1 then measured the cap
holding its own scope at +0 B while the file grew 1,055 B one section over. Expect
this target to tell you WHEN to act and never to prevent anything.

    python3 scripts/verification/check_index_budget.py             # index (default)
    python3 scripts/verification/check_index_budget.py --target project
    python3 scripts/verification/check_index_budget.py --target loaded
    python3 scripts/verification/check_index_budget.py --target pointers

The project file has NO session-entry check — it carries no session log, and the
thing that grows there is the pointer table and the Hard Constraints. Its remedy is
the one `/audit-context` step 1 prescribes: move reference material to a topic file
behind a "Before You Start" pointer.

Exit 0 on PASS (with or without a WARN line), 1 on FAIL, 1 if the file is missing
or empty — an unreadable index must never read as a pass.

⚠️ NO PASS OR WARN LINE MAY CONTAIN A VERDICT WORD — say "hard limit", never
"below the FAIL threshold". Since llm-distillery#137 the runner reads a verdict
where one actually appears: opening a line, followed by a colon, or closing a line,
on ANY line of stdout or stderr, after stripping leading glyphs, markdown, a BOM
and ANSI colour. So the old advice ("only the last line matters") is wrong in the
unsafe direction, and the broader rule replaces it: keep the words out of healthy
output. Healthy prose that merely mentions one — "0 FAILures" — is safe by design
and pinned by `tests/unit/test_verify_annotation_runner.py`.

⚠️ AND PUT THE VERDICT LAST. For a PASSING block the runner reports the command's
final line, so a verdict printed first is displayed as whichever detail row came
last. Failures are found wherever they sit; passes are not.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "memory", "MEMORY.md")
PROJECT = os.path.join(ROOT, "CLAUDE.md")

# ------------------------------------------------- the always-loaded layer
# llm-distillery#138. THE MEMBERS ARE WHAT CLAUDE CODE INJECTS AT SESSION START
# WITH NOBODY OPENING A FILE. Established 2026-08-29 by reading a live session's
# own context, not by reading documentation: `CLAUDE.md` and the USER auto-memory
# index both arrived; the in-repo `memory/MEMORY.md` did NOT -- it is reached by a
# pointer row. That is why it keeps its own target below and is not a member here.
#
# ⚠️ MEMBERSHIP IS THE PART THAT ROTS, AND IT IS THE WHOLE POINT. Before today the
# two targets were `CLAUDE.md` and `memory/MEMORY.md`: one file that is auto-loaded
# and one that is not, with 19,488 B that IS auto-loaded belonging to neither. The
# guard was wrong by the size of a file it had never heard of. Re-establish
# membership from a live session before trusting the total -- not from this comment.
#
# ⚠️ OWNER CALL 2026-08-29 (#138): THE TOTAL GOVERNS; THE PER-FILE LINES ATTRIBUTE.
# The total is the quantity that actually costs context, but the remedy is per file
# ("trim the layer" is not an instruction), so both have to print. `PROJECT_HARD`
# below is NOT a second budget: 40,000 is Claude Code's own wall for that one file,
# a property of the tool rather than a number invented here.
#
# THE NUMBERS, AND THE STATE THEY WERE SET AGAINST. The layer stood at 56,933 B
# when #138 was written and at 48,083 B after the same day's removal of the
# auto-memory index's session log (9,160 B, 47% of that file, two sessions stale;
# moved verbatim to `memory/session-log.md`'s appendix, owner call). SOFT is the
# same runway doctrine as the index budget above -- a warning at the wall is the
# hard limit with extra steps -- sized against the ~486-864 B/day that #133 and
# H-CX1 measured on `CLAUDE.md` alone: ~5,000 B of notice is roughly a week.
LOADED_HARD = 60_000
LOADED_SOFT = 55_000

HARD = 30_000  # ceiling: above this the index is no longer a navigational layer
SOFT = 27_000  # runway: ~3,000 chars ≈ three sessions of notice

# CLAUDE.md. HARD is where Claude Code itself warns; SOFT is `/audit-context`
# step 1's soft flag. Both are the skill's numbers, not ones invented here.
PROJECT_HARD = 40_000
PROJECT_SOFT = 35_000

# ⚠️ THE PATH IS A MODULE ATTRIBUTE NAME, NOT THE PATH ITSELF. Freezing
# `INDEX`'s value into this table at import time silently breaks every caller that
# redirects the guard at a fixture — `tests/unit/test_index_budget_guard.py`
# monkeypatches `INDEX`, and against a frozen table the guard cheerfully measured
# the REAL repo index while the test believed it was measuring a temp file. Three
# tests went green-to-red on that alone. Resolve through `getattr` at call time.
TARGETS = {
    "index":   ("INDEX",   "memory/MEMORY.md", HARD,         SOFT,         True),
    "project": ("PROJECT", "CLAUDE.md",        PROJECT_HARD, PROJECT_SOFT, False),
}

# ----------------------------------------------------------- always-loaded
def _auto_memory_index():
    """`~/.claude/projects/<slug>/memory/MEMORY.md`, DERIVED, never hardcoded.

    The slug is the project's absolute path with every non-alphanumeric character
    replaced by `-`. Checked 2026-08-29 against all 40 directories in
    `~/.claude/projects/`, including one carrying a dot in the path
    (`/home/jeroen/repos/.meta/...` -> `-home-jeroen-repos--meta-...`), which is
    why the class is `[^A-Za-z0-9]` and not just `/`.

    ⚠️ THIS DERIVES FROM `ROOT`; CLAUDE CODE DERIVES ITS OWN FROM THE DIRECTORY THE
    SESSION WAS LAUNCHED IN. Those agree when the session starts at the repo root
    and not otherwise -- so a miss is REPORTED AS A MISS, with the path printed,
    and never silently dropped from the sum. Being wrong by the size of a file
    nobody mentions is the defect this whole target exists to fix.
    """
    slug = re.sub(r"[^A-Za-z0-9]", "-", ROOT)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", slug,
                        "memory", "MEMORY.md")


AUTO_MEMORY = _auto_memory_index()

# Attribute names, not paths -- same reason as TARGETS below: a frozen path makes
# every monkeypatching caller measure the real files while believing otherwise.
LOADED_MEMBERS = (
    ("PROJECT",     "CLAUDE.md"),
    ("AUTO_MEMORY", "auto-memory MEMORY.md"),
)


def _check_loaded():
    """Budget the always-loaded layer as ONE number. Returns (exit_code, lines).

    ⚠️ WHY A MISSING MEMBER IS NOT A FAIL. On a machine where Claude Code has never
    run, or from a clone at another path, the auto-memory index genuinely is not
    part of anyone's context and a hard failure would be false. What must never
    happen is the sum quietly shrinking, so every member prints a line either way,
    the verdict carries `N/M files`, and an incomplete sum says so in the verdict
    itself. All members missing IS `CANNOT VERIFY` -- then the guard measured
    nothing, and a guard that measured nothing must never read as a pass.
    """
    rows, total, present = [], 0, 0
    for attr, label in LOADED_MEMBERS:
        path = globals()[attr]
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            rows.append(f"  {label:<24} NOT PRESENT at {path}")
            continue
        raw = open(path, "rb").read()
        total += len(raw)
        present += 1
        rows.append(f"  {label:<24} {len(raw):>7,} B  {raw.count(b"\n"):>4} lines")

    n = len(LOADED_MEMBERS)
    if not present:
        return 1, rows + [f"CANNOT VERIFY: none of the {n} always-loaded files were "
                          f"readable -- the budget measured nothing"]

    short = "" if present == n else (
        f" -- INCOMPLETE: {n - present} of {n} members not present, so this total "
        f"UNDERSTATES the layer by an unknown amount")
    head = f"always-loaded layer {total:,} B over {present}/{n} files"

    # ⚠️ THE VERDICT GOES LAST, AND THAT IS NOT COSMETIC. For a PASSING block
    # `run_verify_annotations.py` reports the command's LAST line (it anchors on a
    # line-initial FAIL/CANNOT VERIFY only for failures), so a verdict printed
    # first is displayed in the verify report as whichever attribution row happened
    # to come last -- "auto-memory MEMORY.md 10,773 B" reported as the result of a
    # budget check. Failures are still found wherever they sit.
    if total >= LOADED_HARD:
        return 1, rows + [f"FAIL {head}, over the {LOADED_HARD:,} hard limit.{short} "
                          f"The remedy is per file -- see the attribution above. Move "
                          f"reference material out of CLAUDE.md behind a 'Before You "
                          f"Start' pointer; rotate the auto-memory index. Do not "
                          f"delete a Hard Constraint to fit."]
    if total >= LOADED_SOFT:
        return 0, rows + [f"PASS {head} -- WARN: {LOADED_HARD - total:,} left under "
                          f"the {LOADED_HARD:,} hard limit. Act now, while there is "
                          f"still room to choose what goes.{short}"]
    return 0, rows + [f"PASS {head} ({LOADED_HARD - total:,} under the "
                      f"{LOADED_HARD:,} hard limit){short}"]


# ---------------------------------------------------------------- pointer rows
# llm-distillery#133. The size guards above measure the SYMPTOM. What actually
# grows is the "Before You Start" pointer table: every session appends a lesson
# to the row nearest its topic, each audit trims the file back to the wall, and
# the cycle repeats at ~486 bytes/day (measured over 25 commits, 2026-08-16 →
# 08-26: 35,094 → 39,955). Trimming loses that race by construction.
#
# So the rule is a CAP PER ROW, not a budget for the file: a pointer row states
# the trigger and names the target, and the lesson goes in the target. A capped
# table cannot grow, which is the property the byte budget never had.
#
# ⚠️ THE CARVE-OUT IS THE HONEST PART OF THIS RULE, NOT A LOOPHOLE. A pointer
# does NOT fire without opening the target, so a prohibition that prevents
# SPENDING MONEY or PUBLISHING A WRONG NUMBER loses its whole value when it
# becomes a pointer. Those keep a higher cap. The list is deliberately short and
# deliberately checked: see the three failure modes in _check_pointers.
POINTER_CAP = 250          # an ordinary row: trigger + target + one clause
POINTER_CARVEOUT_CAP = 400 # a row on the list below
MAX_CARVEOUTS = 5          # the exemption itself must not grow

# Keyed on a distinctive fragment of the row's TRIGGER cell. Each entry carries
# the cost it prevents, because "why is this exempt" is the question a reader
# asks and the one that decides whether it still should be.
POINTER_CARVEOUTS = {
    "Quoting any Google News number":
        "never oracle-re-score a GN row — a paid oracle run against headline echoes",
    "Anything about the pipeline CONTRACTS":
        "never quote a Contract A version from here — it moves several times a week",
    "Reading a number off NexusMind production data":
        "live_articles is NOT the reader population — a published wrong number",
    "Asking what an article field IS":
        "never quote a field count — every count is a window; this one was stale for weeks",
}

POINTER_HEADER = "| When you're... | Read... |"


def _pointer_rows(raw):
    """The pointer table's data rows, as (line_no, text).

    Returns None when the header is not found. That is CANNOT VERIFY, never a
    pass: renaming the header would otherwise silently retire the whole check,
    which is this repo's signature defect (a guard that cannot fire reports
    success).
    """
    lines = raw.decode("utf-8", "replace").split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == POINTER_HEADER)
    except StopIteration:
        return None
    rows = []
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if not l.startswith("|"):
            break
        if set(l.replace("|", "").replace(" ", "")) <= set("-:"):
            continue                      # the delimiter row
        rows.append((i + 1, l))
    return rows


def _check_pointers():
    """Enforce the per-row cap. Returns (exit_code, list_of_lines)."""
    path = globals()["PROJECT"]
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return 1, ["CANNOT VERIFY: CLAUDE.md missing or empty"]
    rows = _pointer_rows(open(path, "rb").read())
    if rows is None:
        return 1, ["CANNOT VERIFY: pointer table header not found — the check "
                   "examined nothing. Restore the header or update POINTER_HEADER."]
    if not rows:
        return 1, ["CANNOT VERIFY: pointer table found but has no rows"]

    out, bad = [], []
    # Failure mode 1: the exemption list outgrows its purpose.
    if len(POINTER_CARVEOUTS) > MAX_CARVEOUTS:
        bad.append(f"{len(POINTER_CARVEOUTS)} carve-outs, over the {MAX_CARVEOUTS} "
                   f"allowed — the exemption is becoming the rule")
    # Failure mode 2: an exemption that matches no row. Dead weight, and it
    # hides growth: the next reader counts 4 exemptions and finds 3 rows.
    for frag in POINTER_CARVEOUTS:
        if not any(frag in text for _, text in rows):
            bad.append(f"carve-out {frag!r} matches no row — stale exemption, remove it")
    # Failure mode 3: the actual cap.
    over = 0
    for ln, text in rows:
        frag = next((f for f in POINTER_CARVEOUTS if f in text), None)
        cap = POINTER_CARVEOUT_CAP if frag else POINTER_CAP
        if len(text) > cap:
            over += 1
            why = "carve-out" if frag else "ordinary row"
            bad.append(f"CLAUDE.md:{ln} is {len(text)} chars, over the {cap} cap "
                       f"({why}) — move the lesson into the target it points at, "
                       f"and leave the trigger plus one clause")
    if bad:
        out.append(f"FAIL pointer rows: {len(bad)} problem(s) over {len(rows)} rows.")
        out.extend("  " + b for b in bad)
        return 1, out
    longest = max(len(t) for _, t in rows)
    out.append(f"PASS pointer rows: {len(rows)} rows, longest {longest}, cap "
               f"{POINTER_CAP} ({len(POINTER_CARVEOUTS)}/{MAX_CARVEOUTS} carve-outs "
               f"at {POINTER_CARVEOUT_CAP})")
    return 0, out

# The index carries the newest MAX_SESSION_ENTRIES session entries; the next one
# is MOVED to `memory/session-log.md`, verbatim (#123, owner call 2026-08-25).
#
# ⚠️ THIS IS THE CHECK THAT MATTERS, AND IT IS NOT THE CHARACTER ONE. The size
# guard measures the symptom. What actually grew was the session log — 69% of the
# file by character on 2026-08-25, ~600-900 chars per session, against a fixed
# ceiling — and the response it invited (trim an older entry) recovered ~100 chars
# per line removed and turned a finding into a pointer each time. Counting entries
# names the thing that grows, so the fix is a MOVE rather than a deletion.
#
# It is a WARN, not a FAIL. A hard failure here would land on whoever is writing
# the session entry, at the moment they are writing it, which is exactly the
# pressure that made entries go somewhere else instead.
MAX_SESSION_ENTRIES = 4
SESSION_LOG = os.path.join(ROOT, "memory", "session-log.md")

# A session entry starts with a bullet and a date, in either of the two shapes the
# index uses: `- **2026-08-25 — ...` and `- [2026-08-25](...)`.
SESSION_ENTRY = re.compile(rb"^- (?:\*\*)?\[?20\d\d-\d\d-\d\d")


def _session_entries(raw: bytes) -> int:
    """Count session entries in the index itself.

    Counted on the INDEX only. The log file is deliberately unbounded — it is the
    record, and a budget on it would re-create the problem one file over.
    """
    return sum(1 for line in raw.splitlines() if SESSION_ENTRY.match(line))


# Targets that compute their own verdict rather than measuring one file against a
# ceiling. Kept in a table so the argument error message below cannot drift out of
# step with what is actually dispatchable -- it is built from the same two dicts.
EXTRA_TARGETS = {
    "pointers": _check_pointers,
    "loaded":   _check_loaded,
}


def _all_targets():
    """Every dispatchable target name, for the two argument-error messages.

    Built from the dicts themselves: a hand-listed `+ ['pointers']` is how the
    error message came to omit a target the moment one was added.
    """
    return list(TARGETS) + list(EXTRA_TARGETS)


def main(argv=None):
    """Check one target's budget.

    ⚠️ `argv` IS A PARAMETER, NOT `sys.argv`, AND THAT IS LOAD-BEARING. It read
    `sys.argv[1:]` directly for about ten minutes on 2026-08-26 and every caller
    that imports this module — `tests/unit/test_index_budget_guard.py` does — got
    the HOST process's arguments instead of its own. Under pytest that is the test
    file's path, so the guard answered "unknown argument" to five tests that never
    passed one. The tests were the control working; they are not the only caller
    that matters.
    """
    target = "index"
    if argv is None:
        # NOT sys.argv. An imported caller passes its own list or none at all;
        # only __main__ speaks for the command line.
        argv = []
    if argv:
        if argv[0] == "--target" and len(argv) > 1:
            target = argv[1]
        elif argv[0].startswith("--target="):
            target = argv[0].split("=", 1)[1]
        else:
            print(f"CANNOT VERIFY: unknown argument {argv[0]!r}; "
                  f"expected --target {'|'.join(_all_targets())}")
            return 1
    if target in EXTRA_TARGETS:
        rc, lines = EXTRA_TARGETS[target]()
        for l in lines:
            print(l)
        return rc
    if target not in TARGETS:
        print(f"CANNOT VERIFY: unknown target {target!r}; "
              f"expected one of {', '.join(_all_targets())}")
        return 1

    attr, label, hard, soft, count_entries = TARGETS[target]
    # `globals()`, NOT `sys.modules[__name__]`: a caller may exec this module without
    # registering it (importlib.util.module_from_spec + exec_module, which is exactly
    # what two tests in test_index_budget_guard.py do), and the sys.modules form then
    # raises KeyError. globals() is this module's own namespace, which is also where
    # monkeypatch.setattr(mod, ...) writes — so it satisfies both callers.
    path = globals()[attr]

    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        print(f"CANNOT VERIFY: {label} missing or empty")
        return 1

    raw = open(path, "rb").read()
    size = len(raw)
    lines = raw.count(b"\n")
    note = _entry_note(raw) if count_entries else ""

    if size >= hard:
        # The remedy differs per target, so the FAIL line has to as well: a
        # generic "trim it" is what produced the compression #123 was about.
        if count_entries:
            remedy = ("Do NOT drop your session entry to fit — move detail into "
                      "memory/project_session_*.md and leave a hook here. Check each "
                      "trimmed entry has its full session file FIRST.")
        else:
            remedy = ("Move reference material — anything looked up on demand rather "
                      "than needed every session — into a memory/ topic file behind a "
                      "'Before You Start' pointer. Do not delete a Hard Constraint to "
                      "fit; they are why this file is loaded at all.")
        print(f"FAIL {label} is {size:,} B ({lines} lines), over the "
              f"{hard:,} hard limit. {remedy}{note}")
        return 1

    if size >= soft:
        print(f"PASS {label} {size:,} B / {lines} lines — WARN: {hard - size:,} "
              f"left under the {hard:,} hard limit. Act now, while there is still "
              f"room to choose what goes.{note}")
        return 0

    print(f"PASS {label} {size:,} B / {lines} lines ({hard - size:,} under the "
          f"{hard:,} hard limit){note}")
    return 0


def _entry_note(raw: bytes) -> str:
    """The session-entry half of the verdict, appended to whatever PASS line ran."""
    n = _session_entries(raw)
    if n <= MAX_SESSION_ENTRIES:
        return f" — {n}/{MAX_SESSION_ENTRIES} session entries"
    if not os.path.isfile(SESSION_LOG):
        return (f" — WARN: {n} session entries, over the {MAX_SESSION_ENTRIES} the index "
                f"carries, and memory/session-log.md DOES NOT EXIST. Create it before "
                f"moving anything; a move with nowhere to land becomes a deletion.")
    return (f" — WARN: {n} session entries, {n - MAX_SESSION_ENTRIES} over. MOVE the "
            f"oldest to memory/session-log.md VERBATIM — do not compress it, and do not "
            f"drop it. Compression is what stopped the index being a record (#123).")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
