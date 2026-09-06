"""The four claim-SHAPE checks (`scripts/verification/check_claim_shapes.py`).

⚠️ EVERY TEST HERE SEEDS THE DEFECT IT CLAIMS TO CATCH, and that is the whole
reason the file exists rather than being nice-to-have. These four checks were
written on 2026-09-05 to mechanise four defects that a green mechanical battery
had already missed once (`EXP-024`); *a check that never catches anything is
indistinguishable from one that works*, and the project's own record has a guard
shipping with the right caller on the right path and doing nothing. So each check
below is shown FIRING on a seeded true positive, and — because the failure mode
of a claim-shape check is silently matching nothing — also on the empty-scan and
stale-registry paths, where it must read CANNOT VERIFY rather than PASS.

⛔ `test_a_mention_of_the_weight_field_is_not_a_read` and
`test_the_field_named_in_an_error_message_is_not_a_read` pin the same defect
twice, because it was fixed twice and was still wrong the first time: the opening
`# design-weights:` declaration explained the gap by naming
`inclusion_probability` and the substring test read the confession as compliance;
excluding docstrings then left the field's name in an error message and a JSON
label, so the flagship analysis survived deletion of its only real weight read.

⭐ **43 tests**, and the ones that matter are the ones a green suite would not
have produced on its own: every CANNOT VERIFY path, the rewrap that hides a
claim, the two adjacent bullets that are two claims, the declaration inside a
string literal, the null-control exemption confined to a leaf key, the symlinked
directory that contributed zero files, and the latin-1 file whose lost `±` would
have turned a qualified ordering into a FAIL.
"""

import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "scripts", "verification", "check_claim_shapes.py")

MANIFEST = {"filter": "human_thriving", "version": "v8",
            "design_cells": {"pos_clear": {"target": 40}, "neg_low": {"target": 200}}}

# A healthy evidence document: one no-difference claim WITH its reachability
# bound, one quantified ordering WITH a band.
GOOD_MD = """# A fine document

The two arms give identical TP at all eight k — but the comparison was **forced**:
the smallest k at which they could have differed is 140, and the grid stops at 60.

`student_calibrated` beats `probe_reg_large` (AUC 0.9488 vs 0.9021), 95% CI
[+0.0121, +0.0783].
"""

GOOD_JSON = {"bootstrap": {"ci_low": -0.0448, "ci_high": 0.0476},
             "recall_band": [0.4, 0.5142],
             "bootstrap_null_control": {"ci_low": 0.0, "ci_high": 0.0,
                                        "passes": True}}

# An analysis that reads the design-weighted population AND the weights.
GOOD_PY = '''"""Reads datasets/scored/human_thriving_v8/corpus.jsonl."""
import json

CORPUS = "datasets/scored/human_thriving_v8/corpus.jsonl"


def main():
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    return sum(1.0 / r["inclusion_probability"] for r in rows)
'''


@pytest.fixture
def mod(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_claim_shapes", GUARD)
    m = importlib.util.module_from_spec(spec)
    sys.modules["check_claim_shapes"] = m
    spec.loader.exec_module(m)
    for rel in (("docs/evidence/2026-08-29-v8-corpus-draw", "experiments")
                + m.DOC_ROOTS + m.CODE_ROOTS):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/evidence/2026-08-29-v8-corpus-draw/corpus_manifest.json"
     ).write_text(json.dumps(MANIFEST), encoding="utf-8")
    (tmp_path / "docs/evidence/good.md").write_text(GOOD_MD, encoding="utf-8")
    (tmp_path / "docs/evidence/good.json").write_text(json.dumps(GOOD_JSON),
                                                      encoding="utf-8")
    (tmp_path / "scripts/analysis/good.py").write_text(GOOD_PY, encoding="utf-8")
    # ⚠️ EVERY SCAN ROOT MUST BE NON-EMPTY, so the healthy fixture has to populate all of
    # them — that requirement is itself a review finding (a partially emptied root used to
    # report PASS), and a fixture that skipped a root would not exercise it.
    # ⛔ DERIVED FROM `m.DOC_ROOTS`, NOT LISTED BY HAND. Adding a root used to leave
    # the fixture one directory short, and `_walk`'s empty-root guard then turned
    # every doc check into CANNOT VERIFY — which is the guard working, but it fires
    # in 14 tests at once and reads like the checker broke. Widening the roots on
    # 2026-09-06 (`filters`) is what demonstrated it.
    for root in m.DOC_ROOTS:
        if root == "docs/evidence":
            continue                      # already populated above
        (tmp_path / root / "ok.md").write_text(
            "# Neutral\n\nNothing here triggers any check.\n", encoding="utf-8")
        (tmp_path / root / "ok.json").write_text(
            json.dumps({"note": "no interval here"}), encoding="utf-8")
    (tmp_path / "docs/evidence/ok.py").write_text("X = 1\n", encoding="utf-8")
    for root in m.CODE_ROOTS:
        if root != "scripts/analysis":
            (tmp_path / root / "ok.py").write_text("Y = 2\n", encoding="utf-8")
    (tmp_path / "experiments/registry.jsonl").write_text(
        json.dumps({"id": "EXP-001", "metrics": {"delta_ci": [-0.1, 0.2]}}) + "\n",
        encoding="utf-8")
    monkeypatch.setattr(m, "ROOT", str(tmp_path))
    m._tmp = tmp_path
    return m


def _write(mod, rel, body):
    p = mod._tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body if isinstance(body, str) else json.dumps(body),
                 encoding="utf-8")
    return p


def test_the_registry_jsonl_is_actually_scanned(mod, capsys):
    """⛔ A BLOCKER FROM THE REVIEW. `experiments` sat in the JSON scan roots behind an
    `endswith(".json")` filter, and `".jsonl".endswith((".json",))` is False — so the root
    contributed zero files, the `.jsonl` guard beneath it was unreachable dead code, and
    the registry, where an experiment's headline numbers live, was never read."""
    _write(mod, "experiments/registry.jsonl",
           json.dumps({"id": "EXP-002", "metrics": {"delta_ci": [0.4, 0.4]}}) + "\n")
    assert mod.main(["--check", "zero-width-interval"]) == 1
    out = capsys.readouterr().out
    assert "experiments/registry.jsonl:1" in out


def test_a_missing_registry_is_cannot_verify(mod, capsys):
    (mod._tmp / "experiments/registry.jsonl").unlink()
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "narrower than it claims" in capsys.readouterr().out


def test_the_healthy_fixture_passes(mod, capsys):
    assert mod.main([]) == 0
    out = capsys.readouterr().out
    assert "FAIL" not in out and "CANNOT VERIFY" not in out
    assert out.strip().splitlines()[-1].startswith("PASS ")


# ────────────────────────────────────────────── (a) no-difference-range

def test_a_no_difference_claim_without_a_range_fails(mod, capsys):
    """The seeded true positive is EXP-024's own retracted sentence, stripped of
    the bound that made it honest."""
    _write(mod, "docs/evidence/bad.md",
           "# Bad\n\nB and C give identical TP at all eight k, so the gate buys "
           "nothing.\n")
    assert mod.main(["--check", "no-difference-range"]) == 1
    out = capsys.readouterr().out
    assert "FAIL no-difference-range: docs/evidence/bad.md:3" in out
    assert "could have differed" in out


def test_an_observed_difference_elsewhere_counts_as_the_range(mod, capsys):
    """The second honest answer, and the cross-box parity record's: a nearby
    configuration where the same instrument DID show a difference proves the
    difference was reachable."""
    _write(mod, "docs/evidence/parity.md",
           "# Parity\n\nPinned and on CPU, 660/660 bit-identical, 0 flips at "
           "every threshold.\nThe 3 flips at 4.5 were the library stack.\n")
    assert mod.main(["--check", "no-difference-range"]) == 0


def test_a_property_claim_over_a_grid_is_not_in_scope(mod, capsys):
    """Deliberately narrow. `every one of the six dimensions is 0-2` is a claim
    about a property, not about sameness between two arms, and firing on it would
    bury the check in noise until someone turned it off."""
    _write(mod, "docs/evidence/prop.md",
           "# Prop\n\nIf `scope_verdict` is not `in_scope`, every one of the six "
           "dimensions is 0-2.\n")
    assert mod.main(["--check", "no-difference-range"]) == 0


def test_the_bare_idiom_at_all_is_not_a_grid(mod, capsys):
    """`reaching for the prefix at all` was reported as a no-difference-over-a-grid
    claim. The quantifier has to name its grid."""
    _write(mod, "docs/evidence/idiom.md",
           "# Idiom\n\nThe incident text stands unchanged — that session's error was "
           "reaching for the prefix at all.\n")
    assert mod.main(["--check", "no-difference-range"]) == 0


def test_a_qualifier_split_across_a_line_break_still_counts(mod, capsys):
    """⛔ THE VERDICT MUST NOT DEPEND ON WHERE A TEXT EDITOR WRAPPED. "could not have\ncome
    out any other way" failed the reachability search purely because the wrap fell between
    two words."""
    _write(mod, "docs/evidence/wrapped.md",
           "# Wrapped\n\nThe two arms are identical at all eight k, and that is not a\n"
           "result: the comparison could not have\ncome out any other way.\n")
    assert mod.main(["--check", "no-difference-range"]) == 0


def test_no_candidate_sites_reads_as_cannot_verify(mod, capsys):
    """⛔ THE FAILURE MODE OF THIS WHOLE FILE. A pattern that matches nothing
    passes forever. Sites == 0 must be CANNOT VERIFY, never PASS."""
    (mod._tmp / "docs/evidence/good.md").unlink()
    assert mod.main(["--check", "no-difference-range"]) == 1
    assert "CANNOT VERIFY no-difference-range" in capsys.readouterr().out


def test_missing_scan_roots_read_as_cannot_verify(mod, capsys):
    import shutil
    shutil.rmtree(mod._tmp / "docs")
    assert mod.main(["--check", "no-difference-range"]) == 1
    assert "roots moved" in capsys.readouterr().out


# ────────────────────────────────────────────── (b) zero-width-interval

def test_a_zero_width_low_high_pair_fails(mod, capsys):
    _write(mod, "docs/evidence/bad.json", {"delta": {"ci_low": 0.0, "ci_high": 0.0}})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    out = capsys.readouterr().out
    assert "FAIL zero-width-interval" in out and "could not vary" in out


def test_a_zero_width_band_list_fails(mod, capsys):
    _write(mod, "docs/evidence/bad.json", {"recall_band": [0.42, 0.42]})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "recall_band" in capsys.readouterr().out


def test_a_zero_width_ci_in_prose_fails(mod, capsys):
    _write(mod, "docs/evidence/bad.md",
           "# Bad\n\n`student_raw` at k=30, 95% CI [+0, +0].\n")
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "zero width" in capsys.readouterr().out


def test_a_saturated_band_is_exempt_but_printed(mod, capsys):
    """⛔ THE SECOND LEGITIMATE ZERO WIDTH, and it is DATA, not a name.
    `ground_truth_gate.py` widens a band by flipping the rows inside the noise
    floor — the ones in `indeterminate_by_cell`. With none in tn/fp, specificity
    could not have any width, and `belonging v1` is the live case."""
    _write(mod, "docs/evidence/gate.json",
           {"m": {"specificity_band": [0.9847, 0.9847],
                  "indeterminate_by_cell": {"tp": 5, "fn": 2, "fp": 0, "tn": 0}}})
    assert mod.main(["--check", "zero-width-interval"]) == 0
    out = capsys.readouterr().out
    assert "NOTE zero-width-interval" in out and "SATURATED" in out
    assert "FAIL" not in out


def test_a_frozen_band_with_indeterminate_rows_still_fails(mod, capsys):
    """The exemption is checked against the SIBLING COUNTS. One indeterminate row
    in a cell the metric depends on and the band should have had width, so a zero
    one is the instrument, not the data."""
    _write(mod, "docs/evidence/gate.json",
           {"m": {"specificity_band": [0.9847, 0.9847],
                  "indeterminate_by_cell": {"tp": 5, "fn": 2, "fp": 1, "tn": 0}}})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "FAIL zero-width-interval" in capsys.readouterr().out


def test_the_saturated_exemption_needs_the_sibling_counts(mod, capsys):
    """No `indeterminate_by_cell` means nothing was checked — do not exempt on the
    key name alone, which is how the null-control carve-out went wrong once."""
    _write(mod, "docs/evidence/gate.json",
           {"m": {"specificity_band": [0.9847, 0.9847]}})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "FAIL zero-width-interval" in capsys.readouterr().out


def test_the_saturated_exemption_covers_only_known_metrics(mod, capsys):
    """`spearman` has no confusion cells, so zero-width there is unexplained even
    when every cell count is 0 — the exemption must not generalise by shape."""
    _write(mod, "docs/evidence/gate.json",
           {"m": {"spearman_band": [0.72, 0.72],
                  "indeterminate_by_cell": {"tp": 0, "fn": 0, "fp": 0, "tn": 0}}})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "spearman_band" in capsys.readouterr().out


def test_a_declared_null_control_is_exempt_but_printed(mod, capsys):
    """⛔ A FAILING CHECK MAY BE THE CONTROL WORKING. `adr023_op_point_table.py`
    runs an arm against itself and REQUIRES [0,0]; a non-zero width there is the
    defect. The carve-out is narrow (the path must name a null control) and it is
    never silent — it prints on every run."""
    _write(mod, "docs/evidence/bad.json",
           {"bootstrap_null_control": {"ci_low": 0.0, "ci_high": 0.0}})
    assert mod.main(["--check", "zero-width-interval"]) == 0
    out = capsys.readouterr().out
    assert "NOTE zero-width-interval" in out and "null control" in out


def test_zero_width_is_compared_as_numbers_not_strings(mod, capsys):
    """`CI [0.0, 0.00]` passed a lexical equality test."""
    _write(mod, "docs/evidence/bad.md", "# Bad\n\nThe result: 95% CI [0.0, 0.00].\n")
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "zero width" in capsys.readouterr().out


def test_the_null_control_exemption_does_not_cover_a_subtree(mod, capsys):
    """⛔ ONE BADLY-NAMED ANCESTOR EXEMPTED EVERYTHING BENEATH IT. The exemption matched
    the accumulated path, so `{"vs_null_control": {"student": {...}, "probe": {...}}}`
    silenced every real interval nested under it. It matches the LEAF key now."""
    _write(mod, "docs/evidence/bad.json",
           {"vs_null_control": {"student": {"ci_low": 0.42, "ci_high": 0.42}}})
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "FAIL zero-width-interval" in capsys.readouterr().out


def test_min_max_is_not_an_interval(mod, capsys):
    """`("min","max")` matched six score RANGES in a real artifact, two of which already
    read `min: 0.0`; a constant column would have been reported with the wrong diagnosis."""
    _write(mod, "docs/evidence/bad.json", {"latency_ms": {"min": 2.34, "max": 2.34}})
    assert mod.main(["--check", "zero-width-interval"]) == 0


def test_unreadable_json_is_cannot_verify_not_skipped(mod, capsys):
    """A file the scanner cannot parse must not be quietly dropped from the
    denominator — that is how a scan shrinks to nothing."""
    _write(mod, "docs/evidence/broken.json", "{not json")
    assert mod.main(["--check", "zero-width-interval"]) == 1
    assert "not readable JSON" in capsys.readouterr().out


# ────────────────────────────────────────────── (c) ordering-needs-band

def test_a_quantified_ordering_without_a_band_fails(mod, capsys):
    """The seeded true positive is EXP-024's *AUC would have picked the wrong
    arm* — an ordering that was a coin flip (P = 0.523)."""
    _write(mod, "docs/evidence/bad.md",
           "# Bad\n\nAUC would have picked the wrong arm: 0.9035 vs 0.9021.\n")
    assert mod.main(["--check", "ordering-needs-band"]) == 1
    out = capsys.readouterr().out
    assert "FAIL ordering-needs-band: docs/evidence/bad.md:3" in out


def test_an_unquantified_ordering_is_not_in_scope(mod, capsys):
    """`oversensitive is better than missing risk` is a judgement, not a
    measurement, and demanding a p-value for it would train people to ignore
    the check."""
    _write(mod, "docs/evidence/pref.md",
           "# Pref\n\nOversensitive is better than missing a risk.\n")
    assert mod.main(["--check", "ordering-needs-band"]) == 0


def test_a_rewrap_cannot_hide_an_ordering(mod, capsys):
    """⛔ THE THIRD REVIEW BLOCKER, AND IT WAS MINE. The first fix made under this check
    rewrapped a sentence so the ordering verb no longer shared a physical line with its
    two numbers. The site did not get qualified — it stopped existing. The trigger is now
    sentence-scoped, so the line break is irrelevant."""
    _write(mod, "docs/evidence/wrapped.md",
           "# Wrapped\n\nAUC would have picked the wrong arm:\n0.9035 against 0.9021 on "
           "the same rows.\n")
    assert mod.main(["--check", "ordering-needs-band"]) == 1
    assert "FAIL ordering-needs-band" in capsys.readouterr().out


def test_two_adjacent_bullets_are_two_claims(mod, capsys):
    """A bullet carries no terminal punctuation, so joining a paragraph into one string
    made two list items one "sentence" — and reported `- Val MAE 0.654 (8% better than v1)`
    plus `- Test MAE 0.717` as a single quantified ordering."""
    _write(mod, "docs/evidence/bullets.md",
           "# Bullets\n\n- **Val MAE 0.654** (8% better than v1)\n"
           "- **Test MAE 0.717** (all quality gates passed)\n")
    assert mod.main(["--check", "ordering-needs-band"]) == 0


def test_a_nearby_band_satisfies_the_ordering_check(mod, capsys):
    _write(mod, "docs/evidence/ok.md",
           "# OK\n\nEpoch 4 leads on both (recall 0.5140 vs 0.4570).\nThe two are "
           "not distinguishable — two articles each.\n")
    assert mod.main(["--check", "ordering-needs-band"]) == 0


# ────────────────────────────────────────────── (d) design-weights-read

BAD_PY = '''"""An analysis of datasets/scored/human_thriving_v8/corpus.jsonl."""
import json

rows = [json.loads(l) for l in
        open("datasets/scored/human_thriving_v8/corpus.jsonl", encoding="utf-8")]
print(sum(1 for r in rows if r["v8"] >= 4.5) / len(rows))
'''


def test_an_unweighted_analysis_of_a_weighted_population_fails(mod, capsys):
    _write(mod, "scripts/analysis/bad.py", BAD_PY)
    assert mod.main(["--check", "design-weights-read"]) == 1
    out = capsys.readouterr().out
    assert "FAIL design-weights-read: scripts/analysis/bad.py" in out
    assert "describes the sample" in out


def test_a_mention_of_the_weight_field_is_not_a_read(mod, capsys):
    """⛔ THE TEN-MINUTE DEFECT THIS FILE EXISTS TO PIN. The declaration written
    under this very check named `inclusion_probability` while explaining that it
    was NOT read, and a substring test passed the file. *Mention is not use.*"""
    _write(mod, "scripts/analysis/bad.py",
           BAD_PY.replace("import json",
                          "# the corpus carries inclusion_probability, unused\n"
                          "import json"))
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "never reads the weights" in capsys.readouterr().out


def test_a_docstring_mention_is_not_a_read_either(mod, capsys):
    _write(mod, "scripts/analysis/bad.py",
           BAD_PY.replace('corpus.jsonl."""',
                          'corpus.jsonl, which carries inclusion_probability."""'))
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "never reads the weights" in capsys.readouterr().out


def test_the_field_named_in_an_error_message_is_not_a_read(mod, capsys):
    """⛔ THE FIRST REVIEW BLOCKER, AND THE MOST IMPORTANT TEST HERE. `_reads_field` once
    accepted ANY non-docstring string constant, so deleting the only real weight read from
    the flagship analysis still PASSED — the field's name survived in an error message and
    a JSON label. *Mention is not use*, for the second time, inside the fix for the first."""
    _write(mod, "scripts/analysis/bad.py",
           BAD_PY.replace('print(sum(1 for r in rows if r["v8"] >= 4.5) / len(rows))',
                          'if not rows:\n'
                          '    raise SystemExit(f"rows lack `inclusion_probability`")\n'
                          'REPORT = {"field": "inclusion_probability"}\n'
                          'print(sum(1 for r in rows if r["v8"] >= 4.5) / len(rows))'))
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "never reads the weights" in capsys.readouterr().out


def test_a_subscript_or_a_call_argument_is_a_read(mod, capsys):
    """The other direction: the two shapes that ARE reads must not false-FAIL."""
    for body in ('w = 1.0 / rows[0]["inclusion_probability"]',
                 'w = 1.0 / rows[0].get("inclusion_probability", 1.0)'):
        _write(mod, "scripts/analysis/bad.py", BAD_PY + body + "\n")
        assert mod.main(["--check", "design-weights-read"]) == 0, body
        capsys.readouterr()


def test_a_declaration_inside_a_string_is_not_a_declaration(mod, capsys):
    """The opt-out regex was unanchored and searched the whole file text, so a match
    inside a string literal exempted the file and printed the garbage it captured."""
    _write(mod, "scripts/analysis/bad.py",
           BAD_PY + 'HELP = "see the note \'# design-weights: n/a\' upstream"\n')
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "never reads the weights" in capsys.readouterr().out


def test_a_multiline_declaration_is_printed_whole(mod, capsys):
    """The printed-reason defence promised in the docstring was truncated at the first
    newline and again at 120 chars, so every real declaration showed a mid-sentence
    fragment — a reason nobody can re-read is not a defence."""
    _write(mod, "scripts/analysis/bad.py",
           "# design-weights: NOT READ because the comparison is paired on identical\n"
           "# rows, so the weights cancel in the ordering even though they would move\n"
           "# each arm's absolute value.\n" + BAD_PY)
    assert mod.main(["--check", "design-weights-read"]) == 0
    assert "each arm's absolute value." in capsys.readouterr().out


def test_a_file_that_does_not_parse_is_cannot_verify_not_a_pass(mod, capsys):
    """The `unparsed` branch used to fall back to the substring test, which re-opened the
    exact hole the AST pass exists to close: a syntax error plus the field in a comment
    was exempted."""
    _write(mod, "scripts/analysis/bad.py",
           "# inclusion_probability is not read here\n" + BAD_PY + "def (:\n")
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "does not parse as python" in capsys.readouterr().out


def test_a_partially_emptied_scan_root_is_cannot_verify(mod, capsys):
    """⛔ Losing three of four evidence directories took this check from 7 sites to 1 and
    still printed PASS, because the emptiness test was aggregate across roots."""
    import shutil
    shutil.rmtree(mod._tmp / "scripts/diagnostics")
    (mod._tmp / "scripts/diagnostics").mkdir()
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "scan root(s) scripts/diagnostics" in capsys.readouterr().out


def test_the_test_split_is_a_registered_population(mod, capsys):
    """⛔ REVIEW FINDING. The trigger was two literal CORPUS paths, so five analyses
    reading `test.jsonl` — the 660 design-weighted rows every v8 number is computed on —
    were not sites at all. The weight lives in `corpus.jsonl`, so a split reader's "read
    the weights" is the JOIN; a script that does neither must declare."""
    _write(mod, "scripts/analysis/split.py",
           'import json\n'
           'rows = [json.loads(l) for l in\n'
           '        open("datasets/training/human_thriving_v8/test.jsonl")]\n'
           'print(sum(1 for r in rows if r["y"]) / len(rows))\n')
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "test.jsonl" in capsys.readouterr().out


def test_an_undecodable_file_is_cannot_verify_not_a_fail(mod, capsys):
    """⛔ `errors="replace"` IS A SILENT WRONG ANSWER. `±` is a band token; a latin-1
    markdown file loses it to a replacement character and a properly-qualified ordering
    reports as unqualified. A file the instrument cannot read is CANNOT VERIFY."""
    (mod._tmp / "docs/evidence/latin1.md").write_bytes(
        "# X\n\nepoch 6 leads (0.5000 vs 0.4630), \u00b1 0.05.\n".encode("latin-1"))
    assert mod.main(["--check", "ordering-needs-band"]) == 1
    out = capsys.readouterr().out
    assert "CANNOT VERIFY ordering-needs-band" in out and "not valid UTF-8" in out


def test_a_symlinked_root_is_not_silently_empty(mod, capsys):
    """`os.walk`'s default contributes ZERO files for a symlinked directory — a narrowed
    instrument with no signal, which is this file's whole subject."""
    import os
    real = mod._tmp / "elsewhere"
    real.mkdir()
    (real / "linked.md").write_text(
        "# Linked\n\nThe arms are identical at all eight k, full stop.\n",
        encoding="utf-8")
    os.symlink(real, mod._tmp / "docs/evidence/via_symlink")
    assert mod.main(["--check", "no-difference-range"]) == 1
    assert "via_symlink/linked.md" in capsys.readouterr().out


def test_a_written_declaration_passes_and_is_printed(mod, capsys):
    """A marker is a claim, so the opt-out is not silent: the declared reason is
    printed on every passing run, which is the cheapest defence against a marker
    nobody re-reads."""
    _write(mod, "scripts/analysis/bad.py",
           "# design-weights: NOT READ — these are candidate rows for reading, "
           "not rates.\n" + BAD_PY)
    assert mod.main(["--check", "design-weights-read"]) == 0
    out = capsys.readouterr().out
    assert "NOTE design-weights-read" in out
    assert "candidate rows for reading" in out


def test_a_stale_registry_path_reads_as_cannot_verify(mod, capsys):
    """If nothing in the tree references any registered population, the check is
    pointed at a moved file and is proving nothing."""
    (mod._tmp / "scripts/analysis/good.py").unlink()
    _write(mod, "scripts/analysis/unrelated.py", "x = 1\n")
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "the paths in DESIGN_WEIGHTED are stale" in capsys.readouterr().out


def test_an_empty_code_root_names_the_code_roots(mod, capsys):
    """⛔ THE MESSAGE HAS TO NAME THE RIGHT ROOTS. The shared verdict helper defaulted to
    the DOC roots, so this check reported `docs/evidence, docs/decisions` while looking for
    python under three different directories."""
    (mod._tmp / "scripts/analysis/good.py").unlink()
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "scan root(s) scripts/analysis" in capsys.readouterr().out


def test_a_manifest_that_no_longer_declares_a_design_is_cannot_verify(mod, capsys):
    """The registry is hand-maintained, which is this project's most reliable
    source of measurement error — so it is not trusted on its own word. The draw
    manifest has to still describe a weighted design."""
    _write(mod, "docs/evidence/2026-08-29-v8-corpus-draw/corpus_manifest.json",
           {"filter": "human_thriving", "version": "v8"})
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "no longer declares `design_cells`" in capsys.readouterr().out


def test_a_missing_manifest_is_cannot_verify(mod, capsys):
    (mod._tmp / "docs/evidence/2026-08-29-v8-corpus-draw/corpus_manifest.json").unlink()
    assert mod.main(["--check", "design-weights-read"]) == 1
    assert "unbacked" in capsys.readouterr().out


# ────────────────────────────────────────────── CLI and the real tree

def test_an_unknown_check_name_is_cannot_verify(mod, capsys):
    assert mod.main(["--check", "no-such-check"]) == 1
    assert "CANNOT VERIFY: unknown check" in capsys.readouterr().out


def test_argv_is_a_parameter_not_sys_argv(mod):
    """Imported by pytest, `main()` must not read pytest's own arguments — the
    defect `check_index_budget.py` shipped for ten minutes on 2026-08-26."""
    assert mod.main() == 0


def test_the_real_repository_is_clean(capsys):
    """Runs the checks against the ACTUAL tree, not a fixture. This is the
    assertion that makes the four checks part of the battery rather than a
    self-contained toy — and the one that will fail when a future evidence
    document publishes one of these four shapes."""
    spec = importlib.util.spec_from_file_location("check_claim_shapes_real", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.main([]) == 0, capsys.readouterr().out
