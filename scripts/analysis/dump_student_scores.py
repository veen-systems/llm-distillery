"""
Dump a filter's student scores for a labelled split, in BOTH arms — raw and
calibrated — from a SINGLE forward pass.

WHY ONE PASS MATTERS. The question "does this calibration help?" is a comparison of
two score sets at an operating point, and a score is not a function of the article
alone: batch composition alone moves it by up to |0.16| (#95), which is larger than
most calibration effects near a threshold. Scoring twice — once with
`calibration.json` present, once with it moved aside — would put a noise term between
the arms that is bigger than the thing being measured. Calibration is a deterministic
per-dimension map applied to the raw logits BEFORE clamping
(`filter_base_scorer._process_raw_scores`), so both arms can be derived exactly from
one pass. They then differ by calibration and by nothing else.

Output is shaped for `scripts/gate/ground_truth_gate.py --recompute-model-wa`, which
applies the config's weights and gatekeeper identically to both arms:

    {"id": ..., "scores": {dim: value, ...}}

⛔ This does NOT decide anything. It produces two gate inputs; the gate reports recall
and specificity with the #95 band, and ADR-023 forbids ranking on MAE.

Usage:
    PYTHONPATH=. CUDA_VISIBLE_DEVICES= python scripts/analysis/dump_student_scores.py \
        --filter filters/human_thriving/v8 \
        --split-file datasets/training/human_thriving_v8/test.jsonl \
        --out-dir /tmp/ht_v8_test
"""

# design-weights: NOT APPLICABLE -- this script publishes no rate. It emits per-row raw
# and calibrated scores from a single forward pass and aggregates nothing. ⛔ The rows it
# emits ARE a design-weighted sample (25.1x span, weights in
# datasets/scored/human_thriving_v8/corpus.jsonl): anything downstream that turns this
# dump into a rate needs them.

import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _load_fit_calibration_module():
    """Reuse fit_calibration's scorer loading and raw-inference loop rather than
    reimplementing them: the arms must be produced by the same code path the
    calibration was fitted with, or the comparison is against a different program."""
    path = REPO_ROOT / "scripts" / "calibration" / "fit_calibration.py"
    spec = importlib.util.spec_from_file_location("fit_calibration", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fit_calibration"] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--filter", type=Path, required=True)
    parser.add_argument("--split-file", type=Path, required=True,
                        help="JSONL with id, title, content, labels")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    fc = _load_fit_calibration_module()

    filter_dir = args.filter.resolve()
    config = fc.load_filter_config(filter_dir)
    dimension_names = fc.get_dimension_names(config)

    articles = fc.load_data(args.split_file)
    logger.info(f"{args.split_file.name}: {len(articles)} rows")

    # Dimension order must come from the data when it disagrees, exactly as
    # fit_calibration does -- a silent reorder is a wrong label, not a missing one.
    if "dimension_names" in articles[0] and articles[0]["dimension_names"] != dimension_names:
        logger.warning(f"dimension order mismatch; using the data's: "
                       f"{articles[0]['dimension_names']}")
        dimension_names = articles[0]["dimension_names"]

    scorer = fc.load_scorer(filter_dir)
    logger.info(f"device: {scorer.device}")
    calibration = scorer.calibration
    if calibration is None:
        raise SystemExit(
            f"{filter_dir}/calibration.json is absent or failed to load, so there is no "
            f"calibrated arm to dump. Fit it first."
        )

    raw = fc.run_inference_raw(scorer, articles, dimension_names,
                               batch_size=args.batch_size)
    logger.info(f"raw logits: {raw.shape}")

    from filters.common.score_calibration import apply_calibration

    # ⛔ BUILD IN MEMORY AND CHECK BEFORE WRITING. The first version of this function wrote
    # and closed all three files and only then raised on the presence control below -- so
    # the files it "refused to emit" were on disk when it exited, and
    # `ground_truth_gate.py --recompute-model-wa` pointed at that directory would have read
    # them. A guard that fires after the damage is not a guard.
    raw_rows, cal_rows, logit_rows = [], [], []
    n_changed = 0
    for i, article in enumerate(articles):
        aid = article.get("id") or article.get("article_id", "")
        logits = raw[i]
        calibrated = apply_calibration(logits, calibration, dimension_names)

        # Clamp AFTER calibration, matching _process_raw_scores exactly.
        raw_scores = {d: float(max(0.0, min(10.0, logits[j])))
                      for j, d in enumerate(dimension_names)}
        cal_scores = {d: float(max(0.0, min(10.0, calibrated[j])))
                      for j, d in enumerate(dimension_names)}
        if raw_scores != cal_scores:
            n_changed += 1

        raw_rows.append({"id": aid, "scores": raw_scores})
        cal_rows.append({"id": aid, "scores": cal_scores})
        logit_rows.append({"id": aid, "logits": [float(x) for x in logits]})

    # A presence control: if calibration changed nothing, the comparison downstream is
    # vacuous and would read as "calibration is harmless" rather than "it did not run".
    logger.info(f"rows whose clamped scores differ between arms: {n_changed}/{len(articles)}")
    if n_changed == 0:
        raise SystemExit(
            "calibration changed NO row's clamped scores. Either it is an identity map "
            "or it was not applied -- refusing to emit two files that are the same file. "
            "Nothing was written."
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.out_dir / "scores_raw.jsonl"
    cal_path = args.out_dir / "scores_calibrated.jsonl"
    logits_path = args.out_dir / "raw_logits.jsonl"
    for path, rows in ((raw_path, raw_rows), (cal_path, cal_rows),
                       (logits_path, logit_rows)):
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    logger.info(f"wrote {raw_path}")
    logger.info(f"wrote {cal_path}")
    logger.info(f"wrote {logits_path}  (so this pass never has to be repeated)")


if __name__ == "__main__":
    main()
