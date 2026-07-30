"""
Verify a filter package is internally consistent and (optionally) matches what's on Hub.

Purpose: catch the failure mode in issue #44 — a new version directory (v2, v3, …)
copied from the previous version but with imports / repo_id / config still pointing
at the old version, so production runs v_new config × v_old weights.

Static checks (always run):
  1. inference_hub.py default repo_id ends with -v{N} matching the directory version.
  2. inference*.py files import from filters.{name}.v{N}.* matching the directory version.
  3. config.yaml filter.version matches the directory version.
  4. config.yaml scoring.dimensions[*] each have a 'description' field (required by Hub upload).
  5. base_scorer.py FILTER_VERSION matches the directory version.

Hub check (run when --check-hub is passed):
  5. HfApi().repo_info(repo_id) succeeds; auth errors (401/403/Gated) are distinguished
     from "repo does not exist" (404).
  6. Hub last_modified is after local adapter_model.safetensors mtime — catches the case
     where the repo exists but the new weights were never uploaded. Anchored on the
     adapter file (written by training, never by git checkout or data-prep scripts) rather
     than training_history.json (git-tracked, its mtime resets on any checkout and would
     produce false FAILs on fresh clones).
  Skipped when a `NO_HUB` sentinel file exists in the filter directory — used for filters
  intentionally deployed via file-copy without a Hub backup (e.g., uplifting v7, see #47).

Known limitations:
  - check_imports detects cross-version references on lines beginning with `from` / `import`
    only. A continuation line inside a parenthesized multi-line import (`from filters.X.vN
    import (\n    Bad,\n)`) is not inspected. The `from` line itself IS inspected, so the
    #44 failure mode (whole file copied from v_prev) is still caught.
  - check_inference_hub_repo_id matches the typed default in the __init__ signature
    (`repo_id: str = "..."`). A module-level constant (`DEFAULT_REPO_ID = "..."` used as
    the default) would be missed. All current filters use the typed-default pattern.

Exit code is non-zero if any check fails. Intended to run as the first step of any
deploy action, and as a pre-commit gate for commits that claim "deploy".
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


class CheckFailure(Exception):
    pass


def parse_version_from_dir(filter_dir: Path) -> str:
    """filters/nature_recovery/v2 -> '2'. Raises if path doesn't match expected shape."""
    m = re.fullmatch(r"v(\d+)", filter_dir.name)
    if not m:
        raise CheckFailure(
            f"filter dir name must be v{{N}}, got: {filter_dir.name}"
        )
    return m.group(1)


def parse_filter_name_from_dir(filter_dir: Path) -> str:
    """filters/nature_recovery/v2 -> 'nature_recovery'."""
    return filter_dir.parent.name


def check_inference_hub_repo_id(filter_dir: Path, version: str) -> tuple[bool, str, str | None]:
    """Check inference_hub.py default repo_id ends with -v{version}.

    Returns (passed, message, extracted_repo_id).
    """
    path = filter_dir / "inference_hub.py"
    if not path.exists():
        return True, f"skip: {path.name} not present", None

    text = path.read_text(encoding="utf-8")
    # Match repo_id: str = "..."
    m = re.search(r'repo_id\s*:\s*str\s*=\s*"([^"]+)"', text)
    if not m:
        return False, f"{path.name}: no default repo_id found in signature", None

    repo_id = m.group(1)
    if re.search(rf"-v{version}(/|$)", repo_id):
        return True, f"{path.name}: repo_id ok ({repo_id})", repo_id
    return False, (
        f"{path.name}: repo_id {repo_id!r} does not end in -v{version} "
        f"(directory is v{version})"
    ), repo_id


def check_imports(filter_dir: Path, filter_name: str, version: str) -> list[tuple[bool, str]]:
    """Check inference*.py files import only from the matching vN subpackage."""
    results: list[tuple[bool, str]] = []
    pattern = re.compile(
        rf"filters\.{re.escape(filter_name)}\.v(\d+)\."
    )

    for name in ("inference.py", "inference_hub.py", "inference_hybrid.py"):
        path = filter_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        bad: list[tuple[int, str]] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            # Skip comments and docstrings heuristically - only check import statements
            stripped = line.lstrip()
            if not (stripped.startswith("from ") or stripped.startswith("import ")):
                continue
            for m in pattern.finditer(line):
                if m.group(1) != version:
                    bad.append((lineno, line.strip()))
        if bad:
            detail = "; ".join(f"L{ln}: {txt}" for ln, txt in bad)
            results.append((False, f"{name}: cross-version imports — {detail}"))
        else:
            results.append((True, f"{name}: imports ok"))
    return results


def check_config_yaml(filter_dir: Path, version: str) -> tuple[bool, str]:
    path = filter_dir / "config.yaml"
    if not path.exists():
        return True, "skip: config.yaml not present"

    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    declared = str(cfg.get("filter", {}).get("version", "")).split(".")[0]
    if declared == version:
        return True, f"config.yaml: filter.version={cfg['filter']['version']} ok"
    return False, (
        f"config.yaml: filter.version={cfg['filter']['version']!r} "
        f"does not match directory v{version}"
    )


def check_config_schema(filter_dir: Path) -> list[tuple[bool, str]]:
    """Check config.yaml dimensions each have a 'description' field.

    The Hub uploader's model-card template reads per-dim description lines.
    If any dim lacks one, upload_to_huggingface.py fails with KeyError
    after model files have already been transferred. Catches it early.
    """
    path = filter_dir / "config.yaml"
    if not path.exists():
        return [(True, "config.yaml: skip schema check — file not present")]

    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        # yaml.safe_load returns None for an empty file — report a failed
        # check instead of crashing the verifier with AttributeError.
        return [(False, "config.yaml: empty or not a mapping")]

    scoring = cfg.get("scoring", {})
    dims = scoring.get("dimensions", {})
    if not dims:
        return [(True, "config.yaml: no scoring.dimensions to check")]

    results: list[tuple[bool, str]] = []
    missing: list[str] = []
    for dim_name, dim_cfg in dims.items():
        if not isinstance(dim_cfg, dict):
            missing.append(f"{dim_name} (not a dict)")
        elif "description" not in dim_cfg:
            missing.append(dim_name)

    if missing:
        results.append((
            False,
            f"config.yaml: {len(missing)} dimension(s) missing 'description' field "
            f"(required by Hub upload): {', '.join(missing)}"
        ))
    else:
        results.append((
            True,
            f"config.yaml: all {len(dims)} dimension(s) have description"
        ))
    return results


def check_base_scorer_version(filter_dir: Path, version: str) -> tuple[bool, str]:
    path = filter_dir / "base_scorer.py"
    if not path.exists():
        return True, "skip: base_scorer.py not present"

    text = path.read_text(encoding="utf-8")
    m = re.search(r'FILTER_VERSION\s*=\s*"([^"]+)"', text)
    if not m:
        return True, "base_scorer.py: no FILTER_VERSION declared"
    declared = m.group(1).split(".")[0]
    if declared == version:
        return True, f"base_scorer.py: FILTER_VERSION={m.group(1)!r} ok"
    return False, (
        f"base_scorer.py: FILTER_VERSION={m.group(1)!r} "
        f"does not match directory v{version}"
    )


def check_hub(filter_dir: Path, repo_id: str | None, token: str | None) -> list[tuple[bool, str]]:
    """Verify repo exists on Hub and was updated after local adapter_model.safetensors."""
    results: list[tuple[bool, str]] = []

    # NO_HUB sentinel: filter is intentionally not deployed to Hub. Skip the
    # check entirely with a clear message so deploy gating doesn't FAIL on
    # filters that ship via file-copy only (uplifting v7, #47).
    #
    # Coexistence guard: if a filter has BOTH NO_HUB and inference_hub.py the
    # deploy state is ambiguous — inference_hub.py implies "Hub-deployed"
    # while NO_HUB implies "not Hub-deployed". This usually means a v(N+1)
    # was copy-pasted from a Hub-deployed v(N) template and someone forgot
    # to remove one of the two markers. FAIL explicitly so the inconsistency
    # gets resolved before the next deploy.
    if (filter_dir / "NO_HUB").exists():
        if (filter_dir / "inference_hub.py").exists():
            results.append((
                False,
                "hub: NO_HUB sentinel present but inference_hub.py also exists — "
                "ambiguous deploy state. Either remove NO_HUB (filter is Hub-deployed) "
                "or remove inference_hub.py (filter is file-copy only)."
            ))
            return results
        results.append((True, "hub: skip — NO_HUB sentinel present (file-copy deploy only)"))
        return results

    if not repo_id:
        results.append((False, "hub: cannot check — no repo_id extracted from inference_hub.py"))
        return results

    try:
        from huggingface_hub import HfApi
        from huggingface_hub.utils import (
            GatedRepoError,
            HfHubHTTPError,
            RepositoryNotFoundError,
        )
    except ImportError:
        results.append((False, "hub: huggingface_hub not installed"))
        return results

    api = HfApi(token=token)
    try:
        info = api.repo_info(repo_id=repo_id, repo_type="model")
    except RepositoryNotFoundError:
        # True 404. Also returned by Hub when the token can't see a private repo (by design,
        # to avoid leaking repo existence). Mention both possibilities.
        results.append((False, f"hub: repo {repo_id!r} not found — check repo name, or that HF_TOKEN can access it if private"))
        return results
    except GatedRepoError:
        results.append((False, f"hub: repo {repo_id!r} is gated — token needs access grant"))
        return results
    except HfHubHTTPError as e:
        status = e.response.status_code if getattr(e, "response", None) is not None else "?"
        if status in (401, 403):
            results.append((False, f"hub: auth error (HTTP {status}) on {repo_id!r} — HF_TOKEN missing or lacks access"))
        else:
            results.append((False, f"hub: HTTP {status} on {repo_id!r} — {e}"))
        return results
    except Exception as e:
        results.append((False, f"hub: repo_info({repo_id!r}) failed — {type(e).__name__}: {e}"))
        return results

    results.append((True, f"hub: {repo_id} exists"))

    # Anchor freshness on the adapter weights file itself: written by training, untracked
    # by git (model/ is not in the repo), so its mtime is NOT reset by `git checkout`.
    # training_history.json would be wrong here — it's git-tracked and its mtime resets
    # on every checkout, producing false FAILs on fresh clones. See verify_filter_package
    # module docstring for the full rationale.
    adapter_path = filter_dir / "model" / "adapter_model.safetensors"
    if not adapter_path.exists():
        results.append((True, f"hub: skip freshness check (no local {adapter_path.name} to compare against)"))
        return results

    local_mtime = datetime.fromtimestamp(adapter_path.stat().st_mtime, tz=timezone.utc)
    hub_mtime = info.last_modified
    if hub_mtime is None:
        results.append((False, "hub: repo has no last_modified timestamp — can't verify freshness"))
        return results

    # Hub last_modified must be AFTER the local adapter was written.
    # If the local adapter is newer than Hub, the upload hasn't happened since re-training.
    if hub_mtime >= local_mtime:
        results.append((
            True,
            f"hub: last_modified {hub_mtime.isoformat()} >= local adapter "
            f"{local_mtime.isoformat()}",
        ))
    else:
        results.append((
            False,
            f"hub: last_modified {hub_mtime.isoformat()} is OLDER than local adapter "
            f"{local_mtime.isoformat()} — weights likely not uploaded since last training",
        ))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument(
        "--filter",
        type=Path,
        required=True,
        help="Path to filter version directory, e.g., filters/nature_recovery/v2",
    )
    parser.add_argument(
        "--check-hub",
        action="store_true",
        help="Also verify the Hub repo exists and is fresh (requires HF_TOKEN or hf auth login)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face token (or set HF_TOKEN env var)",
    )
    args = parser.parse_args()

    filter_dir: Path = args.filter.resolve()
    if not filter_dir.is_dir():
        print(f"[FAIL] filter dir does not exist: {filter_dir}")
        return 2

    try:
        version = parse_version_from_dir(filter_dir)
    except CheckFailure as e:
        print(f"[FAIL] {e}")
        return 2
    filter_name = parse_filter_name_from_dir(filter_dir)

    print(f"Verifying {filter_name} v{version} at {filter_dir}")
    print("-" * 60)

    all_checks: list[tuple[bool, str]] = []

    passed, msg, repo_id = check_inference_hub_repo_id(filter_dir, version)
    all_checks.append((passed, msg))
    all_checks.extend(check_imports(filter_dir, filter_name, version))
    all_checks.append(check_config_yaml(filter_dir, version))
    all_checks.extend(check_config_schema(filter_dir))
    all_checks.append(check_base_scorer_version(filter_dir, version))

    if args.check_hub:
        token = args.token or os.environ.get("HF_TOKEN")
        all_checks.extend(check_hub(filter_dir, repo_id, token))

    for passed, msg in all_checks:
        prefix = "[OK]  " if passed else "[FAIL]"
        print(f"{prefix} {msg}")

    print("-" * 60)
    failed = sum(1 for p, _ in all_checks if not p)
    total = len(all_checks)
    if failed == 0:
        print(f"All {total} checks passed.")
        return 0
    print(f"{failed}/{total} checks failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
