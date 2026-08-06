#!/usr/bin/env python3
"""LD#98 stage 2: apply the cd v6 e5 probe and report it against the v5 keyword gate.

Runs on gpu-server. Two modes, matching two different #98 acceptance criteria:

  --labelled <split.jsonl>
      Criterion 3. FN-rate on MEDIUM+ against the ORACLE labels, on a split the
      probe's threshold was NOT selected on. `train_probe.py` reports val FN, but
      the threshold is chosen off the val recall curve, so val FN is optimistic
      by construction — the test split is the honest number. Reports FN, never
      probe MAE (the trap named in docs/FILTER_PLAYBOOK.md).

  --rows <rows.jsonl>
      Criteria 1 and 2, over the production window written by
      `extract_probe_ab_rows.py`. Prints the same table shape as
      `measure_topic_gate_ab.py` so the two are read side by side.

Both arms use `filters.common.embedding_stage.EmbeddingStage` rather than
reimplementing embed -> scale -> probe -> weighted-average, so what is measured
here is what production would actually do, including the text preparation
(`title\\n\\ncontent`) and the 0-10 clamp.

Usage:
    cd ~/llm-distillery
    HF_HUB_OFFLINE=1 PYTHONPATH=. python scripts/gate/score_probe_ab.py \
        --filter filters/cultural_discovery/v6 --threshold 3.025 \
        --labelled datasets/training/cultural-discovery_v5/test.jsonl

    HF_HUB_OFFLINE=1 PYTHONPATH=. python scripts/gate/score_probe_ab.py \
        --filter filters/cultural_discovery/v6 --threshold 3.025 \
        --rows /tmp/cd_v6_ab_rows.jsonl --summary /tmp/cd_v6_ab_summary.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

OP, HIGH = 4.0, 7.0


def load_constants(filter_path: str):
    mod = importlib.import_module(str(filter_path).replace("/", ".").strip(".") + ".base_scorer")
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and name != "FilterBaseScorer" and hasattr(obj, "DIMENSION_NAMES"):
            return obj.DIMENSION_NAMES, obj.DIMENSION_WEIGHTS
    raise SystemExit(f"no scorer class with DIMENSION_NAMES in {filter_path}")


def build_stage(filter_path: str, threshold: float, dim_names, dim_weights):
    from filters.common.embedding_stage import EmbeddingStage
    return EmbeddingStage(
        embedding_model_name="intfloat/multilingual-e5-small",
        probe_path=str(Path(filter_path) / "probe" / "embedding_probe_e5small.pkl"),
        threshold=threshold,
        dimension_weights=dim_weights,
        dimension_names=dim_names,
    )


def screen_all(stage, articles, batch=256):
    """Screen in chunks so a long window doesn't build one enormous batch."""
    out = []
    for i in range(0, len(articles), batch):
        out.extend(stage.screen_batch(articles[i:i + batch], batch_size=64))
    return out


def wilson(k, n, z=1.96):
    """Wilson score interval — honest at the small counts the per-language rows hit."""
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def run_labelled(stage, path, dim_names, dim_weights, threshold, gate_path=None):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    arts = [{"title": r["title"], "content": r["content"]} for r in rows]
    res = screen_all(stage, arts)

    truths = []
    for r in rows:
        d = dict(zip(r["dimension_names"], r["labels"]))
        truths.append(sum(d[k] * dim_weights[k] for k in dim_names) >= OP)

    pos = sum(truths)
    neg = len(rows) - pos
    fn = sum(1 for t, s in zip(truths, res) if t and not s.needs_stage2)
    fp = sum(1 for t, s in zip(truths, res) if not t and s.needs_stage2)

    stage2 = sum(s.needs_stage2 for s in res)
    lo, hi = wilson(fn, pos)
    print(f"labelled split : {path}")
    print(f"  n                     {len(rows):,}")
    print(f"  MEDIUM+ positives     {pos} ({pos/len(rows):.1%})")
    print(f"  threshold             {threshold}")
    print(f"  FN on MEDIUM+         {fn}/{pos} = {fn/pos:.3%}   (95% CI {lo:.2%}-{hi:.2%})")
    print(f"  recall on MEDIUM+     {1-fn/pos:.3%}")
    print(f"  stage2 rate           {stage2/len(rows):.3%}  (screens out {1-stage2/len(rows):.1%})")
    print(f"  of negatives kept     {fp}/{neg} = {fp/neg:.1%}")

    # The threshold was selected off the VAL recall curve, so val FN is
    # optimistic by construction. This is the same curve on held-out labels —
    # read the screening cost of any recall target off THIS one.
    print(f"\n  held-out recall curve (threshold -> FN / recall / stage2-rate):")
    was = [s.weighted_avg for s in res]
    for t in [x / 4 for x in range(0, 17)]:
        f = sum(1 for tr, w in zip(truths, was) if tr and w < t)
        s2 = sum(1 for w in was if w >= t)
        mark = "  <- selected" if abs(t - threshold) < 0.13 else ""
        print(f"    t={t:5.2f}  FN={f/pos:6.3f}  recall={1-f/pos:6.3f}  "
              f"stage2={s2/len(rows):6.3f}{mark}")

    if gate_path:
        gate = load_prefilter_local(gate_path)
        # Pass `url` through: the gate's three domain blocklists
        # (VC_STARTUP_DOMAINS / DEFENSE_DOMAINS / CODE_HOSTING_DOMAINS) are
        # checked before any pattern, and silently never fire without it. Every
        # row in the label set carries a url, so omitting it would have measured
        # a weaker gate than the one that actually runs. The probe arm needs no
        # url — EmbeddingStage embeds title+content only.
        gp = [gate.apply_filter({"title": r["title"], "content": r["content"],
                                 "url": r.get("url", "")})[0] for r in rows]
        gfn = sum(1 for t, p in zip(truths, gp) if t and not p)
        gpass = sum(gp)
        glo, ghi = wilson(gfn, pos)
        print(f"\n  KEYWORD GATE on the same ground truth ({gate_path}):")
        print(f"    FN on MEDIUM+       {gfn}/{pos} = {gfn/pos:.3%}   (95% CI {glo:.2%}-{ghi:.2%})")
        print(f"    recall on MEDIUM+   {1-gfn/pos:.3%}")
        print(f"    pass rate           {gpass/len(rows):.3%}  (screens out {1-gpass/len(rows):.1%})")
        print(f"\n  -> on held-out oracle labels the probe misses {fn} positives, "
              f"the gate misses {gfn}.")


def load_prefilter_local(path):
    import importlib.util
    import os
    import sys
    root = os.getcwd()
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location(f"pf_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = next(o for o in vars(mod).values()
               if isinstance(o, type) and getattr(o, "__module__", None) == mod.__name__
               and callable(getattr(o, "apply_filter", None)))
    return cls()


def run_ab(stage, rows_path, summary_path, threshold):
    summary = json.load(open(summary_path, encoding="utf-8"))
    rows = [json.loads(l) for l in open(rows_path, encoding="utf-8") if l.strip()]
    arts = [{"title": r["title"], "content": r["content"]} for r in rows]
    res = screen_all(stage, arts)
    for r, s in zip(rows, res):
        r["cand_pass"] = bool(s.needs_stage2)
        r["cand_wa"] = s.weighted_avg

    surf = [r for r in rows if r["surfacing"]]
    samp = [r for r in rows if r.get("in_sample")]

    n = summary["n_scored"]
    print(f"window: {summary['window_cycles']} cycles  "
          f"{summary['window_first']} .. {summary['window_last']}")
    print(f"scored rows {n:,}   surfacing (raw>={OP}) {summary['n_surfacing']:,}   "
          f"high tier (raw>={HIGH}) {summary['n_high']}")
    print(f"baseline gate: {summary['gate_topic_stems']} topic stems   "
          f"probe threshold: {threshold}")
    print()

    b_blocked = summary["base_surfacing_blocked"]
    c_blocked = sum(not r["cand_pass"] for r in surf)
    b_high = summary["base_high_blocked"]
    c_high = sum(not r["cand_pass"] for r in surf if r["high"])
    n_surf = len(surf)

    # Baseline pass rate is exact over the whole window; the probe's is estimated
    # from the seeded sample of non-surfacing rows plus every surfacing row.
    s_pass = sum(r["cand_pass"] for r in samp)
    n_samp = len(samp)
    surf_frac = summary["n_surfacing"] / n
    cand_rate = (1 - surf_frac) * (s_pass / n_samp) + surf_frac * (sum(r["cand_pass"] for r in surf) / n_surf)
    # All the uncertainty lives in the non-surfacing stratum — the surfacing
    # stratum is measured exhaustively, not sampled — so the interval on the
    # combined estimate is the stratum's interval scaled by that stratum's
    # weight. Reporting the unscaled stratum CI here would overstate the
    # combined uncertainty by a factor of 1/(1-surf_frac).
    slo, shi = wilson(s_pass, n_samp)
    lo = cand_rate - (1 - surf_frac) * (s_pass / n_samp - slo)
    hi = cand_rate + (1 - surf_frac) * (shi - s_pass / n_samp)

    print(f"{'':<28}{'BASELINE':>12}{'CANDIDATE':>12}")
    print(f"{'gate pass rate (all rows)':<28}{summary['base_pass_rate']:>12.4f}{cand_rate:>12.4f}")
    print(f"{'  ^ candidate is sampled':<28}{'exact':>12}{f'±{(hi-lo)/2:.4f}':>12}")
    print(f"{'surfacing blocked':<28}{b_blocked:>12}{c_blocked:>12}")
    print(f"{'  as % of surfacing':<28}{b_blocked/n_surf:>11.1%}{c_blocked/n_surf:>12.1%}")
    print(f"{'high-tier blocked':<28}{b_high:>12}{c_high:>12}")
    print()

    per_lang = defaultdict(lambda: {"surf": 0, "base": 0, "cand": 0})
    for r in surf:
        d = per_lang[r["language"]]
        d["surf"] += 1
        d["base"] += not r["base_pass"]
        d["cand"] += not r["cand_pass"]

    print(f"{'lang':>6}{'surf':>7}{'base':>7}{'cand':>7}    base%   cand%")
    for lang, d in sorted(per_lang.items(), key=lambda kv: -kv[1]["surf"]):
        if d["surf"] < 3:
            continue
        print(f"{lang:>6}{d['surf']:>7}{d['base']:>7}{d['cand']:>7}"
              f"{d['base']/d['surf']:>9.1%}{d['cand']/d['surf']:>8.1%}")

    def pooled(key):
        en = per_lang.get("en")
        if not en:
            return None
        ns = sum(d["surf"] for l, d in per_lang.items() if l != "en")
        nb = sum(d[key] for l, d in per_lang.items() if l != "en")
        if not (en["surf"] and ns):
            return None
        p1, p2 = en[key] / en["surf"], nb / ns
        p = (en[key] + nb) / (en["surf"] + ns)
        se = math.sqrt(p * (1 - p) * (1 / en["surf"] + 1 / ns))
        return p1, p2, (p2 / p1 if p1 else float("nan")), ((p2 - p1) / se if se else 0.0)

    for key, label in (("base", "BASELINE"), ("cand", "CANDIDATE")):
        r = pooled(key)
        if r:
            print(f"\n{label}: en {r[0]:.1%}  non-en {r[1]:.1%}  ratio {r[2]:.2f}x  naive z {r[3]:.2f}")

    print("\n(the z is naive — the 08-02 pass measured a source-clustering design "
          "effect of 1.41, which divides z by ~1.19.)")

    both = sum(1 for r in surf if not r["base_pass"] and not r["cand_pass"])
    only_b = sum(1 for r in surf if not r["base_pass"] and r["cand_pass"])
    only_c = sum(1 for r in surf if r["base_pass"] and not r["cand_pass"])
    print(f"\nsurfacing agreement: blocked by both {both}   "
          f"gate only {only_b}   probe only {only_c}")

    near = sum(1 for r in surf if abs(r["raw"] - OP) <= 0.16)
    print(f"surfacing rows within the #95 noise floor (|raw-{OP}| <= 0.16): {near} "
          f"({near/n_surf:.1%}) — per-article agreement claims there are not evidence.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", required=True)
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--labelled")
    ap.add_argument("--gate", help="[--labelled] prefilter.py to score on the same ground truth")
    ap.add_argument("--rows")
    ap.add_argument("--summary")
    args = ap.parse_args()

    dim_names, dim_weights = load_constants(args.filter)
    stage = build_stage(args.filter, args.threshold, dim_names, dim_weights)

    if args.labelled:
        run_labelled(stage, args.labelled, dim_names, dim_weights, args.threshold, args.gate)
    if args.rows:
        if not args.summary:
            raise SystemExit("--rows needs --summary")
        run_ab(stage, args.rows, args.summary, args.threshold)


if __name__ == "__main__":
    main()
