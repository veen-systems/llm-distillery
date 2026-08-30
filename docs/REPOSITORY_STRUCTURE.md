# Repository Structure

This document explains the LLM Distillery repository organization.

## Core Principle

**Filters are self-contained units** that include their configuration and trained models. **Reports** document how filters were trained.

## Directory Layout

```
llm-distillery/
├── filters/                    # Self-contained filter packages (versioned)
│   ├── common/                 # Shared filter utilities
│   │   ├── __init__.py
│   │   ├── base_prefilter.py   # Base prefilter class
│   │   └── text_cleaning.py    # Text sanitization utilities
│   ├── {filter_name}/
│   │   └── v{version}/
│   │       ├── config.yaml              # Filter configuration
│   │       ├── prefilter.py             # Pre-filter rules
│   │       ├── postfilter.py            # Tier classification logic
│   │       ├── prompt-compressed.md     # Oracle prompt (compressed)
│   │       ├── README.md                # Filter documentation
│   │       ├── TRAINING_DATA_VALIDATION.md  # Validation report
│   │       ├── prefilter_validation_report.md  # Prefilter validation
│   │       ├── reports/                 # Filter-specific reports
│   │       │   ├── oracle_calibration_report.md
│   │       │   └── training_report.md (future)
│   │       └── model/                   # Trained model (gitignored)
│   │           ├── config.json
│   │           ├── model.safetensors
│   │           └── tokenizer files
│   └── base_prefilter.py       # Backward compat (re-exports from common)
│
├── datasets/                   # Generated datasets (gitignored)
│   ├── raw/                    # Raw article collections
│   │   └── master_dataset.jsonl
│   ├── scored/                 # Oracle-scored batches
│   │   └── {filter}_v{version}_training/
│   │       └── labeled_batch_*.jsonl
│   └── training/               # Prepared train/val/test splits
│       └── {filter}_v{version}/
│           ├── train.jsonl (80%)
│           ├── val.jsonl (10%)
│           └── test.jsonl (10%)
│
├── ground_truth/               # Core: Oracle scoring pipeline
│   ├── __init__.py
│   ├── batch_scorer.py         # Universal scoring engine
│   ├── llm_evaluators.py       # Oracle API wrappers
│   ├── secrets_manager.py      # API key management
│   ├── text_cleaning.py        # Text sanitization
│   └── samplers.py             # Sampling strategies
│
├── training/                   # Core: Model training pipeline
│   ├── __init__.py
│   ├── prepare_data.py         # Stratified train/val/test splits
│   ├── validate_training_data.py  # Quality validation
│   ├── deduplicate_training_data.py  # Cross-split deduplication
│   ├── train.py                # Model fine-tuning (planned)
│   ├── configs/                # Training configurations
│   ├── README.md
│   ├── GPU_TEST_GUIDE.md
│   └── HUGGINGFACE_SETUP.md
│
├── scripts/                    # Utility scripts (organized by phase)
│   ├── validation/             # Phase 3-5: Validation utilities
│   │   ├── create_validation_sample.py
│   │   ├── generate_validation_summary.py
│   │   └── generate_prefilter_report.py
│   ├── training/               # Phase 6-7: Training utilities
│   │   ├── compare_training_modes.py
│   │   ├── generate_training_report.py
│   │   └── plot_learning_curves.py
│   ├── oracle/                 # Phase 3: Oracle calibration
│   │   ├── calibrate_oracle.py
│   │   └── calibrate_prefilter.py
│   ├── corpus/                 # Phase 0: corpus assembly (added 2026-08-29)
│   │   ├── draw_v8_corpus.py       # reduce / draw / verify / manifest
│   │   └── materialise_corpus.py   # rejoin article text, verifying content hashes
│   ├── deployment/             # Phase 9: Model deployment
│   │   └── upload_to_huggingface.py
│   ├── dataset/                # General dataset utilities
│   │   └── create_random_sample.py
│   └── README.md               # Scripts documentation
│
├── docs/                       # Documentation
│   ├── agents/                 # Development guide agents
│   │   ├── README.md
│   │   ├── filter-development-guide.md
│   │   └── filter-harmonizer.md
│   ├── decisions/              # Architecture decision records
│   ├── reports/                # General reports (not filter-specific)
│   ├── ARCHITECTURE.md         # System architecture
│   ├── SYSTEM_OVERVIEW.md      # Current state & datasets
│   ├── REPOSITORY_STRUCTURE.md # This file
│   ├── DECISIONS.md            # Strategic decisions
│   ├── PREFILTER_HARMONIZATION_TASK.md  # Task documentation
│   └── SCRIPTS_REORGANIZATION_PLAN.md   # Scripts reorganization plan
│
├── archive/                    # Archived/obsolete code
│   ├── filters_deprecated/     # Old filter versions
│   └── scripts/                # Archived scripts
│       ├── obsolete/           # Old, incompatible scripts
│       ├── filter_specific/    # Filter-specific validation scripts
│       ├── one_off/            # One-time analysis scripts
│       └── sandbox/            # Experimental scripts
│
├── experiments/                # Append-only experiment registry (added 2026-08-29)
│   ├── README.md               # schema, adaptations from veen-systems/augur
│   └── registry.jsonl          # one line per concluded experiment
│
├── tests/                      # Test suite
│   ├── conftest.py             # Shared pytest fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_base_prefilter.py
│   │   ├── test_batch_scorer.py
│   │   └── test_prepare_data.py
│   ├── integration/            # Integration tests
│   │   └── test_filter_loading.py
│   └── ml/                     # ML-focused tests
│       ├── test_data_pipeline.py   # Training data validation
│       ├── test_inference.py       # Model inference tests
│       └── test_reproducibility.py # Determinism tests
│
├── config/                     # Configuration
│   └── credentials/            # API keys (git-ignored)
│       └── secrets.ini
│
├── README.md                   # Project overview and quick start
└── CHANGELOG.md                # Version history
```

## Key Design Decisions

### 1. Filters Are Self-Contained Packages

Each filter version is a **complete package** containing everything needed:
- Configuration (dimensions, weights, thresholds, gatekeepers)
- Prefilter rules (Python class with `should_label()` method)
- Postfilter logic (tier classification without retraining)
- Oracle prompt (compressed version for production use)
- Validation reports (training data validation, prefilter validation)
- Filter-specific reports (oracle calibration, training results)
- Trained model weights (gitignored, ~1-4GB)

**Benefits:**
- Easy to version (just copy the filter directory)
- Clear ownership of all artifacts
- Simple to deploy (entire package is self-contained)
- Independent evolution (each filter can progress separately)

### 2. Core Modules vs Utility Scripts

**Core Modules** (`ground_truth/`, `training/`):
- Python packages with `__init__.py`
- Imported by other code
- Core functionality (batch scoring, data preparation)
- Stay in root directory

**Utility Scripts** (`scripts/`):
- Standalone tools (not imported)
- Generate reports or visualizations
- Organized by development phase
- Filter-agnostic (work with harmonized data format)

**Phase-Based Organization:**
- `validation/` - Phase 3-5: Validation & QA
- `training/` - Phase 6-7: Training utilities
- `oracle/` - Phase 3: Oracle calibration
- `deployment/` - Phase 9: Model deployment
- `dataset/` - General dataset utilities

### 3. Reports Live With Filters

Training reports and validation artifacts live **within filter directories** because:
- They document HOW the specific filter was validated and trained
- Makes filters independently auditable
- Self-contained packages for deployment
- Clear ownership and versioning

**Exception:** General reports (not filter-specific) go in `docs/reports/`

### 4. Archive for Historical Code

The `archive/` directory contains:
- **obsolete/** - Old scripts written for pre-harmonization data format
- **filter_specific/** - Filter-specific validation scripts (superseded)
- **one_off/** - One-time analysis scripts
- **sandbox/** - Experimental/testing scripts
- **filters_deprecated/** - Old filter versions

**Why archive instead of delete:**
- Reference for understanding evolution
- May contain useful patterns for future work
- Audit trail for decisions made

### 5. Clean Root Directory

Root contains only:
- `README.md` - Project overview and quick start
- `CHANGELOG.md` - Version history (standard practice)
- Core module directories (`ground_truth/`, `training/`, `filters/`)
- Support directories (`scripts/`, `docs/`, `datasets/`, `config/`, `archive/`, `tests/`)
- `experiments/` — the append-only experiment registry (added 2026-08-29; see its README)

**No dangling files** - everything has a clear location

## Workflows

### Complete Filter Development (9 Phases)

See [Filter Development Guide](agents/filter-development-guide.md) for complete workflow.

#### Phase 1-2: Planning & Architecture (1-2 days)
```bash
# 1. Create filter directory structure
mkdir -p filters/my_filter/v1

# 2. Create config.yaml with dimensions, tiers, gatekeepers
# 3. Write prompt-compressed.md with oracle prompt
# 4. Write prefilter.py with rule-based filtering
# 5. Write postfilter.py with tier classification logic
```

#### Phase 3-5: Validation & Training Data (3-5 days)

```bash
# 1. Score 5K+ articles with oracle
python -m ground_truth.batch_scorer \
    --filter filters/my_filter/v1 \
    --source datasets/raw/master_dataset.jsonl \
    --output-dir datasets/scored/my_filter_v1_training \
    --llm gemini-flash \
    --target-count 5000 \
    --batch-size 100

# 2. Prepare train/val/test splits with stratification
python training/prepare_data.py \
    --filter filters/my_filter/v1 \
    --data-source datasets/scored/my_filter_v1_training \
    --output-dir datasets/training/my_filter_v1

# 3. Validate training data quality
python training/validate_training_data.py \
    --data-dir datasets/training/my_filter_v1 \
    --filter filters/my_filter/v1

# 4. Deduplicate if needed
python training/deduplicate_training_data.py datasets/training/my_filter_v1

# 5. Generate validation report
python scripts/validation/generate_validation_summary.py \
    --data-dir datasets/training/my_filter_v1 \
    --filter-name my_filter \
    --version v1 \
    --output filters/my_filter/v1/TRAINING_DATA_VALIDATION.md
```

#### Phase 6: Model Training (1-2 days)

```bash
# Train Qwen2.5-7B student model
python training/train.py \
    --filter filters/my_filter/v1 \
    --data-dir datasets/training/my_filter_v1 \
    --output-dir models/my_filter_v1 \
    --base-model unsloth/Qwen2.5-7B-Instruct \
    --epochs 3 \
    --batch-size 4

# Generate learning curves
python scripts/training/plot_learning_curves.py \
    --checkpoint-dir models/my_filter_v1/checkpoints \
    --output filters/my_filter/v1/reports/learning_curves.png

# Generate training report
python scripts/training/generate_training_report.py \
    --model models/my_filter_v1 \
    --test-set datasets/training/my_filter_v1/test.jsonl \
    --output filters/my_filter/v1/reports/training_report.md
```

#### Phase 9: Deployment

```bash
# Upload to Hugging Face
python scripts/deployment/upload_to_huggingface.py \
    --model models/my_filter_v1 \
    --repo-name llm-distillery/my-filter-v1 \
    --private
```

### Using a Trained Filter

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load from filter directory
filter_path = "filters/uplifting/v1/model"
tokenizer = AutoTokenizer.from_pretrained(filter_path)
model = AutoModelForSequenceClassification.from_pretrained(filter_path)

# Or load from Hugging Face (if deployed)
model = AutoModelForSequenceClassification.from_pretrained(
    "your-username/uplifting-filter-v1"
)
```

### Creating a New Filter Version

When improving a filter:

```bash
# 1. Copy the filter directory
cp -r filters/uplifting/v4 filters/uplifting/v5

# 2. Update config.yaml with new version and changes
# Edit filters/uplifting/v5/config.yaml
# Update version number, modify dimensions/gatekeepers/tiers as needed

# 3. Clear old validation reports
rm filters/uplifting/v5/TRAINING_DATA_VALIDATION.md
rm -rf filters/uplifting/v5/reports/

# 4. Score new training data
python -m ground_truth.batch_scorer \
    --filter filters/uplifting/v5 \
    --source datasets/raw/master_dataset.jsonl \
    --output-dir datasets/scored/uplifting_v5_training \
    --llm gemini-flash \
    --target-count 5000

# 5. Prepare and validate training data
python training/prepare_data.py \
    --filter filters/uplifting/v5 \
    --data-source datasets/scored/uplifting_v5_training \
    --output-dir datasets/training/uplifting_v5

# 6. Train the new version
python training/train.py \
    --filter filters/uplifting/v5 \
    --data-dir datasets/training/uplifting_v5 \
    --output-dir models/uplifting_v5

# 7. Compare validation reports
diff filters/uplifting/v4/TRAINING_DATA_VALIDATION.md \
     filters/uplifting/v5/TRAINING_DATA_VALIDATION.md
```

## What Gets Committed to Git

**Yes (small files):**
- Filter configurations (config.yaml, prefilter.py, postfilter.py)
- Filter documentation (README.md, prompt-compressed.md)
- Validation reports (TRAINING_DATA_VALIDATION.md, prefilter_validation_report.md)
- Training metadata (training_*.json - when implemented)
- Core modules and utility scripts
- Documentation (markdown files)

**No (large files - gitignored):**
- Model weights (*.safetensors, *.bin, etc.) - ~1-4GB per filter
- Datasets (*.jsonl) - Raw, scored, and training splits
- Large reports (*.docx, *.pdf) - If generated
- Visualizations (*.png) - Learning curves, plots

**Why gitignore large files:**
- Git is not designed for large binary files
- Model weights can be regenerated by retraining
- Datasets can be regenerated by rescoring
- Use Hugging Face Hub for model sharing
- Use LFS or cloud storage for large datasets if needed

## Current Status (November 2025)

### Repository State

**Phase 5 Complete**: Training Data Validated ✅

All three active filters have:
- ✅ Self-contained directory structure
- ✅ Validated training datasets (16,553 total examples)
- ✅ Clean repository organization
- ✅ Phase-based scripts organization
- ✅ Comprehensive documentation

**Next Phase**: Model training (Qwen2.5-7B fine-tuning)

### Active Filters

| Filter | Version | Examples | Status |
|--------|---------|----------|--------|
| uplifting | v4 | 6,705 | ✅ Ready for training |
| sustainability_tech_innovation | v2 | 4,968 | ✅ Ready for training |
| investment-risk | v4 | 4,880 | ✅ Ready for training |

## Migration Notes

### From Old Structure (Before Nov 2025)

If you have the old structure with dangling files:

```bash
# 1. Move architecture docs to docs/
mv ARCHITECTURE.md SYSTEM_OVERVIEW.md DECISIONS.md docs/

# 2. Organize scripts by phase
mkdir -p scripts/{validation,training,oracle,deployment,dataset}
# Move scripts to appropriate subdirectories

# 3. Move filter reports to filter directories
mv reports/{filter}_v{version}_* filters/{filter}/v{version}/reports/

# 4. Archive obsolete scripts
mkdir -p archive/scripts/{obsolete,filter_specific,one_off}
# Move old scripts to archive

# 5. Clean root directory
# Remove any remaining dangling .py or .md files
```

The current structure (as of Nov 20, 2025) is the recommended organization.
