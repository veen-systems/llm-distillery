"""Steps 1-2 of PREREGISTRATION.md: each build's top 60 under ranking H and under the current ranking (control).

    python3 docs/evidence/2026-10-15-belonging-h-replay/build_population.py > .../builds.json
    python3 docs/evidence/2026-10-15-belonging-h-replay/build_population.py --dated > .../builds_dated.json  (deviation)

Inputs (this directory; ids, dates and scores only):
  ovr_db_rows.json       the baseline README's ovr.db query (read-only on sadalsuud), run 2026-10-15T07:00Z
  page_ids_20261015.txt  card order of https://ovr.news/en/belonging/, fetched 2026-10-15T07:01Z; the page's
                         <meta> build time is BUILT_1015 below
Removals are the union of two observed builds (population minus page): 10-13 06:43Z (the site-ranking dir's
committed files) and 10-15 (these files). Sticky-removal assumption: PREREGISTRATION.md section 1.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SR = HERE.parent / "2026-10-13-belonging-site-ranking"
sys.path.insert(0, str(SR))
from site_rank import pdate, site_order           # the formula that reproduced both pages (control)
from replay import order                          # H, as ovr.news specified it on 2026-10-13

TOP = 60
BUILT_1015 = datetime(2026, 10, 15, 6, 37, 16, tzinfo=timezone.utc)
rows = json.loads((HERE / "ovr_db_rows.json").read_text())


def population(t):
    floor = (t - timedelta(days=10)).date()
    return [r for r in rows if pdate(r["s_created"]) <= t and pdate(r["published_date"]) <= t
            and pdate(r["published_date"]).astimezone(timezone.utc).date() >= floor]   # SQLite date() is UTC


b13 = {r["id"] for r in json.loads((SR / "build_pop_20261013.json").read_text())}
p13 = {l.strip() for l in (SR / "page_ids_20261013.txt").read_text().splitlines() if l.strip()}
b15 = {r["id"] for r in population(BUILT_1015)}
p15 = {l.strip() for l in (HERE / "page_ids_20261015.txt").read_text().splitlines() if l.strip()}
assert p15 <= b15, f"{len(p15 - b15)} page cards not in the rebuilt 10-15 population"
removed = (b13 - p13) | (b15 - p15)
observed = b13 | b15
# DEVIATION from PREREGISTRATION.md section 1, added after review (README "Deviation"): the sticky rule is refuted by
# the data (46 rows removed at 10-15 were on the 10-13 page). With --dated, a removal applies only to builds on its
# own side of 10-13: the 10-13 removals to builds up to 10-13, the 10-15 removals to the later builds.
DATED = "--dated" in sys.argv

builds = [datetime(2026, 10, d, 14, 30, tzinfo=timezone.utc) for d in range(9, 15)] + [BUILT_1015]
out = {"_meta": {"dated": DATED, "removed": len(removed), "removed_1013": len(b13 - p13), "removed_1015": len(b15 - p15),
                 "page_1015_cards": len(p15), "population_1015": len(b15)}}
for t in builds:
    rm = removed if not DATED else ((b13 - p13) if t.date() <= datetime(2026, 10, 13).date() else (b15 - p15))
    pop = [r for r in population(t) if r["id"] not in rm]
    key = t.strftime("%Y-%m-%dT%H:%MZ")
    out[key] = {"population": len(pop),
                "removal_unknown": sum(r["id"] not in observed for r in pop),
                "H": [r["id"] for r in order("H hybrid", pop, t)][:TOP],
                "control": site_order(pop, t)[:TOP],
                "under_24h": sorted(r["id"] for r in pop if (t - pdate(r["published_date"])).total_seconds() < 86400)}
page15 = [l.strip() for l in (HERE / "page_ids_20261015.txt").read_text().splitlines() if l.strip()]
c15 = out[BUILT_1015.strftime("%Y-%m-%dT%H:%MZ")]["control"]
out["_meta"]["control_reproduces_1015_page_top60"] = sum(a == b for a, b in zip(c15, page15[:TOP]))
print(json.dumps(out, indent=1))
