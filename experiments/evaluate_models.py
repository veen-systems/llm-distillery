"""
Stage 2 Model Evaluation — Compare Qwen2.5-1.5B, Qwen2.5-0.5B, and Gemma-3-1B.

Loads each trained model, scores the uplifting v5 val set, and reports:
- Per-dimension MAE
- Overall MAE and weighted average MAE
- Tier assignment accuracy
- Inference speed (ms/article)

Usage (on gpu-server):
    cd ~/llm-distillery-calibration
    python experiments/evaluate_models.py \
        --data-dir datasets/training/uplifting_v7 \
        --config filters/uplifting/v7/config.yaml
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from peft import PeftModel

from filters.common.text_preprocessing import extract_head_tail


def load_model(model_dir: Path, device: str):
    """Load a trained PEFT model from a local checkpoint directory."""
    model_path = model_dir / "model"

    # Load metadata to get base model name
    metadata_path = model_dir / "training_metadata.json"
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    base_model_name = metadata["model_name"]
    num_dims = metadata["num_dimensions"]

    print(f"  Base model: {base_model_name}")
    print(f"  Dimensions: {num_dims}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    base_model = AutoModelForSequenceClassification.from_pretrained(
        base_model_name,
        num_labels=num_dims,
        problem_type="regression",
    )
    if base_model.config.pad_token_id is None:
        base_model.config.pad_token_id = tokenizer.pad_token_id

    # Load PEFT adapter
    model = PeftModel.from_pretrained(base_model, str(model_path))
    model = model.merge_and_unload()  # Merge LoRA weights for faster inference
    model = model.to(device)
    model.eval()

    return model, tokenizer, metadata


def load_val_data(data_dir: Path):
    """Load validation data from JSONL."""
    val_path = data_dir / "val.jsonl"
    examples = []
    with open(val_path, "r", encoding="utf-8") as f:
        for line in f:
            examples.append(json.loads(line))
    return examples


def score_batch(model, tokenizer, texts, device, batch_size=8, max_length=512):
    """Score a batch of texts, return predictions tensor."""
    all_preds = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        encoding = tokenizer(
            batch_texts,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)

        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            all_preds.append(outputs.logits.cpu())

    return torch.cat(all_preds, dim=0)


def compute_tier(scores, weights, dimension_names, config):
    """Compute tier for a single article from dimension scores."""
    # Apply gatekeeper
    gatekeeper_applied = False
    gatekeepers = config["scoring"].get("gatekeepers", {})
    for gk_name, gk_config in gatekeepers.items():
        gk_dim = gk_config["dimension"]
        gk_threshold = gk_config["threshold"]
        gk_max_score = gk_config["max_score"]
        if gk_dim in dimension_names:
            dim_idx = dimension_names.index(gk_dim)
            if scores[dim_idx] < gk_threshold:
                gatekeeper_applied = True
                break

    # Compute weighted average
    weighted_avg = sum(s * w for s, w in zip(scores, weights))

    if gatekeeper_applied:
        weighted_avg = min(weighted_avg, gk_max_score)

    # Assign tier
    tiers = config["scoring"]["tiers"]
    if weighted_avg >= tiers["high"]["threshold"]:
        return "high", weighted_avg
    elif weighted_avg >= tiers["medium"]["threshold"]:
        return "medium", weighted_avg
    else:
        return "low", weighted_avg


def benchmark_speed(model, tokenizer, texts, device, batch_size=1, max_length=512, n_warmup=10, n_runs=100):
    """Benchmark inference speed with batch_size=1 (realistic production scenario)."""
    # Warmup
    for i in range(min(n_warmup, len(texts))):
        encoding = tokenizer(
            texts[i],
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            model(
                input_ids=encoding["input_ids"].to(device),
                attention_mask=encoding["attention_mask"].to(device),
            )

    # Timed runs
    torch.cuda.synchronize()
    start = time.perf_counter()
    for i in range(n_runs):
        encoding = tokenizer(
            texts[i % len(texts)],
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            model(
                input_ids=encoding["input_ids"].to(device),
                attention_mask=encoding["attention_mask"].to(device),
            )
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    return (elapsed / n_runs) * 1000  # ms per article


def evaluate_model(name, model, tokenizer, examples, config, device, dimension_names, weights):
    """Full evaluation of a single model."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {name}")
    print(f"{'='*60}")

    # Prepare texts with head+tail extraction
    texts = []
    labels = []
    for ex in examples:
        text = f"{ex['title']}\n\n{ex['content']}"
        text = extract_head_tail(text, tokenizer, head_tokens=256, tail_tokens=256)
        texts.append(text)
        labels.append(ex["labels"])

    labels_tensor = torch.tensor(labels, dtype=torch.float32)

    # Score all
    print("  Scoring val set...")
    preds = score_batch(model, tokenizer, texts, device, batch_size=8)

    # Per-dimension MAE
    print(f"\n  Per-dimension MAE:")
    dim_maes = {}
    for i, dim_name in enumerate(dimension_names):
        mae = torch.mean(torch.abs(preds[:, i] - labels_tensor[:, i])).item()
        dim_maes[dim_name] = mae
        print(f"    {dim_name}: {mae:.4f}")

    # Overall MAE
    overall_mae = torch.mean(torch.abs(preds - labels_tensor)).item()
    print(f"\n  Overall MAE: {overall_mae:.4f}")

    # Weighted average MAE
    weighted_preds = []
    weighted_labels = []
    for j in range(len(examples)):
        wp = sum(preds[j, i].item() * weights[i] for i in range(len(dimension_names)))
        wl = sum(labels_tensor[j, i].item() * weights[i] for i in range(len(dimension_names)))
        weighted_preds.append(wp)
        weighted_labels.append(wl)

    weighted_preds = np.array(weighted_preds)
    weighted_labels = np.array(weighted_labels)
    weighted_mae = np.mean(np.abs(weighted_preds - weighted_labels))
    print(f"  Weighted Avg MAE: {weighted_mae:.4f}")

    # Tier accuracy
    correct = 0
    tier_counts = {"high": 0, "medium": 0, "low": 0}
    tier_correct = {"high": 0, "medium": 0, "low": 0}

    for j in range(len(examples)):
        pred_scores = [preds[j, i].item() for i in range(len(dimension_names))]
        true_scores = [labels_tensor[j, i].item() for i in range(len(dimension_names))]

        pred_tier, _ = compute_tier(pred_scores, weights, dimension_names, config)
        true_tier, _ = compute_tier(true_scores, weights, dimension_names, config)

        tier_counts[true_tier] += 1
        if pred_tier == true_tier:
            correct += 1
            tier_correct[true_tier] += 1

    tier_accuracy = correct / len(examples)
    print(f"\n  Tier Accuracy: {tier_accuracy:.1%} ({correct}/{len(examples)})")
    for tier in ["high", "medium", "low"]:
        if tier_counts[tier] > 0:
            acc = tier_correct[tier] / tier_counts[tier]
            print(f"    {tier}: {acc:.1%} ({tier_correct[tier]}/{tier_counts[tier]})")

    # Speed benchmark
    print(f"\n  Benchmarking speed (batch_size=1, 100 runs)...")
    ms_per_article = benchmark_speed(model, tokenizer, texts, device, n_runs=100)
    print(f"  Speed: {ms_per_article:.1f} ms/article")

    return {
        "name": name,
        "overall_mae": overall_mae,
        "weighted_mae": weighted_mae,
        "dim_maes": dim_maes,
        "tier_accuracy": tier_accuracy,
        "tier_correct": tier_correct,
        "tier_counts": tier_counts,
        "ms_per_article": ms_per_article,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Stage 2 model candidates")
    parser.add_argument("--data-dir", type=Path, required=True, help="Path to training data dir with val.jsonl")
    parser.add_argument("--config", type=Path, required=True, help="Path to filter config.yaml")
    parser.add_argument("--models", type=str, nargs="+",
                        default=["experiments/qwen05b", "experiments/gemma3_1b"],
                        help="Paths to model experiment directories")
    parser.add_argument("--baseline", type=str, default=None,
                        help="Path to baseline model dir (if available locally)")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dimension_names = list(config["scoring"]["dimensions"].keys())
    weights = [config["scoring"]["dimensions"][d]["weight"] for d in dimension_names]

    print(f"Dimensions: {dimension_names}")
    print(f"Weights: {weights}")

    # Load val data
    examples = load_val_data(args.data_dir)
    print(f"Val examples: {len(examples)}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    results = []

    # Evaluate each model
    for model_dir_str in args.models:
        model_dir = Path(model_dir_str)
        if not model_dir.exists():
            print(f"\nSkipping {model_dir} (not found)")
            continue

        print(f"\nLoading model from {model_dir}...")
        model, tokenizer, metadata = load_model(model_dir, device)
        name = f"{metadata['model_name']} (local)"

        result = evaluate_model(name, model, tokenizer, examples, config, device, dimension_names, weights)
        results.append(result)

        # Free GPU memory
        del model
        torch.cuda.empty_cache()

    # Evaluate baseline if provided
    if args.baseline:
        baseline_dir = Path(args.baseline)
        if baseline_dir.exists():
            print(f"\nLoading baseline from {baseline_dir}...")
            model, tokenizer, metadata = load_model(baseline_dir, device)
            name = f"{metadata['model_name']} (baseline)"
            result = evaluate_model(name, model, tokenizer, examples, config, device, dimension_names, weights)
            results.append(result)
            del model
            torch.cuda.empty_cache()

    # Print comparison table
    print(f"\n{'='*80}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"\n{'Model':<35} {'MAE':>8} {'W-MAE':>8} {'Tier%':>8} {'ms/art':>8}")
    print(f"{'-'*35} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for r in results:
        print(f"{r['name']:<35} {r['overall_mae']:>8.4f} {r['weighted_mae']:>8.4f} {r['tier_accuracy']:>7.1%} {r['ms_per_article']:>7.1f}")

    # Save results
    output_path = Path("experiments/model_comparison.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = []
    for r in results:
        sr = {k: v for k, v in r.items()}
        sr["weighted_mae"] = float(sr["weighted_mae"])
        serializable.append(sr)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
