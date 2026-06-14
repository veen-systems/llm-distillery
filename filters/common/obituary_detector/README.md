# Obituary detector

Multilingual obituary/death-memorial classifier for the constructive-news pipeline
(NexusMind#185 / llm-distillery#51). Same architecture as `commerce_prefilter` v2:
frozen `paraphrase-multilingual-mpnet-base-v2` → StandardScaler → sklearn MLP(256,128)
→ `predict_proba`. Block obituaries upstream of lens scoring.

## Status — NOT production (2026-06-14)

| Model | Corpus | Held-out result | Verdict |
|---|---|---|---|
| v1 | gate-reason-substring labels (777) | **0/22 block precision** (4-lab panel) | ❌ rejected |
| v2 | gemini-relabeled clean labels (777) | held-out FP **22→1** (0 @ 0.95); recall ~33% @ 0.90 | proof-of-fix only |

**v1 lesson (the important one):** training labels bootstrapped from the editorial
gate's reject *reasons* were ~51% contaminated — the gate writes "death" for many
non-obituary rejects (policy, murder, parental-loss, negativity). The model learned
*"death-adjacent AND gate-rejectable"*, not *"is an obituary"*, and would have dropped
legitimate constructive stories (victim-protection laws, suicide-prevention programs,
pandemic-preparedness reports). Cross-validation said 97.7% precision; a held-out set
graded by a 4-independent-lab blind panel said 0%.

**v2 proved the fix** (oracle relabel + retrain) but on the depleted warm DB, so recall
is low. **The production model must be trained on RAW INGEST** (FluxusSource stream),
where obituaries are plentiful. See `NexusMind/docs/obituary-detector-build-plan.md`.

## Labeling rule (owner-endorsed 2026-06-14)
- **Block (obituary):** fresh obituaries / death notices / mourning pieces whose
  PRIMARY purpose is to mark a specific person's recent death.
- **Keep (not_obituary):** memorial events, anniversary/commemoration pieces, legacy
  tributes, laws/programs prompted by a death, profiles of the living, any story that
  merely mentions death.

## Layout
- `training/train_v1.py` — embed → 5-fold OOF CV calibration → refit final artifact.
- `validation/` — the validation harness (reusable, the methodology that caught v1):
  - `make_obit_worksheet.py` — score candidates, sample a decision-relevant held-out worksheet.
  - `relabel_gemini.py` — LLM-oracle relabel (gemini-2.5-flash) with the rule above.
  - `panel_obit.py` — 4-lab blind panel (gemini + gemma3:27b + qwen3:14b + phi4:14b); extensible to DeepSeek.
  - `panel_audit.py` — audit the oracle's labels with the 3 Ollama labs.
  - `rollup_obit.py` — panel-majority vs model, block precision, per-lens FP.
- `validation/artifacts/` — provenance: panel grades, owner adjudication (`human_calls`),
  labeling guideline, calibration reports, roll-ups. Corpora (`*corpus*`, `seed*`,
  `worksheet*`) are gitignored (contain article content).
- `v1/`, `v2/` model pickles live on gpu-server `~/llm-distillery/filters/common/obituary_detector/`
  (not committed — v1 is broken, v2 is a proof; regenerate via `training/train_v1.py`).

## Rebuild (production)
Follow Phase 1–2 of `NexusMind/docs/obituary-detector-build-plan.md`: corpus from raw
ingest → oracle-label → panel-audit → train → held-out panel validation → calibrate.
