"""Embedding-based screener for needle-in-haystack filters.

Uses a small set of positive examples to find similar articles in a large
corpus via cosine similarity with e5-small embeddings.

Usage:
    PYTHONPATH=. python scripts/screening/embedding_screener.py \
        --positives datasets/nature_recovery/positives.jsonl \
        --corpus datasets/raw/fluxus_20260113.jsonl \
        --output datasets/nature_recovery/screen_candidates.jsonl \
        --top-k 500
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# Fix Windows encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', closefd=False)


# --- OFF_LENS source-exclusion mask (upstreamed from the solutions v4 gpu-server
# scratch screener, 2026-07-20). A similarity centroid pulls in off-lens
# ML/science/preprint/code rows (arxiv/pubmed/github/…) — the same contamination
# that made sustainability_technology v3 ~85% not_a_solution. These are noise for
# every news-shaped lens here. When --exclude-off-lens is set, off-lens rows are
# dropped BEFORE the top-k slice, so the quota backfills with the next-ranked news
# (embeddings are already computed — no re-embed). Opt-in so existing screening
# reproductions are unchanged; recommended for any needle filter. ---
OFF_LENS_SOURCE_TYPES = {
    "code_repo", "developer_aggregator", "firehose_aggregator",
    "preprint", "academic", "research_paper",
}
# Domain substrings matched against source / url (lowercased).
OFF_LENS_DOMAIN_SUBSTR = (
    "arxiv.org", "biorxiv.org", "medrxiv.org", "chemrxiv.org", "ssrn.com",
    "pubmed", "ncbi.nlm.nih.gov", "semanticscholar.org", "openreview.net",
    "researchgate.net", "github.com", "gitlab.com", "huggingface.co/papers",
)


def is_off_lens(article: dict) -> bool:
    """True if the article is off-lens ML/science/preprint/code noise (arxiv,
    pubmed, github, …) — see OFF_LENS_* above."""
    st = str(article.get("source_type", "")).strip().lower()
    if st in OFF_LENS_SOURCE_TYPES:
        return True
    hay = f"{article.get('source', '')} {article.get('url', '')}".lower()
    return any(dom in hay for dom in OFF_LENS_DOMAIN_SUBSTR)


def load_articles(path: Path, max_articles: int = 0) -> list:
    """Load articles from JSONL, handling both .json and .jsonl."""
    articles = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            articles.append(json.loads(line))
            if max_articles and len(articles) >= max_articles:
                break
    return articles


def article_to_text(article: dict, max_chars: int = 1024) -> str:
    """Convert article to embedding input text."""
    title = article.get('title', '')
    content = article.get('content', '') or article.get('text', '') or ''
    text = f"{title}. {content[:max_chars]}"
    return f"query: {text}"  # e5 models expect "query: " prefix


def embed_batch(model, texts: list, batch_size: int = 64) -> np.ndarray:
    """Embed texts in batches, return normalized embeddings."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        emb = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.append(emb)
    return np.vstack(all_embeddings)


def main():
    parser = argparse.ArgumentParser(description="Embedding-based article screener")
    parser.add_argument('--positives', type=Path, required=True,
                        help='JSONL of positive example articles')
    parser.add_argument('--corpus', type=Path, required=True, nargs='+',
                        help='JSONL corpus files to screen')
    parser.add_argument('--output', type=Path, required=True,
                        help='Output JSONL of top candidates')
    parser.add_argument('--top-k', type=int, default=500,
                        help='Number of top candidates to output')
    parser.add_argument('--batch-size', type=int, default=256,
                        help='Embedding batch size')
    parser.add_argument('--max-corpus', type=int, default=0,
                        help='Max corpus articles (0 = all)')
    parser.add_argument('--exclude-off-lens', action='store_true',
                        help='Drop off-lens ML/science/preprint/code rows '
                             '(arxiv/pubmed/github/…) before top-k, backfilling '
                             'the quota with next-ranked news. Recommended for '
                             'needle filters (see OFF_LENS_* constants).')
    args = parser.parse_args()

    # Load positive examples
    print(f"Loading positives from {args.positives}...")
    positives = load_articles(args.positives)
    print(f"  {len(positives)} positive examples")

    # Load model
    print("Loading e5-small...")
    model = SentenceTransformer('intfloat/multilingual-e5-small')

    # Embed positives and compute centroid
    pos_texts = [article_to_text(a) for a in positives]
    pos_embeddings = embed_batch(model, pos_texts)
    centroid = pos_embeddings.mean(axis=0)
    centroid = centroid / np.linalg.norm(centroid)  # re-normalize
    print(f"  Centroid computed from {len(positives)} examples")

    # Load and embed corpus in streaming batches
    print(f"Screening corpus files...")
    all_scores = []  # (similarity, article)
    total = 0

    for corpus_path in args.corpus:
        print(f"  Processing {corpus_path}...")
        articles = load_articles(corpus_path, max_articles=args.max_corpus)
        print(f"    {len(articles)} articles loaded")

        # Embed in batches and compute similarities
        for batch_start in range(0, len(articles), args.batch_size):
            batch = articles[batch_start:batch_start + args.batch_size]
            texts = [article_to_text(a) for a in batch]
            embeddings = embed_batch(model, texts, batch_size=args.batch_size)

            # Cosine similarity with centroid (embeddings already normalized)
            similarities = embeddings @ centroid

            for sim, article in zip(similarities, batch):
                all_scores.append((float(sim), article))

            total += len(batch)
            if total % 10000 == 0:
                print(f"    {total:,} articles embedded...")

    print(f"  Total: {total:,} articles embedded")

    # OFF_LENS mask (before top-k so the quota backfills with next-ranked news).
    # Log the drop count — never a silent cap.
    if args.exclude_off_lens:
        before = len(all_scores)
        all_scores = [(s, a) for (s, a) in all_scores if not is_off_lens(a)]
        dropped = before - len(all_scores)
        print(f"  OFF_LENS mask: dropped {dropped:,} off-lens rows "
              f"(arxiv/pubmed/github/science); {len(all_scores):,} remain, "
              f"top-{args.top_k} backfilled from next-ranked news.")

    # Sort by similarity, take top-k
    all_scores.sort(key=lambda x: x[0], reverse=True)
    top_k = all_scores[:args.top_k]

    print(f"\nTop-{args.top_k} similarity range: {top_k[0][0]:.4f} - {top_k[-1][0]:.4f}")
    print(f"Median corpus similarity: {all_scores[len(all_scores)//2][0]:.4f}")

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for sim, article in top_k:
            article['_similarity_score'] = round(sim, 4)
            f.write(json.dumps(article, ensure_ascii=False) + '\n')

    print(f"\nWrote {len(top_k)} candidates to {args.output}")

    # Show top 10 titles
    print("\nTop 10 candidates:")
    for sim, article in top_k[:10]:
        print(f"  [{sim:.4f}] {article.get('title', '?')[:80]}")


if __name__ == '__main__':
    main()
