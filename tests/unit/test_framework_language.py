"""ADR-013 language check (scripts/verification/check_framework_language.py, LD#160).

The first compliance sweep (2026-09-17) returned zero because its control was of the wrong class: Dutch sentences,
not Dutch lens NAMES. These tests seed true positives of the class under test and assert the checker goes red on
them, then pin each carve-out so it cannot silently widen."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cfl", ROOT / "scripts" / "verification" / "check_framework_language.py")
cfl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfl)


def verdicts(path, text):
    return [v for _, _, _, v in cfl.classify(path, text)]


def test_dutch_lens_names_in_identifiers_and_prose_are_violations():
    assert verdicts("scripts/x.py", "s1_welzijn = 0\nfor tab in tabs:\n    print(tab)\n") == ["violation"]
    assert verdicts("scripts/x.py", "print(fmt.format('Scenario', 'welz', 'erfg'))\n") == ["violation", "violation"]
    assert verdicts("docs/x.md", "- Welzijn: who is flourishing?\n") == ["violation"]
    assert verdicts("filters/x/config.yaml", "notes:\n  - \"ovr.news 'Herstel' tab\"\n") == ["violation"]


def test_carve_outs_admit_only_their_role():
    # a regex match pattern is data (deleting it changes what the code matches)
    assert verdicts("filters/x.py", "import re\nP = [(r'\\b(heritage|erfgoed)\\b', re.IGNORECASE, 'h')]\n") == ["match pattern"]
    assert verdicts("filters/x.py", "import re\nX = re.compile('erfgoed')\n") == ["match pattern"]
    assert verdicts("filters/x.py", "HERITAGE_PATTERNS = ['erfgoed']\n") == ["match pattern"]
    # ...but a plain string literal in Python is NOT a pattern
    assert verdicts("filters/x.py", "LABEL = 'Erfgoed tab'\n") == ["violation"]
    # a backticked or quoted name in Markdown is a mention
    assert verdicts("docs/x.md", "The `Herstel` tab and `Leren` were renamed.\n") == ["quoted mention"] * 2
    # quotes LABEL a tab, and apostrophes mis-pair: neither is a mention (review 2026-10-07)
    assert verdicts("docs/x.md", '**ovr.news tab:** "Herstel"\n') == ["violation"]
    assert verdicts("docs/x.md", "The filter's Welzijn tab isn't ready.\n") == ["violation"]
    # verbatim archives are records
    assert verdicts("memory/archive/x.md", "Welzijn\n") == ["frozen record"]
    # the historical record the owner ruled on
    assert verdicts("docs/adr/009-add-filters-first-reduce-later.md", "Welzijn: x\n")[0].startswith("historical")


def test_names_inside_english_words_do_not_match():
    assert verdicts("docs/x.md", "Herstellung and learners and welzijnish\n") == []


def test_the_repository_is_clean_apart_from_known_open_entries():
    assert cfl.main([]) == 0


def test_fixture_strings_in_tests_are_data_but_their_comments_are_not():
    assert verdicts("tests/unit/test_x.py", "ROWS = ['Welzijn tab']  # a fixture\n") == ["fixture/match data"]
    assert verdicts("tests/unit/test_x.py", "x = 1  # the Welzijn tab\n") == ["violation"]


def test_string_detection_survives_apostrophes_in_comments():
    """A regex over the source paired the apostrophe in "checker's" with a later quote and misread everything after."""
    src = "# the checker's list\nLABEL = 'x'\nNOTE = \"the 'Erfgoed' tab\"\n"
    assert verdicts("scripts/x.py", src) == ["violation"]  # a plain string, not a pattern: still a violation
    assert verdicts("tests/unit/t.py", src) == ["fixture/match data"]


def test_docstrings_and_pipes_are_not_data():
    """Review 2026-10-07: a docstring in a test, a `|` in a docstring and a raw docstring all passed as data."""
    assert verdicts("tests/unit/t.py", '"""The Welzijn tab must stay first."""\nX = 1\n') == ["violation"]
    assert verdicts("scripts/x.py", '"""Columns: Welzijn | Erfgoed"""\n') == ["violation", "violation"]
    assert verdicts("scripts/x.py", 'def f():\n    r"""The Welzijn tab."""\n') == ["violation"]
    assert verdicts("scripts/x.py", 'HELP = "rank tabs: welzijn|erfgoed"\n') == ["violation", "violation"]


def test_the_belonging_tab_name_is_in_the_list():
    assert verdicts("docs/x.md", "the Verbondenheid tab\n") == ["violation"]
