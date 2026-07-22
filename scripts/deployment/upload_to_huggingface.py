"""
Upload trained model to Hugging Face Hub.

This script uploads your trained model, tokenizer, and metadata to Hugging Face
for easy deployment and sharing. Models are uploaded as PRIVATE by default.
"""

import argparse
import json
from pathlib import Path
from typing import Dict

import yaml


def create_model_card(
    filter_config: Dict,
    training_metadata: Dict,
    training_history: list,
    repo_name: str,
) -> str:
    """Generate Hugging Face model card (README.md)."""

    final_epoch = training_history[-1]
    val_mae = final_epoch['val']['mae']

    # Oracle provenance must come from config, NOT a hardcoded string — solutions
    # v4 and cultural-discovery v5 use DeepSeek, not Gemini. Prefer an explicit
    # training_metadata.oracle, else config.yaml oracle.recommended, else generic.
    oracle = (
        training_metadata.get('oracle')
        or filter_config.get('oracle', {}).get('recommended')
        or 'the configured oracle'
    )
    oracle_label = {
        'deepseek': 'DeepSeek', 'gemini-flash': 'Gemini Flash',
        'gemini-pro': 'Gemini Pro',
    }.get(str(oracle).lower(), str(oracle))

    card = f"""---
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

# {repo_name}

## Model Description

This model is a fine-tuned version of [{training_metadata['model_name']}](https://huggingface.co/{training_metadata['model_name']})
for multi-dimensional content scoring using the **{filter_config['filter']['name']}** filter.

The model was trained using **knowledge distillation** from {oracle_label}, learning to replicate
its judgment patterns on content evaluation.

**Filter Focus**: {filter_config['filter'].get('focus', filter_config['filter'].get('description', 'Multi-dimensional content scoring'))}

## Intended Use

This model scores articles across {training_metadata['num_dimensions']} semantic dimensions:

"""

    # Add dimensions
    for dim_name, dim_config in filter_config['scoring']['dimensions'].items():
        card += f"- **{dim_name.replace('_', ' ').title()}** (weight: {dim_config['weight']:.2f}): {dim_config['description']}\n"

    card += f"""

## Training Data

- **Training samples**: {training_metadata['train_examples']:,}
- **Validation samples**: {training_metadata['val_examples']:,}
- **Oracle**: {oracle_label} (for ground truth generation)
- **Quality threshold**: Articles with quality_score >= 0.7

## Training Procedure

### Model Architecture

- **Base model**: {training_metadata['model_name']}
- **Parameters**: {training_metadata['num_parameters']:,}
- **Task**: Multi-dimensional regression ({training_metadata['num_dimensions']} outputs)
- **Input**: Article title + content (max {training_metadata['max_length']} tokens)
- **Output**: {training_metadata['num_dimensions']} continuous scores (0-10 range)

### Training Configuration

- **Epochs**: {training_metadata['epochs']}
- **Batch size**: {training_metadata['batch_size']}
- **Learning rate**: {training_metadata['learning_rate']}
- **Optimizer**: AdamW
- **Loss function**: Mean Squared Error (MSE)
- **Gradient checkpointing**: Enabled

## Performance

### Overall Metrics

| Metric | Value |
|--------|-------|
| Validation MAE | {val_mae:.4f} |
| Training MAE | {final_epoch['train']['mae']:.4f} |
| Validation RMSE | {final_epoch['val']['rmse']:.4f} |
| Training RMSE | {final_epoch['train']['rmse']:.4f} |

### Per-Dimension Performance (Validation MAE)

| Dimension | MAE |
|-----------|-----|
"""

    for dim_name in training_metadata['dimension_names']:
        dim_mae = final_epoch['val'][f'{dim_name}_mae']
        card += f"| {dim_name.replace('_', ' ').title()} | {dim_mae:.4f} |\n"

    card += f"""

## Usage

This is a LoRA adapter. Load via PEFT:

```python
from transformers import AutoTokenizer
from peft import PeftModel
import torch

# Load base model + adapter
repo_name = "{repo_name}"
base_model_name = "{training_metadata['model_name']}"

# IMPORTANT: AutoModelForSequenceClassification does NOT work for Gemma-3
# (gemma3_text config type is not in the Auto mapping).
# Use the project's model_loading helper instead:
from filters.common.model_loading import load_base_model_for_seq_cls
base_model = load_base_model_for_seq_cls(
    base_model_name, num_labels={training_metadata['num_dimensions']}, problem_type="regression"
)

tokenizer = AutoTokenizer.from_pretrained(base_model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    base_model.config.pad_token_id = tokenizer.pad_token_id

model = PeftModel.from_pretrained(base_model, repo_name)
model.eval()

# Score an article
text = "Article Title\\n\\nArticle content here..."
inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

with torch.no_grad():
    scores = model(**inputs).logits[0].numpy()

dimensions = {training_metadata['dimension_names']}
for dim, score in zip(dimensions, scores):
    print(f"{{dim}}: {{score:.2f}}")
```

## Limitations

- Model was trained on English news articles
- Performance may vary on other content types
- Validation MAE of {val_mae:.4f} indicates ~0.8 point average error on 0-10 scale
- Some overfitting observed (train/val gap: {val_mae - final_epoch['train']['mae']:.2f})

## Ethical Considerations

This model evaluates content based on specific semantic dimensions. Users should:
- Understand the filter's focus and biases
- Not use as sole decision-maker for content moderation
- Regularly evaluate model performance on their specific use case
- Be aware that automated scoring may miss nuance

## Citation

If you use this model, please cite:

```bibtex
@misc{{{filter_config['filter']['name']}_filter_v{str(filter_config['filter']['version']).replace('.', '_')},
  title={{{filter_config['filter']['name'].title()} Content Filter}},
  author={{Your Name}},
  year={{{filter_config['filter'].get('created', '2026')[:4]}}},
  url={{https://huggingface.co/{repo_name}}}
}}
```

## Model Card Contact

For questions or feedback about this model, please open an issue in the repository.
"""

    return card


def main():
    parser = argparse.ArgumentParser(
        description="Upload trained model to Hugging Face Hub"
    )
    parser.add_argument(
        "--filter",
        type=Path,
        required=True,
        help="Path to filter directory containing trained model (e.g., filters/uplifting/v1)",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        required=True,
        help="Hugging Face repository name (e.g., username/uplifting-filter-v1)",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=True,
        help="Make repository private (default: True)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face token (or set HF_TOKEN env var)",
    )

    args = parser.parse_args()

    # Check huggingface_hub is installed
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("Error: huggingface_hub not installed")
        print("Install with: pip install huggingface_hub")
        return

    # Load model metadata from filter directory
    print(f"Loading model and metadata from {args.filter}")

    model_path = args.filter / "model"
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print(f"Make sure you've trained the model and it's saved in the filter directory")
        return

    history_path = args.filter / "training_history.json"
    metadata_path = args.filter / "training_metadata.json"

    if not history_path.exists() or not metadata_path.exists():
        print(f"Error: training_history.json or training_metadata.json not found in {args.filter}")
        return

    with open(history_path, "r") as f:
        training_history = json.load(f)

    if not training_history:
        print(f"Error: training_history.json is empty in {args.filter}")
        return

    with open(metadata_path, "r") as f:
        training_metadata = json.load(f)

    # Load filter config
    config_path = args.filter / "config.yaml"
    if not config_path.exists():
        print(f"Error: config.yaml not found in {args.filter}")
        return

    with open(config_path, "r") as f:
        filter_config = yaml.safe_load(f)

    print(f"\nModel: {training_metadata['model_name']}")
    print(f"Filter: {filter_config['filter']['name']} v{filter_config['filter']['version']}")
    print(f"Validation MAE: {training_history[-1]['val']['mae']:.4f}")
    print(f"Repository: {args.repo_name}")
    print(f"Private: {args.private}")

    # Get token
    import os
    token = args.token or os.environ.get("HF_TOKEN")

    # If no token provided, let HfApi auto-detect from saved login
    # (HfApi will check ~/.cache/huggingface/token automatically)
    if not token:
        token = None  # HfApi will use saved token from 'hf auth login'

    # Create repository
    print(f"\nCreating repository {args.repo_name}...")
    try:
        api = HfApi(token=token)
        create_repo(
            repo_id=args.repo_name,
            repo_type="model",
            private=args.private,
            token=token,
            exist_ok=True,
        )
        print("[OK] Repository created")
    except Exception as e:
        print(f"Error creating repository: {e}")
        return

    # Generate model card
    print("Generating model card...")
    model_card = create_model_card(
        filter_config,
        training_metadata,
        training_history,
        args.repo_name,
    )

    # Save model card locally (in filter directory)
    readme_path = args.filter / "README_MODEL.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(model_card)
    print(f"[OK] Model card saved to {readme_path}")

    # Upload files
    print(f"\nUploading to Hugging Face...")

    try:
        # Upload model directory
        print("  Uploading model files...")
        api.upload_folder(
            folder_path=str(model_path),
            repo_id=args.repo_name,
            repo_type="model",
            token=token,
        )

        # Upload README
        print("  Uploading model card...")
        api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=args.repo_name,
            repo_type="model",
            token=token,
        )

        # Upload metadata (optional, for reference)
        print("  Uploading training metadata...")
        api.upload_file(
            path_or_fileobj=str(metadata_path),
            path_in_repo="training_metadata.json",
            repo_id=args.repo_name,
            repo_type="model",
            token=token,
        )

        api.upload_file(
            path_or_fileobj=str(history_path),
            path_in_repo="training_history.json",
            repo_id=args.repo_name,
            repo_type="model",
            token=token,
        )

        print("\n[OK] Upload complete!")
        print(f"\nView your model at:")
        print(f"  https://huggingface.co/{args.repo_name}")

        if args.private:
            print("\n[INFO] Repository is PRIVATE - only you can access it")
            print("To make it public later, go to Settings on the model page")

    except Exception as e:
        print(f"\nError during upload: {e}")
        print(f"WARNING: Repository may be in a partial state. Re-run this script to complete upload.")
        print(f"  https://huggingface.co/{args.repo_name}/tree/main")
        return

    # Post-upload verification: try loading from Hub
    print("\n--- Post-upload verification ---")
    try:
        from peft import PeftModel

        from filters.common.model_loading import load_base_model_for_seq_cls

        num_dims = training_metadata["num_dimensions"]
        print(f"Loading base model ({training_metadata['model_name']})...")
        base_model = load_base_model_for_seq_cls(
            training_metadata["model_name"],
            num_labels=num_dims,
            problem_type="regression",
        )
        if base_model.config.pad_token_id is None:
            from transformers import AutoTokenizer

            tok = AutoTokenizer.from_pretrained(training_metadata["model_name"])
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
            base_model.config.pad_token_id = tok.pad_token_id

        print(f"Loading adapter from Hub ({args.repo_name})...")
        model = PeftModel.from_pretrained(
            base_model, args.repo_name, token=token
        )
        model.eval()
        print("[OK] Hub verification passed - model loads via PeftModel.from_pretrained()")
    except Exception as e:
        print(f"[WARN] Hub verification FAILED: {e}")
        print("The adapter may not load correctly from Hub.")
        print("Common cause: adapter was resaved with .default keys (see ADR-007).")
        print("Fix: use the original training output adapter, do NOT run resave_adapter.py before upload.")


if __name__ == "__main__":
    main()
