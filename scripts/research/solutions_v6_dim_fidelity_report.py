#!/usr/bin/env python3
"""Read solutions_v6_student_dim_fidelity.py's output and report per-dimension fidelity.

Three quantities, because they answer different questions and only the first two
are comparable across dimensions with different base rates:

  fires_on_pos  among rows the oracle scored >0, how often does the student put
                anything there at all? Conditional on the true class, so a rare
                dimension is not punished for being rare.
  false_fire    among rows the oracle scored 0, how often does the student fire
                anyway? This is the specificity-side error, the expensive one
                under ADR-023.
  r_pos         correlation with the oracle among oracle-positive rows -- does
                the student get the ORDERING right where the dimension applies.

MAE is printed last, as scale only. Ranking dimensions on it is the ADR-023
error: each dimension has its own positive rate, so per-article error tracks
composition as much as quality. `community_practice_strength` has the LOWEST MAE
of the seven and that fact carries no quality information whatsoever -- it is
zero on 96% of the split.

Also prints the isotonic step count, which is what surfaced the real defect:
a dimension with few training positives gets few calibration breakpoints, so its
output is quantised onto a handful of levels and its magnitude is compressed.

Usage:
  PYTHONPATH=. python3 scripts/research/solutions_v6_dim_fidelity_report.py \
      datasets/scored/solutions_v6_test_predictions.jsonl
"""
import json
import math
import statistics
import sys
from collections import Counter

DIMS = ['solution_concreteness', 'systemic_impact', 'evidence_strength',
        'governance_intervention_strength', 'community_practice_strength',
        'equity_access', 'economic_viability']
WEIGHTS = dict(zip(DIMS, [0.20, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10]))
FIRE = 0.5          # "the student put something here at all"
NOISE_FLOOR = 0.16  # #95, memory/score-batch-shape-noise.md
FOCUS = 'community_practice_strength'


def pearson(a, b):
    n = len(a)
    if n < 3:
        return float('nan')
    ma, mb = sum(a)/n, sum(b)/n
    va = math.sqrt(sum((x-ma)**2 for x in a))
    vb = math.sqrt(sum((x-mb)**2 for x in b))
    if va == 0 or vb == 0:
        return float('nan')
    return sum((x-ma)*(y-mb) for x, y in zip(a, b))/(va*vb)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'datasets/scored/solutions_v6_test_predictions.jsonl'
    rows = [json.loads(l) for l in open(path, encoding='utf-8')]
    print(f'rows: {len(rows):,}\n')

    hdr = (f"{'dimension':34s}{'n_pos':>7s}{'base%':>7s}{'fires_on_pos':>14s}"
           f"{'false_fire':>12s}{'r_pos':>8s}{'steps':>7s}{'MAE':>7s}")
    print(hdr)
    print('-' * len(hdr))
    for d in DIMS:
        o = [r['oracle'][d] for r in rows]
        s = [r['student'][d] for r in rows]
        pos = [(x, y) for x, y in zip(o, s) if x > 0]
        neg = [(x, y) for x, y in zip(o, s) if x == 0]
        fires = 100*sum(1 for _, y in pos if y >= FIRE)/len(pos) if pos else float('nan')
        ff = 100*sum(1 for _, y in neg if y >= FIRE)/len(neg) if neg else float('nan')
        r_pos = pearson([x for x, _ in pos], [y for _, y in pos])
        mae = statistics.mean(abs(x-y) for x, y in zip(o, s))
        print(f'{d:34s}{len(pos):7,}{100*len(pos)/len(o):6.1f}%{fires:13.1f}%'
              f'{ff:11.1f}%{r_pos:8.3f}{len(set(s)):7d}{mae:7.3f}')

    print(f'\n{FOCUS} detail:')
    pos = [(r['oracle'][FOCUS], r['student'][FOCUS], r['title']) for r in rows
           if r['oracle'][FOCUS] > 0]
    if not pos:
        print('  no oracle-positive rows in this split')
        return
    om, sm = statistics.mean(x for x, _, _ in pos), statistics.mean(y for _, y, _ in pos)
    gap = om - sm
    eff = WEIGHTS[FOCUS] * gap
    print(f'  oracle-positive rows: {len(pos)} ({100*len(pos)/len(rows):.1f}% of split)')
    print(f'  oracle mean {om:.2f}  student mean {sm:.2f}  shortfall {gap:.2f}')
    print(f'  weighted-score effect at weight {WEIGHTS[FOCUS]:.2f}: {eff:.3f}')
    print(f'  vs #95 noise floor {NOISE_FLOOR}: '
          f'{"ABOVE" if eff > NOISE_FLOOR else "BELOW"} -- on {100*len(pos)/len(rows):.1f}% of rows')
    print(f'  student==0 exactly on {sum(1 for _, y, _ in pos if y == 0)} of {len(pos)}')
    print(f'  most common student values: {Counter(round(y, 3) for _, y, _ in pos).most_common(6)}')
    print('\n  highest-oracle rows and what the student said:')
    for x, y, t in sorted(pos, key=lambda t: -t[0])[:12]:
        print(f'    oracle {x:4.1f} -> student {y:5.2f}   {t[:64]}')


if __name__ == '__main__':
    main()
