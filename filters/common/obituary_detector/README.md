# Obituary detector

Multilingual obituary/death-memorial classifier for the constructive-news pipeline
(NexusMind#185 / llm-distillery#51). Same architecture as `commerce_prefilter` v2:
frozen `paraphrase-multilingual-mpnet-base-v2` → StandardScaler → sklearn MLP(256,128)
→ `predict_proba`. Block obituaries upstream of lens scoring.

## Status — v3 trained + validated, NOT yet enforced (2026-06-14)

| Model | Corpus | Held-out result | Verdict |
|---|---|---|---|
| v1 | gate-reason-substring labels (777) | **0/22 block precision** (4-lab panel) | ❌ rejected |
| v2 | gemini-relabeled clean labels (777) | held-out FP **22→1** (0 @ 0.95); recall ~33% @ 0.90 | proof-of-fix only |
| **v3** | **raw-ingest, DeepSeek oracle, sharpened-broad rule (11,295 train / 1,562 held-out; 23.5% pos)** | in-corpus held-out (leaky) 0.85 @ 0.90; **temporally-disjoint June holdout: 0.97 @ 0.90, 0 FP @ ≥0.95 (0/58), 1.00 @ 0.99** | **shadow-ready** |

> **Honest validation note (2026-06-14 review):** the in-corpus held-out had train/held-out
> leakage (7% exact-title / 22% near-dup twins, same death from many sources via id-hash
> split). Re-validated on **sadalsuud's fresh June ingest** (zero time overlap, 6 exact-title
> leaks pre-dropped): block precision is *higher* clean — **0 false positives at threshold
> ≥0.95** on 58 model-blocked, never-seen June obituaries. The 0.85 in-corpus figure was the
> pessimistic small-n sample, not leakage inflation. Recommended operating point **~0.95**
> (more recall than 0.99, still 0 FP here). A cluster-dedup retrain (v4) would tidy recall /
> CV-honesty but is not a Phase-3 blocker. See `validation/artifacts/v3_june_validation.json`.

### v3 build (Phase 1–2 of the build plan)
- **Corpus from RAW INGEST** (585K FluxusSource `content_items_*.jsonl`) — where obituaries
  actually live, fixing v2's depleted-warm-DB recall. 12,857 death-adjacent candidates
  (word-boundary multilingual regex) → **DeepSeek** oracle-labeled (`relabel_deepseek.py`,
  independent of the Ollama audit panel; runs on owner credits, frees gemini for the panel).
- **Owner labeling decision (broad → sharpened):** block hard-news death EVENTS (accident,
  crime, disaster) of a specific person, but KEEP politics / opinion / advocacy / reaction
  pieces that merely use a death, and non-person deaths. Decisive "primary purpose" test.
  Landed at 3,016 positives (23.5%); narrow-rule (18.7%) and full-broad (31%) corpora kept
  as `*_narrow` / `*_broad_partial` for comparison.
- **Audit:** panel-vs-DeepSeek 91% headline, **97% on panel-consensus cases** (3 of 4
  disagreements are panel-internal-split accident/crime death-events; ~2% real oracle error).
- **Held-out validation** (the oracle-independent gate): model-blocked worksheet graded blind
  by gemini + gemma3 + qwen3 + phi4. Enforce-grade precision (~0.95–0.97) at threshold ~0.99,
  recall ~0.55 there. Residual FPs = crime-investigation / survivor-resilience profiles /
  split accident cases — **the over-block risk to watch in shadow.** See
  `validation/artifacts/v3_heldout_validation.json` + `v3/calibration_report.json`.

### Phase-1/2 harness (new)
- `training/build_candidates.py` — raw-ingest → death-adjacent candidates (dedup, word-boundary regex).
- `validation/relabel_deepseek.py` — DeepSeek oracle labeling (resumable; key from `config/credentials/secrets.ini`).
- `validation/panel_audit_deepseek.py` — 3-lab Ollama audit of the oracle.
- `training/build_train_split.py` — stable hash split into train / disjoint held-out.

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
