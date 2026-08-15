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
DOCS = ["CLAUDE.md", "memory/MEMORY.md", "memory/gotcha-log.md"] \
       + ([AUTOMEM_INDEX] if _o.path.exists(AUTOMEM_INDEX) else []) \
       if not _o.environ.get("SEED") else [_o.environ["SEED"]]

EXT = {"md","py","json","jsonl","yaml","yml","sh","ps1","ini","txt","toml","js","jinja",
       "cfg","sql","ts","tsx","astro","pkl","safetensors","csv","lock","service",
       "html","log","png","pdf","tsv","env","service","socket","timer"}
PRUNE = {".git","node_modules","venv",".venv","target","__pycache__",".mypy_cache"}
STATE_DIRS = ("data/","state/","cache/","logs/","run/","var/","artifacts/")
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

AUTOMEM=os.path.expanduser("~/.claude/projects/"
    + ROOT.replace("/", "-") + "/memory")
findings, resolved, skipped, generic, placeheld = [], [], [], [], []
seen_ext=set()
for doc in DOCS:
    text=open(doc if os.path.isabs(doc) else os.path.join(ROOT,doc)).read()
    absent=set()
    for rx in ABSENT_SPANS:
        for m in rx.finditer(text):
            for p in PATH_RE.finditer(m.group(0)): absent.add(p.group(1))
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
        eligible=[m for m in PATH_RE.finditer(line)]
        for pm in PLACEHOLDER_RE.finditer(_mask_spans(line)):
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
        for m in PATH_RE.finditer(line):
            frag=m.group(1); seen_ext.add(frag.rsplit(".",1)[-1])
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
                resolves = (os.path.exists(os.path.join(ROOT,bare)) or rung2(bare)
                            or (_ss and (os.path.exists(os.path.join(ROOT,_ss)) or rung2(_ss)))
                            or rung3(bare) or rung4(bare, ctx)
                            or (re.match(r"(feedback|reference|project)-[a-z0-9-]+\.md$", bare)
                                and os.path.exists(os.path.join(AUTOMEM, bare))))
                if resolves:
                    findings.append((doc,frag,"STALE PLACEHOLDER MARKER (the path resolves)"))
                else:
                    placeheld.append((doc,frag))
                continue
            if os.path.exists(os.path.join(ROOT,frag)): continue          # rung 1
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
            if re.match(r"(feedback|reference|project)-[a-z0-9-]+\.md$", frag) and \
               os.path.exists(os.path.join(AUTOMEM, frag)):
                resolved.append((doc,frag,"rung5","claude auto-memory")); continue
            r4=rung4(frag,ctx)
            if r4 and r4[0]=="rung4": resolved.append((doc,frag,"rung4",r4[1])); continue
            if r4: findings.append((doc,frag,r4[1])); continue
            u=unit_lookup(frag)
            if u: resolved.append((doc,frag,"unit",u)); continue
            findings.append((doc,frag,"UNRESOLVED (rungs 1-4 all run)"))

print("="*96); print("STEP 4 — REFERENCE INTEGRITY"); print("="*96)
print(f"docs scanned: {', '.join(DOCS)}   working-tree files: {len(TREE):,}   siblings found: {len(SIBS)}")
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
tree_ext={p.rsplit('.',1)[-1] for p in TREE if '.' in os.path.basename(p)}
drop=sorted(e for e in tree_ext if e not in EXT and len(e)<=12 and e.isalnum())
print(f"\n### EXTENSIONS IN TREE NOT IN WHITELIST (dropped by the extractor)\n  {', '.join(drop[:40])}")
