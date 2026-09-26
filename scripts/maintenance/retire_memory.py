#!/usr/bin/env python3
"""Retire dated memory into archives — the curate "archive pass" as a command.

agent-ready-projects v1.47.0 (`curate` Step 0, above ~300k) proposes moving resolved
gotchas, old session files and done work into an archive; v1.48.0 (`gotcha-log` Retire
phase, upstream #178) says how. Upstream selects gotchas on a `[RESOLVED` prefix; this
log rarely writes one (1 of the 15 entries retired on 2026-09-26 carried it), so this
selects on the DATE in the heading instead, the rule the 2026-09-24 pass (#163) used.

Two moves, DRY-RUN BY DEFAULT (`--apply` writes):

  gotcha    Top-level `## ` entries of memory/gotcha-log.md dated before --before go,
            verbatim and in order, to the END of memory/archive/gotcha-log-archive.md. `### `
            subsections travel with their parent. Dates are read in both shapes the log
            uses: ISO (`2026-08-30`) and month (`Feb 2026`, counted as the LAST day of
            its month, so a month entry is never retired early); a heading naming several
            dates is dated by its latest. Kept whatever their date: the entry template,
            the unreachable-mechanism catalogue and the Mechanized table — and, with them,
            every `### ` entry nested under them; those are COUNTED in the output, never
            silently kept. Undated entries are kept and listed.

  sessions  memory/project_session_YYYY_MM_DD*.md dated before --before are `git mv`ed
            to memory/archive/, and path references in tracked text are rewritten —
            except inside fenced code (quoted tool output) and in frozen records
            (docs/evidence/, *-archive.md), which are verbatim by contract; those are
            counted, not changed. `[[name]]` wikilinks resolve by name and are left alone.

Checks that can fail (gotcha): the new archive must START with the old archive's exact
text, the appended text must equal the removed blocks in order, and deleting those blocks
from the old log by string search must reproduce the new log exactly. Both files are
re-read after writing and compared. The archive is written first, so a failure between
the two writes leaves entries duplicated, never lost.

Usage:
  python3 scripts/maintenance/retire_memory.py gotcha   --before 2026-09-01 [--apply]
  python3 scripts/maintenance/retire_memory.py sessions --before 2026-09-01 [--apply]

Exit: 0 done (or dry run), 1 a check failed (nothing written, or say what was), 2 bad input.
"""

import argparse
import calendar
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "memory", "gotcha-log.md")
ARCHIVE = os.path.join(ROOT, "memory", "archive", "gotcha-log-archive.md")
SESSION_ARCHIVE = os.path.join("memory", "archive")

KEEP_HEADINGS = ("[Short description]", "The unreachable-mechanism catalogue", "Mechanized")
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
MONTHS = {m[:3]: i for i, m in enumerate(MONTH_NAMES, 1)}
ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
# A month is its 3-letter abbreviation or its full name — never a word that merely
# starts with one ("Decisions 2026", "Marchand 2026").
MON = re.compile(r"\b(" + "|".join(f"{m[:3]}(?:{m[3:]})?" for m in MONTH_NAMES)
                 + r")\.? (20\d\d)\b")
SESSION = re.compile(r"^project_session_(\d{4})_(\d\d)_(\d\d)[A-Za-z0-9_]*\.md$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FROZEN = ("docs/evidence/",)


def heading_date(h):
    """Latest date named in a heading, or None. A month counts as its LAST day."""
    ds = []
    for y, m, d in ISO.findall(h):
        try:
            ds.append(datetime.date(int(y), int(m), int(d)))
        except ValueError:
            pass
    for mo, y in MON.findall(h):
        n = MONTHS[mo[:3]]
        ds.append(datetime.date(int(y), n, calendar.monthrange(int(y), n)[1]))
    return max(ds) if ds else None


def fence_state(ln, fence):
    """CommonMark-ish: a fence closes on the same char, at least as long, nothing after."""
    m = FENCE.match(ln)
    if not m:
        return fence
    run = m.group(1)
    if fence is None:
        # CommonMark: a backtick fence's info string cannot hold a backtick, so
        # "```inline``` code" is an inline span, not an opening fence.
        if run[0] == "`" and "`" in ln.strip()[len(run):]:
            return None
        return run
    if run[0] == fence[0] and len(run) >= len(fence) and not ln.strip()[len(run):]:
        return None
    return fence


def split_entries(lines):
    """Preamble, then one block per top-level `## ` heading outside fenced code."""
    blocks, cur, fence = [], [], None
    for ln in lines:
        if fence is None and ln.startswith("## "):
            blocks.append(cur)
            cur = []
        cur.append(ln)
        fence = fence_state(ln, fence)
    blocks.append(cur)
    if fence is not None:
        raise ValueError(f"unclosed {fence} fence — entry boundaries after it are unknown")
    return blocks[0], blocks[1:]


def nested_dated(block, before):
    """`### ` headings inside a kept block that are dated before the cutoff."""
    n, fence = 0, None
    for ln in block[1:]:
        if fence is None and ln.startswith("### "):
            d = heading_date(ln)
            if d is not None and d < before:
                n += 1
        fence = fence_state(ln, fence)
    return n


def gotcha(before, apply):
    old_live = open(LOG, encoding="utf-8").read()
    old_arch = open(ARCHIVE, encoding="utf-8").read()
    try:
        pre, entries = split_entries(old_live.splitlines(keepends=True))
    except ValueError as e:
        print(f"REFUSED: {e}")
        return 1
    keep, move = [], []
    for b in entries:
        h = b[0].rstrip("\n")
        d = heading_date(h)
        pinned = next((k for k in KEEP_HEADINGS if k in h), None)
        if pinned:
            keep.append(b)
            k = nested_dated(b, before)
            if k:
                print(f"  kept by rule: {k} dated `### ` entries under '{pinned}'")
        elif d is None:
            keep.append(b)
            print(f"  UNDATED, kept: {h[:100]}")
        elif d < before:
            move.append(b)
            print(f"  move  {d}  {h[:100]}")
        else:
            keep.append(b)
    if not move:
        print("gotcha: no top-level entry dated before", before)
        return 0
    moved = ["".join(b) for b in move]
    new_live = "".join(pre) + "".join("".join(b) for b in keep)
    sep = "" if old_arch.endswith("\n") or not old_arch else "\n"
    new_arch = old_arch + sep + "\n" + "".join(moved)
    # Independent reconstruction: delete each moved block from the ORIGINAL text by
    # string search, in order. A mis-split, reorder or dropped line makes this differ.
    rest, pos = old_live, 0
    for t in moved:
        i = rest.find(t, pos)
        if i < 0:
            print("CHECK FAILED: a moved block is not a contiguous run of the old log — nothing written")
            return 1
        rest, pos = rest[:i] + rest[i + len(t):], i
    if rest != new_live or not new_arch.startswith(old_arch) \
            or new_arch[len(old_arch) + len(sep) + 1:] != "".join(moved):
        print("CHECK FAILED: live + archive do not reconstruct the originals — nothing written")
        return 1
    print(f"gotcha: {len(move)} entries; live log {len(old_live):,} -> {len(new_live):,} "
          f"chars; reconstruction check passed")
    if apply:
        open(ARCHIVE, "w", encoding="utf-8").write(new_arch)   # first: a crash duplicates
        open(LOG, "w", encoding="utf-8").write(new_live)
        if open(ARCHIVE, encoding="utf-8").read() != new_arch or \
                open(LOG, encoding="utf-8").read() != new_live:
            print("CHECK FAILED after writing: re-read differs — inspect `git diff memory/`")
            return 1
    return 0


def tracked_text():
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], check=True,
                         capture_output=True).stdout.decode().split("\0")
    for rel in out:
        if rel and rel.endswith((".md", ".py", ".sh", ".yaml", ".yml", ".txt", ".json", ".jsonl")):
            yield rel


def rewrite_outside_fences(text, fn):
    out, fence = [], None
    for ln in text.splitlines(keepends=True):
        out.append(ln if fence is not None or FENCE.match(ln) else fn(ln))
        fence = fence_state(ln, fence)
    return "".join(out)


def sessions(before, apply):
    mem = os.path.join(ROOT, "memory")
    names = []
    for f in sorted(os.listdir(mem)):
        m = SESSION.match(f)
        if not m:
            continue
        try:
            d = datetime.date(*map(int, m.groups()))
        except ValueError:
            print(f"  SKIPPED, not a real date: {f}")
            continue
        if d < before:
            names.append(f)
    if not names:
        print("sessions: nothing dated before", before)
        return 0
    tracked = set(tracked_text()) | set(
        subprocess.run(["git", "-C", ROOT, "ls-files", "--", "memory"], check=True,
                       capture_output=True, text=True).stdout.split())
    untracked = [n for n in names if f"memory/{n}" not in tracked]
    if untracked:
        print(f"REFUSED: {len(untracked)} session file(s) not tracked by git, so `git mv` "
              f"would fail after references were rewritten: {untracked[:3]}")
        return 2
    alt = "|".join(re.escape(n) for n in names)
    full = re.compile(r"(^|[^\w/]|\.\./)memory/(" + alt + r")")
    bare = re.compile(r"(?<![\w/\[])(" + alt + r")")
    edits, frozen = {}, 0
    for rel in tracked_text():
        p = os.path.join(ROOT, rel)
        try:
            s = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if not (full.search(s) or bare.search(s)):
            continue
        if rel.startswith(FROZEN) or rel.endswith("-archive.md"):
            frozen += len(full.findall(s)) + len(bare.findall(s))
            continue
        top = os.path.dirname(rel) == "memory" and os.path.basename(rel) not in names

        def fix(ln):
            ln = full.sub(r"\1memory/archive/\2", ln)
            return bare.sub(r"archive/\1", ln) if top else ln
        t = rewrite_outside_fences(s, fix)
        if t != s:
            edits[rel] = t
    globs = [(rel, ln.strip()) for rel in sorted(edits)
             for ln in edits[rel].splitlines() if re.search(r"project_session_[\d_]*[*?]", ln)
             and "memory/archive/project_session_" not in ln.split("*")[0][-40:]]
    print(f"sessions: {len(names)} files -> {SESSION_ARCHIVE}/ "
          f"({names[0]} .. {names[-1]})")
    print(f"  references rewritten in {len(edits)} files; {frozen} mentions in frozen "
          f"records left verbatim (they now point at the old path)")
    for rel in sorted(edits):
        print(f"    {rel}")
    for rel, ln in globs:
        print(f"  CHECK BY HAND — a glob the rewrite cannot follow: {rel}: {ln[:120]}")
    if apply:
        os.makedirs(os.path.join(ROOT, SESSION_ARCHIVE), exist_ok=True)
        subprocess.run(["git", "-C", ROOT, "mv", "--",
                        *[os.path.join("memory", n) for n in names],
                        SESSION_ARCHIVE + "/"], check=True)
        for rel, t in edits.items():
            if os.path.dirname(rel) == "memory" and os.path.basename(rel) in names:
                rel = os.path.join(SESSION_ARCHIVE, os.path.basename(rel))  # moved above
            open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(t)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("gotcha", "sessions"))
    ap.add_argument("--before", required=True, type=datetime.date.fromisoformat,
                    help="retire entries dated strictly before this ISO date")
    ap.add_argument("--apply", action="store_true", help="write (default: dry run)")
    a = ap.parse_args(argv)
    if a.before > datetime.date.today():
        print("--before is in the future; refusing")
        return 2
    rc = (gotcha if a.what == "gotcha" else sessions)(a.before, a.apply)
    if not a.apply and rc == 0:
        print("(dry run — pass --apply to write)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
