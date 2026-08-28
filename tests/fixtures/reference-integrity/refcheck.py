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
# ⚠️ FLAG-GATED ON PURPOSE, and it must stay that way until the tiering in #134 step 2 is
# settled. `docs/evidence/` and (largely) `docs/decisions/` are frozen accounts of a
# moment -- structurally identical to `memory/project_session_*.md`, which this file
# already excludes by default with exactly that rationale. Promoting docs/ to the default
# scan set before tiering would MANUFACTURE findings against files that are correct as
# history, and the pressure would then be to edit the history to silence the checker,
# which is the compression #123 forbids.
#
# ⛔ Step 1 is to MEASURE, so this flag deliberately takes ALL of docs/**/*.md rather than
# a guessed live subset: the per-directory breakdown printed at the end of the run is the
# evidence the tiering decision needs, and a subset chosen up front would decide the
# question it was supposed to inform.
def _docs_files():
    if "--docs" not in _o.sys.argv:
        return []
    return [_o.path.relpath(f, ROOT)
            for f in sorted(_g.glob(_o.path.join(ROOT, "docs", "**", "*.md"),
                                    recursive=True))]


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
              # ⚠️ rung3 sits INSIDE the STALE-PLACEHOLDER `resolves` disjunction
              # (see below), so adding a dir here makes any `<!-- placeholder -->`
              # on that dir fire STALE IMMEDIATELY -- measured, findings went
              # 1 -> 4. The two mechanisms are alternatives, never both: the three
              # markers these dirs cover were removed in the same commit.
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
    if os.path.isabs(doc):
        _rel = os.path.relpath(doc, ROOT)
        docdir = "" if _rel.startswith("..") else os.path.dirname(_rel)
    else:
        docdir = os.path.dirname(doc)
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
                resolves = (os.path.exists(os.path.join(ROOT,bare))
                            or (_ss and os.path.exists(os.path.join(ROOT,_ss)))
                            or (docdir and os.path.exists(os.path.join(
                                   ROOT, os.path.normpath(os.path.join(docdir,bare)))))
                            or rung3(bare) or rung4(bare, ctx)
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
_flags = [f for f in ("--sessions", "--docs") if f in sys.argv] or ["(none)"]
if len(DOCS) <= 34:
    print(f"docs scanned: {', '.join(DOCS)}   working-tree files: {len(TREE):,}   siblings found: {len(SIBS)}")
else:
    _grp = defaultdict(int)
    for d in DOCS:
        _grp[(os.path.dirname(os.path.relpath(d, ROOT)) or "<repo root>")
             if not os.path.isabs(d) or not os.path.relpath(d, ROOT).startswith("..")
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
print(f"\n### EXTENSIONS IN TREE NOT IN WHITELIST (dropped by the extractor)\n  {', '.join(drop[:40])}")

# llm-distillery#134 step 2 needs findings attributed to a TIER, not a total. A single
# number cannot distinguish "the live documents an agent is routed into are rotting" from
# "frozen records name paths the world has since moved", and those want opposite responses:
# fix the first, never edit the second. Printed for every run, so the default scan set is
# broken out the same way and the two are comparable.
print("\n### FINDINGS BY DIRECTORY — attribution, because a total cannot be tiered")
_fd, _sd = defaultdict(int), defaultdict(int)
for d, *_ in set(findings):
    _fd[(os.path.dirname(os.path.relpath(d, ROOT)) if not os.path.isabs(d)
         else "<outside repo>") or "<repo root>"] += 1
for d in DOCS:
    _sd[(os.path.dirname(os.path.relpath(d, ROOT)) if not os.path.isabs(d)
         else "<outside repo>") or "<repo root>"] += 1
if not findings: print("  (no findings)")
for k in sorted(_sd):
    if _fd[k]: print(f"  {k+'/':44s} {_fd[k]:4d} unique in {_sd[k]:4d} file(s)")
_silent = [k for k in sorted(_sd) if not _fd[k]]
print(f"  -- clean: {', '.join(_silent) if _silent else '(none)'}")
