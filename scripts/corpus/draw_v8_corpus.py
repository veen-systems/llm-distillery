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

def script_is_non_latin(text):
    """⛔⛔ THE CENSUS'S FUNCTION, COPIED VERBATIM from
    scripts/analysis/prefilter_removal_probe.py::script_of -- 15% of the first 2000 characters,
    not 50% of the first 400.

    The first version carried a hand-written test (50% / 400 chars) sitting under a comment
    claiming it was "the census's own definition, reused verbatim so the shares are one
    number". It was not, and a review measured the gap on the same 6,590 rows: census
    instrument 10.21%, hand-written 9.77%. That difference is the same size as the "we now
    enrich rather than match" claim it was used to support. A dead constant named NON_LATIN
    sat beside it, referenced nowhere.

    Copied rather than imported because the reduce pass runs on a host with no repo; the copy
    is verbatim and this docstring is its provenance."""
    lat = non = 0
    for ch in (text or "")[:2000]:
        o = ord(ch)
        if o < 0x0250 and ch.isalpha():
            lat += 1
        elif o > 0x0374 and ch.isalpha():
            non += 1
    if lat + non == 0:
        return False
    return (non / float(lat + non)) >= 0.15


def domain_of(url):
    if not url:
        return ""
    m = re.match(r"https?://([^/]+)", url)
    h = (m.group(1) if m else "").lower()
    # ⛔ NOT .lstrip("www.") -- that strips a CHARACTER SET, so washingtonpost.com became
    # ashingtonpost.com, wsj.com became sj.com, welt.de became elt.de. Measured 2026-08-29:
    # 1,897 of the 179,042 drawable rows (1.06%) carried a mangled domain, 1,171 of the 157,504
    # post-floor rows. A first draft of this comment said "1,460" and named NO POPULATION,
    # which is the defect it exists to record. The Google News exclusion survived only
    # because "news.google.com" happens not to start with w/./ -- any future host rule on a
    # w-domain would have failed silently.
    return h[4:] if h.startswith("www.") else h


def load_pool(archive, harm_re, keep_content=True):
    """Every distinct article in the window, first occurrence wins (the census's rule, so
    the two populations reconcile). Returns (records, provenance)."""
    files = sorted(glob.glob(os.path.join(archive, "filtered_*.jsonl")))
    if not files:
        raise SystemExit(f"FATAL: no filtered_*.jsonl under {archive}")
    seen, seen_text, out = set(), set(), []
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
            # ⛔ An id is SOURCE-SCOPED, so id-dedup is not text-dedup: measured 2026-08-29,
            # 1,280 pool rows share a content hash with a row under a DIFFERENT id (419
            # distinct texts), and 3 such pairs reached the first draw. Paying the oracle
            # twice is the small cost; the real one is a duplicate pair straddling the
            # train/test split and inflating the very test metric the #125 baseline uses.
            csha = hashlib.sha256((r.get("content") or "").encode("utf-8")).hexdigest()
            if csha in seen_text:
                counts["dup_text_other_id"] += 1
                continue
            seen_text.add(csha)
            up = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            content = r.get("content") or ""
            title = r.get("title") or ""
            dom = domain_of(r.get("url"))
            counts["articles"] += 1
            if dom == GN_DOMAIN:
                counts["excluded_google_news"] += 1
                continue
            rec = {
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
                "non_latin": script_is_non_latin(title + " " + content),
                "harm_title": bool(harm_re.search(title)) if title else False,
                # so materialisation can PROVE it rejoined the same article, not merely the id
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()[:16],
            }
            if not keep_content:
                rec.pop("content")
            out.append(rec)
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


def load_no_regression_ids(path):
    """The acceptance-test rows, which MUST NOT be drawn into the training corpus.

    ⛔ Nothing enforced this before 2026-08-30. The first draw's disjointness was luck: the
    three rows in the set at the time had aged out of the window entirely, so the pool could
    not contain them. Two rows added on 2026-08-30 ARE in the current pool, in design cell
    `pos_clear|latin|-`, whose inclusion probability is 0.0794 -- roughly a 1-in-13 chance per
    row that a re-draw quietly swallows a guard and hands it back to the gate as a training
    example it has already seen.

    Raises rather than defaulting to empty: an unreadable set and a set with no overlap both
    print "0 excluded", and only one of them is safe.
    """
    if not os.path.exists(path):
        raise SystemExit(
            f"FATAL: no-regression set not found at {path}. The draw refuses to run without "
            f"it -- a corpus that may contain the acceptance-test rows cannot be validated by "
            f"them. Pass --no-regression-set PATH, or run from a checkout that has it.")
    ids = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            aid = row.get("id")
            if not aid:
                raise SystemExit(f"FATAL: a row in {path} has no id; cannot exclude it.")
            # ⛔ The label check is not decoration: `datasets/adverse/uplifting.jsonl` sits in
            # the SAME directory, has the same shape, and carries 18 rows labelled "adverse".
            # Pointed at it, an id-only loader would run clean and silently strip 18 adverse
            # training examples out of the corpus -- a wrong-file error that fails in the
            # direction of looking fine, which is this repo's signature defect.
            if row.get("label") != "no_regression":
                raise SystemExit(
                    f"FATAL: {path} row {aid} is labelled {row.get('label')!r}, not "
                    f"'no_regression'. This flag takes the ACCEPTANCE-TEST set; it is not a "
                    f"general exclusion list.")
            ids.add(aid)
    if not ids:
        raise SystemExit(f"FATAL: {path} holds no rows. Refusing to draw against an empty "
                         f"exclusion set -- see the docstring.")
    return ids


def class_a_instrument():
    """The class-A detector, and it MUST be the one the Gate 0 spec's number came from.

    ⛔⛔ MEASURED 2026-08-29, and it is why this function exists: a hand-written harm lexicon
    (the fallback below) flags 5.04% of the drawable pool; `filters/uplifting/v7/prefilter.py`'s
    `crime_violence` patterns -- the instrument the 2026-08-28 census used -- flag 0.69%, which
    is the 0.70% the spec states. They agree on 758 rows out of ~9,500: 8,265 are lexicon-only
    and 483 are prefilter-only, so neither is a superset. Drawing the class-A supplement with
    the wrong one means enriching a population the ruling was never made about.

    Returns (predicate, name). The fallback is used only when the filters package is not
    importable, and the manifest records which one ran.
    """
    try:
        from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
        pats = UpliftingPreFilterV7()._compiled_exclusions["crime_violence"]
        return (lambda t: any(p.search(t) for p in pats) if t else False,
                f"filters/uplifting/v7/prefilter.py crime_violence ({len(pats)} patterns) -- "
                f"the 2026-08-28 census's instrument")
    except Exception as e:
        rx = _harm_re_fallback()
        return (lambda t: bool(rx.search(t)) if t else False,
                f"FALLBACK hand lexicon ({e.__class__.__name__}) -- flags ~7x as many rows as "
                f"the census instrument; the spec's 0.70% does NOT describe this population")


def _harm_re_fallback():
    """Title-level harm lexicon, used ONLY when the prefilter cannot be imported (e.g. the
    reduce pass, which runs on a host without torch). A candidate GENERATOR, never a
    population: no rate may be inherited from it (spec section 1g)."""
    return re.compile(
        r"\b(kill|killed|murder|shot|shoot|stab|rape|assault|abuse|attack|dead|death|dies|died|"
        r"crash|bomb|war|violence|victim|arrest|jail|prison|court|lawsuit|fraud|scandal|crisis|"
        r"disaster|flood|fire|quake|storm|drought|famine|outbreak|toll)\b", re.I)


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
    # ⛔ CLAUSE (c) -- "spend the freed budget on 1.5-3.5, the thinnest region and the origin
    # of stage-2 false positives". The first version allocated negatives strictly in
    # proportion to the pool, which COPIES the pool's shape rather than steering toward it:
    # the realised per-band ratios came out 1.0006 / 1.0000 / 0.9999 of the pool's, proof the
    # clause never acted. The band's improvement over v7 was a side effect of halving the
    # positive enrichment. `--low-middle-target` states the intended ratio against production
    # explicitly; 1.0 means parity, and the rows come out of neg_low (< 1.5), which is the
    # band production has most of and the task needs least.
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
    # clause (c): steer neg_mid (1.5-3.5) to the requested multiple of its POOL share, moving
    # rows out of neg_low. Reported either way, so a corpus that could not reach it says so.
    if args.low_middle_target:
        # ⚠️ The target is the band's share of the WHOLE POOL, not of the negative budget --
        # that is what the spec compares against and what the manifest check tests. The first
        # version scaled the band's share OF NEGATIVES, which lands ~3pp low and fails the
        # check it was written to satisfy. Rows come out of neg_low (< 1.5), the band
        # production has most of and the task needs least.
        pool_all = sum(len(v) for k, v in strata.items() if k != "unstratifiable")
        want_mid = round(n * (len(strata["neg_mid"]) / max(1, pool_all))
                         * args.low_middle_target)
        move = min(want_mid - quotas["neg_mid"], quotas["neg_low"],
                   len(strata["neg_mid"]) - quotas["neg_mid"])
        if move > 0:
            quotas["neg_mid"] += move
            quotas["neg_low"] -= move
        quotas["_low_middle_moved"] = max(0, move)
    moved = quotas.pop("_low_middle_moved", 0)
    assert sum(quotas.values()) == n, (sum(quotas.values()), n)
    return quotas, moved


def realised(rows):
    """Recompute every Gate 0 quantity FROM THE DRAWN ROWS. Nothing here reads the spec."""
    n = len(rows)
    s2 = [r for r in rows if r["v7_stage_used"] == "stage2" and r["v7_score"] is not None]
    pos = [r for r in s2 if r["v7_score"] >= OP]
    marg = [r for r in pos if r["v7_score"] < MID_TOP]
    lengths = sorted(r["content_length"] for r in rows)
    q = lambda p: lengths[min(len(lengths) - 1, int(p * (len(lengths) - 1)))] if lengths else 0
    # ⚠️ stage1_low rows carry an e5 PROBE estimate on a DIFFERENT SCALE -- measured range
    # 0.835-1.000 against stage2's 0-10 -- so "score < 3.85" sweeps every one of them in by
    # construction. Score-derived statistics are stage2-only.
    harm = [r for r in rows if r["harm_title"]]
    s2h = [r for r in harm if r["v7_stage_used"] == "stage2" and r["v7_score"] is not None]
    harm_hi = [r for r in s2h if r["v7_score"] >= OP]
    harm_lo = [r for r in s2h if r["v7_score"] < ADVERSE_BAR]
    return {
        "rows": n,
        # ⛔ TWO denominators, because a single "positive rate" hid a 2.20x-vs-2.0x error: the
        # ruled 9.76% baseline is measured stage2-only, while dividing by ALL drawn rows
        # includes stage1_low rows that can never be positive. A downstream correction applied
        # with the wrong one under-corrects by ~10%.
        "positive_rate": len(pos) / n if n else 0,
        "positive_rate_stage2": len(pos) / len(s2) if s2 else 0,
        "positive_mix_marginal": len(marg) / len(pos) if pos else 0,
        "non_latin_share": sum(r["non_latin"] for r in rows) / n if n else 0,
        "stage1_low_share": sum(r["v7_stage_used"] == "stage1_low" for r in rows) / n if n else 0,
        "class_a_share": len(harm) / n if n else 0,
        # ⛔ NOT a TP:FP ratio, and it was named one until 2026-08-30. This is
        # above-op : below-op among class-A rows. A below-op class-A row is a harm-lexicon
        # row scoring LOW, which under the ruled table is correct behaviour -- it is
        # neither the TP (harm answered) nor the FP (harm dominant, scoring high). Putting
        # it in the denominator measures a different quantity, and reading 47/33 as
        # "1.42:1 against a ruled 3:1" produced a "3:1 is unreachable, needs 62 of 59
        # available" conclusion that the owner ruling of 2026-08-30 retired.
        "class_a_above_below_op": (len(harm_hi) / len(harm_lo)) if harm_lo else None,
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
    ap.add_argument("--archive", help="directory of filtered_*.jsonl cycle files")
    ap.add_argument("--pool", help="a reduced pool file written by --reduce; draw from this instead of an archive")
    ap.add_argument("--reduce", metavar="OUT", help="stream the archive into a compact pool file (metadata only, NO article text) and exit. Runs where the data is, on a host that need not have torch or the filters package.")
    ap.add_argument("--out", help="directory: corpus.jsonl + corpus_manifest.json")
    ap.add_argument("--size", type=int)
    ap.add_argument("--seed", type=int, default=8829)
    ap.add_argument("--positive-rate", type=float, default=0.195)
    ap.add_argument("--positive-mix", type=float, default=0.635, help="share of positives in 4.5-5.5")
    ap.add_argument("--nonlatin-min", type=float, default=0.0976)
    ap.add_argument("--class-a-min", type=float, default=0.0070)
    ap.add_argument("--class-a-tp-fp", type=float, default=3.0)
    ap.add_argument("--low-middle-target", type=float, default=1.0,
                    help="target for the 1.5-3.5 band as a multiple of its share of the pool "
                         "(spec clause (c): spend the freed budget there). 1.0 = parity; 0 "
                         "disables the steer and copies the pool's negative shape.")
    ap.add_argument("--recall-cohort", type=int, default=0,
                    help="ALSO draw a held-out production-mix cohort of this many rows, "
                         "disjoint from the corpus, for train_probe.py --recall-check-file "
                         "(spec clause (d)). Reserved NOW because the corpus IS the training "
                         "set: a cohort carved out later overlaps it.")
    ap.add_argument("--stage1-share", type=float, default=None,
                    help="corpus share drawn from stage1_low; default = its share of the pool")
    ap.add_argument("--short-form", choices=("exclude", "include"), default="exclude",
                    help="rows under the 300-char ORACLE floor are dropped by "
                         "make_oracle_prefilter at labelling time (#93). 'include' draws them "
                         "anyway and records how many would be lost -- do not use it without "
                         "deciding what happens to them.")
    ap.add_argument("--no-regression-set",
                    default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__)))), "datasets", "adverse",
                        "uplifting_no_regression.jsonl"),
                    help="JSONL of the acceptance-test rows. Every id in it is REMOVED from "
                         "the pool before stratification, so a guard row can never become a "
                         "training example. The draw refuses to run if this file is missing.")
    ap.add_argument("--dry-run", action="store_true", help="report the plan, write nothing")
    args = ap.parse_args()

    if args.reduce:
        if not args.archive:
            raise SystemExit("FATAL: --reduce needs --archive")
        pool, prov = load_pool(args.archive, _harm_re_fallback(), keep_content=False)
        with open(args.reduce, "w", encoding="utf-8") as f:
            f.write(json.dumps({"__provenance__": prov}, ensure_ascii=False) + "\n")
            for r in pool:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("reduced %s articles -> %s drawable rows (Google News excluded: %s)"
              % (f"{prov['counts'].get('articles', 0):,}", f"{len(pool):,}",
                 f"{prov['counts'].get('excluded_google_news', 0):,}"))
        print("wrote " + args.reduce)
        print("NOTE: no article text in this file -- draw from it, then materialise the "
              "winners on the host that holds the archive.")
        return

    if not args.out or not args.size:
        raise SystemExit("FATAL: --out and --size are required unless --reduce is given")
    if bool(args.archive) == bool(args.pool):
        raise SystemExit("FATAL: give exactly one of --archive or --pool")

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


    if args.pool:
        lines = open(args.pool, encoding="utf-8").read().splitlines()
        prov = json.loads(lines[0])["__provenance__"]
        prov["drawn_from"] = "reduced pool file (metadata only; article text absent)"
        pool = [json.loads(l) for l in lines[1:] if l.strip()]
    else:
        pool, prov = load_pool(args.archive, _harm_re_fallback())
        prov["drawn_from"] = "archive directly (article text present)"
    # ⛔ The acceptance-test rows are removed FIRST -- before the short-form filter and before
    # stratification -- so they cannot be counted into a quota and then drawn. See
    # load_no_regression_ids() for why this is enforced rather than assumed.
    #
    # ⚠️ Order is load-bearing for the REPORT, not just the outcome. This ran AFTER the
    # short-form filter until it was reviewed: a guard row under the 300-char floor would then
    # have been dropped as short, counted as zero removals, and printed under "not in the
    # drawable pool" -- a message asserting a reason it had not established. Removing first
    # makes "declared minus removed" mean exactly one thing.
    no_regression_ids = load_no_regression_ids(args.no_regression_set)
    _before_nr = len(pool)
    pool = [r for r in pool if r["id"] not in no_regression_ids]
    dropped_no_regression = _before_nr - len(pool)
    print(f"no-regression set: {len(no_regression_ids)} ids declared, "
          f"{dropped_no_regression} removed from the pool "
          f"({len(no_regression_ids) - dropped_no_regression} not in the drawable pool -- "
          f"aged out of the window, or excluded upstream as Google News)")

    dropped_short = 0
    if args.short_form == "exclude":
        before = len(pool)
        pool = [r for r in pool if r["content_length"] >= ORACLE_FLOOR]
        dropped_short = before - len(pool)

    # ⛔ Recompute the class-A flag with the census's instrument. The reduce pass runs on a
    # host that cannot import the prefilter, so its flag is the fallback lexicon; leaving it
    # in place would draw the class-A supplement from a 7x larger, differently-defined class.
    is_class_a, class_a_name = class_a_instrument()
    for r in pool:
        r["harm_title"] = is_class_a(r.get("title") or "")
    print(f"class-A instrument: {class_a_name}")
    print(f"   flags {sum(r['harm_title'] for r in pool):,} of {len(pool):,} pool rows "
          f"= {sum(r['harm_title'] for r in pool) / max(1, len(pool)):.2%}")

    strata = stratify(pool)
    if strata.get("unstratifiable"):
        print(f"   ⚠️  {len(strata['unstratifiable']):,} rows are UNSTRATIFIABLE (neither "
              f"stage2-with-a-score nor stage1_low) and can never be drawn. A new stage_used "
              f"value upstream would land here silently -- the manifest records the count.")
    quotas, low_middle_moved = allocate(args, strata)
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

    def pick(bucket, n, what, into=None):
        """Reserve n rows and return them. ⛔ It does NOT append to `drawn` implicitly: the
        first version did, so the held-out recall cohort silently landed in the corpus as well
        and its own disjointness assertion caught it. Callers say where the rows go."""
        avail = [r for r in bucket if r["id"] not in taken]
        if n > len(avail):
            raise SystemExit(
                f"FATAL: quota '{what}' asks for {n} rows, pool offers {len(avail)}. "
                f"Reduce --size, or relax the target -- do NOT let this pass silently.")
        got = rng.sample(avail, n)
        for r in got:
            taken.add(r["id"])
        if into is not None:
            into.extend(got)
        return got

    # 1. class-A supplement -- BOTH ARMS ABOVE THE OP-POINT.
    #
    # ⛔⛔ The first version drew the "FP" arm from harm-title rows scoring BELOW the adverse
    # bar (3.85). That violates the spec verbatim -- "Sample the supplement ABOVE the op-point
    # (ADR-023): that is where junk reaches readers. Do not hunt the cheap error below it." --
    # and it is inert as a teaching signal: those 12 rows scored 1.16-2.08, i.e. rows v7
    # ALREADY handles correctly. The class-A defect is a row the student scores HIGH.
    #
    # ⚠️ The TP/FP distinction in the ruling ("harm answered" vs "harm is the dominant
    # subject") is a SHAPE judgement made within the above-op population. It is not a score
    # split and this script cannot make it: the draw selects the population, and the 3:1
    # balance is established by ADJUDICATION at labelling time. The manifest says so rather
    # than reporting a ratio the draw did not achieve.
    n_class_a = math.ceil(args.size * args.class_a_min)
    class_a_pool = [r for r in pool
                    if r["harm_title"]
                    and r["v7_stage_used"] == "stage2"      # a stage1_low score is a PROBE
                    and r["v7_score"] is not None           # estimate, not a Gemma score
                    and r["v7_score"] >= OP]
    if len(class_a_pool) < n_class_a:
        raise SystemExit(
            f"FATAL: the class-A supplement needs {n_class_a} rows ABOVE the op-point and this "
            f"window holds {len(class_a_pool)}. Widen the window or lower --class-a-min; do NOT "
            f"fall back to rows below the op-point -- the spec forbids it (ADR-023) and they "
            f"teach nothing the student does not already do.")
    supp = pick(class_a_pool, n_class_a, "class-A supplement (all above the op-point)", drawn)
    supplement = {
        "rows": len(supp),
        "drawn_from": f"harm-title AND stage2 AND v7_score >= {OP}",
        "pool_available": len(class_a_pool),
        "pool_consumed": len(supp) / len(class_a_pool),
        "ruled_tp_fp": args.class_a_tp_fp,
        "tp_fp_status": "NOT SET BY THE DRAW -- 'harm answered' vs 'harm dominant' is a shape "
                        "judgement within the above-op population and must be adjudicated at "
                        "labelling time (spec section 3).",
        "score_range": [min(r["v7_score"] for r in supp), max(r["v7_score"] for r in supp)],
        "non_latin": sum(r["non_latin"] for r in supp),
    }

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
    # ⛔⛔ PRESERVE EACH STRATUM'S OWN non-Latin SHARE, then top up minimally to reach the
    # corpus-level target. Two earlier rules were both wrong, in opposite directions:
    #   * proportional to each stratum's RESIDUAL QUOTA -> forces one flat ~9.8% share into
    #     every stratum, erasing the script-by-score association (pool 0.877x -> corpus 0.994x)
    #     and over-drawing non-Latin in pos_clear by 1.28x;
    #   * proportional to each stratum's non-Latin SUPPLY -> pushes non-Latin into the big
    #     negative strata, because corpus quotas are enriched toward positives while supply is
    #     not. Measured: corpus 0.434x against the pool's 0.917x, i.e. worse than before.
    # Keeping P(non-Latin | stratum) at the pool's value is the only rule that leaves the
    # association where production put it. The corpus-level target is then met by a top-up
    # spread over spare supply, which is a small, recorded distortion rather than a wholesale
    # reshaping.
    pool_nl_share = {k: (sum(1 for r in strata[k] if r["non_latin"]) / len(strata[k]))
                     if strata[k] else 0.0 for k in order}
    exact = {k: remaining[k] * pool_nl_share[k] for k in order}
    nl_quota = {k: min(int(round(exact[k])), remaining[k], supply[k]) for k in order}
    short = need_total - sum(nl_quota.values())
    if short < 0:                       # conditional shares already exceed the target: keep
        short = 0                       # them, the target is a FLOOR, not a level
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
        pick([r for r in strata[k] if r["non_latin"]], nl_quota[k], f"{k} non-Latin", drawn)
        pick([r for r in strata[k] if not r["non_latin"]], remaining[k] - nl_quota[k],
             f"{k} Latin", drawn)

    assert len({r["id"] for r in drawn}) == len(drawn) == args.size, "draw is not n distinct rows"

    # 3. the held-out recall-check cohort (spec clause (d)), reserved BEFORE labelling.
    #    ⛔ The corpus IS the probe's training set. train_probe.py's own warning is that a
    #    later cohort "may overlap train -- a guard, not a clean test". Reserving it now is
    #    the only moment it can be disjoint by construction. Its positives sit at PRODUCTION's
    #    rate and mix, not the corpus's enriched ones -- that is the whole point of it.
    cohort = []
    if args.recall_cohort:
        prod_pos_rate = (sum(1 for r in pool if _stratum_of(r) in ("pos_clear", "pos_marginal"))
                         / max(1, sum(1 for r in pool if _stratum_of(r) != "stage1_low")))
        n_c = args.recall_cohort
        n_c_pos = round(n_c * prod_pos_rate)
        n_c_marg = round(n_c_pos * args.positive_mix)
        cohort += pick(strata["pos_marginal"], n_c_marg, "cohort marginal positives")
        cohort += pick(strata["pos_clear"], n_c_pos - n_c_marg, "cohort clear positives")
        neg_avail = {k: [r for r in strata[k] if r["id"] not in taken]
                     for k in ("neg_high", "neg_mid", "neg_low")}
        tot = sum(len(v) for v in neg_avail.values())
        want = n_c - n_c_pos
        got = 0
        for i, k in enumerate(("neg_high", "neg_mid", "neg_low")):
            take_n = (want - got) if i == 2 else round(want * len(neg_avail[k]) / tot)
            cohort += pick(strata[k], take_n, f"cohort {k}")
            got += take_n
        assert len({r["id"] for r in cohort}) == len(cohort) == n_c
        assert not ({r["id"] for r in cohort} & {r["id"] for r in drawn}), \
            "recall cohort overlaps the corpus -- it would not be a held-out test"
    # (5) DESIGN WEIGHTS TRAVEL WITH THE ROWS. Inclusion probabilities run ~19.5x across the
    # cells of this design; a single scalar "2.0x enrichment" cannot carry that, and a corpus
    # whose weights live only in a docstring is the `sample-carries-its-design-weighting`
    # failure waiting to happen. Every drawn row gets its own pi.
    cell_n, cell_drawn = Counter(), Counter()
    cell_of = lambda r: (_stratum_of(r), bool(r["non_latin"]), bool(r["harm_title"]))
    for r in pool:
        cell_n[cell_of(r)] += 1
    for r in drawn:
        cell_drawn[cell_of(r)] += 1
    for r in drawn:
        c = cell_of(r)
        r["inclusion_probability"] = cell_drawn[c] / cell_n[c] if cell_n[c] else None
        r["design_cell"] = f"{c[0]}|{'non_latin' if c[1] else 'latin'}|{'classA' if c[2] else '-'}"

    got = realised(drawn)

    # ⚠️ Every rule is TWO-SIDED where the spec states a level rather than a floor. The first
    # version passed `positive_rate` at ">= 0.9x target" with NO upper bound -- a 30% draw
    # would have reported PASS against a ruled 19.5%. And there was no check at all for the
    # SHAPE clauses, so `all_targets_met: true` was silent about the two the spec argues
    # hardest for.
    pool_share = lambda pred: (sum(1 for r in pool if pred(r)) / len(pool)) if pool else 0.0
    band = lambda lo, hi: pool_share(lambda r: r["v7_stage_used"] == "stage2"
                                     and r["v7_score"] is not None and lo <= r["v7_score"] < hi)
    got_band = lambda lo, hi: (sum(1 for r in drawn if r["v7_stage_used"] == "stage2"
                                   and r["v7_score"] is not None and lo <= r["v7_score"] < hi)
                               / len(drawn))
    targets = {
        "positive_rate":   ("~", args.positive_rate, got["positive_rate"], 0.02),
        "positive_mix":    ("~", args.positive_mix, got["positive_mix_marginal"], 0.05),
        "non_latin_share": (">=", args.nonlatin_min, got["non_latin_share"], None),
        "class_a_share":   (">=", args.class_a_min, got["class_a_share"], None),
        # clause (a): "add no mass above 5.5" -- read as "no more than the rate x mix implies",
        # which is the only reading compatible with the ruled 19.5%/63.5 (the literal reading
        # and the base rate cannot both hold; see the spec-compliance review 2026-08-29).
        "clause_a_5_5_plus": ("<=", args.positive_rate * (1 - args.positive_mix) * 1.05,
                              got_band(MID_TOP, 99), None),
        # clause (c): "spend the freed budget on 1.5-3.5"
        "clause_c_low_middle": (">=", band(1.5, 3.5) * args.low_middle_target * 0.95,
                                got_band(1.5, 3.5), None),
    }
    checks, ok = {}, True
    for name, spec in targets.items():
        op_, want, have, tol = spec
        if op_ == "~":
            passed = abs(have - want) <= tol
        elif op_ == ">=":
            passed = have >= want
        else:
            passed = have <= want
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
            "no_regression_set": args.no_regression_set,
            "no_regression_ids_declared": len(no_regression_ids),
            "no_regression_rows_removed": dropped_no_regression,
        },
        "class_a": {
            "instrument": class_a_name,
            "pool_share": sum(r["harm_title"] for r in pool) / max(1, len(pool)),
            # ✅ RULED 2026-08-30 (docs/decisions/2026-08-30-v8-phase-b-rulings.md §3): the 3:1
            # applies to the corpus's class-A rows ABOVE THE OP-POINT -- and that population is
            # exactly the supplement, because the ordinary strata contributed 0 above-op class-A
            # rows of their own. The corpus reading and the supplement reading select the SAME
            # rows once the ruling's own op-point clause is kept, so there is one ruled quantity
            # here, not two, and it is settled by ADJUDICATION at labelling time, never by a draw.
            "supplement": supplement,
            "corpus_level_above_below_op_ratio": got["class_a_above_below_op"],
            "corpus_level_note": "⛔ NOT the ruled ratio and not a TP:FP. This is above-op : "
                                 "below-op over all class-A rows in the corpus. A below-op "
                                 "class-A row is neither TP (harm answered) nor FP (harm "
                                 "dominant, scoring HIGH) under the ruled table -- it is a "
                                 "harm-lexicon row behaving correctly. Do not quote it as "
                                 "compliance with, or a miss against, the 3:1.",
        },
        "prefilter": {"applied": False,
                      "note": "ADR-018/019 amendment 2026-08-21: v8 ships no per-lens "
                              "prefilter; the multilingual e5 probe replaces keyword screening."},
        "spec": {k: v for k, v in vars(args).items() if k not in ("archive", "out", "dry_run")},
        "quotas": quotas,
        "pool_strata": {k: len(v) for k, v in strata.items()},
        "design_cells": {f"{k[0]}|{'non_latin' if k[1] else 'latin'}|{'classA' if k[2] else '-'}":
                         {"pool": cell_n[k], "drawn": cell_drawn[k],
                          "inclusion_probability": cell_drawn[k] / cell_n[k] if cell_n[k] else None}
                         for k in sorted(cell_n, key=str) if cell_drawn[k]},
        "enrichment": {
            "ruled_factor": 2.0,
            "baseline_population": "drawable, stage2-only, all lengths (the census's population "
                                   "C, source of the 9.76% the ruling used)",
            "baseline_positive_rate": None,   # filled below, measured on the pool as loaded
            "note": "the factor a downstream class-weighting or calibration correction should "
                    "use is `realised_factor_vs_baseline`, NOT the ruled 2.0 -- they differ "
                    "because the draw excludes short-form rows, whose positive rate is 6.9x "
                    "lower, so the population actually sampled is already enriched relative "
                    "to the population the ruling was measured on.",
        },
        "low_middle_rows_moved": low_middle_moved,
        "non_latin_allocation": {
            "rule": "P(non-Latin | stratum) held at the pool's value, then topped up to the "
                    "corpus-level floor from spare supply",
            "per_stratum_pool_share": {k: round(v, 5) for k, v in pool_nl_share.items()},
            "per_stratum_drawn": {k: (sum(1 for r in drawn
                                          if _stratum_of(r) == k and r["non_latin"])
                                      / max(1, sum(1 for r in drawn if _stratum_of(r) == k)))
                                  for k in pool_nl_share},
        },
        "recall_cohort": ({"rows": len(cohort), "file": "recall_cohort.jsonl",
                           "positive_rate": sum(1 for r in cohort
                                                if r["v7_score"] is not None
                                                and r["v7_score"] >= OP) / max(1, len(cohort)),
                           "disjoint_from_corpus": True}
                          if cohort else
                          {"rows": 0, "note": "NOT RESERVED -- spec clause (d) needs a "
                                              "production-mix cohort and a later carve-out "
                                              "overlaps the training set"}),
        "staged_artifact": {"note": "the file Phase B will label is materialised separately; "
                                    "record its host, path, sha256 and row count here once "
                                    "staged (materialise_corpus.py prints them)"},
        "pool_reference": {
            "population": "post-300-floor drawable pool actually sampled",
            "rows": len(pool),
            "positive_rate_stage2": (sum(1 for r in pool if r["v7_stage_used"] == "stage2"
                                         and r["v7_score"] is not None and r["v7_score"] >= OP)
                                     / max(1, sum(1 for r in pool
                                                  if r["v7_stage_used"] == "stage2"))),
            "non_latin_share": pool_share(lambda r: r["non_latin"]),
            "class_a_share": pool_share(lambda r: r["harm_title"]),
            "band_1_5_to_3_5": band(1.5, 3.5),
            "band_5_5_plus": band(MID_TOP, 99),
        },
        "denominators": {
            "warning": "a ratio without its population is not a number. Every share under "
                       "`realised` is over ALL drawn rows (including stage1_low). The pool "
                       "shares under `pool_reference` are over the SAME post-300-floor pool "
                       "the draw sampled -- NOT the all-lengths, stage2-only population the "
                       "spec's 9.76% and 0.70% were measured on.",
        },
        "constraint_method": "allocated by construction (class-A first, then non-Latin split within each score stratum); no post-hoc row swapping",
        "realised": realised(reread),
        "checks": checks,
        "all_targets_met": bool(ok),
    }
    pool_s2 = [r for r in pool if r["v7_stage_used"] == "stage2" and r["v7_score"] is not None]
    pool_rate_s2 = (sum(1 for r in pool_s2 if r["v7_score"] >= OP) / len(pool_s2)) if pool_s2 else 0
    manifest["enrichment"]["baseline_positive_rate"] = pool_rate_s2
    manifest["enrichment"]["realised_positive_rate_stage2"] = got["positive_rate_stage2"]
    manifest["enrichment"]["realised_factor_vs_sampled_pool"] = (
        got["positive_rate_stage2"] / pool_rate_s2 if pool_rate_s2 else None)
    manifest["enrichment"]["sampled_pool_note"] = (
        "vs the POST-SHORT-FORM pool this draw sampled. Against the all-lengths drawable "
        "population the ruling was measured on, the factor is higher -- the manifest cannot "
        "compute that one because --short-form exclude removed those rows before the draw; "
        "the reduce pass's own counts give it.")
    with open(os.path.join(args.out, "corpus_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    if cohort:
        cohort_path = os.path.join(args.out, "recall_cohort.jsonl")
        with open(cohort_path, "w", encoding="utf-8") as f:
            for r in cohort:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"wrote {cohort_path} ({len(cohort):,} rows, production-mix, disjoint)")
    print(f"\nwrote {corpus_path} ({len(drawn):,} rows) and corpus_manifest.json")
    print(f"   class-A supplement: {supplement['rows']} rows, ALL above the op-point "
          f"(scores {supplement['score_range'][0]:.2f}-{supplement['score_range'][1]:.2f}), "
          f"{supplement['pool_consumed']:.0%} of the {supplement['pool_available']} available. "
          f"TP:FP is an ADJUDICATION task, not a score split -- ruled "
          f"{supplement['ruled_tp_fp']}:1, see the manifest.")
    for name, c in checks.items():
        print(f"   {'PASS' if c['pass'] else 'FAIL'}  {name:<18} "
              f"target {c['rule']} {c['target']:.4f}   realised {c['realised']:.4f}")
    if not ok:
        raise SystemExit("FATAL: at least one Gate 0 target is unmet. The corpus was written "
                         "so it can be inspected; do NOT label it.")


if __name__ == "__main__":
    main()
