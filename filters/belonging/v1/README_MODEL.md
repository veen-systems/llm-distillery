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

# jeergrvgreg/belonging-filter-v1

## Model Description

This model is a fine-tuned version of [google/gemma-3-1b-pt](https://huggingface.co/google/gemma-3-1b-pt)
for multi-dimensional content scoring using the **belonging** filter.

The model was trained using **knowledge distillation** from Gemini Flash, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: Gemeinschaft over Gesellschaft: organic community bonds, rootedness, intergenerational ties

## Intended Use

This model scores articles across 6 semantic dimensions:

- **Intergenerational Bonds** (weight: 0.25): Youth-elder connections, mentorship across ages, traditional knowledge transfer
- **Community Fabric** (weight: 0.25): Mutual aid, neighborly ties, third places, local institutions, civic participation
- **Reciprocal Care** (weight: 0.10): Family proximity, multigenerational living, elder care at home, mutual dependency as good
- **Rootedness** (weight: 0.15): Long-term residence, place attachment, local knowledge, staying put
- **Purpose Beyond Self** (weight: 0.15): Meaning through contribution, ikigai/plan de vida, service to others, vocation
- **Slow Presence** (weight: 0.10): Unhurried time together, rituals, shared meals, sabbath practices, presence over productivity


## Training Data

- **Training samples**: 5,894
- **Validation samples**: 738
- **Oracle**: Gemini Flash (for ground truth generation)

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
| Validation MAE | 0.5343 |
| Training MAE | 0.5286 |
| Validation RMSE | 0.9103 |
| Training RMSE | 0.8778 |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
| Intergenerational Bonds | 0.5231 |
| Community Fabric | 0.5915 |
| Reciprocal Care | 0.5082 |
| Rootedness | 0.5317 |
| Purpose Beyond Self | 0.5957 |
| Slow Presence | 0.4555 |


## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "jeergrvgreg/belonging-filter-v1"
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

dimensions = ['intergenerational_bonds', 'community_fabric', 'reciprocal_care', 'rootedness', 'purpose_beyond_self', 'slow_presence']
for dim, score in zip(dimensions, scores):
    print(f"{dim}: {score:.2f}")
```

## Limitations

- Trained on the project's production news corpus. Language coverage is a property
  of that corpus and of the filter, and is not asserted here — see the filter's
  `README.md`.
- Performance may vary on other content types
- Validation MAE of 0.5343 indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: 0.01)

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{belonging_filter_v1_0,
  title={Belonging Content Filter},
  author={Your Name},
  year={2025},
  url={https://huggingface.co/jeergrvgreg/belonging-filter-v1}
}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
