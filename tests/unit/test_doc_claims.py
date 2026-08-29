"""`CLAUDE.md`'s cross-layer claim checks (llm-distillery#133/#138).

These four assertions used to be `<!-- verify: -->` shell one-liners inside
`CLAUDE.md` itself — 2,047 bytes, 5.5% of a file that was 2,555 bytes from its
40,000-byte wall. A guard that lives inside its subject spends the budget it is
policing, which is the argument that moved `check_index_budget.py` out of
`memory/MEMORY.md` on 2026-08-17.

⚠️ EVERY TEST HERE SEEDS THE FAILURE IT CLAIMS TO CATCH. A rewrite of a working
check is the case where a green suite proves least: the old one-liners passed, and
so does the new script, so "it still passes" distinguishes a faithful port from a
check that stopped looking at anything. Each test below therefore edits a fixture
into the broken state and asserts the FAIL — and `test_a_faithful_port` pins the
verdicts the shell version produced on the day it was replaced.
"""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "scripts", "verification", "check_doc_claims.py")

CLAUDE_FIXTURE = """---
framework: agent-ready-projects v1.36.1
---
# CLAUDE.md

- **Before shipping any gate, cap, threshold, config key or stamp — name the
  caller.** *(16th occurrence 2026-08-25 — a thing broke. 15th — another.)* More
  prose that belongs to this bullet.
- **Before using any source as evidence, establish what it EXCLUDES.** *(14th
  occurrence 2026-08-29 — a thing. 13th 2026-08-28 — another.)* Trailing prose.
- **Something else entirely.** Not a rule with an ordinal.

| **cultural-discovery** | v6 | (v5's) | **NOT DEPLOYED** — offline only |

*Framework: agent-ready-projects v1.36.1 — triaged.*
"""

RULES_FIXTURE = """# Working rules

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller.** *(16th occurrence 2026-08-25 — the full story.)* Evidence.
- **Before using any source as evidence, establish what it excludes.** *(14th occurrence 2026-08-29 — the full story.)* Evidence.
"""

STATUS_FIXTURE = "# Filter status\n\ncd v6: CUTOVER ATTEMPTED, FAILED AND REVERTED on 2026-08-13.\n"

RUNBOOK_FIXTURE = """# Runbook

`--llm` accepts `claude` | `gemini` | `gpt4`, defaulting to **`claude`**.
DeepSeek runs through `scripts/score_deepseek_production.py`, a separate script.
"""

# A miniature argparse call — the check reads this with `ast`, not with grep, so the
# fixture has to be real syntax rather than a lookalike string.
SCORER_FIXTURE = """import argparse
def build():
    parser = argparse.ArgumentParser()
    parser.add_argument('--llm', default='claude',
                        choices=['claude', 'gemini', 'gpt4'],
                        help='LLM provider')
    return parser
"""


@pytest.fixture
def mod(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_doc_claims", GUARD)
    m = importlib.util.module_from_spec(spec)
    sys.modules["check_doc_claims"] = m
    spec.loader.exec_module(m)
    for attr, name, body in (("CLAUDE", "CLAUDE.md", CLAUDE_FIXTURE),
                             ("RULES", "working-rules.md", RULES_FIXTURE),
                             ("FILTER_STATUS", "filter-status.md", STATUS_FIXTURE),
                             ("RUNBOOK", "RUNBOOK.md", RUNBOOK_FIXTURE),
                             ("BATCH_SCORER", "batch_scorer.py", SCORER_FIXTURE)):
        p = tmp_path / name
        p.write_text(body, encoding="utf-8")
        monkeypatch.setattr(m, attr, str(p))
    m._tmp = tmp_path
    return m


def _edit(mod, attr, old, new):
    p = getattr(mod, attr)
    s = open(p, encoding="utf-8").read()
    assert s.count(old) == 1, f"fixture no longer contains {old!r} exactly once"
    open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))


def test_the_healthy_fixture_passes(mod, capsys):
    assert mod.main([]) == 0
    out = capsys.readouterr().out
    assert "FAIL" not in out and "CANNOT VERIFY" not in out
    assert out.strip().splitlines()[-1].startswith("PASS 5/5 doc claims agree")


# --------------------------------------------------------------- rule ordinals

def test_a_drifted_ordinal_fails_and_names_the_canonical_side(mod, capsys):
    """THE WHOLE POINT. `CLAUDE.md` restates a count whose home is
    `working-rules.md`; the restating surface is the one that rots."""
    _edit(mod, "CLAUDE", "*(16th occurrence 2026-08-25", "*(17th occurrence 2026-08-25")
    assert mod.main(["--check", "rule-ordinals"]) == 1
    out = capsys.readouterr().out
    assert "FAIL gate/cap/threshold caller" in out
    assert "CLAUDE.md says 17" in out and "working-rules.md says 16" in out
    assert "canonical count is working-rules.md" in out


def test_the_second_rules_ordinal_is_also_compared(mod, capsys):
    """Two rules carry ordinals. A check that silently covered only the first
    would pass every test written about the first."""
    _edit(mod, "RULES", "*(14th occurrence 2026-08-29", "*(99th occurrence 2026-08-29")
    assert mod.main(["--check", "rule-ordinals"]) == 1
    assert "FAIL establish what a source excludes" in capsys.readouterr().out


def test_a_renamed_rule_cannot_verify_rather_than_passing(mod, capsys):
    """The signature defect: a guard whose subject moved reports success. Renaming
    the bullet must be loud."""
    _edit(mod, "CLAUDE", "- **Before shipping any gate", "- **Before shipping any GATE")
    assert mod.main(["--check", "rule-ordinals"]) == 1
    out = capsys.readouterr().out
    assert "CANNOT VERIFY" in out and "Before shipping any gate" in out


def test_a_rule_missing_from_working_rules_cannot_verify(mod, capsys):
    _edit(mod, "RULES", "Before shipping any gate", "Before shipping any widget")
    assert mod.main(["--check", "rule-ordinals"]) == 1
    assert "CANNOT VERIFY" in capsys.readouterr().out


def test_an_ordinal_removed_from_claude_md_cannot_verify(mod, capsys):
    """Trimming the occurrence catalogue out of `CLAUDE.md` is a legitimate move
    (#133) — but it retires this check, so it must say so rather than pass."""
    _edit(mod, "CLAUDE", "*(16th occurrence 2026-08-25 — a thing broke. 15th — another.)*", "")
    assert mod.main(["--check", "rule-ordinals"]) == 1
    assert "no ordinal extracted" in capsys.readouterr().out


def test_the_bullet_scope_ends_at_the_next_bullet(mod, capsys):
    """THE DEFECT IN THE SHELL VERSION. It read `sed -n '/…/,+3p'`, a fixed line
    window, so rewrapping a bullet changed what the check compared. Here an ordinal
    belonging to the NEXT rule must not be picked up by this one."""
    _edit(mod, "CLAUDE",
          "- **Something else entirely.** Not a rule with an ordinal.",
          "- **Something else entirely.** The 88th occurrence of something.")
    assert mod.main(["--check", "rule-ordinals"]) == 0
    assert "both layers say 14" in capsys.readouterr().out


# ------------------------------------------------------------------- cd v6 row

def test_a_deployed_looking_cd_v6_row_fails(mod, capsys):
    _edit(mod, "CLAUDE", "**NOT DEPLOYED**", "**DEPLOYED**")
    assert mod.main(["--check", "cd-v6-row"]) == 1
    assert "FAIL cd v6" in capsys.readouterr().out


def test_the_reverted_marker_disappearing_from_filter_status_fails(mod, capsys):
    """The two layers disagreed on this once already, 2026-08-13 to 08-16."""
    _edit(mod, "FILTER_STATUS", "CUTOVER ATTEMPTED, FAILED AND REVERTED", "cutover fine")
    assert mod.main(["--check", "cd-v6-row"]) == 1
    assert "reverted marker=0" in capsys.readouterr().out


# ------------------------------------------------------------ framework stamp

def test_disagreeing_framework_stamps_fail(mod, capsys):
    _edit(mod, "CLAUDE", "*Framework: agent-ready-projects v1.36.1", "*Framework: agent-ready-projects v1.37.0")
    assert mod.main(["--check", "framework-stamp"]) == 1
    out = capsys.readouterr().out
    assert "frontmatter v1.36.1" in out and "footer v1.37.0" in out


def test_a_missing_frontmatter_stamp_cannot_verify(mod, capsys):
    _edit(mod, "CLAUDE", "framework: agent-ready-projects v1.36.1", "framework: none")
    assert mod.main(["--check", "framework-stamp"]) == 1
    assert "no frontmatter framework stamp" in capsys.readouterr().out


# ------------------------------------------------------------------ mechanics

def test_a_missing_file_cannot_verify(mod, capsys):
    os.remove(mod.RULES)
    assert mod.main(["--check", "rule-ordinals"]) == 1
    out = capsys.readouterr().out
    assert "CANNOT VERIFY" in out
    # Pin the DOCUMENTED branch, not just the outcome. Making `_read` hand back an
    # empty string instead of an error survived every other test here: each check
    # then failed closed for a different reason and the exit code was identical.
    # That is an equivalent mutant only as long as nothing downstream ever treats
    # "" as a readable file, which is not a property anyone maintains.
    assert "missing or empty" in out


def test_an_unknown_check_cannot_verify(mod, capsys):
    assert mod.main(["--check", "nope"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("CANNOT VERIFY")
    assert "rule-ordinals" in out and "cd-v6-row" in out and "framework-stamp" in out


def test_main_ignores_the_host_processes_argv(mod, capsys):
    """`check_index_budget.py` shipped this defect for ten minutes on 2026-08-26:
    reading `sys.argv` handed every importing caller pytest's arguments."""
    assert mod.main() == 0
    assert mod.main(None) == 0


def test_a_failure_is_reported_even_when_other_checks_pass(mod, capsys):
    """`run_verify_annotations.py` reports the LAST line of a passing block, so a
    failure printed under three PASS lines would be invisible in the verify report
    unless failures sort first AND the summary itself says FAIL."""
    _edit(mod, "CLAUDE", "**NOT DEPLOYED**", "**DEPLOYED**")
    assert mod.main([]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert out[0].startswith("FAIL")
    assert out[-1].startswith("FAIL 4/5 doc claims agree")


def test_a_faithful_port_of_the_shell_one_liners(capsys):
    """THE REAL FILES. Pins the verdicts the four inline `<!-- verify: -->` blocks
    produced on 2026-08-29, the day they were removed: 16, 14, both-layers-agree,
    v1.36.1. Green here does not prove the port faithful on its own — that is what
    the seeded failures above are for — but a silent change of subject would show."""
    spec = importlib.util.spec_from_file_location("cdc_shipped", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.main([]) == 0
    out = capsys.readouterr().out
    assert "PASS gate/cap/threshold caller" in out
    assert "PASS establish what a source excludes" in out
    assert "PASS cd v6: both layers say it is not deployed" in out
    assert "PASS framework stamp" in out


def test_no_verify_block_has_crept_back_into_claude_md():
    """⛔ THE RULE THIS FILE EXISTS TO ENFORCE. A guard inside `CLAUDE.md` spends
    the budget it polices; the four that were there cost 5.5% of the file. A new
    claim check is a function in the script plus a row in CHECKS."""
    body = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
    assert "<!-- verify:" not in body, (
        "a <!-- verify: --> block is back in CLAUDE.md — move it into "
        "scripts/verification/check_doc_claims.py and annotate from "
        "memory/MEMORY.md instead")


# --------------------------------------------------------- runbook oracle flags

def test_a_provider_the_runbook_never_names_fails(mod, capsys):
    """⛔ THE DEFECT ITSELF. Until 2026-08-29 the runbook's oracle command carried no
    `--llm` at all, so following it scored against `claude` — the default — while
    every oracle decision on record was about Gemini or DeepSeek."""
    _edit(mod, "RUNBOOK", "`claude` | `gemini` | `gpt4`", "`claude` | `gemini`")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    out = capsys.readouterr().out
    assert "FAIL runbook oracle flags" in out and "'gpt4'" in out


def test_a_provider_ADDED_to_the_code_fails_until_the_runbook_says_so(mod, capsys):
    """The drift runs both ways: a new provider in the parser that no doc mentions is
    a capability nobody knows exists."""
    _edit(mod, "BATCH_SCORER", "'claude', 'gemini', 'gpt4'", "'claude', 'gemini', 'gpt4', 'deepseek'")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    assert "'deepseek'" in capsys.readouterr().out


def test_an_unstated_default_fails(mod, capsys):
    """The default is what a reader GETS by omitting the flag, so it is the one value
    that must be unmissable."""
    _edit(mod, "RUNBOOK", "defaulting to **`claude`**", "defaulting to something")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    assert "does not say so in bold" in capsys.readouterr().out


def test_a_CHANGED_default_fails_even_though_the_word_is_present(mod, capsys):
    """⚠️ THE SUBTLE ONE. `claude` still appears in the runbook as a valid choice, so a
    check that only looked for the word would pass while the documented default was
    wrong. It is the BOLD form that carries the claim."""
    _edit(mod, "BATCH_SCORER", "default='claude'", "default='gemini'")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    out = capsys.readouterr().out
    assert "defaults to 'gemini'" in out


def test_dropping_the_deepseek_script_reference_fails(mod, capsys):
    """DeepSeek is not a `--llm` value; a runbook that omits the separate script
    reads as 'DeepSeek is unavailable'."""
    _edit(mod, "RUNBOOK", "`scripts/score_deepseek_production.py`", "`some/other/script.py`")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    assert "separate script" in capsys.readouterr().out


def test_an_unreadable_flag_spec_cannot_verify(mod, capsys):
    """⛔ If the parser call is reshaped or the flag renamed, this check can no longer
    see its subject. That is CANNOT VERIFY — a guard that lost its subject must never
    report agreement."""
    _edit(mod, "BATCH_SCORER", "'--llm'", "'--oracle'")
    assert mod.main(["--check", "runbook-oracle-flags"]) == 1
    out = capsys.readouterr().out
    assert "CANNOT VERIFY" in out and "renamed or the call reshaped" in out


def test_the_shipped_runbook_names_every_provider_it_could_be_run_with():
    """THE REAL FILES: docs/RUNBOOK.md against ground_truth/batch_scorer.py."""
    spec = importlib.util.spec_from_file_location("cdc_runbook", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    choices, default = m._llm_flag_spec()
    assert choices and default, "the --llm spec could not be read from the real scorer"
    assert m.main(["--check", "runbook-oracle-flags"]) == 0
