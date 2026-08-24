#!/usr/bin/env python3
"""Oracle cost per article, from COUNTED tokens only — never a back-solve.

Why this exists: #103's oracle choice was argued for three days on two rounded
figures back-solved from invoice totals under an *assumed* input shape. A residual
inherits the whole error of the terms subtracted from it, so both anchors were
soft, and they straddled the break-even. This script uses token counts that a run
actually reported, and prints the crossover as a ratio so the answer stops
depending on either anchor.

Rates read first-hand from the vendor pages on 2026-08-24:
  https://api-docs.deepseek.com/quick_start/pricing/
  https://ai.google.dev/gemini-api/docs/pricing
Re-read them before trusting the output — DeepSeek raised prices on 2026-08-16
and this file has no way to know it happened again.

Usage:  PYTHONPATH=. python3 scripts/analysis/oracle_cost.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# $ per 1M tokens.
DS = {"hit": 0.007, "miss": 0.22, "out": 0.66}      # deepseek-v4-flash, OFF-PEAK
DS_OLD = {"hit": 0.0028, "miss": 0.14, "out": 0.28}  # pre-2026-08-16, for the log check
GEM_BATCH = {"in": 0.15, "out": 1.25}                # gemini-2.5-flash Batch API
GEM_STD = {"in": 0.30, "out": 2.50}                  # gemini-2.5-flash realtime

PLACEHOLDER = "[Paste the summary of the article here]"

# The DeepSeek batch log this analysis rests on. In-repo, so it stays reproducible.
BATCH_LOG = PROJECT_ROOT / "datasets" / "scored" / "nr_v4_batch.log"

# Gate A, 2026-08-23: 15 articles x 3 runs, BOTH oracles on the identical articles,
# each billed on its own tokenizer's count. Means over the 45 successful calls.
# Raw rows were written to a session scratchpad (swept); these aggregates are the
# surviving record. n=15 ARTICLES (not 45) and they are a hand-picked adversarial
# sample, so absolute $/article are upper bounds — the provider RATIO is the result.
GATE_A = {
    #                     deepseek_in, deepseek_out, gemini_in, gemini_out
    "uplifting v7":         (6954.8, 349.3,  7096.1, 369.1),
    "human_thriving v8":    (8935.8, 315.6,  9128.1, 297.6),
    "human_thriving v8r2": (11022.8, 254.7, 11234.1, 332.3),
    "human_thriving v8r3": (11397.8, 266.1, 11610.1, 308.6),
}


def deepseek_cost(inp: float, out: float, cache: float, rates: dict = DS) -> float:
    blended_in = cache * rates["hit"] + (1.0 - cache) * rates["miss"]
    return (inp * blended_in + out * rates["out"]) / 1e6


def gemini_cost(inp: float, out: float, rates: dict = GEM_BATCH) -> float:
    return (inp * rates["in"] + out * rates["out"]) / 1e6


def crossover_ratio(cache: float) -> float | None:
    """input/output below which DeepSeek off-peak is cheaper than Gemini Batch.

    None means DeepSeek's blended input rate is already under Gemini's, so it wins
    at every shape and there is no crossover.
    """
    blended_in = cache * DS["hit"] + (1.0 - cache) * DS["miss"]
    denom = blended_in - GEM_BATCH["in"]
    if denom <= 0:
        return None
    return (GEM_BATCH["out"] - DS["out"]) / denom


def unconditional_cache_point() -> float:
    """Cache-hit rate at which DeepSeek's blended input equals Gemini Batch's."""
    return (DS["miss"] - GEM_BATCH["in"]) / (DS["miss"] - DS["hit"])


def parse_batch_log(path: Path) -> dict:
    """Pull the counted totals out of a score_deepseek_production.py run log.

    Raises if the log is missing or its shape changed. A cost analysis that
    silently falls back to an estimate is the failure this script exists to stop.
    """
    if not path.exists():
        raise SystemExit(f"FATAL: batch log not found: {path}")
    text = path.read_text(encoding="utf-8")
    tok = re.search(r"Tokens: input ([\d,]+)\s+output ([\d,]+)\s+cached ([\d,]+)", text)
    n = re.search(r"Successful: (\d+)", text)
    cost = re.search(r"Estimated cost: \$([\d.]+)", text)
    if not (tok and n and cost):
        raise SystemExit(f"FATAL: {path.name} does not carry the expected token/cost lines")
    return {
        "in": int(tok.group(1).replace(",", "")),
        "out": int(tok.group(2).replace(",", "")),
        "cached": int(tok.group(3).replace(",", "")),
        "n": int(n.group(1)),
        "logged_cost": float(cost.group(1)),
    }


def cache_ceilings() -> list[tuple[str, int, int, float]]:
    """Per-prompt prefix-cache ceiling.

    build_prompt() substitutes the article INTO the template, so only the part
    before the placeholder is a shared prefix across requests. Char share is a
    proxy for the token share the vendor actually bills — order of magnitude, not
    a hard cap.
    """
    rows = []
    for path in sorted((PROJECT_ROOT / "filters").rglob("prompt*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        idx = text.find(PLACEHOLDER)
        if idx < 0:
            continue
        rows.append((str(path.relative_to(PROJECT_ROOT)), idx, len(text), 100.0 * idx / len(text)))
    if not rows:
        raise SystemExit("FATAL: no prompt template contains the article placeholder — "
                         "did PLACEHOLDER change? Refusing to report a ceiling of nothing.")
    return rows


def main() -> int:
    batch = parse_batch_log(BATCH_LOG)
    per_in = batch["in"] / batch["n"]
    per_out = batch["out"] / batch["n"]
    cache = batch["cached"] / batch["in"]

    print("=" * 78)
    print(f"COUNTED BASELINE — {BATCH_LOG.name}, n={batch['n']:,} articles")
    print("=" * 78)
    print(f"  {per_in:,.0f} input / {per_out:.1f} output tokens per article   "
          f"cache hit {100 * cache:.2f}%   I/O = {per_in / per_out:.1f}")
    # Independent check: the log's own cost line must fall out of the OLD rate card.
    recomputed = deepseek_cost(batch["in"] - batch["cached"], batch["out"], 0.0, DS_OLD) \
        + batch["cached"] * DS_OLD["hit"] / 1e6
    ok = abs(recomputed - batch["logged_cost"]) < 0.01
    print(f"  rate-card check vs the log's own total: ${recomputed:.2f} vs "
          f"${batch['logged_cost']:.2f}  {'OK' if ok else 'MISMATCH — do not trust the counts'}")
    if not ok:
        return 1

    print()
    print("=" * 78)
    print("PER-ARTICLE COST AT MEASURED SHAPES ($/article, DeepSeek OFF-PEAK)")
    print("=" * 78)
    print(f"{'prompt':22s} {'I/O':>6s} {'DS@meas':>9s} {'GemBatch':>9s} {'GemRealtm':>9s}  "
          f"cheapest IMPLEMENTED")
    shapes = [("nature_recovery v3", per_in, per_out,
               per_in * 1.020, per_out * 1.057)]  # gemini tokens scaled from Gate A
    shapes += [(name, di, do, gi, go) for name, (di, do, gi, go) in GATE_A.items()]
    for name, di, do, gi, go in shapes:
        d_meas = deepseek_cost(di, do, cache)
        g_batch = gemini_cost(gi, go)
        g_rt = gemini_cost(gi, go, GEM_STD)
        # Only DeepSeek and Gemini REALTIME have a call site in this repo.
        implemented = "DeepSeek off-peak" if d_meas < g_rt else "Gemini realtime"
        print(f"{name:22s} {di / do:6.1f} {d_meas:9.6f} {g_batch:9.6f} {g_rt:9.6f}  {implemented}")
    print("  note: the nature_recovery Gemini columns scale DeepSeek's counts by the")
    print("        +2.0% input / +5.7% output tokenizer gap measured on Gate A. Estimated.")
    print()
    print("  " + "!" * 72)
    print("  !! THE GemBatch COLUMN IS A PRICE WE CANNOT PAY TODAY. There is no Batch API")
    print("  !! call site in this repo: ground_truth/batch_scorer.py and")
    print("  !! scripts/score_ollama_oracle.py both call models.generate_content (realtime),")
    print("  !! and `.batches` appears nowhere. Against the Gemini path that EXISTS,")
    print("  !! DeepSeek off-peak is the cheaper oracle at every measured shape.")
    print("  " + "!" * 72)

    print()
    print("=" * 78)
    print("THE ANSWER IS A RATIO, NOT AN ANCHOR")
    print("=" * 78)
    for c in (cache, 0.14, 0.30, unconditional_cache_point()):
        r = crossover_ratio(c)
        if r is None:
            print(f"  cache {100 * c:5.1f}%  DeepSeek wins at EVERY prompt shape")
        else:
            print(f"  cache {100 * c:5.1f}%  DeepSeek off-peak wins only when I/O < {r:5.2f}")
    print(f"  every prompt we run measures I/O = 19.9 - 43.3, so no output length reaches it")
    print(f"  unconditional flip point (any shape): cache hit >= "
          f"{100 * unconditional_cache_point():.1f}%")
    print()
    print("  ...but each measured shape flips EARLIER than that. Cache rate at which")
    print("  DeepSeek off-peak overtakes Gemini Batch, per shape:")
    for name, di, do, gi, go in shapes:
        needed = (DS["miss"] - (GEM_BATCH["in"] + (GEM_BATCH["out"] - DS["out"]) * do / di)) \
            / (DS["miss"] - DS["hit"])
        print(f"    {name:22s} I/O {di / do:5.1f}   flips at cache >= {100 * needed:5.1f}%")

    print()
    print("=" * 78)
    print("CACHE CEILING PER PROMPT (share of template before the article placeholder)")
    print("=" * 78)
    for rel, idx, total, pct in sorted(cache_ceilings(), key=lambda r: r[3]):
        print(f"  {pct:5.1f}%   {idx:6,} / {total:6,}   {rel}")
    print("  char share is a PROXY for the billed token share — an order-of-magnitude bound.")
    print("  Moving the placeholder to the END of a template lifts the ceiling toward ~97%,")
    print("  which crosses the unconditional flip point. That is a DIFFERENT PROMPT and needs")
    print("  a label-parity run before any retrain uses it (ADR-010). Untested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
