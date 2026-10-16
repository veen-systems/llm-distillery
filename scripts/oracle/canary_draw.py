"""Draw CANDIDATES for an oracle canary set (#177) from NexusMind production files. Step 1 of 2.

    python3 canary_draw.py --filter human_thriving --version 9.0 --days 7 --seed 20261016 \
        --dir /home/jeroen/local_dev/NexusMind/data/filtered/human_thriving > candidates.jsonl

Population: every distinct row (by id; newest file wins) in the filter's `filtered_*.jsonl` files from the last
`--days` days by file-name date, with ALL of:
  - `nexus_mind_attributes.<filter>.version == --version` and `stage_used == "stage2"` (a `stage1_low` row's
    `raw_weighted_average` is an e5 probe estimate, not a model score — CLAUDE.md working rule);
  - `'news.google.com' not in url` (never oracle-re-score a GN row; match on url, never on a source-key prefix);
  - `len(content) >= 300` (the labelling-time floor, `make_oracle_prefilter`: an item one oracle path refuses
    cannot be a canary for both paths).
Strata by the student's raw score against the op-point (the oracle's own score is unknown until the baseline run):
`hi` >= op, `near` [op - 1.5, op), `lo` < op - 1.5. Draws OVERSAMPLE x3 per stratum so step 2 (training-overlap
exclusion on b650) can drop rows and still fill 30 / 30 / 40. Counts and pool sizes go to stderr. Uses only the
standard library: it runs on sadalsuud's system python3.
"""
import argparse, glob, json, os, random, re, sys

TARGET = {"hi": 30, "near": 30, "lo": 40}
OVERSAMPLE = 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--op", type=float, default=4.5)
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.dir, "filtered_*.jsonl")))
    dates = sorted({re.search(r"filtered_(\d{8})_", f).group(1) for f in files})
    keep_dates = set(dates[-a.days:])
    files = [f for f in files if re.search(r"filtered_(\d{8})_", f).group(1) in keep_dates]
    if not files:
        raise SystemExit("FATAL: no files in the window")
    rows, why = {}, {"version": 0, "stage": 0, "gn": 0, "short": 0, "no_score": 0}
    for f in files:                                   # sorted by name = by time; newest wins the dedup
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            at = (r.get("nexus_mind_attributes") or {}).get(a.filter) or {}
            if at.get("version") != a.version:
                why["version"] += 1; continue
            if at.get("stage_used") != "stage2":
                why["stage"] += 1; continue
            if "news.google.com" in (r.get("url") or ""):
                why["gn"] += 1; continue
            if len(r.get("content") or "") < 300:
                why["short"] += 1; continue
            s = at.get("raw_weighted_average")
            if not isinstance(s, (int, float)):
                why["no_score"] += 1; continue
            rows[r["id"]] = {"id": r["id"], "title": r.get("title"), "content": r.get("content"),
                             "url": r.get("url"), "source": r.get("source"),
                             "published_date": r.get("published_date"), "language": r.get("language"),
                             "student_raw": s, "student_version": a.version, "file": os.path.basename(f)}
    strata = {"hi": [], "near": [], "lo": []}
    for r in rows.values():
        s = r["student_raw"]
        strata["hi" if s >= a.op else "near" if s >= a.op - 1.5 else "lo"].append(r)
    rng = random.Random(a.seed)
    print(f"files {len(files)} ({min(keep_dates)}..{max(keep_dates)}); excluded {why}; "
          f"distinct eligible {len(rows)}", file=sys.stderr)
    for k, pool in strata.items():
        pool.sort(key=lambda r: r["id"])
        take = rng.sample(pool, min(len(pool), TARGET[k] * OVERSAMPLE))
        print(f"  stratum {k}: pool {len(pool)}, drawn {len(take)} (target {TARGET[k]})", file=sys.stderr)
        if len(take) < TARGET[k]:
            raise SystemExit(f"FATAL: stratum {k} has {len(pool)} rows, fewer than its target {TARGET[k]}")
        for i, r in enumerate(take):
            print(json.dumps(dict(r, stratum=k, draw_rank=i), ensure_ascii=False))


if __name__ == "__main__":
    main()
