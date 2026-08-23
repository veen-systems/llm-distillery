"""Score an article set with an Ollama-hosted oracle. $0 — a local judge, no API spend.

Uses the same prompt template + content compression + sanitization as Gemini
batch_scorer.py and validate_deepseek_oracle.py (byte-for-byte parity at the prompt level).

Defaults reproduce the original cultural_discovery v5 behaviour exactly — same prompt, same
frozen 522-article set, same dimensions, same host — so prior runs stay comparable
(ADR-020-draft operational safety: same article set across all oracles):

    PYTHONPATH=. python scripts/score_ollama_oracle.py --model qwen3:14b
    PYTHONPATH=. python scripts/score_ollama_oracle.py --model phi4:14b

Any filter, any article set, any host (llm-distillery#124 step 1, #109 Arm B, and the
human_thriving v8 Gate A calibration run):

    PYTHONPATH=. python scripts/score_ollama_oracle.py --model qwen3:14b \
        --host "$B650_HOST"   # see B650_HOST below; b650-gpu is an ssh alias, not DNS \
        --prompt filters/human_thriving/v8/prompt-candidate.md \
        --config filters/uplifting/v7/config.yaml \
        --input datasets/adverse/uplifting.jsonl \
        --runs 3

⚠️ `--host` defaults to **gpu-server, which runs production scoring**. Pass `B650_HOST`
(below) for experiments — judge inference on gpu-server competes with the live scorer
(`memory/b650-gpu.md`, `memory/gpu-server.md`).

⚠️ **A single run is not a measurement.** Oracle run-to-run noise is 0.82 mean / 2.25 max,
5x the #95 batch band. Use `--runs k` (k>=3); the summary prints per-article spread.

When `--config` is given, the weighted average is computed with that filter's weights and
gatekeeper, mirroring `filters/common/filter_base_scorer.py:_process_raw_scores` — clamp to
0-10, weighted sum, then cap if the gatekeeper dimension is below its minimum. Calibration is
deliberately NOT applied: these are oracle labels, not student outputs.

Output: `datasets/scored/{stem}_ollama_{model_slug}/results.jsonl`
"""

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ground_truth.text_cleaning import (
    clean_article as clean_article_comprehensive,
    sanitize_text_comprehensive,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V5_PROMPT_PATH = PROJECT_ROOT / "filters" / "cultural_discovery" / "v5" / "prompt-compressed.md"
CANONICAL_INPUT = PROJECT_ROOT / "datasets" / "scored" / "cd_v5_522_for_softpenalty_rescore.jsonl"
DEFAULT_OLLAMA_HOST = "http://gpu-server:11434"
# The non-production 3090 Ti. ⚠️ `b650-gpu` is an SSH-config alias, NOT a resolvable
# hostname -- `ssh b650-gpu` works while http://b650-gpu:11434 fails DNS. Use this
# Tailscale name for HTTP. Verified reachable 2026-08-23; ollama binds *:11434.
B650_HOST = "http://jwasys-b650-eagle-ax.taileb31bb.ts.net:11434"
PROMPT_PLACEHOLDER = "[Paste the summary of the article here]"
DEFAULT_DIMENSIONS = [
    "discovery_novelty",
    "heritage_significance",
    "cross_cultural_connection",
    "human_resonance",
    "evidence_quality",
]


def load_scoring_config(config_path: Path) -> dict:
    """Read dimensions, weights and gatekeeper out of a filter's config.yaml.

    Returns {'dimensions': [...], 'weights': {...}, 'gatekeeper': {...} or None}.

    ⚠️ config.yaml is DOCUMENTATION for the deployed runtime -- base_scorer.py's class
    constants are what score in production (CLAUDE.md Hard Constraints). That is fine here:
    this script grades ORACLE output, which never passes through base_scorer.py at all. Do
    not copy this loader into a student-scoring path.
    """
    import yaml

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    scoring = cfg.get("scoring")
    if not scoring or "dimensions" not in scoring:
        raise ValueError(f"{config_path}: no scoring.dimensions block")

    dims_block = scoring["dimensions"]
    dimensions = list(dims_block.keys())
    weights = {}
    for dim, spec in dims_block.items():
        if "weight" not in spec:
            raise ValueError(f"{config_path}: dimension {dim!r} has no weight")
        weights[dim] = float(spec["weight"])

    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"{config_path}: dimension weights sum to {total:.6f}, not 1.0 -- refusing to "
            f"score, because every weighted average would be silently wrong"
        )

    gatekeeper = None
    for dim, spec in dims_block.items():
        if spec.get("gatekeeper"):
            gatekeeper = {
                "dimension": dim,
                "min": float(spec["gatekeeper_threshold"]),
                "cap": float(spec["gatekeeper_max_score"]),
            }
            break

    return {"dimensions": dimensions, "weights": weights, "gatekeeper": gatekeeper}


def weighted_average(scores: dict, weights: dict, gatekeeper) -> tuple:
    """Mirror of filter_base_scorer._process_raw_scores, minus calibration.

    Returns (weighted_avg, gatekeeper_applied).
    """
    clamped = {d: float(max(0.0, min(10.0, scores[d]))) for d in weights}
    wavg = sum(clamped[d] * weights[d] for d in weights)
    applied = False
    if gatekeeper is not None:
        if clamped[gatekeeper["dimension"]] < gatekeeper["min"]:
            if wavg > gatekeeper["cap"]:
                wavg = gatekeeper["cap"]
                applied = True
    return wavg, applied


def smart_compress(content: str, max_words: int = 800) -> str:
    """Mirrors GenericBatchScorer._smart_compress_content exactly."""
    words = content.split()
    if len(words) <= max_words:
        return content
    start_words = int(max_words * 0.7)
    end_words = int(max_words * 0.3)
    beginning = " ".join(words[:start_words])
    ending = " ".join(words[-end_words:])
    return f"{beginning}\n\n[...content compressed...]\n\n{ending}"


def build_prompt(prompt_template: str, article: dict) -> str:
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


def load_articles(input_path: Path) -> list[dict]:
    """Load an article set. Default is the frozen 522 -- the single source of truth
    across all cd v5 oracle runs; do not swap it for a hand-built population."""
    articles = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            articles.append(json.loads(line))
    return articles


def call_ollama(model: str, prompt: str, host: str, max_retries: int = 2):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "num_predict": 4096,
            "num_ctx": 16384,  # enough for 8.4K prompt + 1.2K article + headroom
        },
    }
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{host}/api/chat",
                json=body,
                timeout=600,  # 27B CPU-offload would need much longer; 14B should be <60s
            )
            if resp.status_code == 200:
                return resp.json()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            last_err = str(e)
            time.sleep(2 ** attempt)
    return {"error": f"Max retries exceeded: {last_err}"}


def extract_dim_score(value):
    """Normalize dim value to flat float regardless of input shape.

    Handles:
      - {"score": 7.0, "evidence": "..."}  (Gemini/v5-prompt nested)
      - 7.0                                 (flat)
      - "7.0"                               (string, sometimes from Ollama)
      - None                                (missing)
    """
    if value is None:
        return None
    if isinstance(value, dict):
        s = value.get("score")
        if s is None:
            return None
        try:
            return float(s)
        except (TypeError, ValueError):
            return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def parse_response(resp: dict, dimensions: list):
    if "error" in resp:
        return {"error": resp["error"]}
    try:
        text = resp["message"]["content"]
        parsed = json.loads(text)
        out = {dim: extract_dim_score(parsed.get(dim)) for dim in dimensions}
        if any(v is None for v in out.values()):
            missing = [d for d, v in out.items() if v is None]
            return {
                "error": f"Missing/invalid dims: {missing}",
                "raw_text": text[:500],
                "parsed_keys": list(parsed.keys()),
            }
        out["content_type"] = parsed.get("content_type", "unknown")
        out["_eval_count"] = resp.get("eval_count", 0)
        out["_prompt_eval_count"] = resp.get("prompt_eval_count", 0)
        out["_total_duration_s"] = resp.get("total_duration", 0) / 1e9
        return out
    except (json.JSONDecodeError, KeyError) as e:
        raw = ""
        try:
            raw = resp.get("message", {}).get("content", "")[:500]
        except Exception:
            pass
        return {"error": f"Parse failed: {e}", "raw_text": raw}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Ollama model tag (e.g., qwen3:14b)")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Concurrent requests (default 2; Ollama serves sequentially per model)")
    parser.add_argument("--output-dir", default=None,
                        help="Default: datasets/scored/{input-stem}_ollama_{slug}/")
    parser.add_argument("--host", default=DEFAULT_OLLAMA_HOST,
                        help=f"Ollama base URL (default {DEFAULT_OLLAMA_HOST}). "
                             "⚠️ the default is gpu-server, which runs PRODUCTION scoring — "
                             "use B650_HOST (the b650 Tailscale name) for experiments")
    parser.add_argument("--prompt", default=None,
                        help=f"Prompt template (default: {V5_PROMPT_PATH.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--input", default=None,
                        help=f"Article JSONL (default: {CANONICAL_INPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--config", default=None,
                        help="Filter config.yaml supplying dimensions, weights and gatekeeper. "
                             "Without it, cd v5's dimensions are used and NO weighted average "
                             "is computed")
    parser.add_argument("--runs", type=int, default=1,
                        help="Score the set k times (default 1). ⚠️ oracle run-to-run noise is "
                             "0.82 mean / 2.25 max — a single run is NOT a measurement")
    args = parser.parse_args()

    if args.runs < 1:
        print("ERROR: --runs must be >= 1")
        sys.exit(1)

    prompt_path = Path(args.prompt) if args.prompt else V5_PROMPT_PATH
    input_path = Path(args.input) if args.input else CANONICAL_INPUT
    for label, p in (("--prompt", prompt_path), ("--input", input_path)):
        if not p.exists():
            print(f"ERROR: {label} not found: {p}")
            sys.exit(1)

    if args.config:
        scoring = load_scoring_config(Path(args.config))
        dimensions = scoring["dimensions"]
        weights = scoring["weights"]
        gatekeeper = scoring["gatekeeper"]
    else:
        dimensions, weights, gatekeeper = DEFAULT_DIMENSIONS, None, None

    model_slug = args.model.replace(":", "_").replace("/", "_")
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        stem = "cd_v5" if input_path == CANONICAL_INPUT else input_path.stem
        output_dir = PROJECT_ROOT / f"datasets/scored/{stem}_ollama_{model_slug}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "results.jsonl"

    prompt_template = prompt_path.read_text(encoding="utf-8")
    if PROMPT_PLACEHOLDER not in prompt_template:
        print(f"ERROR: {prompt_path} contains no {PROMPT_PLACEHOLDER!r} placeholder.")
        print("       Every article would be scored on the bare template with no article text,")
        print("       and the run would look successful. Refusing to start.")
        sys.exit(1)

    articles = load_articles(input_path)
    if not articles:
        print(f"ERROR: {input_path} is empty — nothing to score.")
        sys.exit(1)

    print(f"Loaded {len(articles)} articles from {input_path}")
    print(f"Prompt:  {prompt_path}")
    print(f"Config:  {args.config or '(none — no weighted average)'}")
    print(f"Dims:    {len(dimensions)} — {', '.join(dimensions)}")
    if gatekeeper:
        print(f"Gate:    {gatekeeper['dimension']} < {gatekeeper['min']} → cap {gatekeeper['cap']}")
    print(f"Host:    {args.host}" + ("   ⚠️ PRODUCTION BOX" if "gpu-server" in args.host else ""))
    print(f"Model:   {args.model}")
    print(f"Runs:    {args.runs}" + ("   ⚠️ single run is not a measurement" if args.runs == 1 else ""))
    print(f"Output:  {output_path}")
    print(f"Concurrency: {args.concurrency}")
    print()

    # Verify model exists on remote
    try:
        tags = requests.get(f"{args.host}/api/tags", timeout=10).json()
        if not any(m["name"] == args.model for m in tags.get("models", [])):
            print(f"ERROR: Model {args.model} not found on {args.host}")
            print(f"Available: {[m['name'] for m in tags.get('models', [])]}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Cannot reach Ollama at {args.host}: {e}")
        sys.exit(1)

    def _process(article):
        prompt = build_prompt(prompt_template, article)
        resp = call_ollama(args.model, prompt, args.host)
        parsed = parse_response(resp, dimensions)
        return article, parsed

    successes = 0
    errors = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_duration_s = 0

    by_article = defaultdict(list)  # id -> [weighted_average per successful run]

    start = time.time()
    with open(output_path, "w", encoding="utf-8") as f:
        for run_idx in range(1, args.runs + 1):
            if args.runs > 1:
                print(f"--- run {run_idx}/{args.runs} ---")
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = {executor.submit(_process, art): art for art in articles}
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    article = futures[future]
                    article_id = article.get("id", "unknown")[:60]
                    try:
                        _, parsed = future.result()
                    except Exception as e:
                        parsed = {"error": f"Exception: {e}"}

                    if "error" in parsed:
                        errors += 1
                        print(f"  [{completed:3d}/{len(articles)}] {article_id:60s} ERROR: {parsed['error'][:80]}")
                        record = {
                            "id": article["id"],
                            "run": run_idx,
                            "title": article.get("title", "")[:120],
                            "model": args.model,
                            "error": parsed["error"],
                            "raw_text": parsed.get("raw_text", "")[:300],
                        }
                    else:
                        successes += 1
                        total_input_tokens += parsed.get("_prompt_eval_count", 0)
                        total_output_tokens += parsed.get("_eval_count", 0)
                        total_duration_s += parsed.get("_total_duration_s", 0)
                        record = {
                            "id": article["id"],
                            "run": run_idx,
                            "title": article.get("title", "")[:120],
                            "model": args.model,
                            "content_type": parsed["content_type"],
                            "dims": {d: parsed[d] for d in dimensions},
                            "_prompt_eval_count": parsed["_prompt_eval_count"],
                            "_eval_count": parsed["_eval_count"],
                            "_total_duration_s": round(parsed["_total_duration_s"], 2),
                        }
                        if weights is not None:
                            wavg, gk = weighted_average(record["dims"], weights, gatekeeper)
                            record["weighted_average"] = round(wavg, 4)
                            record["gatekeeper_applied"] = gk
                            by_article[article["id"]].append(wavg)
                        if completed % 25 == 0 or completed == len(articles):
                            print(f"  [{completed:3d}/{len(articles)}] {article_id:60s} OK")

                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()

    wall = time.time() - start
    attempted = len(articles) * args.runs
    print()
    print(f"=" * 72)
    print(f"RESULTS for {args.model}")
    print(f"=" * 72)
    print(f"Successful: {successes}/{attempted}  Errors: {errors}")
    print(f"Wall clock: {wall/60:.1f} min  Sum inference: {total_duration_s/60:.1f} min")
    print(f"Tokens: input {total_input_tokens:,}  output {total_output_tokens:,}")
    if successes:
        print(f"Avg input tokens/article: {total_input_tokens/successes:.0f}")
        print(f"Avg duration/article: {total_duration_s/successes:.1f}s")

    # Per-article run-to-run spread. This is the reason --runs exists: a single oracle
    # score is not a measurement, and the spread here is the band every verdict carries.
    if args.runs > 1 and by_article:
        spreads = [max(v) - min(v) for v in by_article.values() if len(v) > 1]
        if spreads:
            spreads.sort()
            mean_spread = sum(spreads) / len(spreads)
            print()
            print(f"Run-to-run spread over {len(spreads)} articles with >1 successful run:")
            print(f"  mean {mean_spread:.3f}   median {spreads[len(spreads)//2]:.3f}   max {spreads[-1]:.3f}")
            print(f"  ⚠️ any two verdicts closer than the spread are NOT distinguishable")
        incomplete = [k for k, v in by_article.items() if len(v) < args.runs]
        if incomplete:
            print(f"  ⚠️ {len(incomplete)} articles have fewer than {args.runs} successful runs — "
                  f"their means rest on fewer samples")

    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
