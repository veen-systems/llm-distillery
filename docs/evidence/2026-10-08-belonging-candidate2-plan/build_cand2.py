#!/usr/bin/env python3
"""Build belonging candidate 2 (PLAN.md in this directory; owner 2026-10-08). A copy of
docs/evidence/2026-10-07-belonging-adj1-build/build_adj1.py (its docstring holds the base recipe) plus:

    .venv/bin/python docs/evidence/2026-10-08-belonging-candidate2-plan/build_cand2.py c2a   # keeps the 121 one-moment negatives
    .venv/bin/python docs/evidence/2026-10-08-belonging-candidate2-plan/build_cand2.py c2b   # WITHOUT them

+ 135 hard negatives from harvest r1 where BOTH blind judges said `out_gift_official` (46) or `out_harm_is_story` (89),
  labelled exactly like r1's hard negatives: k=3 Gemini Flash with v1's prompt on full text, mean per dimension, every
  dimension capped at 2.0 (`datasets/belonging_harvest_r1/hardneg_c2_{articles.jsonl,dimscore/}`).
c2b drops r1's 121 `out_one_moment` hard negatives (owner unsure about single-person stories; the two variants show what they cost).
New groups are split 80/10/10 per origin with the same seed, so the groups both builds share keep their split.
Writes datasets/training/belonging_{variant}/.
"""
import ast, json, random, statistics, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-03-belonging-heldout"))
sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-02-belonging-adjudication"))
sys.path.insert(0, str(ROOT))
import gate  # noqa: E402  (content_twins)
import heldout as H  # noqa: E402  (the held-out rows)
from belonging_exclusions import assert_disjoint, excluded_ids  # noqa: E402
from training import data_quality as DQ  # noqa: E402

D = ROOT / "datasets"
ADJ, HV = D / "belonging_v1_adj", D / "belonging_harvest_r1"
EASY, EASY_SCORES = D / "belonging_easyneg_articles.jsonl", D / "belonging_easyneg_dimscore" / "run1" / "belonging"
LANG = D / "belonging_language_stamps.json"
VARIANT = sys.argv[1] if len(sys.argv) > 1 else ""
if VARIANT not in ("c2a", "c2b"):
    raise SystemExit(__doc__)
OUT = D / "training" / f"belonging_{VARIANT}"
C2_COUNTS = {"out_gift_official": 46, "out_harm_is_story": 89}
SPLITS, CAP, SEED, CUT = ("train", "val", "test"), 2.0, 20261007, 4000
TREAT_COUNTS = {"demote": 238, "drop": 566, "keep_v1_label": 55}
# owner ruling 1b (2026-10-08): v1 rows that later sets (pilot 1/v2 keys, calibration, v2 test) were drawn from are
# DROPPED from training, all of them -- no evaluation set may ever overlap training. Pinned: a change raises.
V1_EXCLUDED_DROP = 61


def fail(msg):
    raise SystemExit(f"BUILD REFUSED: {msg}")


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


V1C = DQ.scoring_constants(ROOT / "filters" / "belonging" / "v1")
MEDIUM = V1C["MEDIUM"]


def label_wa(names, lab):
    """The label's weighted average with v1's weights AND gatekeeper, as the scorer computes it."""
    return DQ.label_wa(V1C, names, lab)


def main():
    base = {s: jl(ADJ / f"{s}.jsonl") for s in SPLITS}
    names = base["train"][0]["dimension_names"]
    if names != list(V1C["DIMENSION_WEIGHTS"]):
        fail(f"v1 split dimension order {names} != base_scorer {list(V1C['DIMENSION_WEIGHTS'])}")
    where = {}
    for s in SPLITS:
        for r in base[s]:
            if r["dimension_names"] != names or r["id"] in where:
                fail(f"{r['id']}: mixed dimension_names or in two v1 splits")
            where[r["id"]] = s

    # --- the 2026-10-03 adjudication ruling
    treat = jl(ADJ / "treatment.jsonl")
    if Counter(t["treatment"] for t in treat) != Counter(TREAT_COUNTS):
        fail(f"treatment counts {Counter(t['treatment'] for t in treat)} != {TREAT_COUNTS}")
    tmap = {}
    for t in treat:
        if t["id"] in tmap or where.get(t["id"]) != t["split"]:
            fail(f"treated id {t['id']} is duplicated or not in split {t['split']}")
        tmap[t["id"]] = t["treatment"]
    rows = {s: [] for s in SPLITS}
    for s in SPLITS:
        for r in base[s]:
            tr = tmap.get(r["id"])
            if tr == "drop":
                continue
            r = dict(r, origin="v1")
            if tr == "demote":
                r["labels"] = [min(x, CAP) for x in r["labels"]]
                r["origin"] = "v1_demoted"
            rows[s].append(r)
    ex = excluded_ids()
    v1_excluded = sorted(r["id"] for s in SPLITS for r in rows[s] if r["id"] in ex)
    if len(v1_excluded) != V1_EXCLUDED_DROP:
        fail(f"{len(v1_excluded)} surviving v1 rows are in the exclusion list, ruling 1b covers {V1_EXCLUDED_DROP}")
    rows = {s: [r for r in rows[s] if r["id"] not in ex] for s in SPLITS}

    # --- harvest r1 (full text where the draw cut it)
    hv = {r["id"]: r for r in jl(HV / "harvest_r1_rows.jsonl")}
    full = {r["id"]: r["content"] for r in jl(HV / "cut_rows_full_content.jsonl")}

    def text(i):
        c = hv[i]["content"]
        if len(c) >= CUT:
            if i not in full or not full[i].startswith(c):
                fail(f"{i}: cut at {CUT} and no matching full text")
            return full[i]
        return c

    new = []
    pos = [r for r in jl(HV / "positives_r1_labels.jsonl") if r["keep"]]
    if len(pos) != 237:
        fail(f"{len(pos)} kept positives, expected 237")
    for p in pos:
        new.append(dict(id=p["id"], labels=[p["labels"][d] for d in names], origin="harvest_positive"))

    def hardnegs(articles, scores, origin):
        neg_in = [r["id"] for r in jl(articles)]
        per = {i: [] for i in neg_in}
        for k in (1, 2, 3):
            seen = set()
            for f in sorted((scores / f"run{k}" / "belonging").glob("scored_batch_*.jsonl")):
                for r in jl(f):
                    a = r.get("belonging_analysis")
                    if a is None or r["id"] not in per or r["id"] in seen:
                        fail(f"{origin} run{k}: unexpected or duplicated row {r.get('id')}")
                    seen.add(r["id"])
                    per[r["id"]].append([float(a[d]["score"]) for d in names])
            if seen != set(neg_in):
                fail(f"{origin} run{k} covers {len(seen)} of {len(neg_in)}")
        hi = 0
        for i, runs in per.items():
            mean = [statistics.fmean(x[j] for x in runs) for j in range(len(names))]
            hi += max(mean) > CAP
            new.append(dict(id=i, labels=[min(x, CAP) for x in mean], origin=origin))
        return hi

    uncapped_hi = {}
    if VARIANT == "c2a":
        uncapped_hi["harvest_hard_negative"] = hardnegs(HV / "hardneg_r1_articles.jsonl", HV / "hardneg_dimscore",
                                                        "harvest_hard_negative")
    c2 = jl(HV / "hardneg_c2_articles.jsonl")
    if Counter(r["judge_class"] for r in c2) != Counter(C2_COUNTS):
        fail(f"c2 hard negatives {Counter(r['judge_class'] for r in c2)} != {C2_COUNTS}")
    judged = {r["id"]: r for r in jl(HV / "positives_r1.jsonl")}
    for r in c2:
        j = judged.get(r["id"])
        if not j or not j["verdict_A"] == j["verdict_B"] == r["judge_class"]:
            fail(f"c2 hard negative {r['id']}: both judges did not say {r['judge_class']}")
    uncapped_hi["harvest_hard_negative_c2"] = hardnegs(HV / "hardneg_c2_articles.jsonl", HV / "hardneg_c2_dimscore",
                                                       "harvest_hard_negative_c2")
    for r in new:
        h = hv[r["id"]]
        r.update(title=h["title"], url=h["url"], content=text(r["id"]), dimension_names=names)

    # --- easy negatives: production draw, k=1, kept as labelled
    easy = {r["id"]: r for r in jl(EASY)}
    seen = set()
    for f in sorted(EASY_SCORES.glob("scored_batch_*.jsonl")):
        for r in jl(f):
            a = r.get("belonging_analysis")
            if a is None or r["id"] not in easy or r["id"] in seen:
                fail(f"easy negatives: unexpected or duplicated row {r.get('id')}")
            seen.add(r["id"])
            e = easy[r["id"]]
            new.append(dict(id=e["id"], title=e["title"], url=e["url"], content=e["content"], dimension_names=names,
                            labels=[float(a[d]["score"]) for d in names], origin="production_easy_negative"))
    if seen != set(easy):
        fail(f"easy negatives: oracle covers {len(seen)} of {len(easy)}")

    rng = random.Random(SEED)
    for origin in ("harvest_positive", "harvest_hard_negative", "harvest_hard_negative_c2", "production_easy_negative"):
        grp = sorted((r for r in new if r["origin"] == origin), key=lambda r: r["id"])
        rng.shuffle(grp)
        n = len(grp)
        cuts = {"train": grp[:round(0.8 * n)], "val": grp[round(0.8 * n):round(0.9 * n)], "test": grp[round(0.9 * n):]}
        for s in SPLITS:
            rows[s] += cuts[s]

    # --- exclusions and held-out twins
    allrows = [r for s in SPLITS for r in rows[s]]
    ids = [r["id"] for r in allrows]
    if len(ids) != len(set(ids)):
        fail(f"{len(ids) - len(set(ids))} duplicate ids across the built splits")
    assert_disjoint(ids, "belonging_v1_adj1 build")
    twins = gate.content_twins([dict(id=r["id"], text_head=r["content"][:1000]) for r in allrows], H.rows())
    drop = {t for t, _, _ in twins}
    for s in SPLITS:
        rows[s] = [r for r in rows[s] if r["id"] not in drop]

    # --- FMEA: FM-D1 cross-split twins DROP the val/test copy; FM-L1..3 RAISE
    cross = DQ.cross_split_twins(rows)
    gone = {(sp, i) for sp, i, _, _ in cross}
    rows = {sp: [r for r in rows[sp] if (sp, r["id"]) not in gone] for sp in SPLITS}
    # Re-run the held-out twin check on the rows that SURVIVED: content_twins discounts a run seen in > 2 training rows
    # as boilerplate, so dropping rows can turn a discounted footer into a "twin" (2026-10-08: the gate refused 2
    # The Better India rows sharing only a social-media footer, which ~10 rows carried at the first check). Owner:
    # drop them, as the gate's docstring prescribes; repeat until the check is empty.
    while True:
        late = gate.content_twins([dict(id=r["id"], text_head=r["content"][:1000]) for s in SPLITS for r in rows[s]],
                                  H.rows())
        if not late:
            break
        twins += late
        bad = {t for t, _, _ in late}
        rows = {sp: [r for r in rows[sp] if r["id"] not in bad] for sp in SPLITS}
    for r in (r for s in SPLITS for r in rows[s]):
        if len(r["labels"]) != len(names) or not 0 <= min(r["labels"]) <= max(r["labels"]) <= 10:
            fail(f"FM-L3: {r['id']} labels out of range or ragged: {r['labels']}")
        w = label_wa(names, r["labels"])
        if r["origin"] in ("v1_demoted", "harvest_hard_negative", "harvest_hard_negative_c2") and (w >= MEDIUM or max(r["labels"]) > CAP):
            fail(f"FM-L1: {r['origin']} {r['id']} has label wa {w:.2f}, max dim {max(r['labels'])}")
        if r["origin"] == "harvest_positive" and w < MEDIUM:
            fail(f"FM-L2: harvest positive {r['id']} has label wa {w:.2f} < {MEDIUM}")

    # --- write
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(variant=VARIANT, seed=SEED, cap=CAP, medium=MEDIUM, heldout_twins_dropped=twins,
                  cross_split_twins_dropped=dict(n=len(cross), by=dict(Counter(b for _, _, b, _ in cross)),
                                                 examples=cross[:5]),
                  hard_negatives_with_a_dim_above_cap=uncapped_hi, v1_excluded_dropped=v1_excluded, splits={})
    with open(OUT / "training_manifest.jsonl", "w", encoding="utf-8") as man:
        for s in SPLITS:
            with open(OUT / f"{s}.jsonl", "w", encoding="utf-8") as f:
                for r in rows[s]:
                    f.write(json.dumps({k: r[k] for k in ("id", "title", "content", "url", "labels", "dimension_names")},
                                       ensure_ascii=False) + "\n")
                    man.write(json.dumps(dict(id=r["id"], url=r["url"] or "", title=r["title"] or "",
                                              text_head=r["content"][:1000]), ensure_ascii=False) + "\n")
            report["splits"][s] = dict(rows=len(rows[s]), by_origin=dict(Counter(r["origin"] for r in rows[s])),
                                       labels_medium_plus=sum(label_wa(names, r["labels"]) >= MEDIUM for r in rows[s]))
    built = [r for s in SPLITS for r in rows[s]]
    production = list(easy.values())
    report["easy_negatives_labelled_positive"] = sum(label_wa(names, r["labels"]) >= MEDIUM for r in built
                                                     if r["origin"] == "production_easy_negative")
    is_pos = lambda r: label_wa(names, r["labels"]) >= MEDIUM  # noqa: E731
    report["text_parity"] = DQ.parity(built, production, is_pos)
    report["mix"] = DQ.mix(built, production, is_pos, DQ.load_language(LANG))
    report["boilerplate"] = DQ.boilerplate(built)
    json.dump(report, open(OUT / "build_report.json", "w"), indent=1)
    # The gate's OWN check on the exact manifest just written: a refusal must surface here, not after training.
    print(gate.refuse_overlap(OUT), file=sys.stderr)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
