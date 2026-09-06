"""
Training script for LLM Distillery.

Fine-tunes language models (default: Gemma-3-1B) for multi-dimensional regression
on filter-specific datasets.
"""

import argparse
import json
import subprocess
import random
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    get_linear_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType

# Import Gemma-3 compatible model loader
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from filters.common.model_loading import load_base_model_for_seq_cls


def set_seed(seed: int):
    """Set random seed for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # Make PyTorch deterministic (may impact performance slightly)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class FilterDataset(Dataset):
    """PyTorch Dataset for filter training data."""

    def __init__(
        self,
        data_path: Path,
        tokenizer,
        max_length: int = 512,
        prompt: str = None,
        use_head_tail: bool = False,
        head_tokens: int = 256,
        tail_tokens: int = 256,
        sample_weight_scale: float = 0.0,
        dimension_weights: List[float] = None,
    ):
        """
        Args:
            data_path: Path to JSONL file with training examples
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length for tokenization
            prompt: Optional filter prompt to prepend to each example (for instruction tuning)
            use_head_tail: Whether to apply head+tail extraction
            head_tokens: Number of tokens to keep from beginning
            tail_tokens: Number of tokens to keep from end
            sample_weight_scale: Scale for score-based sample weighting (0 = disabled).
                Weight per sample = 1.0 + WA * scale, where WA is the weighted average
                of oracle labels. Higher-scoring articles get more influence on the loss.
            dimension_weights: Weights per dimension for WA computation (from config).
                Required when sample_weight_scale > 0. If None, uses equal weights.
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.prompt = prompt
        self.use_head_tail = use_head_tail
        self.head_tokens = head_tokens
        self.tail_tokens = tail_tokens
        self.sample_weight_scale = sample_weight_scale
        self.examples = []

        # Load examples
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                example = json.loads(line)
                self.examples.append(example)

        # Get dimension count from first example
        if self.examples:
            self.num_dimensions = len(self.examples[0]["labels"])
            self.dimension_names = self.examples[0]["dimension_names"]
        else:
            raise ValueError(f"No examples found in {data_path}")

        # Compute per-sample weights if score-based weighting is enabled
        self.sample_weights = None
        if sample_weight_scale > 0:
            if dimension_weights is None:
                dimension_weights = [1.0 / self.num_dimensions] * self.num_dimensions
            self.sample_weights = []
            for ex in self.examples:
                wa = sum(l * w for l, w in zip(ex["labels"], dimension_weights))
                self.sample_weights.append(1.0 + wa * sample_weight_scale)
            # Log weight distribution
            weights = self.sample_weights
            print(f"  Sample weights: min={min(weights):.2f} max={max(weights):.2f} "
                  f"mean={sum(weights)/len(weights):.2f}")

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict:
        example = self.examples[idx]

        # Combine title and content
        article_text = f"{example['title']}\n\n{example['content']}"

        # Apply head+tail extraction if enabled
        if self.use_head_tail:
            from filters.common.text_preprocessing import extract_head_tail
            article_text = extract_head_tail(
                article_text,
                self.tokenizer,
                self.head_tokens,
                self.tail_tokens,
            )

        # Optionally prepend prompt (instruction tuning mode)
        if self.prompt:
            text = f"{self.prompt}\n\n{article_text}"
        else:
            text = article_text

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        # Convert labels to tensor
        labels = torch.tensor(example["labels"], dtype=torch.float32)

        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": labels,
        }

        if self.sample_weights is not None:
            item["weight"] = torch.tensor(self.sample_weights[idx], dtype=torch.float32)

        return item


class FilterModel(torch.nn.Module):
    """
    Language model adapted for multi-dimensional regression.

    Uses the base model with a custom regression head that outputs
    multiple continuous scores (one per dimension).
    """

    def __init__(self, model_name: str, num_dimensions: int, use_gradient_checkpointing: bool = True, use_fp16: bool = False, use_quantization: bool = False):
        super().__init__()

        # Load base model for sequence classification
        # Note: AutoModelForSequenceClassification expects num_labels, but we'll
        # use it for regression by setting num_labels = num_dimensions
        load_kwargs = {
            "num_labels": num_dimensions,
            "problem_type": "regression",
        }

        # Optional: Configure 8-bit quantization for large models (7B+) on 16GB GPU
        # Reduces memory: 15GB -> 4GB, but adds complexity
        # Default: False for 1.5B model (fits in memory without quantization)
        if use_quantization:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
            )
            load_kwargs["quantization_config"] = quantization_config
            load_kwargs["device_map"] = "auto"
        
        # Only use FP16 if explicitly requested (can cause NaN issues)
        if use_fp16:
            load_kwargs["torch_dtype"] = torch.float16
        else:
            # Force float32 for training stability (some models like Gemma 3
            # default to bfloat16 which causes dtype mismatches during backward)
            load_kwargs["torch_dtype"] = torch.float32

        self.base_model = load_base_model_for_seq_cls(
            model_name,
            **load_kwargs
        )

        # Enable gradient checkpointing to save memory
        if use_gradient_checkpointing:
            self.base_model.gradient_checkpointing_enable()

        # Apply LoRA for memory-efficient training
        lora_config = LoraConfig(
            r=16,  # LoRA rank
            lora_alpha=32,  # LoRA scaling factor
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.SEQ_CLS,
        )
        
        # Freeze base model parameters
        for param in self.base_model.parameters():
            param.requires_grad = False
        
        # Apply LoRA
        self.base_model = get_peft_model(self.base_model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.base_model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in self.base_model.parameters())
        print(f"  LoRA applied: {trainable_params:,} / {all_params:,} parameters ({100 * trainable_params / all_params:.2f}% trainable)")

        self.num_dimensions = num_dimensions
        self.use_fp16 = use_fp16

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )

        return outputs


def _medium_threshold_from_config(config: dict):
    """Lowest non-zero tier boundary declared in config, or None.

    Accepts BOTH schemas and BOTH key spellings actually present in this repo:
    `scoring.tiers` (18 configs) and `scoring.tier_thresholds` (resilience/v1),
    with per-tier `threshold` or `min_score`. Reading only
    `scoring.tiers.medium.threshold` silently returned 4.0 for 8 configs, one of
    which (resilience/v1) really deploys at 4.5.

    Name-agnostic by design: the surfacing tier is called `medium` in most
    filters but `connection` in uplifting v1/v4 and `monitoring` in todo/v1,
    so the LOWEST NON-ZERO boundary is the portable rule -- the same one
    scripts/normalization/fit_normalization.py::_op_point_from_config uses.
    """
    scoring = config.get("scoring") or {}
    tiers = scoring.get("tiers") or scoring.get("tier_thresholds") or {}
    if not isinstance(tiers, dict):
        return None

    def _num(spec):
        v = spec.get("threshold", spec.get("min_score")) if isinstance(spec, dict) else spec
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            return float(v)
        return None

    # A tier literally named `medium` wins. Falling straight to lowest-non-zero
    # is WRONG wherever the bottom tier is itself non-zero: resilience/v1 ships
    # high 6.5 / medium 4.5 / low 2.5, so lowest-non-zero returns 2.5 -- its LOW
    # boundary -- while recall_medium means 4.5. Most filters set low: 0.0, which
    # makes the two rules coincide and hides the difference.
    if "medium" in tiers:
        v = _num(tiers["medium"])
        if v is not None:
            return v

    # No `medium` key: uplifting v1/v4 call the surfacing tier `connection`,
    # todo/v1 calls it `monitoring`. Lowest non-zero is the portable fallback.
    vals = [v for v in (_num(spec) for spec in tiers.values()) if v is not None]
    return min(vals) if vals else None


def _medium_threshold_from_base_scorer(filter_dir: Path):
    """TIER_THRESHOLDS out of base_scorer.py -- the AUTHORITATIVE source.

    Reuses fit_normalization's parser rather than adding another rule: CLAUDE.md
    records that the op-point already lives in four places, and this module must
    not become a fifth that resolves it differently. Loaded by path because
    scripts/ is not a package. Returns None if unavailable -- the caller then
    falls back to config and SAYS SO in the stamped source.
    """
    try:
        import importlib.util
        helper = Path(__file__).resolve().parent.parent / "scripts" / "normalization" / "fit_normalization.py"
        if not helper.exists():
            return None
        spec = importlib.util.spec_from_file_location("_fitnorm_op_point", helper)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._op_point_from_base_scorer(Path(filter_dir))
    except Exception:
        return None


def resolve_medium_threshold(filter_dir: Path, config: dict, cli_override=None):
    """Resolve the MEDIUM+ boundary the needle metrics are measured at.

    Returns (value, source). RAISES when it cannot be resolved -- it must never
    default. A wrong-but-plausible threshold silently changes which checkpoint
    ships and is indistinguishable in metadata from a correct one; the previous
    hardcoded 4.0 was exactly that. ("Make the missing case raise, never return
    a value" -- CLAUDE.md working rules.)

    Precedence: --medium-threshold, then base_scorer.py TIER_THRESHOLDS (the
    runtime source), then config.yaml (DOCUMENTATION -- CLAUDE.md is explicit
    that no scoring code reads it, and it has shipped stale). Drift between the
    last two is reported, and the runtime source wins.
    """
    if cli_override is not None:
        return float(cli_override), "cli --medium-threshold"

    from_code = _medium_threshold_from_base_scorer(filter_dir)
    from_config = _medium_threshold_from_config(config)

    if from_code is not None:
        if from_config is not None and from_code != from_config:
            print(f"  WARNING: op-point drift — base_scorer.py TIER_THRESHOLDS says "
                  f"{from_code}, config.yaml says {from_config}. TIER_THRESHOLDS is the "
                  f"runtime source and wins; one of them is a lie, fix it.")
        return from_code, "base_scorer.py TIER_THRESHOLDS"

    if from_config is not None:
        return from_config, "config.yaml (base_scorer.py absent — NOT the runtime source)"

    raise RuntimeError(
        f"Cannot resolve the MEDIUM+ threshold for {filter_dir}. Looked for "
        f"TIER_THRESHOLDS in base_scorer.py and for scoring.tiers / "
        f"scoring.tier_thresholds (threshold or min_score) in config.yaml, and "
        f"found neither. Refusing to default to 4.0 — it decides which checkpoint "
        f"ships. Pass --medium-threshold explicitly."
    )


def resolve_git_provenance(allow_missing: bool = False) -> dict:
    """Which commit is training this checkpoint, and is that commit durable?

    ⛔ THE DEFECT THIS EXISTS FOR. `human_thriving v8`'s shipped adapter was built
    by a tree that became `1878e7b` via `git commit --amend`, so the sha that
    actually trained it (`0697f5a`) is dangling and will not survive `git gc`.
    Nothing recorded that, because `training_metadata.json` recorded no commit at
    all — the run's provenance lived only in a session note, and a session note
    cannot be checked. Recording the sha here is what lets
    `scripts/verification/check_training_provenance.py` notice later that it has
    become unreachable.

    `dirty` is part of the claim: a sha plus uncommitted edits does not identify a
    tree, and that is the same failure wearing a valid-looking commit id.

    RAISES when it cannot establish provenance — a checkpoint whose origin is
    unknown is exactly what we are trying to stop shipping. `--allow-missing-git-
    provenance` is the deliberate opt-out, and it is recorded IN the metadata so
    the checker still sees it.
    """
    repo = Path(__file__).resolve().parent.parent

    def _git(*a):
        return subprocess.run(("git", "-C", str(repo)) + a, capture_output=True,
                              text=True, timeout=30)

    probe = _git("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        reason = (f"{repo} is not a git work tree — the training box holds a copy, "
                  f"not a checkout, so no commit identifies this run")
        if not allow_missing:
            raise RuntimeError(
                f"Refusing to train without provenance: {reason}. Make the box a "
                f"checkout (git init + fetch + checkout), or pass "
                f"--allow-missing-git-provenance to record the gap explicitly."
            )
        return {"git_commit": None, "git_dirty": None,
                "git_provenance": f"UNAVAILABLE: {reason}"}

    sha = _git("rev-parse", "HEAD").stdout.strip()
    # -uno: untracked files (staged datasets, venvs, scratch scripts) are not the
    # tree that trains. Tracked modifications are.
    dirty_out = _git("status", "--porcelain", "-uno").stdout.strip()
    dirty = bool(dirty_out)
    branches = [b.strip().lstrip("* ").strip()
                for b in _git("branch", "--contains", sha).stdout.splitlines()
                if b.strip()]

    if dirty and not allow_missing:
        raise RuntimeError(
            f"Refusing to train from a dirty tree: {len(dirty_out.splitlines())} "
            f"tracked file(s) differ from {sha[:12]}, so that sha does not identify "
            f"what is about to train. Commit or stash them (explicit paths only), "
            f"or pass --allow-missing-git-provenance.\n{dirty_out[:2000]}"
        )
    if not branches and not allow_missing:
        raise RuntimeError(
            f"Refusing to train from a commit on no branch: {sha[:12]} is reachable "
            f"from no branch, so an amend or a gc can erase it — the exact shape "
            f"that orphaned human_thriving v8's first checkpoint. Put it on a "
            f"branch, or pass --allow-missing-git-provenance."
        )
    return {
        "git_commit": sha,
        "git_dirty": dirty,
        "git_branches_at_train_time": branches,
        "git_provenance": ("recorded" if (branches and not dirty)
                           else "recorded WITH A GAP — see git_dirty/branches"),
    }


def compute_metrics(predictions: torch.Tensor, labels: torch.Tensor, dimension_names: List[str], dimension_weights: List[float] = None, medium_threshold: float = 4.0) -> Dict:
    """
    Compute evaluation metrics per dimension.

    Args:
        predictions: Model predictions (batch_size, num_dimensions)
        labels: Ground truth labels (batch_size, num_dimensions)
        dimension_names: Names of dimensions
        dimension_weights: Per-dimension weights from config, used for the
            weighted average the needle metrics are computed on. When None, the
            needle metrics are NOT emitted at all and checkpoint selection falls
            back to aggregate MAE.
        medium_threshold: MEDIUM+ boundary for recall_medium / fn_rate_medium.
            Resolved per-filter by main(); the 4.0 default is not a house value.

    Returns:
        Dictionary of metrics
    """
    metrics = {}

    # Overall metrics
    mae = torch.mean(torch.abs(predictions - labels)).item()
    rmse = torch.sqrt(torch.mean((predictions - labels) ** 2)).item()

    metrics["mae"] = mae
    metrics["rmse"] = rmse

    # Per-dimension metrics
    for i, dim_name in enumerate(dimension_names):
        dim_predictions = predictions[:, i]
        dim_labels = labels[:, i]

        dim_mae = torch.mean(torch.abs(dim_predictions - dim_labels)).item()
        dim_rmse = torch.sqrt(torch.mean((dim_predictions - dim_labels) ** 2)).item()

        metrics[f"{dim_name}_mae"] = dim_mae
        metrics[f"{dim_name}_rmse"] = dim_rmse

    # --- Needle-in-haystack RANKING metrics (SETTLED: docs/agents/
    # filter-development-guide.md Issue 4, verified nature_recovery v1->v2).
    # Aggregate MAE is misleading on an ~85% floor (a floor-predictor wins it),
    # so these are the metrics that judge model quality. Computed on the
    # weighted-average score (per-dim weights from config).
    if dimension_weights is not None:
        import math
        w = torch.tensor(dimension_weights, dtype=predictions.dtype)
        pred_wa = (predictions * w).sum(dim=1)
        true_wa = (labels * w).sum(dim=1)
        n = int(pred_wa.shape[0])
        # Medium/surfacing boundary. Read from the filter's config by main() --
        # it is NOT 4.0 for every filter (solutions 2.25, nature_recovery v4 3.75,
        # investment_risk v6 4.25, uplifting v7 / human_thriving v8 4.5). main()
        # resolves it and RAISES rather than defaulting; the 4.0 here is only for
        # a caller that passes none, of which the repo currently has zero.
        MEDIUM = medium_threshold

        # Recall@k: overlap of top-k predicted with top-k true, divided by k
        # ("finds X% of the top-k articles" — v1/STATUS.md definition).
        for k in (10, 20, 50):
            # SKIP, never clamp. With kk = min(k, n) and n <= k the top-k
            # predicted and top-k true sets are both "every row", so recall_at_k
            # is identically 1.0 however bad the model is -- and with the strict
            # `>` in checkpoint selection that pins epoch 1 forever. Verified:
            # deliberately poor predictions score 1.000 at n=8/15/20, 0.950 at
            # n=21. A metric that cannot fail must not be offered to selection.
            if n <= k:
                continue
            kk = k
            top_pred = set(torch.topk(pred_wa, kk).indices.tolist())
            top_true = set(torch.topk(true_wa, kk).indices.tolist())
            metrics[f"recall_at_{k}"] = len(top_pred & top_true) / kk

        # NDCG@k: true_wa as graded relevance, ranked by predicted_wa
        def _ndcg(k):
            kk = min(k, n)
            if kk == 0:
                return 0.0
            order = torch.topk(pred_wa, kk).indices.tolist()
            dcg = sum(true_wa[idx].item() / math.log2(r + 2) for r, idx in enumerate(order))
            ideal = torch.topk(true_wa, kk).values.tolist()
            idcg = sum(g / math.log2(r + 2) for r, g in enumerate(ideal))
            return dcg / idcg if idcg > 0 else 0.0
        metrics["ndcg_at_10"] = _ndcg(10)
        metrics["ndcg_at_20"] = _ndcg(20)

        # FN-rate / recall on MEDIUM+ — true positives predicted below threshold
        # ("misses X% of positives" — the recall-side product metric).
        pos = true_wa >= MEDIUM
        n_pos = int(pos.sum().item())
        if n_pos > 0:
            fn = int(((pred_wa < MEDIUM) & pos).sum().item())
            metrics["fn_rate_medium"] = fn / n_pos
            metrics["recall_medium"] = 1.0 - fn / n_pos
            metrics["n_positives"] = n_pos

        # Per-band MAE on the weighted average (diagnostic; H4 top-band sparsity)
        for lo, hi in ((0, 2), (2, 4), (4, 6), (6, 8), (8, 10.01)):
            m = (true_wa >= lo) & (true_wa < hi)
            cnt = int(m.sum().item())
            if cnt > 0:
                metrics[f"mae_band_{lo}_{int(hi)}"] = torch.mean(torch.abs(pred_wa[m] - true_wa[m])).item()
                metrics[f"n_band_{lo}_{int(hi)}"] = cnt

    return metrics


def train_epoch(
    model,
    dataloader,
    optimizer,
    scheduler,
    device,
    dimension_names: List[str],
    use_sample_weights: bool = False,
    dimension_weights: List[float] = None,
    medium_threshold: float = 4.0,
):
    """Train for one epoch."""
    model.train()

    total_loss = 0
    all_predictions = []
    all_labels = []

    use_weighted_loss = use_sample_weights

    progress = tqdm(dataloader, desc="Training")
    for batch in progress:
        # Move to device
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        if use_weighted_loss:
            # Compute weighted MSE externally — don't pass labels to model
            weights = batch["weight"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = outputs.logits
            per_sample_mse = torch.mean((predictions - labels) ** 2, dim=1)
            loss = torch.mean(per_sample_mse * weights)
        else:
            # Use model's internal MSE loss (default, backwards compatible)
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            predictions = outputs.logits

        # Check for NaN
        if torch.isnan(loss):
            print(f"\n[WARNING] NaN loss detected at step {len(all_predictions)}, skipping batch")
            continue

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Clip gradients to prevent explosion with FP16
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()
        scheduler.step()

        # Track metrics
        total_loss += loss.item()
        all_predictions.append(predictions.detach().cpu())
        all_labels.append(labels.detach().cpu())

        progress.set_postfix({"loss": loss.item()})

    # Compute epoch metrics
    avg_loss = total_loss / len(dataloader)
    all_predictions = torch.cat(all_predictions, dim=0)
    all_labels = torch.cat(all_labels, dim=0)
    metrics = compute_metrics(all_predictions, all_labels, dimension_names, dimension_weights, medium_threshold)
    metrics["loss"] = avg_loss

    return metrics


def evaluate(model, dataloader, device, dimension_names: List[str], dimension_weights: List[float] = None, medium_threshold: float = 4.0):
    """Evaluate model on validation/test set."""
    model.eval()

    total_loss = 0
    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            # Move to device
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            loss = outputs.loss
            predictions = outputs.logits

            # Track metrics
            total_loss += loss.item()
            all_predictions.append(predictions.cpu())
            all_labels.append(labels.cpu())

    # Compute metrics
    avg_loss = total_loss / len(dataloader)
    all_predictions = torch.cat(all_predictions, dim=0)
    all_labels = torch.cat(all_labels, dim=0)
    metrics = compute_metrics(all_predictions, all_labels, dimension_names, dimension_weights, medium_threshold)
    metrics["loss"] = avg_loss

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train filter model")
    parser.add_argument(
        "--filter",
        type=Path,
        required=True,
        help="Path to filter directory (e.g., filters/uplifting/v1)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to prepared dataset directory (with train.jsonl, val.jsonl, test.jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for trained model (default: saves to filter directory)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="google/gemma-3-1b-pt",
        help="Base model name (default: google/gemma-3-1b-pt)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Training batch size (default: 8)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate (default: 2e-5)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Maximum sequence length (default: 512)",
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=500,
        help="Number of warmup steps (default: 500)",
    )
    parser.add_argument(
        "--resume-from",
        type=Path,
        default=None,
        help="Path to checkpoint directory to resume training from (e.g., filters/uplifting/v1)",
    )
    parser.add_argument(
        "--include-prompt",
        action="store_true",
        help="Include filter prompt in training (instruction tuning mode). Prepends prompt-compressed.md to each article.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--use-head-tail",
        action="store_true",
        help="Use head+tail extraction: keep first N + last M tokens. "
             "Matches inference preprocessing when config.yaml has head_tail.enabled=true",
    )
    parser.add_argument(
        "--head-tokens",
        type=int,
        default=256,
        help="Number of tokens to keep from beginning (default: 256)",
    )
    parser.add_argument(
        "--tail-tokens",
        type=int,
        default=256,
        help="Number of tokens to keep from end (default: 256)",
    )
    parser.add_argument(
        "--sample-weight-scale",
        type=float,
        default=0.0,
        help="Scale for score-based sample weighting (default: 0 = disabled). "
             "Weight = 1 + WA * scale. Use 2-3 for needle-in-haystack filters "
             "with extreme class imbalance (e.g. nature_recovery).",
    )
    parser.add_argument(
        "--medium-threshold",
        type=float,
        default=None,
        help="MEDIUM+ boundary for the needle metrics. Default: base_scorer.py "
             "TIER_THRESHOLDS, else config.yaml tiers. Required when neither resolves.",
    )
    parser.add_argument(
        "--allow-missing-git-provenance",
        action="store_true",
        help=("Train even though the commit that would identify this run cannot be "
              "established (not a checkout, dirty tree, or a commit on no branch). "
              "The gap is written into training_metadata.json, where "
              "check_training_provenance.py will report it."),
    )
    parser.add_argument(
        "--select-metric",
        choices=["recall_at_20", "recall_medium"],
        default="recall_at_20",
        help="Validation metric to select the best checkpoint on (both maximized). "
             "recall_at_20 = top-20 ranking precision (default). recall_medium = "
             "recall on MEDIUM+ positives (1 - FN-rate); prefer this when the "
             "deploy gate penalizes missing/over-demoting positives (needle filters "
             "where not-missing-positives matters more than top-20 precision).",
    )

    args = parser.parse_args()

    # Normalize paths: strip trailing "model" component to prevent double nesting.
    # The script always appends /model when saving/loading, so --output-dir and
    # --resume-from should point to the filter version dir (e.g. filters/name/v1).
    if args.output_dir is not None and args.output_dir.name == "model":
        args.output_dir = args.output_dir.parent
        print(f"Note: stripped trailing /model from --output-dir; using {args.output_dir}")
    if args.resume_from is not None and args.resume_from.name == "model":
        args.resume_from = args.resume_from.parent
        print(f"Note: stripped trailing /model from --resume-from; using {args.resume_from}")

    # ⛔ BEFORE ANYTHING EXPENSIVE. A provenance gap discovered after a 100-minute
    # run is a 100-minute run you cannot cite, so this refuses up front.
    git_provenance = resolve_git_provenance(
        allow_missing=args.allow_missing_git_provenance)
    if git_provenance["git_commit"]:
        print(f"Training under commit {git_provenance['git_commit'][:12]} "
              f"(dirty={git_provenance['git_dirty']}, "
              f"branches={git_provenance['git_branches_at_train_time']})")
    else:
        print(f"WARNING: {git_provenance['git_provenance']}")

    # Set random seed for reproducibility
    set_seed(args.seed)
    print(f"Random seed set to: {args.seed}")

    # Load filter config
    print(f"Loading filter config from {args.filter}")
    config_path = args.filter / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    filter_name = config["filter"]["name"]
    dimension_names = list(config["scoring"]["dimensions"].keys())
    num_dimensions = len(dimension_names)

    print(f"Filter: {filter_name}")
    print(f"Dimensions ({num_dimensions}): {dimension_names}")

    # Set output directory (default: save to filter directory)
    if args.output_dir is None:
        args.output_dir = args.filter
        print(f"Output directory: {args.output_dir} (filter directory)")

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nUsing device: {device}")

    # Load tokenizer
    print(f"\nLoading tokenizer: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    # Set padding token if not set (required for batch processing)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        print(f"  Set pad_token to eos_token: {tokenizer.eos_token}")

    # Optionally load prompt for instruction tuning
    prompt = None
    if args.include_prompt:
        prompt_path = args.filter / "prompt-compressed.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read().strip()

        print(f"\nInstruction tuning mode enabled")
        print(f"  Loaded prompt from: {prompt_path}")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"  Warning: Longer sequences may require --max-length adjustment")

    # Load datasets
    print(f"\nLoading datasets from {args.data_dir}")
    if args.use_head_tail:
        print(f"Head+tail extraction enabled: {args.head_tokens} + {args.tail_tokens} tokens")

    # Dimension weights, ALWAYS built: compute_metrics needs them for the needle
    # metrics (recall_at_k / recall_medium / NDCG), and --sample-weight-scale needs
    # them only when > 0. Gating this on the scale left val_metrics without
    # recall_at_20, so --select-metric fell through to aggregate MAE -- the metric
    # ADR-023 forbids ranking on, on corpora that are ~85-95% floor.
    dimension_weights_list = [
        config["scoring"]["dimensions"][dim].get("weight", 1.0 / len(dimension_names))
        for dim in dimension_names
    ]
    if args.sample_weight_scale > 0:
        print(f"Sample weighting enabled: scale={args.sample_weight_scale}")

    # The surfacing boundary is per-filter, not a constant (see compute_metrics).
    medium_threshold, medium_threshold_source = resolve_medium_threshold(
        args.filter, config, args.medium_threshold
    )
    print(f"Needle metrics at MEDIUM+ threshold: {medium_threshold} "
          f"(source: {medium_threshold_source})")

    train_dataset = FilterDataset(
        args.data_dir / "train.jsonl",
        tokenizer,
        max_length=args.max_length,
        prompt=prompt,
        use_head_tail=args.use_head_tail,
        head_tokens=args.head_tokens,
        tail_tokens=args.tail_tokens,
        sample_weight_scale=args.sample_weight_scale,
        dimension_weights=dimension_weights_list,
    )
    val_dataset = FilterDataset(
        args.data_dir / "val.jsonl",
        tokenizer,
        max_length=args.max_length,
        prompt=prompt,
        use_head_tail=args.use_head_tail,
        head_tokens=args.head_tokens,
        tail_tokens=args.tail_tokens,
    )

    print(f"Train: {len(train_dataset)} examples")
    print(f"Val: {len(val_dataset)} examples")

    # Create dataloaders
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_dataloader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
    )

    # Load or initialize model
    start_epoch = 0
    selection_metric_available = False  # set True once a needle metric is actually computed
    # Provenance OF THE CHECKPOINT ON DISK. None/False until an epoch actually
    # saves one; a run that improves on nothing must not claim to have chosen it.
    checkpoint_saved = False
    saved_select_metric = None
    saved_select_metric_available = False
    saved_medium_threshold = None
    saved_medium_threshold_source = None
    if args.resume_from:
        print(f"\nResuming from checkpoint: {args.resume_from}")

        # Load model from checkpoint
        checkpoint_model_path = args.resume_from / "model"
        if not checkpoint_model_path.exists():
            raise ValueError(f"Checkpoint model not found at {checkpoint_model_path}")

        # Load metadata to get base model name
        metadata_path = args.resume_from / "training_metadata.json"
        if not metadata_path.exists():
            raise ValueError(f"training_metadata.json not found at {args.resume_from}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            base_model_name = metadata["model_name"]

        print(f"  Base model: {base_model_name}")

        # Load base model (handles Gemma-3 compatibility)
        # Force float32 for training stability (match initial training path)
        base_model = load_base_model_for_seq_cls(
            base_model_name,
            num_labels=num_dimensions,
            problem_type="regression",
            torch_dtype=torch.float32,
        )

        # Enable gradient checkpointing to save memory (matches initial training)
        base_model.gradient_checkpointing_enable()

        # Load PEFT adapter (already trained LoRA weights)
        from peft import PeftModel
        model_with_adapter = PeftModel.from_pretrained(base_model, checkpoint_model_path)

        # Enable training on LoRA parameters
        for name, param in model_with_adapter.named_parameters():
            if "lora_" in name or "modules_to_save" in name:
                param.requires_grad = True

        trainable = sum(p.numel() for p in model_with_adapter.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model_with_adapter.parameters())
        print(f"  Resumed LoRA: {trainable:,} / {total:,} parameters ({100 * trainable / total:.2f}% trainable)")

        # Wrap in simple container to match interface
        class ResumedModel(torch.nn.Module):
            def __init__(self, peft_model):
                super().__init__()
                self.base_model = peft_model
                self.num_dimensions = num_dimensions
                self.use_fp16 = False

            def forward(self, input_ids, attention_mask, labels=None):
                return self.base_model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

        model = ResumedModel(model_with_adapter)
        print(f"  Loaded PEFT model from checkpoint (no double LoRA)")

        # Load training history to determine start epoch
        history_path = args.resume_from / "training_history.json"
        if history_path.exists():
            with open(history_path, "r", encoding="utf-8") as f:
                training_history = json.load(f)
            start_epoch = training_history[-1]["epoch"]
            best_val_mae = training_history[-1]["val"]["mae"]
            # max(), not [-1]: seeding from the LAST epoch lets a resumed run
            # overwrite a better checkpoint. nature_recovery v4's own history runs
            # recall_medium 0.0175 / 0.8246 / 0.7368, so [-1] seeds 0.7368 and any
            # epoch scoring 0.75 counts as "improved". Before the metrics fix this
            # line was reachable for one filter; now every run writes them.
            best_val_recall = max(
                (h["val"].get(args.select_metric, -1.0) for h in training_history),
                default=-1.0,
            )
            saved_val_mae = best_val_mae  # approx on resume; overwritten on next save
            print(f"  Resuming from epoch {start_epoch} (best val MAE: {best_val_mae:.4f})")
        else:
            training_history = []
            print(f"  Warning: No training history found, starting fresh")
    else:
        print(f"\nInitializing model: {args.model_name}")
        # Use FP32 by default for stability (FP16 causes NaN issues)
        model = FilterModel(args.model_name, num_dimensions, use_gradient_checkpointing=True, use_fp16=False)
        training_history = []
        best_val_mae = float("inf")
        best_val_recall = -1.0
        saved_val_mae = float("inf")  # val MAE of the checkpoint actually on disk

    # Set pad_token_id in model config to match tokenizer
    if model.base_model.config.pad_token_id is None and tokenizer.pad_token_id is not None:
        model.base_model.config.pad_token_id = tokenizer.pad_token_id
        print(f"  Set model pad_token_id to {tokenizer.pad_token_id}")

    model.to(device)

    # Clear CUDA cache before training
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Count parameters
    num_params = sum(p.numel() for p in model.parameters())
    num_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parameters: {num_params:,} ({num_trainable:,} trainable)")

    # Setup optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    total_steps = len(train_dataloader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=total_steps,
    )

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Training loop
    total_epochs = start_epoch + args.epochs
    print(f"\nStarting training from epoch {start_epoch + 1} to {total_epochs}")

    for epoch in range(start_epoch, total_epochs):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch + 1}/{total_epochs}")
        print(f"{'='*60}")

        # Train
        train_metrics = train_epoch(
            model,
            train_dataloader,
            optimizer,
            scheduler,
            device,
            dimension_names,
            use_sample_weights=args.sample_weight_scale > 0,
            dimension_weights=dimension_weights_list,
            medium_threshold=medium_threshold,
        )

        print(f"\nTraining metrics:")
        print(f"  Loss: {train_metrics['loss']:.4f}")
        print(f"  MAE: {train_metrics['mae']:.4f}")
        print(f"  RMSE: {train_metrics['rmse']:.4f}")

        # Validate
        val_metrics = evaluate(model, val_dataloader, device, dimension_names, dimension_weights_list, medium_threshold)

        print(f"\nValidation metrics:")
        print(f"  Loss: {val_metrics['loss']:.4f}")
        print(f"  MAE: {val_metrics['mae']:.4f}  (aggregate — misleading on a needle filter)")
        print(f"  RMSE: {val_metrics['rmse']:.4f}")
        if "recall_at_20" in val_metrics:
            print(f"  Recall@20: {val_metrics['recall_at_20']:.3f} | Recall@10: {val_metrics.get('recall_at_10', float('nan')):.3f} "
                  f"| NDCG@10: {val_metrics.get('ndcg_at_10', float('nan')):.3f}")
            print(f"  FN-rate MEDIUM+: {val_metrics.get('fn_rate_medium', float('nan')):.3f} "
                  f"(recall {val_metrics.get('recall_medium', float('nan')):.3f} on {val_metrics.get('n_positives', 0)} positives)")

        # Save metrics
        epoch_history = {
            "epoch": epoch + 1,
            "train": train_metrics,
            "val": val_metrics,
        }
        training_history.append(epoch_history)

        # Checkpoint selection: a needle metric (--select-metric) when available,
        # NOT aggregate MAE — a floor-predictor wins MAE on an ~85% floor (settled:
        # filter-development-guide Issue 4). recall_at_20 = top-20 ranking precision;
        # recall_medium = recall on MEDIUM+ (1 - FN-rate), preferred when the deploy
        # gate penalizes over-demoting/missing positives.
        #
        # The MAE fallback below is NOT dead, and its live cause is not the one
        # this comment used to name ("no dimension weights" — impossible since the
        # weights became unconditional). It fires when --select-metric names a
        # metric compute_metrics did not emit: recall_medium is set only under
        # n_pos > 0, so a val split with zero MEDIUM+ positives silently selects on
        # aggregate MAE — the exact defect this plumbing exists to remove.
        val_recall = val_metrics.get(args.select_metric)
        if val_recall is not None:
            selection_metric_available = True
        if val_metrics["mae"] < best_val_mae:
            best_val_mae = val_metrics["mae"]
        if val_recall is not None:
            improved = val_recall > best_val_recall
        else:
            improved = val_metrics["mae"] <= best_val_mae
        if improved:
            if val_recall is not None:
                best_val_recall = val_recall
                print(f"\n✓ New best checkpoint ({args.select_metric}={val_recall:.3f}, "
                      f"Recall@20={val_metrics.get('recall_at_20', float('nan')):.3f}, "
                      f"recall_medium={val_metrics.get('recall_medium', float('nan')):.3f}, "
                      f"MAE={val_metrics['mae']:.4f})")
            else:
                print(f"\n✓ New best checkpoint (MAE={val_metrics['mae']:.4f})")

            # Save model
            args.output_dir.mkdir(parents=True, exist_ok=True)
            model_path = args.output_dir / "model"
            model.base_model.save_pretrained(model_path)
            tokenizer.save_pretrained(model_path)
            # The val MAE that BELONGS to the checkpoint now on disk. When selecting
            # on a recall metric the saved epoch is NOT the global-min-MAE epoch, so
            # metadata must report this, not best_val_mae, or the model card cites an
            # MAE the deployed model never achieved (found 2026-07-10, F3).
            saved_val_mae = val_metrics["mae"]
            # Captured HERE, beside saved_val_mae, for the same reason: these
            # describe the checkpoint now on disk, not this invocation. Written
            # unconditionally they would stamp "selected on recall_medium" onto a
            # model an earlier MAE-selected run wrote, whenever a resume improves
            # on nothing -- partially re-breaking F3.
            saved_select_metric = args.select_metric
            saved_select_metric_available = selection_metric_available
            saved_medium_threshold = medium_threshold
            saved_medium_threshold_source = medium_threshold_source
            checkpoint_saved = True

            print(f"  Model saved to: {model_path}")

    # Save training history
    print(f"\n{'='*60}")
    print(f"Training complete!")
    print(f"Deployed checkpoint val MAE: {saved_val_mae:.4f} "
          f"(min val MAE any epoch: {best_val_mae:.4f})")

    history_path = args.output_dir / "training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2)

    print(f"Training history saved to: {history_path}")

    # Save training metadata
    metadata = {
        "filter_name": filter_name,
        "filter_version": config["filter"]["version"],
        "dimension_names": dimension_names,
        "num_dimensions": num_dimensions,
        "model_name": args.model_name,
        "num_parameters": num_params,
        "num_trainable_parameters": num_trainable,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "warmup_steps": args.warmup_steps,
        "train_examples": len(train_dataset),
        "val_examples": len(val_dataset),
        "best_val_mae": saved_val_mae,          # val MAE of the deployed checkpoint (F3, 2026-07-10)
        "min_val_mae_observed": best_val_mae,    # global min across epochs (may be a different epoch)
        "include_prompt": args.include_prompt,
        "training_mode": "instruction_tuning" if args.include_prompt else "knowledge_distillation",
        "use_head_tail": args.use_head_tail,
        "head_tokens": args.head_tokens if args.use_head_tail else None,
        "tail_tokens": args.tail_tokens if args.use_head_tail else None,
        "sample_weight_scale": args.sample_weight_scale,
        # Run-scoped: what was ASKED of this invocation.
        "requested_select_metric": args.select_metric,
        "requested_medium_threshold": medium_threshold,
        "requested_medium_threshold_source": medium_threshold_source,
        # Checkpoint-scoped: what actually chose the model/ on disk. All None/False
        # when this run saved nothing, in which case model/ is an EARLIER run's and
        # these fields deliberately do not describe it.
        "checkpoint_saved": checkpoint_saved,
        "select_metric": saved_select_metric,
        "select_metric_available": saved_select_metric_available,
        "medium_threshold": saved_medium_threshold,
        "medium_threshold_source": saved_medium_threshold_source,
        # Provenance: which commit trained this, and was it durable at the time.
        # `check_training_provenance.py` re-checks reachability later, which is
        # when an amend or a gc has had a chance to orphan it.
        **git_provenance,
    }

    metadata_path = args.output_dir / "training_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Training metadata saved to: {metadata_path}")

    # Print next steps reminder
    print(f"\n{'='*60}")
    print(f"NEXT STEPS:")
    print(f"{'='*60}")
    print(f"1. Review training results in {args.output_dir}/")
    print(f"2. Run Model Evaluation Agent (see training/README.md)")
    print(f"3. Review report: {args.output_dir}/model_evaluation.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
