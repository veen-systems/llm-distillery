"""H-CV1 arm C: run the prefilter version that EXISTED WHEN THE CORPUS WAS BUILT.

Corpus files are dated 2026-03-11. prefilter.py was created 2026-03-09 (991ffec) and
has changed four times since (\\b boundaries 04-29, branded content 07-27, length floor
removed 08-03).  Running today's version over a March corpus cannot settle whether the
prefilter shaped it.  This runs the March version.
"""
import json, glob, os, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filters.uplifting.v7.prefilter import UpliftingPreFilterV7

P = UpliftingPreFilterV7()


def control():
    cases = [
        ("murder", {"title": "Man convicted of murder", "content": "A jury found him guilty. " * 30, "url": "https://x.com/a"}, False),
        ("military", {"title": "State to expand its armed forces", "content": "Troops will be stationed near the capital. " * 30, "url": "https://x.com/b"}, False),
        ("finance", {"title": "Shares surge after earnings beat", "content": "The stock price rose on quarterly earnings. " * 30, "url": "https://x.com/c"}, False),
        ("clean", {"title": "Library reopens after renovation", "content": "The community library welcomed readers back this week. " * 30, "url": "https://x.com/d"}, True),
    ]
    ok = True
    for name, art, want_pass in cases:
        passed, reason = P.apply_filter(art)
        print("  control %-9s passed=%-5s reason=%s" % (name, passed, reason))
        if passed != want_pass:
            ok = False
    return ok


if __name__ == "__main__":
    print("== POSITIVE CONTROL ==")
    if not control():
        sys.exit("ABORT: control failed")
    base = sys.argv[1]
    files = sorted(glob.glob(os.path.join(base, "*.jsonl")))
    n = 0
    reasons = Counter()
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            n += 1
            passed, reason = P.apply_filter(r)
            if not passed:
                reasons["content_too_short" if "too_short" in reason else reason] += 1
    tb = sum(reasons.values())
    print("\n== MARCH PREFILTER over %s ==" % base)
    print("files: %d  rows: %d" % (len(files), n))
    print("BLOCKED: %d  (%.3f%%)" % (tb, 100.0 * tb / n if n else 0))
    for k, v in reasons.most_common():
        print("   %-34s %6d  %6.3f%%" % (k, v, 100.0 * v / n))
