"""The completeness reporter, and the stale hand-built list it used to carry.

⛔ WHY THESE TESTS EXIST. Until 2026-09-06 `filter_completeness.py` named its
filters in a hand-written dict, and the dict had gone stale: it listed
`sustainability_technology v3`, **deleted on 2026-08-03**, so a removed package
rendered as an incomplete one; it listed two superseded versions; and it omitted
`nature_recovery`, `solutions` and `human_thriving` altogether. This is the tool
the package-parity gate invokes, so its population being wrong made every parity
claim wrong with it — *every measurement error this project has made was a
hand-built population*.

⚠️ The second test is the one that matters over time: `DOC_CORE` is a SECOND COPY
of `memory/filter-doc-standard.md`'s 6-file core, and two hand-maintained copies of
a list disagree the moment one is edited. It cross-checks them rather than trusting
either.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "analysis" / "filter_completeness.py"
DOC_STANDARD = REPO / "memory" / "filter-doc-standard.md"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("filter_completeness", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    sys.modules["filter_completeness"] = m
    spec.loader.exec_module(m)
    return m


def test_discovery_finds_the_real_packages(mod):
    """A discovery that returns nothing would report 0/0 complete and PASS — the
    shape the old hand-built list failed in, one entry at a time."""
    found = mod.discover()
    assert len(found) > 5, found
    assert "filters/human_thriving/v8" in found
    assert "filters/nature_recovery/v4" in found
    assert all(p.startswith("filters/") for p in found)


def test_discovery_excludes_common(mod):
    """`filters/common/` holds shared math and the junk gates, not filter packages;
    including it would report a permanent phantom incompleteness."""
    assert not any(p.startswith("filters/common/") for p in mod.discover())


def test_discovery_tracks_deletions(mod):
    """`sustainability_technology v3` was removed on 2026-08-03 and the old list
    kept naming it. Discovery must not resurrect a package that is gone."""
    found = mod.discover()
    on_disk = (REPO / "filters" / "sustainability_technology").exists()
    named = any("sustainability_technology" in p for p in found)
    assert named == on_disk, (
        "the reporter and the filesystem disagree about "
        f"sustainability_technology (named={named}, on_disk={on_disk})")


def test_doc_core_matches_the_written_standard(mod):
    """DOC_CORE is a second copy of the doc standard's 6-file core. Cross-check it
    against the prose rather than trusting either copy alone."""
    text = DOC_STANDARD.read_text(encoding="utf-8")
    assert len(mod.DOC_CORE) == 6, mod.DOC_CORE
    for fname in mod.DOC_CORE:
        assert f"`{fname}`" in text, (
            f"{fname} is in DOC_CORE but the doc standard never names it")
    assert "prefilter.py" not in mod.DOC_CORE, (
        "prefilter.py was removed from the core on 2026-08-21 (owner ruling); "
        "putting it back makes a correctly-built new filter read as INCOMPLETE")


def test_weights_are_not_counted_as_missing(mod):
    """⚠️ Model checkpoints are gitignored, so absent-in-a-clone is normal. If they
    were in a core list, a fresh clone would report every package broken."""
    for rel in mod.LOCAL_ONLY:
        assert rel not in mod.DOC_CORE and rel not in mod.CODE_CORE


def test_hub_declaration_is_exclusive(mod):
    """verify_filter_package.py refuses NO_HUB and inference_hub.py together as an
    ambiguous state — it blocked a commit for exactly that on 2026-09-06 — so this
    report must treat BOTH as a finding, not as doubly-declared."""
    assert set(mod.HUB_DECLARATION) == {"inference_hub.py", "NO_HUB"}


def test_main_runs_and_returns_zero(mod, capsys):
    assert mod.main([]) == 0
    out = capsys.readouterr().out
    assert "doc standard" in out and "complete" in out
