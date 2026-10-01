"""Fetch the `v1_heldout_top` rows of labels.tsv. Run ON b650-gpu:

    python3 fetch_v1_heldout.py labels.tsv > rows_v1.jsonl

Source: belonging v1's held-out splits, ~/llm-distillery/datasets/training/belonging_v1/{test,val}.jsonl
(Gemini Flash labels; 1,476 rows). Candidates were the 45 rows with the highest v1 ORACLE weighted
average (BaseBelongingScorer weights + community_fabric gatekeeper), all >= 6.15. Only the 11 read as
clear P under the #130 ruling were kept; the rest are not in the set. Because the rows come from v1's own
held-out data, they were never trained on by v1. ⛔ They must also be excluded from any v2 relabel/training draw.
Raises if a labelled url is missing."""
import json, os, sys

want = {l.split('\t')[1] for l in list(open(sys.argv[1]))[1:] if l.startswith('v1_heldout_top\t')}
W = [0.25, 0.25, 0.10, 0.15, 0.15, 0.10]
found = {}
for split in ('test', 'val'):
    for line in open(os.path.expanduser(f'~/llm-distillery/datasets/training/belonging_v1/{split}.jsonl')):
        r = json.loads(line)
        if r.get('url') in want and r['url'] not in found:
            s = r['labels']
            wa = sum(a * b for a, b in zip(s, W))
            if s[1] < 3.0 and wa > 3.42:
                wa = 3.42
            found[r['url']] = dict(id=r['id'], url=r['url'], title=r.get('title'), source=None,
                                   content=r.get('content'), observed_raw=None, observed_stage=None,
                                   observed_harm=None, v1_oracle_wa_training_label=wa,
                                   origin=f'belonging_v1/{split}.jsonl')
missing = want - set(found)
if missing:
    raise SystemExit(f'{len(missing)} labelled urls not found: {sorted(missing)}')
for u in sorted(found):
    print(json.dumps(found[u], ensure_ascii=False))
