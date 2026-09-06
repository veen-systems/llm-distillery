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

# jeergrvgreg/solutions-filter-v6

## Model Description

This model is a fine-tuned version of [google/gemma-3-1b-pt](https://huggingface.co/google/gemma-3-1b-pt)
for multi-dimensional content scoring using the **solutions** filter.

The model was trained using **knowledge distillation** from DeepSeek, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: Solutions lens — concrete actions toward problems across tech, governance, and community

## Intended Use

This model scores articles across 7 semantic dimensions:

- **Solution Concreteness** (weight: 0.20): Is this a CONCRETE ACTION with measurable outputs, or aspirational
rhetoric? Universal across tech / governance / community.

- **Systemic Impact** (weight: 0.20): Scale of the SOLUTION'S actual or credibly-planned reach — NOT the
size of the problem it addresses. Tech: deployment scope.
Governance: population covered by the mechanism. Community: current
reach (replicability across communities belongs to
community_practice_strength).

- **Evidence Strength** (weight: 0.15): Is the solution claim supported by data, cases, peer review, or only
by stakeholder quotes? Cross-cuts all solution types.

- **Governance Intervention Strength** (weight: 0.15): Captures policy reform, institutional design, regulatory innovation.
Score 0 for pure-tech articles with no governance angle. Scores
ALONGSIDE community_practice_strength for hybrid solutions — they
are not mutually exclusive.

- **Community Practice Strength** (weight: 0.10): Captures grassroots, mutual aid, local initiatives, behavioral
practices. Score 0 for pure-tech / pure-policy articles. Scores
ALONGSIDE governance_intervention_strength for hybrid solutions.

- **Equity Access** (weight: 0.10): Does the solution distribute benefits equitably, or concentrate them
among existing advantaged groups?

- **Economic Viability** (weight: 0.10): Is the solution financially / resource sustainable? Tech: cost-
competitive at scale. Governance: fiscally feasible. Community:
sustainable resource model (volunteer time, funding stream).



## Training Data

- **Training samples**: 8,236
- **Validation samples**: 1,029
- **Oracle**: DeepSeek (for ground truth generation)

## Training Procedure

### Model Architecture

- **Base model**: google/gemma-3-1b-pt
- **Parameters**: 1,012,947,840
- **Task**: Multi-dimensional regression (7 outputs)
- **Input**: Article title + content (max 512 tokens)
- **Output**: 7 continuous scores (0-10 range)

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
| Validation MAE | 0.4760 |
| Training MAE | 0.4041 |
| Validation RMSE | 1.0660 |
| Training RMSE | 0.8975 |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
| Solution Concreteness | 0.6479 |
| Systemic Impact | 0.5658 |
| Evidence Strength | 0.5456 |
| Governance Intervention Strength | 0.4428 |
| Community Practice Strength | 0.2308 |
| Equity Access | 0.4486 |
| Economic Viability | 0.4505 |


## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "jeergrvgreg/solutions-filter-v6"
base_model_name = "google/gemma-3-1b-pt"

# IMPORTANT: AutoModelForSequenceClassification does NOT work for Gemma-3
# (gemma3_text config type is not in the Auto mapping).
# Use the project's model_loading helper instead:
from filters.common.model_loading import load_base_model_for_seq_cls
base_model = load_base_model_for_seq_cls(
    base_model_name, num_labels=7, problem_type="regression"
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

dimensions = ['solution_concreteness', 'systemic_impact', 'evidence_strength', 'governance_intervention_strength', 'community_practice_strength', 'equity_access', 'economic_viability']
for dim, score in zip(dimensions, scores):
    print(f"{dim}: {score:.2f}")
```

## Limitations

- Trained on the project's production news corpus. Language coverage is a property
  of that corpus and of the filter, and is not asserted here — see the filter's
  `README.md`.
- Performance may vary on other content types
- Validation MAE of 0.4760 indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: 0.07)

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{solutions_filter_v6_0,
  title={Solutions Content Filter},
  author={Your Name},
  year={2026},
  url={https://huggingface.co/jeergrvgreg/solutions-filter-v6}
}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
