#!/usr/bin/env python3
"""Belonging held-out set 2 (PREREGISTRATION.md here). A copy of ../2026-10-08-belonging-heldout2/heldout2.py at 2x:
800 rows per band, 100 sampled Gemini-outs per band, new seeds. Rows: gitignored datasets/belonging_heldout2/.

    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/heldout2.py check
    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/heldout2.py gemini [--limit N]
    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/heldout2.py build-judges
    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/heldout2.py analyse

Stage A reuses the calibration's call()/parse()/prompt_for() unchanged (same prompt template and Gemini settings).
"""
import argparse, hashlib, json, random, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAL = ROOT / "docs" / "evidence" / "2026-10-02-belonging-adjudication"
sys.path.insert(0, str(CAL)); sys.path.insert(0, str(ROOT))
import calibrate_scope_oracles as cso  # noqa: E402
from belonging_exclusions import assert_is_source  # noqa: E402

DATA = ROOT / "datasets" / "belonging_heldout2"
ROWS, GEM, JUDGE = DATA / "heldout2_rows.jsonl", DATA / "gemini_v2_2.jsonl", DATA / "judges"
RUBRIC = CAL / "rubric_belonging_v2.md"
RUBRIC_SHA = "d450b79510418cf7"  # frozen v2.2 (PREREGISTRATION.md)
BANDS, N_OUT, PER_BATCH, N_BAND = ("hi", "mid", "near"), 100, 50, 800


# Dropped AFTER the draw, BEFORE any oracle or judge call (PREREGISTRATION.md § Amendment 1): twins of v1_adj1/c2a/c2b
# training rows by gate2's own overlap check (title or 8-word-run content). The draw excluded ids only.
DROPPED = {"positive_news_upworthy_35dd196e7214", "romanian_hotnews_1e3c52d614a9",
           "british_irish_independent_uk_b7b6d44c13aa", "austrian_krone_a1b472c6c601"}


def drawn():
    return [json.loads(l) for l in open(ROWS)]


def rows():
    rs = [r for r in drawn() if r["id"] not in DROPPED]
    if len(rs) != 3 * N_BAND - len(DROPPED):
        raise SystemExit(f"{len(rs)} rows after dropping {len(DROPPED)}: a DROPPED id is not in the draw")
    return rs


def band_n(rs):
    """Rows actually held per band (800 minus that band's drops): the design weight's denominator."""
    return Counter(r["band"] for r in rs)


def check():
    rs = drawn()
    if hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16] != RUBRIC_SHA:
        raise SystemExit("rubric is not the frozen v2.2")
    ids = [r["id"] for r in rs]
    if len(ids) != 3 * N_BAND or len(set(ids)) != 3 * N_BAND or Counter(r["band"] for r in rs) != Counter({b: N_BAND for b in BANDS}):
        raise SystemExit(f"draw shape wrong: {len(ids)} rows, {len(set(ids))} distinct, {Counter(r['band'] for r in rs)}")
    assert_is_source(ids, "held-out set 2 2026-10-08")
    print(f"ok: {3 * N_BAND} distinct rows drawn, {N_BAND}/band, in belonging_exclusions as a source, rubric frozen; "
          f"held after drops: {dict(band_n(rows()))}")


def gemini(limit, workers=8):
    check()
    from ground_truth.secrets_manager import get_secrets_manager
    keys = {"gemini": get_secrets_manager().get_llm_key("gemini")}
    rubric, template = RUBRIC.read_text(), (CAL / "oracle_scope_prompt.md").read_text()
    prompt_sha = hashlib.sha256((rubric + "\x00" + template).encode()).hexdigest()[:16]
    done = {json.loads(l)["id"] for l in open(GEM) if "error" not in json.loads(l)} if GEM.exists() else set()
    todo = [r for r in rows() if r["id"] not in done][: limit or None]
    print(f"gemini: {len(done)} done, {len(todo)} to call", flush=True)

    def one(r):
        rec = dict(id=r["id"], band=r["band"], prompt_sha=prompt_sha, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        try:
            text, usage, model, secs = cso.call("gemini", cso.prompt_for(r, rubric, template), keys)
            rec.update(model=model, usage=usage, seconds=round(secs, 2), raw=text)
            d = cso.parse(text)
            rec.update(verdict=d["verdict"], quote=d.get("quote", ""), reason=d.get("reason", ""))
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:300]
            if "FATAL" in str(e):
                raise
        return rec

    with open(GEM, "a") as f:
        ex = ThreadPoolExecutor(max_workers=workers)
        try:
            for fut in as_completed([ex.submit(one, r) for r in todo]):
                f.write(json.dumps(fut.result(), ensure_ascii=False) + "\n"); f.flush()
        finally:
            ex.shutdown(wait=True, cancel_futures=True)
    recs = [json.loads(l) for l in open(GEM)]
    print(f"gemini: {sum('error' not in r for r in recs)} ok, {sum('error' in r for r in recs)} error lines")


def gem_latest():
    """Latest valid verdict per row. A row whose every reply was EMPTY (0 output tokens; 2 rows, twice each on
    2026-10-03, probably a safety block, finish reason not recorded) gets verdict `no_reply`: counted as not-in,
    like cannot_judge (PREREGISTRATION.md), and reported apart. Any other error-only row raises."""
    g, err = {}, {}
    for l in open(GEM):
        r = json.loads(l)
        if "error" not in r:
            g[r["id"]] = r
        else:
            err.setdefault(r["id"], []).append(r)
    shas = {r.get("prompt_sha") for r in g.values()}
    if len(shas) > 1:
        raise SystemExit(f"{GEM.name} mixes prompts {shas}; a resumed run after a template edit")
    for i, es in err.items():
        if i in g:
            continue
        if all((e.get("usage") or {}).get("output") == 0 and not e.get("raw") for e in es):
            g[i] = dict(id=i, band=es[0]["band"], verdict="no_reply", n_attempts=len(es))
        else:
            raise SystemExit(f"{i}: errors other than empty replies: {es[-1]['error']}")
    return g


def build_judges():
    rs, g = {r["id"]: r for r in rows()}, gem_latest()
    if set(g) != set(rs):
        raise SystemExit(f"gemini covers {len(g)} of {len(rs)} rows; finish stage A first")
    if JUDGE.exists():
        raise SystemExit(f"{JUDGE} exists; refusing to overwrite")
    pick = {i: "gemini_in" for i in rs if g[i]["verdict"] == "in_scope"}
    rng = random.Random(20261011)
    for b in BANDS:
        outs = sorted(i for i in rs if rs[i]["band"] == b and g[i]["verdict"] != "in_scope")
        for i in rng.sample(outs, N_OUT):
            pick[i] = "gemini_out_sample"
    ids, id_map = sorted(pick), {}
    nb = -(-len(ids) // PER_BATCH)
    for p, seed in (("A", 41), ("B", 42)):
        order = ids[:]
        random.Random(seed).shuffle(order)
        for b in range(nb):
            d = JUDGE / f"{p}{b + 1}"
            (d / "scratch").mkdir(parents=True)
            with open(d / "input.jsonl", "w") as f:
                for i in order[b::nb]:
                    oid = hashlib.sha256(f"heldout2:{p}:{i}".encode()).hexdigest()[:12]
                    id_map[oid] = i
                    r = rs[i]
                    f.write(json.dumps(dict(id=oid, title=r["title"], url=r["url"], source=r["source"],
                                            content=r["content"]), ensure_ascii=False) + "\n")
    json.dump(dict(rubric_sha=RUBRIC_SHA, id_map=id_map, pick=pick), open(JUDGE / "id_map.json", "w"))
    print(f"{len(ids)} rows to judge ({Counter(pick.values())}), {nb} batches per pass")


def judges():
    """Both passes, mapped back; ids must equal the inputs in order and every picked row judged once per pass."""
    m = json.load(open(JUDGE / "id_map.json"))
    if m["rubric_sha"] != hashlib.sha256(RUBRIC.read_bytes()).hexdigest()[:16]:
        raise SystemExit("rubric changed since the judge build")
    v = {"A": {}, "B": {}}
    for d in sorted(JUDGE.glob("[AB][0-9]*")):
        inp = [json.loads(l)["id"] for l in open(d / "input.jsonl")]
        out = [json.loads(l) for l in open(d / "out.jsonl")]
        if [r["id"] for r in out] != inp:
            raise SystemExit(f"{d.name}: ids are not the input ids in input order")
        for r in out:
            if r["verdict"] not in cso.VERDICTS:
                raise SystemExit(f"{d.name}: verdict {r['verdict']!r}")
            v[d.name[0]][m["id_map"][r["id"]]] = r
    for p in v:
        if set(v[p]) != set(m["pick"]):
            raise SystemExit(f"pass {p} does not cover the picked rows exactly once")
    return m["pick"], v


def analyse():
    rs, g = {r["id"]: r for r in rows()}, gem_latest()
    pick, v = judges()
    lab = {}
    for i in pick:
        a, b = (v[p][i]["verdict"] == "in_scope" for p in "AB")
        lab[i] = dict(both=a and b, either=a or b, split=a != b)
    agree = sum(not x["split"] for x in lab.values())
    print(f"judged {len(pick)} rows; A/B binary agreement {agree}/{len(pick)}; splits {len(pick) - agree}")
    print(f"judge cannot_judge: A {sum(r['verdict'] == 'cannot_judge' for r in v['A'].values())}, "
          f"B {sum(r['verdict'] == 'cannot_judge' for r in v['B'].values())}")
    print(f"gemini no_reply rows: {[i for i, r in g.items() if r['verdict'] == 'no_reply']}")
    tot = {}
    for rule in ("both", "either"):
        print(f"\n=== label rule: {rule} judge(s) say in")
        T = Counter()
        for b in BANDS:
            ids = [i for i in rs if rs[i]["band"] == b]
            pool = rs[ids[0]]["n_in_band"]
            gin = [i for i in ids if g[i]["verdict"] == "in_scope"]
            gout = [i for i in ids if g[i]["verdict"] != "in_scope"]
            samp = [i for i in gout if pick.get(i) == "gemini_out_sample"]
            if len(samp) != N_OUT:
                raise SystemExit(f"{b}: {len(samp)} sampled outs, expected {N_OUT}")
            w_out = len(gout) / len(samp)
            tp = sum(lab[i][rule] for i in gin)
            fp = len(gin) - tp
            miss = sum(lab[i][rule] for i in samp)
            fn_est = miss * w_out
            tn_est = (len(samp) - miss) * w_out
            pos = tp + fn_est
            rate = pos / len(ids)
            rec = tp / pos if pos else float("nan")
            spec = tn_est / (tn_est + fp)
            line = (f"  [{b}] pool {pool}: gemini in {len(gin)}/{len(ids)}; hit {tp}/{len(gin)} = {tp / max(1, len(gin)):.2f}; "
                    f"misses in {len(samp)} sampled outs: {miss} (x{w_out:.2f}); in-rate {rate:.3f} "
                    f"(~{rate * pool:.0f} rows in the band); recall {rec:.2f}; specificity {spec:.3f}")
            if miss == 0:
                line += f"; 0 misses -> rule-of-3 recall lower bound {tp / (tp + 3 / len(samp) * len(gout)) if tp else 0:.2f}"
            print(line)
            s_ = pool / len(ids)
            fn_ub = max(fn_est, 3 / len(samp) * len(gout)) if miss == 0 else fn_est  # rule of 3 when 0 misses seen
            T.update(tp=tp * s_, fn=fn_est * s_, fn_ub=fn_ub * s_, fp=fp * s_, tn=tn_est * s_, pop=pool,
                     gin=len(gin) * s_)
        print(f"  [population, weighted] rows {T['pop']:,}; est. positives {T['tp'] + T['fn']:.0f} "
              f"(rate {(T['tp'] + T['fn']) / T['pop']:.4f}); gemini-in {T['gin']:.0f}; hit {T['tp'] / T['gin']:.2f}; "
              f"recall {T['tp'] / (T['tp'] + T['fn']):.2f} (lower bound, rule of 3 where 0 misses: "
              f"{T['tp'] / (T['tp'] + T['fn_ub']):.2f}); specificity {T['tn'] / (T['tn'] + T['fp']):.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "gemini", "build-judges", "analyse"])
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    {"check": check, "gemini": lambda: gemini(a.limit), "build-judges": build_judges, "analyse": analyse}[a.cmd]()
