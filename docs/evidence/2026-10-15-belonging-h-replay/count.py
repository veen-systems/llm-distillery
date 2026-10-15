"""Step 4 of PREREGISTRATION.md: per build and order, the qwen `personal` count in the first 30 v3 rows (a FLOOR),
the weekly mean over in-range builds, the worst day, H - control per build, and the two controls (determinism,
presence) plus the rebuild check against the baseline's selection.

    python3 docs/evidence/2026-10-15-belonging-h-replay/count.py > .../count_result.txt
    python3 docs/evidence/2026-10-15-belonging-h-replay/count.py --dated > .../count_result_dated.txt  (deviation)

Tags: this run's lab tag/tag/out.jsonl (new ids) first, else the earlier runs' files (reuse rule, section 2).
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser() / "experiments"
NEW = LAB / "2026-10-15-belonging-h-replay/tag/tag/out.jsonl"
CTRL = LAB / "2026-10-15-belonging-h-replay/tag/tag-control/out.jsonl"
OLD = [LAB / "2026-10-13-belonging-daily-baseline/tag/out.jsonl", LAB / "2026-10-12-belonging-c2c/focus-tag/out.jsonl",
       LAB / "2026-10-12-belonging-c2c/focus-tag-comp/out.jsonl"]


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


old = {}
for p in OLD:
    for o in load(p):
        old.setdefault(o["id"], o["focus"])                 # same precedence as the input builder
qwen = dict(old)
DATED = "--dated" in sys.argv
for o in load(NEW) + (load(LAB / "2026-10-15-belonging-h-replay/tag-dated/out.jsonl") if DATED else []):
    assert o["id"] not in old, o["id"]
    qwen[o["id"]] = o["focus"]

ctrl = load(CTRL)
match = sum(o["focus"] == old[o["id"]] for o in ctrl)
print(f"determinism control: {match}/{len(ctrl)} re-tagged reused ids match their earlier tag "
      f"({'PASS' if match >= 9 else 'FAIL: re-tag everything'})")

sel = json.loads((HERE / ("selection_dated.json" if DATED else "selection.json")).read_text())
res = {"H": [], "control": []}
print("\nbuild               order    N  in_range  v1_skipped  <24h  qwen_personal  group  unparsed")
for build, b in sel.items():
    for name in ("H", "control"):
        s = b[name]
        ids = s["top30_v3"]
        assert all(i in qwen for i in ids), f"{build} {name}: untagged rows"
        p = sum(qwen[i] == "personal" for i in ids)
        g = sum(qwen[i] == "group" for i in ids)
        print(f"{build:18}  {name:7} {s['n']:2}  {str(s['in_range']):8}  {s['skipped_by_stamp'].get('1.0', 0):10}  "
              f"{s['under_24h']:4}  {p:13}  {g:5}  {len(ids) - p - g:8}")
        if s["in_range"]:
            res[name].append((build, p))
    print(f"{'':18}  removal status unknown in population: {b['removal_unknown']} of {b['population']}")

print()
for name, xs in res.items():
    c = [p for _, p in xs]
    worst = max(xs, key=lambda x: x[1])
    print(f"{name:7}: in-range builds {len(c)}, qwen personal {c}, weekly mean {sum(c) / len(c):.2f}, "
          f"worst {worst[1]} ({worst[0]})")
hd = dict(res["H"]); cd = dict(res["control"])
print("H - control per in-range build:", {k: hd[k] - cd[k] for k in hd if k in cd})

c12 = [p for k, p in res["control"] if k.startswith("2026-10-12")]
print(f"\npresence control: control 10-12 qwen personal = {c12[0]} ({'PASS' if c12[0] > 0 else 'FAIL'})")
base = json.loads((HERE.parent / "2026-10-13-belonging-daily-baseline" / "selection.json").read_text())
for k in ("2026-10-11T14:30Z", "2026-10-12T14:30Z"):
    ov = len(set(sel[k]["control"]["top30_v3"]) & set(base[k]["top30_v3"]))
    print(f"rebuild check {k}: control top 30 overlaps the baseline's selection {ov}/30")
