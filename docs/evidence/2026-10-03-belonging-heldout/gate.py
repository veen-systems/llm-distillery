#!/usr/bin/env python3
"""Belonging retrain gate runner: GATE.md § Pass rule v2 (owner, 2026-10-03 close). BINDING; one shot.

    # on b650 (GPU), once per package and row order; v1 is the reference
    PYTHONPATH=. .venv/bin/python docs/evidence/2026-10-03-belonging-heldout/gate.py score \
        --package filters/belonging/v1 --order forward  --out datasets/belonging_gate/v1_forward.jsonl
    ... --order reversed ...; then the same for the candidate package

    # anywhere: the verdict (exit 0 = PASS, 1 = FAIL)
    .venv/bin/python docs/evidence/2026-10-03-belonging-heldout/gate.py evaluate \
        --candidate filters/belonging/vN --scores-dir datasets/belonging_gate

    # anywhere, needs no GPU: the rule run on v1's PRODUCTION raws, with controls that must FAIL / PASS
    .venv/bin/python docs/evidence/2026-10-03-belonging-heldout/gate.py controls

The rule, as code (each line is GATE.md § Pass rule v2):
- positives = both judges `in_scope` (44); a split or `cannot_judge` on either pass is excluded.
- deciding negatives = both judges out, EXCEPT Gemini-in rows whose classes are disputed (any class other than
  `out_one_moment` on either pass). Disputed rows are reported apart and never decide.
- a row is "in" only when `stage_used == "stage2"` and `weighted_average` >= the threshold (a `stage1_low` row's
  score is an e5 estimate: it is "out"). The package's `weighted_average` is what NexusMind stores as
  `raw_weighted_average` (normalization happens downstream).
- the candidate's threshold is its own op-point, read from its `base_scorer.py` `TIER_THRESHOLDS` "medium".
- k = positives the candidate finds; t* = the HIGHEST threshold at which v1 still finds >= k (v1's k-th highest
  stage-2 positive score).
- weight = band pool / 400, times band Gemini-outs / 50 for a sampled Gemini-out row (computed from
  `gemini_v2_2.jsonl` here, as `heldout.py analyse` does; `no_reply` counts as out).
- Δspec = spec(candidate @ op) − spec(v1 @ t*), weighted, on the deciding negatives; paired bootstrap stratified by
  band × pick, 2,000 resamples, seed 20261009. PASS needs the 95% lower bound > 0 AND k >= 31, under BOTH orders.
- the gate REFUSES a candidate without `training_ids.txt` (one id per line, written by the build), and any candidate
  whose training ids touch the 1,200 held-out rows (a superset of the 295 judged ones).
"""
import argparse, ast, hashlib, importlib, json, math, platform, random, subprocess, sys, time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
import heldout as H  # noqa: E402  (rows, judges, Gemini verdicts: one implementation)

SEED, NBOOT, K_MIN, N_POS, NOISE = 20261009, 2000, 31, 44, 0.16
ORDERS = ("forward", "reversed")
UNDISPUTED = {"out_one_moment"}
V1 = ROOT / "filters" / "belonging" / "v1"
TRAINING_IDS = "training_ids.txt"


# ---------------------------------------------------------------- labels and weights (no model involved)

def classify(a, b, pick):
    """Two judge verdicts (passes A, B) and the row's pick -> pos | neg | disputed | excluded."""
    if "cannot_judge" in (a, b) or (a == "in_scope") != (b == "in_scope"):
        return "excluded"
    if a == "in_scope":
        return "pos"
    if pick == "gemini_in" and not {a, b} <= UNDISPUTED:
        return "disputed"  # a Gemini-in hard negative in a class the owner kept about half the time
    return "neg"


def labelled():
    """id -> {label: pos|neg|disputed|excluded, band, pick, weight, a, b}. Asserts the shape GATE.md states."""
    rs, g = {r["id"]: r for r in H.rows()}, H.gem_latest()
    pick, v = H.judges()
    gout, samp = Counter(), Counter()
    for i, r in rs.items():
        if g[i]["verdict"] != "in_scope":
            gout[r["band"]] += 1
            samp[r["band"]] += pick.get(i) == "gemini_out_sample"
    if any(samp[b] != H.N_OUT for b in H.BANDS):
        raise SystemExit(f"sampled Gemini-outs per band {dict(samp)}, expected {H.N_OUT} each")
    lab = {}
    for i, p in pick.items():
        a, b = v["A"][i]["verdict"], v["B"][i]["verdict"]
        label = classify(a, b, p)
        band = rs[i]["band"]
        w = rs[i]["n_in_band"] / 400 * (gout[band] / H.N_OUT if p == "gemini_out_sample" else 1)
        lab[i] = dict(label=label, band=band, pick=p, weight=w, a=a, b=b)
    n = Counter(x["label"] for x in lab.values())
    if n["pos"] != N_POS:
        raise SystemExit(f"{n['pos']} positives, GATE.md says {N_POS}: the judge files changed")
    return lab


# ---------------------------------------------------------------- the rule (pure; unit-tested)

def is_in(row, t):
    return row["stage_used"] == "stage2" and row["weighted_average"] >= t


def spec(scores, t, ids, lab, weighted=True):
    w = [(lab[i]["weight"] if weighted else 1.0, not is_in(scores[i], t)) for i in ids]
    tot = sum(x for x, _ in w)
    return sum(x for x, out in w if out) / tot if tot else float("nan")


def t_star(v1, pos, k):
    """HIGHEST threshold at which v1 still finds >= k of the positives."""
    if k == 0:
        return math.inf
    s = sorted((v1[i]["weighted_average"] for i in pos if v1[i]["stage_used"] == "stage2"), reverse=True)
    if len(s) < k:
        raise SystemExit(f"v1 has {len(s)} stage-2 positives, cannot match k={k}")
    return s[k - 1]


def ci95(deltas):
    """Percentile 95% interval: with 2,000 resamples, the 51st and the 1,950th smallest."""
    d, n = sorted(deltas), len(deltas)
    return d[int(0.025 * n)], d[math.ceil(0.975 * n) - 1]


def decide(lab, cand, v1, op, seed=SEED, nboot=NBOOT):
    """One row order. Returns the deciding numbers and the verdict for that order."""
    pos = sorted(i for i in lab if lab[i]["label"] == "pos")
    neg = sorted(i for i in lab if lab[i]["label"] == "neg")
    missing = [i for i in pos + neg if i not in cand or i not in v1]
    if missing:
        raise SystemExit(f"{len(missing)} labelled rows not scored, e.g. {missing[:3]}")
    k = sum(is_in(cand[i], op) for i in pos)
    ts = t_star(v1, pos, k)
    strata = defaultdict(list)
    for i in neg:
        strata[(lab[i]["band"], lab[i]["pick"])].append(i)
    sn, sv = spec(cand, op, neg, lab), spec(v1, ts, neg, lab)
    rng, deltas = random.Random(seed), []
    for _ in range(nboot):
        ids = [i for s in sorted(strata) for i in rng.choices(strata[s], k=len(strata[s]))]
        deltas.append(spec(cand, op, ids, lab) - spec(v1, ts, ids, lab))
    lo, hi = ci95(deltas)
    reasons = []
    if not lo > 0:
        reasons.append(f"Δspec 95% lower bound {lo:+.4f} is not > 0")
    if k < K_MIN:
        reasons.append(f"k = {k} < {K_MIN}")
    return dict(k=k, t_star=ts, op=op, spec_cand=sn, spec_v1=sv, delta=sn - sv, lo=lo, hi=hi,
                n_neg=len(neg), strata={f"{b}/{p}": len(x) for (b, p), x in sorted(strata.items())},
                passed=not reasons, reasons=reasons)


# ---------------------------------------------------------------- packages

def op_point(pkg):
    """`TIER_THRESHOLDS` "medium" from the package's base_scorer.py (read as source, never restated by hand)."""
    tree = ast.parse((pkg / "base_scorer.py").read_text())
    found = [ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", None) == "TIER_THRESHOLDS" for t in n.targets)]
    if len(found) != 1:
        raise SystemExit(f"{pkg}/base_scorer.py: {len(found)} TIER_THRESHOLDS assignments, expected 1")
    med = [t[1] for t in found[0] if t[0] == "medium"]
    if len(med) != 1:
        raise SystemExit(f"{pkg}: no single 'medium' tier in TIER_THRESHOLDS")
    norm = pkg / "normalization.json"
    if norm.exists():
        raw_min = json.load(open(norm))["stats"]["raw_min"]
        if abs(raw_min - med[0]) > 0.01:
            raise SystemExit(f"{pkg}: normalization.json raw_min {raw_min} != base_scorer medium {med[0]} "
                             "(an op-point lives in four places; CLAUDE.md)")
    return float(med[0])


def refuse_overlap(pkg):
    """The candidate must carry its training ids, and none may be a held-out row. v1 is the reference: exempt
    (the held-out draw was asserted disjoint from v1's sources when it was made)."""
    if pkg.resolve() == V1.resolve():
        return "v1 (reference): exempt"
    f = pkg / TRAINING_IDS
    if not f.exists():
        raise SystemExit(f"REFUSED: {f} missing. The build must write every training id (GATE.md, last line).")
    train = {l.strip() for l in open(f) if l.strip()}
    if not train:
        raise SystemExit(f"REFUSED: {f} is empty")
    held = {r["id"] for r in H.rows()}
    hit = train & held
    if hit:
        raise SystemExit(f"REFUSED: {len(hit)} training ids are held-out rows, e.g. {sorted(hit)[:3]}")
    return f"{len(train)} training ids, 0 of the {len(held)} held-out rows"


def pkg_fingerprint(pkg):
    h = hashlib.sha256()
    files = sorted(p for p in pkg.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                   and p.suffix in {".safetensors", ".bin", ".pkl", ".json", ".py", ".yaml"})
    for p in files:
        h.update(str(p.relative_to(pkg)).encode()); h.update(p.read_bytes())
    return h.hexdigest()[:16], len(files)


def scorer_for(pkg):
    mod = importlib.import_module(".".join(pkg.resolve().relative_to(ROOT).parts) + ".inference_hybrid")
    from filters.common.hybrid_scorer import HybridScorer
    cls = [c for c in vars(mod).values() if isinstance(c, type) and issubclass(c, HybridScorer) and c is not HybridScorer]
    if len(cls) != 1:
        raise SystemExit(f"{pkg}/inference_hybrid.py: {len(cls)} HybridScorer subclasses, expected 1")
    return cls[0]


# ---------------------------------------------------------------- commands

def cmd_score(a):
    pkg = (ROOT / a.package).resolve()
    overlap = refuse_overlap(pkg)
    import torch
    if not torch.cuda.is_available() and not a.allow_cpu:
        raise SystemExit("no CUDA: GATE.md scores both packages on b650 GPU (--allow-cpu only for a dry run)")
    rs, lab = {r["id"]: r for r in H.rows()}, labelled()
    ids = sorted(lab)
    if a.order == "reversed":
        ids.reverse()
    arts = [dict(id=i, title=rs[i]["title"], content=rs[i]["content"], url=rs[i]["url"], source=rs[i]["source"])
            for i in ids]
    scorer = scorer_for(pkg)(use_prefilter=False)
    t0 = time.time()
    res = scorer.score_batch(arts)  # the package's default batch size, as production calls it
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite (one shot)")
    fp, nfiles = pkg_fingerprint(pkg)
    import transformers, peft
    meta = dict(package=str(pkg.relative_to(ROOT)), fingerprint=fp, n_files=nfiles, op_point=op_point(pkg),
                order=a.order, n=len(ids), seconds=round(time.time() - t0, 1), overlap=overlap,
                device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
                peak_vram_mib=round(torch.cuda.max_memory_allocated() / 2**20) if torch.cuda.is_available() else None,
                torch=torch.__version__, transformers=transformers.__version__, peft=peft.__version__,
                host=platform.node(), git=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                                         capture_output=True, text=True).stdout.strip(),
                ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(out, "w") as f:
        f.write(json.dumps(dict(meta=meta)) + "\n")
        for i, r in zip(ids, res):
            f.write(json.dumps(dict(id=i, stage_used=r.get("stage_used"), weighted_average=r.get("weighted_average"),
                                    stage1_estimate=r.get("stage1_estimate"), tier=r.get("tier"))) + "\n")
    print(f"wrote {out}: {Counter(r.get('stage_used') for r in res)}; {meta['device']}, {meta['seconds']}s")


def load_scores(path):
    lines = [json.loads(l) for l in open(path)]
    meta, rows = lines[0]["meta"], {r["id"]: r for r in lines[1:]}
    if len(rows) != meta["n"]:
        raise SystemExit(f"{path}: {len(rows)} rows, meta says {meta['n']}")
    return meta, rows


def report(lab, cand, v1, op, ts, tag):
    """Everything GATE.md lists under 'Also reported' that this set can compute."""
    by = defaultdict(list)
    for i, x in lab.items():
        by[x["label"]].append(i)
    himid = [i for i in by["neg"] if lab[i]["band"] in ("hi", "mid")]
    print(f"  [{tag}] unweighted spec on deciding negatives: cand {spec(cand, op, by['neg'], lab, False):.3f} | "
          f"v1@t* {spec(v1, ts, by['neg'], lab, False):.3f}")
    print(f"  [{tag}] hi+mid only (weighted): cand {spec(cand, op, himid, lab):.3f} | v1@t* {spec(v1, ts, himid, lab):.3f} "
          f"(n={len(himid)})")
    d = by["disputed"]
    print(f"  [{tag}] DISPUTED hard negatives (do not decide), n={len(d)}: spec weighted cand "
          f"{spec(cand, op, d, lab):.3f} | v1@t* {spec(v1, ts, d, lab):.3f}; unweighted cand "
          f"{spec(cand, op, d, lab, False):.3f} | v1@t* {spec(v1, ts, d, lab, False):.3f}")
    for name, sc, t in (("cand", cand, op), ("v1", v1, ts)):
        near = [i for i in by["pos"] + by["neg"] + d
                if sc[i]["stage_used"] == "stage2" and abs(sc[i]["weighted_average"] - t) <= NOISE]
        print(f"  [{tag}] {name}: {len(near)} judged rows within ±{NOISE} of its threshold {t:.3f} (could flip on batch "
              f"composition, #95)")


def cmd_evaluate(a):
    cand_pkg = (ROOT / a.candidate).resolve()
    print(f"candidate {cand_pkg.relative_to(ROOT)}: {refuse_overlap(cand_pkg)}")
    op, v1_op = op_point(cand_pkg), op_point(V1)
    lab = labelled()
    print(f"labels: {dict(Counter(x['label'] for x in lab.values()))}; candidate op-point {op} (v1 live op-point {v1_op})")
    sd, verdicts, scored = Path(a.scores_dir), [], {}
    cand_name = cand_pkg.name
    for order in ORDERS:
        mc, cand = load_scores(sd / f"{cand_name}_{order}.jsonl")
        mv, v1 = load_scores(sd / f"v1_{order}.jsonl")
        if mc["package"] != str(cand_pkg.relative_to(ROOT)) or mv["package"] != "filters/belonging/v1":
            raise SystemExit(f"{order}: score files are for {mc['package']} / {mv['package']}")
        if mc["fingerprint"] != pkg_fingerprint(cand_pkg)[0] or mv["fingerprint"] != pkg_fingerprint(V1)[0]:
            raise SystemExit(f"{order}: a package changed since it was scored (fingerprint mismatch)")
        same = ("device", "torch", "transformers", "peft", "host")
        diff = {k: (mc[k], mv[k]) for k in same if mc[k] != mv[k]}
        if diff:
            raise SystemExit(f"{order}: the two packages were not scored on the same stack: {diff}")
        r = decide(lab, cand, v1, op)
        scored[order] = (cand, v1)
        verdicts.append(r["passed"])
        print(f"\n=== order {order} ({mc['device']}, torch {mc['torch']}, {mc['host']})")
        print(f"  k = {r['k']}/{N_POS} at op {op}; v1 matched at t* = {r['t_star']:.4f}")
        print(f"  deciding negatives n={r['n_neg']} {r['strata']}")
        print(f"  spec weighted: cand {r['spec_cand']:.4f} | v1@t* {r['spec_v1']:.4f} | Δ {r['delta']:+.4f} "
              f"95% CI [{r['lo']:+.4f}, {r['hi']:+.4f}]")
        print(f"  ORDER VERDICT: {'PASS' if r['passed'] else 'FAIL: ' + '; '.join(r['reasons'])}")
        report(lab, cand, v1, op, r["t_star"], order)
    for name, j in (("cand", 0), ("v1", 1)):
        f, rv = scored["forward"][j], scored["reversed"][j]
        flips = sum(is_in(f[i], op if j == 0 else v1_op) != is_in(rv[i], op if j == 0 else v1_op) for i in lab)
        print(f"order-to-order verdict flips, {name} at its own op-point: {flips}/{len(lab)}")
    print("\nNOT computed here (GATE.md 'Also reported'): v1's test split under treatment.jsonl "
          "(plan phase 6, ground_truth_gate.py), the owner's 10 rows (owner_check_*.tsv) as a per-row table.")
    ok = all(verdicts)
    print(f"\nGATE VERDICT (both orders must pass): {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


def cmd_controls(_):
    """The rule on v1's PRODUCTION stage-2 raws (heldout_rows.jsonl `raw`; the draw was on stage-2 rows), no GPU.
    Each control states the verdict the rule MUST give; a wrong one raises."""
    rs, lab = {r["id"]: r for r in H.rows()}, labelled()
    n = Counter(x["label"] for x in lab.values())
    hard = [i for i in lab if lab[i]["pick"] == "gemini_in" and lab[i]["label"] in ("neg", "disputed")]
    print(f"labels {dict(n)}; Gemini-in both-out (hard) negatives {len(hard)}, of which disputed {n['disputed']}")
    prod = {i: dict(stage_used="stage2", weighted_average=rs[i]["raw"]) for i in lab}
    pos = [i for i in lab if lab[i]["label"] == "pos"]
    oracle = {i: dict(stage_used="stage2", weighted_average=10.0 if lab[i]["label"] == "pos" else 0.0) for i in lab}
    cut = sorted(pos)[:N_POS - 30]  # an oracle that misses 14 positives: finds 30
    weak = {i: dict(stage_used="stage1_low" if i in cut else "stage2", weighted_average=oracle[i]["weighted_average"])
            for i in lab}
    cases = [("v1 vs itself at 4.0", prod, 4.0, False), ("v1 at 5.8 vs v1 (the refuted rule's pass)", prod, 5.8, False),
             ("perfect candidate", oracle, 4.0, True), ("perfect on negatives, 30/44 found", weak, 4.0, False)]
    for name, cand, op, want in cases:
        r = decide(lab, cand, prod, op)
        print(f"  {name}: k={r['k']} t*={r['t_star']:.3f} Δ={r['delta']:+.4f} CI [{r['lo']:+.4f}, {r['hi']:+.4f}] -> "
              f"{'PASS' if r['passed'] else 'FAIL'} (must {'PASS' if want else 'FAIL'})")
        if r["passed"] != want:
            raise SystemExit(f"CONTROL BROKEN: {name}")
    print("controls ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score"); s.add_argument("--package", required=True); s.add_argument("--order", choices=ORDERS, required=True)
    s.add_argument("--out", required=True); s.add_argument("--allow-cpu", action="store_true")
    e = sub.add_parser("evaluate"); e.add_argument("--candidate", required=True)
    e.add_argument("--scores-dir", default="datasets/belonging_gate")
    sub.add_parser("controls")
    a = ap.parse_args()
    {"score": cmd_score, "evaluate": cmd_evaluate, "controls": cmd_controls}[a.cmd](a)
