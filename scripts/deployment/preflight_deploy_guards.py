#!/usr/bin/env python3
"""Pre-flight guards for the llm-distillery -> NexusMind deploy path.

Why this exists (2026-08-12). Three defects found in one session, none of which a
document prevented, and one of which a document had already described verbatim in
the caller's own header:

  1. `.nexusmind-owns` cannot protect anything under `filters/{name}/v{N}/` —
     Step 1 of the caller is an unconditional `cp -r` that never reads the
     manifest. An entry naming a per-filter path is ACCEPTED and does NOTHING.
     Silent success is the defect; documentation cannot fix a silent success.
  2. `cultural_discovery` v5 and v6 shipped with no `scoring.tiers` block. No
     SCORING code reads it (NexusMind's `production_scorer.py:142` takes the
     op-point from `base.TIER_THRESHOLDS`), but eight llm-distillery tools do —
     see `check_tiers_documented`. An absent block returns None/{} rather than
     redirecting, and one cross-language study silently dropped the filter and
     reported `visible% = 0.0` for every cohort: a wrong answer shaped like a
     finding.
  3. NexusMind's `filter_loader._find_latest_version()` selects the highest `vN`
     directory on disk. So there is NO VERSION-SELECTION STEP anywhere: nothing
     names the version, and a new highest `vN` activates itself.
     ⚠️ Scoped precisely, because an earlier version of this text said "the deploy
     and the cutover are the same keystroke" and that is FALSE. The canonical
     chain (`docs/FILTER_PLAYBOOK.md` §"Deploy safety checklist") is
     **llm-distillery git -> NexusMind git -> sadalsuud `deploy_filters.sh` ->
     gpu-server**, and `NexusMind/scripts/deploy_filters.sh` ships `git archive
     HEAD` (never the working tree), hard-exits on uncommitted or untracked
     scorer-tree files, then rsyncs and restarts. So landing a directory in the
     NexusMind checkout does NOT reach readers. What is missing is any step that
     would make someone *choose* the version — so once it ships, it serves.

The rule this encodes: a guard that fails beats a comment that explains. See
`memory/gotcha-log.md`, entries dated 2026-08-12.

SCOPE, stated because an earlier version of this docstring overclaimed it: these
guards run from `deploy_to_nexusmind.sh` AND `deploy_to_nexusmind.ps1`. Any other
route that copies a filter directory into NexusMind bypasses them.

Exit codes: 0 = all guards pass, 1 = a guard failed (deploy must abort),
2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

# The manifest is consulted ONLY while copying filters/common/. Expressed as an
# allowlist rather than a denylist: an earlier denylist version accepted Windows
# separators, `src/...` paths and `docs/...` paths, all of which protect nothing.
_MANIFEST_HONOURED_RE = re.compile(r"^filters/common/.+")
_VERSION_DIR_RE = re.compile(r"^v(\d+)$")


class GuardFailure(Exception):
    """A guard that must abort the deploy."""


def _fail(msg: str) -> None:
    raise GuardFailure(msg)


# --- Guard A ----------------------------------------------------------------


def check_manifest_scope(manifest_path: Path) -> list[str]:
    """Reject `.nexusmind-owns` entries the manifest step will never read.

    `.nexusmind-owns` is consulted ONLY when copying `filters/common/`. Any other
    entry looks accepted and protects nothing, so a NexusMind-side edit is
    overwritten with no conflict and no warning. Erroring here converts a silent
    no-op into a loud failure at the moment someone reaches for the wrong tool.

    The comparison mirrors the CONSUMER's, which does an exact string match
    against a `filters/common/`-relative path — so a leading `./` or a backslash
    separator is rejected rather than normalised away. A guard more permissive
    than its consumer certifies entries the consumer ignores.
    """
    if not manifest_path.exists():
        return ["manifest absent — nothing to check"]

    offenders: list[tuple[str, str]] = []
    entries = 0
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        entry = raw.split("#", 1)[0].strip()
        if not entry:
            continue
        entries += 1
        if "\\" in entry:
            offenders.append((entry, "backslash separator — the consumer compares POSIX paths"))
        elif entry.startswith("./"):
            offenders.append((entry, "leading './' — the consumer does an exact string match"))
        elif not _MANIFEST_HONOURED_RE.match(entry):
            offenders.append((entry, "not under filters/common/ — the manifest step never sees it"))

    if offenders:
        _fail(
            "`.nexusmind-owns` names path(s) it CANNOT protect:\n"
            + "".join(f"    {e}\n        {why}\n" for e, why in offenders)
            + "  The manifest is read ONLY when copying filters/common/. Step 1 is an\n"
            "  unconditional `cp -r` of the filter directory and never consults it, so\n"
            "  a per-filter entry silently protects nothing and the NexusMind-side copy\n"
            "  WILL be overwritten.\n"
            "  Fix: edit the llm-distillery copy and deploy. Never edit the NexusMind\n"
            "  copy of a per-filter file, and do not add it here expecting protection."
        )

    return [f"manifest scope OK ({entries} entr{'y' if entries == 1 else 'ies'})"]


# --- Guard B ----------------------------------------------------------------


def _runtime_tiers(base_scorer: Path) -> dict[str, float]:
    """Parse TIER_THRESHOLDS via AST, collecting EVERY assignment.

    Deliberately mirrors `scripts/normalization/fit_normalization.py`'s approach
    rather than regex-matching. A regex takes whichever block appears first, so a
    file with a legacy/experimental class above the live one — or a subclass
    overriding its parent — resolves silently to the wrong constant, and this
    guard would then bless a config mirroring a DEAD op-point. Ambiguity must
    fail closed, not pick.
    """
    try:
        tree = ast.parse(base_scorer.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        _fail(f"{base_scorer} does not parse: {exc}")

    found: list[dict[str, float]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == "TIER_THRESHOLDS"):
                continue
            try:
                literal = ast.literal_eval(node.value)
                found.append({t[0]: float(t[1]) for t in literal})
            except (ValueError, SyntaxError, TypeError, KeyError, IndexError) as exc:
                _fail(
                    f"{base_scorer}: TIER_THRESHOLDS is not a readable literal "
                    f"({type(exc).__name__}). Refusing to guess."
                )

    if not found:
        _fail(
            f"{base_scorer} declares no TIER_THRESHOLDS block.\n"
            "  That constant is the SOLE runtime source of the op-point "
            "(NexusMind production_scorer.py:142 reads base.TIER_THRESHOLDS)."
        )
    if len(found) > 1 and any(f != found[0] for f in found[1:]):
        _fail(
            f"{base_scorer} contains MULTIPLE differing TIER_THRESHOLDS definitions:\n"
            + "".join(f"    {f}\n" for f in found)
            + "  Refusing to guess which one runs — collapse them to one.\n"
            "  (A legacy class above the live one, or a subclass overriding its\n"
            "  parent, would otherwise be blessed as 'what actually runs'.)"
        )
    if not found[0]:
        _fail(f"{base_scorer}: TIER_THRESHOLDS parsed as EMPTY. Refusing to compare.")
    return found[0]


def check_tiers_documented(filter_dir: Path) -> list[str]:
    """config.yaml's `scoring.tiers` must mirror base_scorer.py's TIER_THRESHOLDS.

    ⚠️ This is NOT cosmetic and NOT "documentation only" — a claim an earlier
    version of this module printed, and which was refuted by measurement on
    2026-08-12. No PRODUCTION SCORING code reads the block, but at least eight
    llm-distillery tools do:

        scripts/normalization/fit_normalization.py   (op-point cross-check)
        scripts/gate/ground_truth_gate.py            (ADR-021 gate threshold)
        scripts/calibration/fit_calibration.py
        scripts/train_scope_probe.py
        training/prepare_data.py                     (train/val/test STRATIFICATION)
        evaluation/calibrate_hybrid_threshold.py
        experiments/evaluate_models.py
        filters/uplifting/v1/postfilter.py

    Measured consequence of adding the block to cultural_discovery:
    `prepare_data.extract_filter_info` goes `tier_boundaries={}` ->
    `{'high':7.0,'medium':4.0,'low':0.0}`, flipping `use_score_bins` True->False,
    i.e. future splits stratify by TIER instead of score bins. Several other
    consumers were unaffected only because cd's op-point is 4.0 and their
    fallbacks are hardcoded 4.0 — a coincidence of value, not a property of the
    change. On nature_recovery (3.75), investment_risk (4.25), uplifting (4.5) or
    solutions (2.25) the same edit WOULD move the ADR-021 gate threshold.
    """
    config_path = filter_dir / "config.yaml"
    base_scorer = filter_dir / "base_scorer.py"
    if not config_path.exists():
        _fail(f"{config_path} not found")
    if not base_scorer.exists():
        return [f"no base_scorer.py in {filter_dir.name} — tier check skipped"]

    runtime = _runtime_tiers(base_scorer)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    tiers = ((config.get("scoring") or {}).get("tiers")) or {}

    if not tiers:
        _fail(
            f"{config_path} has no `scoring.tiers` block, but "
            f"{base_scorer.name} declares {runtime}.\n"
            "  No PRODUCTION SCORING code reads this block — production is fine.\n"
            "  But eight llm-distillery tools do (fit_normalization,\n"
            "  ground_truth_gate, prepare_data, fit_calibration, train_scope_probe,\n"
            "  calibrate_hybrid_threshold, evaluate_models, uplifting v1 postfilter),\n"
            "  and an absent block yields {} rather than redirecting: a cross-language\n"
            "  study silently dropped cultural_discovery and reported visible%=0.0 for\n"
            "  every cohort (2026-08-12).\n"
            "  Fix: mirror the TIER_THRESHOLDS values into scoring.tiers.\n"
            "  ⚠️ This is NOT a no-op — it changes train/val/test stratification in\n"
            "  prepare_data.py, and if the values disagree it would move the ADR-021\n"
            "  gate threshold. Mirror EXACTLY."
        )
    if not isinstance(tiers, dict):
        _fail(f"{config_path}: `scoring.tiers` is {type(tiers).__name__}, expected a mapping")

    documented: dict[str, float] = {}
    malformed: list[str] = []
    for name, spec in tiers.items():
        if isinstance(spec, dict):
            if "threshold" not in spec:
                malformed.append(f"{name} (dict without a `threshold:` key)")
                continue
            value = spec["threshold"]
        else:
            value = spec
        try:
            documented[name] = float(value)
        except (TypeError, ValueError):
            malformed.append(f"{name} (threshold {value!r} is not a number)")

    if malformed:
        _fail(
            f"{config_path}: `scoring.tiers` entries are malformed: {', '.join(malformed)}.\n"
            "  A tier without a usable threshold is skipped silently by the consumers,\n"
            "  which is how a declared-but-nonexistent tier (investment_risk v6's\n"
            "  `medium_high: 5.0`) survived. Every tier needs a numeric threshold."
        )

    if set(documented) != set(runtime):
        _fail(
            f"`scoring.tiers` in {config_path.name} declares a DIFFERENT SET of tiers "
            f"than {base_scorer.name}:\n"
            f"    config.yaml   : {sorted(documented)}\n"
            f"    base_scorer.py: {sorted(runtime)}   <-- what actually runs\n"
            "  Extra tiers here are the investment_risk v6 `medium_high: 5.0` defect."
        )
    if documented != runtime:
        _fail(
            f"`scoring.tiers` in {config_path.name} DISAGREES with "
            f"{base_scorer.name}'s TIER_THRESHOLDS:\n"
            f"    config.yaml   : {documented}\n"
            f"    base_scorer.py: {runtime}   <-- what actually runs\n"
            "  The module wins at runtime, so this block is actively misleading —\n"
            "  and it is READ by the ADR-021 gate and the split stratifier.\n"
            "  ⚠️ If you intend to MOVE the op-point, it lives in four places and all\n"
            "  four change in one commit: base_scorer.py TIER_THRESHOLDS, this block,\n"
            "  normalization.json stats.raw_min, and tests/unit/"
            "test_normalization_op_point.py — then refit normalization."
        )

    op_point = min((t for t in runtime.values() if t > 0), default=0.0)
    return [f"tiers documented and matching (op-point {op_point})"]


# --- Guard C ----------------------------------------------------------------


def check_cutover(filter_name: str, version: str, nexusmind_root: Path) -> list[str]:
    """Report — and where unambiguous, REFUSE — based on what this deploy becomes.

    NexusMind's `filter_loader._find_latest_version()` picks the highest vN on
    disk, so landing a new highest version makes it live on the next load. There
    is no separate cutover step to review it at.

    Deploying BELOW the current highest is refused outright: `_find_latest_version`
    will keep serving the higher one, so the deploy provably does nothing while
    reporting success — which is the silent-success class this module exists for.
    """
    if not nexusmind_root.is_dir():
        _fail(
            f"NEXUSMIND_ROOT does not exist: {nexusmind_root}\n"
            "  Refusing to continue. Without this check a typo'd root produced a\n"
            "  confident 'this deploy CREATES the filter' and then `mkdir -p`'d a\n"
            "  bogus tree and deployed into nowhere."
        )

    m = _VERSION_DIR_RE.match(version)
    if not m:
        _fail(f"version {version!r} is not vN-shaped — cannot reason about the cutover")
    incoming = int(m.group(1))

    dest_parent = nexusmind_root / "filters" / filter_name
    if not dest_parent.exists():
        return [
            f"NexusMind has no {filter_name} yet — this deploy CREATES it,",
            "    and it will be served on the next load.",
        ]

    existing = [
        int(mm.group(1))
        for child in dest_parent.iterdir()
        if child.is_dir() and (mm := _VERSION_DIR_RE.match(child.name))
    ]
    if not existing:
        return [f"no existing versions in NexusMind — {version} becomes live on arrival"]

    highest = max(existing)
    if incoming < highest:
        _fail(
            f"{version} is BELOW NexusMind's highest (v{highest}).\n"
            f"  filter_loader._find_latest_version() will keep serving v{highest}, so this\n"
            "  deploy would change nothing while reporting success — and would then\n"
            "  commit (and with --push, push) that no-op.\n"
            f"  If you mean to roll back, remove v{highest} from NexusMind explicitly."
        )
    if incoming == highest:
        return [f"replacing {version} in place (already the highest) — live immediately"]
    return [
        "*** THIS DEPLOY STARTS A VERSION CUTOVER ***",
        f"    NexusMind currently serves v{highest}; you are landing {version}.",
        "    filter_loader._find_latest_version() selects the HIGHEST vN on disk, so",
        "    NOTHING will ever name this version: there is no activation step to",
        "    forget and no config flip to review. It serves as soon as it ships.",
        "    It is not live yet — sadalsuud's NexusMind/scripts/deploy_filters.sh",
        "    still has to `git archive HEAD` and rsync to gpu-server (it refuses on",
        "    uncommitted/untracked scorer files). That run is the last checkpoint.",
        f"    Before it: confirm ACTIVE_FILTERS in tests/unit/test_filter_config_schema.py",
        f"    names ({filter_name}, {version}) — it is updated by hand, and the last",
        "    time it lagged, drift in the deployed version went unseen for 6 weeks.",
    ]


# --- Guard D ----------------------------------------------------------------


class ProbeUnavailable(Exception):
    """The weights probe could not reach gpu-server. Not the same as 'absent'."""


DEFAULT_GPU_HOST = "gpu-server"
GPU_FILTERS_ROOT = "~/NexusMind/filters"
_ADAPTER_NAME = "adapter_model.safetensors"


def _ssh_weights_probe(gpu_host: str, filter_name: str, version: str, timeout: int = 20) -> bool:
    """Ask gpu-server whether the LoRA adapter for this version is on disk.

    Returns True/False. Raises ProbeUnavailable when the question could not be
    ASKED — a transport failure must never read as "weights are present", and
    must not read as "absent" either: those are different facts with different
    remedies, and collapsing them is how a guard ends up firing on a VPN blip.
    """
    import subprocess

    remote = (
        f'test -f {GPU_FILTERS_ROOT}/{filter_name}/{version}/model/{_ADAPTER_NAME} '
        f'&& echo PRESENT || echo ABSENT'
    )
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o", "BatchMode=yes",
                "-o", f"ConnectTimeout={timeout}",
                gpu_host,
                remote,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeUnavailable(f"{type(exc).__name__}: {exc}") from exc

    answer = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    if proc.returncode != 0 or answer not in ("PRESENT", "ABSENT"):
        raise ProbeUnavailable(
            f"ssh {gpu_host} exit={proc.returncode} stdout={proc.stdout.strip()!r} "
            f"stderr={proc.stderr.strip()[:200]!r}"
        )
    return answer == "PRESENT"


# --- Guard E ----------------------------------------------------------------


def check_weights_backed_up(filter_dir: Path) -> list[str]:
    """Refuse to ship a version whose weights exist nowhere Veen-owned and backed up.

    Found 2026-08-13, by an infra session inventorying a machine for disaster
    recovery rather than by anyone here. THREE of six live filters —
    `cultural_discovery`, `investment_risk v6`, `belonging v1` — had no local
    copy of their adapter at all. Their only homes were gpu-server (employer
    hardware, outside our control) and a private Hub repo behind a single
    account. Losing that account would not have stopped scoring; it would have
    removed the way back.

    The reason nobody noticed is the reason this has to be a guard rather than a
    note: `filters/**/model/` is gitignored, so the weights are invisible to
    `git status`, to a repo grep, and to any inventory built from the index.
    Two separate sessions searched for them and concluded they were absent. The
    backup walks the filesystem, which is why the *other* four filters were
    protected — **by accident, not by decision.**

    That accident is what this guard replaces. Without it, a version trained
    tomorrow is off-site only if someone remembers, and the evidence says nobody
    does: the three gaps above were created by exactly that.

    Scope, stated because it is narrow: this checks that a copy exists on THIS
    machine, in the tree the backup covers. It cannot verify the backup ran —
    that is `restic ls latest` and it lives on the infra side. A local file is a
    precondition for off-site, not a proof of it.
    """
    adapter = filter_dir / "model" / _ADAPTER_NAME
    if adapter.is_file() and adapter.stat().st_size > 0:
        mb = adapter.stat().st_size / (1024 * 1024)
        return [f"weights present locally for backup ({mb:.0f} MB) — {adapter}"]

    if adapter.is_file():
        _fail(
            f"{adapter} exists but is EMPTY.\n"
            "  A zero-length adapter is worse than an absent one: it satisfies every\n"
            "  presence check and restores as a corrupt model. Re-download it."
        )

    _fail(
        f"no local copy of this version's weights: {adapter}\n"
        "  The deploy would ship a version whose adapter exists only on gpu-server\n"
        "  (employer hardware) and in a private Hub repo behind one account —\n"
        "  no Veen-owned copy, and nothing in the off-site backup, which covers this\n"
        "  tree but is blind to anything not on this disk.\n"
        "  ⚠️ `git status` will NOT show this, and neither will a repo grep:\n"
        "  filters/**/model/ is gitignored by design. `ls -l` on the path above is\n"
        "  the check that discriminates.\n"
        "  Fix — pull from the Hub, which keeps the recovery chain Veen-owned:\n"
        "    python -c \"from huggingface_hub import hf_hub_download as d; \\\n"
        "      [d(repo_id='jeergrvgreg/<repo>', filename=f, local_dir='<filter_dir>/model') \\\n"
        "       for f in ['adapter_model.safetensors','adapter_config.json',\n"
        "                 'tokenizer.json','tokenizer_config.json']]\"\n"
        "  Then delete the .cache/ directory it leaves behind — mirror the artifact,\n"
        "  not the HF cache layout."
    )


def check_weights_channel(
    filter_name: str,
    version: str,
    *,
    probe=None,
    preplaced_ack: bool = False,
    gpu_host: str = DEFAULT_GPU_HOST,
) -> list[str]:
    """Refuse a deploy whose served version has no LoRA weights on gpu-server.

    This turns `docs/FILTER_PLAYBOOK.md` checklist item 5 — *"Pre-place `model/`
    on gpu-server before `deploy_filters.sh`"* — from an instruction into a
    check. The instruction has existed since llm-distillery#67 was closed, and
    #67 was itself filed AFTER the omission took cultural_discovery v5 down on
    2026-05-31. A documented step that has already been missed once is the
    definition of what belongs in this module.

    Why weights cannot ride along with the code: `NexusMind/scripts/deploy_filters.sh`
    rsyncs `filters/` to gpu-server with `--exclude='model/'`, deliberately — the
    adapters are multi-GB and out-of-git, and `--delete` without that exclude
    would WIPE gpu-server's only copy. Both rsync passes exclude it. So a code
    deploy NEVER carries weights, for any version, ever.

    Why the consequence is worse than in 2026-05-31: the check moved from first
    scoring request to scorer STARTUP, and it iterates every discovered filter
    (`nexusmind-scorer/main.py`, `#incident-2026-04-13`):

        for name, cfg in state._filter_configs.items():
            adapter = cfg["path"] / "model" / "adapter_model.safetensors"
            ... raise RuntimeError("Cannot start scorer: ... missing model weights")

    `cfg["path"]` is the version `_find_latest_version()` selected. So a weightless
    highest version does not degrade one filter — the scorer never comes up and
    the cycle scores NOTHING for all six. And nobody is watching when it happens:
    `deploy_filters.sh` runs as `ExecStartPre` on `nexusmind.service`, unattended,
    every four hours.

    The check applies to Hub-backed filters too. The startup validation is a
    plain disk check and does not care that the scorer would have loaded from the
    Hub, so "it's on the Hub" does not make the local adapter optional.

    `probe` is injected so this is testable without a network; `preplaced_ack`
    is the documented override for the offline case. Being unable to ask fails
    CLOSED — see ProbeUnavailable.
    """
    if preplaced_ack:
        return [
            "weights probe SKIPPED — operator asserted --weights-preplaced.",
            f"    Nothing verified {filter_name}/{version}/model/{_ADAPTER_NAME} on {gpu_host}.",
            "    If that assertion is wrong the scorer will not start and the cycle",
            "    scores nothing for every filter, not just this one.",
        ]

    probe = probe or _ssh_weights_probe
    try:
        present = probe(gpu_host, filter_name, version)
    except ProbeUnavailable as exc:
        _fail(
            f"could not ask {gpu_host} whether {filter_name}/{version} has weights: {exc}\n"
            "  Failing CLOSED: 'unreachable' is not 'present'. The deploy path never\n"
            "  ships model/ (deploy_filters.sh excludes it in both rsync passes), so a\n"
            "  weightless highest version stops the scorer from STARTING — all six\n"
            "  filters score nothing, unattended, on the next 4-hourly cycle.\n"
            "  Either fix connectivity and re-run, or pass --weights-preplaced once you\n"
            "  have confirmed by hand:\n"
            f"    ssh {gpu_host} 'ls -l {GPU_FILTERS_ROOT}/{filter_name}/{version}/model/{_ADAPTER_NAME}'"
        )

    if not present:
        _fail(
            f"{gpu_host} has NO weights for {filter_name}/{version}:\n"
            f"    {GPU_FILTERS_ROOT}/{filter_name}/{version}/model/{_ADAPTER_NAME} is absent.\n"
            "  This deploy would ship the code without them — deploy_filters.sh excludes\n"
            "  model/ from BOTH rsync passes, so nothing downstream will fill the gap.\n"
            "  The scorer validates weights for every discovered filter at STARTUP, so it\n"
            "  would refuse to start and the whole cycle would score nothing.\n"
            "  Fix (FILTER_PLAYBOOK checklist item 5, llm-distillery#67): pre-place the\n"
            "  adapter FIRST, then deploy:\n"
            f"    ssh {gpu_host} 'mkdir -p {GPU_FILTERS_ROOT}/{filter_name}/{version}/model'\n"
            f"    scp <adapter dir>/* {gpu_host}:{GPU_FILTERS_ROOT}/{filter_name}/{version}/model/"
        )

    return [f"weights present on {gpu_host} for {filter_name}/{version}"]


def build_parser() -> argparse.ArgumentParser:
    """Exposed so the caller-parity test can DERIVE the flag set rather than
    restate it. A hardcoded copy in the test would be a second place to update,
    and the defect it guards against is exactly two places disagreeing."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--filter-name", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--distillery-root", required=True, type=Path)
    ap.add_argument("--nexusmind-root", required=True, type=Path)
    ap.add_argument(
        "--gpu-host",
        default=DEFAULT_GPU_HOST,
        help="ssh host that serves the scorer (default: %(default)s)",
    )
    ap.add_argument(
        "--weights-preplaced",
        action="store_true",
        help=(
            "Assert by hand that the LoRA adapter is already on the GPU host, "
            "skipping the probe. For the offline case only — a wrong assertion "
            "stops the scorer from starting and the cycle scores nothing."
        ),
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    filter_dir = args.distillery_root / "filters" / args.filter_name / args.version
    if not filter_dir.is_dir():
        print(f"ERROR: filter directory not found: {filter_dir}", file=sys.stderr)
        return 2

    failures: list[str] = []
    for label, fn in (
        ("manifest scope", lambda: check_manifest_scope(args.distillery_root / ".nexusmind-owns")),
        ("tier documentation", lambda: check_tiers_documented(filter_dir)),
        ("cutover", lambda: check_cutover(args.filter_name, args.version, args.nexusmind_root)),
        ("weights backed up", lambda: check_weights_backed_up(filter_dir)),
        (
            "weights channel",
            lambda: check_weights_channel(
                args.filter_name,
                args.version,
                preplaced_ack=args.weights_preplaced,
                gpu_host=args.gpu_host,
            ),
        ),
    ):
        try:
            for note in fn():
                print(f"   [{label}] {note}")
        except GuardFailure as exc:
            failures.append(f"   [{label}] FAILED: {exc}")

    if failures:
        print("")
        for f in failures:
            print(f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
