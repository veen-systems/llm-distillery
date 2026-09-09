#!/usr/bin/env python3
"""Three analyses behind the 2026-09-09 adverse-pool consult with the NexusMind session.

No oracle calls, no network, $0.

  A. Judge-agreement structure of EXP-031's harm panel — is kappa 0.375 the right
     statistic for deciding whether one judge can screen alone?
  B. Corpus coverage — does human_thriving v8's labelled corpus contain the failure
     mode v9/#156 must learn (harm content scoring at or above the op-point)?
  C. Judge competence across language — does the rubric's `fits` clause leak fluency?

⛔ INPUT PROVENANCE. Part A's inputs are committed in this repo. **Part B's are NOT** —
`datasets/*` is gitignored (`.gitignore:83`), so `labels_v84_merged.jsonl` is not in any
clone. Pinned by sha256 below and asserted at load; a clean checkout gets a clear error,
not a wrong number.

⛔ DESIGN WEIGHTS. The label corpus is a 6,586-row subset of the 6,590-row STRATIFIED
draw in `corpus.jsonl`, whose `inclusion_probability` spans 25.132x. Every share Part B
prints is reported BOTH unweighted (a sample rate) and design-weighted (Horvitz-Thompson,
the production estimate). Counts, maxima and zeros are weight-invariant and are printed once.
# design-weights: datasets/scored/human_thriving_v8/corpus.jsonl inclusion_probability

⛔ THE AGGREGATE IS DECLARED BY THE PRODUCER, NOT CHOSEN HERE. Every row carries
`aggregate_used`, and it is "all" on 6,586/6,586 — so the score is `weighted_mean_all`.
An earlier version of this script preferred `weighted_mean_major` with a fallback, which
silently unioned two populations and published 351/5.3% where the declared aggregate gives
316/4.798%. Asserted uniform at load; a mixed corpus raises.

Run:  python3 docs/evidence/2026-09-09-adverse-pool-consult/analyze.py
Committed output: analyze.txt
"""
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PANEL = os.path.join(ROOT, "docs", "evidence", "2026-09-08-thriving-harm-panel")
LABELS = os.path.join(ROOT, "datasets", "scored", "human_thriving_v8", "labels_v84_merged.jsonl")
CORPUS = os.path.join(ROOT, "datasets", "scored", "human_thriving_v8", "corpus.jsonl")
LABELS_SHA256 = "b085b01b07d835eff93f3507e1dad940de594c4e7edcf14fcd2dda8a990d614c"

ORD = ["harmful", "misleading", "weak", "fits"]


def rule(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def op_point():
    """Read the op-point by EXECUTING the runtime surface, never from config.yaml.
    CLAUDE.md: TIER_THRESHOLDS in base_scorer.py is the sole runtime source."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)          # base_scorer imports filters.common.*
    p = os.path.join(ROOT, "filters", "human_thriving", "v8", "base_scorer.py")
    spec = importlib.util.spec_from_file_location("_ht_v8_base_scorer", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = next(v for v in vars(mod).values()
               if isinstance(v, type) and hasattr(v, "TIER_THRESHOLDS"))
    val = dict((n, t) for n, t, _ in cls.TIER_THRESHOLDS)["medium"]
    assert isinstance(val, float), f"op-point is not a float: {val!r}"
    return val


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_panel():
    frame = {}
    with open(os.path.join(PANEL, "panel_frame.jsonl")) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                frame[r["id"]] = r
    ds = {r["id"]: r for r in json.load(open(os.path.join(PANEL, "judge_deepseek_k3.json")))}
    gm = {r["id"]: r for r in json.load(open(os.path.join(PANEL, "judge_gemini_k1.json")))}
    ids = sorted(set(ds) & set(gm) & set(frame))
    assert len(ids) == 137, f"expected the 137-row panel, got {len(ids)}"
    assert not [i for i in ids if ds[i]["majority"] == "ERROR" or gm[i]["majority"] == "ERROR"]
    for i in ids:                       # missing case must RAISE, never default
        frame[i]["language"], frame[i]["stratum"]
    return frame, ds, gm, ids


def load_corpus():
    if not os.path.exists(LABELS):
        raise SystemExit(f"MISSING INPUT: {LABELS}\n  datasets/* is gitignored; this file is "
                         f"not in a clean clone. Expected sha256 {LABELS_SHA256}")
    got = sha256(LABELS)
    assert got == LABELS_SHA256, f"label corpus changed: {got} != {LABELS_SHA256}"
    rows = [json.loads(l) for l in open(LABELS) if l.strip()]
    assert len(rows) == 6586, f"expected 6586 label rows, got {len(rows)}"
    aggs = {r["human_thriving_analysis"]["aggregate_used"] for r in rows}   # raises if absent
    assert aggs == {"all"}, f"aggregate_used is not uniformly 'all': {aggs}"
    weights = {}
    with open(CORPUS) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                weights[r["id"]] = 1.0 / r["inclusion_probability"]
    missing = [r["id"] for r in rows if r["id"] not in weights]
    assert not missing, f"{len(missing)} label rows carry no design weight"
    return rows, weights


def kappa(a, b, keys, cats):
    assert set(a[k] for k in keys) | set(b[k] for k in keys) <= set(cats), \
        "kappa(): a value outside `cats` would make pe=0 and silently return accuracy"
    n = len(keys)
    po = sum(a[i] == b[i] for i in keys) / n
    ca, cb = Counter(a[i] for i in keys), Counter(b[i] for i in keys)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return (po - pe) / (1 - pe), po


def part_a(frame, ds, gm, ids):
    rule("A. JUDGE AGREEMENT — is kappa 0.375 the statistic that decides single-judge screening?")
    dm = {i: ds[i]["majority"] for i in ids}
    gmm = {i: gm[i]["majority"] for i in ids}
    k4, po4 = kappa(dm, gmm, ids, ORD)
    print(f"  4-class Cohen kappa = {k4:.4f}   (agree {int(round(po4*len(ids)))}/{len(ids)}, "
          f"disagree {len(ids)-int(round(po4*len(ids)))})")

    conf = Counter((dm[i], gmm[i]) for i in ids)
    print("\n  Confusion, rows = DeepSeek k=3 majority, cols = Gemini k=1:")
    print("  " + " " * 12 + "".join(f"{c:>12}" for c in ORD))
    for r in ORD:
        print("  " + f"{r:12}" + "".join(f"{conf.get((r,c),0):>12}" for c in ORD))

    dh = {i: str(dm[i] == "harmful") for i in ids}
    gh = {i: str(gmm[i] == "harmful") for i in ids}
    nd = sum(v == "True" for v in dh.values())
    ng = sum(v == "True" for v in gh.values())
    both = sum(1 for i in ids if dh[i] == "True" and gh[i] == "True")
    only_d = sum(1 for i in ids if dh[i] == "True" and gh[i] == "False")
    kb, _ = kappa(dh, gh, ids, ["True", "False"])
    print(f"\n  BINARY harmful:  DeepSeek {nd}   Gemini {ng}   overlap {both}   "
          f"DeepSeek-only {only_d}")
    print(f"  binary-harmful kappa = {kb:.4f}")
    print(f"  ⛔ the binary kappa is NOT better than the 4-class {k4:.4f} — they are")
    print(f"     indistinguishable. The screen argument rests on NESTING, not on kappa.")

    assert only_d == 0, "nesting does not hold — the screen conclusion below is void"
    p = comb(ng, nd) / comb(len(ids), nd)
    print(f"\n  NESTED: every DeepSeek-harmful row is also Gemini-harmful. "
          f"P(by chance) = {p:.3g}")
    print(f"  ⚠️  that null is INDEPENDENCE between two judges reading the same articles —")
    print(f"     guaranteed false, so it establishes correlation, NOT screen safety.")
    ro3 = 3.0 / nd
    print(f"  ⚠️  screen safety is 0 misses in {nd} DeepSeek positives. Rule-of-three 95%")
    print(f"     upper bound on the miss rate = {ro3:.0%}. 'recall-safe' is bounded, not shown.")
    print(f"  staged cost on THIS panel: {ng}/{len(ids)} = {ng/len(ids):.1%} reach the k=3 arm.")

    # nesting within each stratum — stronger than the pooled claim
    print("\n  Nesting per stratum (pooling could hide a reversal):")
    for st in ("v7_only", "both", "v8_only"):
        S = [i for i in ids if frame[i]["stratum"] == st]
        d = sum(1 for i in S if dm[i] == "harmful")
        g = sum(1 for i in S if gmm[i] == "harmful")
        od = sum(1 for i in S if dm[i] == "harmful" and gmm[i] != "harmful")
        print(f"    {st:9} n={len(S):3d}  DeepSeek {d:2d} ⊂ Gemini {g:2d}   "
              f"DeepSeek-only {od}   {'NESTED' if od == 0 else 'REVERSAL'}")

    cand = [i for i in ids if gmm[i] == "harmful" and dm[i] != "harmful"]
    near = sum(1 for i in cand if "harmful" in ds[i]["votes"])
    print(f"\n  Is the gap boundary flutter?  Gemini-only-harmful rows: {len(cand)}; "
          f"DeepSeek cast >=1 harmful vote on {near}.")
    assert near * 3 < len(cand), "most Gemini-only rows ARE near-misses; offset claim void"
    print(f"      => a definitional offset, not marginal disagreement.")

    rank = {v: i for i, v in enumerate(ORD)}
    g_str = sum(1 for i in ids if rank[dm[i]] > rank[gmm[i]])
    d_str = sum(1 for i in ids if rank[dm[i]] < rank[gmm[i]])
    print(f"\n  Severity direction: Gemini stricter on {g_str}, DeepSeek stricter on {d_str}, "
          f"agree on {len(ids)-g_str-d_str}")

    print("\n  Stratum contrast (the WITHDRAWN void condition's quantity):")
    for jn, J in (("DeepSeek", dm), ("Gemini", gmm)):
        b = [i for i in ids if frame[i]["stratum"] == "both"]
        r = [i for i in ids if frame[i]["stratum"] != "both"]
        for q, f in (("harmful", lambda v: v == "harmful"),
                     ("on-promise", lambda v: v in ("fits", "weak"))):
            rb = sum(f(J[i]) for i in b) / len(b)
            rr = sum(f(J[i]) for i in r) / len(r)
            print(f"    {jn:9} {q:11} both {rb:6.1%} (n={len(b)})  rest {rr:6.1%} "
                  f"(n={len(r)})  ratio {rb/rr:.2f}")


def part_b(rows, weights, op):
    rule("B. CORPUS COVERAGE — can the labelled corpus hold the failure mode v9/#156 needs?")
    A = lambda r: r["human_thriving_analysis"]
    wa = lambda r: A(r)["weighted_mean_all"]          # the DECLARED aggregate; raises if absent
    n = len(rows)
    tot = sum(weights[r["id"]] for r in rows)
    hw = lambda f: sum(weights[r["id"]] for r in rows if f(r)) / tot

    print(f"  corpus: {n} rows  (datasets/scored/human_thriving_v8/labels_v84_merged.jsonl)")
    print(f"  sha256 {LABELS_SHA256}  ⛔ GITIGNORED — not in a clean clone")
    print(f"  aggregate_used = 'all' on {n}/{n} rows, so the score is weighted_mean_all")
    print(f"  op-point {op} read by EXECUTING filters/human_thriving/v8/base_scorer.py")
    print(f"  ⚠️  that op-point is on the CALIBRATED scale (2026-09-05-v8-op-point.md);")
    print(f"     weighted_mean_all is an UNCALIBRATED oracle mean, so this band is the")
    print(f"     more permissive of the two. Every count below is a raw-scale count.")
    print(f"  design weights: inclusion_probability from corpus.jsonl, span 25.132x")

    verd = Counter(A(r)["scope_verdict"] for r in rows)
    print(f"\n  scope_verdict: {dict(verd.most_common())}")
    H = [r for r in rows if A(r)["scope_verdict"] == "harm_is_subject"]
    print(f"  harm_is_subject: {len(H)} rows   unweighted {len(H)/n:.4%}   "
          f"design-weighted {hw(lambda r: A(r)['scope_verdict']=='harm_is_subject'):.4%}")
    print(f"    ⛔ 19.0% is the SAMPLE share. The production estimate is ~21.0%.")

    print(f"\n  max weighted_mean_all among harm_is_subject rows: {max(wa(r) for r in H)}")
    n40 = sum(1 for r in H if wa(r) >= 4.0)
    print(f"  harm_is_subject rows with weighted_mean_all >= 4.0: {n40}")
    assert n40 == 0, "a harm row now reaches 4.0 — the coverage conclusion is void"

    above = [r for r in rows if wa(r) >= op]
    av = Counter(A(r)["scope_verdict"] for r in above)
    print(f"\n  rows at or above {op}: {len(above)}   unweighted {len(above)/n:.4%}   "
          f"design-weighted {hw(lambda r: wa(r) >= op):.4%}")
    print(f"  their scope_verdict: {dict(av.most_common())}")
    assert set(av) == {"in_scope"}, f"NOT all in_scope: {dict(av)} — conclusion void"
    print(f"  => COMPUTED: all {len(above)} rows at or above {op} are in_scope, and no")
    print(f"     harm_is_subject row reaches 4.0. Both asserted, not printed.")

    # ⛔ the confound: which prompt produced the above-op population?
    print("\n  ⛔ WHICH PROMPT PRODUCED THEM — the above-op population is NOT the corpus:")
    ph = Counter(A(r).get("prompt_hash") for r in rows)
    for h, c in ph.most_common():
        arm = [r for r in rows if A(r).get("prompt_hash") == h]
        ab = sum(1 for r in arm if wa(r) >= op)
        pf = A(arm[0]).get("prompt_file", "?").split("/")[-1]
        print(f"    {h}  {pf:28} n={len(arm):5d}  above-op {ab:4d} = {ab/len(arm):7.2%}")
    inblock = [r for r in above if A(r).get("prompt_hash") != ph.most_common(1)[0][0]]
    print(f"  => {len(inblock)} of {len(above)} above-op rows ({len(inblock)/len(above):.1%}) come from the")
    print(f"     MINORITY prompt arm, which was itself selected for being above-op under an")
    print(f"     earlier pass. The MAJORITY arm ({ph.most_common(1)[0][1]} rows) has {len(above)-len(inblock)}.")
    print(f"  ⚠️  H-V8-30 measured that this exact prompt swap moves in_scope by +0.1774")
    print(f"     (McNemar p=0.0034), i.e. it moves the variable being cross-tabulated.")

    # ⛔ the $0 route the labels DO contain: per-run scope disagreement
    print("\n  ⛔ WHAT THE LABELS DO CONTAIN — per-run scope disagreement (a $0 route):")
    def votes(r):
        v = A(r).get("scope_verdicts_per_run")
        if isinstance(v, str):
            return [x.strip() for x in v.split(",")]
        return [str(x) for x in v] if isinstance(v, list) else []
    flipped = sum(1 for r in rows if A(r).get("scope_flipped") is True)
    hv = [r for r in rows if A(r)["scope_verdict"] != "harm_is_subject"
          and any(x in ("harm", "harm_is_subject") for x in votes(r))]
    hv_above = [r for r in hv if wa(r) >= op]
    print(f"    scope_flipped True: {flipped}")
    print(f"    >=1 harm run-vote with a NON-harm final verdict: {len(hv)}")
    print(f"    of those, at or above {op}: {len(hv_above)}")
    for r in sorted(hv_above, key=lambda r: -wa(r)):
        print(f"      {wa(r):.3f}  final={A(r)['scope_verdict']}  votes={votes(r)}")
    print(f"    harm_is_subject rows whose own run votes SPLIT: "
          f"{sum(1 for r in rows if A(r)['scope_verdict']=='harm_is_subject' and len(set(votes(r)))>1)}")
    print(f"  ⇒ SO THE ABSOLUTE 'CANNOT HAVE ANY' IS FALSE. {len(hv_above)} row(s) carry a harm")
    print(f"    run-vote and a non-harm final verdict above the op-point. What IS true is")
    print(f"    narrower: the corpus's FINAL LABELS cannot exhibit student/oracle")
    print(f"    disagreement, because they are the oracle's own output.")

    lens = sorted(len(r["content"]) for r in rows)
    hl = sorted(len(r["content"]) for r in H)
    print(f"\n  content length  corpus min {lens[0]} median {lens[len(lens)//2]}   "
          f"harm median {hl[len(hl)//2]}")
    print(f"  ⚠️  min 300 is an EXCLUSION: the #93 labelling-time floor in")
    print(f"     ground_truth.batch_scorer.make_oracle_prefilter. Sub-300-char rows are")
    print(f"     absent by construction, not by measurement.")
    print(f"  english share   corpus unweighted {sum(1 for r in rows if r['language']=='en')/n:.4%}"
          f"  design-weighted {hw(lambda r: r['language']=='en'):.4%}")
    print(f"                  harm_is_subject unweighted {sum(1 for r in H if r['language']=='en')/len(H):.4%}")
    print("  NOTE: that harm-stratum English share is the SUPPLY of harm content per")
    print("        language in a labelled corpus. It is not an error-rate signal and is")
    print("        not a prior about where the student fails.")


def part_c(frame, ds, gm, ids):
    rule("C. JUDGE COMPETENCE ACROSS LANGUAGE — does the rubric's `fits` clause leak fluency?")
    print('  Mechanism under test, quoted from judge.py RUBRIC:')
    print('    "If you cannot name who is better off and how, it is not `fits`."')

    en = [i for i in ids if frame[i]["language"] == "en"]
    ne = [i for i in ids if frame[i]["language"] != "en"]
    print(f"\n  panel: english {len(en)} = {len(en)/len(ids):.1%}, non-english {len(ne)}")

    for jn, J in (("DeepSeek k=3", ds), ("Gemini k=1", gm)):
        for lab, S in (("en", en), ("non-en", ne)):
            c = Counter(J[i]["majority"] for i in S)
            print(f"  {jn:13} {lab:7} n={len(S):3d}  " +
                  "  ".join(f"{v}={c.get(v,0)/len(S):6.1%} ({c.get(v,0):2d})" for v in ORD))

    print("\n  POOLED: `fits` falls and `misleading` absorbs it, in both families:")
    for jn, J in (("DeepSeek", ds), ("Gemini", gm)):
        for q in ("fits", "misleading"):
            a = sum(J[i]["majority"] == q for i in en) / len(en)
            b = sum(J[i]["majority"] == q for i in ne) / len(ne)
            print(f"      {jn:9} {q:11} en {a:5.1%} -> non-en {b:5.1%}   delta {100*(b-a):+.1f}pp")
        h_en = sum(J[i]["majority"] == "harmful" for i in en)
        h_ne = sum(J[i]["majority"] == "harmful" for i in ne)
        print(f"      {jn:9} {'harmful':11} en {h_en/len(en):5.1%} ({h_en}) -> "
              f"non-en {h_ne/len(ne):5.1%} ({h_ne})   FLAT ⚠️ {h_en} vs {h_ne} rows")

    # ⛔ the pooled delta is confounded by stratum — the panel is stratified and
    #    English share varies with it.
    print("\n  ⛔ WITHIN STRATUM — the panel is stratified and English share varies with it:")
    for st in ("v7_only", "both", "v8_only"):
        S = [i for i in ids if frame[i]["stratum"] == st]
        e = [i for i in S if frame[i]["language"] == "en"]
        x = [i for i in S if frame[i]["language"] != "en"]
        print(f"    {st:9} n={len(S):3d}  english {len(e)/len(S):5.1%}", end="")
        for jn, J in (("DS", ds), ("GM", gm)):
            if e and x:
                a = sum(J[i]["majority"] == "fits" for i in e) / len(e)
                b = sum(J[i]["majority"] == "fits" for i in x) / len(x)
                print(f"   {jn} fits delta {100*(b-a):+6.1f}pp", end="")
        print()
    print("  ⇒ THE SIGN REVERSES in v8_only under BOTH judges, and `both` is far larger")
    print("    than pooled. The pooled -15.1/-12.3pp is SUBSTANTIALLY COMPOSITION.")
    print("    'Both families, same direction' does NOT survive the panel's own design")
    print("    variable. No stratum control was pre-registered; H-AP1 stays OPEN and its")
    print("    method must stratify.")

    print("\n  Not raw confusion — DeepSeek k=3 split-vote rate by language:")
    for lab, S in (("en", en), ("non-en", ne)):
        sp = sum(1 for i in S if len(set(ds[i]["votes"])) > 1)
        print(f"      {lab:7} {sp}/{len(S)} = {sp/len(S):.1%}")
    allsp = sum(1 for i in ids if len(set(ds[i]["votes"])) > 1)
    print(f"      ALL     {allsp}/{len(ids)} = {allsp/len(ids):.1%}  "
          f"<- THIS is 'DeepSeek's k=3 split-vote rate'")
    print("      ⛔ 45.8% is the NON-ENGLISH rate, not DeepSeek's rate. Do not cite it as one.")


def main():
    op = op_point()
    frame, ds, gm, ids = load_panel()
    part_a(frame, ds, gm, ids)
    rows, weights = load_corpus()
    part_b(rows, weights, op)
    part_c(frame, ds, gm, ids)
    rule("DONE — Part A/C inputs are committed; Part B's is gitignored and sha256-pinned.")


if __name__ == "__main__":
    main()
