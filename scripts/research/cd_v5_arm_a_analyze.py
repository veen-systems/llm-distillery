#!/usr/bin/env python3
"""#109 arm A, step 3: the pre-registered analysis of the cross-oracle re-score.

Reads the sample design, the Gemini re-scores of both arms, and the duplicate
control, and applies the decision rule fixed in
`docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md` BEFORE any score was seen.

Primary estimand
    D = MAD_refused - MAD_passed,
    MAD_g = mean over arm g of |gemini_weighted - stored_weighted|.

The comparison is PAIRED: every refused row shares a (domain, stored-label band)
cell with a passed row, so the difference is taken within cell and bootstrapped
over pairs. An unpaired test here would measure the label-distribution gap #105
already reported (1.102 vs 2.214), not label defensibility.

Decision rule (pre-registered, both conditions required)
    MATERIAL  iff the paired bootstrap 95% CI for D excludes 0
              AND |D| >= nu
    where nu is the WITHIN-oracle mean |delta| measured on this population by
    re-scoring the duplicate control a second time.

nu is measured, not borrowed. #95's 0.16 is a STUDENT batch-composition figure
and says nothing about oracle sampling at temperature 0.3; using it here would be
the wrong instrument, which this repo has already done three times in one day
(`memory/score-batch-shape-noise.md`).

Usage:
  PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_analyze.py \
      --design <dir>/design.json --scored <dir>/scored.jsonl \
      --noise-scored <dir>/noise_scored.jsonl [--out <report.json>]
"""
import argparse
import collections
import json
import math
import random
import statistics
import sys

BOOTSTRAP = 10000
SEED = 20260812
OP_POINT_FALLBACK = 4.0


def weighted(dims, weights):
    """Weighted mean over the filter's declared dimensions; None if any is absent."""
    num = den = 0.0
    for d, w in weights.items():
        v = dims.get(d)
        if v is None:
            return None
        num += float(v) * w
        den += w
    return num / den if den else None


def read_scores(path, weights, errors):
    """id -> weighted oracle score. Error/skip rows are counted, never dropped silently."""
    out = {}
    if not path:
        return out
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if 'error' in r or 'skipped' in r:
            errors.append({'id': r.get('id'), 'reason': r.get('error') or r.get('skipped')})
            continue
        analysis = None
        for k, v in r.items():
            if k.endswith('_analysis') and isinstance(v, dict):
                analysis = v
                break
        if analysis is None:
            errors.append({'id': r.get('id'), 'reason': 'no analysis field'})
            continue
        dims = {k: (v.get('score') if isinstance(v, dict) else v) for k, v in analysis.items()}
        s = weighted(dims, weights)
        if s is None:
            errors.append({'id': r.get('id'), 'reason': 'incomplete dimensions'})
            continue
        out[r['id']] = {'score': s, 'dims': dims}
    return out


def ci(samples, lo=2.5, hi=97.5):
    s = sorted(samples)
    n = len(s)
    return (round(s[int(lo / 100 * n)], 4), round(s[min(n - 1, int(hi / 100 * n))], 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--design', required=True)
    ap.add_argument('--scored', required=True)
    ap.add_argument('--noise-scored')
    ap.add_argument('--out')
    args = ap.parse_args()

    design = json.load(open(args.design, encoding='utf-8'))
    weights = design['weights']
    op = design.get('op_point_runtime', OP_POINT_FALLBACK)
    rows = design['rows']

    errors = []
    scored = read_scores(args.scored, weights, errors)
    noise_scored = read_scores(args.noise_scored, weights, errors) if args.noise_scored else {}

    # ---- coverage: what is missing, before anything is computed -------------
    missing = [rid for rid in rows if rid not in scored]
    per_arm_missing = collections.Counter(rows[rid]['arm'] for rid in missing)

    # ---- assemble, then pair within cell -----------------------------------
    recs = []
    for rid, meta in rows.items():
        if rid not in scored:
            continue
        g = scored[rid]
        recs.append({'id': rid, 'arm': meta['arm'], 'cell': (meta['domain'], meta['band']),
                     'domain': meta['domain'], 'band': meta['band'],
                     'language': meta.get('language', ''), 'weight': meta['weight'],
                     'stored': meta['stored_score'], 'gemini': g['score'],
                     'stored_dims': dict(zip(meta['dimension_names'], meta['stored_labels'])),
                     'gemini_dims': g['dims'],
                     'abs': abs(g['score'] - meta['stored_score']),
                     'signed': g['score'] - meta['stored_score']})

    by_cell = collections.defaultdict(lambda: {'refused': [], 'passed': []})
    for r in recs:
        by_cell[r['cell']][r['arm']].append(r)
    pairs = []
    dropped_unpairable = collections.Counter()
    for cell, arms in by_cell.items():
        a = sorted(arms['refused'], key=lambda x: x['id'])
        b = sorted(arms['passed'], key=lambda x: x['id'])
        k = min(len(a), len(b))
        # A pair breaks only when one arm's row failed to score. Keeping the
        # survivor would silently un-match the design, so the leftover is
        # dropped and counted.
        dropped_unpairable['refused'] += len(a) - k
        dropped_unpairable['passed'] += len(b) - k
        pairs += list(zip(a[:k], b[:k]))

    if not pairs:
        sys.exit('FATAL: no complete pairs survived scoring.')

    mad = {arm: statistics.mean([p[i]['abs'] for p in pairs])
           for i, arm in ((0, 'refused'), (1, 'passed'))}
    signed = {arm: statistics.mean([p[i]['signed'] for p in pairs])
              for i, arm in ((0, 'refused'), (1, 'passed'))}
    D = mad['refused'] - mad['passed']
    D_signed = signed['refused'] - signed['passed']

    rng = random.Random(SEED)
    boots = []
    boots_signed = []
    n = len(pairs)
    for _ in range(BOOTSTRAP):
        idx = [rng.randrange(n) for _ in range(n)]
        boots.append(statistics.mean([pairs[i][0]['abs'] - pairs[i][1]['abs'] for i in idx]))
        boots_signed.append(statistics.mean(
            [pairs[i][0]['signed'] - pairs[i][1]['signed'] for i in idx]))
    D_ci = ci(boots)
    D_signed_ci = ci(boots_signed)

    # ---- nu: the within-oracle floor, measured on this population ----------
    nu_deltas = []
    nu_by_arm = collections.defaultdict(list)
    for rid, g2 in noise_scored.items():
        base = rid[:-len('__dup2')] if rid.endswith('__dup2') else rid
        if base not in scored:
            errors.append({'id': rid, 'reason': 'duplicate has no first score'})
            continue
        d = abs(g2['score'] - scored[base]['score'])
        nu_deltas.append(d)
        nu_by_arm[rows[base]['arm']].append(d)
    nu = statistics.mean(nu_deltas) if nu_deltas else None
    nu_max = max(nu_deltas) if nu_deltas else None

    verdict = 'INDETERMINATE — nu not measured'
    if nu is not None:
        excludes_zero = (D_ci[0] > 0) or (D_ci[1] < 0)
        exceeds_nu = abs(D) >= nu
        if excludes_zero and exceeds_nu:
            verdict = 'MATERIAL'
        elif excludes_zero and not exceeds_nu:
            verdict = ('NOT MATERIAL — CI excludes 0 but |D| is below the oracle'
                       ' own run-to-run floor, so it is not interpretable')
        else:
            verdict = 'WITHIN NOISE'

    # ---- required secondary outputs ----------------------------------------
    def crossing(i):
        c = collections.Counter()
        for p in pairs:
            r = p[i]
            c[('stored>=op' if r['stored'] >= op else 'stored<op',
               'gemini>=op' if r['gemini'] >= op else 'gemini<op')] += 1
        return {f'{a}|{b}': v for (a, b), v in sorted(c.items())}

    dim_names = list(weights.keys())
    per_dim = {}
    for d in dim_names:
        per_dim[d] = {}
        for i, arm in ((0, 'refused'), (1, 'passed')):
            vals = [abs(float(p[i]['gemini_dims'][d]) - float(p[i]['stored_dims'][d]))
                    for p in pairs if p[i]['gemini_dims'].get(d) is not None]
            per_dim[d][arm] = round(statistics.mean(vals), 3) if vals else None
        if per_dim[d]['refused'] is not None and per_dim[d]['passed'] is not None:
            per_dim[d]['delta'] = round(per_dim[d]['refused'] - per_dim[d]['passed'], 3)

    # Per-source re-check: #109 makes this a required output, not a caveat.
    by_dom = collections.defaultdict(list)
    for p in pairs:
        by_dom[p[0]['domain']].append(p[0]['abs'] - p[1]['abs'])
    per_domain = [{'domain': d, 'pairs': len(v), 'delta': round(statistics.mean(v), 3)}
                  for d, v in sorted(by_dom.items(), key=lambda kv: -len(kv[1]))]
    doms5 = [x for x in per_domain if x['pairs'] >= 5]
    sign_agree = (sum(1 for x in doms5 if (x['delta'] > 0) == (D > 0)), len(doms5))

    by_lang = collections.defaultdict(list)
    for p in pairs:
        by_lang[p[0]['language'] or '?'].append(p[0]['abs'] - p[1]['abs'])
    per_language = [{'language': k, 'pairs': len(v), 'delta': round(statistics.mean(v), 3)}
                    for k, v in sorted(by_lang.items(), key=lambda kv: -len(kv[1]))]

    by_band = collections.defaultdict(list)
    for p in pairs:
        by_band[p[0]['band']].append(p[0]['abs'] - p[1]['abs'])
    per_band = [{'band': k, 'pairs': len(v), 'delta': round(statistics.mean(v), 3)}
                for k, v in sorted(by_band.items())]

    report = {
        'estimand': design.get('estimand'),
        'op_point_runtime': op,
        'n_pairs_designed': design.get('n_pairs'),
        'n_pairs_analysed': len(pairs),
        'coverage': {'scored_rows': len(scored), 'designed_rows': len(rows),
                     'missing': len(missing), 'missing_by_arm': dict(per_arm_missing),
                     'unpaired_dropped': dict(dropped_unpairable),
                     'errors': len(errors), 'error_sample': errors[:10]},
        'primary': {
            'mad_refused': round(mad['refused'], 4), 'mad_passed': round(mad['passed'], 4),
            'D': round(D, 4), 'D_ci95': D_ci,
            'nu_within_oracle_mean_abs_delta': round(nu, 4) if nu is not None else None,
            'nu_max': round(nu_max, 4) if nu_max is not None else None,
            'nu_n': len(nu_deltas),
            'nu_by_arm': {k: round(statistics.mean(v), 4) for k, v in nu_by_arm.items()},
            'ci_excludes_zero': bool((D_ci[0] > 0) or (D_ci[1] < 0)),
            'abs_D_ge_nu': bool(nu is not None and abs(D) >= nu),
            'VERDICT': verdict,
        },
        'signed_bias': {
            'refused_gemini_minus_stored': round(signed['refused'], 4),
            'passed_gemini_minus_stored': round(signed['passed'], 4),
            'difference': round(D_signed, 4), 'difference_ci95': D_signed_ci,
        },
        'op_point_crossing': {'refused': crossing(0), 'passed': crossing(1)},
        'per_dimension_mad': per_dim,
        'per_domain': per_domain,
        'per_domain_sign_agreement_ge5_pairs': f'{sign_agree[0]}/{sign_agree[1]}',
        'per_language': per_language,
        'per_band': per_band,
        'stored_score_balance': {
            'refused': round(statistics.mean([p[0]['stored'] for p in pairs]), 3),
            'passed': round(statistics.mean([p[1]['stored'] for p in pairs]), 3)},
        'excluded_unmatchable': design.get('excluded_unmatchable'),
    }

    print(json.dumps(report, indent=2))
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
