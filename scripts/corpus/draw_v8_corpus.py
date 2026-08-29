"""Draw the human_thriving v8 training corpus from the NexusMind archive, and emit a
manifest that RECONCILES WITH THE DRAWN FILE rather than with the spec it was asked for.

Design rules this file is built to satisfy, each of which cost this project something:

  * The archive window ROLLS. The window is enumerated at draw time and recorded in the
    manifest; a count carried across a session boundary is a different population.
  * The v7 score is a SAMPLING VARIABLE, not a label. The oracle relabels every drawn row,
    so binning on it is stratification, not supervision. But it is only a Gemma score for
    `stage_used == "stage2"` rows -- a `stage1_low` row's number is an e5 PROBE estimate.
    Those two are not the same instrument, so stage1_low is drawn as its OWN stratum with
    a coverage quota and is never mixed into a score bin.
  * A quota that cannot be filled RAISES. It never silently under-fills: a corpus that is
    quietly 40 rows short of its class-A target looks exactly like one that hit it.
  * Every realised figure in the manifest is recomputed FROM THE DRAWN ROWS. The acceptance
    test for #127 is a manifest whose counts reconcile with the split, not a json.dump of
    the arguments this script was called with.

Usage:
  python3 draw_v8_corpus.py --archive DIR --out DIR --size N [--seed S] [...]
"""
import argparse, glob, hashlib, json, math, os, random, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

GN_DOMAIN = "news.google.com"
ORACLE_FLOOR = 300          # ground_truth.batch_scorer.make_oracle_prefilter (#93)
OP = 4.5                    # uplifting v7 op-point (#102). Asserted against the scorer below.
MID_TOP = 5.5               # the marginal/clear positive boundary the plan's mix is stated on
ADVERSE_BAR = 3.85          # the census's low-band bar, reused so class-A numbers reconcile

# Latin-script test: the census's own definition, reused verbatim so the non-Latin share
# here and in docs/evidence/2026-08-28-v8-phase0-drawable-population.md are one number.
NON_LATIN = re.compile(r"[^\x00-\x7FÀ-ɏḀ-ỿ\s\d\W]")


def script_is_non_latin(text):
    sample = (text or "")[:400]
    letters = [c for c in sample if c.isalpha()]
    if not letters:
        return False
    non_latin = sum(1 for c in letters if ord(c) > 0x24F and not (0x1E00 <= ord(c) <= 0x1EFF))
    return non_latin > 0.5 * len(letters)


def domain_of(url):
    if not url:
        return ""
    m = re.match(r"https?://([^/]+)", url)
    return (m.group(1) if m else "").lower().lstrip("www.")


def load_pool(archive, harm_re):
    """Every distinct article in the window, first occurrence wins (the census's rule, so
    the two populations reconcile). Returns (records, provenance)."""
    files = sorted(glob.glob(os.path.join(archive, "filtered_*.jsonl")))
    if not files:
        raise SystemExit(f"FATAL: no filtered_*.jsonl under {archive}")
    seen, out = set(), []
    counts = Counter()
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                counts["unparseable"] += 1
                continue
            counts["rows"] += 1
            aid = r.get("id")
            if not aid:
                counts["no_id"] += 1
                continue
            if aid in seen:
                counts["dup_rows"] += 1
                continue
            seen.add(aid)
            up = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            content = r.get("content") or ""
            title = r.get("title") or ""
            dom = domain_of(r.get("url"))
            counts["articles"] += 1
            if dom == GN_DOMAIN:
                counts["excluded_google_news"] += 1
                continue
            out.append({
                "id": aid,
                "title": title,
                "content": content,
                "url": r.get("url"),
                "source": r.get("source"),
                "language": r.get("language") or "??",
                "published_date": r.get("published_date"),
                "domain": dom,
                "v7_score": up.get("raw_weighted_average"),
                "v7_stage_used": up.get("stage_used"),
                "content_length": len(content),
                "non_latin": script_is_non_latin(title + " " + content[:400]),
                "harm_title": bool(harm_re.search(title)) if title else False,
            })
    prov = {
        "archive": archive,
        "files": len(files),
        "window_first_file": os.path.basename(files[0]),
        "window_last_file": os.path.basename(files[-1]),
        "enumerated_at": datetime.now(timezone.utc).isoformat(),
        "file_list_sha256": hashlib.sha256(
            "\n".join(os.path.basename(f) for f in files).encode()).hexdigest()[:16],
        "counts": dict(counts),
    }
    return out, prov


def _stratum_of(r):
    """Which score stratum a row belongs to -- so a class-A row drawn first is NETTED against
    the stratum quota it occupies, instead of being added on top of it."""
    st, v = r["v7_stage_used"], r["v7_score"]
    if st == "stage1_low":
        return "stage1_low"
    if st != "stage2" or v is None:
        return "unstratifiable"
    if v >= MID_TOP:
        return "pos_clear"
    if v >= OP:
        return "pos_marginal"
    if v >= 3.5:
        return "neg_high"
    if v >= 1.5:
        return "neg_mid"
    return "neg_low"


def stratify(pool):
    """stage2 rows go into score bins; stage1_low is its OWN stratum (probe estimate, not a
    Gemma score); anything else is unusable for stratification and is reported, not dropped
    silently."""
    strata = defaultdict(list)
    for r in pool:
        st, v = r["v7_stage_used"], r["v7_score"]
        if st == "stage2" and v is not None:
            if v >= MID_TOP:
                strata["pos_clear"].append(r)       # >= 5.5
            elif v >= OP:
                strata["pos_marginal"].append(r)    # 4.5 - 5.5
            elif v >= 3.5:
                strata["neg_high"].append(r)        # 3.5 - 4.5
            elif v >= 1.5:
                strata["neg_mid"].append(r)         # 1.5 - 3.5  <- the thin region
            else:
                strata["neg_low"].append(r)         # < 1.5
        elif st == "stage1_low":
            strata["stage1_low"].append(r)
        else:
            strata["unstratifiable"].append(r)
    return strata


def take(rng, bucket, n, what):
    """Draw n WITHOUT replacement, or raise. A quota that cannot be met is a finding."""
    if n > len(bucket):
        raise SystemExit(
            f"FATAL: quota '{what}' asks for {n} rows, pool holds {len(bucket)}. "
            f"Reduce --size, or relax the target -- do NOT let this pass silently.")
    return rng.sample(bucket, n)


def allocate(args, strata):
    """Turn the ruled Gate 0 targets into per-stratum row counts.

    Ruled 2026-08-28 (docs/decisions/2026-08-28-v8-gate0-corpus-spec.md):
      * positive base rate 19.5% (enrichment 2.0x over drawable production's 9.76%),
      * positive MIX held at production's 63.5% marginal (4.5-5.5) / 36.5% clear (5.5+),
      * class-A supplement >= 0.70% of the corpus at 3:1 TP:FP,
      * non-Latin share >= 9.76%.

    Negatives are NOT enriched or reshaped: they are drawn to match the drawable pool's own
    conditional shape below the op-point. That is what fixes the v7 corpus's 0.43x thinness
    at 1.5-3.5 -- not a hand-set boost, which would be another hand-built population.
    """
    n = args.size
    n_pos = round(n * args.positive_rate)
    n_pos_marginal = round(n_pos * args.positive_mix)
    n_pos_clear = n_pos - n_pos_marginal

    neg_keys = ("neg_high", "neg_mid", "neg_low")
    neg_pool = {k: len(strata[k]) for k in neg_keys}
    neg_total_pool = sum(neg_pool.values())
    if neg_total_pool == 0:
        raise SystemExit("FATAL: no negative rows in the pool -- the archive or the score "
                         "field is not what this script expects")
    n_stage1 = round(n * args.stage1_share) if args.stage1_share is not None else \
        round(n * len(strata["stage1_low"]) / max(1, len(strata["stage1_low"]) + neg_total_pool
                                                  + len(strata["pos_marginal"])
                                                  + len(strata["pos_clear"])))
    n_neg = n - n_pos - n_stage1
    if n_neg <= 0:
        raise SystemExit(f"FATAL: positives ({n_pos}) + stage1_low ({n_stage1}) >= size ({n})")
    quotas = {"pos_marginal": n_pos_marginal, "pos_clear": n_pos_clear, "stage1_low": n_stage1}
    for k in neg_keys:                      # proportional to the pool, largest-remainder
        quotas[k] = int(n_neg * neg_pool[k] / neg_total_pool)
    short = n_neg - sum(quotas[k] for k in neg_keys)
    for k in sorted(neg_keys, key=lambda k: -(n_neg * neg_pool[k] / neg_total_pool
                                              - int(n_neg * neg_pool[k] / neg_total_pool))):
        if short <= 0:
            break
        quotas[k] += 1
        short -= 1
    assert sum(quotas.values()) == n, (sum(quotas.values()), n)
    return quotas


def realised(rows):
    """Recompute every Gate 0 quantity FROM THE DRAWN ROWS. Nothing here reads the spec."""
    n = len(rows)
    s2 = [r for r in rows if r["v7_stage_used"] == "stage2" and r["v7_score"] is not None]
    pos = [r for r in s2 if r["v7_score"] >= OP]
    marg = [r for r in pos if r["v7_score"] < MID_TOP]
    lengths = sorted(r["content_length"] for r in rows)
    q = lambda p: lengths[min(len(lengths) - 1, int(p * (len(lengths) - 1)))] if lengths else 0
    harm = [r for r in rows if r["harm_title"]]
    harm_hi = [r for r in harm if r["v7_score"] is not None and r["v7_score"] >= OP]
    harm_lo = [r for r in harm if r["v7_score"] is not None and r["v7_score"] < ADVERSE_BAR]
    return {
        "rows": n,
        "positive_rate": len(pos) / n if n else 0,
        "positive_mix_marginal": len(marg) / len(pos) if pos else 0,
        "non_latin_share": sum(r["non_latin"] for r in rows) / n if n else 0,
        "stage1_low_share": sum(r["v7_stage_used"] == "stage1_low" for r in rows) / n if n else 0,
        "class_a_share": len(harm) / n if n else 0,
        "class_a_tp_fp": (len(harm_hi) / len(harm_lo)) if harm_lo else None,
        "content_length_p10": q(0.10), "content_length_p50": q(0.50), "content_length_p90": q(0.90),
        "under_oracle_floor": sum(r["content_length"] < ORACLE_FLOOR for r in rows) / n if n else 0,
        "distinct_domains": len({r["domain"] for r in rows}),
        "distinct_languages": len({r["language"] for r in rows}),
        "score_histogram": dict(Counter(
            ("stage1_low" if r["v7_stage_used"] == "stage1_low"
             else "unscored" if r["v7_score"] is None
             else f"{0.5 * int(r['v7_score'] / 0.5):.1f}") for r in rows)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True, help="directory: corpus.jsonl + corpus_manifest.json")
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--seed", type=int, default=8829)
    ap.add_argument("--positive-rate", type=float, default=0.195)
    ap.add_argument("--positive-mix", type=float, default=0.635, help="share of positives in 4.5-5.5")
    ap.add_argument("--nonlatin-min", type=float, default=0.0976)
    ap.add_argument("--class-a-min", type=float, default=0.0070)
    ap.add_argument("--class-a-tp-fp", type=float, default=3.0)
    ap.add_argument("--stage1-share", type=float, default=None,
                    help="corpus share drawn from stage1_low; default = its share of the pool")
    ap.add_argument("--short-form", choices=("exclude", "include"), default="exclude",
                    help="rows under the 300-char ORACLE floor are dropped by "
                         "make_oracle_prefilter at labelling time (#93). 'include' draws them "
                         "anyway and records how many would be lost -- do not use it without "
                         "deciding what happens to them.")
    ap.add_argument("--dry-run", action="store_true", help="report the plan, write nothing")
    args = ap.parse_args()

    # The op-point is IMPORTED from the scorer when this runs inside the repo, and asserted
    # when it runs on a host that only has this file. A second copy of an op-point is how
    # NM#161 and NM#205 happened.
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))))
        from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as _S
        live_op = dict((n, t) for n, t, _ in _S.TIER_THRESHOLDS)["medium"]
        if live_op != OP:
            raise SystemExit(f"FATAL: op-point drift -- this file says {OP}, the scorer says "
                             f"{live_op}. Fix the constant, do not run.")
        op_source = "imported from filters/uplifting/v7/base_scorer.py"
    except ImportError:
        op_source = (f"ASSERTED as {OP} -- filters/ not importable from this host, so the "
                     f"scorer could NOT be consulted. Verify before trusting the split.")

    harm_re = re.compile(
        r"\b(kill|killed|murder|shot|shoot|stab|rape|assault|abuse|attack|dead|death|dies|died|"
        r"crash|bomb|war|violence|victim|arrest|jail|prison|court|lawsuit|fraud|scandal|crisis|"
        r"disaster|flood|fire|quake|storm|drought|famine|outbreak|toll)\b", re.I)

    pool, prov = load_pool(args.archive, harm_re)
    dropped_short = 0
    if args.short_form == "exclude":
        before = len(pool)
        pool = [r for r in pool if r["content_length"] >= ORACLE_FLOOR]
        dropped_short = before - len(pool)

    strata = stratify(pool)
    quotas = allocate(args, strata)
    print("== v8 CORPUS DRAW ==")
    print(f"archive  : {args.archive}")
    print(f"window   : {prov['files']} files, {prov['window_first_file']} .. "
          f"{prov['window_last_file']}")
    print(f"op-point : {OP} ({op_source})")
    print(f"pool     : {len(pool):,} drawable articles "
          f"(short-form {args.short_form}, dropped {dropped_short:,})")
    for k in sorted(strata):
        print(f"   {k:<16} pool {len(strata[k]):>7,}   quota {quotas.get(k, 0):>6,}")
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    rng = random.Random(args.seed)

    # ------------------------------------------------------------------ the draw
    # Constraints are satisfied BY CONSTRUCTION, not by repair afterwards. An earlier version
    # drew on score strata alone and then swapped rows in to hit the non-Latin and class-A
    # targets; its own test showed the repair breaking a third target (displacing positives
    # dropped the base rate below spec). Repairing one constraint at the cost of another is
    # the shape that ships a corpus whose manifest says PASS on the target you looked at.
    #
    # Order matters: the SMALLEST, SCARCEST class is drawn first, because it is the one that
    # cannot be topped up later.
    drawn, taken = [], set()

    def pick(bucket, n, what):
        avail = [r for r in bucket if r["id"] not in taken]
        if n > len(avail):
            raise SystemExit(
                f"FATAL: quota '{what}' asks for {n} rows, pool offers {len(avail)}. "
                f"Reduce --size, or relax the target -- do NOT let this pass silently.")
        got = rng.sample(avail, n)
        for r in got:
            taken.add(r["id"])
        drawn.extend(got)
        return got

    # 1. class-A supplement, at the ruled 3:1 TP:FP (2026-08-28 owner ruling, spec §3).
    #    TP proxy = harm in the title AND scored at/above the op-point ("harm answered");
    #    FP proxy = harm in the title AND scored below the adverse bar ("harm dominant").
    n_class_a = math.ceil(args.size * args.class_a_min)
    n_a_tp = round(n_class_a * (args.class_a_tp_fp / (1.0 + args.class_a_tp_fp)))
    harm_tp = [r for r in pool if r["harm_title"] and r["v7_score"] is not None
               and r["v7_score"] >= OP]
    harm_fp = [r for r in pool if r["harm_title"] and r["v7_score"] is not None
               and r["v7_score"] < ADVERSE_BAR]
    pick(harm_tp, n_a_tp, f"class-A harm-answered (TP, {args.class_a_tp_fp}:1)")
    pick(harm_fp, n_class_a - n_a_tp, "class-A harm-dominant (FP)")

    # 2. the score strata, each split so the non-Latin target is met WITHIN the draw rather
    #    than hoped for across it.
    #    ⚠️ Per-stratum `round(want * share)` sums BELOW the corpus-level target -- six
    #    round-downs cost a row, and the draw then misses 0.0975 against 0.0976 and fails its
    #    own gate. Largest-remainder allocation, then a supply sweep, so the total is exact.
    order = ("pos_clear", "pos_marginal", "neg_high", "neg_mid", "neg_low", "stage1_low")
    remaining = {k: max(0, quotas.get(k, 0) - sum(1 for r in drawn if _stratum_of(r) == k))
                 for k in order}
    need_total = math.ceil(args.size * args.nonlatin_min) - sum(1 for r in drawn if r["non_latin"])
    need_total = max(0, need_total)
    supply = {k: len([r for r in strata[k] if r["non_latin"] and r["id"] not in taken])
              for k in order}
    base = sum(remaining.values())
    exact = {k: (need_total * remaining[k] / base if base else 0) for k in order}
    nl_quota = {k: min(int(exact[k]), remaining[k], supply[k]) for k in order}
    short = need_total - sum(nl_quota.values())
    for k in sorted(order, key=lambda k: -(exact[k] - int(exact[k]))):   # largest remainder
        if short <= 0:
            break
        room = min(remaining[k], supply[k]) - nl_quota[k]
        if room > 0:
            add = min(room, short)
            nl_quota[k] += add
            short -= add
    if short > 0:                       # second pass: any stratum with spare non-Latin supply
        for k in order:
            if short <= 0:
                break
            room = min(remaining[k], supply[k]) - nl_quota[k]
            if room > 0:
                add = min(room, short)
                nl_quota[k] += add
                short -= add
    if short > 0:
        raise SystemExit(
            f"FATAL: the pool cannot meet the non-Latin target -- {short} rows short after "
            f"allocating every available non-Latin row across all strata. State the target as "
            f"unreachable for this window rather than drawing a corpus that misses it.")
    for k in order:
        if remaining[k] <= 0:
            continue
        pick([r for r in strata[k] if r["non_latin"]], nl_quota[k], f"{k} non-Latin")
        pick([r for r in strata[k] if not r["non_latin"]], remaining[k] - nl_quota[k],
             f"{k} Latin")

    assert len({r["id"] for r in drawn}) == len(drawn) == args.size, "draw is not n distinct rows"
    got = realised(drawn)

    targets = {
        "positive_rate":     (">=", args.positive_rate * 0.9,  got["positive_rate"]),
        "positive_mix":      ("~",  args.positive_mix,         got["positive_mix_marginal"]),
        "non_latin_share":   (">=", args.nonlatin_min,         got["non_latin_share"]),
        "class_a_share":     (">=", args.class_a_min,          got["class_a_share"]),
    }
    checks, ok = {}, True
    for name, (op_, want, have) in targets.items():
        passed = (have >= want) if op_ == ">=" else (abs(have - want) <= 0.05)
        checks[name] = {"rule": op_, "target": want, "realised": have, "pass": passed}
        ok &= passed

    os.makedirs(args.out, exist_ok=True)
    corpus_path = os.path.join(args.out, "corpus.jsonl")
    with open(corpus_path, "w", encoding="utf-8") as f:
        for r in drawn:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # The manifest's counts are recomputed by READING BACK what was written, so a manifest
    # can never describe a file that does not exist in that shape (llm-distillery#127).
    reread = [json.loads(l) for l in open(corpus_path, encoding="utf-8")]
    if len(reread) != len(drawn):
        raise SystemExit("FATAL: wrote %d rows, read back %d" % (len(drawn), len(reread)))
    manifest = {
        "filter": "human_thriving", "version": "v8",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/corpus/draw_v8_corpus.py",
        "generator_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16],
        "seed": args.seed,
        "op_point": {"value": OP, "source": op_source},
        "provenance": prov,
        "exclusions": {
            "google_news": prov["counts"].get("excluded_google_news", 0),
            "short_form_mode": args.short_form,
            "short_form_dropped": dropped_short,
            "oracle_floor_chars": ORACLE_FLOOR,
        },
        "prefilter": {"applied": False,
                      "note": "ADR-018/019 amendment 2026-08-21: v8 ships no per-lens "
                              "prefilter; the multilingual e5 probe replaces keyword screening."},
        "spec": {k: v for k, v in vars(args).items() if k not in ("archive", "out", "dry_run")},
        "quotas": quotas,
        "constraint_method": "allocated by construction (class-A first, then non-Latin split within each score stratum); no post-hoc row swapping",
        "realised": realised(reread),
        "checks": checks,
        "all_targets_met": bool(ok),
    }
    with open(os.path.join(args.out, "corpus_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nwrote {corpus_path} ({len(drawn):,} rows) and corpus_manifest.json")
    for name, c in checks.items():
        print(f"   {'PASS' if c['pass'] else 'FAIL'}  {name:<18} "
              f"target {c['rule']} {c['target']:.4f}   realised {c['realised']:.4f}")
    if not ok:
        raise SystemExit("FATAL: at least one Gate 0 target is unmet. The corpus was written "
                         "so it can be inspected; do NOT label it.")


if __name__ == "__main__":
    main()
