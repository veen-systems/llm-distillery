# Filter Creation Workflow

> **Start from `docs/FILTER_PLAYBOOK.md`** (the SSoT: compiled lessons + the canonical reference). This is the quick-commands companion to it. The **canonical reference filter is now `nature_recovery v4`** — the uplifting v6 examples below still illustrate the file structure correctly, but for a current end-to-end example (recall-first probe, ground-truth gate, deploy) see `filters/nature_recovery/v4/` + `docs/reports/nature_recovery_v4_report.pdf`.

Practical step-by-step for creating a new production filter. Uses **uplifting v6** for its file-structure illustrations (`filters/uplifting/v6/`).

For detailed validation checklists per phase, see `docs/agents/filter-development-guide.md`.

---

## Reference: uplifting v6 file structure

```
filters/uplifting/v6/
  config.yaml              # Dimensions, weights, tiers, preprocessing, training config
  prompt-compressed.md     # Oracle prompt for ground truth scoring
  prefilter.py             # Fast rule-based noise filter
  base_scorer.py           # Shared scoring logic (calibration, preprocessing, tiers)
  inference.py             # Local inference (loads LoRA adapter from model/)
  inference_hub.py         # HuggingFace Hub inference
  inference_hybrid.py      # Two-stage hybrid inference (probe + model)
  calibration.json         # Post-hoc isotonic regression (fitted on val set)
  README.md                # Results, data sculpting, known limitations
  model/                   # LoRA adapter + tokenizer config
  probe/                   # e5-small MLP probe for hybrid Stage 1
  training_history.json    # Loss curves from training
  training_metadata.json   # Hyperparameters, dataset info
```

---

## Workflow

### 1. Define the filter

Create `filters/<name>/v1/config.yaml`:
- 6-8 scoring dimensions (0-10 scale each)
- Weights summing to 1.0
- Tier thresholds (high/medium/low)
- Gatekeepers (hard dimension thresholds that cap overall score)
- Content type caps (optional domain-specific rules)

Reference: `filters/uplifting/v6/config.yaml`

### 2. Write the oracle prompt

Create `filters/<name>/v1/prompt-compressed.md`:
- Defines how Gemini Flash scores each dimension
- Includes scoring rubrics, contrastive examples, content type handling
- Outputs dimensional scores ONLY (no tier classification)

### 3. Validate dimensions

Score ~50-100 articles with the oracle prompt and check:
- Dimension correlations (PCA/redundancy analysis)
- Oracle calibration (are scores distributed as expected?)
- Gatekeeper effectiveness
- See `docs/agents/filter-development-guide.md` Phase 3

### 3b. Calibration batch (REQUIRED before full scoring)

Score 200-300 articles from a random corpus sample with the oracle and analyze the **score distribution**:

```bash
python -m ground_truth.batch_scorer \
    --filter filters/<name>/v1 \
    --source datasets/raw/master_dataset.jsonl \
    --llm gemini-flash --target-scored 300 --random-sample --seed 42
```

Check for the **bimodal distribution problem**: if >80% of articles score 0-2 and the 2-5 range is empty, the filter concept is too rare for single-pass scoring. This happened with thriving v1 (MAE 0.94) and was caught early with foresight v1 ($0.30 vs $7+ for a full run).

**If bimodal:** Switch to two-stage scoring:
1. Embedding pre-screening (ADR-011) with **hand-crafted seed articles** (not scored data — scored seeds get contaminated by corpus composition)
2. Oracle scores only screened candidates, with **soft content-type caps** (4.0-5.0 instead of 2.0-3.0) to catch false positives without creating dead zones

**Key insight:** For needle-in-haystack filters, the prefilter handles "is this relevant?" and the oracle handles "how much?" Hard content-type caps (2.0-3.0) create a dead zone between noise and signal that the student model cannot learn.

**If smooth:** Proceed to Step 5 (full scoring).

Cost: ~$0.30 for 300 articles. This is cheap insurance against wasting a full scoring budget.

### 4. Build the prefilter

Create `filters/<name>/v1/prefilter.py`:
- Inherits from `filters/common/base_prefilter.py`
- Rule-based filtering (keyword matching, source blocking)
- Target: <10% false negative rate on relevant content
- Commerce prefilter included automatically via base class

### 5. Generate training data

Score 5,000-10,000 articles through the oracle:
```bash
python -m ground_truth.batch_scorer \
    --filter filters/<name>/v1 \
    --source datasets/raw/master_dataset.jsonl
```

For needle-in-haystack filters (low pass rate), use screen+merge strategy (ADR-003):
- Random articles provide negatives
- Pre-screened articles enrich positives

**Embedding screening (ADR-011):** Use hand-crafted seed articles representing the concept:
```bash
PYTHONPATH=. python scripts/screening/embedding_screener.py \
    --positives datasets/<name>/screening/seed_positives.jsonl \
    --corpus datasets/raw/*.jsonl \
    --output datasets/<name>/screening/screen_candidates.jsonl \
    --top-k 2000
```
This finds semantically similar articles via e5-small cosine similarity — much higher recall than keyword screening.

**Important: Hand-craft seeds, don't use scored data.** Write 10-15 synthetic article summaries representing canonical examples of your concept. Seeds extracted from scored data get contaminated by corpus composition (e.g., an academic-heavy corpus produces academic-biased seeds). See `datasets/foresight/screening/seed_positives.jsonl` for an example.

### 6. Prepare training splits

```bash
python training/prepare_data.py \
    --filter filters/<name>/v1 \
    --data-source datasets/scored/<name>_v1.jsonl
```

Produces 80/10/10 train/val/test splits in `datasets/training/<name>_v1/`.

### 7. Train the model

Train Gemma-3-1B with LoRA on GPU server:
```bash
PYTHONPATH=. python training/train.py \
    --config filters/<name>/v1/config.yaml \
    --data-dir datasets/training/<name>_v1 \
    --output-dir filters/<name>/v1/model
```

Key settings (see `filters/uplifting/v6/training_metadata.json`):
- Base model: `google/gemma-3-1b-pt`
- LoRA rank 16, alpha 32
- Max 512 tokens with head+tail preprocessing (256+256)
- Learning rate 2e-4, batch size 16, 3 epochs

**Important**: Use `load_base_model_for_seq_cls()` from `filters/common/model_loading.py` instead of `AutoModelForSequenceClassification` directly (Gemma-3-1B compatibility).

### 8. Write inference code

Copy from uplifting v6 and adapt:

- **`base_scorer.py`** — Change class name, dimension names/weights/tiers, filter metadata. The calibration loading, preprocessing, and score processing logic stays the same.
- **`inference.py`** — Change class name, model path. Model loading pattern stays the same.
- **`inference_hub.py`** — Change class name, Hub repo ID.
- **`inference_hybrid.py`** — Change class name, probe path.
- **`prefilter.py`** — Filter-specific rules.

All scorers inherit from the base class which provides:
- Calibration loading and application (`calibration.json`)
- Head+tail text preprocessing
- Score clamping (0-10), weighted average, gatekeeper logic
- Tier assignment
- Batch inference

### 9. Fit score calibration

After training, fit isotonic regression on the validation set:
```bash
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/<name>/v1 \
    --data-dir datasets/training/<name>_v1

# Verify on held-out test set:
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/<name>/v1 \
    --data-dir datasets/training/<name>_v1 \
    --test-data datasets/training/<name>_v1/test.jsonl
```

This generates `calibration.json` in the filter directory and auto-computes `score_scale_factor` in `config.yaml` (needed by NexusMind for 0-10 normalization). The base scorer picks up calibration automatically at inference time. See ADR-008.

### 10. Train hybrid probe (optional)

Train an e5-small MLP probe for Stage 1 screening:
```bash
PYTHONPATH=. python scripts/train_probe.py \
    --filter filters/<name>/v1 \
    --data-dir datasets/training/<name>_v1
```

Probe is saved to `filters/<name>/v1/probe/embedding_probe_e5small.pkl`. Calibrate the threshold using `evaluation/calibrate_hybrid_threshold.py`.

### 11. Deploy to HuggingFace Hub

```bash
PYTHONPATH=. python scripts/deployment/upload_to_huggingface.py \
    --filter-dir filters/<name>/v1 \
    --repo-id <org>/<name>-filter-v1
```

**Do NOT run `resave_adapter.py` before upload** — it changes key format and breaks Hub loading (ADR-007).

### 12. Document and verify

- Write `README.md` with results, per-dimension MAE, tier accuracy, known limitations
- Run interactive demo: `PYTHONPATH=. python -m filters.<name>.v1.inference`
- Verify Hub loading: `PYTHONPATH=. python -m filters.<name>.v1.inference_hub`

---

## Version upgrade (existing filter, new base model)

For retraining an existing filter with a new base model (e.g., Qwen2.5-1.5B → Gemma-3-1B), skip steps 1-6 and start from step 7. The dimensions, oracle prompt, prefilter, and training data carry forward unchanged.

1. Create new version dir: `filters/<name>/v<new>/`
2. Copy from previous version: `config.yaml`, `prompt-compressed.md`, `prefilter.py`
3. Update `config.yaml`: version number, `recommended_model`, add any new config sections (e.g., `head_tail` preprocessing if missing)
4. Follow steps 7-12 above (train, inference code, calibration, probe, deploy, document)
5. Compare MAE and tier accuracy against previous version baseline

---

## Shared libraries

These live in `filters/common/` and are used by all filters:

| Module | Purpose |
|--------|---------|
| `model_loading.py` | `load_base_model_for_seq_cls()` — Gemma-3-1B compatibility |
| `score_calibration.py` | `fit_calibration()`, `apply_calibration()` — isotonic regression |
| `embedding_stage.py` | e5-small embedding + MLP probe for hybrid Stage 1 |
| `hybrid_scorer.py` | Two-stage inference orchestration |
| `base_prefilter.py` | Commerce prefilter + threading safety |
| `text_preprocessing.py` | Head+tail token extraction |

---

## Key decisions

- **Oracle outputs scores only** — Tier classification in postfilter (flexible thresholds)
- **Gemma-3-1B** — Default student model (replaced Qwen2.5-1.5B, Feb 2026)
- **LoRA adapters in OLD format** — `.lora_A.weight` (not `.lora_A.default.weight`) for Hub compatibility
- **Calibration before clamping** — Pipeline: raw logits -> calibrate -> clamp 0-10 -> weighted avg -> gatekeeper -> tier
- **Screen+merge for rare-positive filters** — ADR-003
- **Commerce is the only universal prefilter** — ADR-004
- **Oracle consistency over data volume** — Prompt precision predicts MAE better than dataset size (ADR-010). Use belonging v1 as template for prompt structure.
- **Anti-hallucination rule** — New prompts should include: "Evidence MUST be an EXACT QUOTE from the article, or 'No evidence in article.'" Prevents oracle drift and paraphrased evidence.
- **Cross-dimension exclusion notes** — When dimensions share conceptual space (correlation r > 0.7), add explicit notes: "This dimension does NOT measure X — that belongs in [other dimension]." Proven to reduce oracle conflation (foresight v1).
- **Calibration batch before full scoring** — Always score 200-300 random articles first to check distribution. Catches bimodal problems at $0.30 instead of $7+.
- **Two-stage scoring for needle filters** — If concept is rare in news, use embedding pre-screening + soft caps. Hard content-type caps (2.0-3.0) create untrainable dead zones.

---

*Last updated: 2026-03-06*
