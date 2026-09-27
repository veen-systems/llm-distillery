#!/usr/bin/env python3
"""ADR-024 order step 3: deploy the packaged detectors by MANIFEST.json (fetch → verify → place → prune).

    # Before anything is copied (deploy_to_nexusmind.sh step 0.7): fetch + verify into a staging dir.
    python scripts/deployment/deploy_detectors.py stage --staging DIR [--package harm_detector/v1 ...]
    # deploy_to_nexusmind.sh step 2: place the staged packages, prune, re-verify the target.
    python scripts/deployment/deploy_detectors.py place --staging DIR --target NEXUSMIND/filters/common [--plan]

`stage` REFUSES, before anything reaches NexusMind:
  - a MANIFEST.json that is not in HEAD or differs from it (the commit is the manifest's trust root);
  - a `.nexusmind-owns` entry inside a packaged detector (step 2a would overwrite it silently);
  - a manifest with `origin: "hub"` files and `hub: null` (nothing to fetch but a guess);
  - a `git` file that is not committed here as-is, and any file whose bytes differ from the manifest;
  - a `.sha256` sidecar whose digest is not its pickle's manifest digest, or whose pickle is not listed.
Hub files are fetched at the PINNED revision; the local working-tree pickles are never read.

`place` copies every listed file, deletes exactly the files the PREVIOUS manifest in the target listed and the
new one does not, then (only if all of that succeeded) writes MANIFEST.json and re-hashes the target against it.
Neither a write nor a delete follows a symlink out of the package dir.
No readable previous manifest for the same detector/version = no prune: it reports the files outside the
package instead and never infers what to delete. `--plan` prints the same actions and writes nothing.
Exit: 0 ok; 1 a refusal, an unknown --package, or a failed post-check; 2 an argparse usage error.
A Hub or network failure is not caught: it exits 1 with a traceback, before step 1.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.deployment.detector_manifest import COMMON, MANIFEST, PACKAGES, REPO, _hash_file, verify  # noqa: E402


class Refused(Exception):
    """A package that must not ship. Raised before the target is touched."""


def _safe_rel(rel: str) -> PurePosixPath:
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or not p.parts or rel != p.as_posix():
        raise Refused(f"unsafe path in manifest: {rel!r}")
    return p


def _committed(git_root: Path, path: Path) -> str | None:
    """None when `path` is in HEAD and neither the index nor the working tree differs from it; else why not.
    `git ls-files` is NOT this test: it passes a file that is only staged (review 2026-09-27, three lenses)."""
    rel = path.resolve().relative_to(git_root.resolve()).as_posix()
    g = ["git", "-C", str(git_root)]
    if subprocess.run(g + ["cat-file", "-e", f"HEAD:{rel}"], capture_output=True).returncode != 0:
        return "not in HEAD"
    if subprocess.run(g + ["diff", "--quiet", "HEAD", "--", rel], capture_output=True).returncode != 0:
        return "modified since HEAD"
    return None


def check_owns(owns_file: Path) -> None:
    """A packaged detector's files are decided by its manifest; `.nexusmind-owns` cannot also claim them
    (step 2a does not consult it, so an entry there would be overwritten silently)."""
    if not owns_file.is_file():
        return
    for raw in owns_file.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        for pkg in PACKAGES:
            if line.startswith(f"filters/common/{pkg}/"):
                raise Refused(f".nexusmind-owns names {line}, inside packaged detector {pkg}: "
                              f"its files ship by MANIFEST.json only")


def _hub_fetcher(token: str | None):
    def fetch(repo_id: str, path_in_repo: str, revision: str) -> Path:
        from huggingface_hub import hf_hub_download
        return Path(hf_hub_download(repo_id, path_in_repo, revision=revision, token=token))
    return fetch


def stage(package: str, staging: Path, fetch, common: Path = COMMON, git_root: Path | None = REPO) -> dict:
    """Fetch and verify one package into staging/<package>/. Returns the manifest. Raises Refused."""
    src = common / package
    mpath = src / MANIFEST
    if not mpath.is_file():
        raise Refused(f"{package}: no {MANIFEST}: a packaged detector never falls back to the working-tree copy")
    if git_root is not None and (why := _committed(git_root, mpath)):
        raise Refused(f"{package}: {MANIFEST} is {why}: commit it first")
    m = json.loads(mpath.read_text(encoding="utf-8"))
    if f"{m.get('detector')}/{m.get('version')}" != package:
        raise Refused(f"{package}: manifest names {m.get('detector')}/{m.get('version')}")
    files = m["files"]
    hub_files = [f for f in files if f["origin"] == "hub"]
    if hub_files and not (m.get("hub") or {}).get("revision"):
        raise Refused(f"{package}: {len(hub_files)} hub-origin file(s) but `hub` is not pinned")
    digests = {f["path"]: f["sha256"] for f in files}
    out = staging / package
    for f in files:
        rel = _safe_rel(f["path"])
        if f["origin"] == "hub":
            hub = m["hub"]
            got = fetch(hub["repo_id"], f"{hub['path_prefix']}/{rel.as_posix()}", hub["revision"])
        elif f["origin"] == "git":
            got = src / rel
            if not got.is_file():
                raise Refused(f"{package}: {rel} is missing here")
            if git_root is not None and (why := _committed(git_root, got)):
                raise Refused(f"{package}: {rel} is {why}: a git-origin file must be committed")
        else:
            raise Refused(f"{package}: {rel}: unknown origin {f['origin']!r}")
        if _hash_file(got) != (f["sha256"], f["bytes"]):
            raise Refused(f"{package}: {rel} ({f['origin']}) does not match the manifest: "
                          f"{_hash_file(got)[0][:12]} != {f['sha256'][:12]}")
        if rel.name.endswith(".sha256"):
            target = rel.as_posix()[: -len(".sha256")]
            said = got.read_text(encoding="utf-8").split()
            if target not in digests or not said or said[0] != digests[target]:
                raise Refused(f"{package}: sidecar {rel} does not carry the manifest digest of {target}"
                              f"{'' if target in digests else ' (which the manifest does not list)'}")
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(got, dest)
    shutil.copyfile(mpath, out / MANIFEST)
    return m


def _previous(target_pkg: Path, package: str) -> dict | None:
    """The target's manifest for THIS detector/version, or None (absent, unreadable, or another package's)."""
    try:
        prev = json.loads((target_pkg / MANIFEST).read_text(encoding="utf-8"))
        if f"{prev['detector']}/{prev['version']}" != package:
            return None
        files = prev.get("files")
        ok = isinstance(files, list) and all(isinstance(f, dict) and isinstance(f.get("path"), str) for f in files)
        return prev if ok else None   # a malformed entry makes the whole manifest unusable as a prune basis
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def _inside(root: Path, p: Path) -> bool:
    """`p` resolves under `root`: a symlinked directory in the target must not carry a write or a delete out."""
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def place(package: str, staging: Path, target_common: Path, plan: bool = False) -> dict:
    """Place one staged package. Returns {written, same, pruned, extra, prune_basis, errors}."""
    staged = staging / package
    m = json.loads((staged / MANIFEST).read_text(encoding="utf-8"))
    tpkg = target_common / package
    listed = [f["path"] for f in m["files"]]
    prev = _previous(tpkg, package)
    res = {"written": [], "same": [], "pruned": [], "extra": [], "prune_basis": "previous manifest" if prev
           else "none (no readable previous manifest): nothing pruned", "errors": []}
    for f in m["files"]:
        dest = tpkg / _safe_rel(f["path"])
        if not _inside(tpkg, dest):
            res["errors"].append(f"{f['path']} resolves outside {tpkg} (symlink): not written")
            continue
        if dest.is_file() and _hash_file(dest) == (f["sha256"], f["bytes"]):
            res["same"].append(f["path"])
            continue
        res["written"].append(f["path"])
        if not plan:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".deploy-tmp")
            shutil.copyfile(staged / f["path"], tmp)
            os.replace(tmp, dest)
    if prev:
        for rel in sorted({f["path"] for f in prev["files"]} - set(listed)):
            try:
                p = tpkg / _safe_rel(rel)
            except Refused as e:
                res["errors"].append(str(e))
                continue
            if rel == MANIFEST or not p.is_file():
                continue
            if not _inside(tpkg, p):
                res["errors"].append(f"prune {rel}: resolves outside {tpkg} (symlink): not deleted")
                continue
            res["pruned"].append(rel)
            if not plan:
                try:
                    p.unlink()
                except OSError as e:
                    res["errors"].append(f"prune {rel}: {e}")
    res["manifest"] = "unchanged" if (tpkg / MANIFEST).is_file() and \
        (tpkg / MANIFEST).read_bytes() == (staged / MANIFEST).read_bytes() else "write"
    # The manifest goes in LAST and only when everything before it succeeded: while the old one stays, a re-run
    # still prunes against it, so a failed copy or prune is retried rather than forgotten.
    if not plan and not res["errors"]:
        tpkg.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staged / MANIFEST, tpkg / MANIFEST)
    if tpkg.is_dir():
        present = {p.relative_to(tpkg).as_posix() for p in tpkg.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts}
        res["extra"] = sorted(present - set(listed) - set(res["pruned"]) - {MANIFEST})
    if not plan and not res["errors"]:   # prove the outcome, not the copy: re-hash what is now in the target
        tree = {p.relative_to(tpkg).as_posix(): _hash_file(p) for p in tpkg.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts}
        check = verify(m, tree)
        if tree.get(MANIFEST) != _hash_file(staged / MANIFEST):
            check["mismatch"].append(f"{MANIFEST}: not the staged manifest")
        res["errors"] += [f"MISSING {x}" for x in check["missing"]] + [f"MISMATCH {x}" for x in check["mismatch"]]
    return res


def _packages(requested: list[str] | None) -> list[str]:
    for p in requested or []:
        if p not in PACKAGES:
            raise SystemExit(f"ERROR: not a packaged detector: {p} (packages: {', '.join(sorted(PACKAGES))})")
    return sorted(requested or PACKAGES)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage"); s.add_argument("--staging", required=True, type=Path)
    s.add_argument("--package", action="append")
    pl = sub.add_parser("place"); pl.add_argument("--staging", required=True, type=Path)
    pl.add_argument("--target", required=True, type=Path, help="NexusMind's filters/common")
    pl.add_argument("--package", action="append"); pl.add_argument("--plan", action="store_true")
    a = ap.parse_args(argv)
    pkgs = _packages(a.package)
    if a.cmd == "stage":
        from scripts.deployment.upload_detector_to_hub import _token
        try:
            token = _token()
        except RuntimeError:   # the pinned revisions may be in the HF cache; a private-repo miss still fails loudly
            token = None
            print("   WARNING: no HF token; fetching anonymously (works only from the HF cache)", file=sys.stderr)
        fetch = _hub_fetcher(token)
        try:
            check_owns(REPO / ".nexusmind-owns")
            for p in pkgs:
                m = stage(p, a.staging, fetch)
                hub = m.get("hub") or {}
                print(f"   STAGED {p}: {len(m['files'])} file(s) verified against {MANIFEST}"
                      f" (hub {hub.get('repo_id')}@{str(hub.get('revision'))[:12]})")
        except Refused as e:
            print(f"ERROR: REFUSED {e}", file=sys.stderr)
            return 1
        return 0
    if not a.target.is_dir():
        print(f"ERROR: target is not a directory: {a.target}", file=sys.stderr)
        return 1
    failed = False
    for p in pkgs:
        r = place(p, a.staging, a.target, plan=a.plan)
        verb = "WOULD" if a.plan else ""
        print(f"   {p}: {verb + ' ' if verb else ''}write {len(r['written'])}, unchanged {len(r['same'])}, "
              f"{verb + ' ' if verb else ''}prune {len(r['pruned'])}, {MANIFEST} {r['manifest']} "
              f"(prune basis: {r['prune_basis']})")
        for x in r["written"]:
            print(f"      write  {x}")
        for x in r["pruned"]:
            print(f"      prune  {x}")
        if r["extra"]:
            print(f"      outside the package, left in place: {', '.join(r['extra'])}")
        for e in r["errors"]:
            print(f"      ERROR {e}", file=sys.stderr)
        failed |= bool(r["errors"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
