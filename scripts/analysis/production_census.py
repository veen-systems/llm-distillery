"""Production-side counterpart to corpus_census.py -- the SAME quantities, so the
corpus can be compared against what the scorer actually serves.

Conditioned on stage_used == 'stage2': a stage1_low row's score is an e5 probe
estimate, not a Gemma score, so mixing them would compare different instruments.
"""
import json, glob, os, sys, re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
from hcv1_probe import script_of

P = UpliftingPreFilterV7()
CV = P._compiled_exclusions["crime_violence"]
OP, ADVERSE_BAR = 4.5, 3.85


def pct(vals, p):
    if not vals:
        return 0.0
    v = sorted(vals)
    i = min(len(v) - 1, max(0, int(round((p / 100.0) * (len(v) - 1)))))
    return v[i]


def main(base):
    rows = skipped_stage = 0
    lens, was = [], []
    harm_title = harm_body_only = 0
    band = Counter(); harm_band = Counter(); scripts = Counter()
    domains = Counter(); langs = Counter()
    for f in sorted(glob.glob(os.path.join(base, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            up = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            v = up.get("raw_weighted_average")
            if v is None:
                continue
            if up.get("stage_used") != "stage2":
                skipped_stage += 1
                continue
            rows += 1
            title = r.get("title") or ""
            content = r.get("content") or ""
            was.append(v); lens.append(len(content))
            scripts[script_of(title + " " + content[:2000])] += 1
            langs[r.get("language") or "??"] += 1
            u = r.get("url") or ""
            m = re.match(r"https?://([^/]+)", u)
            if m:
                domains[m.group(1).lower().replace("www.", "")] += 1
            b = "hi>=4.5" if v >= OP else ("mid" if v >= ADVERSE_BAR else "lo<3.85")
            band[b] += 1
            if P.has_any_pattern(title.lower(), CV):
                harm_title += 1
                harm_band[b] += 1
            elif P.has_any_pattern(content[:2000].lower(), CV):
                harm_body_only += 1

    print("\n== PRODUCTION CENSUS (stage2 only) ==")
    print("rows: %d   (skipped, not stage2: %d)" % (rows, skipped_stage))
    print("\n--- (a) CLASS-A SHAPE ---")
    print("harm in TITLE     : %6d  (%.2f%%)" % (harm_title, 100.0 * harm_title / rows))
    print("harm in BODY only : %6d  (%.2f%%)" % (harm_body_only, 100.0 * harm_body_only / rows))
    print("harm-title rows by SCORE band:")
    for k in ("hi>=4.5", "mid", "lo<3.85"):
        print("   %-9s %6d  (%5.1f%% of harm-title)" % (k, harm_band[k], 100.0 * harm_band[k] / harm_title if harm_title else 0))
    print("\n--- (b) REPRESENTATIVENESS ---")
    print("POSITIVE BASE RATE (raw >= 4.5): %d / %d = %.2f%%" % (band["hi>=4.5"], rows, 100.0 * band["hi>=4.5"] / rows))
    print("bands: " + ", ".join("%s=%d (%.1f%%)" % (k, band[k], 100.0 * band[k] / rows) for k in ("hi>=4.5", "mid", "lo<3.85")))
    print("\nraw score percentiles: p10=%.2f p50=%.2f p90=%.2f p99=%.2f" % (pct(was, 10), pct(was, 50), pct(was, 90), pct(was, 99)))
    print("content length: p10=%d p50=%d p90=%d p99=%d" % (pct(lens, 10), pct(lens, 50), pct(lens, 90), pct(lens, 99)))
    print("\nscript: " + ", ".join("%s=%d (%.2f%%)" % (k, v, 100.0 * v / rows) for k, v in scripts.most_common()))
    print("language top-8: " + ", ".join("%s=%.1f%%" % (k, 100.0 * v / rows) for k, v in langs.most_common(8)))
    print("\nsource concentration: %d distinct domains" % len(domains))
    top = domains.most_common(10)
    print("   top-10 share: %.1f%%" % (100.0 * sum(c for _, c in top) / rows))
    for d, c in top:
        print("     %-38s %6d  %5.2f%%" % (d, c, 100.0 * c / rows))
    for probe in ("arxiv.org", "pubmed.ncbi.nlm.nih.gov"):
        print("   %-30s %6d  %5.2f%%" % (probe, domains.get(probe, 0), 100.0 * domains.get(probe, 0) / rows))


if __name__ == "__main__":
    main(sys.argv[1])
