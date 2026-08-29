# Session 2026-08-29 (later) — the hygiene queue cleared, and a report that counted mentions of checking

**No spend, no model, no filter, no threshold, no probe touched. Nothing deployed — deploy is
N/A, not skipped.** Owner asked for the queued hygiene items in `docs/TODO.md`; all four are
done. Changed: `scripts/verification/` ×3, `tests/unit/` ×3 (two new),
`.claude/skills/review-changes/SKILL.md`, `CLAUDE.md`, `memory/` ×3, `docs/TODO.md`, and the
USER auto-memory index (outside this repo).

## Two owner decisions, both taken before any code

1. **The budget is stated over the always-loaded TOTAL; per-file lines attribute it.** The
   total is what costs context; the remedy is per file, so both print.
2. **The auto-memory index drops its session log and points at this repo**, rather than
   `/curate` learning to rotate a second copy.

## #138 — the guard measured one of the two always-loaded files, and not the auto-loaded one

`--target loaded` sums `CLAUDE.md` (37,445 B) and `~/.claude/projects/<slug>/memory/MEMORY.md`
(19,488 B). **Membership was established by reading a live session's own context**, not from
documentation: both arrived; the in-repo `memory/MEMORY.md` did not — it is pointer-reached.
It keeps its own `--target index` budget, which still carries #123's session rotation.

HARD 60,000 / SOFT 55,000, sized against the ~486–864 B/day #133 and H-CX1 measured. The path
is derived from `ROOT` (`[^A-Za-z0-9]` → `-`, checked against all 40 directories in
`~/.claude/projects/`, one of which carries a dot). **A missing member is printed with the
exact path and counted `N/M`, never dropped**; all members missing is CANNOT VERIFY.

**Removing the auto-memory session log**: 9,160 B, 47% of that file, no rotation rule, no
ceiling, two sessions stale — and the file's own header already said session detail belongs in
the repo. Moved **verbatim** to `memory/session-log.md`'s frozen appendix after extracting
**121 evidence atoms** (issue refs, figures, backticked spans, hashes) and searching them with
`git grep -F`: **119 found; both misses were `00cf55c`**, the left side of a push range and a
real commit here. A control atom that cannot exist was correctly not found, so the negative
carried information. All 6 linked `project_session_*.md` exist. **Layer 56,933 → 46,167 B.**

## `CLAUDE.md`'s runway — the lever was not a trim

37,445 B with 2,555 to the wall. The four inline `<!-- verify: -->` blocks measured **2,047 B,
5.5% of the file**: guard mechanism spending the budget it polices. Moved to
`scripts/verification/check_doc_claims.py`, annotated from `memory/MEMORY.md`, verdicts
byte-identical (16, 14, both-layers-agree, v1.36.1). **35,394 B, runway 4,606, zero content
removed.** The same argument moved `check_index_budget.py` out of `memory/MEMORY.md` on
2026-08-17; it took two weeks to reach one file over. Recorded in `memory/working-rules.md`
under the #133 cap, and `test_no_verify_block_has_crept_back_into_claude_md` stops the reversal.

The Python port also fixed a defect the shell had: it matched a **fixed line window**
(`sed -n '/…/,+3p'`), so rewrapping a bullet changed what the check compared.

## ⛔⛔ THE KEEPER — the verify report's denominator was 18% phantom

`BLOCK` matches any `<!-- verify: ... -->`, **including the empty one that appears when a
memory file QUOTES the idiom while explaining a lesson about it**. Ten — eight in
`memory/gotcha-log.md`, two in `memory/working-rules.md` — were counted in `blocks found` and
tallied `skipped`. **56 reported, 46 real.**

⭐ **It was found by writing an eleventh.** Adding a *prose* sentence moved the count, and that
was the only tell; nothing else about the report looked wrong. ⭐ Nothing executable was ever
affected — `passed`/`failed`/`errored` were identical before and after — so no check was
disabled. But this is the report whose whole job is to say how much is checked, and it was
counting mentions of checking. Empty blocks are now **named and counted separately**: an
unfilled annotation is a real defect and must not vanish into a silent skip.

## #137 — ten shapes, ten seeded positives

Normalisation before matching (`⛔`, `✗`, `- `, `**`, BOM, ANSI); stdout and stderr no longer
concatenated without a separator; classification on the comment-stripped command; `DELEGATES`
widened to `.venv/bin/python`, `pytest` and bare relative paths; a `-->` inside a command now
**refuses to run the fragment** rather than executing a severed one; `CANNOT VERIFY` tested
before the return code; FAIL beating CANNOT VERIFY; no-output passes labelled.

⚠️ **The verdict match is deliberately not a substring.** Three shapes only — opens the line,
followed by a colon, closes the line — because `0 FAILures` and `no FAIL lines found` are
healthy output, and a check that cries wolf gets ignored.

## Mine, caught before they shipped

- ⛔ **Two mutation probes "survived" and had never applied** — shell escaping turned `\b`
  into a backspace and a BOM literal into a non-match. Re-run with `assert s.count(old) == 1`
  in the mutator, both died at once. **A mutation script must assert that it mutated**: a
  no-op mutation is indistinguishable from a test gap, and reads as the more alarming one.
- ⛔ **#137 shape 1 was live one stage earlier than the issue describes it.** `ASSERTS` used
  `\bFAIL\b` on the annotation text; `\033[31mFAIL` and a BOM both put a WORD character
  immediately before the verdict, so those blocks were NO-ASSERTION — never run, no line, exit
  0. Found by the seeded fixture. `ASSERTS` is now deliberately loose: over-matching costs a
  block being run, under-matching costs a check never running.
- A test that ran the entire annotation corpus inside pytest, **+47 s and a verdict that
  depended on 46 unrelated checks**. Rewritten against a fixture: 3.9 s → 0.62 s.
- My own `printf '- FAIL…'` fixture parsed the bullet as an option and printed usage — the
  test failed for a reason that was not the runner's.
- ⛔ **`looks_truncated` counted quotes**, so `echo "it's fine"` — one apostrophe, odd
  count — would have been refused as a severed command. **A false TRUNCATED silences a
  healthy annotation**, the same direction as the defect it was written to fix. Caught in
  self-review; now a quote-STATE machine, same reasoning as `strip_comments`.
- A first `_check_loaded` printed its verdict FIRST, so the verify report displayed
  `auto-memory MEMORY.md 10,773 B` as the result of a budget check. The runner reports the
  LAST line for a passing block.

## Verification

**467 tests pass, 12 skipped.** One pre-existing failure, NOT from this session:
`tests/ml/test_inference.py::test_inference_module_importable` —
`filters/cultural_discovery/v5/inference.py` uses a relative import, entered at `6acd013` and
untouched since. **cd v5 is LIVE**; worth a look before a fix.

**14 mutations seeded across three files, 14 killed** (6 budget guard, 7 claim checks + runner,
plus the two re-run after the escaping artifact). Verify annotations: **46 blocks, 20 passed,
0 failed, 1 CANNOT VERIFY** (a pre-existing remote check needing ssh).

## RUNBOOK drift — asked for after the hygiene queue, fixed in the same session

Owner asked where v8 sits in the runbook and whether it was still aligned. **It was not**, in
five places, and the drift ran one hop further than the runbook.

**Where v8 is** *(my mapping, not the docs'): Phase A ≈ RUNBOOK phase 2, the n=200 calibration
runs ≈ phase 3.* Stopped at **Gate A** — *"owner reads the new prompt and the 30-article
calibration output before any paid run"*. Phase A cost **$0.87** (n=200, k=3, both arms, 1,200
calls). Phase B is additionally behind B2 (NM#231's golden slice is neither on disk nor in git)
and B4 (a missing `calibration.json` still fails silent; `grep -rn "calibration.json"
scripts/deployment/` is empty).

**The five, all fixed in `docs/RUNBOOK.md`:**

1. ⛔ **Its oracle command could not select the oracle the project decided on.**
   `batch_scorer.py --llm` is `choices=['claude','gemini','gemini-pro','gemini-flash','gpt4']`,
   **default `claude`** — DeepSeek is not a value (`grep -rln -i deepseek ground_truth/` hits
   only `text_cleaning.py`); it runs through `scripts/score_deepseek_production.py`, which the
   runbook mentioned **zero** times, as did `--llm` itself. **Following the runbook scored
   against Claude.** Now documented, with the v8 oracle question left OPEN (plan §9: Gemini is
   the stricter arm on class A, 3/10 caps vs 1/10, against DeepSeek being ~7× cheaper).
2. **Phase 4 still said to write a `prefilter.py`** — ADR-018 *and* ADR-019 carry an
   *Amendment 2026-08-21: new filters ship no per-lens prefilter*.
3. **No probe step and no gate step**: 0 mentions of `train_probe.py`, `ground_truth_gate.py`,
   ADR-021 or ADR-023. Added as `6b` (lettered, because the v8 plan and `CLAUDE.md` both cite
   "phase 5" and renumbering costs more than it buys) and folded into phase 8.
4. **Averaging advice now actively wrong for v8**: `1/√k` cannot touch a Bernoulli, and
   averaging k=3 is *how* Gate A missed the `scope_verdict` step function (#135).
5. **Footer read `Last updated: 2026-04-19`** while git said 2026-08-13. Replaced with the
   `git log` command — a hand-maintained copy of something git already knows.

⭐ **The drift ran one hop further than asked.** The two guides the runbook sends you to for
"detailed checklists" — `docs/agents/filter-development-guide.md` (73 prefilter mentions) and
`docs/guides/filter-creation-workflow.md` (11) — **last changed 2026-07-10**, carry **0**
mentions of ADR-018 or the amendment and **0** of `ground_truth_gate`. And
`docs/FILTER_PLAYBOOK.md`, the declared SSoT, had **0** for the amendment and **0** for
ADR-023 despite being current on the gate. **Fixing only the runbook would have moved the trap
one hop.** The playbook now carries both rulings; the two 2026-07-10 guides carry a dated
staleness banner. ⚠️ **Their bodies were NOT rewritten** — the prefilter material runs through
both and a partial rewrite is worse than a flagged one. Stated in the banner itself.

**New guard** so item 1 cannot silently return: `check_claude_md_claims.py` generalised to
`scripts/verification/check_doc_claims.py` with `runbook-oracle-flags`, which reads `--llm`'s
`choices`/`default` from the parser with `ast` (not grep) and requires the runbook to name every
provider, the default **in bold**, and the DeepSeek script. ⚠️ It checks NAMING, not
correctness — it cannot say which oracle a filter should use. Four mutations, four killed,
including the subtle one: changing the default to `gemini` while the word `claude` still
appears as a valid choice.

## Next session

**The v8 decision.** Adopt the reordered oracle prompt or not — it gates corpus sizing, the
b650 staging run and `corpus_manifest.json` (#127). H-V8-9 is the cheap evidence path.
