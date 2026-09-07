"""The completeness reporter, and the stale hand-built list it used to carry.

⛔ WHY THESE TESTS EXIST. Until 2026-09-06 `filter_completeness.py` named its
filters in a hand-written dict, and the dict had gone stale: it listed
`sustainability_technology v3`, **deleted on 2026-08-03**, so a removed package
rendered as an incomplete one; it listed two superseded versions; and it omitted
`nature_recovery`, `solutions` and `human_thriving` altogether — *every measurement
error this project has made was a hand-built population*.

⛔ An earlier version of this header said the script was "the tool the package-parity
gate invokes". It is not; **nothing invokes it**. The real package gate is
`scripts/deployment/verify_filter_package.py`, run by the commit-msg hook.

⚠️ The second test is the one that matters over time: `DOC_CORE` is a SECOND COPY
of `memory/filter-doc-standard.md`'s 6-file core, and two hand-maintained copies of
a list disagree the moment one is edited. It cross-checks them rather than trusting
either.
"""
from __future__ import annotations

import importlib.util
import re
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
    against the prose rather than trusting either copy alone.

    ⛔ THE FIRST VERSION OF THIS TEST WAS A MENTION CHECK and review broke it:
    swapping `README_MODEL.md` for `calibration_report.md` — which the standard
    mentions, as an OPTIONAL extension — still passed. Now each name must appear in
    its own NUMBERED core item, so a swap with an optional file fails."""
    text = DOC_STANDARD.read_text(encoding="utf-8")
    assert len(mod.DOC_CORE) == 6, mod.DOC_CORE
    numbered = re.findall(r"^\d+\.\s+~?~?`([^`]+)`", text, re.M)
    assert numbered, "the doc standard's numbered core list did not parse"
    for fname in mod.DOC_CORE:
        assert fname in numbered, (
            f"{fname} is in DOC_CORE but is not a NUMBERED item of the doc "
            f"standard's core (numbered items found: {numbered})")
    # and the struck-through item 3 must NOT be in the core
    assert "prefilter.py" in numbered, "the standard should still LIST item 3"


def test_the_mention_check_swap_is_caught(mod, monkeypatch):
    """The exact substitution review used, asserted to fail now."""
    text = DOC_STANDARD.read_text(encoding="utf-8")
    numbered = re.findall(r"^\d+\.\s+~?~?`([^`]+)`", text, re.M)
    assert "calibration_report.md" not in numbered, (
        "calibration_report.md is an OPTIONAL extension; if it ever becomes a "
        "numbered core item this test stops discriminating")
    assert "`calibration_report.md`" in text, (
        "it must still be MENTIONED, or the swap this guards against is not possible "
        "and the test proves nothing")


def test_strict_makes_incompleteness_fail(mod, capsys):
    """⛔ main() returns 0 however incomplete the fleet is — correct for a report,
    fatal if it is ever wired into a gate. --strict is the gate mode."""
    assert mod.main(["--core", "docs"]) == 0
    capsys.readouterr()
    assert mod.main(["--core", "docs", "--strict"]) == 1
    assert "FAIL --strict" in capsys.readouterr().out


def test_nothing_actually_invokes_this_script(mod):
    """The docstring claimed "this is the tool the package-parity gate invokes" and
    nothing invoked it — mention-as-use, in the file about stale hand-maintained
    state.

    ⚠️ This asserts the WORLD, not the wording. A first version forbade the phrase
    in the docstring, which the corrected docstring must still QUOTE to record what
    was wrong — so the test would have forced deletion of the record. If this script
    is ever genuinely wired into a hook, a CI job or a `verify:` annotation, this
    test fails and the docstring should be corrected in the other direction."""
    import subprocess
    r = subprocess.run(
        ["grep", "-rn", "filter_completeness",
         "--include=*.sh", "--include=*.yml", "--include=*.yaml",
         "--include=commit-msg", "--include=pre-commit",
         ".githooks", "scripts/deployment", "memory/MEMORY.md"],
        cwd=REPO, capture_output=True, text=True)
    assert r.stdout.strip() == "", (
        "something now invokes filter_completeness.py — it is a REPORT whose main() "
        f"returns 0 however incomplete the fleet is; use --strict:\n{r.stdout}")
    assert "REPORT, NOT A GATE" in (mod.__doc__ or "").upper()


def test_prefilter_is_not_in_the_core(mod):
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
