#!/usr/bin/env python3
"""solutions v6: does the dimension-weighting ceiling actually cost anything?

BACKGROUND. `community_practice_strength` is zero on 83.1% of on-topic articles.
Step 2 of the oracle prompt MANDATES that: content_type "tech" forces both
governance and community to 0, "governance" forces community to 0. Because the
seven weights sum to 1.00, a mandated zero is a straight subtraction, so the
maximum achievable weighted score differs by solution type:

    pure tech (gov=0, comm=0)  ->  7.50
    governance (comm=0)        ->  9.00
    community / hybrid         -> 10.00

That ceiling is arithmetic, not inference. This script asks whether it COSTS
anything, by re-weighting over only the dimensions the content_type permits.

ANSWER (2026-08-11): no. See docs/evidence/2026-08-11-solutions-v6-community-
practice-dimension.md. Kept because the negative result is the useful part and
the ceiling looks alarming enough to be re-proposed.

TWO METHOD POINTS, both load-bearing.

1. A weight change has NO accuracy metric here. The oracle's "correct" weighted
   score IS the baseline weighting, so scoring new weights against ground truth
   defined by the old ones is circular. What is valid is the mechanical effect at
   MATCHED SURFACING VOLUME -- hold the number of surfaced articles fixed and
   vary the threshold. Comparing at a FIXED threshold instead measures only that
   the variants put the score on different scales, which is guaranteed.

2. The absolute-threshold table below is reported and then DISCOUNTED on purpose.
   Re-weighting moves ~20pp of articles across an absolute 4.0, which looks like
   it would fix NexusMind's enrichment starvation (NM#319). It does not.
   NexusMind's gate reads result["weighted_average"] (article_fetcher.py:1355),
   and production_scorer.py overwrites that field with the NORMALIZED score.
   Normalization is a percentile CDF, so a monotone rescale is mapped back to the
   same percentiles and the effect vanishes at the next refit. Section 3 prints
   the mapping so this cannot be re-derived as a win.

Usage:
  PYTHONPATH=. python3 scripts/research/solutions_v6_reweight_ablation.py
"""
import argparse
import bisect
import glob
import json
import os
import statistics
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIMS = ['solution_concreteness', 'systemic_impact', 'evidence_strength',
        'governance_intervention_strength', 'community_practice_strength',
        'equity_access', 'economic_viability']
BASE_W = dict(zip(DIMS, [0.20, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10]))
CONC, GOV, COMM = 0, 3, 4

# base_scorer.py TIER_THRESHOLDS -- the SOLE runtime source. config.yaml's tiers
# section is documentation; reading it here would repeat the confusion the Hard
# Constraints warn about.
OP = 2.25
GK_MIN, GK_CAP = 3.0, 3.0            # solution_concreteness gatekeeper
ENRICH_GATE = 4.0                    # NexusMind pipeline.enrichment.min_score


def gatekeep(wa, lab):
    return min(wa, GK_CAP) if lab[CONC] < GK_MIN else wa


def shape(lab):
    """Proxy for content_type, which is NOT stored in the training splits.

    Ambiguity that cannot be resolved from the splits: for a tech-shaped row we
    cannot tell a PROMPT-MANDATED zero from an honest one. The ceiling applies
    either way, which is why the proxy is adequate for this question and not for
    "did the oracle tag the type correctly".
    """
    if lab[COMM] > 0 and lab[GOV] > 0: return 'hybrid'
    if lab[COMM] > 0:                  return 'community'
    if lab[GOV] > 0:                   return 'governance'
    return 'tech'


def w_baseline(lab):
    return sum(v * BASE_W[d] for v, d in zip(lab, DIMS))


def _renorm(lab, drop):
    keep = [(v, d) for v, d in zip(lab, DIMS) if d not in drop]
    return sum(v * BASE_W[d] for v, d in keep) / sum(BASE_W[d] for _, d in keep)


def w_renorm(lab):
    """Renormalise over the dims the content_type PERMITS to be nonzero.

    Drops only dims the prompt mandates to zero -- never a dim that merely
    scored low on merit.
    """
    s = shape(lab)
    if s == 'tech':
        drop = {'governance_intervention_strength', 'community_practice_strength'}
    elif s == 'governance':
        drop = {'community_practice_strength'}
    else:
        drop = set()
    return _renorm(lab, drop)


def w_dropcg(lab):
    """Drop comm+gov for EVERY article -- makes solution type irrelevant."""
    return _renorm(lab, {'governance_intervention_strength', 'community_practice_strength'})


VARIANTS = [('baseline', w_baseline), ('renorm_permitted', w_renorm), ('drop_comm_gov', w_dropcg)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--splits', default=os.path.join(REPO, 'datasets/training/solutions_v6'))
    ap.add_argument('--filter-dir', default=os.path.join(REPO, 'filters/solutions/v6'))
    args = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(os.path.join(args.splits, '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            lab = r['labels']
            if isinstance(lab, str):
                lab = json.loads(lab)
            if len(lab) != 7:
                continue
            lab = [float(x) for x in lab]
            r['lab'] = lab
            r['shape'] = shape(lab) if max(lab) > 0 else 'not_a_solution'
            for name, fn in VARIANTS:
                r[name] = gatekeep(fn(lab), lab)
            rows.append(r)

    on = [r for r in rows if r['shape'] != 'not_a_solution']
    print(f'rows: {len(rows):,}   on-topic: {len(on):,}')

    print('\n=== ceiling (arithmetic, weights sum to 1.00) ===')
    print(f'  pure tech (gov=0, comm=0): {10*(1-0.15-0.10):.2f}')
    print(f'  governance (comm=0)      : {10*(1-0.10):.2f}')
    print(f'  community / hybrid       : 10.00')

    # ---- 1. matched surfacing volume: does anything REORDER? ----
    base_surf = [r for r in rows if r['baseline'] >= OP]
    N = len(base_surf)
    print(f'\n=== 1. matched volume (baseline surfaces {N:,} at op-point {OP}) ===')
    sets = {}
    for name, _ in VARIANTS:
        surf = sorted(rows, key=lambda r: -r[name])[:N]
        sets[name] = set(id(r) for r in surf)
        print(f'  {name:18s} equal-volume threshold {surf[-1][name]:.3f}')
    base_set = sets['baseline']
    for name, _ in VARIANTS[1:]:
        added = [r for r in rows if id(r) in sets[name] - base_set]
        dropped = [r for r in rows if id(r) in base_set - sets[name]]
        print(f'  {name} vs baseline: {len(added)} in / {len(dropped)} out '
              f'({100*len(added)/N:.1f}% churn)')
        print(f'      IN  {dict(Counter(r["shape"] for r in added).most_common())}')
        print(f'      OUT {dict(Counter(r["shape"] for r in dropped).most_common())}')

    # ---- 2. absolute thresholds: large, and REPORTED ONLY TO BE DISCOUNTED ----
    print(f'\n=== 2. absolute thresholds (see section 3 before believing this) ===')
    print(f"{'variant':18s}{'mean':>7s}{'>=2.25':>9s}{'>=4.0':>9s}{'>=5.0':>8s}")
    for name, _ in VARIANTS:
        sc = [r[name] for r in on]
        n = len(sc)
        print(f'{name:18s}{statistics.mean(sc):7.2f}'
              f'{100*sum(1 for x in sc if x >= OP)/n:8.1f}%'
              f'{100*sum(1 for x in sc if x >= ENRICH_GATE)/n:8.1f}%'
              f'{100*sum(1 for x in sc if x >= 5.0)/n:7.1f}%')
    print(f'\n  >= {ENRICH_GATE} by shape:')
    print(f"{'  shape':14s}{'n':>7s}" + ''.join(f'{nm[:12]:>13s}' for nm, _ in VARIANTS))
    for sh in ('tech', 'governance', 'community', 'hybrid'):
        g = [r for r in on if r['shape'] == sh]
        if not g:
            continue
        cells = ''.join(f'{100*sum(1 for r in g if r[nm] >= ENRICH_GATE)/len(g):12.1f}%'
                        for nm, _ in VARIANTS)
        print(f'  {sh:12s}{len(g):7,}{cells}')

    # ---- 3. why section 2 is not a win ----
    path = os.path.join(args.filter_dir, 'normalization.json')
    print('\n=== 3. the normalization interception ===')
    if not os.path.exists(path):
        print(f'  no normalization.json at {path} -- cannot demonstrate; do not trust section 2')
        return
    nz = json.load(open(path, encoding='utf-8'))
    x, y = nz['x'], nz['y']

    def norm(raw):
        if raw <= x[0]: return y[0]
        if raw >= x[-1]: return y[-1]
        i = bisect.bisect_left(x, raw)
        x0, x1, y0, y1 = x[i-1], x[i], y[i-1], y[i]
        return y0 + (y1-y0)*(raw-x0)/(x1-x0) if x1 > x0 else y0

    lo, hi = x[0], x[-1]
    for _ in range(80):
        m = (lo+hi)/2
        if norm(m) < ENRICH_GATE: lo = m
        else: hi = m
    surf = [r['baseline'] for r in rows if r['baseline'] >= OP]
    nmz = [norm(s) for s in surf]
    print(f'  method={nz["method"]}  fitted n={nz.get("n_articles")}  raw_min={nz["stats"]["raw_min"]}')
    print(f'  normalized {ENRICH_GATE} corresponds to raw {hi:.3f}')
    print(f'  of surfacing rows, {100*sum(1 for v in nmz if v >= ENRICH_GATE)/len(nmz):.1f}% clear it')
    print('\n  NexusMind reads the NORMALIZED score at article_fetcher.py:1355;')
    print('  production_scorer.py sets weighted_average <- apply_normalization(raw).')
    print('  A percentile CDF removes any monotone rescale, so section 2 washes out')
    print('  at the next refit. Re-weighting cannot fix enrichment starvation.')


if __name__ == '__main__':
    main()
