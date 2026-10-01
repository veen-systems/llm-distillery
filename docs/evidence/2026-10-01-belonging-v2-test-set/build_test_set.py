"""Join labels.tsv with fetched rows (fetch_rows.py output) into the belonging v2 test set.

    python3 docs/evidence/2026-10-01-belonging-v2-test-set/build_test_set.py rows.jsonl

Writes two files:
  datasets/belonging_v2_test/test_set_full.jsonl   full text, gitignored — what the oracle reads
  docs/evidence/2026-10-01-belonging-v2-test-set/test_set.jsonl
                                                   300-char excerpt, committed (public repo,
                                                   datasets/adverse/README.md § excerpt rule)
Raises on any label without a row or row without a label."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
labels = {}
for line in list(open(os.path.join(HERE, 'labels.tsv')))[1:]:
    stratum, url, label, basis, reason, title = line.rstrip('\n').split('\t')
    if label not in ('P', 'F', 'B'):
        raise ValueError(f'bad label {label!r} for {url}')
    if url in labels:
        raise ValueError(f'duplicate url {url}')
    labels[url] = dict(stratum=stratum, label=label, label_basis=basis, label_reason=reason)
rows = {}
for line in open(sys.argv[1]):
    r = json.loads(line)
    rows[r['url']] = r
if set(rows) != set(labels):
    raise SystemExit(f'unlabelled rows: {sorted(set(rows) - set(labels))}; '
                     f'rows missing: {sorted(set(labels) - set(rows))}')

out_dir = os.path.join(ROOT, 'datasets', 'belonging_v2_test')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'test_set_full.jsonl'), 'w') as full, \
        open(os.path.join(HERE, 'test_set.jsonl'), 'w') as pub:
    for url in labels:  # labels.tsv order
        r = {**rows[url], **labels[url]}
        content = r.get('content') or ''
        r['content_length'] = len(content)
        full.write(json.dumps(r, ensure_ascii=False) + '\n')
        if len(content) > 300:
            r['content'], r['content_excerpt'] = content[:300], True
        pub.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'{len(labels)} rows -> {out_dir}/test_set_full.jsonl and test_set.jsonl')
