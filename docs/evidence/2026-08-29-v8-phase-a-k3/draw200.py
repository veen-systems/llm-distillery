"""Draw the Phase A k=3 cohort (200 rows, two strata) on the box that holds the archive.

Design is fixed in PREREGISTRATION.md; this file only executes it.

  Stratum R -- 150 rows, uniform at random over ALL eligible rows (production mix).
  Stratum B -- 50 rows, uniform at random over eligible rows with v7
               raw_weighted_average in [4.0, 5.0), MINUS anything R already took.

R is drawn from the whole pool, band rows included, so R stays an unbiased sample of
production. B is drawn afterwards from what R did not take.

Exclusions are the plan's, and identical to draw30.py so the two cohorts are comparable:
  - news.google.com  (sub-300-char headline echoes; never oracle-re-score -- CLAUDE.md)
  - content < 300 chars (the oracle floor, ground_truth.batch_scorer, #93)
  - stage_used != stage2 (a stage1_low score is an e5 PROBE estimate, not a Gemma score)

Reservoir sampling, single pass: the archive is ~1.7 GB and holding every eligible row
would need ~1.6 GB of dicts. Only the reservoirs are kept.

`draw_weight` is written into every row. A design weight that lives in a docstring is a
weight that gets lost the first time someone derives a second number from the cohort.
"""
import json, glob, os, random, re, sys
from collections import defaultdict

# Overridable ONLY so the shipped file is the file that gets exercised on a fixture --
# tidying a scratch copy into a committed module produces a different program, and the
# tidy-up is never re-run. Production runs pass nothing.
ARCHIVE = os.environ.get(
    "DRAW200_ARCHIVE",
    "/home/jeroen/local_dev/NexusMind/data/filtered/uplifting/filtered_*.jsonl")
N_R, N_B = 150, 50
B_LO, B_HI = 4.0, 5.0
B_RESERVOIR = 250          # oversampled so removing R-overlaps still leaves >= N_B
SEED = 20260829

FILES = sorted(glob.glob(ARCHIVE))          # re-enumerated NOW; the window rolls
if not FILES:
    raise SystemExit("FATAL: archive glob matched no files")

rng = random.Random(SEED)


def domain(u):
    m = re.match(r"https?://([^/]+)", u or "")
    return m.group(1).lower().replace("www.", "") if m else ""


def slim(r, wa, stage):
    return {k: r.get(k) for k in
            ("id", "title", "content", "url", "source", "published_date", "language")} | {
        "v7_raw_weighted_average": wa, "v7_stage_used": stage}


stats = defaultdict(int)
seen = set()
res_r, res_b = [], []          # reservoirs
n_elig = 0                     # |pool| for stratum R
n_band = 0                     # |pool| for stratum B

for fp in FILES:
    with open(fp, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                stats["unparsable"] += 1
                continue
            stats["rows"] += 1
            rid = r.get("id")
            if rid in seen:
                stats["dup_id"] += 1
                continue
            if domain(r.get("url")) == "news.google.com":
                stats["excl_gn"] += 1
                continue
            if len(r.get("content") or "") < 300:
                stats["excl_short"] += 1
                continue
            # NOT top-level: the scorer's output is nested per lens. Read off the row
            # root this returns None for every article and the draw silently empties.
            u = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            if not u:
                stats["excl_no_lens_block"] += 1
                continue
            if u.get("stage_used") != "stage2":
                stats["excl_stage1"] += 1
                continue
            wa = u.get("raw_weighted_average")
            if wa is None:
                stats["excl_no_score"] += 1
                continue

            seen.add(rid)
            stats["eligible"] += 1
            row = slim(r, wa, u.get("stage_used"))

            n_elig += 1
            if len(res_r) < N_R:
                res_r.append(row)
            else:
                j = rng.randrange(n_elig)
                if j < N_R:
                    res_r[j] = row

            if B_LO <= wa < B_HI:
                n_band += 1
                stats["in_band"] += 1
                if len(res_b) < B_RESERVOIR:
                    res_b.append(row)
                else:
                    j = rng.randrange(n_band)
                    if j < B_RESERVOIR:
                        res_b[j] = row

# Closed accounting is guaranteed by construction, so it proves nothing on its own --
# but a MISMATCH still proves a branch was added without a counter. Validate, don't trust.
accounted = (stats["dup_id"] + stats["excl_gn"] + stats["excl_short"]
             + stats["excl_no_lens_block"] + stats["excl_stage1"]
             + stats["excl_no_score"] + stats["eligible"])
if accounted != stats["rows"]:
    raise SystemExit(f"FATAL: {accounted} accounted != {stats['rows']} rows seen")

r_ids = {row["id"] for row in res_r}
b_pool = [row for row in res_b if row["id"] not in r_ids]
if len(b_pool) < N_B:
    print(json.dumps({"stats": dict(stats), "b_reservoir": len(res_b),
                      "b_after_r_removal": len(b_pool)}), file=sys.stderr)
    raise SystemExit(2)            # missing case RAISES, never returns a short draw
if len(res_r) < N_R:
    print(json.dumps({"stats": dict(stats)}), file=sys.stderr)
    raise SystemExit(2)

b_final = rng.sample(b_pool, N_B)

manifest = {
    "seed": SEED,
    # The resolved glob, so a fixture draw and a production draw are distinguishable
    # by more than a filename. DRAW200_ARCHIVE is read at import; without this the
    # manifest cannot tell you which population it described.
    "archive": ARCHIVE,
    "files": len(FILES),
    "window": [FILES[0].split("/")[-1], FILES[-1].split("/")[-1]],
    "stats": dict(stats),
    "pool_R": n_elig,
    "pool_B": n_band,
    "drawn_R": len(res_r),
    "drawn_B": len(b_final),
    "draw_weight_R": round(n_elig / N_R, 3),
    "draw_weight_B": round(n_band / N_B, 3),
}
print(json.dumps(manifest), file=sys.stderr)

for row in res_r:
    print(json.dumps(row | {"stratum": "R", "draw_weight": round(n_elig / N_R, 3)},
                     ensure_ascii=False))
for row in b_final:
    print(json.dumps(row | {"stratum": "B", "draw_weight": round(n_band / N_B, 3)},
                     ensure_ascii=False))
