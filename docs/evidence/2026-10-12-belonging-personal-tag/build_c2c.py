"""Build belonging c2c: c2b's splits with every `personal`-tagged row's targets scaled to just above the op-point.

Owner, 2026-10-12: no paid oracle; tag the training data on b650 and lower the personal rows ("just above
op-point"). Tags: qwen3.8:27b on b650 (arm 3 of PREREGISTRATION.md, which passed rule 2), pulled to situla at
~/lab/llm-distillery/experiments/2026-10-12-belonging-c2c/focus-tag-train/ (first pulled into the lab inbox, moved 2026-10-13
by `lab.py move`; same bytes, see MANIFEST.json). Every row with weighted score >= 4.0 was tagged.

A personal row with weighted score > TARGET has ALL six labels multiplied by TARGET / weighted, so its profile
keeps its shape and its weighted score lands on TARGET. Nothing else changes; row order and ids are c2b's.
Run from the repo root: python3 docs/evidence/2026-10-12-belonging-personal-tag/build_c2c.py
"""
import json, os, shutil
SRC, DST = "datasets/training/belonging_c2b", "datasets/training/belonging_c2c"
TAGS = os.path.expanduser("~/lab/llm-distillery/experiments/2026-10-12-belonging-c2c/focus-tag-train/out.jsonl")
TARGET = 4.4
W = dict(intergenerational_bonds=.25, community_fabric=.25, reciprocal_care=.10,
         rootedness=.15, purpose_beyond_self=.15, slow_presence=.10)   # filters/belonging/v3/config.yaml
assert abs(sum(W.values()) - 1) < 1e-9

tags = {}
for l in open(TAGS):
    t = json.loads(l)
    if t["focus"] not in ("personal", "group"):
        raise ValueError(f"untagged row {t['id']}: {t['focus']!r}")
    tags[t["id"]] = t["focus"]

if os.path.exists(DST):
    raise SystemExit(f"{DST} exists; refusing to overwrite")
os.makedirs(DST)
report = {"variant": "c2c", "from": SRC, "tags": TAGS, "target": TARGET, "splits": {}}
for sp in ("train", "val", "test"):
    n = scaled = tagged = 0
    with open(f"{DST}/{sp}.jsonl", "w") as f:
        for l in open(f"{SRC}/{sp}.jsonl"):
            r = json.loads(l); n += 1
            wa = sum(W[k] * x for k, x in zip(r["dimension_names"], r["labels"]))
            if wa >= 4.0:
                if r["id"] not in tags:
                    raise KeyError(f"row {r['id']} ({sp}, weighted {wa:.2f}) was never tagged")
                tagged += 1
                if tags[r["id"]] == "personal" and wa > TARGET:
                    r["labels"] = [round(x * TARGET / wa, 4) for x in r["labels"]]
                    scaled += 1
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report["splits"][sp] = {"rows": n, "tagged": tagged, "scaled": scaled}
shutil.copy(f"{SRC}/training_manifest.jsonl", f"{DST}/training_manifest.jsonl")
json.dump(report, open(f"{DST}/build_report.json", "w"), indent=1)
print(json.dumps(report["splits"]))
