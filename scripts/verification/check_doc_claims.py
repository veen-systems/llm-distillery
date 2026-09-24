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
REVIEW_PROFILE = os.path.join(ROOT, ".claude", "review-profile.md")

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
    """The occurrence COUNT lives in `memory/working-rules.md` and NOWHERE ELSE.

    ⛔ THIS CHECK WAS INVERTED ON 2026-09-04, and the reason is the point. It used to
    require `CLAUDE.md` and `memory/working-rules.md` to state the SAME ordinal — which
    kept the always-loaded copy honest, but made the count un-relocatable: every bump had
    to land in the project file too. Measured over four `/curate` runs, those counters were
    a MONOTONIC FLOOR on a file that degrades past 40,000 B, and H-CX3 recorded the trigger
    firing four times while every other lever (eviction, trimming, padding) was spent.

    The stronger contract, and the one enforced here: a copy that does not exist cannot go
    stale. So `CLAUDE.md` carries the IMPERATIVE and a pointer, `working-rules.md` carries
    the count and the evidence, and this check now fails if the project file starts
    restating the number again.

    Three assertions per rule:
      1. `working-rules.md` states an ordinal        — the canonical count exists
      2. `CLAUDE.md`'s bullet states NO ordinal      — the copy that rots is absent
      3. `CLAUDE.md`'s bullet points at the file     — the reader can still reach it

    (2) is the one with teeth. (1) and (3) stop the rule being emptied out entirely, which
    would otherwise satisfy (2) perfectly.

    ⛔ DISCLOSED LIMIT, measured by mutation on the day this was written. Assertion (1)
    checks that AN ordinal exists, not that it is the RIGHT one — and the occurrence
    catalogue is a single line carrying every past ordinal, so deleting the newest one
    leaves `max()` on the second-newest and the check still passes. Mutation M3 (drop
    `18th` from `working-rules.md`) SURVIVED; M1 (restate the count in `CLAUDE.md`) and M2
    (drop the pointer) were both killed. So: this check stops the count being DUPLICATED or
    ORPHANED. It cannot stop it being WRONG, and nothing here can — the true count is a fact
    about the project's history, not about either file. Do not read a pass as validating the
    number.
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

        wr_ords = [int(m) for m in ORDINAL.findall(wr_line)]
        if not wr_ords:
            out.append(f"FAIL {label}: memory/working-rules.md states no ordinal — it is "
                       f"the canonical count and nothing else records it")
            rc = 1
            continue

        cm_ords = [int(m) for m in ORDINAL.findall(bullet)]
        if cm_ords:
            out.append(f"FAIL {label}: CLAUDE.md restates the count "
                       f"{sorted(set(cm_ords), reverse=True)}. The count belongs in "
                       f"memory/working-rules.md ONLY (currently {max(wr_ords)}) — an "
                       f"always-loaded copy can only grow and can only rot. Replace it "
                       f"with a pointer.")
            rc = 1
            continue

        if "working-rules.md" not in bullet:
            out.append(f"FAIL {label}: CLAUDE.md states no count (correct) and no pointer "
                       f"to memory/working-rules.md either — the reader cannot reach the "
                       f"evidence")
            rc = 1
            continue

        out.append(f"PASS {label}: count {max(wr_ords)} in working-rules.md only, "
                   f"CLAUDE.md points at it and restates nothing")
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
    # ⛔ CLAUDE.md CARRIES THE SAME COMMAND, AND IT IS THE ALWAYS-LOADED COPY.
    # Found by `/curate` Step 4 on 2026-08-29, minutes after the RUNBOOK was fixed:
    # the same `batch_scorer` invocation sat in CLAUDE.md's Getting Started with no
    # `--llm` either. Fixing one copy of a drifted command and not the other is how
    # the drift survives the session that found it.
    cm, cerr = _read(CLAUDE, "CLAUDE.md")
    if cerr:
        return 1, [cerr]
    # ⛔ MATCH AN INVOCATION, NOT A MENTION — `python -m …`, not the bare dotted path.
    # The first version of this loop matched `ground_truth.batch_scorer` anywhere and
    # `break`ed on the first hit, which is a Hard Constraint reading "the floor lives in
    # `ground_truth.batch_scorer.make_oracle_prefilter`" — prose, 200 lines above the
    # command. It reported the fixed file as broken. That is *mention is not use* for the
    # THIRD time in one session, inside the guard written after the second one.
    for line in cm.split("\n"):
        if "python -m ground_truth.batch_scorer" in line and not line.lstrip().startswith("#"):
            if "--llm" not in line:
                rc = 1
                out.append("FAIL runbook oracle flags: CLAUDE.md invokes "
                           "ground_truth.batch_scorer without --llm — the always-loaded "
                           "copy of the command silently selects the default oracle")
            break
    if "score_deepseek_production.py" not in rb:
        rc = 1
        out.append("FAIL runbook oracle flags: the DeepSeek oracle is a separate "
                   "script (scripts/score_deepseek_production.py) and the runbook "
                   "does not mention it — a reader concludes DeepSeek is unavailable")
    if not rc:
        out.append(f"PASS runbook oracle flags: all {len(choices)} --llm providers "
                   f"named, default {default!r} stated, DeepSeek path named")
    return rc, out


SUITE_COUNT = re.compile(r"\b(\d{2,4}) passed, (\d+) skipped")
# ⚠️ FROZEN ACCOUNTS OF A MOMENT. A dated session record saying "on 2026-09-11 the suite
# was 828" stays true forever and is not a live copy. Same carve-out, same reasoning, as
# refcheck.py's --sessions and its docs/ FROZEN tier.
SUITE_HISTORY = ("memory/project_session_", "memory/session-log.md",
                 "docs/decisions/", "docs/evidence/")


def check_suite_baseline_single_copy():
    """`.claude/review-profile.md` says its test-suite count is the ONLY live copy.

    ⛔ THIS EXISTS BECAUSE THE CLAIM WAS BROKEN BY THE CHANGE THAT QUOTED IT. On
    2026-09-17 the #134 step-2 decision record wrote its own copy of `891 passed` into a
    controls table while citing the profile's rule in the sentence beside it — the third
    recorded occurrence, the first two being noted in the profile itself. A review lens
    caught it; `check_doc_claims.py` could not, because its four checks are hand-listed
    CLAIM PAIRS and this class is "any number restated anywhere". That is a finding about
    the CHECK, not about the finding (memory/gotcha-log.md § Mechanized).

    The rule mechanized here is exactly the profile's own sentence: the CURRENT value
    appears in the profile and nowhere else outside a dated record. It cannot tell you
    the value is right — only that there is one live copy of it, which is what #133 asks.
    """
    try:
        text = open(REVIEW_PROFILE).read()
    except OSError:
        return 1, [f"CANNOT VERIFY suite baseline: {REVIEW_PROFILE} unreadable"]
    m = SUITE_COUNT.search(text)
    if not m:
        return 1, ["CANNOT VERIFY suite baseline: no `N passed, M skipped` in "
                   ".claude/review-profile.md — the line this check exists to protect "
                   "is gone, and a missing baseline reads as a passing check"]
    current = m.group(0)
    strays = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".venv", "node_modules", "__pycache__",
                                    ".pytest_cache")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
            if os.path.join(dirpath, fn) == REVIEW_PROFILE \
               or rel == ".claude/review-profile.md" \
               or rel.startswith(SUITE_HISTORY):
                continue
            try:
                body = open(os.path.join(dirpath, fn)).read()
            except OSError:
                continue
            if current in body:
                strays.append(rel)
    if strays:
        return 1, [f"FAIL suite baseline: `{current}` is restated in "
                   f"{', '.join(sorted(strays))} — .claude/review-profile.md says it is "
                   f"the ONLY live copy, and two hand-maintained copies disagree the "
                   f"moment one is updated (#133). Point at the profile instead."]
    return 0, [f"PASS suite baseline: `{current}` lives only in "
               f".claude/review-profile.md (dated session records excepted)"]


# A share quoted against NexusMind's enrichment gate (`pipeline.enrichment.min_score`,
# which reads the NORMALIZED score at 4.0).
GATE_SHARE_GATE = re.compile(
    r"normali[sz]ed(?:\s*(?:≥|>=|>)\s*|[- ])4\.0|enrichment gate", re.I)
GATE_SHARE_PCT = re.compile(r"\d+(?:\.\d+)?\s?%")
# A LEVEL share ("N% clear it"), not a crossing ("moves N% across the gate") — a
# crossing compares two scorings under ONE normalization and is not the tautology.
GATE_SHARE_CLEAR = re.compile(r"\bclear(?:s|ed|ing)?\b", re.I)
# ⚠️ Deliberately NOT `by construction` or `arithmetic`, which the Mechanized row
# proposed: `docs/TODO.md`'s NM#319 block says "normalized(4.5) = 0.0 by construction"
# about the ANCHOR while quoting v7's 60.0% bare, so a looser list passed the very block
# this check exists for. The marker must name the SAMPLE.
GATE_SHARE_MARK = re.compile(r"in-sample|out-of-sample|out of sample|tautolog", re.I)
GATE_SHARE_HISTORY = SUITE_HISTORY + ("memory/gotcha-log",)   # the log and its archive


def _md_blocks(text):
    """(first line number, text) per paragraph; every table row is its own block, so a
    marker in one row cannot excuse a bare share in the next."""
    cur, start = [], 1
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("|"):
            if cur:
                yield start, "\n".join(cur)
                cur = []
            yield i, line
        elif not line.strip():
            if cur:
                yield start, "\n".join(cur)
            cur = []
        else:
            if not cur:
                start = i
            cur.append(line)
    if cur:
        yield start, "\n".join(cur)


def check_gate_share_sample():
    """A share of rows clearing the normalized-4.0 enrichment gate must say WHICH sample.

    ⛔ THE SHAPE IT CATCHES IS A TAUTOLOGY THAT READS AS A MEASUREMENT. Normalization is
    a percentile CDF fitted on production rows, so normalized 4.0 IS the fit sample's own
    40th percentile and ~60% of that sample clears it by construction. On 2026-09-22 a
    session published "60.0% (1,786/2,976) clear the gate" as a CORRECTION of a retracted
    60.4% — the tautology was already written down in three places on that task's routing
    path (memory/gotcha-log.md, H-CTX-1). Measured OUT of sample the same share is a real
    number (`uplifting v7`: fitted 2026-08-10, 60.0% over 2026-08-23 → 09-06), which is
    why the rule is "declare the sample", not "never quote it".

    Live docs only: dated records keep what was said when it was said.
    """
    bare, declared = [], 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".venv", "node_modules", "__pycache__",
                                    ".pytest_cache")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            if rel.startswith(GATE_SHARE_HISTORY):
                continue
            try:
                body = open(path, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            for line_no, block in _md_blocks(body):
                if not (GATE_SHARE_GATE.search(block) and GATE_SHARE_PCT.search(block)
                        and GATE_SHARE_CLEAR.search(block)):
                    continue
                if GATE_SHARE_MARK.search(block):
                    declared += 1
                else:
                    bare.append(f"{rel}:{line_no}")
    if bare:
        return 1, [f"FAIL gate-share sample: {len(bare)} block(s) quote a share clearing "
                   f"the normalized-4.0 enrichment gate without saying in-sample or "
                   f"out-of-sample: {', '.join(bare)} — in-sample, ~60% clears it BY "
                   f"CONSTRUCTION (the gate is the fit's own 40th percentile). Say which."]
    if not declared:
        # Presence control: the tree carries such shares today. Zero matches means the
        # patterns stopped matching the prose, not that the prose got cleaner.
        return 1, ["CANNOT VERIFY gate-share sample: no live doc quotes a share against "
                   "the enrichment gate at all — the patterns have lost their subject"]
    return 0, [f"PASS gate-share sample: {declared} gate-share block(s), each declaring "
               f"its sample (dated records excepted)"]


CHECKS = {
    "rule-ordinals":   check_rule_ordinals,
    "suite-baseline":  check_suite_baseline_single_copy,
    "gate-share-sample": check_gate_share_sample,
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
