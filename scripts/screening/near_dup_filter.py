"""Drop candidate-pool articles that are near-duplicates of the calibration set.

Exact-id exclusion does not stop the SAME story under a different source/id from
leaking the calibration articles (used to pick the oracle/prompt and to seed
screening) into the training corpus — and then into both train and test. This
filter drops any pool article whose multilingual-e5 cosine to ANY calibration
text exceeds a threshold (default 0.93; see DATA_SETUP_PLAN.md Execution
defaults). Cross-lingual by construction (same model as the screener), so a
translated near-dup is caught too.

Run this on the assembled candidate pool BEFORE oracle scoring.

Usage:
    PYTHONPATH=. python scripts/screening/near_dup_filter.py \
        --pool datasets/screening/candidates.jsonl \
        --reference datasets/calibration/solutions_v4_calibration_350.jsonl \
        --output datasets/screening/candidates_dedup.jsonl \
        --threshold 0.93
"""

import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def text_of(a, max_chars=1024):
    # Match embedding_screener.article_to_text so the geometry is consistent.
    title = a.get("title", "")
    content = a.get("content", "") or a.get("text", "") or ""
    return f"query: {title}. {content[:max_chars]}"


def embed(model, articles, batch_size=256):
    texts = [text_of(a) for a in articles]
    out = []
    for i in range(0, len(texts), batch_size):
        out.append(model.encode(texts[i:i + batch_size], normalize_embeddings=True,
                                show_progress_bar=False))
    return np.vstack(out) if out else np.zeros((0, 384))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=Path, required=True, nargs="+",
                    help="candidate JSONL file(s) to filter")
    ap.add_argument("--reference", type=Path, required=True,
                    help="calibration JSONL whose near-dups must be removed")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--threshold", type=float, default=0.93,
                    help="drop a candidate if max cosine to any reference >= this")
    ap.add_argument("--batch-size", type=int, default=256)
    args = ap.parse_args()

    ref = load(args.reference)
    pool = []
    for p in args.pool:
        pool.extend(load(p))
    print(f"reference: {len(ref)}  pool: {len(pool)}  threshold: {args.threshold}")

    model = SentenceTransformer("intfloat/multilingual-e5-small")
    ref_emb = embed(model, ref, args.batch_size)          # (R, d)
    pool_emb = embed(model, pool, args.batch_size)        # (P, d)

    # max cosine of each pool item to any reference (all vectors L2-normalized)
    max_sim = (pool_emb @ ref_emb.T).max(axis=1) if len(ref) else np.zeros(len(pool))

    kept, dropped = [], 0
    for a, s in zip(pool, max_sim):
        if s >= args.threshold:
            dropped += 1
        else:
            kept.append(a)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for a in kept:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    print(f"dropped {dropped} near-dup(s) (>= {args.threshold}); "
          f"kept {len(kept)} -> {args.output}")
    if len(pool):
        print(f"pool max-sim: p50={np.median(max_sim):.3f}  "
              f"p95={np.quantile(max_sim,0.95):.3f}  max={max_sim.max():.3f}")


if __name__ == "__main__":
    main()
