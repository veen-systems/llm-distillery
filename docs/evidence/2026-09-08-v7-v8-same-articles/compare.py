"""uplifting v7 vs human_thriving v8 on the SAME production articles — the free comparison.

No API calls, no judges. Both filters are enabled and score every article of every cycle, so
the comparison is arithmetic over output NexusMind already wrote.

Inputs (produced by the sibling extractors, which run ON sadalsuud):
    extract.py         -> records.jsonl   (both lenses, 4 paired cycles, compact per-article rows)
    extract_lenses.py  -> lenses.jsonl    (the other production lenses' SURFACED rows, same cycles)

Usage:
    python3 docs/evidence/2026-09-08-v7-v8-same-articles/compare.py \
        <records.jsonl> <lenses.jsonl> [union_manifest.jsonl]

⛔ THE CONTROLS RUN HERE, NOT IN A COMMENT. Four assert, and the script fails rather than
reports if any breaks:
  1. the two lenses scored the SAME article set, verified on sets and not on counts;
  2. `raw >= 4.5` reproduces the pipeline's OWN `tier != "low"` on every row of both lenses —
     with a presence control, because a check that cannot fail proves nothing: substituting the
     NORMALIZED score must disagree (it does, on 530 uplifting rows);
  3. no article is counted twice across the four cycles;
  4. nothing SURFACES off a Stage-1 probe estimate, on either lens;
  5. every cross-lens row joins a paired article, so §4 cannot silently understate coverage.

⚠️ Control 4 bounds the SURFACED sets only. 1,604 v7 and 1,881 v8 rows are `stage1_low`, whose
`raw_weighted_average` is an e5 PROBE estimate, not a Gemma score — they are below both op-points
but they are still in the corpus, so any statistic over ALL rows mixes two instruments. §2 is
therefore computed on the BOTH-STAGE2 frame and the mixed frame is printed beside it, labelled.
The first version published only the mixed frame; review caught it, and the correction changes the
headline rank agreement from 0.5551 to 0.7177 and makes the noise null decisive instead of
inconclusive.
"""
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict

OP = 4.5          # BOTH lenses' runtime op-point: base_scorer.py TIER_THRESHOLDS medium
NOISE = 0.16      # llm-distillery#95 batch-composition floor


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def load(records_path):
    recs = defaultdict(dict)
    for line in open(records_path):
        r = json.loads(line)
        key = (r["cycle"], r["id"])
        if r["filter"] in recs[key]:
            raise ValueError(f"duplicate row {key} {r['filter']}")
        recs[key][r["filter"]] = r
    return recs


def main():
    records_path, lenses_path = sys.argv[1], sys.argv[2]
    manifest_path = sys.argv[3] if len(sys.argv) > 3 else None
    recs = load(records_path)
    cycles = sorted({k[0] for k in recs})

    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)

    # --- control 1: same article set, on SETS not counts
    for c in cycles:
        up = {k[1] for k, v in recs.items() if k[0] == c and "uplifting" in v}
        ht = {k[1] for k, v in recs.items() if k[0] == c and "human_thriving" in v}
        print(f"  {c}: uplifting {len(up)}  human_thriving {len(ht)}  symmetric_diff {len(up ^ ht)}")
        assert up == ht, f"{c}: the two lenses did not score the same articles"
    pairs = {k: v for k, v in recs.items() if len(v) == 2}
    assert len(pairs) == len(recs), "unpaired rows survived"
    print(f"  paired rows: {len(pairs)}")

    # --- control 3: no article counted twice across cycles
    seen = Counter(k[1] for k in pairs)
    assert max(seen.values()) == 1, f"article scored in >1 cycle: {seen.most_common(1)}"
    print(f"  distinct articles across the 4 cycles: {len(seen)} (no cycle-to-cycle repeats)")

    def raw(k, f):
        x = pairs[k][f]["raw_weighted_average"]
        if x is None:
            raise ValueError(f"null raw_weighted_average: {k} {f}")
        return x

    # --- control 2: my threshold reproduces the pipeline's own tier, and the check is specific
    for f in ("uplifting", "human_thriving"):
        bad = [k for k in pairs if (raw(k, f) >= OP) != (pairs[k][f]["tier"] != "low")]
        assert not bad, f"{f}: raw>=4.5 disagrees with the pipeline's tier on {len(bad)} rows"
        print(f"  {f}: raw>={OP} reproduces the pipeline's tier on all {len(pairs)} rows")
    alt = sum(1 for k in pairs
              if (pairs[k]["uplifting"]["weighted_average"] >= OP)
              != (pairs[k]["uplifting"]["tier"] != "low"))
    assert alt > 0, "presence control DEAD: the normalized score would agree too, so control 2 " \
                    "does not show the tier follows the RAW score"
    print(f"  [presence control] substituting uplifting's NORMALIZED score disagrees on {alt} rows"
          f" -> control 2 is specific to the raw score, not trivially true")

    for f in ("uplifting", "human_thriving"):
        st = Counter(pairs[k][f]["stage_used"] for k in pairs)
        surf_st = Counter(pairs[k][f]["stage_used"] for k in pairs if raw(k, f) >= OP)
        gk = sum(1 for k in pairs if pairs[k][f].get("gatekeeper_applied"))
        nm = Counter(pairs[k][f]["normalization_method"] for k in pairs)
        # Control 4. This was a PRINT in the first version while the README called it an
        # assert — a claim inside a section whose whole point is that its claims execute.
        # A stage1_low row's score is an e5 probe estimate, not a Gemma output, so if one
        # ever surfaced every score comparison below would silently mix two instruments.
        assert set(surf_st) <= {"stage2"}, \
            f"{f}: a non-stage2 row surfaced ({dict(surf_st)}) — raw_weighted_average is " \
            f"then a probe estimate on some rows, not a model output"
        print(f"  {f}: stage_used={dict(st)}  surfaced_by_stage={dict(surf_st)}  "
              f"gatekeeper_applied={gk}  normalization={dict(nm)}")

    # ------------------------------------------------------------------ surfacing
    print()
    print("=" * 78)
    print(f"1. SURFACING AT raw >= {OP} — the same articles, the two lenses")
    print("=" * 78)
    tot = Counter()
    for c in cycles:
        sub = [k for k in pairs if k[0] == c]
        s7 = {k for k in sub if raw(k, "uplifting") >= OP}
        s8 = {k for k in sub if raw(k, "human_thriving") >= OP}
        j = len(s7 & s8) / len(s7 | s8) if (s7 | s8) else float("nan")
        tot["n"] += len(sub); tot["v7"] += len(s7); tot["v8"] += len(s8)
        tot["both"] += len(s7 & s8); tot["only7"] += len(s7 - s8); tot["only8"] += len(s8 - s7)
        print(f"  {c}: n={len(sub):5d}  v7={len(s7):4d}  v8={len(s8):3d}  both={len(s8 & s7):3d}  "
              f"v7only={len(s7 - s8):4d}  v8only={len(s8 - s7):2d}  "
              f"Jaccard={j:.3f}  v7/v8={len(s7)/len(s8):.1f}x")
    s7 = {k for k in pairs if raw(k, "uplifting") >= OP}
    s8 = {k for k in pairs if raw(k, "human_thriving") >= OP}
    only7, only8, both = s7 - s8, s8 - s7, s7 & s8
    J = len(both) / len(s7 | s8)
    lo7, hi7 = wilson(len(s7), len(pairs))
    lo8, hi8 = wilson(len(s8), len(pairs))
    print(f"  ALL: n={len(pairs)}  v7={len(s7)}  v8={len(s8)}  both={len(both)}  "
          f"v7only={len(only7)}  v8only={len(only8)}  Jaccard={J:.3f}")
    print(f"  pass rate  v7 {len(s7)/len(pairs)*100:.3f}% [{lo7*100:.3f}, {hi7*100:.3f}]   "
          f"v8 {len(s8)/len(pairs)*100:.3f}% [{lo8*100:.3f}, {hi8*100:.3f}]   "
          f"ratio {len(s7)/len(s8):.2f}x")
    print(f"  v8 is nearly a SUBSET of v7: {len(both)}/{len(s8)} = "
          f"{len(both)/len(s8)*100:.1f}% of v8's passers also pass v7")
    print(f"  tier 'high' (raw >= 7.0):  v7 {sum(1 for k in pairs if raw(k,'uplifting')>=7)}   "
          f"v8 {sum(1 for k in pairs if raw(k,'human_thriving')>=7)}   "
          f"(v8 max raw {max(raw(k,'human_thriving') for k in pairs):.3f}, "
          f"v7 max {max(raw(k,'uplifting') for k in pairs):.3f})")

    # ------------------------------------------------- is it a threshold or a different order?
    print()
    print("=" * 78)
    print("2. IS v8 A STRICTER v7, OR A DIFFERENTLY-ORDERED FILTER?")
    print("=" * 78)
    keys = sorted(pairs)
    stage2 = [k for k in keys
              if pairs[k]["uplifting"]["stage_used"] == "stage2"
              and pairs[k]["human_thriving"]["stage_used"] == "stage2"]
    print(f"  FRAMES: all rows n={len(keys)} (MIXED — {len(keys)-len(stage2)} rows carry a probe")
    print(f"  estimate on at least one lens) · both-stage2 n={len(stage2)} (clean, the primary frame)")

    def ranks(f, ks):
        """Mid-ranks of `ks` by lens `f`.

        ⛔ Ranks are computed WITHIN `ks`, not sliced out of a global ranking. The first
        version of this script ranked over all 15,372 rows and then correlated those global
        ranks over the 1,200-row subset — that is not Spearman (Spearman re-ranks inside the
        sample) and it read 0.224 where the statistic is 0.346. Caught by review, 2026-09-08.
        """
        order = sorted(ks, key=lambda k: raw(k, f))
        out, i = {}, 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and raw(order[j + 1], f) == raw(order[i], f):
                j += 1
            avg = (i + j) / 2 + 1
            for t in range(i, j + 1):
                out[order[t]] = avg
            i = j + 1
        return out

    def _corr(xs, ys):
        n = len(xs)
        mx, my = statistics.mean(xs), statistics.mean(ys)
        sx, sy = statistics.pstdev(xs), statistics.pstdev(ys)
        return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / n / (sx * sy)

    def rho(ks, v8=None):
        """Spearman within `ks`. `v8` overrides human_thriving's scores (for the null)."""
        ks = list(ks)
        a = ranks("uplifting", ks)
        if v8 is None:
            b = ranks("human_thriving", ks)
        else:
            order = sorted(ks, key=lambda k: v8[k])
            b, i = {}, 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v8[order[j + 1]] == v8[order[i]]:
                    j += 1
                for t in range(i, j + 1):
                    b[order[t]] = (i + j) / 2 + 1
                i = j + 1
        return _corr([a[k] for k in ks], [b[k] for k in ks])

    for lbl, ks in (("both-stage2 (PRIMARY)", stage2), ("all rows (mixed)", keys)):
        s7f = {k for k in ks if raw(k, "uplifting") >= OP}
        s8f = {k for k in ks if raw(k, "human_thriving") >= OP}
        K = len(s7f)
        top8 = set(sorted(ks, key=lambda k: -raw(k, "human_thriving"))[:K])
        thr = min(raw(k, "human_thriving") for k in top8)
        ov = len(top8 & s7f)
        xs = [raw(k, "uplifting") for k in ks]
        ys = [raw(k, "human_thriving") for k in ks]
        d = sorted(q - p for p, q in zip(xs, ys))
        print(f"\n  [{lbl}] n={len(ks)}  v7={K}  v8={len(s8f)}")
        print(f"    volume-matched: v8's top-{K} needs an op-point of {thr:.3f} (deployed {OP})")
        print(f"    overlap with v7's surfaced set: {ov} = {ov/K*100:.1f}%  "
              f"(random-top-K chance {K/len(ks)*100:.2f}%)")
        print(f"    Spearman rho, all of frame: {rho(ks):.4f}")
        print(f"    Spearman rho WITHIN the surfaced union (n={len(s7f | s8f)}): {rho(s7f | s8f):.4f}")
        print(f"    raw: v7 mean {statistics.mean(xs):.3f} sd {statistics.pstdev(xs):.3f}   "
              f"v8 mean {statistics.mean(ys):.3f} sd {statistics.pstdev(ys):.3f}   "
              f"pearson {_corr(xs, ys):.4f}")
        print(f"    v8 - v7 per article: median {statistics.median(d):+.3f}  "
              f"p05 {d[int(0.05*len(d))]:+.3f}  p95 {d[int(0.95*len(d))]:+.3f}")

    # --- THE NULL THAT MATTERS. "Chance level" above is a RANDOM top-K, which nothing would
    # plausibly produce. The live alternative is "v8 is a noisier, rescaled v7 with no lens
    # difference": tune monotone noise on v7 so the null's Spearman with v7 MATCHES the observed
    # one, quantile-map it onto v8's exact marginal, and read the volume-matched overlap and the
    # within-union rho off it. On the MIXED frame this null is not excluded — which is why the
    # frame matters and why the first version of this evidence did not establish its own headline.
    print()
    print("  NOISE NULL — 'v8 is a noisy, rescaled v7', Spearman-matched, v8's exact marginal")
    for lbl, ks in (("both-stage2 (PRIMARY)", stage2), ("all rows (mixed)", keys)):
        rnd = random.Random(20260908)
        a_sorted = sorted(ks, key=lambda k: raw(k, "uplifting"))
        v8_marginal = sorted(raw(k, "human_thriving") for k in ks)
        s7f = {k for k in ks if raw(k, "uplifting") >= OP}
        K = len(s7f)
        target = rho(ks)

        def draw(sd):
            noisy = sorted(ks, key=lambda k: raw(k, "uplifting") + rnd.gauss(0, sd))
            return {k: v8_marginal[i] for i, k in enumerate(noisy)}

        lo, hi = 0.0, 20.0
        for _ in range(30):
            sd = (lo + hi) / 2
            if rho(ks, draw(sd)) > target:
                lo = sd
            else:
                hi = sd
        ovs, urs = [], []
        for _ in range(15):
            m = draw(sd)
            top = set(sorted(ks, key=lambda k: -m[k])[:K])
            u = s7f | {k for k in ks if m[k] >= OP}
            ovs.append(len(top & s7f) / K)
            urs.append(rho(u, m))
        actual_top = set(sorted(ks, key=lambda k: -raw(k, "human_thriving"))[:K])
        actual_ov = len(actual_top & s7f) / K
        s8f = {k for k in ks if raw(k, "human_thriving") >= OP}
        actual_ur = rho(s7f | s8f)
        print(f"    [{lbl}] sd={sd:.3f} (Spearman matched to {target:.4f})")
        print(f"      volume-matched overlap  NULL {statistics.mean(ovs)*100:.1f}% "
              f"[{min(ovs)*100:.1f}, {max(ovs)*100:.1f}]   ACTUAL {actual_ov*100:.1f}%")
        print(f"      within-union rho        NULL {statistics.mean(urs):.4f} "
              f"[{min(urs):.4f}, {max(urs):.4f}]   ACTUAL {actual_ur:.4f}")

    print("\n  per-dimension mean delta (v8 - v7), same articles, both frames:")
    print("  ⚠️ the six dimension NAMES are shared; the two lenses' RUBRICS are not — different")
    print("  oracle prompts, so a delta is a difference of two definitions, not of one quantity.")
    for dim in pairs[keys[0]]["uplifting"]["scores"]:
        def dl(ks):
            return statistics.mean(pairs[k]["human_thriving"]["scores"][dim]
                                   - pairs[k]["uplifting"]["scores"][dim] for k in ks)
        print(f"    {dim:26s} both-stage2 {dl(stage2):+.3f}   all rows {dl(keys):+.3f}")

    # ---------------------------------------------------------------- boundary noise
    print()
    print("=" * 78)
    print(f"3. IS THE DISAGREEMENT BOUNDARY NOISE? (#95 floor |delta| <= {NOISE})")
    print("=" * 78)
    # ⚠️ A floor belongs to a POPULATION and a MECHANISM. 0.16 is #95's batch-composition term
    # measured on other filters and is the SMALLEST of the measured terms; no batch floor has
    # been measured for human_thriving v8 (its own device term is 0.1428, EXP-026). Report the
    # sensitivity rather than picking one — picking by magnitude looks like rigour and is not.
    FLOORS = [(0.16, "#95 batch"), (0.1428, "v8 device, EXP-026"),
              (0.1956, "CPU->CUDA device"), (0.2008, "library stack"), (0.25, "beyond any measured")]
    for lbl, ks, other in (("v7-only", only7, "human_thriving"), ("v8-only", only8, "uplifting")):
        o = sorted(raw(k, other) for k in ks)
        near = sum(1 for k in ks if abs(raw(k, other) - OP) <= NOISE)
        print(f"  {lbl} n={len(ks)}: {near} ({near/len(ks)*100:.1f}%) sit within {NOISE} of the "
              f"other lens's op-point")
        print(f"    the other lens's score on them: median {statistics.median(o):.3f}  "
              f"min {o[0]:.3f}  max {o[-1]:.3f}")
        print("    sensitivity to the floor chosen: " + "  ".join(
            f"{f}({name})={sum(1 for k in ks if abs(raw(k, other) - OP) <= f)}"
            for f, name in FLOORS))
    gap = sorted(OP - raw(k, "human_thriving") for k in only7)
    print(f"  v7-only, distance below v8's bar: median {statistics.median(gap):.3f}   "
          f"within 0.5: {sum(1 for x in gap if x <= 0.5)}   within 1.0: {sum(1 for x in gap if x <= 1.0)}")

    # ---------------------------------------------------------------- cross-lens coverage
    print()
    print("=" * 78)
    print("4. DO THE DROPPED ROWS LEAVE ovr.news, OR DOES ANOTHER LENS ALREADY CARRY THEM?")
    print("=" * 78)
    other_lens = defaultdict(set)
    totals = Counter()
    unjoined = 0
    for line in open(lenses_path):
        r = json.loads(line)
        k = (r["cycle"], r["id"])
        if k not in pairs:
            unjoined += 1
            continue
        other_lens[k].add(r["filter"])
        totals[r["filter"]] += 1
    # Control 5. A cross-lens row that joins nothing would silently UNDERSTATE coverage and so
    # OVERSTATE the "carried by no other lens" share -- the number this section is quoted for.
    # The lenses' pools are NOT identical (solutions carries 6,209 in c1 against 6,210), so this
    # can fire; it is 0 here, which is the fact being asserted rather than assumed.
    assert unjoined == 0, (
        f"{unjoined} surfaced cross-lens rows do not join a paired article — §4's "
        f"'carried by no other lens' share is inflated by up to that many")
    print(f"  [control 5] cross-lens rows failing to join a paired article: {unjoined}")
    print(f"  other lenses' surfaced totals, same 4 cycles: {dict(sorted(totals.items()))}")
    print("  (investment_risk is PAUSED since 2026-08-25 and writes no files — absent by design)")
    base = sum(1 for k in pairs if other_lens.get(k))
    print(f"  [baseline] any-other-lens coverage over all {len(pairs)} articles: "
          f"{base} = {base/len(pairs)*100:.2f}%")
    for lbl, ks in (("v7-only (v8 would drop these)", only7),
                    ("both", both), ("v8-only (v8 would add these)", only8)):
        cov = sum(1 for k in ks if other_lens.get(k))
        per = Counter(f for k in ks for f in other_lens.get(k, ()))
        print(f"  {lbl}  n={len(ks)}: carried by >=1 other lens {cov} = {cov/len(ks)*100:.1f}%   "
              f"by none {len(ks)-cov} = {(len(ks)-cov)/len(ks)*100:.1f}%")
        print(f"    per-lens: {dict(per.most_common())}")
        pc = Counter(k[0] for k in ks if not other_lens.get(k))
        print(f"    carried by none, PER CYCLE: {dict(sorted(pc.items()))} "
              f"(c1 is the backlog cycle; do not average it in)")

    # ---------------------------------------------------------------- composition
    print()
    print("=" * 78)
    print("5. COMPOSITION OF THE THREE SETS")
    print("=" * 78)
    for lbl, ks in (("both", both), ("v7-only", only7), ("v8-only", only8)):
        lang = Counter(pairs[k]["uplifting"]["language"] for k in ks)
        sg = Counter(pairs[k]["uplifting"]["source_group"] for k in ks)
        ln = sorted(pairs[k]["uplifting"]["len_content"] for k in ks)
        en = lang.get("en", 0)
        print(f"  {lbl}  n={len(ks)}  english {en} = {en/len(ks)*100:.1f}%")
        print(f"    languages: {dict(lang.most_common(6))}")
        print(f"    source_group: {dict(sg.most_common(5))}")
        print(f"    content length: median {statistics.median(ln):.0f}  min {ln[0]}  max {ln[-1]}")

    print()
    print("  the 16 v8-only articles (what the Thriving tab would GAIN):")
    for k in sorted(only8, key=lambda k: -raw(k, "human_thriving")):
        v = pairs[k]["uplifting"]
        print(f"    v8 {raw(k,'human_thriving'):.3f} / v7 {raw(k,'uplifting'):.3f}  "
              f"[{v['language']}] {(v['title'] or '')[:84]}")
    print()
    print("  top 20 of the v7-only articles by v7 score (what the tab would LOSE):")
    for k in sorted(only7, key=lambda k: -raw(k, "uplifting"))[:20]:
        v = pairs[k]["uplifting"]
        carried = ",".join(sorted(other_lens.get(k, ()))) or "-"
        print(f"    v7 {raw(k,'uplifting'):.3f} / v8 {raw(k,'human_thriving'):.3f}  "
              f"[{v['language']}] [{carried}] {(v['title'] or '')[:70]}")

    if manifest_path:
        with open(manifest_path, "w") as out:
            for k in sorted(s7 | s8):
                v = pairs[k]
                out.write(json.dumps({
                    "cycle": k[0], "id": k[1],
                    "title": v["uplifting"]["title"],
                    "language": v["uplifting"]["language"],
                    "source": v["uplifting"]["source"],
                    "len_content": v["uplifting"]["len_content"],
                    "v7_raw": raw(k, "uplifting"), "v8_raw": raw(k, "human_thriving"),
                    "v7_surfaced": k in s7, "v8_surfaced": k in s8,
                    "set": "both" if k in both else ("v7_only" if k in only7 else "v8_only"),
                    "other_lenses": sorted(other_lens.get(k, ())),
                }, ensure_ascii=False) + "\n")
        print(f"\nwrote union manifest ({len(s7 | s8)} rows) to {manifest_path}")


if __name__ == "__main__":
    main()
