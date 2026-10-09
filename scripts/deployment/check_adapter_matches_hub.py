#!/usr/bin/env python3
"""Is this checkout's LoRA adapter byte-identical to its Hub copy?

Since NexusMind#395 (2026-09-29) production scores from a container image that
NexusMind's `deploy/scorer-image/stage.py` builds with `--weights-dir <an llm-distillery
checkout>`. Staging takes the adapter from that checkout and refuses one that differs
from the Hub. So before handing a filter version to NexusMind, the adapter must be HERE,
and it must match the Hub. This answers that question locally, before NexusMind's
staging does.

    python3 scripts/deployment/check_adapter_matches_hub.py belonging v3

Exit 0 = match, 1 = mismatch or missing adapter, 2 = could not ask the Hub.
`--local PATH` compares another file (used by the negative control in the tests).
`NO_HUB` versions (uplifting v7) have no Hub copy: this check does not apply to them.
"""
import argparse
import configparser
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUB_OWNER = "jeergrvgreg"
ADAPTER = "adapter_model.safetensors"


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


def token_from_secrets() -> str | None:
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
    ap.add_argument("--repo-id", help=f"default: {HUB_OWNER}/<name>-filter-<version>")
    args = ap.parse_args(argv)

    local = args.local or ROOT / "filters" / args.name / args.version / "model" / ADAPTER
    repo_id = args.repo_id or f"{HUB_OWNER}/{args.name}-filter-{args.version}"
    if not local.is_file():
        print(f"MISSING: {local} — NexusMind's image staging reads the adapter from this checkout")
        return 1
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
