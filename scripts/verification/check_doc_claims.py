#!/usr/bin/env python3
"""Cross-layer claim checks for the always-loaded and operational docs,
held OUTSIDE the files they check.

`CLAUDE.md` restates things that live elsewhere — an occurrence count whose
canonical home is `memory/working-rules.md`, a deployment state whose canonical
home is `memory/filter-status.md`, a framework stamp it writes twice. Each
restatement can drift, so each carries a check. Until 2026-08-29 those checks were
four `<!-- verify: -->` shell one-liners INSIDE `CLAUDE.md`.

⛔ WHY THEY MOVED, AND WHY NONE MAY GO BACK. They measured 2,047 bytes — 5.5% of
the file — against a 40,000-byte wall the file was 2,555 bytes from, so the guards
were spending the budget of the thing they policed. `check_index_budget.py` was
moved out of `memory/MEMORY.md` for exactly this on 2026-08-17, when adding a stage
inline would have tripped the guard on landing; the same argument reached
`CLAUDE.md` two weeks later. Out here they can also carry their own reasoning,
which a one-liner cannot afford. **A new claim check on `CLAUDE.md` is a function
here plus a row in `CHECKS`, never a comment in the file.**

⚠️ WHAT THIS IS NOT. It does not check that a claim is TRUE — only that the two
layers stating it AGREE. Two copies can agree and both be stale; that is why the
underlying rule (#133) is to stop restating, and why every check below is a
consolation prize for a restatement that has not been removed yet.

    python3 scripts/verification/check_doc_claims.py              # all
    python3 scripts/verification/check_doc_claims.py --check cd-v6-row

Annotated from `memory/MEMORY.md`, NOT from `CLAUDE.md` — see above.
Exit 0 when every selected check passes, 1 otherwise. A check that cannot extract
what it compares is CANNOT VERIFY and exits 1: this repo's signature defect is a
guard that reports success because it looked at nothing.
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLAUDE = os.path.join(ROOT, "CLAUDE.md")
RULES = os.path.join(ROOT, "memory", "working-rules.md")
FILTER_STATUS = os.path.join(ROOT, "memory", "filter-status.md")
RUNBOOK = os.path.join(ROOT, "docs", "RUNBOOK.md")
BATCH_SCORER = os.path.join(ROOT, "ground_truth", "batch_scorer.py")

ORDINAL = re.compile(r"(\d+)(?:st|nd|rd|th)\b")

# (label, CLAUDE.md bullet opener, memory/working-rules.md line fragment).
# ⚠️ MATCHED ON THE RULE'S OWN WORDS, NOT ON LINE OFFSETS. The shell versions used
# `sed -n '/…/,+3p'`, so the check silently changed subject whenever the bullet was
# rewrapped — and a bullet one line longer would have compared the rule against
# whatever followed it.
RULE_ORDINALS = [
    ("gate/cap/threshold caller",
     "Before shipping any gate",
     "Before shipping any gate"),
    ("establish what a source excludes",
     "Before using any source as evidence",
     "establish what it excludes"),
]


def _read(path, label):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return None, f"CANNOT VERIFY: {label} missing or empty"
    return open(path, encoding="utf-8").read(), None


def _bullet(text, opener):
    """The CLAUDE.md bullet that starts with `- **<opener>`, to the next bullet.

    Returns None when no bullet opens with it — a rule that was renamed must read
    as CANNOT VERIFY, never as a pass on an empty string.
    """
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines)
                  if l.startswith("- **" + opener)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("- ") or lines[i].startswith("#")), len(lines))
    return "\n".join(lines[start:end])


def check_rule_ordinals():
    """`CLAUDE.md`'s occurrence count must equal `memory/working-rules.md`'s.

    ⚠️ THE COUNT IS CANONICAL IN `working-rules.md` — `CLAUDE.md` says so in the
    rule's own text. This check is what stops the always-loaded copy going stale
    against it, which is the failure mode #133 names: the surface that restates is
    the surface that rots.

    Compared on the MAXIMUM ordinal on each side, matching the shell version that
    used `sort -n | tail -1`, because both files write the current count first and
    the older occurrences after it.
    """
    out, rc = [], 0
    cm, err = _read(CLAUDE, "CLAUDE.md")
    if err:
        return 1, [err]
    wr, err = _read(RULES, "memory/working-rules.md")
    if err:
        return 1, [err]
    wr_lines = wr.split("\n")
    for label, opener, frag in RULE_ORDINALS:
        bullet = _bullet(cm, opener)
        if bullet is None:
            out.append(f"CANNOT VERIFY: no CLAUDE.md bullet opens with {opener!r} "
                       f"({label}) — renamed, or the rule is gone")
            rc = 1
            continue
        wr_line = next((l for l in wr_lines if frag.lower() in l.lower()), None)
        if wr_line is None:
            out.append(f"CANNOT VERIFY: {frag!r} not found in "
                       f"memory/working-rules.md ({label})")
            rc = 1
            continue
        cm_ords = [int(m) for m in ORDINAL.findall(bullet)]
        wr_ords = [int(m) for m in ORDINAL.findall(wr_line)]
        if not cm_ords or not wr_ords:
            out.append(f"CANNOT VERIFY: no ordinal extracted for {label} "
                       f"(CLAUDE.md={cm_ords}, working-rules.md={wr_ords})")
            rc = 1
            continue
        c, w = max(cm_ords), max(wr_ords)
        if c != w:
            out.append(f"FAIL {label}: CLAUDE.md says {c}, "
                       f"memory/working-rules.md says {w} — the canonical count is "
                       f"working-rules.md; fix CLAUDE.md, not the other way round")
            rc = 1
        else:
            out.append(f"PASS {label}: both layers say {c}")
    return rc, out


def check_cd_v6_row():
    """`cultural_discovery` v6 is NOT deployed, in both layers.

    The two layers disagreed on this once already — 2026-08-13 to 08-16, after the
    cutover failed and was reverted — and a filter's deployment state read off the
    wrong layer is what decides whether someone scores against it.
    """
    cm, err = _read(CLAUDE, "CLAUDE.md")
    if err:
        return 1, [err]
    fs, err = _read(FILTER_STATUS, "memory/filter-status.md")
    if err:
        return 1, [err]
    n_cm = len(re.findall(
        r"cultural-discovery\*\* \| v6 \| \(v5.s\) \| \*\*NOT DEPLOYED\*\*", cm))
    n_fs = fs.count("CUTOVER ATTEMPTED, FAILED AND REVERTED")
    if n_cm == 1 and n_fs == 1:
        return 0, ["PASS cd v6: both layers say it is not deployed"]
    return 1, [f"FAIL cd v6: CLAUDE.md not-deployed row={n_cm}, "
               f"memory/filter-status.md reverted marker={n_fs} — the two layers "
               f"disagreed on this once already (2026-08-13 to 08-16)"]


def check_framework_stamp():
    """`CLAUDE.md` writes the framework version twice; they must match.

    Frontmatter `framework:` and the footer's `Framework:` line. ⚠️ This compares a
    file with ITSELF — it cannot tell you whether either is the version actually
    pinned upstream. `/update-drift` is what answers that; this only stops the two
    stamps disagreeing after a partial edit.
    """
    cm, err = _read(CLAUDE, "CLAUDE.md")
    if err:
        return 1, [err]
    fm = re.search(r"^framework: agent-ready-projects (v[0-9.]+)", cm, re.M)
    ft = re.search(r"Framework: agent-ready-projects (v[0-9.]+)", cm)
    if not fm:
        return 1, ["CANNOT VERIFY: no frontmatter framework stamp in CLAUDE.md"]
    if not ft:
        return 1, ["CANNOT VERIFY: no footer framework stamp in CLAUDE.md"]
    if fm.group(1) == ft.group(1):
        return 0, [f"PASS framework stamp: both say {fm.group(1)}"]
    return 1, [f"FAIL framework stamp: frontmatter {fm.group(1)}, "
               f"footer {ft.group(1)}"]


def _llm_flag_spec():
    """`--llm`'s `choices` and `default`, read from the parser itself.

    ⚠️ READ FROM THE CODE, NEVER FROM A DOC. The whole point is that the doc drifted:
    `docs/RUNBOOK.md` documented the oracle command for months without naming the
    flag, its options, or that it defaults to `claude` — while the project's oracle
    decisions were about Gemini and DeepSeek. Parsed with `ast` rather than grep so
    a reformat of the call does not silently return an empty spec.

    Returns (choices, default) or (None, None) when the call cannot be found — which
    the caller must treat as CANNOT VERIFY, never as agreement.
    """
    try:
        tree = ast.parse(open(BATCH_SCORER, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return None, None
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            continue
        if not any(isinstance(a, ast.Constant) and a.value == "--llm" for a in node.args):
            continue
        choices = default = None
        for kw in node.keywords:
            if kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple)):
                choices = [e.value for e in kw.value.elts if isinstance(e, ast.Constant)]
            elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
                default = kw.value.value
        return choices, default
    return None, None


def check_runbook_oracle_flags():
    """`docs/RUNBOOK.md` must name every `--llm` option and the default it ships.

    ⛔ WHAT THIS EXISTS TO STOP. Until 2026-08-29 the RUNBOOK's oracle command was
    `python -m ground_truth.batch_scorer --filter ... --source ...` with no `--llm`
    at all — so following the runbook scored against **`claude`**, the default,
    while every oracle decision on record was about Gemini or DeepSeek. DeepSeek is
    not even a valid value: it runs through `scripts/score_deepseek_production.py`,
    a different script the runbook did not mention. A doc that silently selects a
    different oracle than the one you decided on costs a paid run.

    ⚠️ It checks NAMING, not correctness — it cannot tell you which oracle a filter
    should use. That is per-filter, and for v8 it is still an open question for the
    owner (plan §9).
    """
    choices, default = _llm_flag_spec()
    if not choices or not default:
        return 1, [f"CANNOT VERIFY: could not read --llm's choices/default from "
                   f"ground_truth/batch_scorer.py (got {choices!r}, {default!r}) — "
                   f"the flag was renamed or the call reshaped; fix this check first"]
    rb, err = _read(RUNBOOK, "docs/RUNBOOK.md")
    if err:
        return 1, [err]
    missing = [c for c in choices if f"`{c}`" not in rb]
    out, rc = [], 0
    if missing:
        rc = 1
        out.append(f"FAIL runbook oracle flags: --llm accepts {len(choices)} providers "
                   f"and docs/RUNBOOK.md never names {missing} — following the runbook "
                   f"then silently uses the default")
    if f"**`{default}`**" not in rb:
        rc = 1
        out.append(f"FAIL runbook oracle flags: --llm defaults to {default!r} and "
                   f"docs/RUNBOOK.md does not say so in bold — the default is the "
                   f"value a reader gets by omitting the flag")
    if "score_deepseek_production.py" not in rb:
        rc = 1
        out.append("FAIL runbook oracle flags: the DeepSeek oracle is a separate "
                   "script (scripts/score_deepseek_production.py) and the runbook "
                   "does not mention it — a reader concludes DeepSeek is unavailable")
    if not rc:
        out.append(f"PASS runbook oracle flags: all {len(choices)} --llm providers "
                   f"named, default {default!r} stated, DeepSeek path named")
    return rc, out


CHECKS = {
    "rule-ordinals":   check_rule_ordinals,
    "cd-v6-row":       check_cd_v6_row,
    "framework-stamp": check_framework_stamp,
    "runbook-oracle-flags": check_runbook_oracle_flags,
}


def main(argv=None):
    """`argv` is a PARAMETER, not `sys.argv` — an imported caller (the tests) would
    otherwise be handed pytest's arguments. Same defect as `check_index_budget.py`
    shipped for ten minutes on 2026-08-26."""
    if argv is None:
        argv = []
    names = list(CHECKS)
    if argv:
        if argv[0] == "--check" and len(argv) > 1:
            sel = argv[1]
        elif argv[0].startswith("--check="):
            sel = argv[0].split("=", 1)[1]
        else:
            print(f"CANNOT VERIFY: unknown argument {argv[0]!r}; expected "
                  f"--check {'|'.join(names + ['all'])}")
            return 1
        if sel != "all":
            if sel not in CHECKS:
                print(f"CANNOT VERIFY: unknown check {sel!r}; expected one of "
                      f"{', '.join(names + ['all'])}")
                return 1
            names = [sel]

    rc, lines = 0, []
    for name in names:
        code, out = CHECKS[name]()
        rc = rc or code
        lines.extend(out)
    # ⚠️ FAILURES FIRST, THEN A SUMMARY LAST, AND BOTH HALVES ARE LOAD-BEARING.
    # `run_verify_annotations.py` anchors on a line-initial FAIL/CANNOT VERIFY
    # anywhere in the output, but reports the LAST line for a passing block -- so
    # without the summary a green run is reported as whichever single check
    # happened to print last, and a reader of the verify report cannot tell that
    # the other three ran at all.
    lines.sort(key=lambda l: 0 if l.startswith(("FAIL", "CANNOT VERIFY")) else 1)
    bad = sum(1 for l in lines if l.startswith(("FAIL", "CANNOT VERIFY")))
    for l in lines:
        print(l)
    verdict = "FAIL" if bad else "PASS"
    print(f"{verdict} {len(lines) - bad}/{len(lines)} doc claims agree, "
          f"over {len(names)} check(s): {', '.join(names)}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
