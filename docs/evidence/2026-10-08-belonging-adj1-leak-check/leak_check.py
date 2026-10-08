#!/usr/bin/env python3
"""belonging adj1 pre-gate leak check (PREREGISTRATION.md in this directory; owner 2026-10-08).

    # here: the id list the draw must avoid
    python3 leak_check.py exclude > datasets/belonging_leak_exclude_ids.txt
    # sadalsuud (stdlib only): the draw
    python3 leak_check.py draw belonging_leak_exclude_ids.txt > belonging_leak_rows.jsonl
    # b650: score both packages on the same rows, same order
    PYTHONPATH=. HF_HUB_OFFLINE=1 venv-prodparity/bin/python leak_check.py score --package filters/belonging/v1
    PYTHONPATH=. HF_HUB_OFFLINE=1 venv-prodparity/bin/python leak_check.py score --package filters/belonging/v1_adj1
    # anywhere: the verdict (exit 0 NOT LEAKED / 1 LEAKED / 2 REFUSED)
    python3 leak_check.py evaluate
"""
import glob, json, os, random, sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
D = ROOT / "datasets"
ROWS, OUT = D / "belonging_leak_rows.jsonl", D / "belonging_leak_scores"
N, SEED, NBOOT, OP, RATIO, LONG = 5000, 20261008, 10000, 4.0, 1.5, 4000
PKGS = ("filters/belonging/v1", "filters/belonging/v1_adj1")
BINS = [(0, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, None)]


def jl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def cmd_exclude():
    sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-02-belonging-adjudication"))
    from belonging_exclusions import excluded_ids
    ex = set(excluded_ids())
    srcs = [D / "belonging_v1_adj" / f"{s}.jsonl" for s in ("train", "val", "test")]
    srcs += [D / "training" / "belonging_v1_adj1" / f"{s}.jsonl" for s in ("train", "val", "test")]
    srcs += [D / "belonging_harvest_r1" / "harvest_r1_rows.jsonl", D / "belonging_easyneg_rows.jsonl"]
    for p in srcs:
        ids = {r["id"] for r in jl(p)}
        if not ids:
            raise SystemExit(f"REFUSED: exclusion source empty: {p}")
        ex |= ids
    print("\n".join(sorted(ex)))
    print(f"{len(ex)} excluded ids from {len(srcs)} files + belonging_exclusions", file=sys.stderr)


def cmd_draw(exclude_file):
    """Same population rules as draw_easy_negatives.py; adds the row's language stamp."""
    d = os.path.expanduser("~/local_dev/NexusMind/data/filtered/belonging/")
    ex = set(open(exclude_file).read().split())
    seen_ids, seen_hash, pool = set(), set(), []
    n = dict(rows=0, bad=0, gn=0, short=0, excluded=0, dup=0)
    files = sorted(glob.glob(d + "filtered_*.jsonl"))
    for fi, f in enumerate(files):
        with open(f) as fh:
            for ln, line in enumerate(fh):
                n["rows"] += 1
                try:
                    r = json.loads(line)
                except ValueError:
                    n["bad"] += 1; continue
                content, h = r.get("content") or "", r.get("content_hash")
                if "news.google.com" in (r.get("url") or ""):
                    n["gn"] += 1; continue
                if len(content) < 300:
                    n["short"] += 1; continue
                if r["id"] in ex:
                    n["excluded"] += 1; continue
                if r["id"] in seen_ids or (h and h in seen_hash):
                    n["dup"] += 1; continue
                seen_ids.add(r["id"])
                if h:
                    seen_hash.add(h)
                pool.append((r["id"], fi, ln))
    pick = random.Random(SEED).sample(sorted(pool), N)
    want = {}
    for _, fi, ln in pick:
        want.setdefault(fi, set()).add(ln)
    out = 0
    for fi, lines in sorted(want.items()):
        with open(files[fi]) as fh:
            for ln, line in enumerate(fh):
                if ln in lines:
                    r = json.loads(line)
                    print(json.dumps(dict(id=r["id"], title=r.get("title"), url=r.get("url"), source=r.get("source"),
                                          content=r.get("content"), language=r.get("language"),
                                          language_source=(r.get("metadata") or {}).get("language_source"),
                                          file=os.path.basename(files[fi])), ensure_ascii=False))
                    out += 1
    if out != N:
        raise SystemExit(f"REFUSED: wrote {out} rows, expected {N}")
    n.update(out=out, pool=len(pool), files=len(files),
             window=f"{os.path.basename(files[0])} .. {os.path.basename(files[-1])}")
    print(json.dumps(n), file=sys.stderr)


def cmd_score(package):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "docs" / "evidence" / "2026-10-03-belonging-heldout"))
    import torch
    import gate  # scorer_for / assert_loads_from: one implementation with the gate
    if not torch.cuda.is_available():
        raise SystemExit("REFUSED: no CUDA (both packages are scored on b650 GPU)")
    pkg = (ROOT / package).resolve()
    out = OUT / f"{pkg.name}.jsonl"
    if out.exists():
        raise SystemExit(f"REFUSED: {out} exists")
    rows = jl(ROWS)
    if len(rows) != N or len({r["id"] for r in rows}) != N:
        raise SystemExit(f"REFUSED: {ROWS} has {len(rows)} rows / ids, expected {N}")
    scorer = gate.scorer_for(pkg)(use_prefilter=False)
    gate.assert_loads_from(pkg, scorer)
    arts = [dict(id=r["id"], title=r["title"], content=r["content"], url=r["url"], source=r["source"]) for r in rows]
    res = scorer.score_batch(arts)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(json.dumps(dict(meta=dict(package=package, fingerprint=gate.pkg_fingerprint(pkg)[0], n=len(rows),
                                          device=torch.cuda.get_device_name(0)))) + "\n")
        for r, s in zip(rows, res):
            f.write(json.dumps(dict(id=r["id"], stage_used=s.get("stage_used"),
                                    raw=s.get("weighted_average"))) + "\n")
    print(f"wrote {out}: {Counter(s.get('stage_used') for s in res)}")


def flagged(s):
    if s["stage_used"] not in ("stage2", "stage1_low"):
        raise SystemExit(f"REFUSED: unknown stage_used {s['stage_used']!r} on {s['id']}")
    if s["stage_used"] == "stage2" and s["raw"] is None:
        raise SystemExit(f"REFUSED: stage2 row {s['id']} has no raw score")
    return s["stage_used"] == "stage2" and s["raw"] >= OP


def compare(ids, v1, cand):
    a = [flagged(v1[i]) for i in ids]
    b = [flagged(cand[i]) for i in ids]
    n = len(ids)
    if n == 0:
        return dict(n=0)
    rv, rc = sum(a) / n, sum(b) / n
    rng = random.Random(SEED)
    d = sorted((lambda k: sum(b[j] - a[j] for j in k) / n)([rng.randrange(n) for _ in range(n)]) for _ in range(NBOOT))
    lo, hi = d[int(0.025 * NBOOT)], d[int(0.975 * NBOOT) - 1]
    ratio = None if rv == 0 else rc / rv
    leaked = (rv == 0 or rc >= RATIO * rv) and lo > 0
    return dict(n=n, v1_flags=sum(a), cand_flags=sum(b), v1_rate=round(rv, 4), cand_rate=round(rc, 4),
                ratio=None if ratio is None else round(ratio, 3), gap_ci95=[round(lo, 4), round(hi, 4)], leaked=leaked)


def cmd_evaluate():
    rows = {r["id"]: r for r in jl(ROWS)}
    sc = {}
    for p in PKGS:
        f = OUT / f"{Path(p).name}.jsonl"
        if not f.exists():
            print(f"REFUSED: {f} missing"); sys.exit(2)
        recs = jl(f)
        sc[p] = {r["id"]: r for r in recs[1:]}
        if set(sc[p]) != set(rows):
            print(f"REFUSED: {f} does not cover the drawn rows"); sys.exit(2)
    v1, cand = sc[PKGS[0]], sc[PKGS[1]]
    split = sum((v1[i]["stage_used"] == "stage1_low") != (cand[i]["stage_used"] == "stage1_low") for i in rows)
    ids = sorted(rows)
    L = lambda i: len(rows[i]["content"] or "")  # noqa: E731
    groups = {"LONG (>4000 chars)": [i for i in ids if L(i) > LONG],
              "FRENCH (language=fr)": [i for i in ids if rows[i].get("language") == "fr"]}
    ctx = {"ALL": ids}
    for lo, hi in BINS:
        ctx[f"len {lo}-{hi or 'inf'}"] = [i for i in ids if L(i) >= lo and (hi is None or L(i) < hi)]
    for lang, _ in Counter(rows[i].get("language") for i in ids).most_common(8):
        ctx[f"lang {lang}"] = [i for i in ids if rows[i].get("language") == lang]
    rep = dict(stage1_split_disagreements=split,
               language_source=dict(Counter(rows[i].get("language_source") for i in ids).most_common()),
               decisive={k: compare(v, v1, cand) for k, v in groups.items()},
               context={k: compare(v, v1, cand) for k, v in ctx.items()})
    rep["verdict"] = "LEAKED" if any(g.get("leaked") for g in rep["decisive"].values()) else "NOT LEAKED"
    json.dump(rep, open(OUT / "result.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))
    sys.exit(1 if rep["verdict"] == "LEAKED" else 0)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "exclude":
        cmd_exclude()
    elif cmd == "draw":
        cmd_draw(sys.argv[2])
    elif cmd == "score" and sys.argv[2:3] == ["--package"]:
        cmd_score(sys.argv[3])
    elif cmd == "evaluate":
        cmd_evaluate()
    else:
        raise SystemExit(__doc__)
