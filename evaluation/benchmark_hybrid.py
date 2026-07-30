"""Speed benchmark: Hybrid (Stage 1 + Stage 2) vs Standard (Stage 2 only).

Run on a machine with GPU and the calibration dataset.

Usage:
    python evaluation/benchmark_hybrid.py --data datasets/calibration/uplifting_v5_production.jsonl
"""
import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

DIMENSION_NAMES = [
    "human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact",
    "evidence_level", "benefit_distribution", "change_durability",
]
DIMENSION_WEIGHTS = {
    "human_wellbeing_impact": 0.25, "social_cohesion_impact": 0.15,
    "justice_rights_impact": 0.10, "evidence_level": 0.20,
    "benefit_distribution": 0.20, "change_durability": 0.10,
}


class MLPProbe(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_sizes=[256, 128], dropout=0.2):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_sizes:
            layers.extend([nn.Linear(prev_dim, h), nn.ReLU(), nn.Dropout(dropout)])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


def load_probe(probe_path, device):
    """Load MLP probe with CPU-safe unpickling."""
    import torch.storage as _ts
    _original_load = _ts._load_from_bytes

    def _cpu_load_from_bytes(b):
        import io
        return torch.load(io.BytesIO(b), map_location="cpu", weights_only=False)

    _ts._load_from_bytes = _cpu_load_from_bytes
    try:
        with open(probe_path, "rb") as f:
            probe_data = pickle.load(f)
    finally:
        _ts._load_from_bytes = _original_load

    config = probe_data["model_config"]
    probe = MLPProbe(input_dim=config["input_dim"], output_dim=config["output_dim"])
    probe.load_state_dict(probe_data["state_dict"])
    probe.to(device)
    probe.eval()
    return probe, probe_data["scaler"], config


def load_stage2_model(repo_id, token, device):
    """Load Qwen model from HuggingFace Hub."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import logging
    logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
    from peft import PeftModel
    from huggingface_hub import hf_hub_download

    config_path = hf_hub_download(repo_id=repo_id, filename="adapter_config.json", token=token)
    with open(config_path) as f:
        adapter_config = json.load(f)
    base_model_name = adapter_config["base_model_name_or_path"]
    print(f"  Base model: {base_model_name}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForSequenceClassification.from_pretrained(
        base_model_name, num_labels=6, problem_type="regression",
    )
    if base_model.config.pad_token_id is None:
        base_model.config.pad_token_id = tokenizer.pad_token_id

    model = PeftModel.from_pretrained(base_model, repo_id, token=token)
    model = model.to(device)
    model.eval()
    return model, tokenizer


def get_hf_token():
    """Get HuggingFace token from cached login or secrets file."""
    # Try cached token
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    if token_path.exists():
        return token_path.read_text().strip()
    # Try secrets.ini
    try:
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read("config/credentials/secrets.ini")
        return cfg.get("api_keys", "huggingface_token", fallback=None)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Benchmark hybrid vs standard inference")
    parser.add_argument("--data", type=Path, required=True, help="Calibration JSONL file")
    # Defaults target solutions v6 — the only deployed filter with BOTH a
    # committed probe and a Hub repo (uplifting v7 is NO_HUB and has no
    # probe dir; the old defaults failed at runtime on either path).
    parser.add_argument("--probe", type=Path, default=Path("filters/solutions/v6/probe/embedding_probe_e5small.pkl"))
    parser.add_argument("--n", type=int, default=1000, help="Number of articles to benchmark")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--threshold", type=float, default=1.225, help="Stage 1 threshold (solutions v6 probe op-point)")
    parser.add_argument("--repo-id", default="jeergrvgreg/solutions-filter-v6", help="HF Hub repo")
    parser.add_argument("--embedding-model", default="intfloat/multilingual-e5-small", help="Embedding model for Stage 1")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load articles (sample to get realistic tier distribution)
    print(f"\nLoading articles from {args.data}...")
    all_articles = []
    with open(args.data) as f:
        for line in f:
            all_articles.append(json.loads(line))

    # Shuffle and sample to get a mix of tiers
    np.random.seed(42)
    indices = np.random.permutation(len(all_articles))[:args.n]
    articles = [all_articles[i] for i in indices]

    tier_counts = {}
    for a in articles:
        t = a.get("production_tier", "unknown")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"Sampled {len(articles)} articles. Tiers: {tier_counts}")

    texts = [f"{a['title']}\n\n{a['content']}" for a in articles]

    # Load Stage 1
    print("\n--- Loading Stage 1 (embedding model + MLP probe) ---")
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    embedder = SentenceTransformer(args.embedding_model, device=device)
    print(f"  Embedding model loaded in {time.time()-t0:.1f}s ({args.embedding_model})")

    probe, scaler, probe_config = load_probe(args.probe, device)
    print(f"  Probe loaded: {probe_config['input_dim']}d -> {probe_config['output_dim']}d")

    # Load Stage 2
    print("\n--- Loading Stage 2 (Qwen2.5-1.5B from Hub) ---")
    hf_token = get_hf_token()
    t0 = time.time()
    model, tokenizer = load_stage2_model(args.repo_id, hf_token, device)
    print(f"  Model loaded in {time.time()-t0:.1f}s")

    # Warmup
    print("\nWarming up...")
    _ = embedder.encode(texts[:2], batch_size=2, show_progress_bar=False, convert_to_numpy=True)
    warmup_inputs = tokenizer(texts[0], max_length=512, padding="max_length", truncation=True, return_tensors="pt")
    warmup_inputs = {k: v.to(device) for k, v in warmup_inputs.items()}
    with torch.no_grad():
        _ = model(**warmup_inputs)
    if device == "cuda":
        torch.cuda.synchronize()

    # ---- Benchmark Stage 1 ----
    print(f"\n--- Stage 1: {len(articles)} articles ---")
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()

    embeddings = embedder.encode(texts, batch_size=args.batch_size, show_progress_bar=False, convert_to_numpy=True)
    embeddings_scaled = scaler.transform(embeddings)
    with torch.no_grad():
        inputs_t = torch.FloatTensor(embeddings_scaled).to(device)
        predictions = probe(inputs_t).cpu().numpy()

    stage1_wavgs = []
    for i in range(len(articles)):
        raw = predictions[i]
        scores = {d: float(max(0, min(10, raw[j]))) for j, d in enumerate(DIMENSION_NAMES)}
        wavg = sum(scores[d] * DIMENSION_WEIGHTS[d] for d in DIMENSION_NAMES)
        stage1_wavgs.append(wavg)

    if device == "cuda":
        torch.cuda.synchronize()
    stage1_time = time.time() - t0

    needs_stage2 = sum(1 for w in stage1_wavgs if w >= args.threshold)
    skip_stage2 = len(articles) - needs_stage2
    print(f"  Time: {stage1_time:.2f}s ({stage1_time/len(articles)*1000:.1f}ms/article)")
    print(f"  Below threshold (skip Stage 2): {skip_stage2} ({skip_stage2/len(articles)*100:.0f}%)")
    print(f"  Above threshold (need Stage 2): {needs_stage2} ({needs_stage2/len(articles)*100:.0f}%)")

    # ---- Benchmark Stage 2: all articles (standard path) ----
    print(f"\n--- Stage 2 (standard): ALL {len(articles)} articles ---")
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()

    for batch_start in range(0, len(articles), args.batch_size):
        batch_end = min(batch_start + args.batch_size, len(articles))
        batch_texts = texts[batch_start:batch_end]
        inputs = tokenizer(batch_texts, max_length=512, padding="max_length", truncation=True, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            _ = outputs.logits.float().cpu().numpy()

    if device == "cuda":
        torch.cuda.synchronize()
    stage2_all_time = time.time() - t0
    print(f"  Time: {stage2_all_time:.2f}s ({stage2_all_time/len(articles)*1000:.1f}ms/article)")

    # ---- Benchmark Stage 2: candidates only (hybrid path) ----
    candidate_texts = [texts[i] for i in range(len(articles)) if stage1_wavgs[i] >= args.threshold]
    print(f"\n--- Stage 2 (hybrid): {len(candidate_texts)} candidates ---")
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.time()

    if candidate_texts:
        for batch_start in range(0, len(candidate_texts), args.batch_size):
            batch_end = min(batch_start + args.batch_size, len(candidate_texts))
            batch_texts = candidate_texts[batch_start:batch_end]
            inputs = tokenizer(batch_texts, max_length=512, padding="max_length", truncation=True, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
                _ = outputs.logits.float().cpu().numpy()

    if device == "cuda":
        torch.cuda.synchronize()
    stage2_cand_time = time.time() - t0

    # ---- Summary ----
    hybrid_total = stage1_time + stage2_cand_time
    standard_total = stage2_all_time
    speedup = standard_total / hybrid_total if hybrid_total > 0 else 0

    print(f"\n{'='*60}")
    print(f"BENCHMARK RESULTS ({len(articles)} articles, threshold={args.threshold})")
    print(f"{'='*60}")
    print(f"Standard (Stage 2 all):  {standard_total:>6.2f}s  ({stage2_all_time/len(articles)*1000:.1f}ms/article)")
    print(f"Hybrid (S1 + S2 cand):   {hybrid_total:>6.2f}s  ({hybrid_total/len(articles)*1000:.1f}ms/article)")
    print(f"Speedup:                 {speedup:.2f}x")
    print(f"")
    print(f"Breakdown:")
    print(f"  Stage 1 (embed+probe): {stage1_time:>6.2f}s  ({stage1_time/len(articles)*1000:.1f}ms/article, all {len(articles)})")
    print(f"  Stage 2 (candidates):  {stage2_cand_time:>6.2f}s  ({needs_stage2} articles)")
    print(f"  Stage 2 skipped:       {skip_stage2} articles ({skip_stage2/len(articles)*100:.0f}%)")
    print(f"")
    print(f"Tier distribution: {tier_counts}")


if __name__ == "__main__":
    main()
