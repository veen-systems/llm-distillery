#!/usr/bin/env python3
"""Does every trained checkpoint name a commit, and is that commit still durable?

⛔ THE DEFECT THIS EXISTS FOR. `human_thriving v8`'s first adapter was trained by
the tree that became `1878e7b` via `git commit --amend`. The sha that actually
produced it (`0697f5a`) is reachable from no branch and will not survive
`git gc`, so the shipped artifact could not be traced to any commit — and nothing
noticed for two days, because `training_metadata.json` recorded no commit at all.
The owner's ruling on 2026-09-06 was *no exception, harmonize it*: the checkpoint
was retrained under a commit on `main` rather than shipped with a carve-out.

Two halves, and the second is the one a stamp alone would miss:

1. `training/train.py` now stamps `git_commit` / `git_dirty` at run time and
   REFUSES to train without them (`--allow-missing-git-provenance` to opt out,
   which is itself recorded).
2. This check re-reads those stamps LATER, which is when an amend, a rebase or a
   gc has had the chance to orphan the commit. A stamp is a claim about the past;
   reachability is a property of now, and only now can be measured.

⚠️ THE PRE-EXISTING FILES ARE NOT FAILURES, and the exemption is bounded. Twenty
`training_metadata.json` files predate the stamp; they are listed in
`UNSTAMPED_BASELINE` and reported as NOTES. A NEW unstamped file FAILS — the
baseline is a frozen list, not a rule, so it can only shrink.

Usage:
    python3 scripts/verification/check_training_provenance.py
    python3 scripts/verification/check_training_provenance.py --json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ⛔ FROZEN 2026-09-06. Files that predate the provenance stamp. This list may
# SHRINK (a filter gets retrained under a commit) and must never grow: a new
# unstamped metadata file means training ran from a tree nobody can name, which
# is the whole defect. Do not add to it — retrain, or record why in the ADR.
UNSTAMPED_BASELINE = frozenset({
    "filters/belonging/v1/training_metadata.json",
    "filters/cultural_discovery/v1/training_metadata.json",
    "filters/cultural_discovery/v2/training_metadata.json",
    "filters/cultural_discovery/v4/training_metadata.json",
    "filters/cultural_discovery/v5/training_metadata.json",
    "filters/cultural_discovery/v6/training_metadata.json",
    "filters/human_thriving/v8/training_metadata.json",
    "filters/human_thriving/v8/training_metadata_baseline_mae.json",
    "filters/investment_risk/v2_distillation/training_metadata.json",
    "filters/investment_risk/v2_instruction/training_metadata.json",
    "filters/investment_risk/v4/training_metadata.json",
    "filters/investment_risk/v6/training_metadata.json",
    "filters/nature_recovery/v1/training_metadata.json",
    "filters/nature_recovery/v2/training_metadata.json",
    "filters/nature_recovery/v4/training_metadata.json",
    "filters/solutions/v4/training_metadata.json",
    "filters/solutions/v6/training_metadata.json",
    "filters/uplifting/v4/training_metadata.json",
    "filters/uplifting/v4_distillation/training_metadata.json",
    "filters/uplifting/v6/training_metadata.json",
})

SCAN_GLOB = "filters/*/*/training_metadata*.json"


def _git(*args, root=None):
    return subprocess.run(("git", "-C", root or ROOT) + args,
                          capture_output=True, text=True, timeout=30)


def _commit_exists(sha: str) -> bool:
    r = _git("cat-file", "-e", f"{sha}^{{commit}}")
    return r.returncode == 0


def _branches_containing(sha: str) -> list[str]:
    r = _git("branch", "--all", "--contains", sha)
    if r.returncode != 0:
        return []
    return [b.strip().lstrip("* ").strip() for b in r.stdout.splitlines() if b.strip()]


def check(argv=None) -> tuple[int, list[str]]:
    out, rc = [], 0

    probe = _git("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return 1, ["CANNOT VERIFY training-provenance: not a git work tree, so "
                   "reachability cannot be established — this check is the one "
                   "thing that must not pass quietly when it cannot run"]

    files = sorted(os.path.relpath(p, ROOT).replace(os.sep, "/")
                   for p in glob.glob(os.path.join(ROOT, SCAN_GLOB)))
    if not files:
        return 1, [f"CANNOT VERIFY training-provenance: {SCAN_GLOB} matched no "
                   f"files — the instrument is narrower than it looks, or the "
                   f"filter layout moved"]

    stamped = unstamped = 0
    for rel in files:
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                meta = json.load(fh)
        except (ValueError, OSError) as exc:
            rc = 1
            out.append(f"CANNOT VERIFY training-provenance: {rel} is not readable "
                       f"JSON ({exc})")
            continue

        if "git_commit" not in meta:
            unstamped += 1
            if rel in UNSTAMPED_BASELINE:
                out.append(f"NOTE training-provenance: {rel} predates the stamp "
                           f"(frozen baseline) — its checkpoint names no commit")
            else:
                rc = 1
                out.append(f"FAIL training-provenance: {rel} records no "
                           f"`git_commit` and is NOT in the frozen baseline. "
                           f"Training ran from a tree nobody can name.")
            continue

        stamped += 1
        sha = meta["git_commit"]
        if sha is None:
            rc = 1
            out.append(f"FAIL training-provenance: {rel} declares "
                       f"{meta.get('git_provenance')!r} — trained with "
                       f"--allow-missing-git-provenance, so the checkpoint's "
                       f"origin is unrecorded by construction")
            continue
        if not _commit_exists(sha):
            rc = 1
            out.append(f"FAIL training-provenance: {rel} names commit "
                       f"{sha[:12]}, which does not exist in this repository")
            continue
        branches = _branches_containing(sha)
        if not branches:
            rc = 1
            out.append(f"FAIL training-provenance: {rel} names commit "
                       f"{sha[:12]}, which is reachable from NO BRANCH — an "
                       f"amend or a gc can erase the tree that trained this "
                       f"checkpoint. This is the human_thriving v8 shape.")
            continue
        if meta.get("git_dirty"):
            rc = 1
            out.append(f"FAIL training-provenance: {rel} names {sha[:12]} but "
                       f"records git_dirty=true — the sha does not identify the "
                       f"tree that trained it")
            continue
        out.append(f"OK   training-provenance: {rel} -> {sha[:12]} "
                   f"(clean, on {branches[0]})")

    gone = sorted(UNSTAMPED_BASELINE - set(files))
    if gone:
        out.append(f"NOTE training-provenance: {len(gone)} baseline entr(ies) no "
                   f"longer on disk — the list may shrink; prune them: "
                   f"{', '.join(gone)}")

    verdict = "PASS" if rc == 0 else "FAIL"
    out.append(f"{verdict} training-provenance: {stamped} stamped, {unstamped} "
               f"unstamped ({len(UNSTAMPED_BASELINE)} in the frozen baseline), "
               f"over {len(files)} metadata file(s)")
    return rc, out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv if argv is not None else [])
    rc, lines = check()
    if args.json:
        print(json.dumps({"rc": rc, "lines": lines}, indent=2))
    else:
        for line in lines:
            print(line)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
