"""A/B the ORACLE gate across the #93 split.

Old (HEAD):  prefilter.apply_filter(article)[0]          — length was inside
New (WT):    make_oracle_prefilter(prefilter_obj)(article) — length hoisted out

The claim under test: the oracle path's *boolean* verdict is unchanged for
every article, for every production filter. Reported separately: how much the
SCORING path (apply_filter alone) opens up, which is the intended change.

Usage: python3 ab_gate.py <repo_root> <corpus.jsonl> old|new
Emits one JSON line: {filter: {"gate": [...], "applyfilter": [...]}} as
0/1 strings, so the two runs can be diffed exactly.
"""
import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
corpus = Path(sys.argv[2])
mode = sys.argv[3]

sys.path.insert(0, str(root))

FILTERS = [
    "filters/nature_recovery/v4/prefilter.py",
    "filters/solutions/v6/prefilter.py",
    "filters/uplifting/v7/prefilter.py",
    "filters/belonging/v1/prefilter.py",
    "filters/investment_risk/v6/prefilter.py",
    "filters/cultural_discovery/v5/prefilter.py",
]

from filters.common.base_prefilter import BasePreFilter  # noqa: E402

if mode == "new":
    from ground_truth.batch_scorer import make_oracle_prefilter  # noqa: E402


def load(rel):
    path = root / rel
    spec = importlib.util.spec_from_file_location(f"pf_{rel.replace('/', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cands = [
        o for _n, o in vars(mod).items()
        if isinstance(o, type) and issubclass(o, BasePreFilter)
        and o.__module__ == mod.__name__
    ]
    return cands[0]()


articles = []
for line in corpus.open(encoding="utf-8"):
    try:
        articles.append(json.loads(line))
    except json.JSONDecodeError:
        continue

out = {}
for rel in FILTERS:
    pf = load(rel)
    if mode == "old":
        # At HEAD the oracle gate WAS apply_filter alone.
        gate = lambda a: pf.apply_filter(a)[0]
    else:
        gate = make_oracle_prefilter(pf)
    out[rel] = {
        "gate": "".join("1" if gate(a) else "0" for a in articles),
        "applyfilter": "".join("1" if pf.apply_filter(a)[0] else "0" for a in articles),
    }

print(json.dumps({"n": len(articles), "filters": out}))
