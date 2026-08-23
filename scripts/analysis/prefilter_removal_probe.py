"""H-CV1: what does the uplifting v7 prefilter REMOVE from a population it did not select?

The 2026-08-21 attempt measured rows in the v7 CORPUS that matched crime_violence.
Those rows are override survivors of the filter under test -- checker and checked are
the same object, so the comparison cannot see depletion.

This runs the ACTUAL v7 prefilter (shipped, not reimplemented) over NexusMind production
rows.  The per-lens prefilter has never executed in the production scoring path
(NM#284, dead since 2026-02-10), so production is NOT selected by the filter under test.
That is the property that makes it a valid instrument.
"""
import json, glob, os, sys, re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filters.uplifting.v7.prefilter import UpliftingPreFilterV7

P = UpliftingPreFilterV7()


def diagnose(article):
    """Re-walk apply_filter's control flow, recording WHY, not just whether."""
    out = {"blocked_by": None, "matched": [], "rescued": []}
    url = article.get("url", "") or ""
    if url:
        d = P._check_domain_exclusions(url)
        if d:
            out["blocked_by"] = d
            return out
        for pat in P.BRANDED_CONTENT_PATH_PATTERNS:
            if re.search(pat, url, re.IGNORECASE):
                out["blocked_by"] = "branded_content"
                return out
    title = article.get("title", "") or ""
    text = (article.get("text") or article.get("content") or "")[:P.MAX_PREFILTER_CONTENT]
    combined = ("%s %s" % (title, text)).lower()
    for cat, pats in P._compiled_exclusions.items():
        if not P.has_any_pattern(combined, pats):
            continue
        out["matched"].append(cat)
        exc = P._compiled_exceptions_per_category.get(cat, [])
        if P.has_any_pattern(combined, exc):
            out["rescued"].append(cat)
            continue
        if out["blocked_by"] is None:
            out["blocked_by"] = cat
    if out["blocked_by"] is None:
        spec = P.count_pattern_matches(combined, P._compiled_speculation)
        outc = P.count_pattern_matches(combined, P._compiled_outcome_evidence)
        if spec >= 3 and outc == 0:
            out["blocked_by"] = "pure_speculation"
    return out


def script_of(text):
    """Coarse script bucket. Used only for REPORTING; never feeds diagnose()."""
    lat = non = 0
    for ch in text[:2000]:
        o = ord(ch)
        if o < 0x0250 and ch.isalpha():
            lat += 1
        elif o > 0x0374 and ch.isalpha():
            non += 1
    if lat + non == 0:
        return "none"
    return "latin" if non / float(lat + non) < 0.15 else "non_latin"


def diagnose_fingerprint():
    import hashlib, inspect
    return hashlib.sha256(inspect.getsource(diagnose).encode("utf-8")).hexdigest()[:16]


def control():
    """Positive control: the instrument MUST be able to say 'blocked'."""
    cases = [
        ("murder", {"title": "Man convicted of murder", "content": "A jury found him guilty. " * 30, "url": "https://x.com/a"}),
        ("military", {"title": "State to expand its armed forces", "content": "Troops will be stationed near the capital. " * 30, "url": "https://x.com/b"}),
        ("finance", {"title": "Shares surge after earnings beat", "content": "The stock price rose on quarterly earnings. " * 30, "url": "https://x.com/c"}),
    ]
    ok = True
    for name, art in cases:
        d = diagnose(art)
        blocked = d["blocked_by"] is not None
        print("  control %-9s blocked=%-5s by=%s" % (name, blocked, d["blocked_by"]))
        if not blocked:
            ok = False
    # negative control: a clean row must pass
    clean = {"title": "Library reopens after renovation",
             "content": "The community library welcomed readers back this week. " * 30,
             "url": "https://x.com/d"}
    d = diagnose(clean)
    print("  control %-9s blocked=%-5s by=%s" % ("clean", d["blocked_by"] is not None, d["blocked_by"]))
    if d["blocked_by"] is not None:
        ok = False
    return ok


def main(paths, label):
    n = 0
    blocked = Counter()
    matched = Counter()
    rescued = Counter()
    by_lang = defaultdict(lambda: [0, 0])          # lang -> [total, blocked]
    by_lang_cv = defaultdict(lambda: [0, 0])       # lang -> [cv_matched, cv_blocked]
    by_script = defaultdict(lambda: [0, 0])        # script -> [total, blocked]
    files = 0
    for f in paths:
        files += 1
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            n += 1
            body = "%s %s" % (r.get("title") or "", (r.get("content") or "")[:2000])
            lang = r.get("language") or ("script:" + script_of(body))
            scr = script_of(body)
            d = diagnose(r)
            by_lang[lang][0] += 1
            by_script[scr][0] += 1
            if d["blocked_by"]:
                blocked[d["blocked_by"]] += 1
                by_lang[lang][1] += 1
                by_script[scr][1] += 1
            for c in d["matched"]:
                matched[c] += 1
            for c in d["rescued"]:
                rescued[c] += 1
            if "crime_violence" in d["matched"]:
                by_lang_cv[lang][0] += 1
                if d["blocked_by"] == "crime_violence":
                    by_lang_cv[lang][1] += 1
    tb = sum(blocked.values())
    print("\n== %s ==" % label)
    print("files: %d   rows: %d" % (files, n))
    print("BLOCKED: %d  (%.3f%%)" % (tb, 100.0 * tb / n if n else 0))
    print("\nblock reason:")
    for k, v in blocked.most_common():
        print("   %-22s %7d  %6.3f%%" % (k, v, 100.0 * v / n))
    print("\ncategory MATCHED vs RESCUED by its own exception list:")
    for c in ("crime_violence", "military_security", "corporate_finance"):
        m, rs = matched[c], rescued[c]
        print("   %-20s matched %6d (%5.2f%%)  rescued %5d  -> blocked %6d  rescue rate %5.1f%%"
              % (c, m, 100.0 * m / n if n else 0, rs, blocked[c], 100.0 * rs / m if m else 0))
    print("\nremoval by language (top 12 by volume):")
    print("   %-6s %8s %8s %8s" % ("lang", "rows", "blocked", "rate%"))
    for lang, (tot, bl) in sorted(by_lang.items(), key=lambda kv: -kv[1][0])[:12]:
        print("   %-6s %8d %8d %8.2f" % (lang, tot, bl, 100.0 * bl / tot if tot else 0))
    print("\nremoval by SCRIPT:")
    for sc, (tot, bl) in sorted(by_script.items(), key=lambda kv: -kv[1][0]):
        print("   %-10s %8d %8d %8.2f%%" % (sc, tot, bl, 100.0 * bl / tot if tot else 0))
    print("\ncrime_violence MATCH RATE by language (the depletion-relevant number):")
    print("   %-6s %8s %10s %10s" % ("lang", "rows", "cv_match", "match%"))
    for lang, (tot, _) in sorted(by_lang.items(), key=lambda kv: -kv[1][0])[:12]:
        cm = by_lang_cv[lang][0]
        print("   %-6s %8d %10d %10.2f" % (lang, tot, cm, 100.0 * cm / tot if tot else 0))
    return {"rows": n, "blocked": tb, "by_reason": dict(blocked),
            "matched": dict(matched), "rescued": dict(rescued),
            "by_lang": {k: v for k, v in by_lang.items()}}


if __name__ == "__main__":
    print("diagnose() fingerprint:", diagnose_fingerprint())
    print("== POSITIVE CONTROL (instrument must be able to say 'blocked') ==")
    if not control():
        sys.exit("ABORT: control failed -- a zero from this instrument would be meaningless")
    base = sys.argv[1]
    files = sorted(glob.glob(os.path.join(base, "*.jsonl")))
    if not files:
        sys.exit("ABORT: no files at %s" % base)
    print("\nwindow: %s .. %s" % (os.path.basename(files[0]), os.path.basename(files[-1])))
    res = main(files, base)
    json.dump(res, open("/tmp/hcv1_result.json", "w"), indent=1)
