# Scripts Directory

**Purpose:** Standalone utility scripts for filter development workflow.

**Organization:** Scripts organized by development phase (validation, training, oracle, deployment, dataset).

**Philosophy:** Scripts are filter-agnostic utilities. Core functionality (imported modules) stays in `ground_truth/` and `training/`.

---

## Directory Structure

```
scripts/
├── validation/          # Phase 3-5: Validation & quality assurance
├── training/            # Phase 6-7: Training utilities
├── oracle/              # Phase 3: Oracle calibration
├── deployment/          # Phase 9: Model deployment
├── dataset/             # General dataset utilities
├── calibration/         # Isotonic calibration fitting (ADR-008)
├── normalization/       # Cross-filter percentile normalization (ADR-014)
├── gate/                # ADR-021 ground-truth deploy gate + agreement gate
├── verification/        # Package verification, cross-box parity harness
├── research/            # One-off investigations. Each script's docstring states
│                        #   the question, the answer, and the date — read it
│                        #   before re-running; several record NEGATIVE results
│                        #   that exist to stop an idea being re-proposed
├── analysis/            # Prediction-error and cross-filter analyses
├── screening/           # Embedding-based corpus screening (ADR-011)
├── experiments/         # Sampling and benchmark experiments
├── diagnostics/         # Ad-hoc debugging aids
└── report/              # Filter report builders
```

**Only the first five directories are documented section-by-section below.** The
rest are self-describing via module docstrings; the sections below were written
at Phase 3-9 and have not been extended since.

---

## Validation Scripts (Phase 3-5)

### `validation/create_validation_sample.py`

**Purpose:** Create random sample for oracle quality testing.

**Phase:** 3 (Oracle Validation)

**Usage:**
```bash
python scripts/validation/create_validation_sample.py \
  --input datasets/raw/master_dataset.jsonl \
  --output filters/uplifting/v4/validation_sample.jsonl \
  --sample-size 100 \
  --seed 2025
```

**Status:** ✅ Production ready

---

### `validation/generate_validation_summary.py`

**Purpose:** Generate training data validation reports for filter documentation.

**Phase:** 5 (Training Data Validation)

**Usage:**
```bash
python scripts/validation/generate_validation_summary.py \
  --data-dir datasets/training/uplifting_v4 \
  --filter-name uplifting \
  --version v4 \
  --output filters/uplifting/v4/TRAINING_DATA_VALIDATION.md
```

**Output:** `TRAINING_DATA_VALIDATION.md` in filter directory

**Status:** ✅ Production ready (used for all 3 filters, Nov 20, 2025)

---

### `validation/generate_prefilter_report.py`

**Purpose:** Retroactively validate prefilter by analyzing training data.

**Phase:** 4 (Prefilter Validation)

**Status:** ⚠️ Blocked by prefilter harmonization (see `docs/PREFILTER_HARMONIZATION_TASK.md`)

---

## Training Scripts (Phase 6-7)

### `training/compare_training_modes.py`

**Purpose:** Compare knowledge distillation vs instruction tuning performance.

**Phase:** 6 (Model Training)

**Usage:**
```bash
python scripts/training/compare_training_modes.py \
  --filter filters/uplifting/v4 \
  --data-dir datasets/training/uplifting_v4
```

**Output:** Training comparison report

**Status:** ✅ Ready for use

---

### `training/generate_training_report.py`

**Purpose:** Generate comprehensive training results report.

**Phase:** 6 (Model Training)

**Usage:**
```bash
python scripts/training/generate_training_report.py \
  --model models/uplifting_v4 \
  --test-set datasets/training/uplifting_v4/test.jsonl \
  --output filters/uplifting/v4/training_report.md
```

**Output:** `training_report.md` in filter directory

**Status:** ✅ Ready for use

---

### `training/plot_learning_curves.py`

**Purpose:** Visualize training metrics (loss, MAE over epochs).

**Phase:** 6 (Model Training)

**Usage:**
```bash
python scripts/training/plot_learning_curves.py \
  --checkpoint-dir models/uplifting_v4/checkpoints \
  --output reports/uplifting_v4_learning_curves.png
```

**Status:** ✅ Ready for use

---

## Oracle Scripts (Phase 3)

### `oracle/calibrate_oracle.py`

**Purpose:** Compare oracle models (Gemini Flash vs Pro vs Claude Sonnet).

**Phase:** 3 (Oracle Validation)

**Usage:**
```bash
python scripts/oracle/calibrate_oracle.py \
  --filter filters/uplifting/v4 \
  --sample filters/uplifting/v4/validation_sample.jsonl \
  --models gemini-flash,gemini-pro,claude-sonnet \
  --output filters/uplifting/v4/oracle_calibration_report.md
```

**Output:** Comparison report (agreement rates, cost analysis)

**Status:** ✅ Production ready

---

### `oracle/calibrate_prefilter.py`

**Purpose:** Measure prefilter pass rate and block reason distribution.

**Phase:** 4 (Prefilter Validation)

**Usage:**
```bash
python scripts/oracle/calibrate_prefilter.py \
  --filter filters/uplifting/v4 \
  --source datasets/raw/master_dataset.jsonl \
  --sample-size 1000 \
  --output filters/uplifting/v4/prefilter_calibration_report.md
```

**Output:** Pass rate, block reasons, false negative analysis

**Status:** ✅ Production ready

---

## Deployment Scripts (Phase 9)

### `deployment/upload_to_huggingface.py`

**Purpose:** Upload trained model to Hugging Face Hub.

**Phase:** 9 (Deployment)

**Usage:**
```bash
python scripts/deployment/upload_to_huggingface.py \
  --model models/uplifting_v4 \
  --repo-name llm-distillery/uplifting-v4 \
  --private
```

**Status:** ✅ Ready for use (when models trained)

---

## Dataset Scripts (General Utilities)

### `dataset/create_random_sample.py`

**Purpose:** Create random sample from any dataset (general utility).

**Usage:**
```bash
python scripts/dataset/create_random_sample.py \
  --input datasets/raw/master_dataset.jsonl \
  --output sample.jsonl \
  --sample-size 500 \
  --seed 42
```

**Note:** Similar to `validation/create_validation_sample.py` but more general-purpose.

**Status:** ✅ Production ready

---

## Core Tools (NOT in scripts/)

These are **core modules** (imported by other code), not standalone scripts:

### `ground_truth/` (Core Modules)
- `batch_scorer.py` - Universal oracle scoring engine
- `llm_evaluators.py` - Oracle API wrappers
- `secrets_manager.py` - API key management
- `text_cleaning.py` - Text sanitization
- `samplers.py` - Sampling strategies

### `training/` (Core Modules)
- `prepare_data.py` - Train/val/test splitting
- `validate_training_data.py` - Quality validation
- `deduplicate_training_data.py` - Duplicate removal
- `train.py` - Model training (future)

### `filters/` (Core Code)
- `base_prefilter.py` - Base prefilter class
- `{filter}/{version}/prefilter.py` - Filter implementation
- `{filter}/{version}/postfilter.py` - Tier classification

---

## Archived Scripts

**Location:** `archive/scripts/`

### `filter_specific/`
- Filter-specific validation scripts (obsolete after harmonization)
- `validate_false_negatives.py`, `validate_prefilter_options.py`, etc.

### `one_off/`
- One-time analysis scripts
- `generate_synthetic_training_data.py`, etc.

### `obsolete/`
- Scripts for OLD data format (pre-harmonization)
- `analyze_uplifting_dataset.py`, `verify_sustainability_tech_data.py`, etc.

### `sandbox/`
- Experimental/testing scripts (already archived)

---

## Design Principles

### ✅ Scripts Should Be:

1. **Standalone** - Don't require imports from other scripts
2. **Filter-agnostic** - Work with harmonized data format
3. **Phase-specific** - Organized by filter development phase
4. **Well-documented** - Clear usage, inputs, outputs
5. **Reusable** - Can be used across multiple filters

### ❌ Scripts Should NOT Be:

1. **Core modules** - If imported by other code, it's not a script
2. **Filter-specific** - No hardcoded dimensions or field names
3. **One-off** - Single-use scripts should be archived
4. **Duplicative** - Use existing tools when possible

---

## When to Add New Scripts

**Add to `scripts/` if:**
- Standalone utility for filter development workflow
- Used across multiple filters
- Part of standard phases (1-9)
- Generates reports or visualizations

**Keep elsewhere if:**
- Core functionality (ground_truth/, training/)
- Filter-specific code (prefilter.py, postfilter.py)
- One-off analysis (archive after use)
- Experimental (sandbox/)

---

## Related Documentation

- **Filter Development Guide:** `docs/agents/filter-development-guide.md`
- **Scripts Reorganization Plan:** `docs/SCRIPTS_REORGANIZATION_PLAN.md`
- **Prefilter Harmonization:** `docs/PREFILTER_HARMONIZATION_TASK.md`

---

**Last Updated:** 2025-11-20
**Structure:** Organized by phase (validation/training/oracle/deployment/dataset)
**Active Scripts:** 11 (10 production-ready, 1 blocked)
