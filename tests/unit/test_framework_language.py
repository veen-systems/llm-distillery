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
    assert verdicts("filters/x.py", "P = [(r'\\b(heritage|erfgoed)\\b', 0)]\n") == ["match pattern"]
    # ...but a plain string literal in Python is NOT a pattern
    assert verdicts("filters/x.py", "LABEL = 'Erfgoed tab'\n") == ["violation"]
    # a backticked or quoted name in Markdown is a mention
    assert verdicts("docs/x.md", "The `Herstel` tab and \"Leren\" were renamed.\n") == ["quoted mention"] * 2
    # the historical record the owner ruled on
    assert verdicts("docs/adr/009-add-filters-first-reduce-later.md", "Welzijn: x\n")[0].startswith("historical")


def test_names_inside_english_words_do_not_match():
    assert verdicts("docs/x.md", "Herstellung and learners and welzijnish\n") == []


def test_the_repository_is_clean_apart_from_known_open_entries():
    assert cfl.main([]) == 0
