"""Filter package completeness, against both cores the project actually declares.

⛔ THE FILTER LIST USED TO BE HAND-MAINTAINED, AND IT WENT STALE. Until 2026-09-06 it
named five filters: `uplifting v6` (superseded by v7), `cultural_discovery v4`
(superseded by v5), and `sustainability_technology v3` — **deleted on 2026-08-03**,
so every row rendered `---` and a removed package read as an incomplete one. It
omitted `nature_recovery`, `solutions` and `human_thriving` entirely. *Every
measurement error this project has made was a hand-built population*; the list is
now discovered from the filesystem.

Two cores, because the project declares two and they are not the same thing:

- **Docs** — `memory/filter-doc-standard.md`'s 6-file core. `prefilter.py` is NOT
  in it (removed 2026-08-21, owner ruling): a per-lens keyword prefilter is
  optional and omission is the default for new filters.
- **Code/artifacts** — what a package needs in order to score.

⚠️ `model/*` AND `probe/*.pkl` ARE EXPECTED ABSENT IN A CLONE. Model checkpoints
are gitignored as large files, so "missing" here means *missing on this disk*, not
*missing from the package*. They are reported in their own section rather than as
failures, because conflating the two is how a correctly-built package reads as
broken.

⚠️ THIS IS A REPORT, NOT A GATE, and an earlier draft of this docstring claimed it
was "the tool the package-parity gate invokes" — which was false. Nothing invokes
it: no hook, no CI, no `<!-- verify: -->` annotation (`grep -rn filter_completeness`
finds only prose, this file and its tests). The actual package gate is
`scripts/deployment/verify_filter_package.py`, which the commit-msg hook runs.
Mention-as-use, inside the file whose whole thesis is that hand-maintained state
goes stale — found in review 2026-09-06.

⚠️ `main()` RETURNS 0 HOWEVER INCOMPLETE THE FLEET IS (today: 4/29 doc-complete).
That is correct for a report and wrong for a gate, so if it is ever wired into a
battery it will pass unconditionally. Use `--strict` to make incompleteness a
non-zero exit; nothing passes that today, deliberately, because most of the 29 are
archived versions nobody intends to complete.

Usage:
    python3 scripts/analysis/filter_completeness.py
    python3 scripts/analysis/filter_completeness.py --core docs
    python3 scripts/analysis/filter_completeness.py --strict   # exit 1 if incomplete
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILTERS_DIR = os.path.join(ROOT, "filters")
VERSION_RE = re.compile(r"^v\d+")

# memory/filter-doc-standard.md, items 1-2 and 4-7. Item 3 (prefilter.py) was
# removed from the core on 2026-08-21 and is deliberately not here.
DOC_CORE = [
    "config.yaml",
    "prompt-compressed.md",
    "STATUS.md",
    "DEEP_ROOTS.md",
    "README.md",
    "README_MODEL.md",
]

CODE_CORE = [
    "base_scorer.py",
    "inference.py",
    "inference_hybrid.py",
    "calibration.json",
    "training_history.json",
    "training_metadata.json",
]

# Present only when the weights are on this disk. Never counted as missing.
LOCAL_ONLY = [
    "model/adapter_config.json",
    "model/adapter_model.safetensors",
    "model/tokenizer.json",
    "model/tokenizer_config.json",
    "probe/embedding_probe_e5small.pkl",
]

# `inference_hub.py` and `NO_HUB` are mutually exclusive by
# verify_filter_package.py's own rule, so "exactly one" is the check, not presence.
HUB_DECLARATION = ["inference_hub.py", "NO_HUB"]


def discover() -> list[str]:
    """Every `filters/<name>/v<N>/` on disk, in path order."""
    found = []
    if not os.path.isdir(FILTERS_DIR):
        return found
    for name in sorted(os.listdir(FILTERS_DIR)):
        base = os.path.join(FILTERS_DIR, name)
        if not os.path.isdir(base) or name == "common":
            continue
        for ver in sorted(os.listdir(base)):
            if VERSION_RE.match(ver) and os.path.isdir(os.path.join(base, ver)):
                found.append(f"filters/{name}/{ver}")
    return found


def present(pkg: str, rel: str) -> bool:
    return os.path.exists(os.path.join(ROOT, pkg, rel))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core", choices=("docs", "code", "both"), default="both")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any package is incomplete — off by default because "
                         "this is a report, not a gate, and most of the 29 packages are "
                         "archived versions nobody intends to complete")
    args = ap.parse_args(argv if argv is not None else [])
    incomplete = 0

    packages = discover()
    if not packages:
        print("CANNOT VERIFY: no filters/<name>/v<N>/ directories found — the "
              "layout moved, or this is not the repo root")
        return 1

    cores = []
    if args.core in ("docs", "both"):
        cores.append(("doc standard (6-file core)", DOC_CORE))
    if args.core in ("code", "both"):
        cores.append(("code + artifacts", CODE_CORE))

    for title, core in cores:
        print(f"\n=== {title} ===")
        width = max(len(p) for p in packages)
        for pkg in packages:
            missing = [f for f in core if not present(pkg, f)]
            status = "COMPLETE" if not missing else "missing: " + " ".join(missing)
            print(f"  {pkg:<{width}}  {status}")
        complete = [p for p in packages if all(present(p, f) for f in core)]
        incomplete += len(packages) - len(complete)
        print(f"  -- {len(complete)}/{len(packages)} complete")

    print("\n=== hub declaration (exactly one of inference_hub.py / NO_HUB) ===")
    width = max(len(p) for p in packages)
    for pkg in packages:
        have = [f for f in HUB_DECLARATION if present(pkg, f)]
        if len(have) == 1:
            note = have[0]
        elif not have:
            note = ("NEITHER — verify_filter_package.py --check-hub cannot resolve "
                    "this package")
        else:
            note = "BOTH — ambiguous, --check-hub refuses this outright"
        print(f"  {pkg:<{width}}  {note}")

    print("\n=== weights and probe (gitignored; absent in a clone is normal) ===")
    for pkg in packages:
        have = sum(present(pkg, f) for f in LOCAL_ONLY)
        if have:
            print(f"  {pkg:<{width}}  {have}/{len(LOCAL_ONLY)} present on this disk")
    if args.strict and incomplete:
        print(f"\nFAIL --strict: {incomplete} package/core pair(s) incomplete")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
