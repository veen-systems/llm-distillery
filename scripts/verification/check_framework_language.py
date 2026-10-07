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
- MENTIONS: in Markdown, a hit inside backticks or quotes is a name being discussed, not used (ADR-013 itself does
  this). ⚠️ This is the softest rule here: a doc that labels a tab in backticks passes. It is visible in `--all`.
- HISTORICAL RECORDS (owner ruling 2026-10-01, LD#160): ADR-009 predates ADR-013 and gets a dated note mapping
  the names; it is not rewritten.
- KNOWN OPEN: violations found and handed to the owner, each naming where it is tracked. Printed on every run so
  they cannot become silent; delete the entry when the line is fixed (a stale entry is reported).
"""
import argparse, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# ovr.news tab names that were Dutch at some point (ADR-009, ADR-013 Context), plus the abbreviations
# cross_filter_landscape.py printed. Matched case-insensitively, delimited by NON-LETTERS, so `s1_welzijn` counts.
# NOT "voor" (cross_filter_landscape.py's Vooruitgang column header): it is also the Dutch word "for", and adding it
# measured 4 false hits, all article text quoted in evidence docs or fixture sentences (2026-10-07).
NAMES = ["welzijn", "erfgoed", "vooruitgang", "herstel", "leren", "verwondering", "welz", "erfg"]
NAME_RE = re.compile(r"(?<![a-zA-Z])(" + "|".join(NAMES) + r")(?![a-zA-Z])", re.IGNORECASE)
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".sh", ".toml"}

HISTORICAL = {"docs/adr/009-add-filters-first-reduce-later.md": "owner 2026-10-01 (LD#160): note, never rewrite"}
KNOWN_OPEN = {
    ("filters/nature_recovery/v1/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
    ("filters/nature_recovery/v2/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
    ("filters/nature_recovery/v4/config.yaml", "'Herstel' tab"): "docs/TODO.md START HERE item 4 (LD#160 follow-up)",
}

PY_STR = re.compile(r"""(?P<prefix>[rRbBuUfF]{0,2})(?P<q>'''|\"\"\"|'|")(?P<body>.*?)(?P=q)""", re.DOTALL)
MD_QUOTED = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"|“[^”\n]*”|'[^'\n]*'")


def tracked():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if Path(p).suffix in SUFFIXES and not p.startswith("datasets/")]


def _spans(regex, text, keep=lambda m: True):
    return [(m.start(), m.end()) for m in regex.finditer(text) if keep(m)]


def _is_pattern(m):
    return "r" in m.group("prefix").lower() or "\\b" in m.group("body") or "|" in m.group("body")


def classify(path, text):
    """[(line_no, line, name, verdict)] for every name hit; verdict is 'violation' or the carve-out that admits it."""
    allowed = []
    if path.endswith(".py"):
        allowed = _spans(PY_STR, text, _is_pattern)
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
            v = "match pattern" if path.endswith(".py") else "quoted mention"
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
