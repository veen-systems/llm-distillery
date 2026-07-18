"""Reproducible corpus-noise diagnostic for the Solutions v4 data-setup decision.

Why this exists: the DATA_SETUP_PLAN.md pivot (do NOT re-score the old ST v3 +
foresight corpora as-is) rests on a measured claim — that under the v4 Solutions
lens those corpora are ~85% not_a_solution. A 2026-07-18 review flagged that the
number came from an ephemeral run and was not reproducible from committed code.
This script makes it reproducible.

Two checks:
  1. composition  — FREE, no API. Source mix + preprint/arXiv share of a corpus.
  2. noise-rate   — given an already-scored file, the not_a_solution rate and
                    weighted-average distribution under the v4 config weights.

Rebuild the corpus (gpu-server, hcl@gpu-server ~/llm-distillery) if you need it:
    union of datasets/training/sustainability_technology_v3/*.jsonl (10,608)
          + datasets/training/foresight_v1_r2/*.jsonl (3,453), deduped by id
    -> 13,796 unique articles (fields id/title/content/url).

CANONICAL RESULT (seed=43, n=80, DeepSeek + v4 prompt, 2026-07-18):
    composition : 3,331 science_arxiv_cs of 13,796; preprint/arXiv share ~42%
    noise-rate  : 68/80 not_a_solution (85%); median weighted-avg 0.00;
                  1/80 (1%) ovr-visible (wa >= 4.5)

Usage:
    # free composition check
    python scripts/diagnostics/solutions_v4_corpus_noise_check.py \
        --corpus datasets/scored/solutions_v4_rescore_corpus.jsonl

    # write the deterministic sample to re-score
    python scripts/diagnostics/solutions_v4_corpus_noise_check.py \
        --corpus <corpus> --sample 80 --seed 43 --sample-out /tmp/diag_in.jsonl
    # ...score /tmp/diag_in.jsonl with scripts/score_deepseek_production.py...
    python scripts/diagnostics/solutions_v4_corpus_noise_check.py \
        --scored /tmp/diag_out.jsonl --config filters/solutions/v4/config.yaml
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path

PREPRINT_PREFIXES = ("arxiv", "science_arxiv", "science_biorxiv", "science_medrxiv",
                     "science_mdpi")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def source_of(rec):
    # ids are "<source>_<hash>"; the source is everything before the last "_".
    return rec.get("id", "unknown").rsplit("_", 1)[0]


def composition(corpus_path):
    rows = load(corpus_path)
    n = len(rows)
    src = Counter(source_of(r) for r in rows)
    preprint = sum(c for s, c in src.items() if s.startswith(PREPRINT_PREFIXES))
    print(f"corpus: {n} articles")
    print(f"distinct sources: {len(src)}")
    print(f"preprint/arXiv share: {preprint}/{n} ({100*preprint/n:.1f}%)")
    print("top sources:")
    for s, c in src.most_common(8):
        print(f"  {c:>5}  {s}")


def write_sample(corpus_path, n, seed, out):
    rows = load(corpus_path)
    random.seed(seed)
    sample = random.sample(rows, min(n, len(rows)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps({k: r.get(k, "") for k in
                    ["id", "title", "content", "source", "url", "published_date", "language"]},
                    ensure_ascii=False) + "\n")
    print(f"wrote {len(sample)} sampled articles (seed={seed}) -> {out}")


def noise_rate(scored_path, config_path):
    import yaml
    dims = yaml.safe_load(open(config_path))["scoring"]["dimensions"]
    weights = {k: v.get("weight", 0) for k, v in dims.items()}
    gk = next((k for k, v in dims.items() if v.get("gatekeeper")), None)
    af = "solutions_analysis"
    rows = [r for r in load(scored_path) if af in r]
    ct = Counter()
    was = []
    for r in rows:
        a = r[af]
        ct[a.get("content_type")] += 1
        wa = sum(a[d]["score"] * weights[d] for d in weights) / sum(weights.values())
        if gk and a[gk]["score"] < dims[gk].get("gatekeeper_threshold", 3):
            wa = min(wa, dims[gk].get("gatekeeper_max_score", 3.0))
        was.append(wa)
    n = len(rows) or 1
    was.sort()
    print(f"scored: {len(rows)} articles")
    print(f"content_type: {dict(ct)}")
    print(f"not_a_solution rate: {100*ct.get('not_a_solution',0)/n:.0f}%")
    print(f"median weighted-avg: {was[len(was)//2]:.2f}   max: {max(was):.2f}")
    print(f"ovr-visible (wa>=4.5): {sum(w>=4.5 for w in was)}/{n} "
          f"({100*sum(w>=4.5 for w in was)/n:.0f}%)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, help="corpus JSONL for composition/sampling")
    ap.add_argument("--sample", type=int, help="write a deterministic sample of this size")
    ap.add_argument("--seed", type=int, default=43)
    ap.add_argument("--sample-out", type=Path)
    ap.add_argument("--scored", type=Path, help="already-scored JSONL for the noise-rate check")
    ap.add_argument("--config", type=Path,
                    default=Path("filters/solutions/v4/config.yaml"))
    args = ap.parse_args()

    if args.corpus and not args.sample:
        composition(args.corpus)
    if args.corpus and args.sample:
        if not args.sample_out:
            ap.error("--sample requires --sample-out")
        write_sample(args.corpus, args.sample, args.seed, args.sample_out)
    if args.scored:
        noise_rate(args.scored, args.config)
    if not args.corpus and not args.scored:
        ap.error("give --corpus and/or --scored")


if __name__ == "__main__":
    main()
