#!/usr/bin/env python3
"""ADR-013 (amended 2026-09-17): the framework's own text is English. This checks the class that ADR names and
that the first compliance sweep could not see: Dutch LENS / TAB NAMES in framework text (LD#160).

    python3 scripts/verification/check_framework_language.py        # exit 0 clean, 1 on any unlisted hit
    python3 scripts/verification/check_framework_language.py --all  # also print the carved-out hits

⭐ Why names, not words. The first sweep (2026-09-17) searched Dutch FUNCTION words and returned zero, while two sites
used Dutch lens names: a name contains no function word. The positive control must be of the CLASS UNDER TEST.
`tests/unit/test_framework_language.py` seeds a true positive of that class (`s1_welzijn`, a bare `Welzijn:` in
prose) and asserts this script goes red on it.

Scope: tracked `*.py *.md *.yaml *.yml *.sh *.toml` outside `datasets/`. Article text (`*.jsonl`, tokenizer files)
is data in six languages and is out of scope by construction.

The allowlist is ADR-013's carve-out table, by ROLE (the table itself says the class governs, not its examples):
- MATCH PATTERNS: a hit inside a Python regex string literal (raw string, or one containing `\\b` or `|`). Deleting
  it would change what the code matches, so it is data.
- FIXTURES: any string literal in `tests/**.py`, and in this checker (its name list is what it matches). Comments in
  those files are still checked.
- MENTIONS: in Markdown, a hit inside backticks or quotes is a name being discussed, not used (ADR-013 itself does
  this). ⚠️ This is the softest rule here: a doc that labels a tab in backticks passes. It is visible in `--all`.
- HISTORICAL RECORDS (owner ruling 2026-10-01, LD#160): ADR-009 predates ADR-013 and gets a dated note mapping
  the names; it is not rewritten.
- KNOWN OPEN: violations found and handed to the owner, each naming where it is tracked. Printed on every run so
  they cannot become silent; delete the entry when the line is fixed (a stale entry is reported).
"""
import argparse, io, re, subprocess, sys, tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# ovr.news tab names that were Dutch at some point (ADR-009, ADR-013 Context), plus the abbreviations
# cross_filter_landscape.py printed. Matched case-insensitively, delimited by NON-LETTERS, so a name inside an
# identifier (prefix_name) counts.
# NOT "voor" (cross_filter_landscape.py's old Solutions column header): it is also the Dutch word "for", and adding it
# measured 4 false hits, all article text quoted in evidence docs or fixture sentences (2026-10-07).
NAMES = ["welzijn", "erfgoed", "vooruitgang", "herstel", "leren", "verwondering", "welz", "erfg"]
NAME_RE = re.compile(r"(?<![a-zA-Z])(" + "|".join(NAMES) + r")(?![a-zA-Z])", re.IGNORECASE)
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".sh", ".toml"}
SELF = "scripts/verification/check_framework_language.py"

HISTORICAL = {"docs/adr/009-add-filters-first-reduce-later.md": "owner 2026-10-01 (LD#160): note, never rewrite"}
KNOWN_OPEN = {
    ("filters/nature_recovery/v1/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
    ("filters/nature_recovery/v2/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
    ("filters/nature_recovery/v4/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
}

MD_QUOTED = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"|“[^”\n]*”|'[^'\n]*'")


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if Path(p).suffix in SUFFIXES and not p.startswith("datasets/")]


def _spans(regex, text, keep=lambda m: True):
    return [(m.start(), m.end()) for m in regex.finditer(text) if keep(m)]


def _py_strings(text):
    """(start, end, token_text) of every string literal, from Python's own tokenizer: a regex over the source mis-pairs
    quotes across an apostrophe in a comment or an escaped quote (found 2026-10-07 on this file)."""
    starts, pos = [0], 0
    for l in text.split("\n"):
        pos += len(l) + 1; starts.append(pos)
    kinds = {tokenize.STRING} | {getattr(tokenize, n) for n in ("FSTRING_MIDDLE",) if hasattr(tokenize, n)}
    out = []
    for t in tokenize.generate_tokens(io.StringIO(text).readline):
        if t.type in kinds:
            out.append((starts[t.start[0] - 1] + t.start[1], starts[t.end[0] - 1] + t.end[1], t.string))
    return out


def _is_pattern(tok):
    prefix = re.match(r"[rRbBuUfF]*", tok).group(0)
    return "r" in prefix.lower() or "\\b" in tok or "|" in tok


def classify(path, text):
    """[(line_no, line, name, verdict)] for every name hit; verdict is 'violation' or the carve-out that admits it."""
    allowed = []
    if path.endswith(".py") and (path.startswith("tests/") or path == SELF):
        allowed = [(a, b) for a, b, _ in _py_strings(text)]  # fixture strings / this checker's name list: data, by role
    elif path.endswith(".py"):
        allowed = [(a, b) for a, b, tok in _py_strings(text) if _is_pattern(tok)]
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
