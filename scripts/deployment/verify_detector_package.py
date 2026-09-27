#!/usr/bin/env python3
"""Detector packages (ADR-024, llm-distillery#165): write a MANIFEST.json, or verify a tree against one.

    # Backfill a manifest from the bytes production serves (read-only over ssh):
    python scripts/deployment/verify_detector_package.py write harm_detector/v1 --source sadalsuud:~/local_dev/NexusMind

    # Check any tree against the committed manifest (REPORTING mode: exit 0 unless --strict):
    python scripts/deployment/verify_detector_package.py verify harm_detector/v1 --target sadalsuud:~/local_dev/NexusMind
    python scripts/deployment/verify_detector_package.py verify --all --target ../NexusMind --strict

`write` puts `filters/common/<detector>/<version>/MANIFEST.json` in THIS repo. `verify` reports
missing / mismatching files (errors) and files outside the package (`extra`, informational until step 3
prunes). Exit: 0 clean or reporting mode, 1 a problem under --strict, 2 usage, a missing manifest, or an
unreadable source or target (a mistyped local path included).
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.deployment.detector_manifest import (  # noqa: E402
    COMMON, MANIFEST, PACKAGES, REPO, STACK_SOURCES, _hash_file, build, listing, remote_path, select, verify)


def _read_text(source: str, package: str, rel: str) -> str:
    if ":" in source and not Path(source).exists():
        host, root = source.split(":", 1)
        path = f"{root.rstrip('/')}/filters/common/{package}/{rel}"
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, f"cat {remote_path(path)}"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"ssh cat {path}: {r.stderr.strip()[:200]}")
        return r.stdout
    return (Path(source) / "filters" / "common" / package / rel).read_text(encoding="utf-8")


def _served_commit(source: str) -> str | None:
    if ":" in source and not Path(source).exists():
        host, root = source.split(":", 1)
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, f"git -C {remote_path(root)} rev-parse --short HEAD"],
                           capture_output=True, text=True, timeout=60)
    else:
        r = subprocess.run(["git", "-C", source, "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def cmd_write(pkg: str, source: str) -> int:
    files = select(pkg, listing(source, pkg))
    cfg = None
    for rel in STACK_SOURCES:   # where the build stack is recorded; commerce v1 predates training_config.json
        if rel in files:
            cfg = json.loads(_read_text(source, pkg, rel))
            break
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    m = build(pkg, files, source, cfg, commit, _served_commit(source))
    out = COMMON / pkg / MANIFEST
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    hub = sum(f["bytes"] for f in m["files"] if f["origin"] == "hub")
    print(f"WROTE {out.relative_to(REPO)}: {len(m['files'])} files, {hub:,} B hub-origin, stack {m['build_stack']}")
    return 0


def cmd_adopt(pkg: str, rel: str, why: str) -> int:
    """Make THIS repo's copy of a git-origin file the one the manifest names (e.g. an owner ruling that our
    training_config.json is canonical). Production then differs until step 3 ships it: that is the point."""
    mpath = COMMON / pkg / MANIFEST
    m = json.loads(mpath.read_text(encoding="utf-8"))
    entry = next((f for f in m["files"] if f["path"] == rel), None)
    if entry is None or entry["origin"] != "git":
        raise ValueError(f"{pkg}: {rel} is not a git-origin file in the manifest")
    src = COMMON / pkg / rel
    if subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", str(src)],
                      capture_output=True).returncode != 0:
        raise ValueError(f"{src.relative_to(REPO)} is not tracked here: commit it before adopting it")
    old = entry["sha256"][:12]
    entry["sha256"], entry["bytes"] = _hash_file(src)
    if rel in STACK_SOURCES:   # the build stack must describe the file the manifest now names (review 2026-09-27)
        fresh = build(pkg, {}, "", json.loads(src.read_text(encoding="utf-8")), "")
        m["build_stack"] = fresh["build_stack"]
        pkl = any(f["path"].endswith(".pkl") for f in m["files"])
        m["build_stack_unrecorded"] = ["sklearn_version"] if pkl and "sklearn_version" not in fresh["build_stack"] else []
    m.setdefault("adopted_from_this_repo", []).append({"path": rel, "was": old, "why": why})
    mpath.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"ADOPTED {pkg}/{rel}: {old} -> {entry['sha256'][:12]} ({why})")
    return 0


def cmd_verify(pkg: str, target: str) -> tuple[int, int]:
    mpath = COMMON / pkg / MANIFEST
    if not mpath.is_file():
        raise FileNotFoundError(f"{pkg}: no manifest at {mpath.relative_to(REPO)}")
    res = verify(json.loads(mpath.read_text(encoding="utf-8")), listing(target, pkg))
    errors = len(res["missing"]) + len(res["mismatch"])
    for k in ("missing", "mismatch"):
        for x in res[k]:
            print(f"{pkg}: {k.upper()} {x}")
    print(f"{pkg}: {'OK' if not errors else 'FAIL'} against {target} "
          f"({errors} error(s); {len(res['extra'])} file(s) outside the package: {', '.join(res['extra'][:6])}"
          f"{' …' if len(res['extra']) > 6 else ''})")
    return errors, len(res["extra"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write"); w.add_argument("package", choices=sorted(PACKAGES)); w.add_argument("--source", required=True)
    ad = sub.add_parser("adopt"); ad.add_argument("package", choices=sorted(PACKAGES)); ad.add_argument("path")
    ad.add_argument("--why", required=True)
    v = sub.add_parser("verify"); v.add_argument("package", nargs="?", choices=sorted(PACKAGES))
    v.add_argument("--all", action="store_true"); v.add_argument("--target", required=True)
    v.add_argument("--strict", action="store_true", help="exit 1 on any missing/mismatching file")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "write":
            return cmd_write(a.package, a.source)
        if a.cmd == "adopt":
            return cmd_adopt(a.package, a.path, a.why)
        pkgs = sorted(PACKAGES) if a.all else [a.package] if a.package else None
        if not pkgs:
            ap.error("verify needs a package or --all")
        errors = sum(cmd_verify(p, a.target)[0] for p in pkgs)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if errors and not a.strict:
        print("(reporting mode: exit 0; pass --strict to fail)")
    return 1 if errors and a.strict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
