#!/usr/bin/env python3
"""Re-label the 242-row calibration set under rubric v2.1 (START HERE item 0.1, 2026-10-03). See CALIBRATION.md § Step 6.

    .venv/bin/python docs/evidence/2026-10-02-belonging-adjudication/relabel_v2_1.py build [v2_1|v2_2]
    .venv/bin/python docs/evidence/2026-10-02-belonging-adjudication/relabel_v2_1.py import [v2_1|v2_2]

The version (default v2_1) picks the rubric copy whose sha the import checks, the seeds, the batch directory and the
output key. v2_2 (2026-10-03) is the same procedure after the owner amended ruling 3; its judges read
rubric_belonging_v2.md, which then held v2.2.

build   two independent blind passes (A, B) over EVERY calibration row. Each pass is its own shuffle into 5 batches,
        with its own opaque ids, so neither the batch nor the id tells a judge (or the other pass) where a row came
        from. The judges see only judge_instructions_v2.md + rubric_belonging_v2.md (v2.1, sha recorded) and the text
        every oracle read. They see no oracle verdict and no prior label. Writes the gitignored
        datasets/belonging_adjudication/relabel_v2_1/{A1..A5,B1..B5}/input.jsonl and id_map.json.
import  checks each out.jsonl (ids = input ids in input order, verdicts valid), maps back, and writes
        calib_key_v2_1.jsonl: label = consensus of A and B (`split` when they disagree), plus the owner's own
        verdicts as a separate column (`owner`: in / out / unsure), never folded into the judge label.
"""
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "datasets" / "belonging_adjudication"
# version -> (the verbatim rubric copy the judges read (via rubric_belonging_v2.md at the time), pass seeds)
VERSIONS = {"v2_1": ("rubric_belonging_v2_1.md", (1003, 2003)), "v2_2": ("rubric_belonging_v2.md", (1004, 2004))}
VER = sys.argv[2] if len(sys.argv) > 2 else "v2_1"
BASE = DATA / f"relabel_{VER}"
RUBRIC = HERE / VERSIONS[VER][0]
VERDICTS = ["in_scope", "out_gift_official", "out_one_moment", "out_harm_is_story", "out_culture_topic",
            "out_event_spectated", "out_other", "cannot_judge"]
NBATCH = 5
# The owner's own verdicts on calibration rows, by article id. Pilot v2 spot-check (spot_check_v2_owner.tsv) and the
# Step 5 DIY ruling, and (v2_2 only, since it postdates the v2_1 relabel) the 2026-10-03 owner check
# (spot_check_v2_1_owner.tsv, mapped through spot_check_v2_1_key.tsv). Recorded beside the judge label, never
# substituted for it.
OWNER = {"pilot3:british_irish_bbc_northern_ireland_dc99721a35e2": "in"}


def owner_labels(key):
    by_id = {k["id"]: k["calib_id"] for k in key}
    out = dict(OWNER)
    lines = (HERE / "spot_check_v2_owner.tsv").read_text().splitlines()
    hdr = lines[0].split("\t")
    for line in lines[1:]:
        r = dict(zip(hdr, line.split("\t")))
        if r["id"] not in by_id:
            raise SystemExit(f"owner row {r['id']} is not in the calibration set")
        out[by_id[r["id"]]] = r["owner"]
    if len(out) != len(lines) - 1 + len(OWNER):
        raise SystemExit("owner rows overlap")
    if VER != "v2_1":
        n2c = {r.split("\t")[0]: r.split("\t")[1] for r in (HERE / "spot_check_v2_1_key.tsv").read_text().splitlines()[1:]}
        for r in (HERE / "spot_check_v2_1_owner.tsv").read_text().splitlines()[1:]:
            f = r.split("\t")
            if n2c[f[0]] in out:
                raise SystemExit(f"owner row {n2c[f[0]]} judged twice")
            out[n2c[f[0]]] = f[-1]
    return out


def build():
    rows = [json.loads(l) for l in open(DATA / "calib" / "calib_set.jsonl")]
    key = [json.loads(l) for l in open(HERE / "calib_key.jsonl")]
    if sorted(r["calib_id"] for r in rows) != sorted(k["calib_id"] for k in key) or len(rows) != 242:
        raise SystemExit("calib_set.jsonl and calib_key.jsonl do not hold the same 242 rows")
    if BASE.exists():
        raise SystemExit(f"{BASE} exists; refusing to overwrite judge inputs")
    rubric_sha = hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16]
    id_map = {}
    for p, seed in zip("AB", VERSIONS[VER][1]):
        order = rows[:]
        random.Random(seed).shuffle(order)
        for b in range(NBATCH):
            d = BASE / f"{p}{b + 1}"
            (d / "scratch").mkdir(parents=True)
            with open(d / "input.jsonl", "w") as f:
                for r in order[b::NBATCH]:
                    oid = hashlib.sha256(f"{p}:{seed}:{r['calib_id']}".encode()).hexdigest()[:12]
                    id_map[oid] = r["calib_id"]
                    f.write(json.dumps(dict(id=oid, title=r.get("title"), url=r.get("url"), source=r.get("source"),
                                            content=r.get("content")), ensure_ascii=False) + "\n")
    if len(id_map) != 2 * len(rows):
        raise SystemExit("opaque id collision")
    json.dump(dict(rubric_file=RUBRIC.name, rubric_sha=rubric_sha, id_map=id_map), open(BASE / "id_map.json", "w"))
    print(f"built {2 * NBATCH} batches over {len(rows)} rows; rubric {RUBRIC.name} sha {rubric_sha}")


def import_():
    m = json.load(open(BASE / "id_map.json"))
    now = hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16]
    if now != m["rubric_sha"]:
        raise SystemExit(f"rubric changed since build ({m['rubric_sha']} -> {now})")
    v = {"A": {}, "B": {}}
    for d in sorted(BASE.glob("[AB][0-9]")):
        inp = [json.loads(l)["id"] for l in open(d / "input.jsonl")]
        out = [json.loads(l) for l in open(d / "out.jsonl")]
        if [r["id"] for r in out] != inp:
            raise SystemExit(f"{d.name}: ids are not the input ids in input order")
        for r in out:
            if r["verdict"] not in VERDICTS:
                raise SystemExit(f"{d.name}: {r['id']} verdict {r['verdict']!r}")
            v[d.name[0]][m["id_map"][r["id"]]] = r
    key = [json.loads(l) for l in open(HERE / "calib_key.jsonl")]
    for p in v:
        if sorted(v[p]) != sorted(k["calib_id"] for k in key):
            raise SystemExit(f"pass {p} does not cover the calibration set exactly once")
    owner = owner_labels(key)
    with open(HERE / f"calib_key_{VER}.jsonl", "w") as f:
        for k in key:
            a, b = v["A"][k["calib_id"]]["verdict"], v["B"][k["calib_id"]]["verdict"]
            if "cannot_judge" in (a, b):
                label = "cannot_judge" if a == b else "split"
            else:
                ai, bi = a == "in_scope", b == "in_scope"
                label = ("in" if ai else "out") if ai == bi else "split"
            f.write(json.dumps(dict(calib_id=k["calib_id"], id=k["id"], source_set=k["source_set"], label=label,
                                    label_kind=f"judge_consensus_{VER}", verdict_A=a, verdict_B=b,
                                    owner=owner.get(k["calib_id"]), label_v2_0=k["label"],
                                    named_in_rubric_v2_1=k["named_in_rubric_v2_1"],
                                    rubric_sha=m["rubric_sha"])) + "\n")
    ks = [json.loads(l) for l in open(HERE / f"calib_key_{VER}.jsonl")]
    print(len(ks), "rows;", dict(Counter(k["label"] for k in ks)))
    print(f"v2.0 -> {VER} label moves:", dict(Counter((k["label_v2_0"], k["label"]) for k in ks if k["label_v2_0"] != k["label"])))


if __name__ == "__main__":
    {"build": build, "import": import_}[sys.argv[1]]()
