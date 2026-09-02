# human_thriving v8 — STATUS

**NOT DEPLOYED. NOT TRAINED. Labelled.** Last updated 2026-09-02.

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
| Phase B2 hard negatives | ⛔ not started ($0 oracle; plan §4b) |
| Phase C train / probe / calibrate | ⛔ not started |
| Phase D gate | ⛔ not started. ⚠️ **Acceptance criterion 1 is FAILING today** — see below |
| Phase E normalization | ⛔ not started |
| Phase F deploy | ⛔ not started |

⚠️ **The labelled corpus is 6,586, not 6,590** — four scrape-junk skips, all JavaScript-required
boilerplate at 357–489 chars, all *above* the 300-char floor.

## ⛔ Known-failing and known-missing, before anyone reads the state as green

- **Acceptance criterion 1 (Gate B-A) does not pass on either oracle.** Both fail *"Parents of
  baby girl killed at nursery"*, and on both it is a **scope-gate coin toss** — DeepSeek
  6.10/0.90/6.20, Gemini 7.20/7.15/1.05. Recorded as a knowing decision, not an oversight
  (`docs/decisions/2026-09-01-v8-oracle-ruling.md` §3).
- **A v8.1 prompt fix is owed**, ~6 calls: §2's qualifier *"especially as a trailing sentence"*
  leaks on a policy change that occupies a third of the body. The Travelodge and nursery rows
  bracket the boundary. ⛔ Deliberately **not** applied during Phase B — editing the prompt
  mid-corpus would have invalidated the labels.
- **The 47-row class-A supplement is unadjudicated** — `tp_fp_status: adjudication-pending`.
  31.9% above the op-point, **29.8% gate-flipped** against the corpus's 15.35%.
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
