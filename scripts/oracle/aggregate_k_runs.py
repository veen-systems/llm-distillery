"""Aggregate k oracle runs of the SAME corpus into one label set — for a SCOPE-GATED prompt.

Why not `average_oracle_runs.py`
--------------------------------
That script predates the scope gate and does three things wrong for `human_thriving` v8,
each verified against real run files on 2026-09-01:

1. **It joins on `url`.** The scorer's own resume key is `id`, and `id` is what the corpus
   guarantees unique. A row with an empty url is skipped with a bare `continue`.
2. **It REPLACES the analysis object with six averaged numbers**, so `scope_verdict`,
   `dominant_subject`, `content_type` and every evidence quote are deleted. After it runs,
   the #135 measurement cannot be made at all — the runbook's own instruction is *"before
   averaging, check whether the prompt has a binary gate; if it does, report the flip RATE,
   not the mean"*, and the flip rate needs the per-run verdicts this discards.
3. **It intersects silently**: rows absent from any run vanish with a log line and exit 0.

⛔ Averaging a step function
---------------------------
`1/√k` describes a noisy continuum. The v8 scope gate is a Bernoulli that zeroes all six
dimensions, measured to flip on 5.3% of production-mix rows between identical runs (#135).
On a flipping row the arithmetic mean of three runs represents NO run: two verdicts of
`harm_is_subject` (dims 0–2) and one `in_scope` (dims high) average to a middling score that
neither the prompt nor a human would assign.

This script therefore does not choose for you. It writes **both** aggregates and the evidence
to tell them apart:

  `weighted_mean_all`   — the plain mean over all k runs (what "k=3 with aggregation" has
                          meant so far, and what Phase A measured)
  `weighted_mean_major` — the mean over only the runs agreeing with the MAJORITY verdict
  `scope_flipped`       — true when the k runs did not agree on the verdict
  `runs`                — every run's verdict and dimensions, kept, so the choice stays
                          re-derivable after the money is spent

The six top-level dimension keys carry `--aggregate` (default `all`), because that is what
`training/prepare_data.py` reads. Everything else rides alongside; prepare_data looks
dimensions up by name and ignores the rest.

⚠️ A flip rate is reported against a stated denominator, never as a bare percentage.

Usage:
  python3 scripts/oracle/aggregate_k_runs.py --runs r1.jsonl r2.jsonl r3.jsonl \
      --config filters/human_thriving/v8/config.yaml --out labels.jsonl [--aggregate all|majority]
"""
import argparse, collections, json, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import yaml
from ground_truth import analysis_field_name


def load_run(path, field):
    """Rows of one run, keyed by id. Errors and skips are counted, never silently dropped."""
    rows, errors, skipped, dup = {}, [], [], 0
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        rid = r.get("id")
        if rid is None:
            raise SystemExit(f"FATAL: {path} has a row with no id. Refusing to guess a join key.")
        if "error" in r:
            errors.append(rid); continue
        if "skipped" in r:
            skipped.append(rid); continue
        if field not in r:
            raise SystemExit(f"FATAL: {path} row {rid} has no '{field}'. Wrong --config for "
                             f"these runs? The field name comes from the config's filter.name.")
        if rid in rows:
            dup += 1
        rows[rid] = r
    return rows, errors, skipped, dup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="one JSONL FILE per run (not a directory)")
    ap.add_argument("--config", required=True, help="the filter config that was used to SCORE")
    ap.add_argument("--out", required=True)
    ap.add_argument("--aggregate", choices=("all", "majority"), default="all",
                    help="which mean lands on the six top-level dimension keys (default: all)")
    ap.add_argument("--allow-missing", type=int, default=0,
                    help="tolerate at most N ids absent from some run. A partial row is a REAL "
                         "event; make it a decision, not a default.")
    args = ap.parse_args()

    if len(args.runs) < 2:
        raise SystemExit("FATAL: aggregation needs at least 2 runs. With one run there is no "
                         "flip rate to report and no mean to take.")
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    dims = list(cfg["scoring"]["dimensions"].keys())
    field = analysis_field_name(cfg["filter"]["name"])
    weights = {d: cfg["scoring"]["dimensions"][d]["weight"] for d in dims}
    print(f"field {field}   dims {dims}")

    runs, ids_per_run = [], []
    for p in args.runs:
        rows, errors, skipped, dup = load_run(p, field)
        print(f"  {p}: {len(rows)} scored, {len(errors)} error, {len(skipped)} skipped"
              + (f", {dup} DUPLICATE id(s) — last wins" if dup else ""))
        runs.append(rows); ids_per_run.append(set(rows))

    common = set.intersection(*ids_per_run)
    union = set.union(*ids_per_run)
    partial = sorted(union - common)
    print(f"ids: {len(union)} seen, {len(common)} in all {len(runs)} runs, {len(partial)} partial")
    if len(partial) > args.allow_missing:
        for i in partial[:20]:
            miss = [args.runs[k] for k, s in enumerate(ids_per_run) if i not in s]
            print(f"  PARTIAL {i} missing from {miss}")
        raise SystemExit(f"FATAL: {len(partial)} id(s) are not in every run and --allow-missing "
                         f"is {args.allow_missing}. No output written. Resume the short run "
                         f"(the scorer skips ids already in its output) rather than dropping rows.")

    def wavg(scores):
        return sum(scores[d] * weights[d] for d in dims)

    out, flipped, verdict_counts = [], [], collections.Counter()
    for rid in sorted(common):
        per_run = []
        for rows in runs:
            a = rows[rid][field]
            sc = {}
            for d in dims:
                v = a.get(d, None)
                if v is None:
                    raise SystemExit(f"FATAL: {rid} is missing dimension '{d}'. prepare_data "
                                     f"would silently score it 0; refusing to write that.")
                sc[d] = float(v["score"] if isinstance(v, dict) else v)
            per_run.append({"scope_verdict": a.get("scope_verdict", "__absent__"),
                            "dominant_subject": a.get("dominant_subject", ""),
                            "content_type": a.get("content_type", ""),
                            "dimensions": sc, "weighted_average": round(wavg(sc), 4)})

        verdicts = [r["scope_verdict"] for r in per_run]
        for v in verdicts:
            verdict_counts[v] += 1
        major = collections.Counter(verdicts).most_common(1)[0][0]
        agree = [r for r in per_run if r["scope_verdict"] == major]
        is_flip = len(set(verdicts)) > 1
        if is_flip:
            flipped.append(rid)

        mean_all = {d: round(statistics.fmean(r["dimensions"][d] for r in per_run), 4) for d in dims}
        mean_maj = {d: round(statistics.fmean(r["dimensions"][d] for r in agree), 4) for d in dims}
        chosen = mean_all if args.aggregate == "all" else mean_maj

        base = dict(runs[0][rid])
        a0 = runs[0][rid][field]
        agg = dict(chosen)
        agg.update({
            "scope_verdict": major,
            "scope_flipped": is_flip,
            "scope_verdicts_per_run": verdicts,
            "dominant_subject": agree[0]["dominant_subject"],
            "content_type": agree[0]["content_type"],
            "weighted_mean_all": round(wavg(mean_all), 4),
            "weighted_mean_major": round(wavg(mean_maj), 4),
            "aggregate_used": args.aggregate,
            "k": len(runs),
            "runs": per_run,
            "filter_version": a0.get("filter_version", ""),
            "analyzed_by": a0.get("analyzed_by", ""),
            "prompt_hash": a0.get("prompt_hash", ""),
            "prompt_file": a0.get("prompt_file", ""),
        })
        base[field] = agg
        base.pop("usage", None)
        out.append(base)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(out)
    print(f"\nwrote {n} rows to {args.out}   (top-level dims = mean over "
          f"{'all runs' if args.aggregate == 'all' else 'the majority runs'})")
    print(f"⚠️ SCOPE GATE FLIP RATE: {len(flipped)}/{n} = {100*len(flipped)/n:.2f}% of rows "
          f"disagreed on scope_verdict across k={len(runs)} runs")
    print(f"   verdicts over all {n*len(runs)} run-rows: {dict(verdict_counts)}")
    deltas = [abs(r[field]["weighted_mean_all"] - r[field]["weighted_mean_major"]) for r in out]
    moved = [d for d in deltas if d > 0]
    if moved:
        print(f"   |mean_all - mean_major| on the {len(moved)} affected rows: "
              f"median {statistics.median(moved):.3f}  max {max(moved):.3f}")
    else:
        print("   the two aggregates are identical on every row (no flips)")
    print("⛔ The flip rate is not a defect to average away — it is the #135 step function. "
          "Decide --aggregate on this number, and keep the run files.")


if __name__ == "__main__":
    main()
