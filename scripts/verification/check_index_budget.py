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

⚠️ THE BUDGET IS IN CHARACTERS, NOT LINES, AND THAT IS LOAD-BEARING. The file
reached 54,808 chars in 91 lines on 2026-08-15 — up 69% in three days — because
entries grow by LENGTHENING, not by multiplying. Every line-count heuristic passed
throughout. Do not add one back as the primary check.

    python3 scripts/verification/check_index_budget.py

Exit 0 on PASS (with or without a WARN line), 1 on FAIL, 1 if the file is missing
or empty — an unreadable index must never read as a pass.

⚠️ The runner treats the LAST output line containing "FAIL" as a failure regardless
of exit code, so no PASS or WARN line may contain that word. Say "hard limit".
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "memory", "MEMORY.md")

HARD = 30_000  # ceiling: above this the index is no longer a navigational layer
SOFT = 27_000  # runway: ~3,000 chars ≈ three sessions of notice

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


def main():
    if not os.path.isfile(INDEX) or os.path.getsize(INDEX) == 0:
        print("CANNOT VERIFY: memory/MEMORY.md missing or empty")
        return 1

    raw = open(INDEX, "rb").read()
    size = len(raw)
    lines = raw.count(b"\n")

    if size >= HARD:
        print(f"FAIL memory/MEMORY.md is {size:,} chars ({lines} lines), over the "
              f"{HARD:,} hard limit. Do NOT drop your session entry to fit — move "
              f"detail into memory/project_session_*.md and leave a hook here. "
              f"Check each trimmed entry has its full session file FIRST."
              f"{_entry_note(raw)}")
        return 1

    if size >= SOFT:
        print(f"PASS {size:,} chars / {lines} lines — WARN: {HARD - size:,} left "
              f"under the {HARD:,} hard limit, roughly {(HARD - size) // 800} more "
              f"entries. Trim now, while there is still room to choose what goes."
              f"{_entry_note(raw)}")
        return 0

    print(f"PASS {size:,} chars / {lines} lines ({HARD - size:,} under the "
          f"{HARD:,} hard limit){_entry_note(raw)}")
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
    sys.exit(main())
