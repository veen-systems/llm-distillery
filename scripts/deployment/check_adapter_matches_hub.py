#!/usr/bin/env python3
"""Is this checkout's LoRA adapter byte-identical to its Hub copy?

Since NexusMind#395 (2026-09-29) production scores from a container image that
NexusMind's `deploy/scorer-image/stage.py` builds with `--weights-dir <an llm-distillery
checkout>`. When that checkout HAS a version's adapter, staging uses it and refuses it if
it differs from the Hub copy; when it has none, staging downloads the Hub copy; a `NO_HUB`
version must be local (stage.py `fill_weights`, NexusMind origin/main 2026-10-09). So a
local adapter that differs from the Hub fails NexusMind's build after merge. This asks the
same question here, before handing the version over.

    python3 scripts/deployment/check_adapter_matches_hub.py belonging v3

The Hub repo id is read from the package's `inference_hub.py` (`repo_id: str = "..."`),
exactly as stage.py's `hub_repo_id()` reads it — never derived from the directory name,
which uses underscores where the Hub repos use hyphens (cultural_discovery, human_thriving,
nature_recovery: review 2026-10-09).

Exit 0 = match (or `NO_HUB` with an adapter present: nothing to compare), 1 = mismatch,
or a missing / stub (< 1 MB, e.g. a git-LFS pointer) adapter, 2 = no such package, could
not ask the Hub, or the package names no repo id.
`--local PATH` compares another file (used by the negative control in the tests).
Token: `HF_TOKEN` from the environment first, then `config/credentials/secrets.ini`.
"""
import argparse
import configparser
import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = "adapter_model.safetensors"
# Every real LoRA adapter here is ~52 MB (11 on disk, 52,254,448–52,263,664 B, measured
# 2026-10-09: `find filters -name adapter_model.safetensors -printf '%s\n' | sort -n`).
# Below this it is a stub, e.g. a git-LFS pointer from cloning a Hub repo without git-lfs,
# and hashing it would report a MISMATCH whose advice (re-upload) replaces the real Hub copy. Guard E in preflight_deploy_guards.py uses the
# same floor (a test pins them equal).
MIN_ADAPTER_BYTES = 1_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hub_sha256(repo_id: str, token: str | None) -> str | None:
    from huggingface_hub import HfApi

    info = HfApi(token=token).model_info(repo_id, files_metadata=True)
    for s in info.siblings:
        if s.rfilename == ADAPTER:
            return s.lfs.sha256 if s.lfs else None
    return None


def hub_repo_id(filter_dir: Path) -> str | None:
    """The package's own Hub repo id, parsed as NexusMind's stage.py `hub_repo_id()` does."""
    hub_py = filter_dir / "inference_hub.py"
    if not hub_py.is_file():
        return None
    m = re.search(r'repo_id\s*:\s*str\s*=\s*"([^"]+)"', hub_py.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def token_from_secrets() -> str | None:
    """`HF_TOKEN` from the environment first (so a stale secrets.ini can be overridden),
    then config/credentials/secrets.ini."""
    env = os.environ.get("HF_TOKEN", "").strip()
    if env:
        return env
    c = configparser.ConfigParser()
    c.read(ROOT / "config" / "credentials" / "secrets.ini")
    try:
        return c["api_keys"]["huggingface_token"].strip() or None
    except KeyError:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    ap.add_argument("version", help="e.g. v3")
    ap.add_argument("--local", type=Path, help="adapter file to compare (default: the package's)")
    ap.add_argument("--repo-id", help="default: the repo_id in the package's inference_hub.py")
    args = ap.parse_args(argv)

    filter_dir = ROOT / "filters" / args.name / args.version
    local = args.local or filter_dir / "model" / ADAPTER
    if not args.local and not filter_dir.is_dir():
        print(f"NO PACKAGE: {filter_dir} does not exist")
        return 2
    # Before NO_HUB (review round 2, 2026-10-09): a NO_HUB version's local file is the ONLY
    # copy staging can serve, so its absence is the worst case, not "nothing to compare".
    if not local.is_file():
        print(f"MISSING: {local} — NexusMind's image staging reads the adapter from this checkout")
        return 1
    size = local.stat().st_size
    if size < MIN_ADAPTER_BYTES:
        print(f"STUB: {local} is only {size} bytes — a git-LFS pointer or a stub, not an adapter.\n"
              "  Re-download it from the Hub; never re-upload it, which would replace the real Hub copy.")
        return 1
    if not args.repo_id and (filter_dir / "NO_HUB").exists():
        print(f"NO_HUB: {args.name}/{args.version} has no Hub copy to compare (staging records its sha256)")
        return 0
    repo_id = args.repo_id or hub_repo_id(filter_dir)
    if not repo_id:
        print(f"NO REPO ID: {filter_dir}/inference_hub.py names no `repo_id: str = \"...\"` and there is "
              "no NO_HUB file. NexusMind's staging would stage a local adapter UNCHECKED.")
        return 2
    try:
        hub = hub_sha256(repo_id, token_from_secrets())
    except Exception as e:  # network, auth, 404 for a private repo the token cannot see
        print(f"CANNOT ASK THE HUB for {repo_id}: {type(e).__name__}: {e}")
        return 2
    if hub is None:
        print(f"CANNOT VERIFY: {repo_id} lists no LFS sha256 for {ADAPTER}")
        return 2
    mine = sha256(local)
    verdict = "MATCH" if mine == hub else "MISMATCH"
    print(f"{verdict}  {repo_id}\n  local {mine}  {local}\n  hub   {hub}")
    return 0 if mine == hub else 1


if __name__ == "__main__":
    sys.exit(main())
