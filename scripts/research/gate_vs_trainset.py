#!/usr/bin/env python3
"""What share of each DEPLOYED training set would today's oracle labelling gate refuse?

Runs the real gate -- ground_truth.batch_scorer.make_oracle_prefilter wrapped
around the filter package's own prefilter -- over the rows the model was actually
trained on. Blocking is attributed to the length floor vs the lens rules so the
two are never conflated (#93).
"""
import json, os, sys, glob, inspect, importlib
sys.path.insert(0, os.path.expanduser(sys.argv[1]))
from ground_truth.batch_scorer import make_oracle_prefilter
from filters.common.base_prefilter import BasePreFilter

TRAIN = os.path.expanduser(sys.argv[2])
# training dir name -> filter package path
PKG = {
    'solutions_v6': 'filters.solutions.v6.prefilter',
    'nature_recovery_v4': 'filters.nature_recovery.v4.prefilter',
    'uplifting_v7': 'filters.uplifting.v7.prefilter',
    'belonging_v1': 'filters.belonging.v1.prefilter',
    'investment_risk_v6': 'filters.investment_risk.v6.prefilter',
    'cultural-discovery_v5': 'filters.cultural_discovery.v5.prefilter',
}
out = []
for d in sorted(glob.glob(os.path.join(TRAIN, '*'))):
    name = os.path.basename(d)
    if name not in PKG:
        continue
    try:
        m = importlib.import_module(PKG[name])
    except Exception as e:
        out.append({'filter': name, 'error': f'import: {e}'}); continue
    cands = [o for n, o in vars(m).items()
             if inspect.isclass(o) and issubclass(o, BasePreFilter) and o is not BasePreFilter]
    if not cands:
        out.append({'filter': name, 'error': 'no prefilter class'}); continue
    try:
        pf = cands[0]()
    except Exception as e:
        out.append({'filter': name, 'error': f'init: {e}'}); continue
    gate = make_oracle_prefilter(pf)
    n = blocked = by_len = by_lens = gn_blocked = gn = 0
    for split in ('train', 'val', 'test'):
        p = os.path.join(d, split + '.jsonl')
        if not os.path.exists(p):
            continue
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            art = {'title': r.get('title', ''), 'content': r.get('content', ''),
                   'url': r.get('url', ''), 'source': '', 'description': ''}
            n += 1
            isgn = 'news.google.com' in (art['url'] or '')
            gn += isgn
            if gate(art):
                continue
            blocked += 1
            gn_blocked += isgn
            if not pf.check_content_length(art)[0]:
                by_len += 1
            else:
                by_lens += 1
    out.append({'filter': name, 'n': n, 'blocked': blocked,
                'pct_blocked': round(100 * blocked / n, 1) if n else None,
                'by_length': by_len, 'by_lens_rules': by_lens,
                'gn': gn, 'gn_blocked': gn_blocked,
                'cls': cands[0].__name__})
print(json.dumps(out))
