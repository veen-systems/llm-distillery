#!/usr/bin/env python3
# ⛔ REJECTED 2026-09-27 and deliberately UNWIRED: see README.md in this directory. Kept so nobody rebuilds it.
"""Fail when an edit to CLAUDE.md drops an operative CLAUSE, not just a token.

Mechanized-table row (memory/gotcha-log.md § Mechanized, 2026-09-26): a trim of CLAUDE.md kept
every backticked span, number and issue id and still lost five operative clauses, among them the
ADR-015 ban on excluding adjacent-lens content from oracle prompts and "compare filters ONLY on
recall + specificity". A token-survival check passed; only a review lens noticed.

An OPERATIVE clause is a sentence of the OLD file that carries a ⛔ or a bold span with an
imperative marker (never / do not / must / only / always / not). It SURVIVES when some paragraph
of the NEW file, or of a file named by path on the clause's own line (the file its bullet points
to), contains:
  - at least KEEP_FRACTION of the clause's content words, and
  - every polarity CLASS the clause has (NEG: never / not / no / do not; ONLY), because dropping
    "never" inverts a rule while keeping almost every other word. Classes, not words: "not
    partitions" and "never exclude" are both NEG.
Other files are deliberately NOT searched unless DECLARED with --moved-to: a rule that still lives
in its ADR (or in docs/adr/README.md's index) but has left the always-loaded file is exactly the
loss this check exists for. A deliberate move names its destination, and that is the declaration.

Usage:
    check_claude_md_trim.py                      # HEAD:CLAUDE.md vs the working tree
    check_claude_md_trim.py --staged             # HEAD:CLAUDE.md vs the index (commit-msg hook)
    check_claude_md_trim.py --old A.md --new B.md
    check_claude_md_trim.py --moved-to docs/decisions/framework-adoption-history.md   # declared destination
Exit 0: every operative clause survives. Exit 1: at least one is missing (listed). Exit 2: usage.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEP_FRACTION = 0.7
IMPERATIVE = re.compile(r"\b(never|do not|don't|must|only|always|not)\b", re.I)
IMPERATIVE_ANY = re.compile(r"\b(never|do not|don.t|must not|must)\b|\bNOT\b|\bONLY\b", re.I)
STOP = frozenset("""
a an the and or but if then than that this these those is are was were be been being it its of in on at to
for from by with as into onto over under per via vs any all each every some such so do does did done has have
had not no never only must always can cannot will would should may might here there what which who whom when
where why how also just still even more most less least very too own same other one two three first second
""".split())
PATH = re.compile(r"`?((?:[\w.-]+/)+[\w.-]+\.(?:md|py|json|yaml|sh))`?")


def _plain(text: str) -> str:
    return re.sub(r"[*_`>|]", " ", text)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9#.+-]*[a-z0-9]|[a-z0-9]", _plain(text).lower())


def content_words(text: str) -> set[str]:
    return {w for w in _words(text) if len(w) >= 4 and w not in STOP}


def polarity(text: str) -> set[str]:
    ws = set(_words(text))
    found = set()
    if ws & {"never", "not", "no", "don't", "cannot", "nothing"} or re.search(r"\bn't\b|\bNOT\b", text):
        found.add("NEG")
    if "only" in ws:
        found.add("ONLY")
    return found


def operative_clauses(text: str) -> list[tuple[str, str]]:
    """(clause, the full line it came from) for every operative sentence."""
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "<!--")):
            continue
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z⛔⚠*`(])", line):
            bold = re.findall(r"\*\*(.+?)\*\*", sent)
            if "⛔" in sent or any(IMPERATIVE.search(b) for b in bold) or IMPERATIVE_ANY.search(sent):
                if len(content_words(sent)) >= 3:
                    out.append((sent.strip(), line))
    return out


def paragraphs(text: str) -> list[str]:
    paras, cur = [], []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith(("- ", "* ", "| ", "#")) and cur:
            if cur:
                paras.append(" ".join(cur))
            cur = [line] if line.strip() else []
        else:
            cur.append(line)
    if cur:
        paras.append(" ".join(cur))
    return paras


def survives(clause: str, haystacks: list[str]) -> bool:
    need = content_words(clause)
    pol = polarity(clause)
    for para in haystacks:
        have = content_words(para)
        if len(need & have) >= KEEP_FRACTION * len(need) and pol <= polarity(para):
            return True
    return False


def missing_clauses(old: str, new: str, root: Path = REPO, moved_to: list[Path] | None = None) -> list[str]:
    new_paras = paragraphs(new)
    for f in moved_to or []:
        new_paras += paragraphs(Path(f).read_text(encoding="utf-8", errors="replace"))
    lost = []
    for clause, line in operative_clauses(old):
        hay = list(new_paras)
        for p in PATH.findall(line):
            f = root / p
            if f.is_file():
                hay += paragraphs(f.read_text(encoding="utf-8", errors="replace"))
        if not survives(clause, hay):
            lost.append(clause)
    return lost


def _git_show(spec: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), "show", spec], check=True,
                          capture_output=True, text=True).stdout


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--moved-to", action="append", default=[], metavar="FILE",
                    help="a file the removed clauses were deliberately moved to (repeatable)")
    a = ap.parse_args(argv)
    try:
        old = Path(a.old).read_text(encoding="utf-8") if a.old else _git_show("HEAD:CLAUDE.md")
        if a.new:
            new = Path(a.new).read_text(encoding="utf-8")
        elif a.staged:
            new = _git_show(":CLAUDE.md")
        else:
            new = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    total = len(operative_clauses(old))
    lost = missing_clauses(old, new, moved_to=[REPO / m if not Path(m).is_absolute() else Path(m) for m in a.moved_to])
    for c in lost:
        print(f"DROPPED CLAUSE: {c[:220]}")
    print(f"{'FAIL' if lost else 'PASS'} {total - len(lost)}/{total} operative clauses of the old file survive")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
