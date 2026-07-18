"""Extract per-solution-type e5 seed files for Solutions v4 corpus screening.

Reads the DeepSeek-scored calibration set, keeps content_type == "solution", and
writes one seed file per solution_type for embedding_screener.py. Per-type
centroids (not one global centroid) so the minority community/governance types
are not drowned — see filters/solutions/v4/DATA_SETUP_PLAN.md Step 0.

Hybrids feed BOTH the governance and community screens (a hybrid is, by
definition, partly each). Seeds carry title + content (what the screener embeds)
plus id/language for provenance and the multilingual-balance report.

Usage:
    PYTHONPATH=. python scripts/screening/extract_solution_seeds.py \
        --scored datasets/calibration/solutions_v4_calib350_deepseek.jsonl \
        --out-dir datasets/screening
"""

import argparse
import json
from collections import Counter
from pathlib import Path

ANALYSIS_FIELD = "solutions_analysis"
FIELDS = ["id", "title", "content", "language"]


def nonen(lang):
    return lang not in ("en", "en-US", "en-GB", "English")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", type=Path, required=True,
                    help="DeepSeek-scored calibration JSONL (carries solutions_analysis)")
    ap.add_argument("--out-dir", type=Path, default=Path("datasets/screening"))
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.scored, encoding="utf-8") if l.strip()]
    solutions = [r for r in rows if r.get(ANALYSIS_FIELD, {}).get("content_type") == "solution"]

    # type -> list of seed records; hybrids duplicated into gov + community.
    buckets = {"tech": [], "governance": [], "community": [], "hybrid": []}
    for r in solutions:
        t = r[ANALYSIS_FIELD].get("solution_type")
        if t in buckets:
            buckets[t].append({k: r.get(k, "") for k in FIELDS})

    seed_files = {
        "tech": buckets["tech"],
        "governance": buckets["governance"] + buckets["hybrid"],
        "community": buckets["community"] + buckets["hybrid"],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(solutions)} solution seeds  "
          f"(tech {len(buckets['tech'])}, governance {len(buckets['governance'])}, "
          f"community {len(buckets['community'])}, hybrid {len(buckets['hybrid'])})")
    for name, recs in seed_files.items():
        out = args.out_dir / f"seeds_{name}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        lang = Counter(rec.get("language", "?") for rec in recs)
        ne = sum(v for k, v in lang.items() if nonen(k))
        print(f"  seeds_{name}.jsonl: {len(recs)} seeds "
              f"({ne} non-English, {100*ne/max(len(recs),1):.0f}%) -> {out}")

    print("\nNOTE: augment seeds_community.jsonl with the ~20-30 hand-curated "
          "high-concreteness community seeds (DATA_SETUP_PLAN Step 0) before screening.")


if __name__ == "__main__":
    main()
