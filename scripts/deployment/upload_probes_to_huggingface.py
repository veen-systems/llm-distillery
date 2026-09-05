#!/usr/bin/env python3
"""Upload the rescued e5 probes to a PRIVATE Hugging Face repo.

⛔ WHY THIS EXISTS RATHER THAN `upload_to_huggingface.py`. That script uploads a
FILTER PACKAGE — it reads `config.yaml`, `training_metadata.json` and
`training_history.json` and builds a model card from them. These eleven files are
not a filter package: they are experiment artifacts, four of them named after
production filters while matching the sha256 of no shipped artifact.

⛔ WHY NOT GIT. Owner decision, 2026-09-05. The repo keeps model weights out of git as
large checkpoints (`.gitignore` § *Model checkpoints (large files)*) and probes are model artifacts, so the same
argument applies. ⚠️ The first version of this docstring cited llm-distillery#97 for that
rule; #97 is the TDM assessment and says nothing about it. Corrected the same day. The Hub is
the path this project already uses for them, it keeps the git policy intact, and
it gives the committed manifest a durable address to point at. Before this they
lived only in an untracked home directory on one non-production box — rescued
from `/tmp` on a machine with 36 days of uptime, one reboot from gone.

⚠️ WHAT IS UPLOADED, AND IT IS ELEVEN NOT NINE. Two of the eleven are already in
git byte-identically under different names (`embedding_probe_e5small.pkl` is
`nature_recovery v4`'s shipped probe; `probe_v2.pkl` is `human_thriving v8`'s).
They go too, so the archive is self-contained and `sha256sum -c` can verify the
whole set against the committed manifest — but the README says which two, so
nobody treats the Hub copy as the source of record for a shipped artifact.

    PYTHONPATH=. python scripts/deployment/upload_probes_to_huggingface.py \
        --src <dir of .pkl> --manifest docs/evidence/2026-09-05-scorer-device-throughput/rescued_probes_manifest.txt \
        --repo-name jeergrvgreg/llm-distillery-probes

⛔ The token comes from `config/credentials/secrets.ini` and is NEVER printed.
⛔ Every file is sha256-verified against the manifest BEFORE anything is uploaded;
a mismatch aborts. Uploading bytes nobody checked would defeat the manifest.
"""
import argparse
import configparser
import hashlib
import sys
from pathlib import Path


def read_manifest(path):
    """{filename: (sha256, size, objective, encoder, seed, device, dims, in_git)}"""
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        if len(p) < 9:
            raise SystemExit(f"manifest row has {len(p)} columns, expected 9: {line[:80]}")
        rows[p[2]] = (p[0], int(p[1]), p[3], p[4], p[5], p[6], p[7], p[8])
    if not rows:
        raise SystemExit(f"{path} yielded 0 rows — refusing to upload against an "
                         f"empty manifest, which would verify nothing")
    return rows


def card(rows):
    body = [
        "---", "library_name: sklearn", "tags: [llm-distillery, e5, probe]",
        "---", "", "# llm-distillery — rescued e5 probes", "",
        "Stage-1 embedding probes from the `human_thriving v8` work "
        "(`EXP-016`/`EXP-018`/`EXP-019`/`EXP-024`) plus older per-filter probes.",
        "**Private, and not a deployment surface** — production filters load the probe "
        "committed inside their own package, never this repo.", "",
        "⛔ **Four files are named after production filters and are NOT those filters' "
        "shipped probes.** `probe_belonging_v1_recall`, "
        "`probe_cultural_discovery_v5_recall`, `probe_investment_risk_v6_recall` and "
        "`probe_uplifting_v7_recall` match the sha256 of no tracked artifact and carry "
        "the older metadata format (no seed, no device, no encoder). They are "
        "precursors or re-trainings. A name is an assertion; do not substitute one for "
        "a shipped probe.", "",
        "⚠️ Two files ARE byte-identical to committed artifacts and are marked below.",
        "", "| file | objective | encoder | seed | device | dims | also in git |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in sorted(rows):
        sha, size, obj, enc, seed, dev, dims, git = rows[name]
        body.append(f"| `{name}` | {obj} | {enc} | {seed} | {dev} | {dims} | "
                    f"{'`' + git + '`' if git != '-' else '—'} |")
    body += [
        "", "## Provenance and its limit", "",
        "Rescued 2026-09-05 from `b650-gpu:/tmp`, which does not survive a reboot, on a "
        "box with 36 days of uptime. They were found only after a review pointed out "
        "that a `find` rooted at `filters/**` could not reach `/tmp` — which is how the "
        "source document came to claim the e5-large probe had never been retained.", "",
        "⛔ **The bytes are pinned; the RUN that produced each is not.** `objective`, "
        "`embedding_model`, `seed` and `device` above are read from each pickle's own "
        "`metrics` key, so the recall/regression pair at 1024 dims is now unambiguous — "
        "but which training invocation wrote which file rests on evidence outside this "
        "repo (`b650-gpu:~/llm-distillery/logs/exp019_dump.log`).", "",
        "⚠️ `probe_seed42.pkl` and `probe_v2.pkl` report identical metrics at different "
        "sha256 — consistent with the 2026-09-04 finding that two seed-42 runs differ "
        "in 134 of 541,144 pickle bytes (torch storage keys) while every tensor is "
        "identical. Not re-verified tensor-by-tensor.", "",
        "## Verify", "",
        "```bash", "sha256sum -c rescued_probes_manifest.txt   # from the download dir",
        "```", "",
        "The manifest is committed at "
        "`docs/evidence/2026-09-05-scorer-device-throughput/rescued_probes_manifest.txt` "
        "in `veen-systems/llm-distillery`, and is the source of record for these hashes.",
    ]
    return "\n".join(body) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--repo-name", required=True)
    ap.add_argument("--secrets", type=Path,
                    default=Path("config/credentials/secrets.ini"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = read_manifest(args.manifest)
    files = sorted(args.src.glob("*.pkl"))
    if not files:
        raise SystemExit(f"no .pkl under {args.src} — nothing to upload")

    # ⛔ VERIFY BEFORE UPLOADING, BOTH DIRECTIONS. A file present but unlisted is as
    # much a defect as a listed file that is absent: the manifest is the only thing
    # that says what this set IS.
    missing = sorted(set(rows) - {f.name for f in files})
    extra = sorted({f.name for f in files} - set(rows))
    if missing or extra:
        raise SystemExit(f"manifest/disk disagree — missing {missing}, unlisted {extra}")
    for f in files:
        b = f.read_bytes()
        sha, size = rows[f.name][0], rows[f.name][1]
        got = hashlib.sha256(b).hexdigest()
        if got != sha or len(b) != size:
            raise SystemExit(f"{f.name}: sha256 {got[:16]} / {len(b)} B against the "
                             f"manifest's {sha[:16]} / {size} B — aborting")
    print(f"verified {len(files)} files against {args.manifest}")

    readme = args.src / "README.md"
    readme.write_text(card(rows), encoding="utf-8")
    manifest_copy = args.src / args.manifest.name
    manifest_copy.write_text(args.manifest.read_text(encoding="utf-8"), encoding="utf-8")

    if args.dry_run:
        print(f"DRY RUN — would upload {len(files) + 2} files to "
              f"{args.repo_name} (private)")
        return 0

    cfg = configparser.ConfigParser()
    cfg.read(args.secrets)
    token = cfg.get("api_keys", "huggingface_token", fallback="").strip()
    if not token:
        raise SystemExit(f"no huggingface_token in {args.secrets}")

    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.create_repo(args.repo_name, repo_type="model", private=True, exist_ok=True)
    api.upload_folder(folder_path=str(args.src), repo_id=args.repo_name,
                      repo_type="model", allow_patterns=["*.pkl", "*.md", "*.txt"])
    listed = api.list_repo_files(args.repo_name, repo_type="model")
    info = api.repo_info(args.repo_name, repo_type="model")
    print(f"uploaded to https://huggingface.co/{args.repo_name} (private={info.private})")
    print(f"repo now holds {len(listed)} files: {sorted(listed)}")
    absent = sorted(set(rows) - set(listed))
    if absent:
        print(f"FAIL: {len(absent)} manifest files are NOT in the repo: {absent}")
        return 1
    print(f"PASS all {len(rows)} manifest files present on the Hub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
