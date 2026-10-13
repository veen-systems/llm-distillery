"""Reproduce ovr.news's Belonging page order offline (H-BB7; docs/TODO.md item 0a, option 1).

The site's order, read from ovr.news at c4aa42a3:
  - src/lib/data/pipeline.ts: rows = getArticlesForBuild(filter, 4.5, maxAgeDays=10); each gets
    _displayRank = calculateDisplayRank(weighted_average, published_date, language); sort; Chief Editor;
    then the merged lens is RE-SORTED by _displayRank, so the editor's two reorder rules
    (corroboration-boost, source-diversity) change nothing that survives. The editor, canonical-lens collapse
    and cluster dedup only REMOVE rows.
  - src/lib/ranking.ts calculateDisplayRank: weighted_average (NORMALIZED) x 0.85^age_days x language boost
    (1.0, so a no-op) x 1.3 if age < 24 h. A naive date means UTC (ADR-046).
So the page = the build population minus removed rows, ordered by rank() below. This script tests that claim
against two pages and prints what it finds:

    python3 docs/evidence/2026-10-13-belonging-site-ranking/site_rank.py > .../result.txt

Inputs, all in this directory and free of article text (ids, dates, scores only):
  page_ids_20261013.txt     card order of https://ovr.news/en/belonging/, fetched 2026-10-13T06:48:57Z
                            (page built 2026-10-13T06:43:02Z, the page's own timestamp)
  build_pop_20261013.json   getArticlesForBuild('belonging', 4.5, 10) on sadalsuud's ovr.db (read-only),
                            window anchored at 2026-10-13
  pop_window_20261012.json  the same query anchored at 2026-10-12, plus summaries.created_at, to rebuild
                            the 2026-10-12 page the owner labelled (../2026-10-12-belonging-personal-tag/tags.tsv)
⚠️ ovr.db holds each row's CURRENT score; a row re-scored between 10-12 and 10-13 would carry its new score.
"""
import csv, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAGS = HERE.parent / "2026-10-12-belonging-personal-tag" / "tags.tsv"
# Owner correction after the pre-registered count (../2026-10-12-belonging-personal-tag/README.md § Owner
# correction: "Slip: it's personal"). tags.tsv keeps the original label by rule 3; the correction is applied here.
OWNER_CORRECTIONS = {"professional_business_business_insider_78697b7d3cf0": "personal"}
DECAY, RECENCY_H, RECENCY_BOOST = 0.85, 24, 1.3          # ovr.news src/lib/config.ts `ranking`


def pdate(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def rank(row, now):
    age_h = max(0.0, (now - pdate(row["published_date"])).total_seconds() / 3600)
    return row["weighted_average"] * DECAY ** (age_h / 24) * (RECENCY_BOOST if age_h < RECENCY_H else 1.0)


def site_order(rows, now):
    """Ids in the order the page would show them at build time `now` (before editor/dedup removals)."""
    return [r["id"] for r in sorted(rows, key=lambda r: -rank(r, now))]


def live_page():
    now = datetime(2026, 10, 13, 6, 43, 2, tzinfo=timezone.utc)
    rows = {r["id"]: r for r in json.loads((HERE / "build_pop_20261013.json").read_text())}
    page = [l.strip() for l in (HERE / "page_ids_20261013.txt").read_text().splitlines() if l.strip()]
    pred = [i for i in site_order(rows.values(), now) if i in set(page)]
    print("== 1. live page, built 2026-10-13T06:43:02Z")
    print(f"page cards {len(page)}; build population {len(rows)}; page cards not in it "
          f"{len(set(page) - set(rows))}; population rows the page does not show {len(set(rows) - set(page))}")
    print(f"page order reproduced at {sum(a == b for a, b in zip(page, pred))}/{len(page)} positions; "
          f"top 30 at {sum(a == b for a, b in zip(page[:30], pred[:30]))}/30")
    ages = [(now - pdate(rows[i]["published_date"])).total_seconds() / 3600 for i in page[:30]]
    print(f"top 30 published < 24 h before the build: {sum(a < 24 for a in ages)}/30")


def owner_page():
    rows = json.loads((HERE / "pop_window_20261012.json").read_text())
    tags = list(csv.DictReader(TAGS.open(encoding="utf-8"), delimiter="\t"))
    page30 = [t["id"] for t in tags]
    print("\n== 2. the 2026-10-12 page the owner labelled (fetched 14:58:38Z; build time unknown, scanned)")
    print(f"page-30 ids absent from the population: {len(set(page30) - {r['id'] for r in rows})}")
    hits, t = [], datetime(2026, 10, 12, 0, 0, tzinfo=timezone.utc)
    while t <= datetime(2026, 10, 12, 14, 58, tzinfo=timezone.utc):
        pop = [r for r in rows if pdate(r["s_created"]) <= t and pdate(r["published_date"]) <= t]
        if [i for i in site_order(pop, t) if i in set(page30)] == page30:
            hits.append(t)
        t += timedelta(minutes=10)
    print(f"build times (10-min grid, 00:00-14:58Z) whose order matches all 30: {len(hits)}"
          + (f", {hits[0]:%H:%M}-{hits[-1]:%H:%M}Z" if hits else ""))
    if not hits:
        return
    t = hits[0]
    pop = [r for r in rows if pdate(r["s_created"]) <= t and pdate(r["published_date"]) <= t]
    order = site_order(pop, t)
    above = order[:order.index(page30[-1]) + 1]
    print(f"at {t:%H:%M}Z: rows ranked above the page's #30 that the page did not show (removed): "
          f"{len(set(above) - set(page30))}")
    byid = {r["id"]: r for r in pop}
    fresh = [r for r in pop if (t - pdate(r["published_date"])).total_seconds() < RECENCY_H * 3600]
    ages = [(t - pdate(byid[i]["published_date"])).total_seconds() / 3600 for i in page30]
    print(f"window population {len(pop)}, of which < 24 h old {len(fresh)}; page top 30 < 24 h old "
          f"{sum(a < 24 for a in ages)}/30 (oldest {max(ages):.1f} h)")
    by_score = {r["id"] for r in sorted(pop, key=lambda r: -r["weighted_average"])[:30]}
    print(f"page top 30 that are also in the top 30 by normalized score alone: {len(by_score & set(page30))}")
    personal = {t_["id"] for t_ in tags if t_["owner"] == "personal"}
    corrected = personal | {i for i, v in OWNER_CORRECTIONS.items() if v == "personal" and i in page30}
    print(f"owner-personal in the page top 30: {len(personal)} pre-registered (tags.tsv), {len(corrected)} after the "
          f"owner's correction")


if __name__ == "__main__":
    live_page()
    owner_page()
