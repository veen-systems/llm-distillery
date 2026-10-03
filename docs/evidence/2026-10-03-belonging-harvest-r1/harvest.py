#!/usr/bin/env python3
"""Belonging harvest round 1 (README.md): Gemini v2.2 screen over every eligible hi-band row, then two blind judge
passes on Gemini's ins; positive = BOTH judges say in (owner ruling 2026-10-03). Rows: datasets/belonging_harvest_r1/.

    .venv/bin/python docs/evidence/2026-10-03-belonging-harvest-r1/harvest.py check|gemini|build-judges|import

The Gemini call, prompt, settings, empty-reply handling and judge batching are the held-out run's
(../2026-10-03-belonging-heldout/heldout.py), pointed at this round's files.
"""
import hashlib, json, random, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-03-belonging-heldout"))
import heldout as h  # noqa: E402
from belonging_exclusions import assert_disjoint  # noqa: E402

DATA = ROOT / "datasets" / "belonging_harvest_r1"
h.ROWS, h.GEM, h.JUDGE = DATA / "harvest_r1_rows.jsonl", DATA / "gemini_v2_2.jsonl", DATA / "judges"
_rows = h.rows
h.rows = lambda: [dict(r, band="hi") for r in _rows()]  # heldout's records carry a band; every row here is hi
N_ROWS = 4591  # extract_hi.py's count on 2026-10-03 (= hi pool 4,991 minus the 400 held-out rows)


def check():
    rs = h.rows()
    if hashlib.sha256(h.RUBRIC.read_bytes()).hexdigest()[:16] != h.RUBRIC_SHA:
        raise SystemExit("rubric is not the frozen v2.2")
    ids = [r["id"] for r in rs]
    if len(ids) != N_ROWS or len(set(ids)) != N_ROWS or any(r["raw"] < 5.6 for r in rs):
        raise SystemExit(f"extract shape wrong: {len(ids)} rows, {len(set(ids))} distinct")
    assert_disjoint(ids, purpose="harvest round 1")
    print(f"ok: {N_ROWS} distinct hi-band rows, disjoint from belonging_exclusions (incl. the held-out set), rubric frozen")


h.check = check  # h.gemini() calls check() first


def build_judges():
    rs, g = {r["id"]: r for r in h.rows()}, h.gem_latest()
    if set(g) != set(rs):
        raise SystemExit(f"gemini covers {len(g)} of {len(rs)} rows; finish stage A first")
    if h.JUDGE.exists():
        raise SystemExit(f"{h.JUDGE} exists; refusing to overwrite")
    ids = sorted(i for i in rs if g[i]["verdict"] == "in_scope")
    nb, id_map = -(-len(ids) // h.PER_BATCH), {}
    for p, seed in (("A", 41), ("B", 42)):
        order = ids[:]
        random.Random(seed).shuffle(order)
        for b in range(nb):
            d = h.JUDGE / f"{p}{b + 1}"
            (d / "scratch").mkdir(parents=True)
            with open(d / "input.jsonl", "w") as f:
                for i in order[b::nb]:
                    oid = hashlib.sha256(f"harvest_r1:{p}:{i}".encode()).hexdigest()[:12]
                    id_map[oid] = i
                    r = rs[i]
                    f.write(json.dumps(dict(id=oid, title=r["title"], url=r["url"], source=r["source"],
                                            content=r["content"]), ensure_ascii=False) + "\n")
    json.dump(dict(rubric_sha=h.RUBRIC_SHA, id_map=id_map, pick={i: "gemini_in" for i in ids}),
              open(h.JUDGE / "id_map.json", "w"))
    print(f"{len(ids)} Gemini-in rows to judge, {nb} batches per pass")


def import_():
    pick, v = h.judges()
    out = DATA / "positives_r1.jsonl"
    rs = {r["id"]: r for r in h.rows()}
    lab = Counter()
    with open(out, "w") as f:
        for i in sorted(pick):
            a, b = (v[p][i]["verdict"] for p in "AB")
            label = "in" if a == b == "in_scope" else "split" if "in_scope" in (a, b) else "out"
            lab[label] += 1
            f.write(json.dumps(dict(id=i, label=label, verdict_A=a, verdict_B=b, quote_A=v["A"][i]["quote"],
                                    quote_B=v["B"][i]["quote"], raw=rs[i]["raw"], file=rs[i]["file"])) + "\n")
    print(f"{len(pick)} judged: {dict(lab)}; positives (both in) = {lab['in']} -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"check": check, "gemini": lambda: h.gemini(0), "build-judges": build_judges, "import": import_}[cmd]()
