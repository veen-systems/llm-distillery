# Gate B-A becomes executable, with a third verdict — and the control that stopped me breaking the draw

**2026-09-03. $0** — code and existing run files only, no oracle calls.

## 1. The gate had never been executable, and that is why this morning cost a day

`docs/HUMAN_THRIVING_V8_PLAN.md` §5 said so itself: *"nothing enforces either form in code —
`grep -r 'assertion_margin\|max_acceptable_wa'` over `*.py` returns zero hits, so the stored
margins are documentation of a check that was made, not a check."* Verified 2026-09-03: the only
`.py` files reading `max_acceptable_wa` are two **evidence-directory analysers**, and no test
loads the adverse suite for gating.

⭐ **The consequence was measured, not hypothesised.** The nursery row was reported FAILING
criterion 1 at **4.400** against a 3.85 bar, from a k=3 mean on a row whose own spread is
sd 2.560. That margin (0.550) never cleared its band (2.858). At k=6 it is 3.608 and at k=12
2.342 — both PASSES.

## 2. `scripts/gate/adverse_suite_gate.py` — three verdicts, four exit codes

The band comes from **each row's own observed spread**, `t·sd/√k`, never from a project-wide
constant: the #95 0.16 batch floor is the wrong floor here and §1f's 0.82/2.25 are a third
population (`feedback-noise-floor-per-population`). Both are printed as context and neither
decides. Bars and assertions are read off the rows; nothing about the suite is typed into the
file.

⛔ **The third verdict is the whole point.** A gate that can only say PASS or FAIL will answer a
question it cannot resolve.

| run | verdict | exit |
|---|---|---|
| v8 k=3 (**the run that produced the 4.400 FAIL**) | **INDETERMINATE** — margin 0.550 < band 2.858, **need k≈82** | **2** |
| v8 k=12 | PASS (12 rows, 1 SKIP) | 0 |
| v8.4 k=12 | PASS | 0 |
| v8.2 k=12 (the union prompt) | **FAIL** — origin row 5.921, margin 2.071 ≥ band 0.145 | **1** |
| glob matches nothing · runs mix prompt hashes · ragged k | plumbing | **3** |

**Had this existed, it would have refused to certify rather than reporting a failure.**

⛔ **Plumbing is 3, never 1** — a bare `SystemExit("msg")` exits 1, which is this gate's "a row
FAILS" code, so a gate that never ran would have been indistinguishable from a gate that ran and
failed. ⚠️ Found only on the second look: the first exit-code check was piped through `| tail`,
which swallowed every code and reported 0. **[x5]** for that gotcha, committed while testing
exit codes.

18 unit tests; 3 mutations killed (band check removed · band replaced by a constant · plumbing
exits 1), each asserted present on disk before its run.

## 3. ⛔⛔ THE KEEPER — a failing check was the control working, and it was mine to break

Growing the benchmark needs guard rows kept out of training, so I widened
`draw_v8_corpus.py`'s exclusion to cover `datasets/adverse/uplifting.jsonl`. **20 of its 33
tests went red**, two of them named `test_draw_REFUSES_the_ADVERSE_set_pointed_at_this_flag`
and `test_the_real_adverse_set_would_be_refused`.

**They were right and I was wrong.** Seven of the 18 adverse rows carry
`training_use: HARD NEGATIVE for human_thriving v8 per FILTER_PLAYBOOK.md §4b` — they are
**intended training inputs**, which is why the loader refuses that file by design. My change
would have silently stripped them. **Reverted; 33 tests green again.**

⭐ **But the concern sharpens rather than disappears, and this is the part worth keeping:**

- A designated hard negative is **ADDED** with an **editorial** label of `negative` (§4b).
- A row **DRAWN** into the corpus is labelled **by the ORACLE** — and these rows are adverse
  *precisely because* a scorer read them as positive.
- **So a drawn adverse row can enter training as a POSITIVE — the error it was collected to
  fix.** Nothing reconciles the two paths and nothing would have printed the collision.

Measured against the real 177,592-row pool: **3 of the 18 adverse rows were DRAWABLE**, at
inclusion probabilities **0.0810 / 0.0794 / 0.0794**, all three designated hard negatives, one
of them **class A**. None was drawn. **P(all three escaped) = 0.7787 — the draw ran a 22.1%
chance of the collision**, and it is the *second* time this shape has appeared here (2026-08-30:
the no-regression rows escaped only by having aged out of the window).

**Fix: REPORT, do not exclude** (ADR-022, *stamp always, decide once*). The draw now prints how
many designated hard negatives it declared and how many are drawable, names them, and records
both in the manifest. 4 tests, 3 mutations killed.

⚠️ **A second finding fell out of it: the class-A instrument does not detect a declared class-A
row.** *"Children's helpline says number of calls about child domestic abuse cases has risen"*
matches **none** of `crime_violence`'s 37 title patterns, so it sat in a `|-` cell, not
`|classA`. The class-A *supplement* population and the class-A *adverse* population are defined
by different things, and neither document says so.

⛔ **And one of my own numbers nearly went out wrong.** The first probe printed `id[:40]`, so one
id came back **truncated**, its suite lookup silently failed, and it defaulted to
`class-A: False`. Had that row been class-A-detected its cell probability is **0.763**, not
0.081 — a tenfold error in the alarming direction. Re-run with full ids: the figures above hold,
because the instrument genuinely does not flag it. **A truncated key breaks a join silently, and
the default it falls back to is a claim.**

## 4. Not done

- **The 6 benchmark candidates are identified, not promoted.** One row per distinct shape
  (proposal · anniversary/roundup · delisting · programme published · conference · commitment
  restated), each discriminating — v8 above the 3.85 bar, v8.4 below 2.0, sd < 0.30 — and two of
  them **Greek**, against an adverse suite that is currently 16/18 English (#141). They live in
  `datasets/scored/human_thriving_v8/v8_4/benchmark_candidates.json`. ⛔ **Promoting them needs
  an owner ruling on the train/test question in §3**, since all six are in the training corpus.
