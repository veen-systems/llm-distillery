"""Dump the Stage-1 probe's per-row screen weighted-average for a labelled split.

The probe's score is normally invisible: Stage 1 only decides route-or-not, and for rows
it routes onward the probe's number is discarded in favour of the student's. That makes
"could the probe do this job alone?" unanswerable from any artifact the pipeline keeps —
which is why the question keeps coming back and never gets settled.

Emits `{"id": ..., "probe_wa": float}`, the EXACT statistic the deployed threshold is
compared against: `filters/common/embedding_stage.EmbeddingStage.screen_batch`'s clamped
weighted average, with NO gatekeeper (hybrid_scorer.py documents that Stage 1 skips it).
Computed by that class, not reimplemented.

    PYTHONPATH=. python scripts/analysis/dump_probe_scores.py \
        --filter filters/human_thriving/v8 \
        --split-file datasets/training/human_thriving_v8/test.jsonl \
        --out probe_scores_test.jsonl
"""

# design-weights: NOT APPLICABLE -- this script publishes no rate. It emits one row per
# article ({"id", "probe_wa"}) and aggregates nothing, so there is no denominator for a
# weight to correct. ⛔ The rows it emits ARE a design-weighted sample (25.1x span,
# weights in datasets/scored/human_thriving_v8/corpus.jsonl): anything downstream that
# turns this dump into a rate needs them.

import argparse
import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--filter", type=Path, required=True)
    ap.add_argument("--split-file", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--probe", type=Path, default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--embedding-model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--batch-size", type=int, default=32)
    args = ap.parse_args()

    import importlib
    dotted = f"filters.{args.filter.parts[-2]}.{args.filter.parts[-1]}.base_scorer"
    mod = importlib.import_module(dotted)
    cls = next(v for k, v in vars(mod).items()
               if isinstance(v, type) and k.startswith("Base") and hasattr(v, "DIMENSION_NAMES"))

    probe = args.probe or (args.filter / "probe" / "embedding_probe_e5small.pkl")
    if not probe.exists():
        raise SystemExit(f"no probe at {probe}")

    articles = [json.loads(l) for l in open(args.split_file, encoding="utf-8") if l.strip()]
    logger.info(f"{args.split_file.name}: {len(articles)} rows")

    from filters.common.embedding_stage import EmbeddingStage
    stage = EmbeddingStage(
        embedding_model_name=args.embedding_model,
        probe_path=str(probe),
        threshold=0.0,               # irrelevant: we keep the score, not the verdict
        dimension_weights=cls.DIMENSION_WEIGHTS,
        dimension_names=cls.DIMENSION_NAMES,
        device=args.device,
    )
    results = stage.screen_batch(articles, batch_size=args.batch_size)
    if len(results) != len(articles):
        raise SystemExit(f"screen_batch returned {len(results)} for {len(articles)} rows")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for a, r in zip(articles, results):
            f.write(json.dumps({"id": a.get("id") or a.get("article_id", ""),
                                "probe_wa": float(r.weighted_avg),
                                "scores": r.scores}) + "\n")
    logger.info(f"wrote {args.out}")


if __name__ == "__main__":
    main()
