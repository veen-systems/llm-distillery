#!/usr/bin/env python3
"""solutions v6: score the test split through the student and persist per-dimension
predictions next to the oracle labels.

Companion to solutions_v6_dim_fidelity_report.py, which reads the output. Split in
two because scoring needs a GPU box and the analysis does not.

WHY. `community_practice_strength` is zero on 83.1% of on-topic articles, and the
labels being sound says nothing about whether the STUDENT reproduces the
dimension. If the student predicts ~0 everywhere, the dimension is dead in
production however good the corpus is -- which is the real form of the question.

ANSWER (2026-08-11): the student learns it BETTER than most dimensions
conditional on presence. Details in docs/evidence/2026-08-11-solutions-v6-
community-practice-dimension.md.

CROSS-BOX CAVEAT (memory/b650-gpu.md). The Gemma-3-1B student is NOT probe-clean
across boxes: b650 vs gpu-server ran to |0.2008| on uplifting v7, above the #95
0.16 floor. That is acceptable for "does this dimension carry signal at all",
which is not a threshold question. It is NOT acceptable for quoting any number
here as production's -- re-run scripts/verification/box_parity.py at the
threshold you care about first.

Usage (on the GPU box, from the repo root):
  PYTHONPATH=. TQDM_DISABLE=1 HF_HUB_DISABLE_PROGRESS_BARS=1 \
    venv-prodparity/bin/python scripts/research/solutions_v6_student_dim_fidelity.py
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from filters.solutions.v6.inference import SolutionsScorer  # noqa: E402

DIMS = ['solution_concreteness', 'systemic_impact', 'evidence_strength',
        'governance_intervention_strength', 'community_practice_strength',
        'equity_access', 'economic_viability']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', default=str(REPO / 'datasets/training/solutions_v6/test.jsonl'))
    ap.add_argument('--output', default=str(REPO / 'datasets/scored/solutions_v6_test_predictions.jsonl'))
    ap.add_argument('--limit', type=int, default=None,
                    help='smoke-test first; the scorer load is the slow part')
    args = ap.parse_args()

    rows = []
    for line in open(args.test, encoding='utf-8'):
        r = json.loads(line)
        lab = r['labels']
        if isinstance(lab, str):
            lab = json.loads(lab)
        if len(lab) != 7:
            continue
        r['lab'] = [float(x) for x in lab]
        rows.append(r)
    if args.limit:
        rows = rows[:args.limit]
    print(f'test rows: {len(rows):,}', flush=True)

    # use_prefilter=False: these rows already passed at labelling time, and the
    # per-lens prefilter does not run in the production scoring path anyway
    # (NM#284) -- running it here would measure a stage production skips.
    print('loading student...', flush=True)
    scorer = SolutionsScorer(use_prefilter=False)
    print('loaded, scoring...', flush=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    ok = err = 0
    with open(out, 'w', encoding='utf-8') as fo:
        for i, r in enumerate(rows, 1):
            try:
                res = scorer.score_article({'title': r.get('title', ''),
                                            'content': r.get('content', ''),
                                            'url': r.get('url', '')})
                sd = {d: float(res['scores'][d]) for d in DIMS}
                fo.write(json.dumps({
                    'id': r.get('id'),
                    'title': r.get('title', '')[:160],
                    'oracle': dict(zip(DIMS, r['lab'])),
                    'student': {d: round(sd[d], 3) for d in DIMS},
                    'student_wavg': round(float(res.get('weighted_average') or 0.0), 3),
                }, ensure_ascii=False) + '\n')
                ok += 1
                if i % 100 == 0:
                    print(f'  {i}/{len(rows)}', flush=True)
            except Exception as e:                       # noqa: BLE001 - report and continue
                err += 1
                if err <= 5:
                    print(f'  ERROR {r.get("id", "?")}: {e}', flush=True)

    print(f'done: {ok} ok, {err} errors -> {out}', flush=True)


if __name__ == '__main__':
    main()
