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

# jeergrvgreg/human-thriving-filter-v8

> ⛔ **NOT PUBLISHED.** `jeergrvgreg/human-thriving-filter-v8` does not exist on the Hub. This card is the
> package's model-card source (`README_MODEL.md`), kept per the project doc
> standard; the repo id below is the name publishing would use, not a live link.
> The filter directory's `NO_HUB` file records why and what would change it.

## Model Description

This model is a fine-tuned version of [google/gemma-3-1b-pt](https://huggingface.co/google/gemma-3-1b-pt)
for multi-dimensional content scoring using the **human_thriving** filter.

The model was trained using **knowledge distillation** from DeepSeek, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: DOCUMENTED OUTCOMES delivered to people, not emotional tone, funding, or speculation

## Intended Use

This model scores articles across 6 semantic dimensions:

- **Human Wellbeing Impact** (weight: 0.30): Improvement in health, safety, livelihoods, or basic needs
- **Social Cohesion Impact** (weight: 0.20): Bonds among people: trust, belonging, cooperation between groups
- **Justice Rights Impact** (weight: 0.15): Rights expanded, accountability delivered, injustice actively addressed
- **Evidence Level** (weight: 0.10): Verification OF THE THRIVING OUTCOME, not general journalism quality
- **Benefit Distribution** (weight: 0.10): Distribution OF THE BENEFIT -- who actually receives it, not audience size
- **Change Durability** (weight: 0.15): How lasting the change is: episodic, sustained, or structural


## Training Data

- **Training samples**: 5,268
- **Validation samples**: 658
- **Oracle**: DeepSeek (for ground truth generation)

## Training Procedure

### Model Architecture

- **Base model**: google/gemma-3-1b-pt
- **Parameters**: 1,012,945,536
- **Task**: Multi-dimensional regression (6 outputs)
- **Input**: Article title + content (max 512 tokens)
- **Output**: 6 continuous scores (0-10 range)

### Training Configuration

- **Epochs**: 6 trained, checkpoint from epoch 5
- **Batch size**: 8
- **Learning rate**: 2e-05
- **Optimizer**: AdamW
- **Loss function**: Mean Squared Error (MSE)
- **Gradient checkpointing**: Enabled

## Performance

### Overall Metrics

| Metric | Value |
|--------|-------|
| Validation MAE | 0.5715 |
| Training MAE | 0.4303 |
| Validation RMSE | 0.9498 |
| Training RMSE | 0.6781 |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
| Human Wellbeing Impact | 0.5771 |
| Social Cohesion Impact | 0.5368 |
| Justice Rights Impact | 0.4300 |
| Evidence Level | 0.6756 |
| Benefit Distribution | 0.5879 |
| Change Durability | 0.6216 |


## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "jeergrvgreg/human-thriving-filter-v8"
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

dimensions = ['human_wellbeing_impact', 'social_cohesion_impact', 'justice_rights_impact', 'evidence_level', 'benefit_distribution', 'change_durability']
for dim, score in zip(dimensions, scores):
    print(f"{dim}: {score:.2f}")
```

## Limitations

- Trained on the project's production news corpus. Language coverage is a property
  of that corpus and of the filter, and is not asserted here — see the filter's
  `README.md`.
- Performance may vary on other content types
- Validation MAE of 0.5715 indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: 0.14)

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{human_thriving_filter_v8_0,
  title={Human_Thriving Content Filter},
  author={Your Name},
  year={2026},
  url={https://huggingface.co/jeergrvgreg/human-thriving-filter-v8}
}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
