"""Checks A and B of PREREGISTRATION.md, from the lab's scores and tags.

    python3 analyse.py tag-input > tag_input.jsonl     # ids that need a qwen tag (neither A nor B has one yet)
    python3 analyse.py report > result.txt            # both checks, the controls, the predictions' inputs

Lab layout (~/ld-lab/experiments/2026-10-15-belonging-c2d/): population/population.jsonl,
scores/scores_pop/<pkg>.jsonl, scores/scores_comp/<pkg>.jsonl, tag/out.jsonl (+ tag-control/out.jsonl).
"""
import json, os, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE.parent / "2026-10-13-belonging-site-ranking"))
from filters.common.score_normalization import apply_normalization, load_normalization
from replay import order                                   # H, as in EXP-049
from site_rank import pdate

LABX = Path(os.environ.get("LD_LAB", Path.home() / "ld-lab")).expanduser() / "experiments"
LAB = LABX / "2026-10-15-belonging-c2d"
PKGS = ["v3", "v1_c2d_s42", "v1_c2d_s43"]
NORM = load_normalization(str(REPO / "filters/belonging/v3/normalization.json"))
OP, DISPLAY, TOP, RECALL_BAR, SAFE_RAW = 4.0, 4.5, 30, 0.9, 5.0
AMS = ZoneInfo("Europe/Amsterdam")                         # NexusMind file names are local time (CEST)
BUILDS = [datetime(2026, 10, d, 14, 30, tzinfo=timezone.utc) for d in range(9, 15)] + \
         [datetime(2026, 10, 15, 6, 37, 16, tzinfo=timezone.utc)]
OLD_TAGS = [LABX / "2026-10-13-belonging-daily-baseline/tag/out.jsonl",
            LABX / "2026-10-12-belonging-c2c/focus-tag/out.jsonl",
            LABX / "2026-10-12-belonging-c2c/focus-tag-comp/out.jsonl",
            LABX / "2026-10-15-belonging-h-replay/tag/tag/out.jsonl",
            LABX / "2026-10-15-belonging-h-replay/tag-dated/out.jsonl"]


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def scores(kind, pkg, ids):
    rows = jl(LAB / "scores" / f"scores_{kind}" / f"{pkg}.jsonl")
    meta, rows = rows[0]["meta"], rows[1:]
    assert [r["id"] for r in rows] == ids, f"{kind} {pkg}: rows differ from the input order"
    for r in rows:
        assert r["stage_used"] in ("stage2", "stage1_low"), r
        assert r["stage_used"] != "stage2" or r["raw"] is not None, r
    return meta, {r["id"]: r for r in rows}


def file_time(name):                                       # filtered_YYYYMMDD_HHMMSS.jsonl, local time
    return datetime.strptime(name[9:24], "%Y%m%d_%H%M%S").replace(tzinfo=AMS).astimezone(timezone.utc)


def removals():                                            # EXP-049's dated sets
    sr, hr = HERE.parent / "2026-10-13-belonging-site-ranking", HERE.parent / "2026-10-15-belonging-h-replay"
    b13 = {r["id"] for r in json.loads((sr / "build_pop_20261013.json").read_text())}
    p13 = {l.strip() for l in (sr / "page_ids_20261013.txt").read_text().splitlines() if l.strip()}
    rows = json.loads((hr / "ovr_db_rows.json").read_text())
    t15 = BUILDS[-1]
    b15 = {r["id"] for r in rows if pdate(r["s_created"]) <= t15 and pdate(r["published_date"]) <= t15
           and pdate(r["published_date"]).astimezone(timezone.utc).date() >= (t15 - timedelta(days=10)).date()}
    p15 = {l.strip() for l in (hr / "page_ids_20261015.txt").read_text().splitlines() if l.strip()}
    return b13 - p13, b15 - p15, b13 | b15


def check_b():
    pop = jl(LAB / "population/population.jsonl")
    ids = [r["id"] for r in pop]
    rm13, rm15, observed = removals()
    out = {}
    for pkg in PKGS:
        meta, s = scores("pop", pkg, ids)
        out[pkg] = {"meta": meta, "builds": {}}
        rows = [dict(id=r["id"], published_date=r["published_date"], avail=file_time(r["first_file"]),
                     raw=s[r["id"]]["raw"], weighted_average=apply_normalization(s[r["id"]]["raw"], NORM))
                for r in pop if r["stratum"] == "screen" and s[r["id"]]["stage_used"] == "stage2"]
        for t in BUILDS:
            rm = rm13 if t.date() <= datetime(2026, 10, 13).date() else rm15
            floor = (t - timedelta(days=10)).date()
            cand = [r for r in rows if r["avail"] <= t and pdate(r["published_date"]) <= t
                    and pdate(r["published_date"]).astimezone(timezone.utc).date() >= floor
                    and r["weighted_average"] >= DISPLAY and r["id"] not in rm]
            top = [r["id"] for r in order("H hybrid", cand, t)][:TOP]
            out[pkg]["builds"][t.strftime("%Y-%m-%dT%H:%MZ")] = dict(n=len(top), population=len(cand), top30=top,
                                                                    removal_unknown=sum(i not in observed for i in top))
        sample = {r["id"]: r["stratum"] for r in pop if r["stratum"] != "screen"}
        out[pkg]["safety"] = {st: sum(1 for i, x in sample.items() if x == st and s[i]["stage_used"] == "stage2"
                                      and s[i]["raw"] >= SAFE_RAW) for st in ("below", "stage1_low")}
    return out


def check_a():
    draw = jl(Path.home() / "ld-lab/datasets/belonging_comp_draw/v1/belonging_comp_rows.jsonl")
    ids = [r["id"] for r in draw]
    sc = {p: scores("comp", p, ids) for p in PKGS}
    v3pass = [i for i in ids if sc["v3"][1][i]["stage_used"] == "stage2" and sc["v3"][1][i]["raw"] >= OP]
    return draw, sc, v3pass


def tags():
    t = {}
    for p in OLD_TAGS:
        for o in jl(p):
            t.setdefault(o["id"], o["focus"])
    new = LAB / "tag/tag/out.jsonl"
    if new.exists():
        for o in jl(new):
            assert o["id"] not in t, o["id"]
            t[o["id"]] = o["focus"]
    return t


def cmd_tag_input():
    t = tags()
    b = check_b()
    draw, sc, v3pass = check_a()
    need = sorted({i for p in PKGS for v in b[p]["builds"].values() for i in v["top30"]} | set(v3pass))
    need = [i for i in need if i not in t]
    text = {r["id"]: r for r in jl(LAB / "population/population.jsonl")}
    text.update({r["id"]: r for r in draw})
    for i in need:
        print(json.dumps(dict(id=i, title=text[i]["title"], content=text[i]["content"]), ensure_ascii=False))
    reused = sorted(i for i in ({i for p in PKGS for v in b[p]["builds"].values() for i in v["top30"]} | set(v3pass)) if i in t)
    with open(HERE / "determinism_ids.txt", "w") as f:
        f.write("\n".join(random.Random(0).sample(reused, 10)) + "\n")
    print(f"tag input: {len(need)} new ids; 10 determinism ids -> determinism_ids.txt", file=sys.stderr)


def cmd_report():
    t = tags()
    ctrl = jl(LAB / "tag/tag-control/out.jsonl")
    old = {}
    for p in OLD_TAGS:
        for o in jl(p):
            old.setdefault(o["id"], o["focus"])
    m = sum(o["focus"] == old[o["id"]] for o in ctrl)
    print(f"determinism control: {m}/{len(ctrl)} ({'PASS' if m >= 9 else 'FAIL'})")
    nc = jl(LAB / "population/norm_control.jsonl")
    ok = sum(abs(apply_normalization(r["raw"], NORM) - r["norm"]) <= 0.01 for r in nc)
    print(f"normalization control: {ok}/{len(nc)} within 0.01 ({'PASS' if ok >= 0.99 * len(nc) else 'FAIL: STOP'})")

    draw, sc, v3pass = check_a()
    group = [i for i in v3pass if t[i] == "group"]
    unparsed = [i for i in v3pass if t[i] not in ("personal", "group")]
    print(f"\n== Check A: recall guard. v3 (rescored) passes {len(v3pass)}, qwen group among them {len(group)}, "
          f"unparsed {len(unparsed)} {unparsed}")
    a_ok = {}
    for p in PKGS[1:]:
        kept = sum(sc[p][1][i]["stage_used"] == "stage2" and sc[p][1][i]["raw"] >= OP for i in group)
        a_ok[p] = kept / len(group) >= RECALL_BAR
        passes = sum(sc[p][1][i]["stage_used"] == "stage2" and sc[p][1][i]["raw"] >= OP for i in sc[p][1])
        print(f"{p}: {kept}/{len(group)} = {kept / len(group):.3f} ({'PASS' if a_ok[p] else 'FAIL'}); passes at 4.0: {passes}")

    b = check_b()
    print("\n== Check B: qwen personal in the H top 30 (a FLOOR)")
    means = {}
    for p in PKGS:
        cs = []
        for k, v in b[p]["builds"].items():
            assert all(i in t for i in v["top30"]), f"{p} {k}: untagged"
            c = sum(t[i] == "personal" for i in v["top30"])
            u = sum(t[i] not in ("personal", "group") for i in v["top30"])
            cs.append(c)
            print(f"{p:11} {k}  N {v['n']:2}  personal {c:2}  unparsed {u}  removal-unknown {v['removal_unknown']:2}  population {v['population']}")
        means[p] = sum(cs) / len(cs)
        print(f"{p:11} weekly mean {means[p]:.2f}  worst {max(cs)}  safety (rows >= {SAFE_RAW} raw): {b[p]['safety']}")
    print()
    for p in PKGS[1:]:
        d = means[p] - means["v3"]
        print(f"{p}: weekly mean {means[p]:.2f} vs v3 {means['v3']:.2f}, difference {d:+.2f} "
              f"({'meets' if d <= -1.0 else 'does not meet'} the -1.0 bar); <= 6: {means[p] <= 6} (undetermined on a floor)")
    worth = all(a_ok.values()) and all(means[p] - means["v3"] <= -1.0 for p in PKGS[1:])
    print(f"\nWORTH A GATE: {worth}")
    print(f"presence control: v3 arm personal >= 1 on some build: "
          f"{any(sum(t[i] == 'personal' for i in v['top30']) for v in b['v3']['builds'].values())}")
    sel = json.loads((HERE.parent / "2026-10-15-belonging-h-replay/selection_dated.json").read_text())
    for k in list(sel)[2:]:
        print(f"rebuild control {k}: v3 arm top 30 vs EXP-049 dated H selection overlap "
              f"{len(set(b['v3']['builds'][k]['top30']) & set(sel[k]['H']['top30_v3']))}/30")


{"tag-input": cmd_tag_input, "report": cmd_report}[sys.argv[1]]()
