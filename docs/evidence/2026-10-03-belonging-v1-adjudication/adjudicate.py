#!/usr/bin/env python3
"""Belonging v1 label adjudication (PLAN.md). Rows: gitignored datasets/belonging_v1_adj/.

    .venv/bin/python docs/evidence/2026-10-03-belonging-v1-adjudication/adjudicate.py build|import|ruling

build   the pool (label weighted avg >= 3.5, v1 weights + gatekeeper read from base_scorer.py), two blind passes in
        batches of <= 50 with opaque ids, judges/{A,B}N/input.jsonl.
import  checks every out.jsonl (ids = inputs in order, valid verdicts, both passes cover the pool once) and writes
        verdicts.jsonl with the PLAN.md outcome per row (kept_in / moved_out / unchanged_split / unchanged_cannot).
        ⚠️ `outcome` is PLAN.md's SUPERSEDED rule; the build must read `treatment` from `ruling`.
ruling  the owner's 2026-10-03 rule (README § Ruling) as data: writes treatment.jsonl with
        demote (moved_out AND both judges out_one_moment) / drop (other moved_out) / keep_v1_label (the rest),
        and asserts the ruled counts 238 / 566 / 55, so a changed verdicts file cannot silently move them.
"""
import ast, hashlib, json, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "datasets" / "belonging_v1_adj"
J = D / "judges"
RUBRIC = ROOT / "docs" / "evidence" / "2026-10-02-belonging-adjudication" / "rubric_belonging_v2.md"
RUBRIC_SHA = "d450b79510418cf7"
VERDICTS = ["in_scope", "out_gift_official", "out_one_moment", "out_harm_is_story", "out_culture_topic",
            "out_event_spectated", "out_other", "cannot_judge"]
SPLITS, PER_BATCH = ("train", "val", "test"), 50

c = {}
for n in ast.walk(ast.parse((ROOT / "filters" / "belonging" / "v1" / "base_scorer.py").read_text())):
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in (
            "DIMENSION_WEIGHTS", "GATEKEEPER_DIMENSION", "GATEKEEPER_MIN", "GATEKEEPER_CAP"):
        c[n.targets[0].id] = ast.literal_eval(n.value)
W = c["DIMENSION_WEIGHTS"]


def wavg(r):
    if r["dimension_names"] != list(W):
        raise SystemExit(f"{r['id']}: dimension order differs from base_scorer")
    s = dict(zip(r["dimension_names"], r["labels"]))
    w = sum(W[d] * s[d] for d in W)
    return min(w, c["GATEKEEPER_CAP"]) if s[c["GATEKEEPER_DIMENSION"]] < c["GATEKEEPER_MIN"] else w


def pool():
    out = {}
    for sp in SPLITS:
        for l in open(D / f"{sp}.jsonl"):
            r = json.loads(l)
            if wavg(r) >= 3.5:
                if r["id"] in out:
                    raise SystemExit(f"{r['id']} in two splits")
                out[r["id"]] = dict(r, split=sp)
    return out


def build():
    if hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16] != RUBRIC_SHA:
        raise SystemExit("rubric is not the frozen v2.2")
    if J.exists():
        raise SystemExit(f"{J} exists; refusing to overwrite")
    P = pool()
    ids, id_map = sorted(P), {}
    nb = -(-len(ids) // PER_BATCH)
    for p, seed in (("A", 51), ("B", 52)):
        order = ids[:]
        random.Random(seed).shuffle(order)
        for b in range(nb):
            d = J / f"{p}{b + 1}"
            (d / "scratch").mkdir(parents=True)
            with open(d / "input.jsonl", "w") as f:
                for i in order[b::nb]:
                    oid = hashlib.sha256(f"v1adj:{p}:{i}".encode()).hexdigest()[:12]
                    id_map[oid] = i
                    r = P[i]
                    f.write(json.dumps(dict(id=oid, title=r.get("title"), url=r.get("url"), source=r.get("source"),
                                            content=r.get("content")), ensure_ascii=False) + "\n")
    json.dump(dict(rubric_sha=RUBRIC_SHA, id_map=id_map), open(J / "id_map.json", "w"))
    print(f"pool {len(ids)} ({Counter(P[i]['split'] for i in ids)}); {nb} batches per pass")


def import_():
    if hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16] != RUBRIC_SHA:
        raise SystemExit("rubric changed since the judges ran")
    P, m = pool(), json.load(open(J / "id_map.json"))
    v = {"A": {}, "B": {}}
    for d in sorted(J.glob("[AB][0-9]*")):
        inp = [json.loads(l)["id"] for l in open(d / "input.jsonl")]
        out = [json.loads(l) for l in open(d / "out.jsonl")]
        if [r["id"] for r in out] != inp:
            raise SystemExit(f"{d.name}: ids are not the input ids in input order")
        for r in out:
            if r["verdict"] not in VERDICTS:
                raise SystemExit(f"{d.name}: verdict {r['verdict']!r}")
            v[d.name[0]][m["id_map"][r["id"]]] = r
    for p in v:
        if set(v[p]) != set(P):
            raise SystemExit(f"pass {p} does not cover the pool exactly once")
    T = Counter()
    with open(D / "verdicts.jsonl", "w") as f:
        for i in sorted(P):
            a, b = v["A"][i]["verdict"], v["B"][i]["verdict"]
            if "cannot_judge" in (a, b):
                o = "unchanged_cannot"
            elif a == b == "in_scope":
                o = "kept_in"
            elif a != "in_scope" and b != "in_scope":
                o = "moved_out"
            else:
                o = "unchanged_split"
            T[(P[i]["split"], o)] += 1
            f.write(json.dumps(dict(id=i, split=P[i]["split"], outcome=o, verdict_A=a, verdict_B=b,
                                    reason_A=v["A"][i]["reason"], reason_B=v["B"][i]["reason"],
                                    v1_wavg=round(wavg(P[i]), 3))) + "\n")
    agree = sum((v["A"][i]["verdict"] == "in_scope") == (v["B"][i]["verdict"] == "in_scope") for i in P)
    print(f"A/B binary agreement {agree}/{len(P)}")
    for sp in SPLITS:
        print(sp, {o: T[(sp, o)] for o in ("kept_in", "moved_out", "unchanged_split", "unchanged_cannot")})
    tot = Counter(o for (_, o), n in T.items() for _ in range(n))
    print("total", dict(tot), f"moved out share {tot['moved_out'] / len(P):.3f}")


RULED = {"demote": 238, "drop": 566, "keep_v1_label": 55}  # owner ruling 2026-10-03


def ruling():
    V = [json.loads(l) for l in open(D / "verdicts.jsonl")]

    def treat(v):
        if v["outcome"] != "moved_out":
            return "keep_v1_label"
        return "demote" if v["verdict_A"] == v["verdict_B"] == "out_one_moment" else "drop"

    got = Counter(treat(v) for v in V)
    if dict(got) != RULED:
        raise SystemExit(f"treatment counts {dict(got)} differ from the ruling {RULED}")
    with open(D / "treatment.jsonl", "w") as f:
        for v in V:
            f.write(json.dumps(dict(id=v["id"], split=v["split"], treatment=treat(v))) + "\n")
    print("treatment.jsonl:", dict(got), dict(Counter((v["split"], treat(v)) for v in V)))


if __name__ == "__main__":
    {"build": build, "import": import_, "ruling": ruling}[sys.argv[1]]()
