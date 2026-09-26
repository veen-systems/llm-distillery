#!/usr/bin/env python3
"""Reference integrity per /audit-context step 4.

Rungs, in order: 1 as-written · 2 whole-fragment suffix in the WORKING TREE
(collision => report) · 3 runtime state (state dir or state-file shape, and
gitignored is necessary-not-sufficient) · 4 sibling repo, only when the
reference is MARKED cross-repo by a whole-token repo name in surrounding prose
that is not the path's own text.

Output is three sections, not one list: findings / resolved-below-rung-1 /
skipped-as-asserted-absent. Also reports extensions the whitelist dropped.
"""
import os, re, sys, glob
from collections import defaultdict

ROOT = os.environ.get("REFCHECK_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SIBLING_ROOTS = [os.path.dirname(ROOT), os.path.dirname(os.path.dirname(ROOT))]
import os as _o


def _relroot(d):
    """Path as written relative to ROOT, with forward slashes; '' if outside ROOT.

    ⚠️ NOT os.path.relpath(d, ROOT) on its own: that resolves an already-relative
    path against the CWD first, so every report section below was silently
    cwd-dependent and emitted "../../.." directory keys when the checker ran from
    outside the repo (REFCHECK_ROOT exists exactly for that case, and the tier tests
    run that way). Found 2026-09-17 while tiering docs/ for #134 step 2.
    """
    r = os.path.relpath(d, ROOT) if os.path.isabs(d) else d
    r = r.replace(os.sep, "/")
    return "" if r.startswith("../") or r == ".." else r

# The USER-LEVEL auto-memory index is auto-loaded every session and its pointers
# name repo files — but it lived outside DOCS until 2026-08-13, when a curate pass
# found THREE dead session pointers in it (files never committed). The audit could
# not have caught them: it was not looking at the file. Absolute path, because it
# is outside ROOT.
AUTOMEM_INDEX = _o.path.expanduser(
    "~/.claude/projects/-home-jeroen-repos-veen-systems-llm-distillery/memory/MEMORY.md")
# ⛔ Until 2026-08-16 DOCS was three files. The audit then reported 0 findings and
# the 0 was real — over 3 of 84 in-repo context documents. The 26 LIVE topic files
# an agent is actually pointed at were never scanned, and the same instrument found
# 51 unresolved references in them on first run, dominated by unmarked cross-repo
# paths (`scripts/main.py` means NexusMind's; a reader here looks locally and finds
# nothing). Session records are excluded by default: they are frozen accounts of a
# moment, so a path that has since moved is not decay there. `--sessions` includes
# them (85 more).
import glob as _g


def _topic_files():
    out = []
    for f in sorted(_g.glob(_o.path.join(ROOT, "memory", "*.md"))):
        rel = _o.path.relpath(f, ROOT)
        if rel in ("memory/MEMORY.md", "memory/gotcha-log.md"):
            continue
        if "project_session_" in rel and "--sessions" not in _o.sys.argv:
            continue
        out.append(rel)
    return out


# llm-distillery#134 (2026-08-28) — `docs/` was NEVER scanned. The check stopped exactly
# one hop short of where it is aimed: CLAUDE.md IS scanned, so the pointer table's targets
# are verified to exist -- but those targets are the live context an agent is ROUTED INTO,
# and what THEY reference was unchecked. A pointer that resolves into a document full of
# dead references is a working door into a broken room.
#
# ⚠️ STILL FLAG-GATED, and step 2 (2026-09-17) is the decision NOT to promote, taken with
# the number in hand rather than deferred again: the LIVE tier alone carries 274 findings
# in 65 of the 120 files it scans, against a default run of 0. Promoting replaces the 0
# baseline -- the thing that makes a NEW break visible -- with a section the reader learns
# to skip. ⛔ The precondition is the MARKING PASS, not more measurement: `memory/` went
# 23 -> 0 on 2026-09-17 with 19 of the 23 moving into the counted placeholder section and
# only ONE being a genuine stale marker, and `docs/` has never had that pass.
#
# ⛔ THE TIER IS CODE, NOT A README TABLE. It lived as a hand-written table in
# `docs/evidence/2026-08-28-refcheck-docs/README.md`, and the drift re-read was recomputed
# by hand in llm-distillery#134's comments -- a hand-built population, which is what every
# measurement error this project has made turned out to be. `### FINDINGS BY TIER` below
# is emitted by the instrument that produced the findings.
#
# FROZEN means "a frozen account of a moment": a reference that broke because the world
# moved is NOT decay there, and editing the record to silence the checker is the
# compression #123 forbids. Same rationale and same disposition as
# `memory/project_session_*.md` under --sessions.
#
# ⛔ THE DIRECTORY IS NOT THE TIER, AND THE FIRST DRAFT OF THIS CODE SAID IT WAS. It
# warranted a directory-only rule with "every frozen entry is dated BY CONSTRUCTION",
# which is false: `docs/decisions/framework-adoption-history.md` is undated, was edited
# the same day, is routed into from `CLAUDE.md` TWICE, and carries the largest
# finding count of any single file in the frozen set. A directory-only rule froze it
# -- "never to be edited to satisfy this checker" -- along with 4 more pointer targets
# and every undated index. Caught by the adversarial lens of `/review-changes`, not by
# the 17 tests written to guard the tier. So the tier is three tests, in this order:
#
#   1. LIVE if the directory says so (anything not in DOCS_FROZEN_DIRS).
#   2. LIVE if the ALWAYS-LOADED layer routes an agent into it -- the LIVE criterion's
#      own wording, computed from the two files rather than hand-listed. Five files
#      qualify today, all under docs/decisions/, and one of them
#      (2026-08-25-pause-investment-risk.md) is reached for an UN-PAUSE PROCEDURE: a
#      dated filename on an operational document.
#   3. LIVE if the path carries no date AND sits DIRECTLY in the frozen directory --
#      an undated file among dated siblings is an index or a running history, not an
#      account of a moment. `_archive/` is exempt: frozen by definition, not by date.
#      ⛔ THE DEPTH RESTRICTION IS NOT TIDINESS, and its absence was the SECOND round's
#      repeat of the first round's defect -- another unhedged absolute about a population
#      nobody had enumerated. Undated at ANY depth admitted 13 files of which 10 are
#      frozen accounts by the tier's own definition: six verbatim copies of OTHER repos'
#      ADRs under `evidence/adr/`, two training reports for a filter removed 2026-08-03,
#      an article draft, a log excerpt -- 21 findings, 7.7% of the live total the
#      promotion decision and the marking pass both rest on. A nested undated directory
#      is a COLLECTION inside a frozen one; only a file beside the dated ones is an
#      index. Enumerated at depth 3: `decisions/README.md`, `evidence/README.md`,
#      `evidence/hypothesis-log-excerpts.md` -- two indexes and one excerpt file that is
#      arguably frozen, carrying 1 finding. That residue is named, not hidden.
#
# ⚠️ ROUTED_FROM is IN-REPO ONLY, deliberately. The user-level auto-memory index is
# auto-loaded too, but it lives outside the repo and is absent on another machine or a
# fresh clone -- and a tier that differs by machine makes the split differ by who ran it.
# Measured 2026-09-17: including it changes nothing (17 docs targets either way, the same
# 5 in frozen directories), so the determinism is free.
#
# ⚠️ `templates/` IS LIVE, reversing step 1's "frozen or marked" proposal. A template is a
# MAINTAINED document whose paths are non-resolving BY PURPOSE, and this instrument
# already has the purpose-built mechanism for that: the `<!-- placeholder -->` marker,
# which COUNTS them in their own section. Dropping a maintained file from the scan to hide
# paths known not to resolve is the silent skip the whole instrument exists to prevent.
DOCS_FROZEN_DIRS = ("_archive", "decisions", "evidence", "experiments", "reports")
DOCS_LIVE_DIRS = ("<root>", "adr", "agents", "articles", "checklists", "guides",
                  "ideas", "proposals", "references", "templates")
ROUTED_FROM = ("CLAUDE.md", "memory/MEMORY.md")
# ⛔ THE LEFT BOUNDARY IS THE WHOLE POINT. Without it, `NexusMind/docs/ARTICLE_RECORD.md`
# -- a CROSS-REPO path, and `CLAUDE.md` carries two of them -- matched from its `docs/`
# onward and registered as a routing target for a file of ours that does not exist. So
# did a github.com URL ending in a docs path (fixture-verified, both directions). The
# cross-repo pair was live in this repo while the pattern was unanchored: measured
# 2026-09-17, the routed set went 17 -> 15 when the boundary landed, and the two that
# left were exactly those NexusMind paths. They were inert only because no local file
# happened to share their names, which is not a property anyone chose. `../docs/...` must still match -- `memory/MEMORY.md` writes its
# pointers that way -- so the boundary is in front of the OPTIONAL `../`, not in front of
# `docs/`, and the prefix is stripped after matching.
#
# ⚠️ WHAT IT STILL CANNOT SEE, stated because a residue nobody names is read as zero: the
# pattern is context-blind. A path inside a fenced code block, inside a sentence saying it
# does NOT exist, or inside a ~~struck~~ deletion marker still registers as routed. That
# over-includes into LIVE -- more scanned, not less -- and the count of files reaching
# LIVE this way is printed in FINDINGS BY TIER so a wrong one is visible rather than
# silent. Building fence/polarity parsing here would be a second extractor beside the
# one this file already has, and that is the duplication this change exists to remove.
ROUTED_RE = re.compile(r"(?<![A-Za-z0-9_/-])((?:\.\./)*docs/[A-Za-z0-9_./-]+\.md)")
_DATED_RE = re.compile(r"(19|20)\d\d[-_]\d\d[-_]\d\d")
DOCS_FLAGS = ("--docs", "--docs-live", "--docs-frozen")
# ⛔ `--docs` KEEPS MEANING ALL OF docs/. Every number on record -- 339 (2026-08-28), 401
# (2026-09-12), 376 and 377 (2026-09-17, four surfaces and this file's own earlier draft)
# -- was measured with it, and silently narrowing a flag to a subset would make those
# readings wrong without touching the documents that quote them. `--docs-live` is the
# preview of what promotion would put in the default set.
KNOWN_FLAGS = ("--sessions",) + DOCS_FLAGS


_ROUTED_CACHE = None


def _routed_targets():
    """docs/ paths the always-loaded layer routes an agent into (see ROUTED_FROM)."""
    global _ROUTED_CACHE
    if _ROUTED_CACHE is not None:
        return _ROUTED_CACHE
    out = set()
    for f in ROUTED_FROM:
        try:
            text = open(_o.path.join(ROOT, f)).read()
        except OSError:
            # ⛔ Not a silent skip. A missing routing surface means the OVERRIDE cannot
            # fire, so files that should be live would be tiered frozen and never
            # scanned -- a narrowing that reports FEWER findings, which reads exactly
            # like a repo that got cleaner.
            raise SystemExit(f"refcheck: cannot read {f}, which the docs tier is derived "
                             f"from (ROUTED_FROM). Refusing to tier without it.")
        out |= {m.group(1).replace("../", "") for m in ROUTED_RE.finditer(text)}
    _ROUTED_CACHE = out
    return out


def _tier_of_doc(rel, routed=None):
    """Tier of a `docs/...` path. Raises if its directory has not been tiered.

    Three tests in order -- see the DOCS_FROZEN_DIRS comment for why the directory
    alone is not the tier.
    """
    parts = rel.split("/")
    seg = parts[1] if len(parts) > 2 else "<root>"
    if seg in DOCS_LIVE_DIRS:
        return "live"
    if seg not in DOCS_FROZEN_DIRS:
        # ⛔ RAISE, never default into a tier. Landing silently in LIVE puts findings in
        # the default set the day promotion happens; landing silently in FROZEN hides them
        # forever; neither reads as a decision anyone took. And a run that cannot say what
        # its scan set EXCLUDES must not print a number -- that is the same rule this
        # instrument is built to enforce, applied to itself.
        #
        # ⚠️ NOT the three-outcome exit contract, which is a recorded DECLINE: originally
        # at v1.29.0, then re-adopted and reverted twice (2026-08-29, and 2026-09-11 ->
        # 2026-09-12) -- docs/decisions/framework-adoption-history.md, llm-distillery#134.
        # That was a VERDICT nothing read. This aborts BEFORE any verdict, and what
        # carries it is the printed demand, which the human running the audit reads --
        # the caller this script actually has.
        raise SystemExit(
            f"refcheck: docs/{seg}/ has no tier, so the scan set is undefined -- refusing "
            f"to report a number. Add '{seg}' to DOCS_LIVE_DIRS (maintained; a dead "
            f"reference there costs something) or DOCS_FROZEN_DIRS (dated accounts of a "
            f"moment, correct as history). llm-distillery#134 step 2.")
    if rel in (_routed_targets() if routed is None else routed):
        return "live"                       # the always-loaded layer points agents here
    if seg == "_archive":
        return "frozen"                     # frozen by definition, not by date
    if _DATED_RE.search(rel):
        return "frozen"
    # rule 3, depth-restricted: docs/<frozen-dir>/<file>.md only
    return "live" if len(parts) == 3 else "frozen"


# ⛔ An UNRECOGNISED ARGUMENT must not read as a clean run, and "unrecognised" is not
# "starts with --". The first draft checked only `--`-prefixed tokens and its own error
# message then asserted "there are no positional arguments" while not enforcing it:
# `refcheck.py . CLAUDE.md memory/MEMORY.md` -- the /audit-context command with its one
# flag dropped -- ran to exit 0 and printed the full default report, which is precisely
# the "small, reassuring findings count" the guard was written against. `-docs`, `-h` and
# an em-dash `--docs` did the same, and em dashes are everywhere in this repo's prose.
# Found by the adversarial lens of /review-changes; all four reproduced before this line
# was widened. Upstream's checker DOES take --sibling-root and positional arguments, so a
# command copied from the skill runs a DIFFERENT PROGRAM here.
#
# Module level, not inside _docs_files(): under SEED the DOCS ternary never calls that
# function, and the harness is where a typo is most likely to be copied.
for _a in _o.sys.argv[1:]:
    if _a not in KNOWN_FLAGS:
        raise SystemExit(f"refcheck: unrecognised argument {_a!r}. This fork takes only "
                         f"{', '.join(KNOWN_FLAGS)} -- siblings are auto-discovered and "
                         f"there are no positional arguments.")


def _docs_files():
    argv = _o.sys.argv
    want = {"live": ("--docs" in argv or "--docs-live" in argv),
            "frozen": ("--docs" in argv or "--docs-frozen" in argv)}
    if not any(want.values()):
        return []
    out = []
    for f in sorted(_g.glob(_o.path.join(ROOT, "docs", "**", "*.md"), recursive=True)):
        rel = _o.path.relpath(f, ROOT).replace(os.sep, "/")
        if want[_tier_of_doc(rel)]:
            out.append(rel)
    return out


DOCS = ["CLAUDE.md", "memory/MEMORY.md", "memory/gotcha-log.md"] \
       + _topic_files() \
       + _docs_files() \
       + ([AUTOMEM_INDEX] if _o.path.exists(AUTOMEM_INDEX) else []) \
       if not _o.environ.get("SEED") else [_o.environ["SEED"]]

EXT = {"md","py","json","jsonl","yaml","yml","sh","ps1","ini","txt","toml","js","jinja",
       "cfg","sql","ts","tsx","astro","pkl","safetensors","csv","lock","service",
       "html","log","png","pdf","tsv","env","service","socket","timer"}
PRUNE = {".git","node_modules","venv",".venv","target","__pycache__",".mypy_cache"}
STATE_DIRS = ("data/","state/","cache/","logs/","run/","var/","artifacts/",
              # 2026-08-16: the datasets/ CORPUS subdirs only -- each has 0
              # git-tracked files and is re-materialised routinely. NOT bare
              # `datasets/`: adverse/ (14 tracked) and parity/ (8 tracked) are
              # committed adjudication and cross-box sets, exactly the files a
              # broken reference most needs reported, and a bare prefix would
              # mark all 22 expected-absent.
              #
              # ⚠️ HISTORICAL, AND NO LONGER TRUE OF THE CODE (superseded
              # 2026-09-17). This note used to read: "rung3 sits INSIDE the
              # STALE-PLACEHOLDER `resolves` disjunction, so adding a dir here makes
              # any `<!-- placeholder -->` on that dir fire STALE IMMEDIATELY --
              # measured, findings went 1 -> 4. The two mechanisms are alternatives,
              # never both." The measurement was right and the remedy was the wrong
              # one: the three markers were removed to satisfy a shape test that can
              # never stop matching, so the coupling came back the moment anyone wrote
              # a state path again (it did, four times, 2026-09-07..09-10). rung3 is
              # now excluded from that disjunction at its own site, and the two
              # mechanisms are independent. Adding a dir here is safe for markers.
              "datasets/raw/","datasets/scored/","datasets/training/",
              "datasets/screening/","datasets/calibration/","datasets/gate/")
STATE_SHAPE = re.compile(r"(_state\.json|_health\.json|\.pid|\.sock|\.log)$")

# NOTE the char class ADMITS < and >, and allows a trailing >. Without that,
# angle-bracket placeholders (`filters/<name>/<version>/config.yaml`) are never
# EXTRACTED, so "not reported" silently means "never checked" -- indistinguishable
# from a working skip. Caught by seed cases 14 and 17 on 2026-08-12.
PATH_RE = re.compile(r"`([A-Za-z0-9_<][A-Za-z0-9_./+<>-]*\.(?:" + "|".join(EXT) + r")>?)`")
# v1.23.0 (#45) — paths that were never meant to resolve: instructional
# placeholders, files a runbook tells the reader to create, units owned by
# another repo. Ported from the framework's copy rather than swapped for it:
# ours adds the generic-artifact-name class, which upstream lacks, and a plain
# swap re-reported 33 `config.yaml` matches as collisions.
# v1.26.1 — an entry that is FILENAME-shaped rather than EXTENSION-shaped re-admits
# the phantom class the whitelist exists to exclude: the rule matches the tail of any
# dotted token, so `env` captures `process.env`, a code identifier no rung can resolve.
# Keep such a token only when it still looks like a path: it contains a "/"
# (`config/settings.env`), or it starts with a "." (`.config.env`). A bare `.env` is
# never extracted at all -- PATH_RE requires a character before the dot -- and
# `.env.example`'s extension is `example`, so neither reaches this test.
# Measured here 2026-08-27: ZERO occurrences in the scanned set, so this is a guard
# against a future phantom, not a fix for an observed one. Counted, never dropped
# silently -- an un-extracted path and a skipped one must stay distinguishable.
IDENTIFIER_EXT = {"env"}
def _is_identifier_not_path(frag):
    ext = frag.rsplit(".", 1)[-1].rstrip(">")
    if ext not in IDENTIFIER_EXT: return False
    return "/" not in frag and not frag.startswith(".")

# v1.28.0 (#55) — a markdown link's TEXT is a label, not a reference; its URL is the
# reference. In [`writing-guide.md`](templates/writing-guide.md) the URL resolves and
# the label is presentation, so extracting the label MANUFACTURES a collision against
# any same-named file -- meaning the better a document follows this framework's own
# recommended link style, the more phantom findings it generates, and the pressure is
# to stop backticking link text, which makes the docs worse.
#
# Masking alone would be a SILENT LOSS, not a noise reduction: the label used to give a
# broken URL accidental coverage. So every URL we decline to check is REPORTED with its
# reason, never dropped.
LINK_RE = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*([^)\s]+)(?:\s+(?:\"[^\"]*\"|\'[^\']*\'))?\s*\)")
def _mask_link_labels(line):
    """Blank the LABEL span, preserving offsets so the span-scoped placeholder
    arithmetic below is untouched, and extract the URL in its place."""
    out = line
    for m in LINK_RE.finditer(line):
        a, b = m.start(1), m.end(1)
        out = out[:a] + " " * (b - a) + out[b:]
    return out

def _link_urls(line):
    """-> (refs, declined). A URL we cannot check is named with its reason."""
    refs, dec = [], []
    for m in LINK_RE.finditer(line):
        u = m.group(2).strip()
        bare = u.split("#", 1)[0].split("?", 1)[0]
        if re.match(r"^(https?:|mailto:|ftp:|//)", u):   dec.append((u, "external URL")); continue
        if u.startswith("#"):                            dec.append((u, "bare anchor")); continue
        if not bare or bare.endswith("/"):               dec.append((u, "directory")); continue
        ext = bare.rsplit(".", 1)[-1] if "." in os.path.basename(bare) else ""
        if ext not in EXT:  dec.append((u, f"extension outside whitelist ({ext or 'none'})")); continue
        if _is_identifier_not_path(bare): dec.append((u, "identifier-shaped, not a path")); continue
        refs.append(bare)
    return refs, dec

PLACEHOLDER_RE = re.compile(r"<!--\s*placeholder\s*-->")
ANGLE_SEG_RE   = re.compile(r"<[^>]+>")
SPAN_RE        = re.compile(r"`[^`]*`")
def _mask_spans(line):
    """Blank code spans, preserving offsets, so a marker MENTIONED inside
    backticks (this file, or any doc explaining the convention) is not read as
    a marker in use."""
    return SPAN_RE.sub(lambda m: " " * len(m.group(0)), line)
# ---------------------------------------------------------------- #122
# PATH SHAPES NOT EXTRACTED. Ported from the framework's refcheck.py on
# 2026-09-17 (/audit-context); the fork had the EXTENSIONS line and not this one.
#
# ⚠️ THE TWO OMISSION AXES ARE DIFFERENT, AND ONLY ONE WAS REPORTED. "Report what
# the extractor dropped" was implemented for dropped EXTENSIONS. A dropped SHAPE
# had no equivalent line, so a document naming `C:\dev\notes.md` -- or, here,
# `filters/{name}/v{N}/prefilter.py` and `~/.claude/projects/<slug>/memory/MEMORY.md`
# -- got a clean verdict from a run that never examined it. That is this repo's own
# negatives rule turned on its checker: a CLEAN says nothing about what was never
# looked at. Measured on the real corpus at port time: 6 tokens across CLAUDE.md and
# memory/gotcha-log.md.
#
# These are NOT findings. Nothing here is known to be wrong, only unchecked. Naming
# them decides nothing and forecloses nothing; giving each shape a rung is a separate
# change needing a disposition and seeded cases per shape.
#
# ⚠️ NAMED SHAPES, NOT A GENERIC SEPARATOR CLASS. Upstream wrote the generic form
# first, measured it, and refuted it: `[/\\{[]` plus an extension tail reported 61
# entries / 26 distinct tokens over its own tracked markdown, most not path
# references at all (a regex `X\.Y\.Z`, an npm package, a git ref). Adding a shape
# means adding a ROW here -- the visible edit that widening a character class is not.
# The tail is the EXTRACTOR'S OWN whitelist, which also stops the two axes
# overlapping: an unwhitelisted extension is the EXTENSIONS line's business.
_TAIL = r"\.(?:" + "|".join(EXT) + r")$"
UNEXTRACTED_SHAPES = (
    ("brace group",         re.compile(r"^[^\s`]*\{[^\s`]*\}[^\s`]*" + _TAIL)),
    ("bracket placeholder", re.compile(r"^[^\s`]*\[[^\s`]+\][^\s`]*" + _TAIL)),
    ("root-absolute",       re.compile(r"^/[^\s`]*" + _TAIL)),
    ("home-relative",       re.compile(r"^~/[^\s`]*" + _TAIL)),
    ("Windows path",        re.compile(r"^[A-Za-z]:\\[^\s`]*" + _TAIL)),
    ("UNC path",            re.compile(r"^\\\\[^\s`]+" + _TAIL)),
)

def _unextracted_shapes(raw_line):
    """Backticked spans that look like a path and that PATH_RE did not take."""
    out = []
    for m in SPAN_RE.finditer(raw_line):
        frag = m.group(0).strip("`").strip()
        if not frag or PATH_RE.fullmatch("`" + frag + "`"):
            continue
        if "://" in frag:
            continue
        for label, rx in UNEXTRACTED_SHAPES:
            if rx.match(frag):
                out.append((frag, label))
                break
    return out

# spans whose paths are ASSERTED ABSENT — scoped to the span, never the line
#
# 2026-08-11: added the "we keep no X" family. The audit reported CLAUDE.md's
# `hypothesis-log.md` as UNRESOLVED when the prose around it says "we keep no
# `hypothesis-log.md` at either path" — an absence assertion, and correct as
# written. The tell was the report itself: SKIPPED AS ASSERTED-ABSENT read 0
# across three documents, which is implausible for docs that record removals.
# Kept tight and span-scoped: the pattern must reach the backticked path, so a
# sentence that retires one file and names its replacement still yields the
# replacement.
ABSENT_SPANS = [re.compile(r"~~(.+?)~~"),
                re.compile(r"!\s*test\s+-f\s+(\S+)"),
                re.compile(r"\*\*Deleted\*\*:\s*(`[^`]+`)"),
                # "we keep no `x.md`" / "keeps no `x.md`" / "no `x.md` at either path"
                re.compile(r"\bkeeps?\s+no\s+(`[^`]+`)", re.I),
                re.compile(r"\bno\s+(`[^`]+`)\s+at\s+either\s+path", re.I)]
# REJECTED, and left here so it is not re-attempted: patterns of the shape
#   r"(`[^`]+`)\s+(?:was|were|has been)\s+(?:removed|deleted)"
#   r"(`[^`]+`)\s+no\s+longer\s+exists"
# Tried 2026-08-11 and reverted the same minute. Prose past-tense cannot
# distinguish "this file is gone" from "this file was once deleted, and that is
# the story being told". It matched gotcha-log's account of the 2026-04-16
# normalization incident — "`filter_base_scorer.py` was deleted on 2026-04-16" —
# and silently skipped a file that exists right now, taking 8 occurrences out of
# the report. A skip is the one outcome with no rung to name, so a false skip is
# invisible. Absence markers must be STRUCTURAL (`~~`, `**Deleted**:`,
# `! test -f`) or an explicit present-tense statement about what the repo keeps.

def walk(base):
    out=[]
    for dp,dn,fn in os.walk(base):
        dn[:] = [d for d in dn if d not in PRUNE]
        for f in fn: out.append(os.path.relpath(os.path.join(dp,f), base))
    return out

TREE = walk(ROOT)
BY_SUFFIX = defaultdict(list)
for p in TREE: BY_SUFFIX[p].append(p)

def rung2(frag):
    """whole-fragment suffix match against the working tree"""
    hits=[p for p in TREE if p==frag or p.endswith("/"+frag)]
    return hits

SELF = os.path.basename(ROOT)

def selfstrip(frag):
    """Drop a leading component that repeats THIS repo's name.

    2026-08-15 (/audit-context): rung 4 has stripped a leading *sibling* repo name
    since it was written, but nothing stripped the LOCAL one -- so
    `llm-distillery/scripts/remote_deploy.sh` was reported UNRESOLVED while
    `scripts/remote_deploy.sh` sat in the tree. The shape is common in this repo's
    docs: a cross-repo sentence qualifies every path, including its own.

    This is a LOOSENING, and a loosening can only ever turn a report into a
    resolution -- so the risk is laundering a genuine break. It is bounded the same
    way rungs 2 and 4 are: the stripped form still has to resolve on its own, and a
    multi-match still reports as a COLLISION rather than picking a winner. Seeded as
    cases 21-23; 22 (fabricated behind the prefix) and 23 (ambiguous behind the
    prefix) are the newly-permitted failures, not the case it was built for.
    """
    parts=frag.split("/")
    return "/".join(parts[1:]) if len(parts)>1 and parts[0]==SELF else None

def rung3(frag):
    if frag.startswith(STATE_DIRS) or STATE_SHAPE.search(frag):
        # data, not source: a source file merely named *_state.py is still source
        if not frag.endswith(".py"): return True
    return False

SIBS={}
for r in SIBLING_ROOTS:
    for d in glob.glob(os.path.join(r,"*")):
        if os.path.isdir(d) and os.path.isdir(os.path.join(d,".git")):
            SIBS[os.path.basename(d)] = d
SIB_TREES={}

GENERIC = {"docs","src","scripts","tests","config","memory","filters","data","lib"}

# A bare `foo.service` / `foo.timer` / `foo.socket` is a systemd UNIT NAME, not a file locator. Prose says
# "`nexusmind.service` runs `deploy_filters.sh` as ExecStartPre" -- the subject is the
# running unit; which repo's deploy/ dir holds its definition is incidental, and is
# exactly the token rung 4 needs in the window and rarely gets. Four unit names
# accounted for 6 of 15 findings across three audits without one of them ever being a
# real break (/audit-context 2026-08-15).
#
# This is DELIBERATELY NOT a blanket skip: the unit file must exist SOMEWHERE in the
# estate. A fabricated unit resolves nowhere and stays a finding -- so the newly
# permitted failure (laundering a made-up unit) cannot occur. Seeded as case 24.
UNIT_INDEX=None
def unit_lookup(frag):
    global UNIT_INDEX
    if "/" in frag or not frag.endswith((".service",".timer",".socket")): return None
    if UNIT_INDEX is None:
        UNIT_INDEX=defaultdict(list)
        for p in TREE:
            if p.endswith((".service",".timer",".socket")): UNIT_INDEX[os.path.basename(p)].append(SELF+"/"+p)
        for name,path in SIBS.items():
            for p in walk(path):
                if p.endswith((".service",".timer",".socket")): UNIT_INDEX[os.path.basename(p)].append(name+"/"+p)
    hits=UNIT_INDEX.get(frag)
    return hits[0] if hits else None

def rung4(frag, ctx):
    ctx_clean = re.sub(r"`[^`]*`", " ", ctx)          # a ref may not mark itself
    first = frag.split("/")[0]
    for name, path in SIBS.items():
        if name == os.path.basename(ROOT): continue
        qualified = (first == name and name.lower() not in GENERIC)
        if not qualified and not re.search(
                r"(?<![A-Za-z0-9_])"+re.escape(name)+r"(?![A-Za-z0-9_])", ctx_clean):
            continue                                   # whole token only
        if name not in SIB_TREES: SIB_TREES[name]=walk(path)
        t=SIB_TREES[name]
        cands=[frag]
        parts=frag.split("/")
        if parts[0]==name and len(parts)>1: cands.append("/".join(parts[1:]))
        for c in cands:
            hits=[p for p in t if p==c or p.endswith("/"+c)]
            if len(hits)==1: return ("rung4", f"{name}/{hits[0]}")
            if len(hits)>1:  return ("collision", f"{name}: {len(hits)} matches for {c}")
    return None

# rung 5 — the Claude Code auto-memory, which lives OUTSIDE ROOT. Extended 2026-08-27
# to `project_session_*.md`: the gotcha log cites `project_session_2026_08_02.md` and
# `_08_03.md`, and both exist in the auto-memory directory at exactly the byte sizes it
# quotes (14,194 / 9,502) -- they were reported UNRESOLVED only because the rung's
# pattern was written for the kebab-case `feedback-*` family. This is a loosening, so
# what it newly permits is laundering a fabricated session file; bounded the same way
# the rest of the rung is -- the file must actually BE in that directory. Seeded.
AUTOMEM_RE = r"((feedback|reference|project)-[a-z0-9-]+|project_session_[0-9a-z_]+)\.md$"
AUTOMEM=os.path.expanduser("~/.claude/projects/"
    + ROOT.replace("/", "-") + "/memory")
findings, resolved, skipped, generic, placeheld = [], [], [], [], []
declined, identifiers = [], []
dropped_shapes = []   # backticked path shapes outside the population (#122)
seen_ext=set()
for doc in DOCS:
    text=open(doc if os.path.isabs(doc) else os.path.join(ROOT,doc)).read()
    # rung 1b needs the REFERRING doc's directory, expressed relative to ROOT.
    # ⚠️ Gate on "outside ROOT", NOT on "absolute". The first draft used isabs(), which
    # ALSO disabled rung 1b for any doc named by an absolute path -- and run.sh names
    # SEED.md absolutely, so the rung silently never fired under its own harness while
    # working in the real run. Caught only because the seeded assertion tests the RUNG
    # LABEL rather than the mere absence of a finding.
    # The auto-memory index genuinely is outside ROOT, where doc-relative has no
    # meaning; rung5 covers it.
    # ⚠️ ONE spelling of "relative to ROOT, or outside it". This was a second,
    # independent copy of _relroot()'s predicate (`startswith("..")` against its
    # `startswith("../") or == ".."`), which is how two copies of one rule drift apart.
    docdir = os.path.dirname(_relroot(doc))
    absent=set()
    for rx in ABSENT_SPANS:
        for m in rx.finditer(text):
            for p in PATH_RE.finditer(m.group(0)): absent.add(p.group(1))
            # a struck / **Deleted**: / `! test -f` markdown LINK asserts absence just
            # as a backticked path does; without this the URL arm re-reports it.
            for u in _link_urls(m.group(0))[0]: absent.add(u)
    lines=text.split("\n")
    # YAML frontmatter is ONE marker scope. A `framework: <repo> vN` stamp on its
    # own line declares the whole frontmatter's cross-repo context, but the
    # references that rely on it sit several lines lower inside a block scalar --
    # outside the 1-line window, so they were reported UNRESOLVED while existing
    # in the sibling all along (4 false findings, /audit-context 2026-08-11).
    # Deliberately NOT widened to the enclosing block: a dense markdown table is
    # contiguous non-blank lines, so block scope would put unrelated rows in
    # range, which is the over-absorption the skill warns about. Frontmatter is
    # bounded, hand-maintained, and semantically one declaration.
    fm_end=0
    if lines and lines[0].strip()=="---":
        for k in range(1,len(lines)):
            if lines[k].strip()=="---": fm_end=k; break
    fm_ctx=" ".join(lines[:fm_end]) if fm_end else ""
    for ln,line in enumerate(lines):
        ctx=" ".join(lines[max(0,ln-1):ln+2])
        if fm_end and ln<fm_end: ctx=fm_ctx
        # SPAN-scoped, not line-scoped: a marker covers the nearest eligible
        # path BEFORE it. Line-scoping relabels a co-located genuine break as
        # intentional -- the defect already measured once for strikethrough.
        placeheld_frags=set()
        mline=_mask_link_labels(line)      # #55: label is presentation, URL is the reference
        for _shfrag, _shlbl in _unextracted_shapes(line):
            if (doc, _shfrag, _shlbl) not in dropped_shapes:   # a token repeats per line
                dropped_shapes.append((doc, _shfrag, _shlbl))
        url_refs, url_dec = _link_urls(line)
        for u,why in url_dec: declined.append((doc,u,why))
        eligible=[m for m in PATH_RE.finditer(mline)]
        for pm in PLACEHOLDER_RE.finditer(_mask_spans(mline)):
            before=[m for m in eligible if m.end()<=pm.start()]
            # ADJACENCY: only whitespace may sit between the path and its marker.
            # Without this, a trailing marker absorbs whatever broken path happened
            # to come last on the line -- silently, and in the one direction that
            # hides a defect (a marker placed too early fails LOUD as COVERS NO PATH).
            if before and line[before[-1].end():pm.start()].strip()=="":
                placeheld_frags.add(before[-1].group(1))
            else:
                findings.append((doc,f"(line {ln+1})",
                    "PLACEHOLDER MARKER COVERS NO PATH -- it is span-scoped and takes the "
                    "nearest backticked path before it. Either none is there, or the token "
                    "is not extractable (directory, glob, URL, or an extension outside the "
                    "whitelist -- that last one is a whitelist gap, not a marker problem)"))
        for frag in [m.group(1) for m in PATH_RE.finditer(mline)] + url_refs:
            seen_ext.add(frag.rsplit(".",1)[-1])
            if _is_identifier_not_path(frag): identifiers.append((doc,frag)); continue
            if frag in absent: skipped.append((doc,frag)); continue
            if frag in placeheld_frags or ANGLE_SEG_RE.search(frag):
                # A marker on a path that DOES resolve is the failure this skip
                # newly permits: mislabelling is how a real break gets hidden.
                # Strip the angle markers before testing resolution: the whole
                # point of the angle form is that <name> stands for a variable
                # segment, so `tests/unit/<real_file.py>` -- a real path merely
                # wrapped in brackets -- must be caught as a mislabel, and it
                # can only be caught by resolving the DE-ANGLED form.
                # De-angle ONLY whole path components (`/<x>/`, `<x>` as the
                # basename stem) -- de-angling a partial word made
                # `docs/<FILTER>_PLAYBOOK.md` resolve to a real file and report a
                # false STALE, which costs the re-triage this skip exists to remove.
                bare=re.sub(r"<([^<>/]*)>", r"\1", frag) if re.fullmatch(r"[^<>]*(<[^<>/]+>[^<>]*)+", frag) else frag
                # ⚠️ FULL LADDER. Checking only rungs 1-2 made this guard unable to
                # fire for CROSS-REPO paths -- which is where every placeholder in
                # this repo actually lives. 7 of 12 markers were mislabelling real
                # files when that was found (2026-08-12 review). A guard that cannot
                # fire for its own population is this repo's signature defect.
                _ss = selfstrip(bare)
                # #56 (v1.28.0): LOCALLY "does resolve" means rung 1 -- deliberately
                # NOT the suffix rung. A marker whose path merely shares a SUFFIX with
                # some file elsewhere is not evidence of mislabelling; that is the
                # bare-basename ambiguity rung 2 exists to FLAG, and using it to
                # ADJUDICATE INTENT leaves an author who ships a template AND instances
                # of it no correct move (marked -> STALE, unmarked -> COLLISION, both
                # findings, neither a defect, re-triaged every audit).
                # ⚠️ RUNG 4 STAYS. The 2026-08-12 measurement that put the full ladder
                # here (7 of 12 markers mislabelling real files) was a CROSS-REPO
                # finding, so dropping rung 2 does not touch that evidence. Verified:
                # seeds 13/14 resolve at rung 1 and 20 at rung 4, so all three survive.
                #
                # ⛔ RUNG 3 IS EXCLUDED HERE, AND IT IS THE ONLY RUNG THAT HAS TO BE
                # (/audit-context 2026-09-17). Every other rung asks "is this file
                # THERE?"; rung 3 asks "does this path LOOK like runtime state?" --
                # `frag.startswith(STATE_DIRS)`, a pure shape test that no file system
                # can falsify. So an angle-segment path under a state directory --
                # `data/raw/.processed_ids_<name>.json`, the correct way to write a
                # per-filter state store -- was ruled STALE unconditionally, and the
                # author had no legal move: the angle form is mandatory for a variable
                # segment, and rung 3 always says it "resolves". That is exactly the
                # no-correct-move shape the #56 note above describes, one rung over.
                # Measured: 3 of this audit's 23 findings, all four sites written
                # 2026-09-07..09-10 and guaranteed to recur at every future audit
                # because a shape test cannot stop matching. Upstream's checker already
                # counts these in its declared-placeholder section ("decided at rung 3
                # (runtime state)"); the fork was the one diverging.
                #
                # ⚠️ WHAT THIS NEWLY PERMITS, and why it is bounded: a path that is
                # angle-marked, under a state directory, AND really on disk. Rung 1 is
                # tested FIRST in the same expression and catches precisely that case,
                # so the only thing lost is a path that does NOT exist and merely
                # starts with `data/` -- which was never evidence of mislabelling.
                # Seeded both ways (run.sh cases 34/35) before this line was written.
                resolves = (os.path.exists(os.path.join(ROOT,bare))
                            or (_ss and os.path.exists(os.path.join(ROOT,_ss)))
                            or (docdir and os.path.exists(os.path.join(
                                   ROOT, os.path.normpath(os.path.join(docdir,bare)))))
                            or rung4(bare, ctx)
                            or (re.match(AUTOMEM_RE, bare)
                                and os.path.exists(os.path.join(AUTOMEM, bare))))
                if resolves:
                    findings.append((doc,frag,"STALE PLACEHOLDER MARKER (the path resolves)"))
                else:
                    placeheld.append((doc,frag))
                continue
            if os.path.exists(os.path.join(ROOT,frag)): continue          # rung 1
            # rung 1b (v1.28.0 #54) — DOC-RELATIVE, and it is not a courtesy rung:
            # markdown link semantics ARE doc-relative, so a bare `b650-gpu.md` in
            # memory/MEMORY.md means the file beside it. Without it such a reference
            # either misses rung 1 outright or is DOWNGRADED at rung 2 to a COLLISION
            # -- reported as a defect requiring a decision when there is nothing to
            # decide (42 of 102 findings, 41%, on the adopter that reported it).
            # MUST sit above rung 2 or the collision fires first. Enumerated, not
            # silent, so a reader can see how much of the tree resolves this way.
            if docdir:
                dr=os.path.normpath(os.path.join(docdir,frag))
                if not dr.startswith("..") and os.path.exists(os.path.join(ROOT,dr)):
                    resolved.append((doc,frag,"rung1b",dr)); continue
            # rung 1b-outside (/audit-context 2026-09-26) — the same doc-relative
            # semantics for a doc OUTSIDE ROOT, which `docdir` above cannot express.
            # The auto-memory index links `../../../../repos/.../memory/X.md`: correct,
            # existing, and ruled UNRESOLVED because rung5 only knows the auto-memory
            # directory's own files. A LOOSENING, so bounded: the resolved path must
            # land INSIDE ROOT and exist. A `../` escape to anywhere else is still a
            # finding. Both halves seeded in run.sh (38, 39, 40).
            elif not _relroot(doc):
                ab=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(doc)),frag))
                inr=_relroot(ab)
                if inr and os.path.exists(ab):
                    resolved.append((doc,frag,"rung1b-outside",inr)); continue
            h=rung2(frag)
            if len(h)==1: resolved.append((doc,frag,"rung2",h[0])); continue
            if len(h)>1:
                if "/" not in frag:
                    generic.append((doc,frag,len(h)))   # class of artifact, not a locator
                else:
                    findings.append((doc,frag,f"COLLISION: {len(h)} local matches"))
                continue
            # self-prefix strip: BEFORE rung 3/4, for the same reason rung 3 precedes
            # rung 4 -- a path this repo owns must be explained here, not by a
            # neighbour that happens to carry the same filename.
            ss=selfstrip(frag)
            if ss:
                if os.path.exists(os.path.join(ROOT,ss)):
                    resolved.append((doc,frag,"rung1-self",ss)); continue
                hs=rung2(ss)
                if len(hs)==1: resolved.append((doc,frag,"rung2-self",hs[0])); continue
                if len(hs)>1:
                    findings.append((doc,frag,
                        f"COLLISION: {len(hs)} local matches after self-prefix strip")); continue
            if rung3(frag): resolved.append((doc,frag,"rung3","runtime state")); continue
            if re.match(AUTOMEM_RE, frag) and \
               os.path.exists(os.path.join(AUTOMEM, frag)):
                resolved.append((doc,frag,"rung5","claude auto-memory")); continue
            r4=rung4(frag,ctx)
            if r4 and r4[0]=="rung4": resolved.append((doc,frag,"rung4",r4[1])); continue
            if r4: findings.append((doc,frag,r4[1])); continue
            u=unit_lookup(frag)
            if u: resolved.append((doc,frag,"unit",u)); continue
            findings.append((doc,frag,"UNRESOLVED (rungs 1-4 all run)"))

print("="*96); print("STEP 4 — REFERENCE INTEGRITY"); print("="*96)
# ⚠️ Naming every scanned file was readable at 34 and is unreadable at 202. Collapse only
# the LISTING, never the count, and always say which flags were in effect -- a report whose
# scan set you cannot reconstruct is the "establish what a source EXCLUDES" failure in its
# purest form, and this instrument's own history is two widenings whose prior clean results
# were true-but-narrow.
#
# ⛔ THE FLAGS LINE PRINTS ON BOTH BRANCHES, and until 2026-09-17 it printed on neither
# that mattered: `flags:` sat only in the >34 branch, and the default scan set is EXACTLY
# 34 documents -- so the one run anybody makes routinely said nothing about its own scope,
# and one more memory/*.md file would have flipped it. An absolute in a comment
# ("always say which flags were in effect") that the code applies to one branch is the
# same shape as a guard on a path its input never reaches.
_flags = [f for f in KNOWN_FLAGS if f in sys.argv] or ["(none)"]
if len(DOCS) <= 34:
    print(f"docs scanned: {', '.join(DOCS)}   flags: {' '.join(_flags)}   "
          f"working-tree files: {len(TREE):,}   siblings found: {len(SIBS)}")
else:
    _grp = defaultdict(int)
    for d in DOCS:
        _grp[(os.path.dirname(_relroot(d)) or "<repo root>") if _relroot(d)
             else "<outside repo>"] += 1
    print(f"docs scanned: {len(DOCS)} files   flags: {' '.join(_flags)}   "
          f"working-tree files: {len(TREE):,}   siblings found: {len(SIBS)}")
    for k in sorted(_grp): print(f"    {k+'/':44s} {_grp[k]:4d}")
print(f"\n### FINDINGS ({len(set(findings))} unique, {len(findings)} occurrences)")
for d,f,w in sorted(set(findings)): print(f"  {d:22s} {f:50s} {w}")
if not findings: print("  (none)")
print(f"\n### RESOLVED BELOW RUNG 1 ({len(set(resolved))} unique, {len(resolved)} occurrences) — not defects, shown so a wrong twin is visible")
for d,f,r,t in sorted(set(resolved)): print(f"  {d:22s} {f:44s} [{r}] -> {t}")
if not resolved: print("  (none)")
print(f"\n### GENERIC ARTIFACT NAMES ({len(set(generic))} unique) — bare basenames naming a CLASS of file, not a locator")
for d,f,n in sorted(set(generic)): print(f"  {d:22s} {f:44s} {n} instances in tree")
print(f"\n### SKIPPED AS DECLARED-PLACEHOLDER ({len(set(placeheld))} unique) — never meant to resolve; counted, not dropped")
for d,f in sorted(set(placeheld)): print(f"  {d:22s} {f}")
if not placeheld: print("  (none)")
print(f"\n### SKIPPED AS ASSERTED-ABSENT ({len(set(skipped))} unique)")
for d,f in sorted(set(skipped)): print(f"  {d:22s} {f}")
if not skipped: print("  (none)")
print(f"\n### LINK URLS DECLINED ({len(set(declined))} unique) — masking a label is a SILENT LOSS unless the URL is named")
for d,u,w in sorted(set(declined))[:40]: print(f"  {d:22s} {u:44s} {w}")
if not declined: print("  (none)")
print(f"\n### DROPPED AS IDENTIFIER-SHAPED ({len(set(identifiers))} unique) — filename-shaped whitelist entry, not a path")
for d,f in sorted(set(identifiers)): print(f"  {d:22s} {f}")
if not identifiers: print("  (none)")
tree_ext={p.rsplit('.',1)[-1] for p in TREE if '.' in os.path.basename(p)}
drop=sorted(e for e in tree_ext if e not in EXT and len(e)<=12 and e.isalnum())
if dropped_shapes:
    print(f"\n### PATH SHAPES NOT EXTRACTED ({len(dropped_shapes)} unique) — outside the population, never checked")
    for _d, _f, _l in sorted(dropped_shapes):
        print(f"  {_d:22s} {_f:50s} {_l}")
    print("  Backticked, path-shaped, and never extracted — each labelled with the shape that\n"
          "  put it here. NOT findings: unchecked, not known-wrong. The FINDINGS count above\n"
          "  says nothing about these (#122).")
print(f"\n### EXTENSIONS IN TREE NOT IN WHITELIST (dropped by the extractor)\n  {', '.join(drop[:40])}")

# llm-distillery#134 step 2 needs findings attributed to a TIER, not a total. A single
# number cannot distinguish "the live documents an agent is routed into are rotting" from
# "frozen records name paths the world has since moved", and those want opposite responses:
# fix the first, never edit the second. Printed for every run, so the default scan set is
# broken out the same way and the two are comparable.
print("\n### FINDINGS BY DIRECTORY — attribution, because a total cannot be tiered")
_fd, _sd = defaultdict(int), defaultdict(int)
for d, *_ in set(findings):
    _fd[(os.path.dirname(_relroot(d)) if _relroot(d)
         else "<outside repo>") or "<repo root>"] += 1
for d in DOCS:
    _sd[(os.path.dirname(_relroot(d)) if _relroot(d)
         else "<outside repo>") or "<repo root>"] += 1
if not findings: print("  (no findings)")
for k in sorted(_sd):
    if _fd[k]: print(f"  {k+'/':44s} {_fd[k]:4d} unique in {_sd[k]:4d} file(s)")
_silent = [k for k in sorted(_sd) if not _fd[k]]
print(f"  -- clean: {', '.join(_silent) if _silent else '(none)'}")

# llm-distillery#134 step 2 (2026-09-17) — THE TIER, EMITTED BY THE INSTRUMENT. It was a
# hand-written table, and its drift re-read was recomputed by hand in the issue's
# comments; a hand-built population is what every measurement error this project has made
# turned out to be.
#
# ⛔ THE SPLIT IS THE SIGNAL, BUT IT IS NOT A RATE, AND THE FIRST DRAFT OF THIS COMMENT
# READ IT AS ONE. It said "frozen grew ~7x faster", and #134's own comment said "~8x".
# The denominator kills both: over those twenty days the whole `docs/` corpus went from
# 168 files to 242, the growth almost entirely DATED EVIDENCE DIRECTORIES, which is the
# frozen tier by construction. More frozen findings because there are more frozen files
# is not a rot rate. Re-scored under today's rule by
# `scripts/analysis/refcheck_tier_reparse.py`, from the two stored logs:
# live 265 -> 274, frozen 73 -> 104. The promotion decision rests on neither -- 274 live
# findings against a 0-finding default stands alone -- and the file counts below are
# printed so the next reader is not handed a count to mistake for a rate.
#
# ⚠️ Printed only for a tier that is IN the scan set. A tier that was not scanned prints
# "not scanned", never 0: "live 0 / frozen 0" would be a verdict over a population that
# contains none of that tier -- a zero carrying no information, which is the failure this
# file's own header warns about. The first draft printed the zero under --docs-live and
# --docs-frozen, i.e. in the two runs this change exists to add, and a test asserted it.
_docs_in_scan = [d for d in DOCS if _relroot(d).startswith("docs/")]
if _docs_in_scan:
    _tf, _tfiles, _thit = defaultdict(int), defaultdict(int), defaultdict(set)
    # ⛔ THE OVERRIDES ARE COUNTED IN THE REPORT, because rule 2 makes the tier a
    # function of MUTABLE TEXT. `CLAUDE.md` is the most-edited file here and its pointer
    # table is under a per-row cap that every audit trims, so the likely edit is a
    # REMOVAL -- which moves a file live -> frozen and makes the LIVE count FALL. A
    # falling LIVE count reads as "the marking pass is working", which is the exact
    # direction this instrument's own tests say they exist to catch. It cannot be
    # prevented without going back to a hand-kept list, so it is made VISIBLE: if this
    # number drops, a pointer went away, and the report says so where the audit reads it.
    _ovr = defaultdict(int)
    for d in _docs_in_scan:
        _rel = _relroot(d)
        _parts = _rel.split("/")
        if len(_parts) > 2 and _parts[1] in DOCS_FROZEN_DIRS \
           and _tier_of_doc(_rel) == "live":
            _ovr["routing" if _rel in _routed_targets() else "undated index"] += 1
        _tfiles[_tier_of_doc(_rel)] += 1
    for d, *_ in set(findings):
        rel = _relroot(d)
        if rel.startswith("docs/"):
            _tf[_tier_of_doc(rel)] += 1
            _thit[_tier_of_doc(rel)].add(rel)
    print("\n### FINDINGS BY TIER — docs/ only (#134 step 2); the split, not the total")
    for t in ("live", "frozen"):
        dirs = ", ".join(DOCS_LIVE_DIRS if t == "live" else DOCS_FROZEN_DIRS)
        if not _tfiles[t]:
            print(f"  {t.upper():7s} not scanned   {dirs}")
            continue
        # ⚠️ TWO file counts, because one word cannot carry both. "212 in 103 files" was
        # read as "103 files have findings" when 103 was the files SCANNED -- and it is
        # the number that sizes the marking pass, so the ~2x error landed in the document
        # defining the work.
        why = ""
        if t == "live" and _ovr:
            why = "   [+" + ", +".join(f"{n} by {k}" for k, n in sorted(_ovr.items())) + "]"
        print(f"  {t.upper():7s} {_tf[t]:4d} unique in {len(_thit[t]):4d} of "
              f"{_tfiles[t]:4d} scanned file(s)   {dirs}{why}")
    # ⚠️ These lines deliberately do NOT begin with a tier name. They did, and a
    # consumer matching "the line starting with LIVE" then picked up the prose instead
    # of the numbers -- it raised rather than asserting, which is luck, not a guard.
    print("  The live tier is the promotion candidate and is NOT in the default scan\n"
          "  set: it would replace a 0-finding baseline with 200+ and cost the ability\n"
          "  to see a NEW break. Frozen records stay flag-gated permanently -- correct\n"
          "  as history, never to be edited to satisfy this checker (#123). A frozen\n"
          "  DIRECTORY does not freeze a file the always-loaded layer routes into, or an\n"
          "  undated index sitting beside the dated ones: see _tier_of_doc.")
