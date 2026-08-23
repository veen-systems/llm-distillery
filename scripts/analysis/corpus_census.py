"""Is the v7 training corpus a good corpus? Two questions the H-CV1 work left open.

(a) CLASS-A SHAPE: does the corpus contain the shape that fools the scorer --
    a harm subject carrying a positive fragment -- and how is it LABELLED?
    Counting crime keyword MATCHES (what I did before) is not the same question:
    the defect needs harm to be the DOMINANT SUBJECT, so this uses the TITLE.

(b) REPRESENTATIVENESS: length, script, source concentration, and above all the
    POSITIVE BASE RATE, against production.
"""
import json, glob, os, sys, re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
from hcv1_probe import script_of

P = UpliftingPreFilterV7()
CV = P._compiled_exclusions["crime_violence"]

NAMES = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact",
         "evidence_level", "benefit_distribution", "change_durability"]
W = {"human_wellbeing_impact": 0.3, "social_cohesion_impact": 0.2, "justice_rights_impact": 0.15,
     "evidence_level": 0.1, "benefit_distribution": 0.1, "change_durability": 0.15}
OP = 4.5
ADVERSE_BAR = 3.85


def wa(labels, apply_gk=True):
    s = dict(zip(NAMES, labels))
    v = sum(s[d] * W[d] for d in NAMES)
    if apply_gk and s["evidence_level"] < 3.0 and v > 3.0:
        v = 3.0
    return v


def pct(vals, p):
    if not vals:
        return 0.0
    v = sorted(vals)
    i = min(len(v) - 1, max(0, int(round((p / 100.0) * (len(v) - 1)))))
    return v[i]


def control():
    """The harm matcher must be able to say yes on a title, and no on a clean one."""
    yes = P.has_any_pattern("man convicted of murder", CV)
    no = P.has_any_pattern("library reopens after renovation", CV)
    print("  control harm-title=%s clean-title=%s" % (yes, no))
    return yes and not no


def main(base):
    rows = 0
    lens, was = [], []
    harm_title = 0
    harm_body_only = 0
    band = Counter()          # overall label bands
    harm_band = Counter()     # label bands for harm-in-title rows
    scripts = Counter()
    domains = Counter()
    examples_hi, examples_lo = [], []
    for f in sorted(glob.glob(os.path.join(base, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            labels = r.get("labels")
            if not labels or len(labels) != 6:
                continue
            rows += 1
            title = r.get("title") or ""
            content = r.get("content") or ""
            v = wa(labels)
            was.append(v)
            lens.append(len(content))
            scripts[script_of(title + " " + content[:2000])] += 1
            u = r.get("url") or ""
            m = re.match(r"https?://([^/]+)", u)
            if m:
                domains[m.group(1).lower().replace("www.", "")] += 1

            b = "hi>=4.5" if v >= OP else ("mid" if v >= ADVERSE_BAR else "lo<3.85")
            band[b] += 1

            t_harm = P.has_any_pattern(title.lower(), CV)
            if t_harm:
                harm_title += 1
                harm_band[b] += 1
                if v >= OP and len(examples_hi) < 12:
                    examples_hi.append((round(v, 2), title[:95]))
                elif v < ADVERSE_BAR and len(examples_lo) < 6:
                    examples_lo.append((round(v, 2), title[:95]))
            elif P.has_any_pattern(content[:2000].lower(), CV):
                harm_body_only += 1

    print("\n== CORPUS CENSUS: %s ==" % base)
    print("rows with labels: %d" % rows)

    print("\n--- (a) CLASS-A SHAPE (harm in the TITLE = dominant-subject proxy) ---")
    print("harm in TITLE          : %5d  (%.2f%%)" % (harm_title, 100.0 * harm_title / rows))
    print("harm in BODY only      : %5d  (%.2f%%)" % (harm_body_only, 100.0 * harm_body_only / rows))
    print("\nhow are the harm-in-title rows LABELLED by the oracle?")
    for k in ("hi>=4.5", "mid", "lo<3.85"):
        c = harm_band[k]
        print("   %-9s %5d  (%5.1f%% of harm-title rows)" % (k, c, 100.0 * c / harm_title if harm_title else 0))
    print("\n  >>> rows TEACHING THE DEFECT (harm title, labelled >= 4.5): %d" % harm_band["hi>=4.5"])
    print("  >>> rows TEACHING THE FIX  (harm title, labelled < 3.85): %d" % harm_band["lo<3.85"])
    if examples_hi:
        print("\n  examples of harm-title rows the oracle scored HIGH:")
        for v, t in examples_hi:
            print("     %5.2f  %s" % (v, t))
    if examples_lo:
        print("\n  examples of harm-title rows the oracle scored LOW:")
        for v, t in examples_lo:
            print("     %5.2f  %s" % (v, t))

    print("\n--- (b) REPRESENTATIVENESS ---")
    print("POSITIVE BASE RATE (oracle label >= 4.5): %d / %d = %.2f%%"
          % (band["hi>=4.5"], rows, 100.0 * band["hi>=4.5"] / rows))
    print("label bands: " + ", ".join("%s=%d (%.1f%%)" % (k, band[k], 100.0 * band[k] / rows)
                                      for k in ("hi>=4.5", "mid", "lo<3.85")))
    print("\nweighted-average label percentiles: p10=%.2f p50=%.2f p90=%.2f p99=%.2f"
          % (pct(was, 10), pct(was, 50), pct(was, 90), pct(was, 99)))
    print("content length: p10=%d p50=%d p90=%d p99=%d  (min=%d max=%d)"
          % (pct(lens, 10), pct(lens, 50), pct(lens, 90), pct(lens, 99), min(lens), max(lens)))
    print("\nscript: " + ", ".join("%s=%d (%.2f%%)" % (k, v, 100.0 * v / rows) for k, v in scripts.most_common()))
    print("\nsource concentration: %d distinct domains" % len(domains))
    top = domains.most_common(10)
    print("   top-10 share: %.1f%%" % (100.0 * sum(c for _, c in top) / rows))
    for d, c in top:
        print("     %-38s %5d  %5.2f%%" % (d, c, 100.0 * c / rows))


if __name__ == "__main__":
    print("== CONTROL ==")
    if not control():
        sys.exit("ABORT: harm matcher control failed")
    main(sys.argv[1])
