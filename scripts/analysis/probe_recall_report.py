"""
Stage-1 probe recall report: FN@MEDIUM+ and routing rate, by script, by language,
and design-weighted back to the drawable population.

WHY THIS EXISTS, and what `train_probe.py`'s own printout cannot tell you:

  1. `train_probe.py` reports FN-rate on the val split UNWEIGHTED. The v8 corpus was
     drawn with per-cell inclusion probabilities (0.034-0.857, class-A cells oversampled
     ~20x), so an unweighted split rate is a rate for the SAMPLE, not for any population
     the filter will meet. This script joins `inclusion_probability` back from the corpus
     file and reports a Horvitz-Thompson estimate beside the raw one.
     ⚠️ The HT estimate is for the DRAWABLE population -- which excludes news.google.com
     (22.1% of production) and everything the draw's own exclusions removed. It is NOT
     a production estimate. Naming the population is the point of the column.

  2. The v8 plan requires FN@MEDIUM+ **split by language and by script**: with the keyword
     prefilter dropped (ADR-018/019 Amendment 2026-08-21) the multilingual probe is the
     only layer carrying multilingual selection. If it screens non-Latin content harder
     than Latin, ruling 3 has been undone silently and nothing else would catch it.

  3. It screens through the REAL consumer -- `filters/common/embedding_stage.EmbeddingStage`,
     the class production loads -- not a reimplementation of the weighted average. The
     numbers here are what the shipped code produces from the shipped pickle.

⛔ A rate without its denominator is not a measurement: every row of output prints n and,
for FN, the number of positives it is conditional on. An FN-rate over 3 positives is a
coin flip with a decimal point.

Usage:
    PYTHONPATH=. python scripts/analysis/probe_recall_report.py \
        --filter filters/human_thriving/v8 \
        --data-dir datasets/training/human_thriving_v8 \
        --split val \
        --corpus datasets/scored/human_thriving_v8/corpus.jsonl \
        --device cpu \
        --output docs/evidence/.../probe_recall_report_val.json
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# uplifting v7's shipped Stage-1 threshold -- v8's PREDECESSOR, and the only reason this
# constant has a defensible value. Reported as a reference column so "what would the filter
# this replaces have done" never has to be re-derived.
#
# ⛔ DO NOT RENAME THIS BACK TO A FLEET-WIDE CLAIM. It was called
# `DEPLOYED_DEFAULT_THRESHOLD` and described as "the screen threshold hardcoded in every
# inference_hybrid.py today"; that is false. Measured 2026-09-04 over 13 other packages:
# 0.75 (nature_recovery v1/v2/v4), 1.00 (belonging v1, uplifting v7), 1.225 (solutions
# v5/v6), 1.25 (cultural_discovery v4/v5), 1.50 (investment_risk v6), 2.25 (uplifting v6,
# thriving v1), 2.50 (cultural_discovery v6). Only 2 of 13 are 1.00, so pointing this
# script at another filter emitted a reference column wrong by up to 1.75 under a name that
# asserted otherwise. A field name is an assertion, read far more often than the note
# beside it.
# ⚠️ For any filter other than human_thriving/uplifting, pass --thresholds explicitly.
V7_DEPLOYED_THRESHOLD = 1.00


def load_jsonl(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _rate(num: float, den: float):
    """None, not 0.0, when the denominator is empty -- an absent rate must not read
    as a good one (the project's `make the missing case raise` rule, softened to
    `report it as missing` because a per-language table legitimately has empty cells)."""
    return (num / den) if den > 0 else None


def summarize(mask_names, wa, y, weights, threshold, weighted=True):
    """Screening stats at `threshold` for the rows selected by each mask.

    mask_names: list of (label, boolean mask over rows)
    wa:         predicted screen weighted-average per row (EmbeddingStage's own)
    y:          binary MEDIUM+ target per row (oracle labels, gatekeepered)
    weights:    design weight (1/inclusion_probability) per row
    weighted:   False when no --corpus was given. The weighted columns are then emitted
                as None rather than computed with weight 1.

    ⛔ `weighted=False` MUST null the weighted columns, not fill them with the unweighted
    value. This function shipped on 2026-09-04 emitting them unconditionally while its own
    caller's help text and the JSON's `design_weight_note` both promised they were
    "omitted rather than silently computed with weight 1" -- the field is there, is
    populated, and is a different instrument from the one its name claims. That is the
    2026-09-03 shape (`harm_title` recomputed vs stored) and it is the reason this
    parameter exists.
    """
    out = []
    for label, mask in mask_names:
        m = np.asarray(mask, dtype=bool)
        n = int(m.sum())
        pos = m & (y >= 0.5)
        n_pos = int(pos.sum())
        screened_out = m & (wa < threshold)
        fn = screened_out & pos

        w = weights[m]
        w_pos = weights[pos]
        row = {
            "group": label,
            "n": n,
            "n_positives": n_pos,
            "positive_rate": _rate(n_pos, n),
            "fn": int(fn.sum()),
            "fn_rate": _rate(int(fn.sum()), n_pos),
            "recall": None if n_pos == 0 else 1.0 - (int(fn.sum()) / n_pos),
            "stage2_rate": _rate(n - int(screened_out.sum()), n),
            # Σw, so a weighted rate can be POOLED across splits. Without these the only
            # poolable statistic is the unweighted one, which is what forced the
            # 2026-09-04 routing-gap test to be computed on sample rates in a document
            # arguing that sample rates describe no population.
            "sum_weights": float(w.sum()) if weighted else None,
            "sum_weights_positives": float(w_pos.sum()) if weighted else None,
            "sum_weights_screened_out": float(weights[screened_out].sum()) if weighted else None,
            "sum_weights_fn": float(weights[fn].sum()) if weighted else None,
        }
        if weighted:
            # Horvitz-Thompson: estimates for the population the draw sampled FROM.
            # `screened_out` is already masked by m, so it needs no second `& m`.
            row["weighted_positive_rate"] = _rate(float(w_pos.sum()), float(w.sum()))
            row["weighted_fn_rate"] = _rate(float(weights[fn].sum()), float(w_pos.sum()))
            row["weighted_stage2_rate"] = _rate(
                float(w.sum()) - float(weights[screened_out].sum()), float(w.sum())
            )
        else:
            row["weighted_positive_rate"] = None
            row["weighted_fn_rate"] = None
            row["weighted_stage2_rate"] = None
        out.append(row)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--filter", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--split", default="val", choices=["train", "val", "test"])
    parser.add_argument("--corpus", type=Path, default=None,
                        help="JSONL carrying id -> inclusion_probability / language / "
                             "non_latin. Without it every design-weighted column is null "
                             "(never silently computed with weight 1) and "
                             "design_weighted is false in the output.")
    parser.add_argument("--probe", type=Path, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--embedding-model", type=str,
                        default="intfloat/multilingual-e5-small")
    parser.add_argument("--thresholds", type=float, nargs="*", default=None,
                        help="Thresholds to report in full. Default: the probe's own "
                             "selected threshold, the filter's SHIPPED "
                             "hybrid_inference.stage1.threshold, and uplifting v7's 1.00 "
                             "as a reference.")
    parser.add_argument("--min-language-n", type=int, default=20,
                        help="Languages with fewer rows than this are pooled into "
                             "'(other)' -- a per-language FN over 3 positives is noise "
                             "with a decimal point.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    # Reuse train_probe's target definition rather than reimplementing the gatekeeper.
    import importlib.util
    tp_path = Path(__file__).resolve().parents[1] / "train_probe.py"
    spec = importlib.util.spec_from_file_location("train_probe", tp_path)
    tp = importlib.util.module_from_spec(spec)
    sys.modules["train_probe"] = tp
    spec.loader.exec_module(tp)

    cfg = tp._load_filter_constants(args.filter)
    tp.MEDIUM = cfg["MEDIUM"]
    tp.GATEKEEPER_DIM = cfg["GATEKEEPER_DIM"]
    tp.GATEKEEPER_MIN = cfg["GATEKEEPER_MIN"]
    tp.GATEKEEPER_CAP = cfg["GATEKEEPER_CAP"]
    tp.DIMENSION_NAMES = cfg["DIMENSION_NAMES"]
    tp.WEIGHTS = cfg["WEIGHTS"]

    probe_path = args.probe or (args.filter / "probe" / "embedding_probe_e5small.pkl")
    if not probe_path.exists():
        raise SystemExit(f"No probe at {probe_path}")

    with open(probe_path, "rb") as f:
        import pickle
        probe_metrics = pickle.load(f).get("metrics", {})

    articles = load_jsonl(args.data_dir / f"{args.split}.jsonl")
    logger.info(f"{args.split}: {len(articles)} rows")

    y = tp.labels_to_binary(np.array([a["labels"] for a in articles], dtype=np.float32))

    # --- design weights + strata, joined by id ------------------------------------
    weights = np.ones(len(articles), dtype=np.float64)
    languages = ["(unknown)"] * len(articles)
    non_latin = np.zeros(len(articles), dtype=bool)
    design_cell = ["(unknown)"] * len(articles)
    weighted = False
    if args.corpus:
        meta = {r["id"]: r for r in load_jsonl(args.corpus)}
        missing = [a["id"] for a in articles if a["id"] not in meta]
        if missing:
            # A silent partial join is how a design weighting gets lost. Refuse.
            raise SystemExit(
                f"{len(missing)} of {len(articles)} {args.split} ids are absent from "
                f"{args.corpus} (e.g. {missing[:3]}). Refusing to report weighted "
                f"numbers from a partial join."
            )
        missing_script = [a["id"] for a in articles if "non_latin" not in meta[a["id"]]]
        if missing_script:
            # ⛔ NOT a falsy default. `bool(m.get("non_latin"))` made every row Latin when
            # the field was renamed or absent, which empties the `script:non_latin` group
            # and makes the ruling-3 multilingual check report NO ASYMMETRY -- a negative
            # from an instrument that could not have said yes. Measured on the v8 corpus:
            # 0 of 6,590 rows missing (644 true, 9.8%), so this is latent, not live.
            raise SystemExit(
                f"{len(missing_script)} of {len(articles)} rows have no `non_latin` field "
                f"in {args.corpus} (e.g. {missing_script[:3]}). Defaulting it to False "
                f"would empty the non-Latin group and report no multilingual asymmetry "
                f"whether or not one exists. Refusing."
            )
        for i, a in enumerate(articles):
            m = meta[a["id"]]
            prob = m.get("inclusion_probability")
            if not prob or prob <= 0:
                raise SystemExit(f"id {a['id']} has inclusion_probability={prob!r}")
            weights[i] = 1.0 / float(prob)
            languages[i] = m.get("language") or "(unknown)"
            non_latin[i] = bool(m["non_latin"])
            design_cell[i] = m.get("design_cell") or "(unknown)"
        weighted = True
        logger.info(f"Joined {len(articles)} rows to design weights "
                    f"(w range {weights.min():.2f}-{weights.max():.2f})")

    # --- screen through the REAL consumer ------------------------------------------
    from filters.common.embedding_stage import EmbeddingStage

    stage = EmbeddingStage(
        embedding_model_name=args.embedding_model,
        probe_path=str(probe_path),
        threshold=V7_DEPLOYED_THRESHOLD,   # only affects needs_stage2, not wa
        dimension_weights=cfg["WEIGHTS"],
        dimension_names=cfg["DIMENSION_NAMES"],
        device=args.device,
    )
    logger.info("Screening through EmbeddingStage (the class production loads)...")
    results = stage.screen_batch(articles, batch_size=32)
    wa = np.array([r.weighted_avg for r in results], dtype=np.float64)

    thresholds = args.thresholds
    if not thresholds:
        # Include the SHIPPED threshold, not just the probe's own FN-budget pick. Without
        # this, re-running the script to check the deployed config produced a report that
        # omitted the deployed number -- the one thing a reader would come here to verify.
        candidates = {
            float(probe_metrics.get("selected_threshold", V7_DEPLOYED_THRESHOLD)),
            V7_DEPLOYED_THRESHOLD,
        }
        try:
            import yaml
            cfg = yaml.safe_load((args.filter / "config.yaml").read_text(encoding="utf-8"))
            shipped = ((cfg or {}).get("hybrid_inference") or {}).get("stage1", {}).get("threshold")
            if shipped is not None:
                candidates.add(float(shipped))
        except Exception as exc:  # a missing/unreadable config must not kill the report
            logger.warning(f"could not read the shipped stage-1 threshold: {exc}")
        thresholds = sorted(candidates)

    # --- groups ---------------------------------------------------------------------
    lang_counts = defaultdict(int)
    for l in languages:
        lang_counts[l] += 1
    big_langs = sorted([l for l, c in lang_counts.items() if c >= args.min_language_n])

    def groups():
        g = [("ALL", np.ones(len(articles), dtype=bool))]
        g.append(("script:latin", ~non_latin))
        g.append(("script:non_latin", non_latin))
        lang_arr = np.array(languages, dtype=object)
        for l in big_langs:
            g.append((f"lang:{l}", lang_arr == l))
        small = np.array([l not in big_langs for l in languages], dtype=bool)
        if small.any():
            g.append((f"lang:(other, n<{args.min_language_n} each)", small))
        return g

    report = {
        "filter": str(args.filter),
        "split": args.split,
        "n_rows": len(articles),
        "probe_path": str(probe_path),
        "probe_metrics": probe_metrics,
        "medium_threshold": cfg["MEDIUM"],
        "device": args.device,
        "design_weighted": weighted,
        "design_weight_note": (
            "Weighted columns are Horvitz-Thompson estimates for the DRAWABLE "
            "population the corpus was sampled from -- not for production, which "
            "the draw excluded news.google.com from (22.1%)."
        ) if weighted else "No --corpus given; weighted columns omitted.",
        "curve": [],
        "by_threshold": {},
    }

    # Full curve on ALL rows, so the threshold choice is auditable.
    for t in np.round(np.arange(0.0, 4.0001, 0.25), 3):
        rows = summarize([("ALL", np.ones(len(articles), dtype=bool))], wa, y, weights,
                         float(t), weighted=weighted)
        report["curve"].append({"threshold": float(t), **{
            k: rows[0][k] for k in ("fn", "fn_rate", "recall", "stage2_rate",
                                    "weighted_fn_rate", "weighted_stage2_rate")}})

    for t in thresholds:
        report["by_threshold"][f"{t:.3f}"] = summarize(groups(), wa, y, weights, float(t),
                                                       weighted=weighted)

    # --- print ----------------------------------------------------------------------
    print()
    print("=" * 96)
    print(f"Stage-1 probe recall report — {args.filter} — {args.split} split "
          f"(n={len(articles)}, {int(y.sum())} MEDIUM+ positives at >= {cfg['MEDIUM']})")
    print("=" * 96)
    print(f"probe: {probe_path}")
    print(f"probe metrics: {json.dumps(probe_metrics)}")
    if weighted:
        print(report["design_weight_note"])
    print()
    print("Curve on ALL rows (raw = this split; wtd = drawable population):")
    print(f"  {'thr':>5}  {'FN':>4}  {'FNrate':>7}  {'recall':>7}  {'stage2':>7}  "
          f"{'wFNrate':>8}  {'wStage2':>8}")
    for row in report["curve"]:
        def f(x, w=7):
            return f"{x:{w}.4f}" if x is not None else f"{'--':>{w}}"
        print(f"  {row['threshold']:5.2f}  {row['fn']:4d}  {f(row['fn_rate'])}  "
              f"{f(row['recall'])}  {f(row['stage2_rate'])}  "
              f"{f(row['weighted_fn_rate'], 8)}  {f(row['weighted_stage2_rate'], 8)}")

    for t, rows in report["by_threshold"].items():
        print()
        print(f"--- threshold {t} " + "-" * 60)
        print(f"  {'group':<34} {'n':>6} {'pos':>5} {'FN':>4} {'FNrate':>8} "
              f"{'stage2':>8} {'wFNrate':>8} {'wStage2':>8}")
        for r in rows:
            def f(x, w=8):
                return f"{x:{w}.4f}" if x is not None else f"{'--':>{w}}"
            print(f"  {r['group']:<34} {r['n']:6d} {r['n_positives']:5d} {r['fn']:4d} "
                  f"{f(r['fn_rate'])} {f(r['stage2_rate'])} "
                  f"{f(r['weighted_fn_rate'])} {f(r['weighted_stage2_rate'])}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
