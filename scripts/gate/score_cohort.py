"""
Score the agreement-gate cohorts with one nature_recovery student (v2 or v4).

Produces the {id, weighted_average} JSONL that scripts/gate/agreement_gate.py
consumes. Runs with skip_prefilter=True so the output isolates the STUDENT's
surfacing opinion (the gatekeepered weighted average) — the prefilter differs
between v2 (English keyword gate) and v4 (commerce-only), and mixing it in would
confound the agreement/over-demotion metrics.

Usage (gpu-server):
    PYTHONPATH=. python scripts/gate/score_cohort.py --version v4 \
        --inputs datasets/gate/nr_v4_sourceA_reference.jsonl \
                 datasets/gate/nr_v4_heldout_probes.jsonl \
                 datasets/gate/nr_v4_protection_probes.jsonl \
        --out datasets/gate/nr_v4_scored_by_v4.jsonl
"""
import argparse
import importlib
import json
from pathlib import Path


def load_articles(paths):
    """Load + dedupe by id across all input cohorts."""
    seen, arts = set(), []
    for p in paths:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rid = r.get("id") or r.get("article_id")
            if not rid or rid in seen:
                continue
            # test-split records store labels but the text is always title+content
            if not r.get("content"):
                continue
            seen.add(rid)
            arts.append({"id": rid, "title": r.get("title", ""), "content": r["content"]})
    return arts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", choices=["v2", "v4"], required=True)
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    mod = importlib.import_module(f"filters.nature_recovery.{args.version}.inference")
    scorer = mod.NatureRecoveryScorer(use_prefilter=False)

    arts = load_articles(args.inputs)
    print(f"[{args.version}] scoring {len(arts)} unique articles (skip_prefilter)")
    results = scorer.score_batch(arts, batch_size=args.batch_size, skip_prefilter=True)

    n = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for art, res in zip(arts, results):
            wa = res.get("weighted_average")
            if wa is None:
                continue
            f.write(json.dumps({"id": art["id"], "weighted_average": float(wa)}) + "\n")
            n += 1
    print(f"[{args.version}] wrote {n} scored records -> {args.out}")


if __name__ == "__main__":
    main()
