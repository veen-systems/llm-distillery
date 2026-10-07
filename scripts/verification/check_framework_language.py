#!/usr/bin/env python3
"""ADR-013 (amended 2026-09-17): the framework's own text is English. This checks the class that ADR names and
that the first compliance sweep could not see: Dutch LENS / TAB NAMES in framework text (LD#160).

    python3 scripts/verification/check_framework_language.py        # exit 0 clean, 1 on any unlisted hit
    python3 scripts/verification/check_framework_language.py --all  # also print the carved-out hits

⭐ Why names, not words. The first sweep (2026-09-17) searched Dutch FUNCTION words and returned zero, while two sites
used Dutch lens names: a name contains no function word. The positive control must be of the CLASS UNDER TEST.
`tests/unit/test_framework_language.py` seeds a true positive of that class (a name inside an identifier, a bare name in
prose) and asserts this script goes red on it.

Scope: tracked `*.py *.md *.yaml *.yml *.sh *.toml` outside `datasets/`. Article text (`*.jsonl`, tokenizer files)
is data in six languages and is out of scope by construction.

The allowlist is ADR-013's carve-out table, by ROLE (the table itself says the class governs, not its examples):
- MATCH PATTERNS: a hit inside a Python string that feeds `re.<fn>()`, sits in a tuple with an `re.` flag, or is
  assigned to a name saying pattern/regex. Deleting it would change what the code matches, so it is data.
- FIXTURES: non-docstring string literals in `tests/**.py` and in this checker (its name list is what it matches).
  Comments and docstrings in those files are still checked (ADR-013: "comments, docstrings ... stay English").
- MENTIONS: in Markdown, a hit inside BACKTICKS is a name being discussed, not used. Quotes do not count: they also
  label a tab. ⚠️ Still the softest rule: a doc that labels a tab in backticks passes. It is visible in `--all`.
- RECORDS: ADR-009 (owner ruling) and ADR-013 (the rule must cite the names) are exempt, and so are the verbatim
  archives (`memory/archive/`, `docs/TODO-archive.md`, `memory/session-log.md`), which are never edited.
- NOT CHECKED: commit messages, which ADR-013 also covers; nothing reads them yet.
- HISTORICAL RECORDS (owner ruling 2026-10-01, LD#160): ADR-009 predates ADR-013 and gets a dated note mapping
  the names; it is not rewritten.
- KNOWN OPEN: violations found and handed to the owner, each naming where it is tracked. Printed on every run so
  they cannot become silent; delete the entry when the line is fixed (a stale entry is reported).
"""
import argparse, ast, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# ovr.news tab names that were Dutch at some point (ADR-009, ADR-013 Context), plus the abbreviations
# cross_filter_landscape.py printed. Matched case-insensitively, delimited by NON-LETTERS, so a name inside an
# identifier (prefix_name) counts.
# NOT "voor" (cross_filter_landscape.py's old Solutions column header): it is also the Dutch word "for", and adding it
# measured 4 false hits, all article text quoted in evidence docs or fixture sentences (2026-10-07).
# The Belonging tab's Dutch label (commit e7e8863, 2026-03-07) was missing until review 2026-10-07.
# Compounds (natuurherstel) are NOT matched: names are delimited by non-letters by design.
NAMES = ["welzijn", "erfgoed", "vooruitgang", "herstel", "leren", "verwondering", "verbondenheid", "welz", "erfg"]
NAME_RE = re.compile(r"(?<![a-zA-Z])(" + "|".join(NAMES) + r")(?![a-zA-Z])", re.IGNORECASE)
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".sh", ".toml"}
SELF = "scripts/verification/check_framework_language.py"

HISTORICAL = {"docs/adr/009-add-filters-first-reduce-later.md": "owner 2026-10-01 (LD#160): note, never rewrite",
              "docs/adr/013-english-lens-names.md": "the rule's own text, which must cite the names it forbids"}
FROZEN = ("memory/archive/", "docs/TODO-archive.md", "memory/session-log.md")  # verbatim records, never edited
KNOWN_OPEN = {}  # the nature_recovery v1/v2/v4 config.yaml tab label was fixed 2026-10-07 (owner ruling)

MD_QUOTED = re.compile(r"`[^`\n]*`")  # backticks only: quotes also LABEL a tab, and apostrophes mis-pair


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if Path(p).suffix in SUFFIXES and not p.startswith("datasets/")]


def _spans(regex, text, keep=lambda m: True):
    return [(m.start(), m.end()) for m in regex.finditer(text) if keep(m)]


RE_FUNCS = {"compile", "search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
PATTERN_NAME = re.compile(r"pattern|regex|_re$", re.IGNORECASE)


def _py_string_spans(text):
    """(docstrings, patterns, other strings) as character spans, from the AST. A string is a MATCH PATTERN only if it
    feeds `re.<fn>(...)`, sits in a tuple carrying an `re.` flag, or is assigned (at any depth) to a name that says
    pattern/regex (review 2026-10-07: a `|` in a docstring or a raw docstring had counted as a pattern)."""
    tree = ast.parse(text)
    lines = text.split("\n")
    starts, pos = [], 0
    for l in lines:
        starts.append(pos); pos += len(l) + 1

    def off(lineno, col_bytes):
        line = lines[lineno - 1]
        return starts[lineno - 1] + len(line.encode("utf-8")[:col_bytes].decode("utf-8", "ignore"))

    def span(n):
        return off(n.lineno, n.col_offset), off(n.end_lineno, n.end_col_offset)

    def strs(n):
        return [x for x in ast.walk(n) if isinstance(x, ast.Constant) and isinstance(x.value, str)]

    docs, pats = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            docs.add(span(n.body[0].value))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in RE_FUNCS \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "re" and n.args:
            pats.update(span(x) for x in strs(n.args[0]))
        if isinstance(n, ast.Tuple) and any(isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name)
                                            and e.value.id == "re" for e in n.elts):
            pats.update(span(x) for x in strs(n))
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and PATTERN_NAME.search(t.id) for t in targets) and n.value is not None:
                pats.update(span(x) for x in strs(n.value))
    every = {span(x) for x in ast.walk(tree) if isinstance(x, ast.Constant) and isinstance(x.value, str)}
    return docs, pats - docs, every - docs - pats


def classify(path, text):
    """[(line_no, line, name, verdict)] for every name hit; verdict is 'violation' or the carve-out that admits it."""
    allowed = []
    if path.endswith(".py"):
        docs, pats, other = _py_string_spans(text)
        allowed = list(pats)
        if path.startswith("tests/") or path == SELF:
            allowed += list(other)  # fixture strings / this checker's name list: data, by role; docstrings are NOT
    elif path.endswith(".md"):
        allowed = _spans(MD_QUOTED, text)
    lines = text.split("\n")
    starts, pos = [], 0
    for l in lines:
        starts.append(pos); pos += len(l) + 1
    hits = []
    for m in NAME_RE.finditer(text):
        ln = max(i for i, s in enumerate(starts) if s <= m.start())
        line = lines[ln]
        if path in HISTORICAL:
            v = "historical: " + HISTORICAL[path]
        elif path.startswith(FROZEN):
            v = "frozen record"
        elif any(a <= m.start() and m.end() <= b for a, b in allowed):
            v = ("fixture/match data" if path.startswith("tests/") or path == SELF else "match pattern") \
                if path.endswith(".py") else "quoted mention"
        else:
            k = next((k for k in KNOWN_OPEN if k[0] == path and k[1] in line), None)
            v = "known open: " + KNOWN_OPEN[k] if k else "violation"
        hits.append((ln + 1, line.strip(), m.group(1), v))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="print carved-out hits too")
    ap.add_argument("paths", nargs="*", help="check these files instead of every tracked one")
    a = ap.parse_args(argv)
    paths = a.paths or tracked()
    bad, seen_open = 0, set()
    for p in paths:
        try:
            text = (ROOT / p).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for ln, line, name, v in classify(p, text):
            if v == "violation":
                bad += 1
                print(f"VIOLATION {p}:{ln}: '{name}' in: {line[:140]}")
            elif v.startswith("known open"):
                seen_open.add(next(k for k in KNOWN_OPEN if k[0] == p and k[1] in line))
                print(f"open      {p}:{ln}: '{name}' ({v})")
            elif a.all:
                print(f"allowed   {p}:{ln}: '{name}' ({v})")
    stale = [] if a.paths else [k for k in KNOWN_OPEN if k not in seen_open]
    for k in stale:
        print(f"STALE known-open entry (fixed? delete it): {k}")
    print(f"{bad} violation(s), {len(seen_open)} known open, {len(stale)} stale entr(ies)")
    return 1 if bad or stale else 0


if __name__ == "__main__":
    sys.exit(main())
