---
license: eupl-1.2
language: en
tags:
- text-classification
- content-filtering
- multi-dimensional-scoring
- knowledge-distillation
library_name: transformers
pipeline_tag: text-classification
---

# jeergrvgreg/nature-recovery-filter-v4

## Model Description

This model is a fine-tuned version of [google/gemma-3-1b-pt](https://huggingface.co/google/gemma-3-1b-pt)
for multi-dimensional content scoring using the **nature_recovery** filter.

The model was trained using **knowledge distillation** from DeepSeek, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: Documented ecological outcomes, not technologies, pledges, or doom

## Intended Use

This model scores articles across 6 semantic dimensions:

- **Recovery Evidence** (weight: 0.25): Is nature actually recovering? Species returning, populations growing, habitats regenerating, pollution declining
- **Measurable Outcomes** (weight: 0.20): Quantified results with data: before/after comparisons, population counts, area measurements, concentration reductions
- **Ecological Significance** (weight: 0.20): How ecologically important is the recovery? Keystone species, critical habitats, ecosystem function, trophic cascades
- **Restoration Scale** (weight: 0.15): Geographic scope and temporal duration of recovery
- **Human Agency** (weight: 0.10): Was recovery caused by deliberate human action — policy, restoration project, community effort, cessation of harm?
- **Protection Durability** (weight: 0.10): Will this recovery last? Legal protection, threat removal, sustainable management, ecological connectivity


## Training Data

- **Training samples**: 3,112
- **Validation samples**: 389
- **Oracle**: DeepSeek (for ground truth generation)

## Training Procedure

### Model Architecture

- **Base model**: google/gemma-3-1b-pt
- **Parameters**: 1,012,945,536
- **Task**: Multi-dimensional regression (6 outputs)
- **Input**: Article title + content (max 512 tokens)
- **Output**: 6 continuous scores (0-10 range)

### Training Configuration

- **Epochs**: 3
- **Batch size**: 8
- **Learning rate**: 2e-05
- **Optimizer**: AdamW
- **Loss function**: Mean Squared Error (MSE)
- **Gradient checkpointing**: Enabled

## Performance

### Overall Metrics

| Metric | Value |
|--------|-------|
| Validation MAE | 0.7730 |
| Training MAE | 0.7823 |
| Validation RMSE | 1.1683 |
| Training RMSE | 1.1642 |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
| Recovery Evidence | 0.7430 |
| Measurable Outcomes | 0.7951 |
| Ecological Significance | 0.8229 |
| Restoration Scale | 0.6911 |
| Human Agency | 0.9166 |
| Protection Durability | 0.6697 |


## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "jeergrvgreg/nature-recovery-filter-v4"
base_model_name = "google/gemma-3-1b-pt"

# IMPORTANT: AutoModelForSequenceClassification does NOT work for Gemma-3
# (gemma3_text config type is not in the Auto mapping).
# Use the project's model_loading helper instead:
from filters.common.model_loading import load_base_model_for_seq_cls
base_model = load_base_model_for_seq_cls(
    base_model_name, num_labels=6, problem_type="regression"
)

tokenizer = AutoTokenizer.from_pretrained(base_model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    base_model.config.pad_token_id = tokenizer.pad_token_id

model = PeftModel.from_pretrained(base_model, repo_name)
model.eval()

# Score an article
text = "Article Title\n\nArticle content here..."
inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

with torch.no_grad():
    scores = model(**inputs).logits[0].numpy()

dimensions = ['recovery_evidence', 'measurable_outcomes', 'ecological_significance', 'restoration_scale', 'human_agency', 'protection_durability']
for dim, score in zip(dimensions, scores):
    print(f"{dim}: {score:.2f}")
```

## Limitations

- Trained on the project's production news corpus. Language coverage is a property
  of that corpus and of the filter, and is not asserted here — see the filter's
  `README.md`.
- Performance may vary on other content types
- Validation MAE of 0.7730 indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: -0.01)

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{nature_recovery_filter_v4_0,
  title={Nature_Recovery Content Filter},
  author={Your Name},
  year={2026},
  url={https://huggingface.co/jeergrvgreg/nature-recovery-filter-v4}
}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
