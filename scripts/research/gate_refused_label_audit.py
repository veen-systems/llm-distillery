#!/usr/bin/env python3
"""#105: do the rows today's labelling gate REFUSES carry different oracle labels
than the rows it passes?

#105 measured that `investment_risk v6` (51.6%) and `cultural_discovery v5`
(52.2%) were trained on corpora more than half of which today's gate refuses, and
left the load-bearing question open: are the LABELS wrong, or did the RULE merely
tighten? A retrain drops those rows either way, but the two readings have opposite
consequences -- one says the deployed model learned from bad labels, the other
says a retrain would lose good signal.

This answers it WITHOUT re-scoring anything. Every refused row already carries the
oracle label it was trained on. Comparing the label distribution of refused vs
passed rows is free, uses no oracle, and -- unlike a re-score -- does not run the
oracle outside its validated range, which is the instrument trap #105 flags and
that the 300-char floor exists to prevent.

Reading the output:

  refused rows score LOWER than passed  -> the gate and the labels AGREE. The gate
      refuses material the oracle also considered negative. A retrain loses little
      signal; the corpus is not contaminated, the rule just became redundant.

  refused rows score HIGHER than passed -> the labels on refused rows are inflated
      relative to the rest of the corpus. For LENGTH-refused rows this is the #92
      short-stub over-scoring signature, and it means the gate is right and the
      deployed model trained on bad labels.

  no difference -> the rule tightened on a dimension unrelated to label quality.

Blocking is attributed to the length floor vs the lens rules separately, because
the two filters fail for opposite reasons and only the length-refused half is
subject to the short-content instrument caveat (#93).

Usage:
  PYTHONPATH=. python3 scripts/research/gate_refused_label_audit.py <splits-dir>
"""
import glob
import importlib
import inspect
import json
import os
import statistics
import sys

import yaml

from filters.common.base_prefilter import BasePreFilter
from ground_truth.batch_scorer import make_oracle_prefilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# training dir name -> (prefilter module, filter package dir)
PKG = {
    'solutions_v6': ('filters.solutions.v6.prefilter', 'filters/solutions/v6'),
    'nature_recovery_v4': ('filters.nature_recovery.v4.prefilter', 'filters/nature_recovery/v4'),
    'uplifting_v7': ('filters.uplifting.v7.prefilter', 'filters/uplifting/v7'),
    'belonging_v1': ('filters.belonging.v1.prefilter', 'filters/belonging/v1'),
    'investment_risk_v6': ('filters.investment_risk.v6.prefilter', 'filters/investment_risk/v6'),
    'cultural-discovery_v5': ('filters.cultural_discovery.v5.prefilter', 'filters/cultural_discovery/v5'),
}


def load_weights(pkg_dir):
    """dimension name -> weight, from the filter's own config.yaml."""
    cfg = yaml.safe_load(open(os.path.join(REPO, pkg_dir, 'config.yaml'), encoding='utf-8'))
    dims = (cfg.get('scoring') or {}).get('dimensions') or cfg.get('dimensions') or {}
    out = {}
    if isinstance(dims, dict):
        for name, spec in dims.items():
            if isinstance(spec, dict) and spec.get('weight') is not None:
                out[name] = float(spec['weight'])
    return out


def op_point(pkg_dir):
    """The RUNTIME operating point: base_scorer.py TIER_THRESHOLDS, not config.yaml.

    config.yaml scoring.tiers is documentation -- reading it here would repeat the
    exact confusion this repo's Hard Constraints warn about.
    """
    path = os.path.join(REPO, pkg_dir, 'base_scorer.py')
    src = open(path, encoding='utf-8').read()
    ns = {}
    marker = 'TIER_THRESHOLDS = ['
    i = src.index(marker)
    j = src.index(']', i)
    exec('TIER_THRESHOLDS = ' + src[i + len(marker) - 1:j + 1], ns)
    for name, thr, *_ in ns['TIER_THRESHOLDS']:
        if name == 'medium':
            return float(thr)
    raise ValueError('no medium threshold in ' + path)


def weighted(labels, dim_names, weights):
    """Weighted average in the dimension order the row itself declares."""
    if not labels or not dim_names or len(labels) != len(dim_names):
        return None
    num = den = 0.0
    for v, d in zip(labels, dim_names):
        w = weights.get(d)
        if w is None:
            return None
        num += float(v) * w
        den += w
    return num / den if den else None


def describe(rows):
    if not rows:
        return {'n': 0}
    scores = [r['score'] for r in rows]
    lens_ = [r['len'] for r in rows]
    return {
        'n': len(rows),
        'mean_label': round(statistics.mean(scores), 3),
        'median_label': round(statistics.median(scores), 3),
        'pct_at_or_above_op': round(100 * sum(1 for s in scores if s >= rows[0]['op']) / len(scores), 1),
        'median_content_len': int(statistics.median(lens_)),
    }


def main():
    splits_dir = os.path.expanduser(sys.argv[1])
    report = []
    for d in sorted(glob.glob(os.path.join(splits_dir, '*'))):
        name = os.path.basename(d)
        if name not in PKG:
            continue
        mod_path, pkg_dir = PKG[name]
        mod = importlib.import_module(mod_path)
        cands = [o for _, o in vars(mod).items()
                 if inspect.isclass(o) and issubclass(o, BasePreFilter) and o is not BasePreFilter]
        pf = cands[0]()
        gate = make_oracle_prefilter(pf)
        weights = load_weights(pkg_dir)
        op = op_point(pkg_dir)

        groups = {'passed': [], 'refused_length': [], 'refused_lens': []}
        unscorable = 0
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
                s = weighted(r.get('labels'), r.get('dimension_names'), weights)
                if s is None:
                    unscorable += 1
                    continue
                rec = {'score': s, 'len': len(art['content'] or ''), 'op': op}
                if gate(art):
                    groups['passed'].append(rec)
                elif not pf.check_content_length(art)[0]:
                    groups['refused_length'].append(rec)
                else:
                    groups['refused_lens'].append(rec)

        report.append({
            'filter': name,
            'op_point_runtime': op,
            'weights_found': len(weights),
            'unscorable_rows': unscorable,
            'groups': {k: describe(v) for k, v in groups.items()},
        })
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
