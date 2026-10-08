#!/usr/bin/env python3
"""Build datasets/training/belonging_v1_adj1/ (plan phase 5; owner rulings 2026-10-03 and 2026-10-07).

    .venv/bin/python docs/evidence/2026-10-07-belonging-adj1-build/build_adj1.py

adj1 = v1's own splits under the 2026-10-03 adjudication ruling
     + the 237 harvest-r1 positives (k=3 oracle labels, v1's prompt)
     + the 121 harvest-r1 hard negatives (both judges `out_one_moment`, owner 2026-10-07): k=3 oracle labels with
       v1's prompt, mean per dimension, every dimension capped at 2.0
     + ~800 EASY negatives (owner 2026-10-07): a uniform random production draw (`draw_easy_negatives.py`), k=1 oracle
       labels with v1's prompt, kept AS LABELLED (a genuine positive among them stays a positive).
- treatment.jsonl: `demote` -> every dimension min(label, 2.0); `drop` -> removed; `keep_v1_label` -> unchanged.
  Every treated id must sit exactly once in the split it names, and the counts must be 238 / 566 / 55.
- Text: FULL text for every harvest row the draw cut at 4,000 chars (owner 2026-10-07); v1's own rows were never cut.
- New rows are split 80/10/10 with seed 20261007; v1's rows keep their split.
- v1 rows in the exclusion list are DROPPED (owner ruling 1b, 2026-10-08; exactly 61, pinned); then every id is
  checked against `belonging_exclusions.assert_disjoint`; every row is checked against the held-out set
  with `gate.content_twins` and DROPPED if it twins one.
- The FMEA checks (docs/checklists/training-data-fmea.md, `training/data_quality.py`): cross-split twins DROP the val/test copy (FM-D1); label sanity RAISES
  (FM-L1..3); text parity, language/source mix and boilerplate are REPORTED every run (FM-T1, FM-D2, FM-D3).
- Writes train/val/test.jsonl, training_manifest.jsonl (the gate's contract) and build_report.json.
Any plumbing surprise raises (exit 1).
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
OUT = D / "training" / "belonging_v1_adj1"
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

    neg_in = [r["id"] for r in jl(HV / "hardneg_r1_articles.jsonl")]
    per = {i: [] for i in neg_in}
    for k in (1, 2, 3):
        seen = set()
        for f in sorted((HV / "hardneg_dimscore" / f"run{k}" / "belonging").glob("scored_batch_*.jsonl")):
            for r in jl(f):
                a = r.get("belonging_analysis")
                if a is None or r["id"] not in per or r["id"] in seen:
                    fail(f"hard negatives run{k}: unexpected or duplicated row {r.get('id')}")
                seen.add(r["id"])
                per[r["id"]].append([float(a[d]["score"]) for d in names])
        if seen != set(neg_in):
            fail(f"hard negatives run{k} covers {len(seen)} of {len(neg_in)}")
    uncapped_hi = 0
    for i, runs in per.items():
        mean = [statistics.fmean(x[j] for x in runs) for j in range(len(names))]
        uncapped_hi += max(mean) > CAP
        new.append(dict(id=i, labels=[min(x, CAP) for x in mean], origin="harvest_hard_negative"))
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
    for origin in ("harvest_positive", "harvest_hard_negative", "production_easy_negative"):
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
    for r in (r for s in SPLITS for r in rows[s]):
        if len(r["labels"]) != len(names) or not 0 <= min(r["labels"]) <= max(r["labels"]) <= 10:
            fail(f"FM-L3: {r['id']} labels out of range or ragged: {r['labels']}")
        w = label_wa(names, r["labels"])
        if r["origin"] in ("v1_demoted", "harvest_hard_negative") and (w >= MEDIUM or max(r["labels"]) > CAP):
            fail(f"FM-L1: {r['origin']} {r['id']} has label wa {w:.2f}, max dim {max(r['labels'])}")
        if r["origin"] == "harvest_positive" and w < MEDIUM:
            fail(f"FM-L2: harvest positive {r['id']} has label wa {w:.2f} < {MEDIUM}")

    # --- write
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(seed=SEED, cap=CAP, medium=MEDIUM, heldout_twins_dropped=twins,
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
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
