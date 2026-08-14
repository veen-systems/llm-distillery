"""
Validate DeepSeek as an oracle for cultural_discovery v5 by comparing its
dimensional scores against Gemini Flash 2.5 on the same articles + same prompt.

Picks N articles already scored under v5 prompt by Gemini, re-scores them with
DeepSeek using the identical prompt, computes per-dimension correlation.

Decision rule (per oracle-selection investigation 2026-05-30):
  - All 5 dims Pearson r > 0.90  → switch to DeepSeek for 8K re-score (saves ~$13)
  - Any dim r < 0.85             → stay with Gemini Batch
  - Between                      → judgment call

Usage:
    PYTHONPATH=. python scripts/validate_deepseek_oracle.py
    PYTHONPATH=. python scripts/validate_deepseek_oracle.py --n-sample 50 --model deepseek-chat

Requires:
    deepseek_api_key in [api_keys] of config/credentials/secrets.ini
    OR DEEPSEEK_API_KEY environment variable

Cost: ~$0.01-0.05 for 50 articles via the DeepSeek direct API (auto-cached prompt).
      Stale-cost warning: that figure predates the 2026-08-16 peak/off-peak repricing,
      under which every tier bills above the old flat rate — see
      memory/oracle-pricing-scheduling.md before quoting it.

"""

import argparse
import configparser
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# Reuse the existing sanitization + json-repair helpers so the prompt going to
# DeepSeek matches what Gemini saw byte-for-byte.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ground_truth.text_cleaning import (
    clean_article as clean_article_comprehensive,
    sanitize_text_comprehensive,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SECRETS_INI = PROJECT_ROOT / "config" / "credentials" / "secrets.ini"
V5_PROMPT_PATH = PROJECT_ROOT / "filters" / "cultural_discovery" / "v5" / "prompt-compressed.md"
MERGED_JSONL = PROJECT_ROOT / "datasets" / "scored" / "cultural_discovery_v5_merged.jsonl"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DIMENSIONS = [
    "discovery_novelty",
    "heritage_significance",
    "cross_cultural_connection",
    "human_resonance",
    "evidence_quality",
]
PROMPT_PLACEHOLDER = "[Paste the summary of the article here]"


def get_deepseek_key():
    env_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_key:
        return env_key.strip()
    if SECRETS_INI.exists():
        cp = configparser.ConfigParser()
        cp.read(SECRETS_INI, encoding="utf-8")
        if "api_keys" in cp and "deepseek_api_key" in cp["api_keys"]:
            key = cp["api_keys"]["deepseek_api_key"].strip()
            if key:
                return key
    raise SystemExit(
        "ERROR: DeepSeek API key not found.\n"
        "  Option 1: add to config/credentials/secrets.ini under [api_keys]:\n"
        "             deepseek_api_key = sk-xxxxxxxx\n"
        "  Option 2: set environment variable DEEPSEEK_API_KEY=sk-xxxxxxxx\n"
        "  Get a key at: https://platform.deepseek.com/api_keys"
    )


def smart_compress(content: str, max_words: int = 800) -> str:
    """Replicates GenericBatchScorer._smart_compress_content exactly."""
    words = content.split()
    if len(words) <= max_words:
        return content
    start_words = int(max_words * 0.7)
    end_words = int(max_words * 0.3)
    beginning = " ".join(words[:start_words])
    ending = " ".join(words[-end_words:])
    return f"{beginning}\n\n[...content compressed...]\n\n{ending}"


def build_prompt(prompt_template: str, article: dict) -> str:
    """Replicates GenericBatchScorer.build_prompt for the modern (placeholder) format."""
    article = clean_article_comprehensive(article)
    content = article.get("content", "")
    compressed = smart_compress(content, max_words=800)
    title = sanitize_text_comprehensive(article.get("title", "N/A"))
    source = sanitize_text_comprehensive(article.get("source", "N/A"))
    published = sanitize_text_comprehensive(article.get("published_date", "N/A"))
    text = sanitize_text_comprehensive(compressed)
    article_summary = (
        f"Title: {title}\nSource: {source}\nPublished: {published}\n\n{text}"
    )
    return prompt_template.replace(PROMPT_PLACEHOLDER, article_summary)


def load_v5_scored_articles():
    """Articles scored under v5 prompt (filter_version 5.0-draft) by Gemini."""
    articles = []
    with open(MERGED_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            af = r.get("cultural_discovery_analysis", {})
            if af.get("filter_version") == "5.0-draft":
                articles.append(r)
    return articles


def stratified_sample(articles, n_target: int, seed: int = 42):
    """Sample stratified by content_type with floor of 2 per type."""
    random.seed(seed)
    by_type = defaultdict(list)
    for r in articles:
        ct = r["cultural_discovery_analysis"].get("content_type", "unknown")
        by_type[ct].append(r)
    total = sum(len(v) for v in by_type.values())
    sample = []
    for ct, items in by_type.items():
        share = max(2, int(round(n_target * len(items) / total)))
        share = min(share, len(items))
        random.shuffle(items)
        sample.extend(items[:share])
    if len(sample) > n_target:
        random.shuffle(sample)
        sample = sample[:n_target]
    return sample


def call_deepseek(api_key: str, model: str, prompt: str, max_retries: int = 3):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=body, timeout=120)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (401, 403):
                # auth error — fail fast, don't burn 50 calls
                raise SystemExit(
                    f"ERROR: DeepSeek auth failed (HTTP {resp.status_code}): {resp.text[:300]}"
                )
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(2 ** attempt)
                continue
            return {"error": f"HTTP {resp.status_code}: {resp.text[:500]}"}
        except requests.exceptions.RequestException as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    return {"error": f"Max retries exceeded: {last_err}"}


def extract_dim_score(value):
    """Extract score from nested {score, evidence} dict or flat float."""
    if isinstance(value, dict):
        return value.get("score")
    return value


def parse_deepseek_response(resp):
    if "error" in resp:
        return {"error": resp["error"]}
    try:
        text = resp["choices"][0]["message"]["content"]
        parsed = json.loads(text)
        out = {dim: extract_dim_score(parsed.get(dim)) for dim in DIMENSIONS}
        out["content_type"] = parsed.get("content_type")
        out["_usage"] = resp.get("usage", {})
        return out
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raw = ""
        try:
            raw = resp["choices"][0]["message"]["content"][:300]
        except (KeyError, IndexError):
            pass
        return {"error": f"Parse failed: {e}", "raw_text": raw}


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    dy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def spearman(xs, ys):
    n = len(xs)
    if n < 2:
        return None

    def ranks(vals):
        sorted_idx = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[sorted_idx[j + 1]] == vals[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[sorted_idx[k]] = avg_rank
            i = j + 1
        return r

    return pearson(ranks(xs), ranks(ys))


def compute_correlations(pairs):
    results = {}
    for dim in DIMENSIONS:
        gem, deep = [], []
        for p in pairs:
            g = p["gemini"].get(dim)
            d = p["deepseek"].get(dim)
            if g is not None and d is not None:
                gem.append(float(g))
                deep.append(float(d))
        if len(gem) < 2:
            results[dim] = {"n": len(gem)}
            continue
        results[dim] = {
            "n": len(gem),
            "pearson": pearson(gem, deep),
            "spearman": spearman(gem, deep),
            "mae": sum(abs(g - d) for g, d in zip(gem, deep)) / len(gem),
            "mean_diff": sum(d - g for g, d in zip(gem, deep)) / len(gem),
        }
    return results


def fmt(v, spec=".3f"):
    if v is None:
        return "—"
    return format(v, spec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sample", type=int, default=50)
    parser.add_argument("--model", default="deepseek-chat",
                        help="DeepSeek model ALIAS. Default 'deepseek-chat' resolves "
                             "server-side to deepseek-v4-flash in non-reasoning mode. "
                             "Do NOT 'pin' it to the literal 'deepseek-v4-flash' — that "
                             "enables reasoning mode and returns empty content "
                             "(see memory/gotcha-log.md, 2026-08-14)")
    parser.add_argument(
        "--output",
        default="datasets/scored/cd_v5_deepseek_validation/results.jsonl",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    api_key = get_deepseek_key()
    prompt_template = V5_PROMPT_PATH.read_text(encoding="utf-8")

    print(f"Loading v5-scored articles from {MERGED_JSONL.name}")
    all_v5 = load_v5_scored_articles()
    print(f"  Found {len(all_v5)} v5-scored articles")
    if len(all_v5) < args.n_sample:
        print(f"  WARN: Only {len(all_v5)} available, sampling all")

    sample = stratified_sample(all_v5, args.n_sample, args.seed)
    print(f"  Sampled {len(sample)} articles (stratified by content_type)")

    ct_dist = Counter(
        r["cultural_discovery_analysis"].get("content_type", "?") for r in sample
    )
    print(f"  Sample content_type dist: {dict(sorted(ct_dist.items(), key=lambda x: -x[1]))}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pairs = []
    errors = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_hit_tokens = 0

    def _process_one(article):
        prompt = build_prompt(prompt_template, article)
        resp = call_deepseek(api_key, args.model, prompt)
        parsed = parse_deepseek_response(resp)
        return article, parsed

    print(f"\nCalling DeepSeek ({args.model}) with 10-thread concurrency...")
    with open(output_path, "w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_process_one, art): art for art in sample}
            completed = 0
            for future in as_completed(futures):
                completed += 1
                article = futures[future]
                article_id = article.get("id", "unknown")[:60]
                try:
                    _, parsed = future.result()
                except Exception as exc:
                    parsed = {"error": f"Exception: {exc}"}

                if "error" in parsed:
                    errors += 1
                    print(f"  [{completed:3d}/{len(sample)}] {article_id:60s} ERROR: {parsed['error'][:60]}")
                    record = {
                        "id": article["id"],
                        "title": article.get("title", "")[:120],
                        "error": parsed["error"],
                        "raw_text": parsed.get("raw_text", ""),
                    }
                else:
                    gem_af = article["cultural_discovery_analysis"]
                    gem_dims = {dim: extract_dim_score(gem_af.get(dim)) for dim in DIMENSIONS}
                    deep_dims = {dim: parsed.get(dim) for dim in DIMENSIONS}
                    usage = parsed.get("_usage", {})
                    total_input_tokens += usage.get("prompt_tokens", 0)
                    total_output_tokens += usage.get("completion_tokens", 0)
                    total_cache_hit_tokens += usage.get("prompt_cache_hit_tokens", 0)
                    pair = {
                        "id": article["id"],
                        "title": article.get("title", "")[:120],
                        "gemini": gem_dims,
                        "gemini_content_type": gem_af.get("content_type"),
                        "deepseek": deep_dims,
                        "deepseek_content_type": parsed.get("content_type"),
                        "usage": usage,
                    }
                    pairs.append(pair)
                    record = pair
                    print(f"  [{completed:3d}/{len(sample)}] {article_id:60s} OK")

                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

    print(f"\n{'=' * 80}")
    print("VALIDATION REPORT")
    print(f"{'=' * 80}")
    print(f"Sample size:    {len(sample)}")
    print(f"Successful:     {len(pairs)}")
    print(f"Errors:         {errors}")
    print(f"\nDeepSeek tokens — input: {total_input_tokens:,}  "
          f"output: {total_output_tokens:,}  cached: {total_cache_hit_tokens:,}")
    if total_input_tokens:
        cache_rate = 100 * total_cache_hit_tokens / max(total_input_tokens, 1)
        print(f"Prompt cache hit rate: {cache_rate:.1f}%")

    if not pairs:
        print("\nNo successful pairs to analyze. Check errors above.")
        return

    results = compute_correlations(pairs)
    print(f"\nPer-dimension agreement (Gemini Flash 2.5  vs  DeepSeek {args.model}):")
    print(
        f"{'Dimension':<30} {'N':>4} {'Pearson':>10} {'Spearman':>10} "
        f"{'MAE':>8} {'Δmean':>8}"
    )
    print("-" * 80)
    for dim in DIMENSIONS:
        r = results[dim]
        p = fmt(r.get("pearson"))
        s = fmt(r.get("spearman"))
        m = fmt(r.get("mae"), ".2f")
        d = fmt(r.get("mean_diff"), "+.2f")
        print(f"{dim:<30} {r['n']:>4} {p:>10} {s:>10} {m:>8} {d:>8}")

    pearsons = [results[d].get("pearson") for d in DIMENSIONS if results[d].get("pearson") is not None]
    if pearsons:
        min_p, max_p = min(pearsons), max(pearsons)
        verdict = (
            "STRONG MATCH — switch to DeepSeek (saves ~$13)" if min_p > 0.90 else
            "WEAK MATCH — stay with Gemini Batch" if min_p < 0.85 else
            "BORDERLINE — judgment call (consider per-dim usage)"
        )
        print(f"\nMin/Max Pearson: {min_p:.3f} / {max_p:.3f}")
        print(f"Verdict (per decision rule): {verdict}")

    ct_match = sum(
        1 for p in pairs if p["gemini_content_type"] == p["deepseek_content_type"]
    )
    print(f"\ncontent_type exact agreement: {ct_match}/{len(pairs)} "
          f"({100 * ct_match / len(pairs):.0f}%)")

    print("\nTop 5 disagreement examples (largest mean |Δ| across dims):")
    for p in sorted(
        pairs,
        key=lambda x: -sum(
            abs((x["gemini"].get(d) or 0) - (x["deepseek"].get(d) or 0)) for d in DIMENSIONS
        ),
    )[:5]:
        print(f"\n  '{p['title']}'")
        print(
            f"  ct: Gemini={p['gemini_content_type']!r}  "
            f"DeepSeek={p['deepseek_content_type']!r}"
        )
        for dim in DIMENSIONS:
            g = p["gemini"].get(dim)
            d = p["deepseek"].get(dim)
            if g is not None and d is not None:
                print(f"    {dim:<32}: gem {float(g):>4.1f}  ds {float(d):>4.1f}  "
                      f"Δ {float(d) - float(g):+.1f}")

    print(f"\nResults: {output_path}")


if __name__ == "__main__":
    main()
