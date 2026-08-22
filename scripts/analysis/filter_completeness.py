"""Check filter package completeness across all filters."""
import os

def list_files(d):
    files = set()
    for root, dirs, fnames in os.walk(d):
        dirs[:] = [x for x in dirs if x != '__pycache__']
        for f in fnames:
            rel = os.path.relpath(os.path.join(root, f), d).replace(os.sep, '/')
            files.add(rel)
    return files

filters = {
    'belonging v1': 'filters/belonging/v1',
    'uplifting v6': 'filters/uplifting/v6',
    'sust_tech v3': 'filters/sustainability_technology/v3',
    'inv-risk v6': 'filters/investment_risk/v6',
    'cult-disc v4': 'filters/cultural_discovery/v4',
}

all_files = {}
for name, path in filters.items():
    all_files[name] = list_files(path)

core = [
    'base_scorer.py', 'inference.py', 'inference_hub.py', 'inference_hybrid.py',
    'config.yaml', 'calibration.json',
    # 'prefilter.py' REMOVED 2026-08-21 (owner ruling; memory/filter-doc-standard.md).
    # A per-lens keyword prefilter is optional and omission is the default for new
    # filters. Leaving it in `core` made this script -- the very tool the v8 package
    # parity gate invokes -- report a correctly-built v8 as INCOMPLETE.
    # NB: nature_recovery v4 and cultural_discovery v5 still ship one; that is
    # legacy, not a requirement, and copying from them re-introduces it.
    'training_history.json', 'training_metadata.json',
    'model/adapter_config.json', 'model/adapter_model.safetensors',
    'model/tokenizer.json', 'model/tokenizer_config.json',
    'probe/embedding_probe_e5small.pkl',
]

print(f'{"File":>45s}', end='')
for name in filters:
    print(f'  {name[:10]:>10s}', end='')
print()
print('-' * 105)

for f in core:
    print(f'{f:>45s}', end='')
    for name in filters:
        has = f in all_files[name]
        marker = 'YES' if has else '---'
        print(f'  {marker:>10s}', end='')
    print()

# Show belonging-specific extras
print()
print('Belonging-only files:')
prod_common = set()
for name in list(filters.keys())[1:]:
    prod_common |= all_files[name]
for f in sorted(all_files['belonging v1'] - prod_common):
    print(f'  {f}')
