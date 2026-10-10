"""situla is the single source of truth for experiment data; GPU hosts are scratch.

Owner ruling 2026-10-10 (docs/decisions/2026-10-10-situla-single-source-of-truth.md): bring data
and code TO a host, run, pull the results BACK to situla, verify, and only then is the host copy
disposable. This tool is the "pull back and verify" half, so that the verification is a byte
comparison and not somebody's recollection that the copy finished.

    python3 scripts/lab/lab.py pull b650-gpu:~/v8_corpus inbox/b650-gpu/2026-10-10/v8_corpus
    python3 scripts/lab/lab.py verify inbox/b650-gpu/2026-10-10/v8_corpus
    python3 scripts/lab/lab.py cite docs/evidence/<dir> inbox/b650-gpu/2026-10-10/v8_corpus/pool_v2.jsonl

Lab root: --lab-root, else $LD_LAB, else ~/ld-lab (inside $HOME, so situla's restic backup covers it).

`pull host:path dest`: dest (relative to the lab root) is always a NEW directory; a file source
lands at dest/<its name>. Refuses if dest exists, so a verified, possibly cited copy is never
overwritten (pull to a new dest instead). After rsync it lists every file AND symlink on BOTH sides
and exits 1 unless they are identical: (path, sha256) for files, (path, target) for links.
A symlink that dangles, is absolute, or points outside the pulled tree fails the pull: its data
would not be in the copy, and the copy would still look complete. `--allow-external-links`
records such links and warns instead. The record is dest/_LAB_MANIFEST.json.

`adopt host:path dest`: for a tree that is ALREADY on situla (copied before this tool, or by
another tool): never copies; lists both sides and writes the manifest only if they are identical.
dest must exist and must not carry a manifest yet. Same link rules as `pull`.

`--replace-manifest` re-lists a tree that already has one (e.g. written by an older version of
this tool) and replaces it only if host and copy are identical.

dest must resolve inside the lab root and not inside another pulled tree. If rsync fails, the
partial dest is left for inspection and the message says how to recover.

`verify dest` re-checks a pulled tree against its manifest. `cite <evidence dir> <lab paths>`
writes the evidence dir's MANIFEST.json (path, sha256, size, origin, pulled_at) and refuses a
file outside the lab root, one not recorded by `pull`/`adopt`, or one changed since. Checked by
scripts/verification/check_lab_manifests.py. ⛔ Never move or rename a pulled tree after citing
from it: MANIFEST.json records the lab path.

⛔ This tool never deletes anything on a host. Host deletion is per item, with the owner's go.
"""
import argparse, datetime, fnmatch, hashlib, json, os, posixpath, shlex, stat, subprocess, sys
from pathlib import Path

LAB_MANIFEST = "_LAB_MANIFEST.json"
EVIDENCE_MANIFEST = "MANIFEST.json"
# Excluded on BOTH sides (rsync --exclude and the remote find -prune). A lab manifest inside a
# source tree is excluded too: inputs sent from the lab to a host carry one (flow step 1).
EXCLUDES = ["__pycache__", "*.pyc", "venv", "venv-*", ".venv", ".git", LAB_MANIFEST]
LAB_ROOT_FLAG = None


def lab_root():
    if LAB_ROOT_FLAG:
        return Path(LAB_ROOT_FLAG).expanduser()
    return Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def excluded(name):
    return any(fnmatch.fnmatch(name, e) for e in EXCLUDES)


def link_problem(rel, target):
    """None if a symlink at `rel` (tree-relative) with `target` stays inside the tree."""
    if target.startswith("/"):
        return "absolute target"
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
    if joined == ".." or joined.startswith("../"):
        return "points outside the pulled tree"
    return None


def local_listing(root):
    """({relpath: (sha256, size)}, {relpath: target}) under root, excludes applied (which also
    skips the tree's own manifest)."""
    root = Path(root)
    files, links = {}, {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = Path(dirpath).relative_to(root)
        keep = []
        for d in dirnames:
            full = Path(dirpath) / d
            if excluded(d):
                continue
            if full.is_symlink():
                links[(rel_dir / d).as_posix()] = os.readlink(full)
                continue
            keep.append(d)
        dirnames[:] = keep
        for f in filenames:
            if excluded(f):
                continue
            full = Path(dirpath) / f
            rel = (rel_dir / f).as_posix()
            if full.is_symlink():
                links[rel] = os.readlink(full)
            elif stat.S_ISREG(full.lstat().st_mode):
                files[rel] = (sha256_file(full), full.stat().st_size)
            else:                                    # FIFO, socket, device: opening one can hang
                files[rel] = ("special-file", 0)     # never equal to a remote hash, so it FAILs
    return files, links


def remote_listing(host, path):
    """Same shape as local_listing, computed ON the host, plus the root's kind ('F' or 'D')
    and the links that do not resolve there. Every FIELD is NUL-terminated so any name or
    link target survives (tabs, newlines); the hash is read from stdin so sha256sum never
    escapes a name. Run under bash explicitly: the script uses `read -d ""`."""
    prune = " -o ".join(f"-name {shlex.quote(e)}" for e in EXCLUDES)
    script = (
        "set -e; p=" + shlex.quote(path) + "; "
        'case $p in "~") p=$HOME;; "~/"*) p=$HOME/${p#"~/"};; /*) ;; *) p=$HOME/$p;; esac; '
        'rec() { f=$1; r=$2; '
        '  if [ -L "$f" ]; then e=0; [ -e "$f" ] && e=1; printf "L\\0%s\\0%s\\0%s\\0" "$r" "$e" "$(readlink -- "$f")"; '
        '  else h=$(sha256sum < "$f"); printf "F\\0%s\\0%s\\0%s\\0" "$r" "$(stat -c %s -- "$f")" "${h%% *}"; fi; }; '
        'if [ -f "$p" ] && [ ! -L "$p" ]; then printf "T\\0F\\0"; cd -- "$(dirname -- "$p")"; b=$(basename -- "$p"); rec "./$b" "$b"; '
        'elif [ -d "$p" ] && [ ! -L "$p" ]; then printf "T\\0D\\0"; cd -- "$p"; '
        f"  find . -mindepth 1 \\( {prune} \\) -prune -o \\( -type f -o -type l \\) -print0 | "
        '  while IFS= read -r -d "" f; do rec "$f" "${f#./}"; done; '
        'elif [ -L "$p" ]; then echo "the source itself is a symlink: $p -> $(readlink "$p"); pull its target" >&2; exit 3; '
        'else echo "no such file or directory: $p" >&2; exit 3; fi')
    r = subprocess.run(["ssh", "-n", host, "bash -c " + shlex.quote(script)],
                       capture_output=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        sys.exit(f"remote listing failed on {host}:{path}: {r.stderr.decode(errors='replace').strip()}")
    kind, files, links, dangling = None, {}, {}, set()
    fields = r.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    i = 0
    while i < len(fields) and fields[i]:
        tag = fields[i]
        if tag == "T":
            kind = fields[i + 1]; i += 2
        elif tag == "F":
            path_, size, digest = fields[i + 1:i + 4]; i += 4
            files[path_] = (digest, int(size))
        elif tag == "L":
            path_, exists, target = fields[i + 1:i + 4]; i += 4
            links[path_] = target
            if exists != "1":
                dangling.add(path_)
        else:
            sys.exit(f"unparseable remote listing from {host}:{path} near field {i}: {tag!r}")
    if kind is None:
        sys.exit(f"remote listing of {host}:{path} returned no header; refusing")
    return kind, files, links, dangling


def write_lab_manifest(dest, origin, kind, files, links, link_warnings, verb):
    manifest = {
        "origin": origin,
        "kind": "file" if kind == "F" else "dir",
        "pulled_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "pulled_by": f"scripts/lab/lab.py {verb}",
        "n_files": len(files),
        "bytes": sum(s for _, s in files.values()),
        "files": {k: {"sha256": d, "size": s} for k, (d, s) in sorted(files.items())},
        "links": dict(sorted(links.items())),
        "link_warnings": link_warnings,
    }
    (dest / LAB_MANIFEST).write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")  # ensure_ascii: odd names survive
    return dest / LAB_MANIFEST


def compare(want_files, want_links, have_files, have_links):
    missing = sorted(set(want_files) - set(have_files)) + sorted(set(want_links) - set(have_links))
    extra = sorted(set(have_files) - set(want_files)) + sorted(set(have_links) - set(want_links))
    differ = sorted(k for k in set(want_files) & set(have_files) if want_files[k][0] != have_files[k][0])
    differ += sorted(k for k in set(want_links) & set(have_links) if want_links[k] != have_links[k])
    return missing, extra, differ


def checked_remote(a, host, path):
    """The remote listing, refused when empty or when a link's data would not be in the copy."""
    kind, r_files, r_links, dangling = remote_listing(host, path)
    if not r_files and not r_links:
        sys.exit(f"REFUSED: {a.source} holds no files after excludes; nothing to pull")
    problems = [f"{k} -> {t}: dangling on the host" if k in dangling else f"{k} -> {t}: {p}"
                for k, t in sorted(r_links.items())
                for p in [link_problem(k, t)] if k in dangling or p]
    if problems and not a.allow_external_links:
        print(f"REFUSED {a.source}: {len(problems)} symlink(s) whose data would not be in the copy:")
        for p in problems[:20]:
            print("  ", p)
        print("   (pull the targets separately, or pass --allow-external-links to record them)")
        sys.exit(1)
    return kind, r_files, r_links, problems


def finish(a, dest, kind, r_files, r_links, problems, verb):
    l_files, l_links = local_listing(dest)
    missing, extra, differ = compare(r_files, r_links, l_files, l_links)
    if missing or extra or differ:
        print(f"FAIL {a.source} -> {dest}: missing {len(missing)}, extra {len(extra)}, differ {len(differ)}"
              f" (no manifest written; the local copy stays for inspection)")
        for k in (missing + extra + differ)[:20]:
            print("  ", k)
        sys.exit(1)
    m = write_lab_manifest(dest, a.source, kind, l_files, l_links, problems, verb)
    done = "pulled" if verb == "pull" else "adopted"
    print(f"OK {done} {a.source} -> {dest}: {len(l_files)} files, {len(l_links)} links, "
          f"{sum(s for _, s in l_files.values()):,} bytes, identical on both sides; manifest {m}")
    for p in problems:
        print("   WARNING (recorded, target NOT pulled):", p)


def split_source(source):
    host, _, path = source.partition(":")
    if not host or not path:
        sys.exit("source must be host:path")
    return host, path


def lab_dest(rel):
    """dest resolved inside the lab root, not inside (or equal to) another pulled tree."""
    root = lab_root().resolve()
    dest = (root / rel).resolve()
    if not dest.is_relative_to(root) or dest == root:
        sys.exit(f"REFUSED: {rel} resolves outside the lab root {root}")
    for anc in dest.parents:
        if anc.is_relative_to(root) and anc != root and (anc / LAB_MANIFEST).exists():
            sys.exit(f"REFUSED: {rel} is inside the pulled tree {anc}; pick a dest outside it")
    return dest


def cmd_pull(a):
    host, path = split_source(a.source)
    dest = lab_dest(a.dest)
    if dest.exists() or dest.is_symlink():
        sys.exit(f"REFUSED: {dest} exists. A pulled tree is never overwritten; pull to a new dest "
                 f"(e.g. add a suffix), or `adopt` a copy made by other means.")
    kind, r_files, r_links, problems = checked_remote(a, host, path)
    dest.mkdir(parents=True)
    rpath = path.rstrip("/") if kind == "F" else path.rstrip("/") + "/"
    if rpath.startswith("~/"):
        rpath = rpath[2:]
    cmd = (["rsync", "-a", "--partial"] + [f"--exclude={e}" for e in EXCLUDES]
           + [f"{host}:{rpath}", str(dest) + "/"])
    rc = subprocess.run(cmd, stdin=subprocess.DEVNULL).returncode  # ssh/rsync must not eat a caller's stdin loop
    if rc != 0:
        sys.exit(f"FAIL rsync exited {rc}; {dest} holds a PARTIAL copy and no manifest. Inspect it, then either "
                 f"remove it (rm -rf) and pull again, or finish the copy by hand and run `adopt`.")
    finish(a, dest, kind, r_files, r_links, problems, "pull")


def cmd_adopt(a):
    host, path = split_source(a.source)
    root = lab_root().resolve()
    dest = (root / a.dest).resolve()
    if not dest.is_relative_to(root) or dest == root:
        sys.exit(f"REFUSED: {a.dest} resolves outside the lab root {root}")
    if not dest.is_dir() or (root / a.dest).is_symlink():
        sys.exit(f"REFUSED: {dest} is not an existing directory (a single file must sit inside one)")
    if (dest / LAB_MANIFEST).exists() and not a.replace_manifest:
        sys.exit(f"REFUSED: {dest} already has a manifest; use `verify`, or --replace-manifest to re-list it")
    hidden = [p for p in dest.rglob("*") if excluded(p.name) and p.name != LAB_MANIFEST or
              p.name == LAB_MANIFEST and p.parent != dest]
    if hidden:
        sys.exit(f"REFUSED: {dest} holds {len(hidden)} excluded entries the comparison would not see "
                 f"(first: {hidden[0].relative_to(dest)}); remove them first")
    kind, r_files, r_links, problems = checked_remote(a, host, path)
    finish(a, dest, kind, r_files, r_links, problems, "adopt")


def cmd_verify(a):
    dest = lab_root() / a.dest
    mf = dest / LAB_MANIFEST
    if not mf.is_file():
        sys.exit(f"no {LAB_MANIFEST} in {dest}")
    m = json.loads(mf.read_text(encoding="utf-8"))
    l_files, l_links = local_listing(dest)
    m_files = {k: (v["sha256"], v["size"]) for k, v in m["files"].items()}
    missing, extra, differ = compare(m_files, m.get("links", {}), l_files, l_links)
    bad = missing + extra + differ
    print(f"{'OK' if not bad else 'FAIL'} {dest}: {len(m_files)} files + {len(m.get('links', {}))} links "
          f"in manifest; {len(missing)} missing, {len(differ)} changed, {len(extra)} not in manifest")
    for k in bad[:20]:
        print("  ", k)
    sys.exit(1 if bad else 0)


def cmd_cite(a):
    """Record, in an evidence dir, which lab files it rests on. Origin comes from the lab
    manifest, so a file that was never pulled through `pull` cannot be cited."""
    ev = Path(a.evidence_dir)
    if not ev.is_dir():
        sys.exit(f"no such evidence dir: {ev}")
    root = lab_root().resolve()
    path = ev / EVIDENCE_MANIFEST
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "lab_root": "$LD_LAB (default ~/ld-lab, on situla)", "entries": []}
    by_path = {e["path"]: e for e in doc["entries"]}
    for given in a.lab_paths:
        full = (root / given).resolve()
        if not full.is_relative_to(root) or full == root:
            sys.exit(f"{given}: outside the lab root {root}")
        if not full.is_file():
            sys.exit(f"not a file under the lab root: {full}")
        rel = full.relative_to(root).as_posix()
        tree = next((anc for anc in full.parents if anc != root and anc.is_relative_to(root)
                     and (anc / LAB_MANIFEST).is_file()), None)
        if tree is None:
            sys.exit(f"{rel}: no {LAB_MANIFEST} above it -- pull it with `lab.py pull` first")
        inner = full.relative_to(tree).as_posix()
        lm = json.loads((tree / LAB_MANIFEST).read_text(encoding="utf-8"))
        rec = lm["files"].get(inner)
        if rec is None or sha256_file(full) != rec["sha256"]:
            sys.exit(f"{rel}: not in its lab manifest, or changed since the pull")
        origin = lm["origin"].rstrip("/")
        if lm.get("kind") != "file":                 # a single-file pull's origin already names the file
            origin = f"{origin}/{inner}"
        by_path[rel] = {"path": rel, "sha256": rec["sha256"], "size": rec["size"],
                        "origin": origin, "pulled_at": lm["pulled_at"]}
    doc["entries"] = sorted(by_path.values(), key=lambda e: e["path"])
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{path}: {len(doc['entries'])} entries")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lab-root", help="lab root (default $LD_LAB, else ~/ld-lab)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull"); p.add_argument("source"); p.add_argument("dest")
    p.add_argument("--allow-external-links", action="store_true",
                   help="record dangling/absolute/outside symlinks and warn instead of refusing")
    p.set_defaults(f=cmd_pull)
    p = sub.add_parser("adopt"); p.add_argument("source"); p.add_argument("dest")
    p.add_argument("--allow-external-links", action="store_true", help="as for pull")
    p.add_argument("--replace-manifest", action="store_true",
                   help="re-list a tree that already has a manifest (e.g. an older format)")
    p.set_defaults(f=cmd_adopt)
    p = sub.add_parser("verify"); p.add_argument("dest"); p.set_defaults(f=cmd_verify)
    p = sub.add_parser("cite"); p.add_argument("evidence_dir"); p.add_argument("lab_paths", nargs="+")
    p.set_defaults(f=cmd_cite)
    a = ap.parse_args()
    global LAB_ROOT_FLAG
    LAB_ROOT_FLAG = a.lab_root
    a.f(a)


if __name__ == "__main__":
    main()
