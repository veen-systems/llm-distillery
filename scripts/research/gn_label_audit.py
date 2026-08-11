#!/usr/bin/env python3
"""GN / short-content share and label distribution across filter training splits.

Instrument, identical on every box:
  GN    = 'news.google.com' in row['url']
  short = 0 < len(row['content']) < 300
  label = mean(row['labels'])   (per-dimension oracle scores, 0-10)
Emits one JSON blob per split so the two hosts' output can be merged verbatim.
"""
import json, os, sys, glob
from statistics import mean

root = sys.argv[1]
out = []
for d in sorted(glob.glob(os.path.join(root, '*'))):
    if not os.path.isdir(d):
        continue
    name = os.path.basename(d)
    for split in ('train', 'val', 'test'):
        p = os.path.join(d, split + '.jsonl')
        if not os.path.exists(p):
            continue
        groups = {'gn': [], 'short_nongn': [], 'long': []}
        n = bad = 0
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                bad += 1
                continue
            labs = r.get('labels')
            if not isinstance(labs, list) or not labs:
                bad += 1
                continue
            try:
                m = mean(float(x) for x in labs)
            except Exception:
                bad += 1
                continue
            n += 1
            c = len(r.get('content') or '')
            u = r.get('url') or ''
            if 'news.google.com' in u:
                groups['gn'].append(m)
            elif 0 < c < 300:
                groups['short_nongn'].append(m)
            else:
                groups['long'].append(m)
        rec = {'filter': name, 'split': split, 'n': n, 'unparsed': bad}
        for g, v in groups.items():
            rec[g] = {
                'n': len(v),
                'share': round(100 * len(v) / n, 2) if n else None,
                'mean_label': round(mean(v), 4) if v else None,
                'pct_all_zero': round(100 * sum(1 for x in v if x == 0.0) / len(v), 1) if v else None,
                'max_label': round(max(v), 2) if v else None,
            }
        out.append(rec)
print(json.dumps(out))
