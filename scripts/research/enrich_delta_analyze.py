#!/usr/bin/env python3
"""Pre- vs post-enrichment score delta, step 3: the analysis.

Reports, in this order, because the later numbers are uninterpretable without the
earlier ones:

1. The reproduction control -- does this box reproduce production's persisted
   `raw_weighted_average` on the POST text? Split by `stage_used`, because a
   `stage1_*` row's persisted score is an e5 PROBE ESTIMATE, not a model score
   (ADR-006), and comparing a full-model score against it compares two
   instruments rather than two boxes.
2. This population's own batch-composition floor, measured by scoring the same
   texts twice under different orderings. #95's |0.16| was measured on
   `uplifting v7` held-out rows and must not be inherited here.
3. The delta distribution, per lens and pooled -- percentiles, not a central
   estimate, because a mean over a bimodal population hides the effect.
4. Gate crossings, at BOTH each filter's raw op-point (from `base_scorer.py`
   TIER_THRESHOLDS, the runtime source) and at the NORMALIZED 4.0 that
   NexusMind's `pipeline.enrichment.min_score` actually reads. The same fitted
   mapping is applied to both sides, or the fit would move under the comparison
   and the result would report the refit rather than the enrichment.
5. Strata: stub-length band, and the empty-stub population reported as its own
   number rather than folded in.

Usage:
  PYTHONPATH=. python3 scripts/research/enrich_delta_analyze.py \
      --scored <dir>/scored.jsonl --design <dir>/pilot_design.json [--out report.json]
"""
import argparse
import collections
import json
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PKG = {
    'uplifting': 'filters/uplifting/v7',
    'investment_risk': 'filters/investment_risk/v6',
    'cultural_discovery': 'filters/cultural_discovery/v5',
    'belonging': 'filters/belonging/v1',
    'nature_recovery': 'filters/nature_recovery/v4',
    'solutions': 'filters/solutions/v6',
}
NORMALIZED_ENRICHMENT_GATE = 4.0  # NexusMind pipeline.enrichment.min_score, NM#319


def op_point(pkg_dir):
    """RUNTIME op-point: base_scorer.py TIER_THRESHOLDS, never config.yaml."""
    src = open(os.path.join(REPO, pkg_dir, 'base_scorer.py'), encoding='utf-8').read()
    marker = 'TIER_THRESHOLDS = ['
    i = src.index(marker)
    j = src.index(']', i)
    ns = {}
    exec('T = ' + src[i + len(marker) - 1:j + 1], ns)
    for name, thr, *_ in ns['T']:
        if name == 'medium':
            return float(thr)
    raise ValueError('no medium threshold in ' + pkg_dir)


def load_norm(pkg_dir):
    p = os.path.join(REPO, pkg_dir, 'normalization.json')
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding='utf-8'))


def pct(vals, ps=(1, 5, 10, 25, 50, 75, 90, 95, 99)):
    if not vals:
        return {}
    s = sorted(vals)
    out = {}
    for p in ps:
        k = min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))
        out[f'p{p}'] = round(s[k], 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scored', required=True)
    ap.add_argument('--design')
    ap.add_argument('--out')
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.scored, encoding='utf-8') if l.strip()]
    import numpy as np
    from filters.common.score_normalization import apply_normalization

    ops = {lens: op_point(d) for lens, d in PKG.items()}
    norms = {lens: load_norm(d) for lens, d in PKG.items()}

    report = {'n_units': len(rows), 'lenses': sorted(set(r['lens'] for r in rows)),
              'op_points_runtime': ops,
              'normalized_enrichment_gate': NORMALIZED_ENRICHMENT_GATE}

    # ---- 1. reproduction control, conditioned on stage --------------------
    ctrl = collections.defaultdict(list)
    for r in rows:
        if r.get('prod_raw') is None:
            continue
        stage = r.get('prod_stage') or 'unknown'
        key = 'stage2' if stage == 'stage2' else f'probe:{stage}'
        ctrl[key].append(abs(r['body_batch_a'] - r['prod_raw']))
    report['control_vs_production'] = {
        k: {'n': len(v), 'mean': round(statistics.mean(v), 4),
            'median': round(statistics.median(v), 4), 'max': round(max(v), 4),
            'within_0.16': sum(1 for d in v if d <= 0.16)}
        for k, v in sorted(ctrl.items())}
    report['control_note'] = (
        'A probe:* row\'s persisted raw_weighted_average is a Stage-1 e5 estimate, '
        'not a model score (ADR-006). Disagreement there is two instruments, not '
        'two boxes, and must not be read as reproduction failure.')

    # ---- 2. this population's own composition floor -----------------------
    comp = [abs(r['body_batch_a'] - r['body_batch_b']) for r in rows]
    single_vs_batch = [abs(r['body_batch_a'] - r['body_single']) for r in rows]
    report['own_batch_composition_floor'] = {
        'n': len(comp), 'mean': round(statistics.mean(comp), 6),
        'max': round(max(comp), 6),
        'note': 'measured on THIS population by re-scoring under a different '
                'ordering; #95\'s 0.16 was measured on uplifting v7 held-out rows '
                'and is a different population and length regime'}
    report['score_batch_vs_score_article'] = {
        'mean': round(statistics.mean(single_vs_batch), 6),
        'max': round(max(single_vs_batch), 6)}

    # ---- the empty-stub population, reported not folded in ----------------
    empty = [r for r in rows if r.get('stub_unscoreable')]
    report['empty_stub_population'] = {
        'n': len(empty), 'pct_of_units': round(100 * len(empty) / len(rows), 2),
        'post_enrichment_at_or_above_op': sum(
            1 for r in empty if r['body_single'] >= ops[r['lens']]),
        'note': 'empty pre-enrichment content cannot be scored -- _validate_article '
                'rejects it and always has (#93), so production could not have '
                'scored these either. Enrichment is the difference between the '
                'article being scored and being dropped; a score delta cannot '
                'express that.'}

    scoreable = [r for r in rows if r.get('stub_single') is not None]

    # ---- 3. the delta -----------------------------------------------------
    def deltas(rs):
        return [r['body_single'] - r['stub_single'] for r in rs]

    d_all = deltas(scoreable)
    report['delta_pooled'] = {
        'n': len(d_all), 'mean': round(statistics.mean(d_all), 4),
        'median': round(statistics.median(d_all), 4),
        'stdev': round(statistics.stdev(d_all), 4) if len(d_all) > 1 else None,
        'percentiles': pct(d_all),
        'share_negative': round(100 * sum(1 for d in d_all if d < 0) / len(d_all), 1),
        'share_within_0.1': round(100 * sum(1 for d in d_all if abs(d) <= 0.1) / len(d_all), 1),
    }
    report['delta_by_lens'] = {}
    for lens in sorted(set(r['lens'] for r in scoreable)):
        rs = [r for r in scoreable if r['lens'] == lens]
        d = deltas(rs)
        report['delta_by_lens'][lens] = {
            'n': len(d), 'mean': round(statistics.mean(d), 4),
            'median': round(statistics.median(d), 4), 'percentiles': pct(d),
            'share_negative': round(100 * sum(1 for x in d if x < 0) / len(d), 1)}
    report['delta_by_stub_band'] = {}
    for band in sorted(set(r['band'] for r in scoreable)):
        rs = [r for r in scoreable if r['band'] == band]
        d = deltas(rs)
        report['delta_by_stub_band'][band] = {
            'n': len(d), 'mean': round(statistics.mean(d), 4),
            'median': round(statistics.median(d), 4)}

    # ---- 4. gate crossings ------------------------------------------------
    raw_cross = collections.defaultdict(collections.Counter)
    norm_cross = collections.defaultdict(collections.Counter)
    norm_missing = []
    for r in scoreable:
        lens = r['lens']
        op = ops[lens]
        s, b = r['stub_single'], r['body_single']
        if s < op <= b:
            raw_cross[lens]['gained'] += 1
        elif b < op <= s:
            raw_cross[lens]['lost'] += 1
        elif s >= op and b >= op:
            raw_cross[lens]['both_above'] += 1
        else:
            raw_cross[lens]['both_below'] += 1

        nd = norms.get(lens)
        if not nd:
            norm_missing.append(lens)
            continue
        # The SAME fitted mapping on both sides. Re-fitting per side would report
        # the refit, not the enrichment.
        ns_, nb_ = apply_normalization(s, nd), apply_normalization(b, nd)
        g = NORMALIZED_ENRICHMENT_GATE
        if ns_ < g <= nb_:
            norm_cross[lens]['gained'] += 1
        elif nb_ < g <= ns_:
            norm_cross[lens]['lost'] += 1
        elif ns_ >= g and nb_ >= g:
            norm_cross[lens]['both_above'] += 1
        else:
            norm_cross[lens]['both_below'] += 1

    report['crossings_raw_op_point'] = {k: dict(v) for k, v in sorted(raw_cross.items())}
    report['crossings_normalized_4.0'] = {k: dict(v) for k, v in sorted(norm_cross.items())}
    if norm_missing:
        report['crossings_normalized_missing_fit'] = sorted(set(norm_missing))
    report['crossing_note'] = (
        'Raw crossings use each filter\'s runtime TIER_THRESHOLDS medium value. The '
        'normalized 4.0 is NexusMind pipeline.enrichment.min_score, which reads the '
        'NORMALIZED score (production_scorer.py:698 assigns weighted_average = '
        'normalized). Both sides share one fitted mapping.')

    totals_raw = collections.Counter()
    for v in raw_cross.values():
        totals_raw.update(v)
    totals_norm = collections.Counter()
    for v in norm_cross.values():
        totals_norm.update(v)
    report['crossings_pooled'] = {'raw': dict(totals_raw), 'normalized': dict(totals_norm)}

    print(json.dumps(report, indent=2))
    if args.out:
        json.dump(report, open(args.out, 'w', encoding='utf-8'), indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
