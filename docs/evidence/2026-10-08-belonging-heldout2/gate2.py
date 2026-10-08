#!/usr/bin/env python3
"""Belonging retrain gate runner, HELD-OUT SET 2 (PREREGISTRATION.md here). A copy of ../2026-10-08-belonging-heldout2/gate2.py:
the SAME pass rule v2 (GATE.md, owner 2026-10-03, BINDING; one shot), on a 2x set (owner 2026-10-08: "only the size changes").
Changes, all size or seed: 800 rows/band, 100 sampled Gemini-outs/band, k_min scaled, new bootstrap seed, full text from the draw.

    # on b650 (GPU), once per package and row order; v1 is the reference
    PYTHONPATH=. .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/gate2.py score \
        --package filters/belonging/v1 --order forward  --out datasets/belonging_gate2/v1_forward.jsonl
    ... --order reversed ...; then the same for the candidate package

    # anywhere: the verdict (exit 0 = PASS, 1 = FAIL)
    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/gate2.py evaluate \
        --candidate filters/belonging/vN --scores-dir datasets/belonging_gate2

    # anywhere, needs no GPU: the rule run on v1's PRODUCTION raws, with controls that must FAIL / PASS
    .venv/bin/python docs/evidence/2026-10-08-belonging-heldout2/gate2.py controls

The rule, as code (each line is GATE.md § Pass rule v2):
- positives = both judges `in_scope` (N_POS, fixed in PREREGISTRATION.md § Result before any candidate is scored); a split or `cannot_judge` on either pass is excluded.
- deciding negatives = both judges out, EXCEPT Gemini-in rows whose classes are disputed (any class other than
  `out_one_moment` on either pass). Disputed rows are reported apart and never decide.
- a row is "in" only when `stage_used == "stage2"` and `weighted_average` >= the threshold (a `stage1_low` row's
  score is an e5 estimate: it is "out"). The package's `weighted_average` is what NexusMind stores as
  `raw_weighted_average` (normalization happens downstream).
- the candidate's threshold is its own op-point, read from its `base_scorer.py` `TIER_THRESHOLDS` "medium".
- k = positives the candidate finds; t* = the HIGHEST threshold at which v1 still finds >= k (v1's k-th highest
  stage-2 positive score).
- weight = band pool / 800, times band Gemini-outs / 100 for a sampled Gemini-out row (computed from
  `gemini_v2_2.jsonl` here, as `heldout.py analyse` does; `no_reply` counts as out).
- Δspec = spec(candidate @ op) − spec(v1 @ t*), weighted, on the deciding negatives; paired bootstrap stratified by
  band × pick, 2,000 resamples, seed 20261012. PASS needs the 95% lower bound > 0 AND k >= K_MIN = ceil(31/44 × N_POS),
  under BOTH orders (set 1's recall bar as a share, Claude's translation; owner ruling: only the size changes).
- the gate REFUSES a candidate without `training_manifest.jsonl` (one {"id", "url", "title", "text_head"} per
  training row, text_head = the first 1,000 chars of the training text, written by the build; every field required),
  and any candidate whose training rows touch the 2,400 held-out rows (a superset of the judged ones) by id,
  normalised url, normalised title or a normalised content window: the same story can sit under two ids, two
  outlets and two titles (review 2026-10-07 found held-out twins inside harvest r1, one a deciding negative).
- exit codes: 0 PASS, 1 FAIL, 2 REFUSED (a refusal is not a verdict).
- a labelled row that is not a scored `stage1_low`/`stage2` row with a finite score RAISES. An invalid or failed row
  is not a correct rejection (review 2026-10-07: counting it as "out" let a candidate PASS with every negative unscored).
"""
import argparse, ast, hashlib, importlib, inspect, json, math, os, platform, random, re, subprocess, sys, time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
import heldout2 as H  # noqa: E402  (rows, judges, Gemini verdicts: one implementation)

N_POS = None  # set from PREREGISTRATION.md § Result once the judges are in, BEFORE any candidate is scored; None refuses
SEED, NBOOT, NOISE = 20261012, 2000, 0.16
K_MIN = None if N_POS is None else math.ceil(31 / 44 * N_POS)
ORDERS = ("forward", "reversed")
UNDISPUTED = {"out_one_moment"}
V1 = ROOT / "filters" / "belonging" / "v1"
TRAINING_MANIFEST = "training_manifest.jsonl"  # one {"id", "url", "title", "text_head"} per training row (build)
STAGES = {"stage1_low", "stage2"}
MAX_NORMALIZATION_RAW_MIN = 4.5  # scripts/normalization/fit_normalization.py: NexusMind's loader silently falls back above it


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
        w = rs[i]["n_in_band"] / H.N_BAND * (gout[band] / H.N_OUT if p == "gemini_out_sample" else 1)
        lab[i] = dict(label=label, band=band, pick=p, weight=w, a=a, b=b)
    n = Counter(x["label"] for x in lab.values())
    if N_POS is None:
        raise SystemExit(f"{n['pos']} positives found; N_POS is not yet fixed in gate2.py (PREREGISTRATION.md § Result)")
    if n["pos"] != N_POS:
        raise SystemExit(f"{n['pos']} positives, PREREGISTRATION.md says {N_POS}: the judge files changed")
    return lab


# ---------------------------------------------------------------- the rule (pure; unit-tested)

def check_row(row):
    wa = row.get("weighted_average")
    if row.get("stage_used") not in STAGES or isinstance(wa, bool) or not isinstance(wa, (int, float)) or not math.isfinite(wa):
        raise SystemExit(f"row {row.get('id')}: stage_used={row.get('stage_used')!r} weighted_average={wa!r}. Only a "
                         "scored stage1_low/stage2 row can be judged; an invalid or failed row is NOT a correct rejection")


def is_in(row, t):
    check_row(row)
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
    missing = [i for i in lab if i not in cand or i not in v1]
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
    if med[0] > MAX_NORMALIZATION_RAW_MIN:
        raise SystemExit(f"{pkg}: op-point {med[0]} > {MAX_NORMALIZATION_RAW_MIN}; NexusMind's normalization loader "
                         "silently falls back above it (CLAUDE.md), so a production deploy would not run this op-point")
    norm = pkg / "normalization.json"
    if norm.exists():
        raw_min = json.load(open(norm))["stats"]["raw_min"]
        if abs(raw_min - med[0]) > 0.01:
            raise SystemExit(f"{pkg}: normalization.json raw_min {raw_min} != base_scorer medium {med[0]} "
                             "(an op-point lives in four places; CLAUDE.md)")
    return float(med[0])


def _norm_url(u):
    """Scheme, `www.`, fragment, trailing slash and TRACKING parameters dropped; the rest of the query is KEPT
    (WordPress `?p=167850` IS the article id: stripping it made 6 distinct aib.media stories one url)."""
    u = re.sub(r"^https?://(www\.)?", "", (u or "").strip().lower()).split("#")[0]
    base, _, q = u.partition("?")
    keep = sorted(x for x in q.split("&") if x and not re.match(r"(utm_[a-z]+|fbclid|gclid|mc_[a-z]+|ref)=", x))
    return base.rstrip("/") + ("?" + "&".join(keep) if keep else "")


def _norm_title(t):
    """Letters and digits in ANY script (a Latin-only class erased 85 Arabic/Greek/Cyrillic/... held-out titles)."""
    t = re.sub(r"[\W_]+", "", (t or "").lower())
    return t if len(t) >= 20 else None  # short titles ("Editorial") collide by chance


SHINGLE, SHINGLE_HITS = 8, 20


def _shingles(text):
    """8-word runs from words 10..160. Alignment-free, so a dateline or "Country:" prefix that differs between
    syndicated copies (newtimes.co.rw vs allafrica.com, review 2026-10-07) does not hide the twin; a fixed character
    window did."""
    w = re.findall(r"\w+", (text or "").lower())[10:160]
    return {tuple(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1)}


def content_twins(train, held):
    """[(train_id, held_id, shared_runs)] for pairs sharing >= SHINGLE_HITS distinctive 8-word runs. A run counts only
    if it occurs in ONE held-out row and at most two training rows: site boilerplate (cookie banners, series intros,
    newsletter footers) otherwise "matched" 13 different 20minutos stories to the same held-out row. Measured on
    harvest r1 (2026-10-07): syndicated copies share 85-142 runs; 20-55 is a mix of real twins and same-series
    boilerplate, so 20 over-refuses on purpose (a false hit costs one training row, a miss leaks a held-out story).
    The build should call this BEFORE training and drop what it returns."""
    hs = {r["id"]: _shingles(r.get("content")) for r in held}
    ts = {r["id"]: _shingles(r.get("text_head")) for r in train}
    dfh = Counter(sh for x in hs.values() for sh in x)
    dft = Counter(sh for x in ts.values() for sh in x)
    index = defaultdict(set)
    for i, x in hs.items():
        for sh in x:
            if dfh[sh] == 1:
                index[sh].add(i)
    out = []
    for i, x in ts.items():
        c = Counter(h for sh in x if dft[sh] <= 2 for h in index.get(sh, ()))
        out += [(i, h, n) for h, n in c.items() if n >= SHINGLE_HITS]
    return sorted(out)


def refuse_overlap(pkg, held=None):
    """The candidate must carry its training manifest, and no training row may be a held-out row by id, url or title.
    v1 is the reference: exempt (the held-out draw was asserted disjoint from v1's sources when it was made)."""
    if pkg.resolve() == V1.resolve():
        return "v1 (reference): exempt"
    f = pkg / TRAINING_MANIFEST
    if not f.exists():
        raise SystemExit(f"REFUSED: {f} missing. The build must write every training row (GATE.md § The runner).")
    train = [json.loads(l) for l in open(f) if l.strip()]
    if not train:
        raise SystemExit(f"REFUSED: {f} is empty")
    thin = [r.get("id") for r in train if not all(isinstance(r.get(k), str) and r[k].strip()
                                                   for k in ("id", "url", "title", "text_head"))]
    if thin:
        raise SystemExit(f"REFUSED: {len(thin)} manifest rows lack id/url/title/text_head, e.g. {thin[:3]}; an id-only "
                         "manifest would shrink the overlap check to ids")
    held = H.rows() if held is None else held
    keys = {"id": lambda r: r.get("id"), "url": lambda r: _norm_url(r.get("url")) or None,
            "title": lambda r: _norm_title(r.get("title"))}
    for name, k in keys.items():
        hk = {k(r) for r in held} - {None}
        hit = sorted({k(r) for r in train} & hk)
        if hit:
            raise SystemExit(f"REFUSED: {len(hit)} training rows match held-out rows by {name}, e.g. {hit[:3]}")
    twins = content_twins(train, held)
    if twins:
        raise SystemExit(f"REFUSED: {len(twins)} training rows match held-out rows by content "
                         f"(>= {SHINGLE_HITS} shared {SHINGLE}-word runs), e.g. {twins[:3]}")
    return f"{len(train)} training rows, 0 of the {len(held)} held-out rows by id, url, title or content"


def _hash_tree(root, files):
    h = hashlib.sha256()
    for p in files:
        h.update(os.path.relpath(p, root).encode()); h.update(Path(p).read_bytes())
    return h.hexdigest()[:16], len(files)


def _scoring_file(name):
    """What scoring can load: not docs (*.md: b650's v1 has a model/README.md this machine lacks, review 2026-10-07),
    not hidden or editor files, not bytecode."""
    return not (name.startswith(".") or name.endswith((".md", ".pyc", "~", ".swp", ".swo")))


def pkg_fingerprint(pkg):
    """Every scoring file in the package, following symlinked folders (rglob skipped a symlinked model/)."""
    files = sorted(os.path.join(d, f) for d, ds, fs in os.walk(pkg, followlinks=True) if "__pycache__" not in d
                   for f in fs if _scoring_file(f))
    return _hash_tree(pkg, files)


def common_fingerprint():
    """The shared scoring code every package runs through (hybrid_scorer, filter_base_scorer, model_loading, ...)."""
    d = ROOT / "filters" / "common"
    return _hash_tree(d, sorted(str(p) for p in d.glob("*.py")))[0]


def _version(dist):
    from importlib.metadata import version, PackageNotFoundError
    try:
        return version(dist)
    except PackageNotFoundError:
        return "absent"


STACK = ("text", "text_fingerprint", "device", "host", "prefix", "batch_size", "common_fingerprint", "torch",
         "transformers", "peft", "scikit-learn", "sentence-transformers", "tokenizers")
CUT = 4000


def scoring_text(rs, ids):
    """FULL article text (owner ruling 2026-10-07): the draw stores `full_content`; the cut `content` must be its prefix."""
    out = {}
    for i in ids:
        c, full = rs[i]["content"], rs[i].get("full_content")
        if not isinstance(full, str) or not full.startswith(c) or (len(c) < CUT and full != c):
            raise SystemExit(f"{i}: full_content missing or does not match the cut content")
        out[i] = full
    return out


def assert_loads_from(pkg, scorer):
    """The scorer must load its model and probe from THIS package. belonging v1's code imports
    `filters.belonging.v1.inference`, whose default model path is v1/model: a copied package that keeps those imports
    scores v1's weights under the candidate's name (found 2026-10-07 while staging the first candidate)."""
    paths = {"model": getattr(scorer.stage2_scorer, "model_path", None), "probe": getattr(scorer, "_probe_path", None)}
    for what, p in paths.items():
        if p is None or pkg.resolve() not in Path(p).resolve().parents:
            raise SystemExit(f"REFUSED: {pkg.name}'s scorer loads its {what} from {p}, outside the package")


def refuse_v1_clone(pkg):
    if pkg.resolve() != V1.resolve() and pkg_fingerprint(pkg)[0] == pkg_fingerprint(V1)[0]:
        raise SystemExit(f"REFUSED: {pkg.name} is byte-identical to v1 (same fingerprint)")


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
    refuse_v1_clone(pkg)
    import torch
    if not torch.cuda.is_available() and not a.allow_cpu:
        raise SystemExit("no CUDA: GATE.md scores both packages on b650 GPU (--allow-cpu only for a dry run)")
    rs, lab = {r["id"]: r for r in H.rows()}, labelled()
    ids = sorted(lab)
    if a.order == "reversed":
        ids.reverse()
    text = scoring_text(rs, ids)
    arts = [dict(id=i, title=rs[i]["title"], content=text[i], url=rs[i]["url"], source=rs[i]["source"]) for i in ids]
    text_fp = hashlib.sha256("".join(text[i] for i in sorted(text)).encode()).hexdigest()[:16]
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite (one shot)")
    out.parent.mkdir(parents=True, exist_ok=True)
    scorer = scorer_for(pkg)(use_prefilter=False)
    assert_loads_from(pkg, scorer)
    batch_size = inspect.signature(scorer.score_batch).parameters["batch_size"].default
    t0 = time.time()
    res = scorer.score_batch(arts)  # the package's default batch size, as production calls it
    fp, nfiles = pkg_fingerprint(pkg)
    meta = dict(package=str(pkg.relative_to(ROOT)), fingerprint=fp, n_files=nfiles, op_point=op_point(pkg),
                order=a.order, n=len(ids), seconds=round(time.time() - t0, 1), overlap=overlap,
                text="full (owner 2026-10-07)", text_fingerprint=text_fp,
                device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
                peak_vram_mib=round(torch.cuda.max_memory_allocated() / 2**20) if torch.cuda.is_available() else None,
                host=platform.node(), prefix=sys.prefix, batch_size=batch_size, common_fingerprint=common_fingerprint(),
                git=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                   capture_output=True, text=True).stdout.strip(),
                ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **{k: _version(k) for k in ("torch", "transformers", "peft", "scikit-learn", "sentence-transformers",
                                            "tokenizers")})
    with open(out, "w") as f:
        f.write(json.dumps(dict(meta=meta)) + "\n")
        for i, r in zip(ids, res):
            f.write(json.dumps(dict(id=i, stage_used=r.get("stage_used"), weighted_average=r.get("weighted_average"),
                                    stage1_estimate=r.get("stage1_estimate"), tier=r.get("tier"))) + "\n")
    print(f"wrote {out}: {Counter(r.get('stage_used') for r in res)}; {meta['device']}, {meta['seconds']}s")


def load_scores(path, order, ids):
    """One `score` output: its meta must name `order`, and its rows must be exactly `ids` in that order, each scored."""
    lines = [json.loads(l) for l in open(path)]
    meta, body = lines[0]["meta"], lines[1:]
    want = sorted(ids)[::-1] if order == "reversed" else sorted(ids)
    if meta.get("order") != order:
        raise SystemExit(f"{path}: meta order {meta.get('order')!r}, expected {order!r}")
    if [r["id"] for r in body] != want or meta.get("n") != len(want):
        raise SystemExit(f"{path}: rows are not the {len(want)} labelled ids in {order} order")
    for r in body:
        check_row(r)
    return meta, {r["id"]: r for r in body}


def report(lab, cand, v1, op, ts, tag):
    """Everything GATE.md lists under 'Also reported' that this set can compute."""
    by = defaultdict(list)
    for i, x in lab.items():
        by[x["label"]].append(i)
    himid = [i for i in by["neg"] if lab[i]["band"] in ("hi", "mid")]
    print(f"  [{tag}] unweighted spec on deciding negatives: cand {spec(cand, op, by['neg'], lab, False):.3f} | "
          f"v1@t* {spec(v1, ts, by['neg'], lab, False):.3f}")
    print(f"  [{tag}] hi+mid only (n={len(himid)}): weighted cand {spec(cand, op, himid, lab):.3f} | v1@t* "
          f"{spec(v1, ts, himid, lab):.3f}; unweighted cand {spec(cand, op, himid, lab, False):.3f} | v1@t* "
          f"{spec(v1, ts, himid, lab, False):.3f}")
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
    refuse_v1_clone(cand_pkg)
    op, v1_op = op_point(cand_pkg), op_point(V1)
    lab = labelled()
    print(f"labels: {dict(Counter(x['label'] for x in lab.values()))}; candidate op-point {op} (v1 live op-point {v1_op})")
    print("strata: the rule names 6 (band x pick); a stratum with no deciding negatives (near/gemini_in today: its "
          "Gemini-in hard negatives are all disputed) simply has no rows to resample")
    sd, verdicts, scored = Path(a.scores_dir), [], {}
    cand_name = cand_pkg.name
    for order in ORDERS:
        mc, cand = load_scores(sd / f"{cand_name}_{order}.jsonl", order, lab)
        mv, v1 = load_scores(sd / f"v1_{order}.jsonl", order, lab)
        if mc["package"] != str(cand_pkg.relative_to(ROOT)) or mv["package"] != "filters/belonging/v1":
            raise SystemExit(f"{order}: score files are for {mc['package']} / {mv['package']}")
        if mc["fingerprint"] != pkg_fingerprint(cand_pkg)[0] or mv["fingerprint"] != pkg_fingerprint(V1)[0]:
            raise SystemExit(f"{order}: a package changed since it was scored (fingerprint mismatch)")
        diff = {k: (mc.get(k), mv.get(k)) for k in STACK if mc.get(k) != mv.get(k) or mc.get(k) is None}
        if diff:
            raise SystemExit(f"{order}: the two packages were not scored on the same stack: {diff}")
        r = decide(lab, cand, v1, op)
        scored[order] = (cand, v1, r["t_star"])
        verdicts.append(r["passed"])
        print(f"\n=== order {order} ({mc['device']}, torch {mc['torch']}, {mc['host']})")
        print(f"  k = {r['k']}/{N_POS} at op {op}; v1 matched at t* = {r['t_star']:.4f}")
        print(f"  deciding negatives n={r['n_neg']} {r['strata']}")
        print(f"  spec weighted: cand {r['spec_cand']:.4f} | v1@t* {r['spec_v1']:.4f} | Δ {r['delta']:+.4f} "
              f"95% CI [{r['lo']:+.4f}, {r['hi']:+.4f}]")
        print(f"  ORDER VERDICT: {'PASS' if r['passed'] else 'FAIL: ' + '; '.join(r['reasons'])}")
        report(lab, cand, v1, op, r["t_star"], order)
    ts = scored["forward"][2]
    for name, j, t in (("cand", 0, op), ("v1", 1, ts), ("v1", 1, v1_op)):
        f, rv = scored["forward"][j], scored["reversed"][j]
        flips = sum(is_in(f[i], t) != is_in(rv[i], t) for i in lab)
        print(f"order-to-order verdict flips, {name} at {t:.4f}: {flips}/{len(lab)} (t* forward {ts:.4f}, "
              f"reversed {scored['reversed'][2]:.4f})" if name == "v1" and t == ts else
              f"order-to-order verdict flips, {name} at {t:.4f}: {flips}/{len(lab)}")
    lab_ = lab
    print("\nDISPUTED rows by judge class (do not decide; PREREGISTRATION.md: the classes candidate 2 targets are mostly here):")
    for cls in sorted({x["a"] for x in lab_.values() if x["label"] == "disputed"} | {x["b"] for x in lab_.values() if x["label"] == "disputed"}):
        ids = [i for i, x in lab_.items() if x["label"] == "disputed" and cls in (x["a"], x["b"])]
        c, v = scored["forward"][0], scored["forward"][1]
        print(f"  {cls}: n={len(ids)}; unweighted spec cand@op {spec(c, op, ids, lab_, False):.3f} | v1@t* {spec(v, ts, ids, lab_, False):.3f}"
              f" | v1@{v1_op} {spec(v, v1_op, ids, lab_, False):.3f}")
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
    cut = sorted(pos)[:N_POS - (K_MIN - 1)]  # an oracle that finds K_MIN - 1 positives
    weak = {i: dict(stage_used="stage1_low" if i in cut else "stage2", weighted_average=oracle[i]["weighted_average"])
            for i in lab}
    cases = [("v1 vs itself at 4.0", prod, 4.0, False), ("v1 at 5.8 vs v1 (the refuted rule's pass)", prod, 5.8, False),
             ("perfect candidate", oracle, 4.0, True), (f"perfect on negatives, {K_MIN - 1}/{N_POS} found", weak, 4.0, False)]
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
    e.add_argument("--scores-dir", default="datasets/belonging_gate2")
    sub.add_parser("controls")
    a = ap.parse_args()
    try:
        {"score": cmd_score, "evaluate": cmd_evaluate, "controls": cmd_controls}[a.cmd](a)
    except SystemExit as e:
        if isinstance(e.code, str):  # a refusal or a broken input, never a verdict
            print(e.code, file=sys.stderr)
            sys.exit(2)
        raise
