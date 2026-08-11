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
DOCS = ["CLAUDE.md", "memory/MEMORY.md", "memory/gotcha-log.md"] if not _o.environ.get("SEED") else [_o.environ["SEED"]]

EXT = {"md","py","json","jsonl","yaml","yml","sh","ps1","ini","txt","toml",
       "cfg","sql","ts","tsx","astro","pkl","safetensors","csv","lock","service"}
PRUNE = {".git","node_modules","venv",".venv","target","__pycache__",".mypy_cache"}
STATE_DIRS = ("data/","state/","cache/","logs/","run/","var/","artifacts/")
STATE_SHAPE = re.compile(r"(_state\.json|_health\.json|\.pid|\.sock)$")

PATH_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./+-]*\.(?:" + "|".join(EXT) + r"))`")
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
findings, resolved, skipped, generic = [], [], [], []
seen_ext=set()
for doc in DOCS:
    text=open(doc if os.path.isabs(doc) else os.path.join(ROOT,doc)).read()
    absent=set()
    for rx in ABSENT_SPANS:
        for m in rx.finditer(text):
            for p in PATH_RE.finditer(m.group(0)): absent.add(p.group(1))
    lines=text.split("\n")
    for ln,line in enumerate(lines):
        ctx=" ".join(lines[max(0,ln-1):ln+2])
        for m in PATH_RE.finditer(line):
            frag=m.group(1); seen_ext.add(frag.rsplit(".",1)[-1])
            if frag in absent: skipped.append((doc,frag)); continue
            if os.path.exists(os.path.join(ROOT,frag)): continue          # rung 1
            h=rung2(frag)
            if len(h)==1: resolved.append((doc,frag,"rung2",h[0])); continue
            if len(h)>1:
                if "/" not in frag:
                    generic.append((doc,frag,len(h)))   # class of artifact, not a locator
                else:
                    findings.append((doc,frag,f"COLLISION: {len(h)} local matches"))
                continue
            if rung3(frag): resolved.append((doc,frag,"rung3","runtime state")); continue
            if re.match(r"(feedback|reference|project)-[a-z0-9-]+\.md$", frag) and \
               os.path.exists(os.path.join(AUTOMEM, frag)):
                resolved.append((doc,frag,"rung5","claude auto-memory")); continue
            r4=rung4(frag,ctx)
            if r4 and r4[0]=="rung4": resolved.append((doc,frag,"rung4",r4[1])); continue
            if r4: findings.append((doc,frag,r4[1])); continue
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
print(f"\n### SKIPPED AS ASSERTED-ABSENT ({len(set(skipped))} unique)")
for d,f in sorted(set(skipped)): print(f"  {d:22s} {f}")
if not skipped: print("  (none)")
tree_ext={p.rsplit('.',1)[-1] for p in TREE if '.' in os.path.basename(p)}
drop=sorted(e for e in tree_ext if e not in EXT and len(e)<=12 and e.isalnum())
print(f"\n### EXTENSIONS IN TREE NOT IN WHITELIST (dropped by the extractor)\n  {', '.join(drop[:40])}")
