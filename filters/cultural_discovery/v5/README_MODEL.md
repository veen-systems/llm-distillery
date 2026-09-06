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

# jeergrvgreg/cultural-discovery-filter-v5

## Model Description

This model is a fine-tuned version of [google/gemma-3-1b-pt](https://huggingface.co/google/gemma-3-1b-pt)
for multi-dimensional content scoring using the **cultural_discovery** filter.

The model was trained using **knowledge distillation** from DeepSeek, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: DISCOVERIES about art, culture, history AND CONNECTIONS between peoples/civilizations

## Intended Use

This model scores articles across 5 semantic dimensions:

- **Discovery Novelty** (weight: 0.25): Degree to which the article surfaces a new finding, revelation, or insight — not a known fact rehashed
- **Heritage Significance** (weight: 0.20): Cultural or historical importance of the subject matter — from local interest to UNESCO-level world heritage
- **Cross Cultural Connection** (weight: 0.25): Bridges between different peoples, traditions, or civilizations — documented exchange, shared origins, or meaningful dialogue
- **Human Resonance** (weight: 0.15): Personal stories, emotional depth, lived experience — connection to human meaning beyond dry facts
- **Evidence Quality** (weight: 0.15): Quality of sources, research depth, and documentation — from clickbait/speculation to peer-reviewed primary sources


## Training Data

- **Training samples**: 6,839
- **Validation samples**: 855
- **Oracle**: DeepSeek (for ground truth generation)

## Training Procedure

### Model Architecture

- **Base model**: google/gemma-3-1b-pt
- **Parameters**: 1,012,943,232
- **Task**: Multi-dimensional regression (5 outputs)
- **Input**: Article title + content (max 512 tokens)
- **Output**: 5 continuous scores (0-10 range)

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
| Validation MAE | 0.6968 |
| Training MAE | 0.6739 |
| Validation RMSE | 1.0532 |
| Training RMSE | 1.0060 |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
| Discovery Novelty | 0.8622 |
| Heritage Significance | 0.5647 |
| Cross Cultural Connection | 0.4867 |
| Human Resonance | 0.6756 |
| Evidence Quality | 0.8950 |


## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "jeergrvgreg/cultural-discovery-filter-v5"
base_model_name = "google/gemma-3-1b-pt"

# IMPORTANT: AutoModelForSequenceClassification does NOT work for Gemma-3
# (gemma3_text config type is not in the Auto mapping).
# Use the project's model_loading helper instead:
from filters.common.model_loading import load_base_model_for_seq_cls
base_model = load_base_model_for_seq_cls(
    base_model_name, num_labels=5, problem_type="regression"
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

dimensions = ['discovery_novelty', 'heritage_significance', 'cross_cultural_connection', 'human_resonance', 'evidence_quality']
for dim, score in zip(dimensions, scores):
    print(f"{dim}: {score:.2f}")
```

## Limitations

- Trained on the project's production news corpus. Language coverage is a property
  of that corpus and of the filter, and is not asserted here — see the filter's
  `README.md`.
- Performance may vary on other content types
- Validation MAE of 0.6968 indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: 0.02)

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{cultural_discovery_filter_v5_0,
  title={Cultural_Discovery Content Filter},
  author={Your Name},
  year={2026},
  url={https://huggingface.co/jeergrvgreg/cultural-discovery-filter-v5}
}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
