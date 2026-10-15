"""Build belonging c2d: c2c's idea (personal-tagged rows lowered to just above the op-point), made cap-aware.

c2c (../2026-10-12-belonging-personal-tag/build_c2c.py) scaled all six labels by TARGET / weighted. That ignored the
community_fabric gatekeeper (filters/belonging/v3/base_scorer.py: community_fabric < 3.0 caps the score at 3.42), so
11 of its 42 scaled rows were trained to an EFFECTIVE 3.42 (blocked), not 4.4 (EXP-048, H-BB8). Owner, 2026-10-14:
"prepare now, judge on H".

c2d: a personal-tagged row whose EFFECTIVE score (weighted, then the gatekeeper cap) exceeds TARGET gets
  community_fabric' = max(3.0, community_fabric * TARGET / weighted)       (never below the gatekeeper minimum)
  the other five labels scaled by one factor k, chosen so the weighted score lands on TARGET.
Every changed row is asserted: community_fabric' >= 3.0, 0 < k <= 1, the effective score of the written
(rounded) labels is TARGET within 0.001, and it is not above the row's effective score before. Rows already at or below TARGET effective are untouched, as are group rows.
Same tags as c2c (qwen on b650, lab experiments/2026-10-12-belonging-c2c/focus-tag-train/out.jsonl).

    python3 docs/evidence/2026-10-15-belonging-c2d/build_c2d.py --check   # report only, writes nothing
    python3 docs/evidence/2026-10-15-belonging-c2d/build_c2d.py           # writes datasets/training/belonging_c2d
"""
import json, os, shutil, sys

SRC, DST = "datasets/training/belonging_c2b", "datasets/training/belonging_c2d"
TAGS = os.path.expanduser("~/ld-lab/experiments/2026-10-12-belonging-c2c/focus-tag-train/out.jsonl")
TARGET, GK, GK_MIN, GK_CAP = 4.4, "community_fabric", 3.0, 3.42
W = dict(intergenerational_bonds=.25, community_fabric=.25, reciprocal_care=.10,
         rootedness=.15, purpose_beyond_self=.15, slow_presence=.10)   # filters/belonging/v3/config.yaml
assert abs(sum(W.values()) - 1) < 1e-9
CHECK = "--check" in sys.argv


def weighted(d):
    return sum(W[k] * x for k, x in d.items())


def effective(d):
    wa = weighted(d)
    return min(wa, GK_CAP) if d[GK] < GK_MIN else wa


tags = {}
for l in open(TAGS):
    t = json.loads(l)
    if t["focus"] not in ("personal", "group"):
        raise ValueError(f"untagged row {t['id']}: {t['focus']!r}")
    tags[t["id"]] = t["focus"]

if not CHECK:
    if os.path.exists(DST):
        raise SystemExit(f"{DST} exists; refusing to overwrite")
    os.makedirs(DST)
report = {"variant": "c2d", "from": SRC, "tags": TAGS, "target": TARGET, "splits": {}, "changed": []}
for sp in ("train", "val", "test"):
    n = tagged = changed = cf_floored = 0
    out = []
    for l in open(f"{SRC}/{sp}.jsonl"):
        r = json.loads(l); n += 1
        d = dict(zip(r["dimension_names"], r["labels"]))
        if weighted(d) >= 4.0:                          # c2c's tagging rule: every row with weighted >= 4.0 was tagged
            if r["id"] not in tags:
                raise KeyError(f"row {r['id']} ({sp}, weighted {weighted(d):.2f}) was never tagged")
            tagged += 1
            if tags[r["id"]] == "personal" and effective(d) > TARGET:
                wa = weighted(d)
                cf = max(GK_MIN, d[GK] * TARGET / wa)
                rest = wa - W[GK] * d[GK]
                k = (TARGET - W[GK] * cf) / rest
                assert 0 < k <= 1 + 1e-9, (r["id"], k)
                new = {dim: (round(cf, 4) if dim == GK else round(x * k, 4)) for dim, x in d.items()}
                assert new[GK] >= GK_MIN and abs(effective(new) - TARGET) < 1e-3, (r["id"], new)
                assert effective(new) <= effective(d) + 1e-9, ("c2d may only LOWER a row", r["id"])
                cf_floored += cf == GK_MIN
                report["changed"].append(dict(id=r["id"], split=sp, before=round(effective(d), 4),
                                              cf_before=d[GK], cf_after=new[GK], k=round(k, 4)))
                r["labels"] = [new[dim] for dim in r["dimension_names"]]
                changed += 1
        out.append(r)
    report["splits"][sp] = {"rows": n, "tagged": tagged, "changed": changed, "cf_held_at_3": cf_floored}
    if not CHECK:
        with open(f"{DST}/{sp}.jsonl", "w") as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
if not CHECK:
    shutil.copy(f"{SRC}/training_manifest.jsonl", f"{DST}/training_manifest.jsonl")
    json.dump(report, open(f"{DST}/build_report.json", "w"), indent=1)
print(json.dumps(report["splits"]))
