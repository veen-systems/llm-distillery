"""Move line ranges of a memory file VERBATIM to memory/archive/<stem>-archive.md, replace each with hook lines.
spec json: {"file": "...", "title": "...", "intro": [...], "moves": [[a, b, ctx_heading_or_null, [hook lines]]]}
Then: lossless check (C-locale set of old lines ⊆ new ∪ archive) and a mutant (drop the longest unique
archived line → must report exactly 1 missing)."""
import json, sys, os, collections
spec = json.load(open(sys.argv[1])); p = spec["file"]; stem = os.path.basename(p)[:-3]
A = f"archive/{stem}-archive.md"; ap = os.path.join(os.path.dirname(p), A)
old = open(p).read(); L = old.split("\n")
prior = open(ap).read() if os.path.exists(ap) else None
arch = [f"# {spec['title']} — archive of closed entries", "",
        f"*Moved VERBATIM from `memory/{stem}.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under",
        "the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open",
        "entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading."]
arch += spec.get("intro", []); arch[-1] += "*"; arch.append("")
out, i, prev = [], 1, 0
for a, b, ctx, hook in spec["moves"]:
    assert a > prev and b >= a, (a, b); prev = b
    if ctx: arch += [ctx + "  *(context heading, repeated)*", ""]
    arch += L[a-1:b]
    out += L[i-1:a-1] + [h.replace("{A}", f"[`{A}`]({A})") for h in hook]
    i = b + 1
out += L[i-1:]
if prior is not None:
    body = arch[arch.index("") + 1:]          # drop the first-time title line
    body = body[next(k for k, l in enumerate(body) if l.endswith("*")) + 2:]   # and the first-time intro
    arch = ["", "---", "", f"## Moved 2026-10-12 — {spec['title']} (`docs/TODO.md` item {spec.get('item', '2b')}, #163 the read surface)", ""] + spec.get("intro", []) + [""] + body
new = "\n".join(out); open(p, "w").write(new)
open(ap, "w").write((prior.rstrip("\n") + "\n" if prior is not None else "") + "\n".join(arch) + "\n")
def missing(n, a):
    have = set(n.split("\n")) | set(a.split("\n"))
    return sorted(set(L) - have)
arch_txt = open(ap).read()
m = missing(new, arch_txt); print("missing:", len(m)); assert not m
cnt = collections.Counter(new.split("\n") + arch_txt.split("\n"))
uniq = max((l for l in arch_txt.split("\n") if cnt[l] == 1 and l in set(L)), key=len)
mut = "\n".join(l for l in arch_txt.split("\n") if l != uniq)
print("mutant:", len(missing(new, mut)))
print(f"{len(old)} -> {len(new)} chars; archive {len(arch_txt)}")
