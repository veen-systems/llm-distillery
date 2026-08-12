#!/usr/bin/env python3
"""Pre- vs post-enrichment score delta, step 1: draw the pilot from the paired index.

Owner-assigned 2026-08-12. Decides whether NexusMind#310 ("~15.8% of the corpus is
scored on an RSS blurb rather than a body") is a compute story or a quality story,
and feeds ovr.news#312's ordering argument.

The measurement is possible at all because NexusMind persists `original_content`
top-level on every row where pre-scoring enrichment actually replaced the body
(`src/enrichment/article_fetcher.py:821`). ABSENCE means no replacement happened --
the opposite convention to `resolved_url`, so absent must never be read as unknown.

Why the PRE-scoring path and not the post-scoring one: `pre_enrich` does no
scoring and no `min_score` filtering (verified in its docstring on sadalsuud,
`article_fetcher.py:1081`), so this population is UNGATED. The post-scoring
`enrich_articles` path only considers articles that already cleared `min_score` on
the stub, which makes it structurally blind to the harm #310 alleges -- an article
that scored low BECAUSE it was scored on a blurb was never enriched and never got
a second look. It is also tiny: 3 rows across the last 40 cycle files.

Two exclusions this design cannot fix, both measured rather than assumed:

- **Google News is 0.0% of the paired population** (0 of 122,557). Per NM#310 the
  GN redirect never resolves, so there is no enriched body to compare a GN stub
  against -- absent by construction, not by sampling. Extending any result here to
  GN's ~25.7% of the corpus requires assuming GN stubs behave like these stubs,
  and they are shorter (median 89 vs 160 chars). The delta is therefore reported
  AGAINST STUB LENGTH, so the extrapolation has a slope under it instead of an
  assumption.
- `original_content` is retained for **6 days** (2026-08-07..08-12 at time of
  writing), not the whole archive. This is a recent-window measurement.

Usage:
  PYTHONPATH=. python3 scripts/research/enrich_delta_sample.py \
      --index <index.jsonl> --out-dir <scratch> [--per-lens 50]
"""
import argparse
import collections
import json
import os
import random
import statistics
import sys

# Stub-length bands. The 300 boundary is the labelling floor (#93); the 150 split
# separates headline echoes from short blurbs, which matters because the GN
# population this cannot reach sits at median 89.
BANDS = [(0, 150), (150, 300), (300, 600), (600, 10 ** 9)]
BAND_NAMES = ['0-150', '150-300', '300-600', '600+']


def band_of(n):
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= n < hi:
            return BAND_NAMES[i]
    return BAND_NAMES[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--per-lens', type=int, default=50,
                    help='units per lens; the pilot is per-lens because each '
                         'filter is a separate model and the reproduction control '
                         'has to hold per model, not pooled')
    ap.add_argument('--seed', type=int, default=20260812)
    args = ap.parse_args()

    rows = []
    for line in open(args.index, encoding='utf-8'):
        line = line.strip()
        if line:
            rows.append(json.loads(line))

    # Every unit must carry production's own post-enrichment score, or the
    # reproduction control -- the only thing that validates this instrument
    # against production -- cannot be computed for it.
    missing_prod = [r for r in rows if r.get('prod_raw') is None]
    if missing_prod:
        print(f'WARNING: dropping {len(missing_prod)} units with no persisted '
              f'raw_weighted_average; the control needs it.', file=sys.stderr)
    rows = [r for r in rows if r.get('prod_raw') is not None]

    gn = sum(1 for r in rows if r.get('gn'))
    by_lens = collections.defaultdict(list)
    for r in rows:
        r['band'] = band_of(r['stub_len'])
        by_lens[r['lens']].append(r)

    rng = random.Random(args.seed)
    sample = []
    alloc_report = {}
    for lens in sorted(by_lens):
        pool = by_lens[lens]
        bands = collections.defaultdict(list)
        for r in pool:
            bands[r['band']].append(r)
        # Proportional to the lens's own band mass, so the pilot mirrors what the
        # filter actually sees rather than an even spread across bands that do not
        # exist in equal size.
        total = len(pool)
        want = {}
        for b in BAND_NAMES:
            if bands[b]:
                want[b] = max(1, round(args.per_lens * len(bands[b]) / total))
        # trim/pad to exactly per-lens
        while sum(want.values()) > args.per_lens:
            b = max(want, key=lambda k: (want[k], k))
            want[b] -= 1
            if want[b] == 0:
                del want[b]
        while sum(want.values()) < args.per_lens:
            b = max(want, key=lambda k: (len(bands[k]) - want[k], k))
            want[b] += 1
        for b, n in sorted(want.items()):
            n = min(n, len(bands[b]))
            for r in rng.sample(sorted(bands[b], key=lambda x: x['id']), n):
                sample.append(r)
        alloc_report[lens] = dict(sorted(want.items()))

    design = {
        'purpose': 'pre- vs post-enrichment score delta (NM#310, ovr#312)',
        'population': {
            'units_total': len(rows),
            'unique_articles': len(set(r['id'] for r in rows)),
            'google_news_units': gn,
            'google_news_pct': round(100 * gn / len(rows), 2) if rows else None,
            'date_range': [min(r['cd'] for r in rows if r.get('cd')),
                           max(r['cd'] for r in rows if r.get('cd'))],
            'stub_len_median': int(statistics.median([r['stub_len'] for r in rows])),
            'body_len_median': int(statistics.median([r['body_len'] for r in rows])),
            'stub_under_300_pct': round(
                100 * sum(1 for r in rows if r['stub_len'] < 300) / len(rows), 1),
            'by_lens': {k: len(v) for k, v in sorted(by_lens.items())},
            'dropped_no_prod_score': len(missing_prod),
        },
        'exclusions': {
            'google_news': 'absent BY CONSTRUCTION (0 units) — NM#310, the redirect '
                           'never resolves so no enriched body exists to pair against',
            'original_content_retention': 'about 6 days; this is a recent-window '
                                          'measurement, not an archive-wide one',
        },
        'bands': BAND_NAMES,
        'per_lens': args.per_lens,
        'seed': args.seed,
        'allocation': alloc_report,
        'units': [{'id': r['id'], 'lens': r['lens'], 'band': r['band'],
                   'stub_len': r['stub_len'], 'body_len': r['body_len'],
                   'prod_raw': r['prod_raw'], 'prod_norm': r.get('prod_norm'),
                   'stage': r.get('stage'), 'ver': r.get('ver'),
                   'src': r.get('src'), 'lang': r.get('lang'), 'cd': r.get('cd')}
                  for r in sample],
    }

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, 'pilot_design.json'), 'w', encoding='utf-8') as f:
        json.dump(design, f, indent=2)
    # The id list pass 2 fetches texts for. Article text never enters this repo (#97).
    with open(os.path.join(args.out_dir, 'pilot_ids.txt'), 'w', encoding='utf-8') as f:
        for r in sample:
            f.write(f"{r['lens']}\t{r['id']}\n")

    print(json.dumps({k: v for k, v in design.items()
                      if k not in ('units',)}, indent=2))
    print(f'\nsampled units: {len(sample)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
