#!/usr/bin/env python3
"""Pre- vs post-enrichment score delta, step 2: score both texts. Runs on ONE box.

For every sampled (article, lens) unit this produces four numbers:

  prod_raw      production's persisted `raw_weighted_average` on the POST text
  body_batch    this box's score_batch() on the POST text   <- reproduction control
  body_single   this box's score_article() on the POST text
  stub_single   this box's score_article() on the PRE text  <- the measurement

Why two code paths rather than one. Production scores via `score_batch`, so the
reproduction control must use `score_batch` or it is not comparing like with like.
But `score_batch` is batch-composition dependent -- that is #95, up to |0.16| from
composition alone -- and the stub/body delta should not inherit that noise.
`score_article` pads every input to MAX_TOKEN_LENGTH, so it is composition-free
and is the right instrument for the paired delta. Both are reported; neither is
allowed to stand in for the other.

`score_batch` is additionally run TWICE under different orderings, so this
population's own composition floor is MEASURED rather than inherited from #95's
0.16 (which was measured on `uplifting v7` held-out rows -- a different population
and a different length regime, and reaching for it here is the exact
wrong-instrument error `memory/score-batch-shape-noise.md` exists to prevent).

Prefilters are skipped, matching production: the GPU scorer builds every scorer
with `use_prefilter=False` and calls `score_batch(skip_prefilter=True)` (NM#284).
Not skipping them would drop precisely the short stubs this measures.

The per-filter `short_content.cap` state is printed at the start of every run. It
is `{}` on all six filters today, but it is a config-gated cap that acts on SHORT
CONTENT, which is exactly this measurement's treatment variable -- so its state is
proven per run, never assumed.

Usage (on b650-gpu, venv-prodparity):
  PYTHONPATH=. python3 scripts/research/enrich_delta_score.py \
      --design <dir>/pilot_design.json --texts <dir>/texts.jsonl \
      --out <dir>/scored.jsonl [--device cpu]
"""
import argparse
import collections
import importlib
import inspect
import json
import os
import random
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# lens name in NexusMind output -> (package dir, inference module)
LENS = {
    'uplifting': ('filters/uplifting/v7', 'filters.uplifting.v7.inference'),
    'investment_risk': ('filters/investment_risk/v6', 'filters.investment_risk.v6.inference'),
    'cultural_discovery': ('filters/cultural_discovery/v5', 'filters.cultural_discovery.v5.inference'),
    'belonging': ('filters/belonging/v1', 'filters.belonging.v1.inference'),
    'nature_recovery': ('filters/nature_recovery/v4', 'filters.nature_recovery.v4.inference'),
    'solutions': ('filters/solutions/v6', 'filters.solutions.v6.inference'),
}


def short_content_cfg(pkg_dir):
    cfg = yaml.safe_load(open(os.path.join(REPO, pkg_dir, 'config.yaml'), encoding='utf-8'))
    return (cfg.get('scoring') or {}).get('short_content') or cfg.get('short_content') or {}


def load_scorer(lens, device):
    pkg_dir, mod_path = LENS[lens]
    mod = importlib.import_module(mod_path)
    from filters.common.filter_base_scorer import FilterBaseScorer
    cands = [o for _, o in vars(mod).items()
             if inspect.isclass(o) and issubclass(o, FilterBaseScorer)
             and o.__module__ == mod.__name__]
    if not cands:
        cands = [o for _, o in vars(mod).items()
                 if inspect.isclass(o) and issubclass(o, FilterBaseScorer)
                 and o is not FilterBaseScorer]
    if not cands:
        raise RuntimeError(f'no scorer class in {mod_path}')
    kwargs = {'use_prefilter': False}
    if device:
        kwargs['device'] = device
    return cands[0](**kwargs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--design', required=True)
    ap.add_argument('--texts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--device', default=None, help='cpu forces the production-parity path')
    ap.add_argument('--lens', action='append', help='restrict to these lenses')
    ap.add_argument('--seed', type=int, default=20260812)
    args = ap.parse_args()

    design = json.load(open(args.design, encoding='utf-8'))
    texts = {}
    for line in open(args.texts, encoding='utf-8'):
        line = line.strip()
        if line:
            r = json.loads(line)
            texts[r['id']] = r

    units = design['units']
    if args.lens:
        units = [u for u in units if u['lens'] in args.lens]
    by_lens = collections.defaultdict(list)
    missing = 0
    for u in units:
        if u['id'] not in texts:
            missing += 1
            continue
        by_lens[u['lens']].append(u)
    if missing:
        print(f'WARNING: {missing} units have no text and are skipped', file=sys.stderr)

    out = open(args.out, 'w', encoding='utf-8')
    rng = random.Random(args.seed)
    for lens in sorted(by_lens):
        us = by_lens[lens]
        pkg_dir, _ = LENS[lens]
        sc_cfg = short_content_cfg(pkg_dir)
        print(f'=== {lens}: {len(us)} units | short_content cap config: {sc_cfg} '
              f'| {"CAP ACTIVE — the treatment variable is capped, read results with care" if sc_cfg else "no cap"}',
              flush=True)
        scorer = load_scorer(lens, args.device)

        def art(u, which):
            t = texts[u['id']]
            return {'title': t.get('title', ''),
                    'content': t['stub'] if which == 'stub' else t['body'],
                    'url': t.get('url', ''), 'source': t.get('source', ''),
                    'description': ''}

        # Reproduction control: production's code path, two different orderings so
        # this population's own composition floor is measured.
        order_a = list(range(len(us)))
        order_b = order_a[:]
        rng.shuffle(order_b)
        batch_a = scorer.score_batch([art(us[i], 'body') for i in order_a],
                                     skip_prefilter=True)
        batch_b = scorer.score_batch([art(us[i], 'body') for i in order_b],
                                     skip_prefilter=True)
        a_by_idx = {i: batch_a[pos]['weighted_average'] for pos, i in enumerate(order_a)}
        b_by_idx = {i: batch_b[pos]['weighted_average'] for pos, i in enumerate(order_b)}

        for i, u in enumerate(us):
            body_single = scorer.score_article(art(u, 'body'), skip_prefilter=True)
            # An EMPTY pre-enrichment body is its own population, not a zero-length
            # stub. `_validate_article` rejects empty content and always has -- "empty
            # is not short" (#93) -- so production could not have scored these either.
            # For them enrichment is not improving a score, it is the difference
            # between the article existing and being dropped. Scoring them as if the
            # stub were text would invent a counterfactual that the pipeline has no
            # path to. 7.71% of units (9,455 of 122,557; 1,582 articles).
            stub_text = (texts[u['id']]['stub'] or '').strip()
            if not stub_text:
                stub_single = {'weighted_average': None, 'scores': None,
                               'unscoreable': 'empty pre-enrichment content'}
            else:
                stub_single = scorer.score_article(art(u, 'stub'), skip_prefilter=True)
            out.write(json.dumps({
                'id': u['id'], 'lens': lens, 'band': u['band'],
                'stub_len': u['stub_len'], 'body_len': u['body_len'],
                'src': u.get('src'), 'lang': u.get('lang'),
                'prod_raw': u['prod_raw'], 'prod_norm': u.get('prod_norm'),
                'prod_stage': u.get('stage'), 'prod_ver': u.get('ver'),
                'body_batch_a': a_by_idx[i], 'body_batch_b': b_by_idx[i],
                'body_single': body_single['weighted_average'],
                'stub_single': stub_single['weighted_average'],
                'stub_unscoreable': stub_single.get('unscoreable'),
                'body_single_dims': body_single.get('scores'),
                'stub_single_dims': stub_single.get('scores'),
                'body_gatekeeper': body_single.get('gatekeeper_applied'),
                'stub_gatekeeper': stub_single.get('gatekeeper_applied'),
                'short_content_cap_cfg': sc_cfg,
                'device': args.device or 'default',
            }, ensure_ascii=False) + '\n')
            out.flush()
        del scorer
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
    out.close()
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
