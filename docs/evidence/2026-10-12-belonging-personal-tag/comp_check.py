#!/usr/bin/env python3
"""Composition check for belonging c2c (PREREGISTRATION.md amendment B, this directory).

    # sadalsuud (stdlib only): the draw, every row of the newest 12 belonging filtered files, dedup by id
    python3 comp_check.py draw > belonging_comp_rows.jsonl
    # b650: score each package on the same rows, same order, same box (writes datasets/belonging_comp_scores/<pkg>.jsonl)
    PYTHONPATH=. HF_HUB_OFFLINE=1 venv-prodparity/bin/python comp_check.py score --package filters/belonging/v3
    # anywhere: the union of each model's top 30 (stage2 raw) plus the BASELINE's passes, as qwen tagger input
    python3 comp_check.py tops ROWS SCORES_DIR BASELINE PKG [PKG ...] > tag_input.jsonl
    # anywhere: the verdict, from the scores + qwen's tags
    python3 comp_check.py evaluate ROWS SCORES_DIR TAGS BASELINE CAND [CAND ...]
"""
import glob, json, os, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] if len(HERE.parents) > 2 else HERE   # the draw runs from /tmp on sadalsuud
NFILES, TOP, OP, BAR, RECALL_BAR = 12, 30, 4.0, 6, 0.9


def jl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def cmd_draw():
    files = sorted(glob.glob(os.path.expanduser("~/local_dev/NexusMind/data/filtered/belonging/filtered_*.jsonl")))[-NFILES:]
    seen = set()
    for p in reversed(files):                       # newest first: a re-scored id keeps its newest text
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            if r["id"] in seen or not r.get("content"):
                continue
            seen.add(r["id"])
            print(json.dumps(dict(id=r["id"], title=r.get("title"), content=r["content"], url=r.get("url"),
                                  source=r.get("source"), file=os.path.basename(p)), ensure_ascii=False))
    print(f"draw: {len(seen)} rows from {files[0][-35:]} .. {files[-1][-35:]}", file=sys.stderr)


def cmd_score(package, rows_path="datasets/belonging_comp_rows.jsonl"):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-03-belonging-heldout"))
    import torch
    import gate
    if not torch.cuda.is_available():
        raise SystemExit("REFUSED: no CUDA (every package is scored on b650 GPU)")
    pkg = (ROOT / package).resolve()
    out = ROOT / "datasets" / "belonging_comp_scores" / f"{pkg.name}.jsonl"
    if out.exists():
        raise SystemExit(f"REFUSED: {out} exists")
    rows = jl(ROOT / rows_path)
    if len({r["id"] for r in rows}) != len(rows):
        raise SystemExit("REFUSED: duplicate ids in the draw")
    scorer = gate.scorer_for(pkg)(use_prefilter=False)
    gate.assert_loads_from(pkg, scorer)
    res = scorer.score_batch([dict(id=r["id"], title=r["title"], content=r["content"], url=r["url"],
                                   source=r["source"]) for r in rows])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(json.dumps(dict(meta=dict(package=package, fingerprint=gate.pkg_fingerprint(pkg)[0], n=len(rows),
                                          device=torch.cuda.get_device_name(0)))) + "\n")
        for r, s in zip(rows, res):
            f.write(json.dumps(dict(id=r["id"], stage_used=s.get("stage_used"), raw=s.get("weighted_average"))) + "\n")
    print(f"wrote {out}: {Counter(s.get('stage_used') for s in res)}")


def load_scores(d, pkg, n):
    rows = jl(Path(d) / f"{pkg}.jsonl")
    meta, rows = rows[0]["meta"], rows[1:]
    if len(rows) != n:
        raise SystemExit(f"REFUSED: {pkg} scored {len(rows)} rows, the draw has {n}")
    out = {}
    for s in rows:
        if s["stage_used"] not in ("stage2", "stage1_low"):
            raise SystemExit(f"REFUSED: unknown stage_used {s['stage_used']!r} on {s['id']}")
        if s["stage_used"] == "stage2" and s["raw"] is None:
            raise SystemExit(f"REFUSED: stage2 row {s['id']} has no raw score")
        out[s["id"]] = s
    return meta, out


def top(scores):
    st2 = [s for s in scores.values() if s["stage_used"] == "stage2"]   # a stage1_low raw is a probe estimate
    return [s["id"] for s in sorted(st2, key=lambda s: (-s["raw"], s["id"]))[:TOP]]


def passes(s):
    return s["stage_used"] == "stage2" and s["raw"] >= OP


def cmd_tops(rows_path, d, *pkgs):
    rows = {r["id"]: r for r in jl(rows_path)}
    want = []
    for k, p in enumerate(pkgs):
        s = load_scores(d, p, len(rows))[1]
        ids = top(s) + ([i for i, x in s.items() if passes(x)] if k == 0 else [])   # pkgs[0] = baseline: its passes feed the recall guard
        for i in ids:
            if i not in want:
                want.append(i)
    for i in want:
        print(json.dumps(dict(id=i, title=rows[i]["title"], content=rows[i]["content"]), ensure_ascii=False))
    print(f"tops: {len(want)} distinct ids over {len(pkgs)} packages", file=sys.stderr)


def cmd_evaluate(rows_path, d, tags_path, baseline, *cands):
    rows = {r["id"]: r for r in jl(rows_path)}
    tags = {t["id"]: t["focus"] for t in jl(tags_path)}
    sc = {p: load_scores(d, p, len(rows))[1] for p in (baseline, *cands)}
    count = {}
    for p, s in sc.items():
        t = top(s)
        missing = [i for i in t if tags.get(i) not in ("personal", "group")]
        if missing:
            raise SystemExit(f"REFUSED: {len(missing)} of {p}'s top {TOP} untagged, e.g. {missing[0]}")
        count[p] = sum(tags[i] == "personal" for i in t)
        print(f"{p:14s} top {TOP}: personal {count[p]:2d}  (bar <= {BAR})")
    if count[baseline] <= BAR:
        print(f"UNDECIDABLE: the baseline {baseline} is already <= {BAR} on this draw")
    base_pass = [i for i, s in sc[baseline].items() if passes(s)]
    untagged = [i for i in base_pass if i not in tags]
    print(f"recall guard population: {baseline} passes {len(base_pass)} rows; {len(untagged)} untagged")
    ok = count[baseline] > BAR
    for p in cands:
        grp = [i for i in base_pass if tags.get(i) == "group"]
        kept = sum(passes(sc[p][i]) for i in grp)
        r = kept / len(grp) if grp else float("nan")
        good = count[p] <= BAR and r >= RECALL_BAR
        ok = ok and good
        print(f"{p:14s} recall guard: {kept}/{len(grp)} = {r:.3f} (bar >= {RECALL_BAR})  -> {'PASS' if good else 'FAIL'}")
    print("CHECK:", "PASS" if ok else ("UNDECIDABLE" if count[baseline] <= BAR else "FAIL"))


if __name__ == "__main__":
    c, a = sys.argv[1], sys.argv[2:]
    if c == "draw":
        cmd_draw()
    elif c == "score":
        cmd_score(a[a.index("--package") + 1])
    elif c == "tops":
        cmd_tops(*a)
    elif c == "evaluate":
        cmd_evaluate(*a)
    else:
        raise SystemExit(__doc__)
