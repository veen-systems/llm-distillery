"""Production scoring of articles via DeepSeek V4 Flash for cultural_discovery v5 retrain.

Per ADR-020-draft methodology + 5-reviewer convergent verdict (2026-05-31): DeepSeek
selected as production oracle. This script scores arbitrary article batches with the
current v5 prompt and writes flat-format output suitable for prepare_data.py.

Resume-capable: skips article IDs already in the output file.

Usage:
    PYTHONPATH=. python scripts/score_deepseek_production.py \\
        --input datasets/scored/cd_v5_8k_v4prompt_articles.jsonl \\
        --output datasets/scored/cd_v5_8k_deepseek_v5_prompt.jsonl \\
        --concurrency 15
"""

import argparse
import configparser
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from ground_truth.text_cleaning import (
    clean_article as clean_article_comprehensive,
    sanitize_text_comprehensive,
)
from ground_truth import analysis_field_name

SECRETS_INI = PROJECT_ROOT / "config" / "credentials" / "secrets.ini"
V5_PROMPT_PATH = PROJECT_ROOT / "filters" / "cultural_discovery" / "v5" / "prompt-compressed.md"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
PROMPT_PLACEHOLDER = "[Paste the summary of the article here]"

# Defaults preserve cultural_discovery v5 back-compat; overridden by --config (see main()).
DIMENSIONS = [
    "discovery_novelty",
    "heritage_significance",
    "cross_cultural_connection",
    "human_resonance",
    "evidence_quality",
]
ANALYSIS_FIELD = "cultural_discovery_analysis"
FILTER_VERSION = "5.0-deepseek-production"


def load_filter_spec(config_path: Path):
    """Derive (dimensions, analysis_field, filter_version, prompt_path) from a filter config.yaml."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    name = cfg["filter"]["name"]
    version = str(cfg["filter"]["version"])
    dims = list(cfg["scoring"]["dimensions"].keys())
    prompt_path = config_path.parent / "prompt-compressed.md"
    return dims, analysis_field_name(name), f"{version}-deepseek", prompt_path


def get_deepseek_key():
    env_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_key:
        return env_key.strip()
    if SECRETS_INI.exists():
        cp = configparser.ConfigParser()
        cp.read(SECRETS_INI, encoding="utf-8")
        if "api_keys" in cp and "deepseek_api_key" in cp["api_keys"]:
            return cp["api_keys"]["deepseek_api_key"].strip()
    raise SystemExit("DeepSeek API key not found. See scripts/validate_deepseek_oracle.py for setup.")


def smart_compress(content: str, max_words: int = 800) -> str:
    words = content.split()
    if len(words) <= max_words:
        return content
    start = int(max_words * 0.7)
    end = int(max_words * 0.3)
    return f"{' '.join(words[:start])}\n\n[...content compressed...]\n\n{' '.join(words[-end:])}"


def build_prompt(prompt_template: str, article: dict) -> str:
    article = clean_article_comprehensive(article)
    content = article.get("content", "")
    compressed = smart_compress(content, max_words=800)
    title = sanitize_text_comprehensive(article.get("title", "N/A"))
    source = sanitize_text_comprehensive(article.get("source", "N/A"))
    published = sanitize_text_comprehensive(article.get("published_date", "N/A"))
    text = sanitize_text_comprehensive(compressed)
    summary = f"Title: {title}\nSource: {source}\nPublished: {published}\n\n{text}"
    return prompt_template.replace(PROMPT_PLACEHOLDER, summary)


def call_deepseek(api_key: str, model: str, prompt: str, max_retries: int = 3):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
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
                raise SystemExit(f"Auth failed: HTTP {resp.status_code}")
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = f"HTTP {resp.status_code}"
                time.sleep(2 ** attempt)
                continue
            return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except requests.exceptions.RequestException as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    return {"error": f"Max retries: {last_err}"}


def extract_dim_score(val):
    if val is None:
        return None
    if isinstance(val, dict):
        s = val.get("score")
        try:
            return float(s) if s is not None else None
        except (TypeError, ValueError):
            return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return None
    return None


def parse_response(resp: dict):
    if "error" in resp:
        return {"error": resp["error"]}
    try:
        text = resp["choices"][0]["message"]["content"]
        parsed = json.loads(text)
        dims = {d: extract_dim_score(parsed.get(d)) for d in DIMENSIONS}
        if any(v is None for v in dims.values()):
            return {"error": f"Missing dims: {[d for d, v in dims.items() if v is None]}", "raw": text[:300]}
        return {
            "dims": dims,
            "content_type": parsed.get("content_type", "unknown"),
            "usage": resp.get("usage", {}),
        }
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raw = ""
        try:
            raw = resp["choices"][0]["message"]["content"][:300]
        except (KeyError, IndexError):
            pass
        return {"error": f"Parse failed: {e}", "raw": raw}


def load_already_scored(output_path: Path) -> set:
    if not output_path.exists():
        return set()
    ids = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                ids.add(r["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSONL of articles")
    parser.add_argument("--output", required=True, help="Output JSONL of scored records")
    parser.add_argument("--model", default="deepseek-chat", help="DeepSeek model name")
    parser.add_argument("--concurrency", type=int, default=15)
    parser.add_argument("--progress-every", type=int, default=50)
    parser.add_argument("--config", help="Filter config.yaml; derives dimensions, "
                        "analysis field, version, and prompt path (default: cultural_discovery v5)")
    parser.add_argument("--prompt", help="Prompt template path (overrides the config-derived one)")
    args = parser.parse_args()

    global DIMENSIONS, ANALYSIS_FIELD, FILTER_VERSION
    prompt_path = V5_PROMPT_PATH
    if args.config:
        DIMENSIONS, ANALYSIS_FIELD, FILTER_VERSION, prompt_path = load_filter_spec(Path(args.config))
    if args.prompt:
        prompt_path = Path(args.prompt)

    api_key = get_deepseek_key()
    prompt_template = prompt_path.read_text(encoding="utf-8")
    print(f"Scoring with: dims={DIMENSIONS} | field={ANALYSIS_FIELD} | prompt={prompt_path.name}")
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load all articles
    articles = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                articles.append(json.loads(line))
    print(f"Loaded {len(articles)} articles from {input_path}")

    # Resume: skip already-scored
    already_scored = load_already_scored(output_path)
    if already_scored:
        articles = [a for a in articles if a["id"] not in already_scored]
        print(f"Resuming: {len(already_scored)} already scored, {len(articles)} remaining")

    if not articles:
        print("All articles already scored. Nothing to do.")
        return

    def _process(article):
        prompt = build_prompt(prompt_template, article)
        resp = call_deepseek(api_key, args.model, prompt)
        parsed = parse_response(resp)
        return article, parsed

    successes = 0
    errors = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cached_tokens = 0
    start = time.time()

    with open(output_path, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {executor.submit(_process, a): a for a in articles}
            completed = 0
            for future in as_completed(futures):
                completed += 1
                article = futures[future]
                try:
                    _, parsed = future.result()
                except Exception as e:
                    parsed = {"error": f"Exception: {e}"}

                if "error" in parsed:
                    errors += 1
                    record = {
                        "id": article["id"],
                        "title": article.get("title", "")[:200],
                        "url": article.get("url", ""),
                        "content": article.get("content", ""),
                        "source": article.get("source", ""),
                        "published_date": article.get("published_date", ""),
                        "language": article.get("language", ""),
                        "error": parsed["error"],
                        "raw": parsed.get("raw", "")[:300],
                    }
                else:
                    successes += 1
                    usage = parsed["usage"]
                    total_input_tokens += usage.get("prompt_tokens", 0)
                    total_output_tokens += usage.get("completion_tokens", 0)
                    total_cached_tokens += usage.get("prompt_cache_hit_tokens", 0)
                    # Match the format prepare_data.py expects: nested {dim: {score, evidence}} under cultural_discovery_analysis
                    analysis = {
                        d: {"score": parsed["dims"][d], "evidence": ""}
                        for d in DIMENSIONS
                    }
                    analysis["content_type"] = parsed["content_type"]
                    analysis["filter_version"] = FILTER_VERSION
                    analysis["analyzed_by"] = f"deepseek-{args.model}"
                    analysis["analyzed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    record = {
                        "id": article["id"],
                        "title": article.get("title", "")[:200],
                        "url": article.get("url", ""),
                        "content": article.get("content", ""),
                        "source": article.get("source", ""),
                        "published_date": article.get("published_date", ""),
                        "language": article.get("language", ""),
                        ANALYSIS_FIELD: analysis,
                    }

                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

                if completed % args.progress_every == 0 or completed == len(articles):
                    rate = completed / (time.time() - start)
                    eta_min = (len(articles) - completed) / max(rate, 0.01) / 60
                    cache_hit_pct = 100 * total_cached_tokens / max(total_input_tokens, 1)
                    print(f"  [{completed:>4}/{len(articles)}] {successes} OK | {errors} err | "
                          f"{rate:.1f} art/s | ETA {eta_min:.0f} min | cache hit {cache_hit_pct:.0f}%")

    wall = (time.time() - start) / 60
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {successes}  Errors: {errors}")
    print(f"Wall clock: {wall:.1f} min")
    print(f"Tokens: input {total_input_tokens:,}  output {total_output_tokens:,}  cached {total_cached_tokens:,}")
    print(f"Cache hit rate: {100*total_cached_tokens/max(total_input_tokens,1):.1f}%")
    # Cost estimate: DS V4 Flash = $0.14/M input miss, $0.0028/M cache hit, $0.28/M output
    uncached_input = total_input_tokens - total_cached_tokens
    cost = (uncached_input * 0.14 / 1e6) + (total_cached_tokens * 0.0028 / 1e6) + (total_output_tokens * 0.28 / 1e6)
    print(f"Estimated cost: ${cost:.2f}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
