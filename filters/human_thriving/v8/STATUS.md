# human_thriving v8 — STATUS

**NOT DEPLOYED. NOT TRAINED. Labelled, adjudicated; prompt settled at v8.4, re-label pending.** Last updated 2026-09-03.

⛔ **This package is 1 of the 6-file core** (`memory/filter-doc-standard.md`). It carries
`config.yaml` and the prompt; `DEEP_ROOTS.md`, `README.md` and `README_MODEL.md` are owed, and
Phase F1 of the plan gates shipping on package parity with `nature_recovery v4`. This file exists
now because v8's state is complicated enough that "not deployed" is not a useful summary.

## Where it actually stands

| phase | state |
|---|---|
| Prompt (Phase A) | ✅ **`prompt-candidate-tail.md` ADOPTED** 2026-08-30, on the label argument |
| Corpus (Phase 0) | ✅ 6,590 drawn, manifested, `sha256 5e2cf729…`; guard rows excluded by construction |
| Oracle | ✅ **DeepSeek**, ruled 2026-09-01 (`docs/decisions/2026-09-01-v8-oracle-ruling.md`) |
| Labels (Phase B) | ✅ **6,586 at k=3, $6.8853**, `--aggregate all`. `EXP-010` |
| Label review | ✅ 2026-09-02 — `docs/evidence/2026-09-02-phase-b-label-review/` |
| Class-A adjudication | ✅ 2026-09-03 — v8 demotes **32 of 47**; the 15 survivors are 11 events. `docs/evidence/2026-09-03-classA-supplement-adjudication/` |
| Phase B2 hard negatives | ⚠️ **12 rows of headroom, not a corpus** — the draw took 47 of the 59 available and 32 already carry low labels. `docs/evidence/2026-09-03-phase-b2-headroom/` |
| Phase C train / probe / calibrate | ⛔ not started |
| Phase D gate | ⛔ not started. ⚠️ **Criterion 1 is NOT stably failing** — the 4.400 was a k=3 mean on a coin-toss row; at k=6 under unchanged v8 it is **3.608 ± 2.560, PASS**. `docs/evidence/2026-09-03-v8-1-gate/` |
| Phase E normalization | ⛔ not started |
| Phase F deploy | ⛔ not started |

⚠️ **The labelled corpus is 6,586, not 6,590** — four scrape-junk skips, all JavaScript-required
boilerplate at 357–489 chars, all *above* the 300-char floor.

## ⛔ Known-failing and known-missing, before anyone reads the state as green

- ⛔⛔ **CORRECTED 2026-09-03: acceptance criterion 1 was never stably failing.** The 4.400
  that read as a FAIL is a **k=3 mean on a bimodal row**. At **k=6 under the unchanged v8
  prompt** the nursery row is **3.608, sd 2.560, 3 `in_scope` / 3 `response_to_harm` — a PASS**.
  With that sd the standard error at k=3 is **1.48** against a 0.55 margin, so the k=3 verdict
  never cleared its own band, which Gate B-A's rule requires. ⭐ **On a bimodal row a k=3 mean
  is a sample of a coin flip, not a measurement** (#135: the scope gate is a step function and
  `1/√k` does not describe it). The gate's k must be re-derived before Phase D.
- ✅ **`prompt-v8-4.md` is the settled prompt** (`sha c4705408c477`) — **B** (§2 commencement)
  + **C** (§3 jurisdiction) + **A3** (§5 nothing-has-taken-effect). Validated at **k=12** on all
  13 gate rows: Gate B-A **9/9**, worst class-A sd **2.250 → 0.205**, `in_scope` runs on class A
  **3 of 108 → 0**, no-regression **4/4**. ⭐ **The gain is variance, not verdict** — both
  prompts pass 9/9; v8.4 makes the labels stable.
- ⛔⛔ **D (§5 judicial relief) is DROPPED, so the convict-relief ruling is NOT implemented.**
  Three corpus rows keep their labels and decision 2 stands unexecuted until a wording is found
  that does not license a positive. **The four clauses are not additive**: each is individually
  safe, and their union scores the #91 origin row **5.921 with 12/12 `in_scope`** where v8 pins
  it at **0.900 sd 0.000**. Leave-one-out isolates a **B×D interaction** — D held the only
  sentence among the four that licenses a positive (*"the release **is** the repair and **scores
  normally**"*), and deleting that sentence helped but was not sufficient.
  ⭐ **Never validate a multi-clause prompt change by its parts**: ablate to attribute, validate
  the artifact you intend to ship. ⭐ A placebo of **+996 chars** of §1 restatement left the row
  at **0.883 ± 0.037**, refuting length and location — *a rule stated as a **test** inside a
  reasoning step becomes a question asked of every article; the same rule as a **category** in an
  exclusion list does not.* `docs/evidence/2026-09-03-v8-1-gate/` PART 2.
- **A v8.1 prompt fix is owed**, ~6 calls. ✅ **Ruled 2026-09-03** — the fix is on
  **commencement** (a policy change that has not taken effect is an announcement), bounded
  **inside §2**, not on prominence and not extended into §1
  (`docs/decisions/2026-09-03-v8-1-commencement-clause.md`). ⛔ **Unwritten and untested** —
  criterion 1 stays FAILING until it is measured, with the Travelodge row as negative control.
- ⭐ **A SECOND v8.1 candidate, distinct from the first**: §1's announcement rule is written in
  terms of **money** (*"funding secured, mobilised, pledged or allocated"*), so a **legislative
  proposal** has no rule pointing at it. Six above-op rows name a proposal, plan or
  *preparations* in the oracle's own `dominant_subject` and score 4.55–6.33 anyway.
- ✅ **The 47-row class-A supplement is ADJUDICATED** (2026-09-03). v8 demotes **32 of 47
  (68.1%)**; the 15 survivors are **11 distinct events**, one of which (the US removing Syria
  from its terrorism list) is **9 above-op rows corpus-wide**. Two owner questions remain: the
  Syria cluster under §3, and judicial relief granted to convicted offenders.
- ⚠️ **The prompt is not named `prompt-compressed.md`**, which is what `load_filter_spec` derives
  from `config.yaml` and what the doc standard's item 2 calls for. Every run so far passed
  `--prompt` explicitly. Left as-is on purpose: the 6,586 labels record
  `prompt_file: filters/human_thriving/v8/prompt-candidate-tail.md` as provenance, and renaming
  now would break that pointer. Resolve at Phase F, by copying rather than renaming.
- **`config.yaml` is labelling-scope only.** No `hybrid_inference` block (the probe is retrained
  and its threshold re-derived at Phase C) and no normalization anchor (Phase E). `prefilter` and
  `content_type_caps` are omitted **with the reason written where the block would be**.

## Open questions that do not block

- **Plan §9 Q4** — is `social_cohesion_impact` at 0.20 right for Thriving? ⭐ Does **not** gate
  anything: a weight change needs no re-labelling (ADR-001), and dropping a dimension is free.
  Only *adding* one would force a re-score.
- **`benefit_distribution` has a median of exactly 0.00**, the only dimension that does. Watch at
  Phase C; not acting on it now.

## Provenance

Corpus and labels are **not in this repo** — article text at corpus scale (#97). They live at
`datasets/scored/human_thriving_v8/` (gitignored) and the corpus is staged on `b650-gpu`.
Journal: `docs/HUMAN_THRIVING_V8_JOURNAL.md`. Plan: `docs/HUMAN_THRIVING_V8_PLAN.md`.
