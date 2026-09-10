import json, os
from pathlib import Path
OBIT=Path.home()/"llm-distillery/filters/common/obituary_detector"
ids=lambda p:{json.loads(l)["id"] for l in open(p,encoding="utf-8") if l.strip()}
ho=ids(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl")
tr={v:ids(OBIT/"training/data"/f) for v,f in
    {"v3":"train_split_corpus.jsonl","v4":"v4b_train_seed.jsonl","v5":"v5_train_seed.jsonl"}.items()}
union=set().union(*tr.values())
print("heldout:",len(ho))
for v,s in tr.items(): print(f"  heldout rows in {v} training corpus: {len(ho&s)}")
print("  heldout rows in ANY training corpus:", len(ho&union))
print("  -> eval set:", len(ho-union), "| published uses 1529, i.e. excludes", len(ho)-1529)
