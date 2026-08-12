#!/usr/bin/env python3
"""#109 arm A, step 1: draw the matched sample for the `cultural_discovery v5`
cross-oracle re-score. Draws only -- no oracle call, no spend.

#105 established that today's labelling gate refuses 52.2% of the corpus
`cultural_discovery v5` was trained on, and that the refused rows carry LOWER
stored labels (mean 1.102 vs 2.214). That compares distributions, not truth.
Arm A asks whether the refused rows' labels are also less DEFENSIBLE, by
re-scoring them with a second oracle and comparing agreement against a matched
control drawn from the passed rows.

Three design constraints, each with a reason that has already cost this repo a
result:

1. Cross-oracle, not same-oracle. v5 was labelled by DeepSeek (ADR-020), so the
   instrument is Gemini Flash. Re-scoring with the labelling oracle measures
   self-consistency and cannot see a systematic error
   (`feedback-oracle-not-ground-truth`).

2. 1:1 matched on (domain, stored-label band) -- both variables, not either.
   Band, because #105 showed the two groups' label distributions differ sharply
   and an unmatched comparison would measure that instead. Domain, because #108
   died exactly here: a clean corpus-level result evaporated once the treatment
   turned out to be near-collinear with source. In this population refusal IS
   source-linked (eco.sapo.pt 198 refused / 14 passed), so source is a
   confounder, not a caveat.

3. Rows under 300 chars are excluded from BOTH arms. Only 6 refused rows are
   length-refused, so this costs almost nothing here, and it keeps the oracle
   inside the range the floor exists to protect (#93, #92).

What the design CANNOT reach, and why weighting does not fix it: a
(domain, band) cell with no passed row admits no matched pair. Those cells are
~55% of the refused population and concentrate in domains the lens gate refuses
almost totally. Weighting the matched sample up to the full refused population
would assume the unmatchable cells behave like the matchable ones -- the
assumption #108 refuted. The estimand is therefore the PAIR-MATCHABLE refused
population, and the excluded part is enumerated in the design report rather than
extrapolated over.

Usage:
  PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_sample.py \
      --splits-dir <dir with train/val/test.jsonl> \
      --meta <cd_v5_deepseek_merged_for_training.jsonl> \
      --out-dir <scratchpad dir>

Writes into --out-dir (article text -- keep it OUT of the repo, #97):
  sample.jsonl        rows to score, in the scorer's input schema
  noise_control.jsonl a subset re-emitted under `<id>__dup2` ids, so the same
                      oracle scores the same article twice and the within-oracle
                      floor is MEASURED before the gap is called material
  design.json         per-id arm/cell/weight/stored label + the cell table,
                      coverage and exclusions. Carries no article text.
"""
import argparse
import collections
import importlib
import inspect
import json
import os
import random
import statistics
import sys
from urllib.parse import urlparse

import yaml

from filters.common.base_prefilter import BasePreFilter
from ground_truth.batch_scorer import make_oracle_prefilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG_DIR = 'filters/cultural_discovery/v5'
PREFILTER_MOD = 'filters.cultural_discovery.v5.prefilter'
MIN_CHARS = 300

# Stored-label bands. Chosen from the measured joint distribution so every band
# holds pairable mass in both arms; the top band starts at the RUNTIME op-point
# (base_scorer.py TIER_THRESHOLDS medium = 4.0), not at config.yaml's copy of it.
BANDS = [(0.0, 0.5), (0.5, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 10.01)]


def band_of(score):
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= score < hi:
            return i
    return len(BANDS) - 1


def load_weights():
    cfg = yaml.safe_load(open(os.path.join(REPO, PKG_DIR, 'config.yaml'), encoding='utf-8'))
    return {k: float(v['weight']) for k, v in cfg['scoring']['dimensions'].items()}


def op_point():
    """The RUNTIME operating point: base_scorer.py TIER_THRESHOLDS, not config.yaml."""
    src = open(os.path.join(REPO, PKG_DIR, 'base_scorer.py'), encoding='utf-8').read()
    marker = 'TIER_THRESHOLDS = ['
    i = src.index(marker)
    j = src.index(']', i)
    ns = {}
    exec('T = ' + src[i + len(marker) - 1:j + 1], ns)
    for name, thr, *_ in ns['T']:
        if name == 'medium':
            return float(thr)
    raise ValueError('no medium threshold')


def weighted(labels, names, weights):
    if not labels or not names or len(labels) != len(names):
        return None
    num = den = 0.0
    for v, d in zip(labels, names):
        w = weights.get(d)
        if w is None:
            return None
        num += float(v) * w
        den += w
    return num / den if den else None


def allocate_by_slots(capacity, total, rng):
    """Draw `total` pairs by simple random sampling over PAIR SLOTS.

    Each cell contributes `capacity[cell]` slots; `total` slots are drawn without
    replacement from the pooled list. Every slot therefore has the same inclusion
    probability, so the design is self-weighting and no cell can be excluded by
    construction.

    The first version of this function allocated proportionally with largest
    remainders instead, and measurement killed it: 150 pairs over 342 cells sent
    252 cells to zero and produced weights spanning 4.0-17.0. Proportional
    rounding does not merely approximate a size-proportional sample at this
    ratio -- it deletes every cell smaller than one unit, and the surviving
    weights cannot represent what was deleted.
    """
    slots = []
    for k in sorted(capacity):
        slots += [k] * capacity[k]
    return collections.Counter(rng.sample(slots, total))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--splits-dir', required=True)
    ap.add_argument('--meta', required=True,
                    help='pre-split scored file; supplies source/published_date/language '
                         'so the re-score prompt carries the same metadata the labelling '
                         'oracle saw. Joined on id; a miss is fatal, never defaulted.')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--n', type=int, default=150, help='pairs (so 2n rows scored)')
    ap.add_argument('--noise-pairs', type=int, default=20,
                    help='pairs re-emitted for the within-oracle duplicate control '
                         '(2*this rows re-scored)')
    ap.add_argument('--seed', type=int, default=20260812)
    args = ap.parse_args()

    weights = load_weights()
    op = op_point()
    mod = importlib.import_module(PREFILTER_MOD)
    cls = [o for _, o in vars(mod).items()
           if inspect.isclass(o) and issubclass(o, BasePreFilter) and o is not BasePreFilter][0]
    pf = cls()
    gate = make_oracle_prefilter(pf)

    meta = {}
    for line in open(args.meta, encoding='utf-8'):
        line = line.strip()
        if line:
            r = json.loads(line)
            meta[r['id']] = r

    # ---- partition the training corpus exactly as the #105 audit does -------
    arms = {'passed': [], 'refused_lens': []}
    tally = collections.Counter()
    unattributed = []
    for split in ('train', 'val', 'test'):
        p = os.path.join(args.splits_dir, split + '.jsonl')
        if not os.path.exists(p):
            continue
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            art = {'title': r.get('title', ''), 'content': r.get('content', ''),
                   'url': r.get('url', ''), 'source': '', 'description': ''}
            score = weighted(r.get('labels'), r.get('dimension_names'), weights)
            if score is None:
                tally['unscorable'] += 1
                continue
            tally['rows'] += 1
            passed = gate(art)
            len_ok = pf.check_content_length(art)[0]
            lens_ok = pf.apply_filter(art)[0]
            if passed:
                arm = 'passed'
            elif not len_ok:
                arm = 'refused_length'
            elif not lens_ok:
                arm = 'refused_lens'
            else:
                arm = 'refused_unattributed'
                unattributed.append(r['id'])
            tally[arm] += 1
            if arm not in arms:
                continue
            if len((r.get('content') or '')) < MIN_CHARS:
                # Excluded from BOTH arms, and counted so the exclusion is visible.
                tally['dropped_short_' + arm] += 1
                continue
            m = meta.get(r['id'])
            if m is None:
                sys.exit(f'FATAL: id {r["id"]} is in the splits but not in --meta. '
                         f'The join must be complete; a defaulted source/date would '
                         f'make the two arms differ in prompt metadata.')
            arms[arm].append({
                'id': r['id'], 'title': r.get('title', ''), 'content': r.get('content', ''),
                'url': r.get('url', ''), 'source': m.get('source', ''),
                'published_date': m.get('published_date', ''), 'language': m.get('language', ''),
                'split': split, 'stored_labels': r['labels'],
                'dimension_names': r['dimension_names'], 'stored_score': score,
                'content_len': len(r.get('content') or ''),
                'domain': urlparse(r.get('url', '')).netloc.lower(),
                'band': band_of(score),
            })

    if unattributed:
        print(f'ATTRIBUTION INCOMPLETE: {len(unattributed)} rows are blocked by the gate '
              f'but pass both the length floor and apply_filter. The gate has grown a '
              f'refusal path this script does not know about; the refused arm is not '
              f'what it claims to be. Refusing to sample.', file=sys.stderr)
        return 1

    # ---- cells, pair capacity, allocation ----------------------------------
    R = collections.defaultdict(list)
    P = collections.defaultdict(list)
    for row in arms['refused_lens']:
        R[(row['domain'], row['band'])].append(row)
    for row in arms['passed']:
        P[(row['domain'], row['band'])].append(row)

    capacity = {k: min(len(v), len(P.get(k, []))) for k, v in R.items()}
    capacity = {k: c for k, c in capacity.items() if c > 0}
    total_cap = sum(capacity.values())
    refused_pop = len(arms['refused_lens'])
    if total_cap < args.n:
        sys.exit(f'FATAL: pair capacity {total_cap} < requested {args.n} pairs.')

    rng = random.Random(args.seed)
    alloc = dict(allocate_by_slots(capacity, args.n, rng))
    assert sum(alloc.values()) == args.n, (sum(alloc.values()), args.n)
    assert all(alloc[k] <= capacity[k] for k in alloc), 'a cell was over-drawn'
    sample = []
    for k in sorted(alloc):
        n = alloc[k]
        r_pool = sorted(R[k], key=lambda x: x['id'])
        p_pool = sorted(P[k], key=lambda x: x['id'])
        for row in rng.sample(r_pool, n):
            sample.append((k, 'refused', row))
        for row in rng.sample(p_pool, n):
            sample.append((k, 'passed', row))

    # ---- IPW back to the pair-matchable refused population ------------------
    # Slot sampling gives every pair slot the same inclusion probability
    # n / total_capacity, so the Horvitz-Thompson weight is the same constant for
    # every drawn pair. That is the IPW #109 asks for, and it is uniform because
    # of how the sample was DRAWN, not because the cells happen to be equal
    # sized -- they are not (capacity 1 to 68).
    #
    # A per-cell ratio weight (capacity_k / n_k) would also be unbiased and is
    # the more obvious reading of "inverse inclusion probability", but at 150
    # pairs over 342 cells almost every drawn cell has n_k = 1, so those weights
    # would be dominated by which small cells happened to be hit. Uniform HT
    # weights are used, and the analysis reports per-domain results separately
    # rather than leaning on cell weights to carry source balance.
    ht_weight = total_cap / args.n
    w = {k: ht_weight for k in alloc}

    os.makedirs(args.out_dir, exist_ok=True)
    design = {'filter': 'cultural_discovery v5', 'op_point_runtime': op,
              'weights': weights, 'bands': BANDS, 'seed': args.seed,
              'min_chars': MIN_CHARS, 'n_pairs': args.n,
              'population': {
                  'rows_scored_by_partition': dict(tally),
                  'refused_lens_ge_min_chars': refused_pop,
                  'passed_ge_min_chars': len(arms['passed']),
                  'pair_matchable_refused': total_cap,
                  'pair_matchable_pct_of_refused': round(100 * total_cap / refused_pop, 1),
                  'cells_refused': len(R), 'cells_pairable': len(capacity),
              },
              'estimand': 'the pair-matchable refused population '
                          f'({total_cap} of {refused_pop} rows, '
                          f'{round(100 * total_cap / refused_pop, 1)}%)',
              'cells': [{'domain': k[0], 'band': k[1], 'capacity': capacity[k],
                         'n_per_arm': alloc[k], 'weight': round(w[k], 4)}
                        for k in sorted(alloc)],
              'rows': {}}

    # What the estimand leaves out, enumerated by domain rather than assumed away.
    unmatchable = collections.Counter()
    for k, v in R.items():
        extra = len(v) - min(len(v), len(P.get(k, [])))
        if extra:
            unmatchable[k[0]] += extra
    design['excluded_unmatchable'] = {
        'rows': sum(unmatchable.values()),
        'pct_of_refused': round(100 * sum(unmatchable.values()) / refused_pop, 1),
        'top_domains': unmatchable.most_common(20),
    }

    with open(os.path.join(args.out_dir, 'sample.jsonl'), 'w', encoding='utf-8') as f:
        for k, arm, row in sample:
            f.write(json.dumps({kk: row[kk] for kk in
                                ('id', 'title', 'content', 'url', 'source',
                                 'published_date', 'language')}, ensure_ascii=False) + '\n')
            design['rows'][row['id']] = {
                'arm': arm, 'domain': k[0], 'band': k[1], 'weight': round(w[k], 4),
                'stored_score': round(row['stored_score'], 4),
                'stored_labels': row['stored_labels'],
                'dimension_names': row['dimension_names'],
                'split': row['split'], 'content_len': row['content_len'],
                'language': row['language'],
            }

    # ---- within-oracle duplicate control -----------------------------------
    # The pre-registered decision rule says the refused-vs-passed gap is
    # material only if it exceeds the same oracle's own run-to-run spread. That
    # floor has to be measured on THIS population, not borrowed: #95's 0.16 is a
    # STUDENT batch-composition number and says nothing about oracle sampling at
    # temperature 0.3.
    by_arm = collections.defaultdict(list)
    for k, arm, row in sample:
        by_arm[arm].append(row)
    dup_rng = random.Random(args.seed + 1)
    dups = []
    for arm in ('refused', 'passed'):
        pool = sorted(by_arm[arm], key=lambda x: x['id'])
        dups += dup_rng.sample(pool, min(args.noise_pairs, len(pool)))
    with open(os.path.join(args.out_dir, 'noise_control.jsonl'), 'w', encoding='utf-8') as f:
        for row in dups:
            rec = {kk: row[kk] for kk in ('title', 'content', 'url', 'source',
                                          'published_date', 'language')}
            rec['id'] = row['id'] + '__dup2'
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    design['noise_control_ids'] = [r['id'] for r in dups]

    with open(os.path.join(args.out_dir, 'design.json'), 'w', encoding='utf-8') as f:
        json.dump(design, f, indent=2)

    print(json.dumps({
        'partition': dict(tally),
        'refused_pop_ge300': refused_pop, 'passed_pop_ge300': len(arms['passed']),
        'pair_capacity': total_cap,
        'pct_matchable': round(100 * total_cap / refused_pop, 1),
        'cells_used': len(alloc),
        'rows_to_score': len(sample), 'noise_control_rows': len(dups),
        'weight_range': [round(min(w.values()), 3), round(max(w.values()), 3)],
        'sampled_stored_score_mean': {
            arm: round(statistics.mean([r['stored_score'] for _, a, r in sample if a == arm]), 3)
            for arm in ('refused', 'passed')},
        'sampled_median_len': {
            arm: int(statistics.median([r['content_len'] for _, a, r in sample if a == arm]))
            for arm in ('refused', 'passed')},
        'out_dir': args.out_dir,
    }, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
