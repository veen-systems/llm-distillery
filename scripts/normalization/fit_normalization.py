"""
Fit cross-filter percentile normalization from production data (ADR-014).

Reads raw_weighted_average scores from NexusMind filtered output, filters
by score threshold (the filter's operating point), fits a percentile CDF,
and saves normalization.json to the filter directory.

The score threshold is resolved from the filter's operating point rather than
being a free parameter — see `resolve_op_point()`. Fitting below the op-point
is what caused NexusMind#161: nature_recovery v2's CDF was fitted at
raw >= 1.5, giving the fit set a median of 2.19, so correctly-scored doom
articles (raw 2.2-3.3) mapped to normalized 5.2-8.3 and reached the
visibility band. The model was right; the fit threshold put it on screen.

The CDF's lower edge is ANCHORED to the operating point (2026-07-16): the
lookup table is extended down to it, so stats.raw_min == op_point by
construction, dense or sparse. Sparse fits can no longer drift raw_min upward
into the band NexusMind#205 lives in, and the repo invariant
(tests/unit/test_normalization_invariant.py) can assert near-equality.

Usage:
    # From local JSONL files (e.g., after scp from sadalsuud)
    PYTHONPATH=. python scripts/normalization/fit_normalization.py \
        --filter filters/nature_recovery/v1 \
        --data-dir /path/to/filtered/nature_recovery

    # From sadalsuud directly via SSH
    PYTHONPATH=. python scripts/normalization/fit_normalization.py \
        --filter filters/nature_recovery/v1 \
        --ssh sadalsuud \
        --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/nature_recovery
"""

import argparse
import ast
import json
import logging
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from filters.common.score_normalization import fit_normalization, save_normalization

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Mirrors of the CONSUMER's guards in NexusMind src/scoring/production_scorer.py.
# A fit that production will reject is worse than no fit: the operator sees
# "Normalization fitted on N articles" plus a sample-mapping table, believes
# percentile normalization is live, and it silently is not — ProductionScorer
# falls back to the linear score_scale_factor at load. Keep these in step with
# NexusMind; if they drift, this script cheerfully produces dead files.
MIN_NORMALIZATION_ARTICLES = 200   # ADR-018 safety valve; below this the CDF is sampling noise
MAX_NORMALIZATION_RAW_MIN = 4.5    # NexusMind#205: the loader REJECTS files whose raw_min exceeds this

# How far stats.raw_min may sit from the operating point. Since 2026-07-16 the
# fitter anchors the CDF's lower edge to the op-point (fit_normalization's
# anchor_min), so new fits satisfy raw_min == op_point EXACTLY; this epsilon
# only absorbs float round-tripping plus the pre-anchor legacy fits, whose
# raw_min is the sample minimum and lands within +0.0006 of the op-point on
# every conforming filter. tests/unit/test_normalization_invariant.py imports
# this value — the fitter's post-fit guard and the repo-wide invariant test
# must agree on ONE band, or the fitter writes files the test rejects (the
# round-3/round-4 inconsistency of 2026-07-16).
OP_POINT_EPS = 0.01


def _lowest_nonzero(thresholds) -> Optional[float]:
    """The operating point is the lowest threshold above 0.0 — i.e. the score at
    which an article first becomes visible. Derived positionally rather than by
    tier name, because names vary across filters (sustainability_technology uses
    medium/medium_high/high_sustainability, not high/medium/low)."""
    nonzero = [t for t in thresholds if isinstance(t, (int, float)) and t > 0]
    return min(nonzero) if nonzero else None


def _op_point_from_base_scorer(filter_dir: Path) -> Optional[float]:
    """Read TIER_THRESHOLDS out of base_scorer.py without importing it.

    base_scorer imports torch (via filters.common.filter_base_scorer), which
    isn't installed on the workstation where this script runs — so parse the
    literal instead of importing the module.
    """
    path = filter_dir / "base_scorer.py"
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None

    # Collect EVERY TIER_THRESHOLDS assignment, not the first ast.walk happens to
    # yield. A file with two (a legacy/experimental class above the live one, or a
    # subclass overriding its parent) would otherwise resolve silently to whichever
    # came first — and the guard could not catch it, because it compares --min-score
    # against that same wrong value. Ambiguity must fail closed, not pick.
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == "TIER_THRESHOLDS"):
                continue
            try:
                tiers = ast.literal_eval(node.value)
                # Indexing belongs inside the guard: TIER_THRESHOLDS reshaped to
                # dicts (mirroring config.yaml) or bare floats raises TypeError /
                # KeyError here, and an uncaught traceback is not the documented
                # "degrade to None" contract.
                thresholds = [t[1] for t in tiers]
            except (ValueError, SyntaxError, TypeError, KeyError, IndexError):
                return None
            op = _lowest_nonzero(thresholds)
            if op is not None:
                found.append(op)

    if not found:
        return None
    if len(set(found)) > 1:
        logger.error(
            f"Ambiguous operating point: {path} contains multiple TIER_THRESHOLDS "
            f"definitions resolving to different values {sorted(set(found))}. Refusing "
            f"to guess — pass --min-score explicitly, or collapse them to one."
        )
        return None
    return found[0]


def _op_point_from_config(config: dict) -> Optional[float]:
    scoring = config.get("scoring") or {}
    tiers = scoring.get("tiers") or scoring.get("tier_thresholds") or {}
    if not isinstance(tiers, dict):
        return None
    thresholds = []
    for spec in tiers.values():
        thresholds.append(spec.get("threshold") if isinstance(spec, dict) else spec)
    return _lowest_nonzero(thresholds)


def resolve_op_point(filter_dir: Path, config: dict) -> Optional[float]:
    """Resolve the filter's operating point (the visibility threshold).

    base_scorer.py's TIER_THRESHOLDS is the ONLY authoritative source: it is what
    the runtime actually assigns tiers from — no scoring code reads config's tiers
    section. config.yaml is documentation that must mirror it, and is used here
    solely to cross-check and report drift.

    If TIER_THRESHOLDS cannot be resolved we return None rather than falling back
    to config, because config is demonstrably unreliable: sustainability_technology
    v3 and investment_risk v6 both ship a stale `scoring.tiers` medium=3.0 against
    a live code value of 4.0. Silently adopting 3.0 as the fit floor would map the
    3.0-4.0 band — currently clamped to ~0 — into the visible band, which is
    precisely the NexusMind#161 failure this guard exists to prevent, delivered by
    the guard's own default. An earlier version of this function did exactly that,
    and its drift warning could never fire on that path (it required BOTH sources
    to be non-None). Returning None makes main() demand an explicit --min-score,
    which is the safe degradation — including under ADR-016, should tiers ever be
    dropped from the filters entirely.
    """
    from_code = _op_point_from_base_scorer(filter_dir)
    from_config = _op_point_from_config(config)

    if from_code is None:
        if from_config is not None:
            logger.warning(
                f"Could not resolve the operating point from base_scorer.py "
                f"TIER_THRESHOLDS. config.yaml says {from_config}, but config is NOT "
                f"authoritative and is known to go stale — refusing to use it as the "
                f"fit floor. Pass --min-score explicitly if {from_config} is correct."
            )
        return None

    if from_config is not None and from_code != from_config:
        logger.warning(
            f"Operating point drift: base_scorer.py TIER_THRESHOLDS says {from_code}, "
            f"config.yaml scoring.tiers says {from_config}. TIER_THRESHOLDS is the runtime "
            f"source and wins here — but fix the mismatch, one of them is a lie."
        )
    return from_code


def load_weighted_averages_local(
    data_dir: Path,
    filter_name: str,
    min_score: float,
    filter_version: str | None = None,
) -> list:
    """Load weighted averages from local filtered JSONL files."""
    was = []
    n_raw = 0
    n_fallback = 0
    n_below_threshold = 0
    n_wrong_version = 0
    n_foreign = 0
    n_nonfinite = 0
    # Match only THIS filter's attribute block. An article scored by several
    # filters carries several blocks; iterating them all blends foreign filters'
    # score distributions into the CDF whenever version strings coincide.
    # Normalize hyphen/underscore: config.yaml says "cultural-discovery" while
    # production keys say "cultural_discovery" — a strict compare would silently
    # match zero articles for those filters.
    want = filter_name.replace("-", "_")

    # Read flat JSONL files (NexusMind#144: flat output, no tier subdirs)
    jsonl_files = sorted(data_dir.glob("filtered_*.jsonl"))

    for jsonl_file in jsonl_files:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    article = json.loads(line)
                    attrs = article.get("nexus_mind_attributes", {})
                    for key, analysis in attrs.items():
                        if isinstance(analysis, dict) and "weighted_average" in analysis:
                            if key.replace("-", "_") != want:
                                n_foreign += 1
                                continue
                            # Production writes the version as "version" inside the
                            # per-filter nexus_mind_attributes block (e.g. {"version":"5.0"}).
                            # Older code/data used "filter_version"; accept either.
                            # str()-compare so "5.0" (arg) matches "5.0" (data). Bug fixed
                            # 2026-07-10: was reading only "filter_version", excluding ALL
                            # articles when --filter-version was passed (production uses "version").
                            art_ver = analysis.get("version", analysis.get("filter_version"))
                            if filter_version is not None and str(art_ver) != str(filter_version):
                                n_wrong_version += 1
                                continue
                            # Use raw_weighted_average to avoid double-normalization
                            raw = analysis.get("raw_weighted_average")
                            wa = raw if raw is not None else analysis["weighted_average"]
                            # NaN passes `wa < min_score` (False) and would count
                            # toward the article floor while fit_normalization()
                            # silently drops it — a <200-article CDF shipping under
                            # a 250-article headcount. Exclude at load.
                            if not isinstance(wa, (int, float)) or not math.isfinite(wa):
                                n_nonfinite += 1
                                continue
                            if wa < min_score:
                                n_below_threshold += 1
                                continue
                            if raw is not None:
                                n_raw += 1
                            else:
                                n_fallback += 1
                            was.append(wa)
                except (json.JSONDecodeError, KeyError):
                    continue

    if n_foreign > 0:
        logger.info(f"Excluded {n_foreign} attribute blocks belonging to other filters (matching {want!r})")
    if n_nonfinite > 0:
        logger.warning(f"Excluded {n_nonfinite} articles with non-finite/non-numeric scores")
    if n_wrong_version > 0:
        logger.info(f"Excluded {n_wrong_version} articles not matching filter_version={filter_version}")
    if n_below_threshold > 0:
        logger.info(f"Excluded {n_below_threshold} articles below min_score={min_score}")
    if n_fallback > 0 and n_raw > 0:
        logger.warning(
            f"Mixed fields: {n_raw} articles used raw_weighted_average, "
            f"{n_fallback} used weighted_average (possibly normalized). "
            f"CDF may blend raw and normalized scores."
        )
    elif n_fallback > 0:
        logger.warning(
            f"raw_weighted_average not found in any article — using weighted_average "
            f"for all {n_fallback} articles. Check for double-normalization risk."
        )
    else:
        logger.info(f"Using raw_weighted_average for all {n_raw} articles")

    return was


def load_weighted_averages_ssh(
    ssh_host: str,
    remote_dir: str,
    filter_name: str,
    min_score: float,
    filter_version: str | None = None,
) -> list:
    """Load weighted averages from a remote host via SSH."""
    # Write extraction script to temp file, scp to remote, execute, retrieve results.
    # Mirrors load_weighted_averages_local exactly — own-filter block matching
    # (hyphen/underscore-normalized) and non-finite exclusion included; keep the
    # two in step.
    script_content = """import json, glob, math, os, sys
remote_dir = sys.argv[1]
min_score = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
want = sys.argv[3].replace("-", "_") if len(sys.argv) > 3 else ""
filter_version = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
was = []
n_raw = 0
n_fallback = 0
n_below = 0
n_wrong_version = 0
n_foreign = 0
n_nonfinite = 0
# Read flat JSONL files (NexusMind#144: flat output, no tier subdirs)
files = sorted(glob.glob(os.path.join(remote_dir, "filtered_*.jsonl")))
for fp in files:
    with open(fp) as f:
        for line in f:
            try:
                d = json.loads(line)
                attrs = d.get("nexus_mind_attributes", {})
                for k, v in attrs.items():
                    if isinstance(v, dict) and "weighted_average" in v:
                        if want and k.replace("-", "_") != want:
                            n_foreign += 1
                            continue
                        if filter_version is not None and str(v.get("version", v.get("filter_version"))) != str(filter_version):
                            n_wrong_version += 1
                            continue
                        raw = v.get("raw_weighted_average")
                        wa = raw if raw is not None else v["weighted_average"]
                        if not isinstance(wa, (int, float)) or not math.isfinite(wa):
                            n_nonfinite += 1
                            continue
                        if wa < min_score:
                            n_below += 1
                            continue
                        if raw is not None:
                            n_raw += 1
                        else:
                            n_fallback += 1
                        was.append(wa)
            except Exception:
                pass
for w in was:
    print(w)
print("META:raw=%d,fallback=%d,below=%d,wrong_version=%d,foreign=%d,nonfinite=%d" % (n_raw, n_fallback, n_below, n_wrong_version, n_foreign, n_nonfinite), file=sys.stderr)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        local_script = f.name

    remote_script = "/tmp/_extract_wa.py"
    try:
        subprocess.run(["scp", local_script, f"{ssh_host}:{remote_script}"],
                       capture_output=True, timeout=30, check=True)
        ssh_args = ["ssh", ssh_host, "python3", remote_script, remote_dir, str(min_score), filter_name]
        if filter_version is not None:
            ssh_args.append(filter_version)
        result = subprocess.run(
            ssh_args,
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            logger.error(f"SSH command failed: {result.stderr}")
            sys.exit(1)
    finally:
        Path(local_script).unlink(missing_ok=True)
        subprocess.run(["ssh", ssh_host, "rm", "-f", remote_script],
                       capture_output=True, timeout=15)

    was = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            was.append(float(line))

    # Parse field-usage metadata from remote script stderr
    import re
    meta_match = re.search(
        r"META:raw=(\d+),fallback=(\d+),below=(\d+),wrong_version=(\d+),foreign=(\d+),nonfinite=(\d+)",
        result.stderr or "",
    )
    if meta_match:
        n_raw = int(meta_match.group(1))
        n_fallback = int(meta_match.group(2))
        n_below = int(meta_match.group(3))
        n_wrong_version = int(meta_match.group(4))
        n_foreign = int(meta_match.group(5))
        n_nonfinite = int(meta_match.group(6))
        if n_foreign > 0:
            logger.info(f"Excluded {n_foreign} attribute blocks belonging to other filters")
        if n_nonfinite > 0:
            logger.warning(f"Excluded {n_nonfinite} articles with non-finite/non-numeric scores")
        if n_wrong_version > 0:
            logger.info(f"Excluded {n_wrong_version} articles not matching filter_version={filter_version}")
        if n_below > 0:
            logger.info(f"Excluded {n_below} articles below min_score={min_score}")
        if n_fallback > 0 and n_raw > 0:
            logger.warning(
                f"Mixed fields: {n_raw} articles used raw_weighted_average, "
                f"{n_fallback} used weighted_average (possibly normalized). "
                f"CDF may blend raw and normalized scores."
            )
        elif n_fallback > 0:
            logger.warning(
                f"raw_weighted_average not found in any article — using weighted_average "
                f"for all {n_fallback} articles. Check for double-normalization risk."
            )
        else:
            logger.info(f"Using raw_weighted_average for all {n_raw} articles")

    return was


def main():
    parser = argparse.ArgumentParser(
        description="Fit cross-filter percentile normalization from production data (ADR-014)"
    )
    parser.add_argument(
        "--filter", type=Path, required=True,
        help="Path to filter directory (e.g., filters/nature_recovery/v1)",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=None,
        help="Local directory containing flat filtered_*.jsonl files",
    )
    parser.add_argument(
        "--ssh", type=str, default=None,
        help="SSH host to read production data from (e.g., sadalsuud)",
    )
    parser.add_argument(
        "--remote-dir", type=str, default=None,
        help="Remote directory on SSH host (e.g., /home/jeroen/local_dev/NexusMind/data/filtered/nature_recovery)",
    )
    parser.add_argument(
        "--n-bins", type=int, default=200,
        help="Number of breakpoints in the lookup table (default: 200)",
    )
    parser.add_argument(
        "--min-score", type=float, default=None,
        help="Minimum raw_weighted_average to include. Defaults to the filter's operating "
             "point (lowest non-zero TIER_THRESHOLDS entry). Values below the op-point are "
             "refused — see --allow-below-op-point.",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Write the result here instead of into the filter package. NOTE: --out does "
             "NOT relax any guard — it can point at a package normalization.json, so it is "
             "just a location. To fit something the guards would refuse, use --analysis-only.",
    )
    parser.add_argument(
        "--analysis-only", action="store_true",
        help="Downgrade the deploy guards (thin fit, raw_min off the op-point) from errors "
             "to warnings, for throwaway inspection fits. Requires --out, and the output "
             "file must NOT be named normalization.json — an analysis artifact must not be "
             "deployable by a stray copy.",
    )
    parser.add_argument(
        "--allow-thin-fit", action="store_true",
        help=f"Fit even with fewer than {MIN_NORMALIZATION_ARTICLES} articles. Production "
             f"rejects such a CDF at load, so this requires --analysis-only.",
    )
    parser.add_argument(
        "--allow-below-op-point", action="store_true",
        help="Permit --min-score below the filter's operating point. This is what caused "
             "NexusMind#161 — it maps sub-visibility articles into the visible band, so the "
             "result is undeployable by definition and this requires --analysis-only.",
    )
    parser.add_argument(
        "--all-versions", action="store_true",
        help="Fit across EVERY filter_version present in the data. Different versions are "
             "different models with different score distributions, so the CDF becomes a "
             "bimodal blend — cross-version analysis only; requires --analysis-only.",
    )
    parser.add_argument(
        "--filter-version", type=str, default=None,
        help="Only include articles where nexus_mind_attributes.<filter>.filter_version "
             "matches this string (e.g., '2.0'). Required when production has v1 leftovers "
             "mixed with the current version's output.",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.filter.is_dir():
        logger.error(f"Filter directory not found: {args.filter}")
        sys.exit(1)

    # --analysis-only is the ONLY thing that relaxes the deploy guards. Round-4
    # (2026-07-16) proved "--out means analysis" is false — --out can point AT a
    # package normalization.json — so the escape hatch must be an explicit flag,
    # and its output must be un-deployable by filename: nothing that loads
    # normalization data will ever pick up a file not named normalization.json.
    if args.analysis_only:
        if args.out is None:
            logger.error(
                "--analysis-only requires --out: without it the fit would be written to "
                "the filter package's normalization.json, which is the deploy path."
            )
            sys.exit(1)
        # Check the RESOLVED name too: a pre-placed symlink called foo_analysis.json
        # pointing at a package normalization.json would otherwise carry a
        # guard-relaxed fit straight onto the deploy path.
        if "normalization.json" in (args.out.name, args.out.resolve().name):
            logger.error(
                f"--analysis-only refuses to write to {args.out}: an analysis artifact "
                f"must not be (or resolve to) a file named normalization.json — a copy or "
                f"a mispointed --out would make it deployable. Name it e.g. "
                f"{args.out.stem}_analysis.json."
            )
            sys.exit(1)
    elif args.out is not None:
        # --out without --analysis-only is a full-guard fit written to a custom
        # location — but it must not silently retarget ANOTHER package: a valid fit
        # for filter A written into filter B's normalization.json is loadable and
        # invariant-test-green whenever their op-points coincide (8 of 10 deployed
        # filters sit at 4.0), so B would deploy A's score distribution with no
        # signal anywhere.
        out_r = args.out.resolve()
        if out_r.name == "normalization.json" and out_r.parent != args.filter.resolve():
            logger.error(
                f"--out {args.out} is a package normalization.json that does not belong to "
                f"--filter {args.filter}. Point --filter at that package instead, or choose "
                f"a different output name."
            )
            sys.exit(1)

    # Every flag that by definition produces an undeployable file demands the
    # analysis path — validated UPFRONT, before any (possibly minutes-long --ssh)
    # data pull. Round-4 lesson: a control that contradicts another control at the
    # END of the run is itself an operational defect.
    for flag, is_set, why in (
        ("--allow-thin-fit", args.allow_thin_fit,
         f"produces a CDF production rejects at load (< {MIN_NORMALIZATION_ARTICLES} articles)"),
        ("--allow-below-op-point", args.allow_below_op_point,
         "produces raw_min below the op-point, which the invariant test rejects (the #161 shape)"),
        ("--all-versions", args.all_versions,
         "blends distinct model distributions into one CDF (gotcha-log: 19,948 v1 leftovers)"),
    ):
        if is_set and not args.analysis_only:
            logger.error(
                f"{flag} {why} — it is analysis by definition. "
                f"Pass --analysis-only (with an --out not named normalization.json)."
            )
            sys.exit(1)

    if args.ssh and not args.remote_dir:
        logger.error("--remote-dir is required when using --ssh")
        sys.exit(1)

    if not args.ssh and not args.data_dir:
        logger.error("Either --data-dir or --ssh + --remote-dir is required")
        sys.exit(1)

    # Load config for filter name/version
    config_path = args.filter / "config.yaml"
    filter_name = args.filter.parent.name
    filter_version = args.filter.name

    if config_path.exists():
        import yaml
        with open(config_path) as f:
            # `or {}`: yaml.safe_load returns None for an empty file, and every
            # downstream .get would die on an AttributeError traceback.
            config = yaml.safe_load(f) or {}
        filter_info = config.get("filter", {})
        filter_name = filter_info.get("name", filter_name)
        filter_version = str(filter_info.get("version", filter_version))

    logger.info(f"Filter: {filter_name} v{filter_version}")

    # Resolve the operating point and reconcile it with --min-score. Fitting the CDF
    # on articles below the visibility threshold maps invisible content into the
    # visible band by construction (NexusMind#161), so the op-point is the floor.
    op_point = resolve_op_point(args.filter, config if config_path.exists() else {})

    # A deploy-path fit REQUIRES a resolved op-point, --min-score or not: the anchor
    # and the post-fit guard would otherwise key on --min-score alone, making them
    # tautological (any value <= 4.5 would ship), and the invariant test fails the
    # written package anyway because IT can only resolve the op-point from
    # base_scorer.py. Writing a file the repo's own test then rejects is the exact
    # fitter/test inconsistency this file must not reintroduce.
    if op_point is None and not args.analysis_only:
        logger.error(
            "Cannot resolve the operating point from base_scorer.py TIER_THRESHOLDS, so a "
            "deploy-path fit cannot be validated against it — and "
            "tests/unit/test_normalization_invariant.py will fail the package for the same "
            "reason, whatever --min-score says. Fix TIER_THRESHOLDS so it parses as one "
            "literal list, or use --analysis-only with --out for inspection fits."
        )
        sys.exit(1)

    if args.min_score is None:
        if op_point is None:
            logger.error(
                "Could not resolve the operating point from base_scorer.py TIER_THRESHOLDS, "
                "and no --min-score was given. config.yaml is NOT consulted as a fallback — it "
                "is documentation and is known to go stale (sustainability_technology v3 and "
                "investment_risk v6 both ship 3.0 against a live 4.0). Pass --min-score "
                "explicitly: it must be the filter's visibility threshold, the value the "
                "runtime assigns tiers from."
            )
            sys.exit(1)
        args.min_score = op_point
        logger.info(f"Operating point: {op_point} (resolved) — using as --min-score")
    elif op_point is not None and args.min_score < op_point:
        if not args.allow_below_op_point:
            logger.error(
                f"--min-score {args.min_score} is below the operating point {op_point}.\n"
                f"  Fitting below the op-point maps sub-visibility articles into the visible\n"
                f"  band: it is exactly what put doom articles on the Recovery lens at 8.34/10\n"
                f"  (NexusMind#161 — v2 fitted at 1.5, fit-set median 2.19).\n"
                f"  Use --min-score {op_point} , or --allow-below-op-point if you truly mean it."
            )
            sys.exit(1)
        logger.warning(
            f"--min-score {args.min_score} is below the operating point {op_point}, allowed via "
            f"--allow-below-op-point (analysis path). The result maps sub-visibility articles "
            f"into the visible band — never deploy it."
        )
    elif op_point is not None and args.min_score > op_point:
        # Pre-anchor, this only hard-failed above the 4.5 reject bound; anchoring
        # would now make the result LOADABLE, so the guard must move to the
        # op-point itself or a mistyped --min-score ships a population that
        # zeroes part of the visible band.
        msg = (
            f"--min-score {args.min_score} is above the operating point {op_point}: articles "
            f"in [{op_point}, {args.min_score}) are visible in production but excluded from "
            f"the reference population. The CDF is still anchored at {op_point}, so that "
            f"band normalizes onto a 0-percentile ramp — near-invisible in ranking."
        )
        if not args.analysis_only:
            logger.error(
                msg + f"\n  There is no deploy-path reason to do this. Use --min-score "
                f"{op_point}, or --analysis-only with --out for inspection fits."
            )
            sys.exit(1)
        logger.warning(msg)

    # The CDF's lower edge is ANCHORED to the op-point (fit_normalization's
    # anchor_min), so stats.raw_min equals the anchor by construction and cannot
    # drift up on a sparse fit. The anchor is the op-point when it resolves, else
    # the explicit --min-score the operator was forced to supply.
    anchor = op_point if op_point is not None else args.min_score

    # One case is decidable pre-fit: an anchor already above the consumer's reject
    # bound writes stats.raw_min > MAX, which NexusMind's ProductionScorer REJECTS
    # at load — the fit is guaranteed dead regardless of article count. Fail fast
    # with THAT diagnosis — otherwise it falls through to the article-count floor
    # and gets misreported as data scarcity (the #205-shape misdiagnosis this file
    # fights). On the deploy path the op-point is guaranteed resolved (guard above)
    # and the anchor IS the op-point — so no --min-score advice can apply here: an
    # earlier draft's "Refit at --min-score {op_point}" rendered as "--min-score
    # None" on the one path that could reach it.
    if anchor > MAX_NORMALIZATION_RAW_MIN and not args.analysis_only:
        logger.error(
            f"The fit anchor {anchor} exceeds MAX_NORMALIZATION_RAW_MIN "
            f"({MAX_NORMALIZATION_RAW_MIN}): stats.raw_min would land above the bound and "
            f"NexusMind's ProductionScorer REJECTS the file at load, silently falling back "
            f"to score_scale_factor (NexusMind#205).\n"
            f"  The operating point itself ({op_point}) exceeds the bound, so NO fit for "
            f"this filter can load: fix base_scorer.py TIER_THRESHOLDS (or NexusMind's "
            f"MAX_NORMALIZATION_RAW_MIN) first — do not work around it with --min-score.\n"
            f"  For throwaway inspection above the bound, pass --analysis-only with --out."
        )
        sys.exit(1)

    # Scope to one filter version. Different versions are different models with
    # different score distributions; blending them yields a bimodal CDF in which
    # this version's articles are ranked against another version's population. The
    # documented invocation omitted --filter-version, and the rolling production
    # window straddles version cutovers — this already happened once, with 19,948
    # v1 leftovers (gotcha-log "fit_normalization.py Blends Across Filter Versions").
    if args.all_versions:
        if args.filter_version:
            logger.error("--all-versions and --filter-version are mutually exclusive.")
            sys.exit(1)
        logger.warning(
            "--all-versions: fitting across EVERY filter_version in the data. The CDF will "
            "blend distinct model distributions. Only correct for deliberate analysis."
        )
    elif args.filter_version is None:
        # filter_version falls back to the DIRECTORY NAME ("v4") when config.yaml has
        # no filter.version. Production writes "4.0", so scoping to "v4" matches
        # nothing and the run dies on the article-count floor — an error blaming data
        # volume for what is actually a version-scope bug. Refuse instead of guessing.
        config_version = (config.get("filter") or {}).get("version") if config_path.exists() else None
        if config_version is None:
            logger.error(
                f"Cannot scope the fit: config.yaml has no filter.version, so the only "
                f"candidate is the directory name {filter_version!r} — production writes a "
                f"numeric string like '4.0' and would match zero articles.\n"
                f"  Pass --filter-version explicitly (the value production writes to "
                f"nexus_mind_attributes.<filter>.version), or --all-versions to disable scoping."
            )
            sys.exit(1)
        args.filter_version = str(config_version)
        logger.info(
            f"Scoping to filter_version={args.filter_version} (from config.yaml filter.version). "
            f"Override with --filter-version, or --all-versions to disable scoping."
        )

    # Load production weighted averages
    score_label = f"raw_weighted_average >= {args.min_score}"
    version_label = f", filter_version={args.filter_version}" if args.filter_version else ""
    if args.ssh:
        logger.info(f"Loading production data ({score_label}{version_label}) from {args.ssh}:{args.remote_dir}")
        source_desc = f"production {score_label}{version_label} from {args.ssh}:{args.remote_dir}"
        was = load_weighted_averages_ssh(
            args.ssh, args.remote_dir, filter_name,
            min_score=args.min_score, filter_version=args.filter_version,
        )
    else:
        logger.info(f"Loading production data ({score_label}{version_label}) from {args.data_dir}")
        source_desc = f"production {score_label}{version_label} from {args.data_dir}"
        was = load_weighted_averages_local(
            args.data_dir, filter_name, min_score=args.min_score, filter_version=args.filter_version,
        )

    if len(was) < MIN_NORMALIZATION_ARTICLES:
        msg = (
            f"Only {len(was)} articles at/above {args.min_score} — production requires "
            f"{MIN_NORMALIZATION_ARTICLES} (MIN_NORMALIZATION_ARTICLES in NexusMind "
            f"production_scorer.py).\n"
            f"  Fitting anyway would produce a normalization.json that ProductionScorer "
            f"SILENTLY REJECTS at load, falling back to the linear score_scale_factor —\n"
            f"  you would see a sample-mapping table describing a curve production never "
            f"applies.\n"
            f"  For a needle filter this is weeks of live accumulation. Don't wait: rescore a "
            f"production-representative historical harvest (playbook §6) — it must be at the\n"
            f"  production base rate, NOT the enriched val set. Use --allow-thin-fit only for "
            f"throwaway analysis whose output you will not deploy."
        )
        if len(was) == 0:
            msg += (
                "\n  ZERO articles usually is not scarcity at all: check the data files parse, "
                "the directory holds filtered_*.jsonl, and --filter-version matches what "
                "production writes (a version-scope or parse failure reports as 0 here)."
            )
        if not args.allow_thin_fit:
            logger.error(msg)
            sys.exit(1)
        # --allow-thin-fit already implies --analysis-only (+ a non-package --out),
        # validated upfront — the thin CDF cannot land on the deploy path. WARNING,
        # not ERROR: an ERROR that is followed by a successful write poisons
        # log-grepping.
        logger.warning(msg)
        logger.warning(
            f"--allow-thin-fit: writing a {len(was)}-article CDF to {args.out}. Production "
            f"REJECTS fits under {MIN_NORMALIZATION_ARTICLES} — analysis only, never deploy it."
        )

    logger.info(f"Loaded {len(was)} weighted averages")

    # fit_normalization() itself raises ValueError below 10 scores. --allow-thin-fit
    # bypassed the article floor and walked straight into that as an unhandled
    # traceback; fail with a readable message instead.
    if len(was) < 10:
        logger.error(
            f"Only {len(was)} articles — fit_normalization() cannot build a CDF from fewer "
            f"than 10 scores. Not even --allow-thin-fit can rescue this; widen the corpus."
        )
        sys.exit(1)

    # Fit normalization
    wa_array = np.array(was, dtype=np.float64)
    norm_data = fit_normalization(
        wa_array,
        filter_name=filter_name,
        filter_version=filter_version,
        source_description=source_desc,
        n_bins=args.n_bins,
        anchor_min=anchor,
    )

    # Report
    stats = norm_data["stats"]
    pcts = stats["percentiles"]
    logger.info(f"\nNormalization fitted on {norm_data['n_articles']} articles")
    logger.info(f"  Raw WA range: {stats['raw_min']:.2f} - {stats['raw_max']:.2f}")
    logger.info(f"  Raw WA mean:  {stats['raw_mean']:.2f} (std {stats['raw_std']:.2f})")
    logger.info(f"  Percentiles (raw):  p25={pcts['p25']:.2f}  p50={pcts['p50']:.2f}  "
                f"p75={pcts['p75']:.2f}  p90={pcts['p90']:.2f}  p95={pcts['p95']:.2f}")

    # Show what key raw scores map to after normalization. Sample points sit on
    # the fit anchor (the op-point) rather than a fixed 4.0 — a filter whose
    # op-point is 3.75 would otherwise never show the [3.75, 4.0) band, which is
    # where tier flips happen.
    logger.info(f"\n  Sample mappings (raw -> normalized):")
    sample_points = [anchor] + [anchor + step for step in (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)]
    for raw in sample_points:
        norm = float(np.interp(raw, norm_data["x"], norm_data["y"]))
        marker = "  <- operating point" if raw == anchor else ""
        logger.info(f"    {raw:.2f} -> {norm:.2f}{marker}")

    # A sample whose lowest article sits well above the anchor is the #205
    # ROOT-CAUSE signature: the reference population never reached down to the
    # visibility threshold, usually because it was drawn from already-filtered /
    # oracle-biased output rather than a production-representative slice
    # (playbook §6). Anchoring makes such a file LOADABLE (raw_min == op_point),
    # so without a gate here the gross case would ship where the pre-anchor
    # fitter hard-blocked it (raw_min was the sample minimum, > 4.5 → rejected).
    # Two tiers, honestly imperfect:
    #   sample_min > 4.5 (the old reject bound)  -> HARD ERROR on the deploy path;
    #       exactly the protection the pre-anchor code gave, no false-block
    #       possible for any real op-point (3.75/4.0).
    #   gap > 0.5 but sample_min <= 4.5          -> advisory WARNING only. No
    #       static threshold separates a subtly biased sample from a legitimately
    #       sparse needle fit — they are indistinguishable in the data. The gap
    #       is recorded as stats.sample_min for audit; representativeness is the
    #       operator's verification, playbook §6.
    sample_gap = stats["sample_min"] - anchor
    if stats["sample_min"] > MAX_NORMALIZATION_RAW_MIN:
        msg = (
            f"Lowest observed article ({stats['sample_min']:.2f}) is above "
            f"MAX_NORMALIZATION_RAW_MIN ({MAX_NORMALIZATION_RAW_MIN}): the reference "
            f"population never reaches the visibility threshold {anchor} — the #205 "
            f"root-cause signature (sample drawn from already-filtered/oracle-biased "
            f"output; playbook §6). The anchor would make this file loadable, hiding "
            f"what the pre-anchor fitter hard-blocked."
        )
        if not args.analysis_only:
            logger.error(msg + "\n  Nothing is written.")
            sys.exit(1)
        logger.warning(msg + f"\n  Writing to {args.out} anyway (--analysis-only); never "
                             f"deploy this file.")
    elif sample_gap > 0.5:
        logger.warning(
            f"Lowest observed article ({stats['sample_min']:.2f}) sits {sample_gap:.2f} above "
            f"the anchor {anchor}: the whole [{anchor}, {stats['sample_min']:.2f}) band was "
            f"never observed and normalizes onto a 0-percentile ramp. For a gap this large, "
            f"check the sample isn't drawn from already-filtered output (#205's root cause) "
            f"before deploying."
        )

    # Post-fit mirror of the repo invariant (tests/unit/test_normalization_invariant.py)
    # and of the consumer's load guard, applied to what we are about to write. With the
    # anchor in place raw_min deviates from the op-point only when something is actually
    # wrong: --allow-below-op-point pulled data under the anchor (raw_min < op_point,
    # the #161 shape), or the anchor itself is off. Two regimes above the op-point:
    #   op_point+eps < raw_min <= 4.5  loader ACCEPTS the file and silently clamps
    #                                  [op_point, raw_min) to ~0 — the #205 blind spot
    #   raw_min > 4.5                  loader REJECTS the file at load and silently
    #                                  falls back to score_scale_factor — #205 proper
    raw_min = stats["raw_min"]
    reference = op_point if op_point is not None else args.min_score
    if abs(raw_min - reference) > OP_POINT_EPS or raw_min > MAX_NORMALIZATION_RAW_MIN:
        if raw_min < reference:
            regime = (
                f"Below the op-point: sub-visibility articles are in the reference population, "
                f"mapping invisible content into the visible band (NexusMind#161 — v2 fitted "
                f"at 1.5 put doom on the Recovery lens at 8.34/10)."
            )
        elif raw_min <= MAX_NORMALIZATION_RAW_MIN:
            regime = (
                f"Above the op-point but under MAX_NORMALIZATION_RAW_MIN "
                f"({MAX_NORMALIZATION_RAW_MIN}): NexusMind's ProductionScorer ACCEPTS this "
                f"file and silently clamps everything in [{reference}, {raw_min}) to ~0 — "
                f"the load guard's blind spot."
            )
        else:
            regime = (
                f"Above MAX_NORMALIZATION_RAW_MIN ({MAX_NORMALIZATION_RAW_MIN}): NexusMind's "
                f"ProductionScorer REJECTS this file at load and silently falls back to the "
                f"linear score_scale_factor (NexusMind#205: foresight fitted at raw_min 5.01 "
                f"sent raw 4.60 -> wavg 0.02)."
            )
        msg = (
            f"stats.raw_min={raw_min:.4f} is off the fit anchor {reference} "
            f"(±{OP_POINT_EPS}) — tests/unit/test_normalization_invariant.py rejects this "
            f"file.\n  {regime}"
        )
        if not args.analysis_only:
            logger.error(msg + "\n  Nothing is written.")
            sys.exit(1)
        logger.warning(msg + f"\n  Writing to {args.out} anyway (--analysis-only); this file "
                             f"must never be deployed.")

    # Save
    output_path = args.out if args.out is not None else (args.filter / "normalization.json")
    save_normalization(norm_data, str(output_path))
    logger.info(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
