"""Phase 0 (human_thriving v8): what is the DRAWABLE population, and what is its shape?

production_census.py answers "what does the scorer serve" -- rows, across every cycle
file in the archive.  That is the right instrument for comparing the v7 corpus against
production, and the wrong one for drawing a corpus, for two reasons the plan names but
never quantified:

  1. An article rescored in N cycles contributes N rows.  A draw wants articles.
  2. `news.google.com` is 22% of rows and must be excluded from any draw
     (sub-300-char headline echoes; never oracle-re-score them).

So the Gate 0 targets -- base rate, non-Latin share, length, class-A share -- have never
been stated on the population a draw would actually sample from.  This reports every
quantity at three nested stages so the effect of each exclusion is visible, not assumed.

Conditioned on stage_used == 'stage2' throughout: a stage1_low row's score is an e5 probe
estimate, not a Gemma score.

Usage: PYTHONPATH=<repo> python3 v8_draw_population.py <archive-dir>
"""
import json, glob, os, sys, re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
from prefilter_removal_probe import script_of

P = UpliftingPreFilterV7()
CV = P._compiled_exclusions["crime_violence"]
OP, ADVERSE_BAR = 4.5, 3.85
ORACLE_FLOOR = 300          # ground_truth.batch_scorer.make_oracle_prefilter (#93)
GN_DOMAIN = "news.google.com"


def pct(vals, p):
    if not vals:
        return 0.0
    v = sorted(vals)
    i = min(len(v) - 1, max(0, int(round((p / 100.0) * (len(v) - 1)))))
    return v[i]


def domain_of(url):
    m = re.match(r"https?://([^/]+)", url or "")
    return m.group(1).lower().replace("www.", "") if m else ""


class Stage:
    """One nested population.  Accumulates the same quantities for every stage."""

    def __init__(self, name):
        self.name = name
        self.n = 0
        self.lens, self.was = [], []
        self.band = Counter(); self.harm_band = Counter()
        self.scripts = Counter(); self.domains = Counter(); self.langs = Counter()
        self.harm_title = 0
        self.under_floor = 0

    def add(self, rec):
        v, title, content, dom, lang = rec
        self.n += 1
        self.lens.append(len(content))
        if v is not None:
            self.was.append(v)
        if len(content) < ORACLE_FLOOR:
            self.under_floor += 1
        self.scripts[script_of(title + " " + content[:2000])] += 1
        self.langs[lang] += 1
        if dom:
            self.domains[dom] += 1
        b = None
        if v is not None:
            b = "hi>=4.5" if v >= OP else ("mid" if v >= ADVERSE_BAR else "lo<3.85")
            self.band[b] += 1
        if P.has_any_pattern(title.lower(), CV):
            self.harm_title += 1
            if b:
                self.harm_band[b] += 1

    def report(self):
        n = self.n
        if not n:
            print("\n== %s ==\n  EMPTY -- refusing to report rates on an empty population" % self.name)
            return
        print("\n== %s ==" % self.name)
        print("  n                     : %d" % n)
        if self.was:
            print("  positive base rate    : %d / %d = %.2f%%  (raw >= %.1f)"
                  % (self.band["hi>=4.5"], n, 100.0 * self.band["hi>=4.5"] / n, OP))
        else:
            print("  positive base rate    : n/a -- stage1_low included; its score is an e5")
            print("                          probe estimate, not a Gemma score (never mix them)")
        print("  non-Latin script      : %d (%.2f%%)"
              % (self.scripts["non_latin"], 100.0 * self.scripts["non_latin"] / n))
        print("  content length        : p10=%d p50=%d p90=%d"
              % (pct(self.lens, 10), pct(self.lens, 50), pct(self.lens, 90)))
        print("  under the 300ch oracle floor: %d (%.2f%%)"
              % (self.under_floor, 100.0 * self.under_floor / n))
        print("  class-A shape (harm in title): %d (%.2f%%)"
              % (self.harm_title, 100.0 * self.harm_title / n))
        if self.harm_title and self.was:
            for k in ("hi>=4.5", "mid", "lo<3.85"):
                print("      %-9s %5d  (%5.1f%% of harm-title)"
                      % (k, self.harm_band[k], 100.0 * self.harm_band[k] / self.harm_title))
        print("  distinct domains      : %d   top-10 share %.1f%%"
              % (len(self.domains), 100.0 * sum(c for _, c in self.domains.most_common(10)) / n))
        for d, c in self.domains.most_common(6):
            print("      %-34s %6d  %5.2f%%" % (d, c, 100.0 * c / n))
        tot_l = sum(self.langs.values())
        print("  language top-8        : " + ", ".join(
            "%s=%.1f%%" % (k, 100.0 * c / tot_l) for k, c in self.langs.most_common(8)))


def main(base):
    files = sorted(glob.glob(os.path.join(base, "*.jsonl")))
    if not files:
        sys.exit("ABORT: no *.jsonl under %s -- an empty scan reports clean" % base)

    all_rows = Stage("A. ALL ROWS (every cycle file; production_census's population)")
    distinct = Stage("B. DISTINCT ARTICLES (dedup by id, first occurrence wins)")
    drawable = Stage("C. DRAWABLE (distinct, minus news.google.com)")
    pool = Stage("D. FULL POOL (C, plus stage1_low: the probe must not shape the draw)")

    seen_id, seen_hash = set(), set()
    dup_rows = total_rows = 0
    skipped_stage = skipped_noscore = 0
    id_missing = 0

    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            up = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            v = up.get("raw_weighted_average")
            if v is None:
                skipped_noscore += 1
                continue
            total_rows += 1
            is_s2 = up.get("stage_used") == "stage2"
            if not is_s2:
                skipped_stage += 1
            title = r.get("title") or ""
            content = r.get("content") or ""
            dom = domain_of(r.get("url"))
            rec = (v, title, content, dom, r.get("language") or "??")

            if is_s2:
                all_rows.add(rec)

            aid = r.get("id")
            if not aid:
                id_missing += 1
                continue
            h = r.get("content_hash")
            if h:
                seen_hash.add(h)
            if aid in seen_id:
                dup_rows += 1
                continue
            seen_id.add(aid)
            if is_s2:
                distinct.add(rec)
                if dom != GN_DOMAIN:
                    drawable.add(rec)
            if dom != GN_DOMAIN:
                pool.add((None, title, content, dom, r.get("language") or "??"))

    print("== v8 PHASE 0 -- DRAWABLE POPULATION ==")
    print("archive     : %s" % base)
    print("files       : %d   (%s .. %s)"
          % (len(files), os.path.basename(files[0]), os.path.basename(files[-1])))
    print("skipped     : not-stage2 %d, no score %d, no id %d" % (skipped_stage, skipped_noscore, id_missing))
    print("rows -> articles: %d scored rows (all stages), %d distinct ids, %d repeat rows"
          % (total_rows, len(seen_id), dup_rows))
    print("                  duplication %.4fx -- an article is scored ONCE, not per cycle"
          % (total_rows / float(len(seen_id)) if seen_id else 0.0))
    print("                  of those rows, %d are stage2 and %d stage1_low"
          % (all_rows.n, skipped_stage))
    print("distinct content_hash: %d  (vs %d ids -- #119: the dedup key is not settled)"
          % (len(seen_hash), len(seen_id)))

    for s in (all_rows, distinct, drawable, pool):
        s.report()


if __name__ == "__main__":
    main(sys.argv[1])
