"""Detector package manifests: ADR-024 order step 1 (llm-distillery#165).

A detector package is `filters/common/<detector>/<version>/`. Its `MANIFEST.json` names the package's runtime
files, each with a sha256 and a byte count, and whether the bytes live in git or on the Hub. Only
listed files ship (step 3). The loaders will verify against it (NexusMind, step 4).

What each package holds is declared in PACKAGES below, from what each loader reads (NexusMind `main`,
2026-09-27): no loader reads `config.yaml`, `calibration_report.json` or `README.md`, and commerce v1 loads only
`models/distilbert` (its minilm / qwen-lora / xlm-roberta folders are benchmark candidates). The `.sha256` sidecars
stay listed until the loaders read the manifest instead (step 4). Two deliberate differences from "what the loader
reads": `models/training_config.json` is listed for every MLP detector although only harm READS it, because it is
where the build stack is recorded (Q5); and the list does NOT cover runtime dependencies outside the package dir,
namely the shared `filters/common/embedding_stage.py` and the (unpinned) sentence-transformers embedder that
every MLP detector loads. ADR-024 keeps shared modules out of a detector's manifest on purpose.

⚠️ Until step 2 fills `hub`, a manifest has `origin: "hub"` files and `hub: null`: step 3 must REFUSE such a
manifest, not fetch from a guess.

The package set is the owner's ruling (ADR-024, 2026-09-27): harm v1, obituary v5, violence_promotion v1,
commerce_prefilter v1. obituary v3/v4 and commerce v2 are retired, not packaged.

Hashes are taken from a TREE, local or `host:path` over ssh (read-only), because the backfill must describe
the bytes production SERVES, not this working tree (ADR-024 Risks).
"""

from __future__ import annotations

import datetime as _dt
import fnmatch
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMON = REPO / "filters" / "common"
MANIFEST = "MANIFEST.json"
SCHEMA = 1

# Patterns are relative to the package dir; `*` never crosses a `/`. Every pattern must match at least one file.
PACKAGES: dict[str, list[str]] = {
    "harm_detector/v1": [
        "__init__.py", "inference.py",
        "models/training_config.json", "models/scaler.pkl", "models/scaler.pkl.sha256",
        "models/mlp_classifier_seed*.pkl", "models/mlp_classifier_seed*.pkl.sha256",
    ],
    "obituary_detector/v5": [
        "__init__.py", "inference.py",
        "models/training_config.json", "models/mlp_classifier.pkl", "models/mlp_classifier.pkl.sha256",
        "models/scaler.pkl", "models/scaler.pkl.sha256",
    ],
    "violence_promotion/v1": [
        "inference.py",
        "models/training_config.json", "models/mlp_classifier.pkl", "models/mlp_classifier.pkl.sha256",
        "models/scaler.pkl", "models/scaler.pkl.sha256",
    ],
    "commerce_prefilter/v1": [
        "__init__.py", "inference.py",
        "models/distilbert/config.json", "models/distilbert/model.safetensors",
        "models/distilbert/tokenizer.json", "models/distilbert/tokenizer_config.json",
        "models/distilbert/special_tokens_map.json", "models/distilbert/vocab.txt",
    ],
}
# Bytes that go to the Hub (step 2); everything else is small and stays in git.
HUB_SUFFIXES = (".pkl", ".safetensors", ".bin")
# Files that record the build stack, first present wins; and the keys copied from it (ADR-024 Q5).
STACK_SOURCES = ("models/training_config.json", "models/distilbert/config.json")
# Keys copied (ADR-024 Q5: warn on skew at load).
STACK_KEYS = ("sklearn_version", "joblib_version", "numpy_version", "torch_version", "transformers_version",
              "python_version", "embedder", "embedding_model", "embedder_model")


def _match(pattern: str, rel: str) -> bool:
    return len(pattern.split("/")) == len(rel.split("/")) and all(
        fnmatch.fnmatchcase(r, p) for p, r in zip(pattern.split("/"), rel.split("/")))


def select(package: str, listing: dict[str, tuple[str, int]]) -> dict[str, tuple[str, int]]:
    """The package's runtime files out of a {relpath: (sha256, bytes)} listing of its directory.
    Raises when a pattern matches nothing: a missing runtime file must never become a smaller manifest."""
    patterns = PACKAGES[package]
    chosen = {}
    for pat in patterns:
        hits = {r: v for r, v in listing.items() if _match(pat, r)}
        if not hits:
            raise ValueError(f"{package}: no file matches {pat!r}")
        chosen.update(hits)
    return dict(sorted(chosen.items()))


def _hash_file(p: Path) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    with p.open("rb") as f:                       # streamed: commerce v1's model is 541 MB
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk); n += len(chunk)
    return h.hexdigest(), n


def listing_local(pkg_dir: Path) -> dict[str, tuple[str, int]]:
    """Raises when the dir is missing: a mistyped target must not read as a tree with every file MISSING."""
    if not pkg_dir.is_dir():
        raise FileNotFoundError(f"not a directory: {pkg_dir}")
    return {p.relative_to(pkg_dir).as_posix(): _hash_file(p)
            for p in sorted(pkg_dir.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def remote_path(path: str) -> str:
    """Shell-quote a remote path, keeping a leading `~/` expandable (shlex.quote makes it a literal `~`)."""
    return '"$HOME"/' + shlex.quote(path[2:]) if path.startswith("~/") else shlex.quote(path)


def listing_remote(host: str, pkg_dir: str, timeout: int = 600) -> dict[str, tuple[str, int]]:
    """sha256 + size of every file under a remote package dir, read-only over ssh."""
    cmd = (f"cd {remote_path(pkg_dir)} && find . -type f ! -path '*/__pycache__/*' -print0 "
           f"| xargs -0 -r sh -c 'for f; do printf \"%s %s %s\\n\" \"$(sha256sum \"$f\" | cut -d\" \" -f1)\" "
           f"\"$(stat -c %s \"$f\")\" \"$f\"; done' _")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, cmd],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"ssh {host}: exit {r.returncode}: {r.stderr.strip()[:300]}")
    return parse_listing(r.stdout)


def parse_listing(text: str) -> dict[str, tuple[str, int]]:
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        digest, size, path = line.split(" ", 2)
        if len(digest) != 64:
            raise ValueError(f"bad listing line: {line!r}")
        out[path[2:] if path.startswith("./") else path] = (digest, int(size))
    return out


def listing(source: str, package: str) -> dict[str, tuple[str, int]]:
    """`source` is a NexusMind (or llm-distillery) repo root, local or `host:path`."""
    if ":" in source and not Path(source).exists():
        host, root = source.split(":", 1)
        return listing_remote(host, f"{root.rstrip('/')}/filters/common/{package}")
    return listing_local(Path(source) / "filters" / "common" / package)


def build(package: str, files: dict[str, tuple[str, int]], source: str, training_config: dict | None,
          source_commit: str, served_commit: str | None = None) -> dict:
    detector, version = package.split("/")
    stack = {k: training_config[k] for k in STACK_KEYS if training_config and k in training_config}
    # Q5 needs the library that unpickles the weights. Say so when the build did not record it, rather than
    # write an empty stack that reads as "nothing to record".
    need = {".pkl": "sklearn_version", ".safetensors": "transformers_version"}
    unrecorded = sorted({v for suf, v in need.items() if any(p.endswith(suf) for p in files) and v not in stack})
    return {
        "schema": SCHEMA,
        "detector": detector,
        "version": version,
        "source_commit": source_commit,   # llm-distillery HEAD when the manifest was written
        "built_utc": (training_config or {}).get("built_utc"),   # ADR-024 field; null when the build did not record it
        "backfilled_from": source,
        "served_commit": served_commit,   # the NexusMind checkout's HEAD the bytes were hashed from (untracked files: none)
        "written_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "build_stack": stack,
        "build_stack_unrecorded": unrecorded,
        "hub": None,   # step 2 fills {repo_id, revision}; until then `hub` files have no record of origin
        "files": [{"path": p, "sha256": d, "bytes": n, "origin": "hub" if p.endswith(HUB_SUFFIXES) else "git"}
                  for p, (d, n) in files.items()],
    }


def verify(manifest: dict, tree: dict[str, tuple[str, int]]) -> dict[str, list[str]]:
    """Compare a package dir listing with its manifest. `extra` files are reported, never an error:
    until step 3 prunes, NexusMind legitimately holds files outside the package."""
    listed = {f["path"]: (f["sha256"], f["bytes"]) for f in manifest["files"]}
    out = {"missing": [], "mismatch": [], "extra": []}
    for p, (d, n) in listed.items():
        if p not in tree:
            out["missing"].append(p)
        elif tree[p] != (d, n):
            out["mismatch"].append(f"{p}: manifest {d[:12]}/{n} B, tree {tree[p][0][:12]}/{tree[p][1]} B")
    out["extra"] = sorted(set(tree) - set(listed))
    return out
