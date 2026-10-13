"""Step 1 of PREREGISTRATION.md: each build's top 60 in site order (ids only), from ovr.db rows.

    python3 docs/evidence/2026-10-13-belonging-daily-baseline/build_population.py <ovr_db_rows.json> > builds.json

<ovr_db_rows.json>: the belonging build query on sadalsuud's ovr.db with summaries.created_at, published since
2026-09-29 (the query is in README.md). Output: {build: [ids in site order, top 60]}. Ids, dates and scores only.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SR = HERE.parent / "2026-10-13-belonging-site-ranking"
sys.path.insert(0, str(SR))
from site_rank import pdate, site_order        # the formula that reproduced both pages

TOP = 60
rows = json.loads(Path(sys.argv[1]).read_text())
b13 = {r["id"] for r in json.loads((SR / "build_pop_20261013.json").read_text())}
p13 = {l.strip() for l in (SR / "page_ids_20261013.txt").read_text().splitlines() if l.strip()}
removed = b13 - p13                              # sticky-removal assumption (PREREGISTRATION.md section 1)
out = {}
for day in (9, 10, 11, 12):
    t = datetime(2026, 10, day, 14, 30, tzinfo=timezone.utc)
    floor = (t - timedelta(days=10)).date()
    pop = [r for r in rows if r["id"] not in removed and pdate(r["s_created"]) <= t
           and pdate(r["published_date"]) <= t and pdate(r["published_date"]).date() >= floor]
    out[t.strftime("%Y-%m-%dT%H:%MZ")] = site_order(pop, t)[:TOP]
live = json.loads((SR / "lenses_20261013" / "belonging.json").read_text())
out["2026-10-13T06:55Z"] = [r["id"] for r in live["page_order"]][:TOP]
print(json.dumps(out, indent=1))
