"""
Schema conformance gate for filter config.yaml files.

Purpose: lock in a canonical shape for filter configuration so new filters
don't introduce fresh drift. Existing known drift is allowed via the
EXEMPTIONS set — each exemption is a concrete (filter, version, issue_code)
tuple that documents a specific deviation.

Removing an exemption while the underlying drift still exists fails the
test (the exemption must match a real violation). Fixing the drift while
leaving the exemption in place also fails (exemption must stop matching).
This forces the cleanup and the allow-list to stay in lockstep.

See also: docs/adr/ (add ADR when the canonical schema is ratified).
"""

import sys
from pathlib import Path

import pytest
import yaml

# Add project root to path so `filters.*` imports resolve during test collection.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

REPO_ROOT = Path(__file__).parent.parent.parent

# --- Active filters ------------------------------------------------------
# The versions NexusMind currently deploys. Legacy versions (older than these)
# are archived and intentionally not validated. When a filter is promoted to
# a new version, update this list AND the NexusMind CLAUDE.md table.

ACTIVE_FILTERS = [
    ("sustainability_technology", "v3"),
    ("uplifting", "v7"),
    ("cultural_discovery", "v5"),
    ("investment_risk", "v6"),
    ("belonging", "v1"),
    ("nature_recovery", "v4"),
    ("foresight", "v1"),
]

# --- Canonical schema ---------------------------------------------------

REQUIRED_TOP_LEVEL = {
    "filter",             # filter metadata (name, version, id)
    "prefilter",          # keyword prefilter config
    "oracle",             # training-data oracle (NOT "ground_truth")
    "preprocessing",      # text preprocessing (head+tail, max_tokens, etc.)
    "scoring",            # dimensions, gatekeepers, tiers, scale factor
    "training",           # LoRA / training hyperparams
    "hybrid_inference",   # e5-small probe + threshold
    "deployment",         # HuggingFace Hub target repo
}

REQUIRED_SCORING_KEYS = {
    "dimensions",         # dict of dimension_name -> weight / description
    "gatekeepers",        # MUST be dict (not list)
    "tiers",              # dict of tier_name -> threshold/description
    "score_scale_factor", # linear fallback when percentile normalization is off
}

# --- Known source-type vocabulary (NexusMind#189) -----------------------
# Optional `source_filter:` top-level block — when present, its
# `excluded_source_types: [...]` entries must be drawn from this set.
# Source-of-truth for the vocabulary lives in FluxusSource:
#   - tag-based + domain-based: src/quality/heuristic_scorer.py classify_type
#   - declarative aggregator types: config/app.yaml (apis.*)
#
# When FluxusSource adds a new value (e.g., a `social` aggregator class),
# add it here in the same PR to keep the gate in lockstep.

KNOWN_SOURCE_TYPES = {
    # News — all emitted by classify_type() via tags/categories/tld
    "news_major", "news_regional", "news_global",
    "wire_service", "public_broadcaster",
    # Aggregators — three new types from NexusMind#189
    "aggregator", "developer_aggregator", "firehose_aggregator",
    # Specialized — academic/government emitted by classify_type();
    # think_tank emitted by classify_type() via tag; ngo is reserved
    # forward-planning vocabulary (no emitter today, but accepted in
    # filter configs to avoid blocking future use).
    "academic", "government", "ngo", "think_tank",
    # Tech / repos — code_repo emitted by classify_type() via domain;
    # tech_industry not emitted by classify_type() but heavily used in
    # FluxusSource's credibility.yaml manual_overrides (e.g., heise.de,
    # techcrunch.com, dev.to platform_types entry).
    "code_repo", "tech_industry",
    # Other — blog_independent emitted by classify_type() via tag;
    # social emitted via platform_types (bsky.app, mastodon.social);
    # unknown is the catch-all default.
    "blog_independent", "social", "unknown",
}

# --- Known-drift exemptions ---------------------------------------------
# Each entry = (filter, version, issue_code). Issue codes follow the
# convention used in _violations(). Tuples here are ACCEPTED; they don't
# cause the test to fail. But every tuple MUST still correspond to a real
# violation — removing one while drift persists is a bug.
#
# When fixing a drift during the B migration, remove the exemption(s) in
# the same commit as the config fix.

EXEMPTIONS: set[tuple[str, str, str]] = {
    # cultural_discovery v5 (deployed 2026-05-31) shipped a deliberately leaner
    # config: 87 lines vs v4's 160, dropping five sections this schema requires.
    # Surfaced 2026-07-14 when ACTIVE_FILTERS was corrected — it had still named
    # v4, so the deployed version was never checked and the drift was invisible
    # for six weeks.
    #
    # These are NOT obviously bugs, which is why they are exemptions rather than
    # fixes. Nothing under filters/common/ reads deployment / hybrid_inference /
    # training — they are documentation-only. gatekeepers and tiers DO have
    # runtime meaning, but the runtime reads them from base_scorer.py's
    # GATEKEEPER_* / TIER_THRESHOLDS constants, not from config (that is the
    # 2026-07-10 "inert config value" lesson: config's tiers section is read by
    # no code). So v5 may well be right and this schema stale.
    #
    # OPEN DECISION (engineer): either ratify the leaner shape and drop these
    # from REQUIRED_TOP_LEVEL / REQUIRED_SCORING_KEYS, or backfill v5's config.
    # Do not let these sit here indefinitely — an exemption is a tracked debt,
    # not a resolution.
    ("cultural_discovery", "v5", "missing_top_level:deployment"),
    ("cultural_discovery", "v5", "missing_top_level:hybrid_inference"),
    ("cultural_discovery", "v5", "missing_top_level:training"),
    ("cultural_discovery", "v5", "scoring_missing:gatekeepers"),
    ("cultural_discovery", "v5", "scoring_missing:tiers"),
}
# Migration B complete (2026-05-04): all 7 active filters conform to the
# canonical schema. Add an exemption here only with a written justification
# explaining why the deviation is intentional and what would unblock removal.


def _violations(cfg: dict) -> set[str]:
    """
    Return the set of issue codes this config triggers against the canonical
    schema. Empty set = fully conformant.
    """
    issues: set[str] = set()

    # Top-level section presence
    present = set(cfg.keys())
    for missing in REQUIRED_TOP_LEVEL - present:
        issues.add(f"missing_top_level:{missing}")
    # Flag well-known aliases explicitly — easier to read than a generic
    # "unexpected key" for keys we intentionally want to discourage.
    for alias in ("ground_truth",):
        if alias in present:
            issues.add(f"unexpected_top_level:{alias}")

    # Scoring section
    scoring = cfg.get("scoring")
    if scoring is None:
        issues.add("missing_top_level:scoring")
    elif isinstance(scoring, dict):
        scoring_keys = set(scoring.keys())
        for missing in REQUIRED_SCORING_KEYS - scoring_keys:
            issues.add(f"scoring_missing:{missing}")

        # gatekeepers must be a dict — list form is legacy
        gk = scoring.get("gatekeepers")
        if isinstance(gk, list):
            issues.add("scoring_type:gatekeepers_is_list_not_dict")
    else:
        issues.add("scoring_type:not_a_dict")

    # source_filter section — optional (NexusMind#189). When present, its
    # contents must conform: excluded_source_types is a list of known
    # vocabulary strings, shadow_mode is a bool.
    sf = cfg.get("source_filter")
    if sf is not None:
        if not isinstance(sf, dict):
            issues.add("source_filter_type:not_a_dict")
        else:
            excluded = sf.get("excluded_source_types")
            if excluded is None:
                issues.add("source_filter_missing:excluded_source_types")
            elif not isinstance(excluded, list):
                issues.add("source_filter_type:excluded_not_list")
            else:
                for entry in excluded:
                    if not isinstance(entry, str):
                        issues.add("source_filter_type:excluded_item_not_str")
                    elif entry not in KNOWN_SOURCE_TYPES:
                        issues.add(f"source_filter_unknown_type:{entry}")
            shadow_mode = sf.get("shadow_mode")
            if shadow_mode is not None and not isinstance(shadow_mode, bool):
                issues.add("source_filter_type:shadow_mode_not_bool")

    return issues


def _filter_dir(filter_name: str, version: str) -> Path:
    return REPO_ROOT / "filters" / filter_name / version


def _config_path(filter_name: str, version: str) -> Path:
    return _filter_dir(filter_name, version) / "config.yaml"


def _load_config(filter_name: str, version: str) -> dict:
    with open(_config_path(filter_name, version), encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize("filter_name,version", ACTIVE_FILTERS,
                         ids=lambda x: x if isinstance(x, str) else f"v{x}")
def test_active_filter_config_conforms_or_is_exempt(filter_name, version):
    """
    Each active filter must conform to the canonical config schema, OR every
    deviation must be in EXEMPTIONS. New drift → test fails. Fixed drift with
    stale exemption → test fails (see separate test_no_stale_exemptions).
    """
    assert _config_path(filter_name, version).exists(), (
        f"{filter_name}/{version}: config.yaml missing — is ACTIVE_FILTERS stale?"
    )

    cfg = _load_config(filter_name, version)
    issues = _violations(cfg)

    filter_exemptions = {
        code for (f, v, code) in EXEMPTIONS
        if f == filter_name and v == version
    }
    unexpected = issues - filter_exemptions
    assert not unexpected, (
        f"{filter_name}/{version}: new config drift detected.\n"
        f"  Unexpected violations: {sorted(unexpected)}\n"
        f"  Fix the config, or add to EXEMPTIONS with justification."
    )


class TestSourceFilterValidation:
    """Tests for the optional source_filter: block (NexusMind#189).

    These do not exercise actual filter configs — they call _violations()
    directly on synthetic configs to lock in the validation rules ahead
    of Phase 1 (when 7 filter configs gain real source_filter blocks).
    """

    def _base_config(self) -> dict:
        """Minimal valid-ish config so we can layer source_filter on top."""
        return {
            "filter": {"name": "test", "version": "v1"},
            "prefilter": {},
            "oracle": {},
            "preprocessing": {},
            "scoring": {
                "dimensions": {},
                "gatekeepers": {},
                "tiers": {},
                "score_scale_factor": 1.0,
            },
            "training": {},
            "hybrid_inference": {},
            "deployment": {},
        }

    def test_absent_source_filter_is_valid(self):
        """source_filter is optional — its absence triggers no violation."""
        cfg = self._base_config()
        sf_issues = {i for i in _violations(cfg) if i.startswith("source_filter")}
        assert sf_issues == set()

    def test_well_formed_source_filter_passes(self):
        cfg = self._base_config()
        cfg["source_filter"] = {
            "excluded_source_types": ["code_repo", "developer_aggregator"],
            "shadow_mode": True,
        }
        sf_issues = {i for i in _violations(cfg) if i.startswith("source_filter")}
        assert sf_issues == set()

    def test_excluded_types_must_be_list(self):
        cfg = self._base_config()
        cfg["source_filter"] = {"excluded_source_types": "code_repo"}  # str not list
        assert "source_filter_type:excluded_not_list" in _violations(cfg)

    def test_excluded_types_must_be_known_vocabulary(self):
        cfg = self._base_config()
        # Valid + invalid mixed — only the invalid entry is flagged.
        cfg["source_filter"] = {
            "excluded_source_types": ["code_repo", "code_rep"],  # typo
        }
        v = _violations(cfg)
        assert "source_filter_unknown_type:code_rep" in v
        assert "source_filter_unknown_type:code_repo" not in v  # valid one passes

    def test_excluded_types_items_must_be_strings(self):
        cfg = self._base_config()
        cfg["source_filter"] = {"excluded_source_types": ["code_repo", 42]}
        assert "source_filter_type:excluded_item_not_str" in _violations(cfg)

    def test_excluded_source_types_required_when_block_present(self):
        cfg = self._base_config()
        cfg["source_filter"] = {"shadow_mode": True}
        assert "source_filter_missing:excluded_source_types" in _violations(cfg)

    def test_shadow_mode_must_be_bool(self):
        cfg = self._base_config()
        cfg["source_filter"] = {
            "excluded_source_types": ["code_repo"],
            "shadow_mode": "yes",  # str not bool
        }
        assert "source_filter_type:shadow_mode_not_bool" in _violations(cfg)

    def test_shadow_mode_omitted_is_valid(self):
        cfg = self._base_config()
        cfg["source_filter"] = {"excluded_source_types": ["code_repo"]}
        sf_issues = {i for i in _violations(cfg) if i.startswith("source_filter")}
        assert sf_issues == set()

    def test_source_filter_must_be_dict(self):
        cfg = self._base_config()
        cfg["source_filter"] = ["code_repo"]  # list at top
        assert "source_filter_type:not_a_dict" in _violations(cfg)

    def test_all_known_vocabulary_values_accepted(self):
        """Every entry in KNOWN_SOURCE_TYPES must validate cleanly. This
        prevents typos in the vocabulary set itself."""
        cfg = self._base_config()
        cfg["source_filter"] = {"excluded_source_types": sorted(KNOWN_SOURCE_TYPES)}
        sf_issues = {i for i in _violations(cfg) if i.startswith("source_filter")}
        assert sf_issues == set()


def test_no_stale_exemptions():
    """
    Every EXEMPTIONS entry must correspond to a real current violation. If
    someone fixes the drift but forgets to remove the exemption, this test
    tells them. Prevents the allow-list from silently growing obsolete.
    """
    stale = []
    for filter_name, version, code in EXEMPTIONS:
        if (filter_name, version) not in ACTIVE_FILTERS:
            stale.append((filter_name, version, code, "not in ACTIVE_FILTERS"))
            continue
        cfg = _load_config(filter_name, version)
        if code not in _violations(cfg):
            stale.append((filter_name, version, code, "no matching violation"))

    assert not stale, (
        "Stale EXEMPTIONS found — remove these entries:\n"
        + "\n".join(f"  {f}/{v}: {c}  ({reason})" for f, v, c, reason in stale)
    )
