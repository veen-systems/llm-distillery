"""Evidence must rest on data that lives on situla, not on a GPU host.

Owner ruling 2026-10-10 (docs/decisions/2026-10-10-situla-single-source-of-truth.md): situla is the
single source of truth; b650-gpu, gpu-server and sadaltager are scratch, and so is sadalsuud outside
NexusMind's production tree. Before this check, six v8 evidence dirs named `b650-gpu:~/v8_corpus/`
as the durable home of their inputs -- one host wipe from evidence nobody could re-open.

Two checks:
1. Every docs/evidence/*/MANIFEST.json is non-empty, and (unless `--no-lab`) each entry exists under
   the lab root with its recorded size and sha256 (`--fast`: size only) AND agrees with the
   `_LAB_MANIFEST.json` of the pulled tree it sits in (same hash, same origin). Entries are written
   by `scripts/lab/lab.py cite`.
2. Every evidence unit (a dir, or a top-level file) that names a scratch host is covered:
   - a `host:path` citation (absolute, `~/`, `$HOME/`, relative, quoted, backticked, any case) needs
     a MANIFEST.json entry whose `origin` is that path, lies under it, lies above it, or matches it
     as a glob;
   - a bare mention of a PURE scratch host (one with no `--exempt` prefix, so not sadalsuud by
     default) -- `ssh [opts] <host>`, `on/from/at <host>`, `<host> only` -- needs a non-empty
     MANIFEST.json. Deliberately broad: a result produced on a GPU host belongs on situla before it
     is written up.
   An uncovered item FAILS unless it is listed in the committed baseline
   (scripts/verification/lab_manifest_baseline.json): the evidence that already cited hosts on
   2026-10-10, much of it host /tmp paths that are gone. Enforcement is per item, not per date, so a
   new citation added to an OLD dir fails too. ⛔ `--write-baseline` rewrites that file from the
   current state; a diff that ADDS baseline entries is a loosening and needs review as one.

A unit that names hosts without resting on host data (an inventory OF the hosts) declares it with a
line `lab-check: not-host-data: <reason>`; it is reported as EXEMPT with the reason, never silently
passed. A marker with no reason is a failure.

`--exempt host:prefix` marks production paths that are not scratch: the path (with a leading `~/`,
`$HOME/` or `/home/<user>/` removed) must equal the prefix or start with it plus `/`.
Default: sadalsuud `local_dev`.

Exit 0 = pass, 1 = fail. With no lab root on this machine the check FAILS rather than skipping
(`--no-lab` runs the lab-free parts, and says so) -- a check that passes where it cannot look is how
an unreachable mechanism ships.

⚠️ Known blind spots: prose that names no host ("the GPU box"); `/home/...` paths with no host;
experiments/registry.jsonl (not scanned); text files over 2 MB and binary files; a citation that
is a PUSH to a host (`scp x b650-gpu:~/dir/`) reads as a citation and needs a manifest or a
rephrase -- except a bare `host:~/`, which is skipped.
"""
import argparse, fnmatch, hashlib, json, os, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "evidence"
BASELINE = Path(__file__).resolve().parent / "lab_manifest_baseline.json"
DEFAULT_HOSTS = ["b650-gpu", "b650", "gpu-server", "sadalsuud", "sadaltager"]
DEFAULT_EXEMPT = ["sadalsuud:local_dev"]
MAX_BYTES = 2_000_000
OPT_OUT = re.compile(r"lab-check:\s*not-host-data:?(.*)")
LAB_MANIFEST = "_LAB_MANIFEST.json"
SSH_OPTS = r"(?:-[bcDEeFIiJLlmOopQRSWw]\s*\S+\s+|-\w+\s+)*"


def patterns(hosts):
    alts = "|".join(re.escape(h) for h in sorted(hosts, key=len, reverse=True))
    host = rf"(?<![\w.-])(?<!//)`?({alts})`?(?![\w.-])"
    cite = re.compile(host + r":`?['\"]?((?:~|\$\{?HOME\}?)?/?[\w.~/*{},$-]*)", re.IGNORECASE)
    bare = re.compile(rf"(?:\bssh\s+{SSH_OPTS}|\b(?:on|from|at)\s+)`?({alts})`?(?![\w.-])"
                      rf"|(?<![\w.-])`?({alts})`?\s+only\b", re.IGNORECASE)
    return cite, bare


def norm(path):
    p = path.strip("'\"`")
    p = re.sub(r"^(~/?|\$\{?HOME\}?/?|/home/[^/]+/?)", "", p)
    return p.rstrip("/")


def lab_root(flag=None):
    if flag:
        return Path(flag).expanduser()
    return Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unit_texts(unit):
    files = [unit] if unit.is_file() else sorted(f for f in unit.rglob("*") if f.is_file())
    for f in files:
        if f.name == "MANIFEST.json" or f.stat().st_size > MAX_BYTES:
            continue
        raw = f.read_bytes()
        if b"\0" in raw[:8192]:
            continue
        yield raw.decode("utf-8", errors="replace")


def exempted(host, path, exempt):
    return any(host == h and (path == pre or path.startswith(pre + "/")) for h, pre in exempt)


def scan(unit, cite, bare, exempt):
    """(set of (host, path) citations, set of hosts mentioned bare, opt-out reasons)."""
    mixed = {h for h, _ in exempt}          # hosts with production paths are not pure scratch
    cites, mentions, marks = set(), set(), []
    for text in unit_texts(unit):
        marks += [m.group(1).strip(" -:>") for m in OPT_OUT.finditer(text)]
        for m in cite.finditer(text):
            host, path = m.group(1).lower(), norm(m.group(2))
            if path and not exempted(host, path, exempt):
                cites.add((host, path))
        for m in bare.finditer(text):
            h = (m.group(1) or m.group(2)).lower()
            if h not in mixed:
                mentions.add(h)
    return cites, mentions, marks


def brace_to_glob(path):
    return re.sub(r"\{[^}]*\}", "*", path)


def covered(host, path, origins):
    is_glob = bool(re.search(r"[*?\[{]", path))
    glob = brace_to_glob(path)
    for o in origins:
        oh, _, op = o.partition(":")
        if oh.lower() != host:
            continue
        op = norm(op)
        if op == path or op.startswith(path + "/") or path.startswith(op + "/"):
            return True
        if is_glob and (fnmatch.fnmatchcase(op, glob) or fnmatch.fnmatchcase(op, glob + "/*")):
            return True
    return False


def check_lab_entries(mf, entries, root, fast, fails):
    for e in entries:
        p = root / e["path"]
        if not p.is_file():
            fails.append(f"{mf.parent.name}: {e['path']} missing from {root}")
            continue
        if p.stat().st_size != e["size"] or (not fast and sha256_file(p) != e["sha256"]):
            fails.append(f"{mf.parent.name}: {e['path']} changed since it was cited")
            continue
        tree = next((a for a in p.parents if a != root and a.is_relative_to(root)
                     and (a / LAB_MANIFEST).is_file()), None)
        if tree is None:
            fails.append(f"{mf.parent.name}: {e['path']} is not inside a pulled tree")
            continue
        lm = json.loads((tree / LAB_MANIFEST).read_text(encoding="utf-8"))
        inner = p.relative_to(tree).as_posix()
        rec = lm["files"].get(inner)
        origin = lm["origin"].rstrip("/")
        want = origin if lm.get("kind") == "file" else f"{origin}/{inner}"
        if rec is None or rec["sha256"] != e["sha256"] or e["origin"] != want:
            fails.append(f"{mf.parent.name}: {e['path']} disagrees with its pulled tree's manifest "
                         f"(hash or origin; expected origin {want})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="compare sizes, not sha256")
    ap.add_argument("--no-lab", action="store_true", help="skip the lab-side half of check 1")
    ap.add_argument("--evidence", type=Path, default=EVIDENCE)
    ap.add_argument("--baseline", type=Path, default=BASELINE)
    ap.add_argument("--write-baseline", action="store_true",
                    help="rewrite the baseline from the current state (a loosening: review the diff)")
    ap.add_argument("--lab-root", help="lab root (default $LD_LAB, else ~/ld-lab)")
    ap.add_argument("--hosts", nargs="+", default=DEFAULT_HOSTS, help="scratch host names")
    ap.add_argument("--exempt", nargs="*", default=DEFAULT_EXEMPT, metavar="HOST:PREFIX",
                    help="production paths that are not scratch (default %(default)s)")
    a = ap.parse_args()
    cite, bare = patterns(a.hosts)
    exempt = [(h.lower(), norm(pre)) for h, _, pre in (e.partition(":") for e in a.exempt)]
    fails, backlog, opted, current = [], [], [], {}
    root = lab_root(a.lab_root)
    if not a.no_lab and not root.is_dir():
        print(f"FAIL: lab root {root} does not exist (run on situla, or pass --no-lab)")
        return 1
    n_entries = 0
    for mf in sorted(a.evidence.glob("*/MANIFEST.json")):
        entries = json.loads(mf.read_text(encoding="utf-8")).get("entries", [])
        if not entries:
            fails.append(f"{mf.parent.name}: MANIFEST.json has no entries")
        if not a.no_lab:
            n_entries += len(entries)
            check_lab_entries(mf, entries, root.resolve(), a.fast, fails)
    baseline = json.loads(a.baseline.read_text(encoding="utf-8")) if a.baseline.is_file() else {}
    for unit in sorted(a.evidence.iterdir()):
        cites, mentions, marks = scan(unit, cite, bare, exempt)
        if not cites and not mentions:
            continue
        if marks:
            reason = next((r for r in marks if r), "")
            if reason:
                opted.append(f"{unit.name}: {reason}")
            else:
                fails.append(f"{unit.name}: `lab-check: not-host-data` marker with no reason")
            continue
        mf = unit / "MANIFEST.json" if unit.is_dir() else None
        entries = json.loads(mf.read_text(encoding="utf-8")).get("entries", []) if mf and mf.is_file() else []
        origins = [e["origin"] for e in entries]
        items = sorted(f"{h}:{p}" for h, p in cites if not covered(h, p, origins))
        if not entries:
            items += sorted(f"mention:{h}" for h in mentions)
        if not items:
            continue
        current[unit.name] = items
        known = set(baseline.get(unit.name, []))
        new = [i for i in items if i not in known]
        tail = "" if unit.is_dir() else " (a top-level file cannot carry a manifest: make it a dir)"
        if new:
            fails.append(f"{unit.name}: {', '.join(new[:4])}{' …' if len(new) > 4 else ''} not covered "
                         f"by a MANIFEST.json entry{tail}")
        else:
            backlog.append(f"{unit.name}: {len(items)} item(s), all in the baseline")
    if a.write_baseline:
        a.baseline.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {a.baseline}: {len(current)} units, {sum(map(len, current.values()))} items")
        return 0
    stale = sum(1 for u, its in baseline.items() for i in its if i not in current.get(u, []))
    print(f"manifest entries checked {n_entries}{' (SKIPPED: --no-lab)' if a.no_lab else ''}; "
          f"failures {len(fails)}; backlog units {len(backlog)}; declared exempt {len(opted)}; "
          f"baseline items now covered or gone {stale}")
    for f in fails:
        print("FAIL", f)
    for o in opted:
        print("EXEMPT", o)
    for b in backlog:
        print("BACKLOG", b)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
