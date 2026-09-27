#!/usr/bin/env python3
"""ADR-024 order step 2: record a detector package's hub-origin files on the HF Hub and pin the revision.

    python scripts/deployment/upload_detector_to_hub.py harm_detector/v1 [--dry-run]

Per the owner's rulings (2026-09-27) there is ONE private repo per detector, named `jeergrvgreg/<concept>-detector` (REPO_NAMES),
and each version lives under `<version>/` in it. The script:
  1. finds, for every `origin: "hub"` file in the committed MANIFEST.json, a local copy whose sha256 matches the
     manifest (this repo first, then the NexusMind checkout beside it). A file with no matching copy STOPS the run:
     the manifest records what production serves, and nothing else may be uploaded in its name;
  2. creates the private repo if needed and uploads all of them in ONE commit;
  3. re-downloads every file AT THAT COMMIT into a temp dir and compares sha256 + size with the manifest. The
     upload's exit code is not the evidence;
  4. only then writes `hub: {repo_id, revision, path_prefix}` into the manifest.
The token comes from HF_TOKEN or config/credentials/secrets.ini, as deploy_to_nexusmind.sh reads it.
⚠️ Not idempotent: every run makes a NEW Hub commit (a new revision), even for unchanged bytes. If step 3 fails
after the commit, the manifest stays unpinned and the Hub keeps an unreferenced commit: harmless (nothing points
at it), but re-running uploads again rather than reusing it.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.deployment.detector_manifest import COMMON, MANIFEST, PACKAGES, REPO, _hash_file  # noqa: E402

OWNER = "jeergrvgreg"
SEARCH = (REPO, REPO.parent / "NexusMind")


# Owner ruling 2026-09-27: `<concept>-detector`, parallel to the filters' `<name>-filter-v<N>`. An explicit table,
# not a derivation from the folder name: the folders do not share a pattern, and deriving copied that into the
# first four repos (two were renamed the same day: violence-promotion, commerce-prefilter).
REPO_NAMES = {
    "harm_detector": "harm-detector",
    "obituary_detector": "obituary-detector",
    "violence_promotion": "violence-promotion-detector",
    "commerce_prefilter": "commerce-detector",
}


def repo_id_for(detector: str) -> str:
    """Raises for a detector with no ruled name, rather than inventing one."""
    return f"{OWNER}/{REPO_NAMES[detector]}"


def find_local(package: str, rel: str, sha: str, size: int, roots=SEARCH) -> Path:
    for root in roots:
        p = root / "filters" / "common" / package / rel
        if p.is_file() and _hash_file(p) == (sha, size):
            return p
    raise FileNotFoundError(f"{package}/{rel}: no local copy with sha256 {sha[:12]} ({size} B) in "
                            + ", ".join(str(r) for r in roots))


def _token() -> str:
    t = os.environ.get("HF_TOKEN", "")
    if not t:
        c = configparser.ConfigParser()
        c.read(REPO / "config" / "credentials" / "secrets.ini")
        t = c.get("api_keys", "huggingface_token", fallback="").strip()
    if not t:
        raise RuntimeError("no HF token (HF_TOKEN or config/credentials/secrets.ini)")
    return t


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("package", choices=sorted(PACKAGES))
    ap.add_argument("--dry-run", action="store_true", help="find and hash the local copies; upload nothing")
    a = ap.parse_args(argv)
    mpath = COMMON / a.package / MANIFEST
    m = json.loads(mpath.read_text(encoding="utf-8"))
    hub_files = [f for f in m["files"] if f["origin"] == "hub"]
    local = {f["path"]: find_local(a.package, f["path"], f["sha256"], f["bytes"]) for f in hub_files}
    repo_id, prefix = repo_id_for(m["detector"]), m["version"]
    for f in hub_files:
        print(f"  {f['path']}  {f['bytes']:,} B  <- {local[f['path']]}")
    if a.dry_run:
        print(f"DRY RUN: would upload {len(hub_files)} file(s) to {repo_id} under {prefix}/")
        return 0

    from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
    api = HfApi(token=_token())
    api.create_repo(repo_id, private=True, exist_ok=True, repo_type="model")
    ops = [CommitOperationAdd(path_in_repo=f"{prefix}/{f['path']}", path_or_fileobj=str(local[f["path"]]))
           for f in hub_files]
    info = api.create_commit(repo_id, operations=ops, commit_message=(
        f"{m['detector']} {prefix}: {len(ops)} file(s) from MANIFEST.json (llm-distillery ADR-024; "
        f"served_commit {m.get('served_commit')})"))
    revision = info.oid
    print(f"UPLOADED {len(ops)} file(s) to {repo_id}@{revision}")

    with tempfile.TemporaryDirectory() as tmp:
        for f in hub_files:
            got = Path(hf_hub_download(repo_id, f"{prefix}/{f['path']}", revision=revision,
                                       token=api.token, cache_dir=tmp))
            if _hash_file(got) != (f["sha256"], f["bytes"]):
                print(f"FAIL re-download {f['path']}: {_hash_file(got)[0][:12]} != manifest {f['sha256'][:12]}")
                return 1
    print(f"VERIFIED by re-download at {revision[:12]}: {len(hub_files)} file(s) match the manifest")
    m["hub"] = {"repo_id": repo_id, "revision": revision, "path_prefix": prefix}
    mpath.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"PINNED {mpath.relative_to(REPO)}: hub = {m['hub']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
