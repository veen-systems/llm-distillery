"""POST HOC diagnostics, written after result.txt was read (not pre-registered). Reads what analyse.py reads.

    python3 diagnose.py > diagnose.txt

1. Seed agreement: top-30 overlap per build between the two c2d seeds and with the v3 arm.
2. Targeting: the median raw shift (c2d minus v3) of the rows in v3's top 30 over the week, split by qwen tag.
3. Scorer equivalence: this run's v3 comp scores (score_rows.py) vs c2c's v3 comp scores (comp_check.py score).
4. Page geometry (display cut in raw, eligible-population ratio, lowest top-30 raw) and the screen safety sample.
"""
import json, statistics, sys
from pathlib import Path

sys.argv = [sys.argv[0], "report"]                         # analyse.py dispatches on argv at import end
src = (Path(__file__).resolve().parent / "analyse.py").read_text()
exec(src.rsplit("\n{", 1)[0])                              # everything but the dispatch line

t, b = tags(), check_b()
print("== 1. top-30 overlap per build")
for k in b["v3"]["builds"]:
    s42, s43, v3 = (set(b[p]["builds"][k]["top30"]) for p in ("v1_c2d_s42", "v1_c2d_s43", "v3"))
    print(f"{k}  s42&s43 {len(s42 & s43):2}  s42&v3 {len(s42 & v3):2}  s43&v3 {len(s43 & v3):2}")

print("\n== 2. median raw shift (c2d - v3) of v3's weekly top-30 rows, by qwen tag")
pop = jl(LAB / "population/population.jsonl")
ids = [r["id"] for r in pop]
sc = {p: scores("pop", p, ids)[1] for p in PKGS}
week = {i for v in b["v3"]["builds"].values() for i in v["top30"]}
for p in PKGS[1:]:
    for focus in ("personal", "group"):
        rows = [i for i in week if t[i] == focus]
        d = [sc[p][i]["raw"] - sc["v3"][i]["raw"] for i in rows]
        print(f"{p:11} {focus:8} n {len(rows):3}  median shift {statistics.median(d):+.2f}")

print("\n== 3. v3 comp scores: this run vs c2c's")
draw_ids = [r["id"] for r in jl(Path.home() / "ld-lab/datasets/belonging_comp_draw/v1/belonging_comp_rows.jsonl")]
mine = scores("comp", "v3", draw_ids)[1]
c2c = {r["id"]: r for r in jl(LABX / "2026-10-12-belonging-c2c/belonging_comp_scores/v3.jsonl")[1:]}
assert c2c.keys() == mine.keys()
both = [i for i in draw_ids if mine[i]["stage_used"] == c2c[i]["stage_used"] == "stage2"]
print(f"rows {len(draw_ids)}  stage differs {sum(mine[i]['stage_used'] != c2c[i]['stage_used'] for i in draw_ids)}  "
      f"max |raw delta| {max(abs(mine[i]['raw'] - c2c[i]['raw']) for i in both)}  "
      f"flips at {OP} {sum((mine[i]['raw'] >= OP) != (c2c[i]['raw'] >= OP) for i in both)}")

print("\n== 4. page geometry and the screen safety sample")
r = 4.0
while apply_normalization(r, NORM) < DISPLAY:
    r += 0.01
print(f"raw at normalized {DISPLAY} (v3 curve): {r:.2f}")
for p in PKGS[1:]:
    ratios = [b[p]["builds"][k]["population"] / b["v3"]["builds"][k]["population"] for k in b["v3"]["builds"]]
    print(f"{p:11} display-eligible population vs v3 per build: {min(ratios):.2f}..{max(ratios):.2f}")
print(f"lowest raw in any arm's top 30: {min(sc[p][i]['raw'] for p in PKGS for v in b[p]['builds'].values() for i in v['top30']):.2f}")
strata = {st: [x["id"] for x in pop if x["stratum"] == st] for st in ("below", "stage1_low")}
for p in PKGS:
    below2 = [sc[p][i]["raw"] for i in strata["below"] if sc[p][i]["stage_used"] == "stage2"]
    print(f"{p:11} below-screen max raw {max(below2):.2f}, >= {OP}: {sum(x >= OP for x in below2)}; "
          f"stage1_low sample still stage1_low: {sum(sc[p][i]['stage_used'] == 'stage1_low' for i in strata['stage1_low'])}/{len(strata['stage1_low'])}")
