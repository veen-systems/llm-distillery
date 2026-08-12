"""#106: does Google News mass in the normalization fit population distort the CDF?

Normalization is fitted from NexusMind filtered output at
`raw_weighted_average >= the filter's operating point` (ADR-014,
scripts/normalization/fit_normalization.py). Google News rows are 100%
sub-300-char headline echoes that can never be enriched (NM#310). Any that
clear the op-point enter the CDF that maps every real article's rank.

This script measures the effect rather than the share: it fits the repo's own
CDF twice per filter — once on the real fit population, once with GN rows
removed — and reports the resulting normalized-score delta on the NON-GN
articles, plus the count crossing normalized 4.0 (NexusMind's
`pipeline.enrichment.min_score`, the one consumer of a normalized score that
changes an outcome; visibility itself is `raw >= op-point` per ADR-022 and
cannot move).

Two rules this script exists to respect:

  * **Match GN on `'news.google.com' in url`, never on a `gn_` source-key
    prefix** — a key prefix identifies only the country-proxy population and
    under-counts total GN roughly 5:1
    (`memory/google-news-corpus-hypotheses.md`).
  * **The remote traversal mirrors `fit_normalization.py`'s exactly** — same
    nesting, same raw-vs-fallback rule, same threshold comparison — so the
    counted population IS the fit population, not an approximation.

Source caveat, carried into any report built on this: `filtered_*.jsonl` holds
only prefilter passers and drops source-type-excluded rows. That is the correct
source here because it is the SAME source the fitter reads, but it is not the
production corpus — shares here are not comparable to the corpus-wide 25.7%.

Usage:
    PYTHONPATH=. python scripts/research/gn_normalization_cdf_share.py --ssh sadalsuud
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from filters.common.score_normalization import apply_normalization_batch, fit_normalization

# (filtered/ subdirectory, lens key, op-point).
# The op-point is `stats.raw_min` of the DEPLOYED version's normalization.json,
# which the anchored fitter sets equal to the operating point by construction.
TARGETS = [
    ("uplifting", "uplifting", 4.5),
    ("investment_risk", "investment_risk", 4.25),
    ("cultural_discovery", "cultural_discovery", 4.0),
    ("belonging", "belonging", 4.0),
    ("nature_recovery", "nature_recovery", 3.75),
    ("solutions", "solutions", 2.25),
]

# NexusMind config/app.yaml pipeline.enrichment.min_score. Reads the NORMALIZED
# score (NM#319) — an independent constant that merely shares the value 4.0
# with several tier thresholds. It is NOT a tier boundary.
ENRICHMENT_GATE = 4.0

# The targets are interpolated into the source rather than passed as an argv
# element: ssh reassembles arguments through a remote shell, so a JSON string
# loses its quoting in transit and arrives as an unparseable fragment.
REMOTE_DUMP = r'''
import glob, json, math, os, sys
base = sys.argv[1]
targets = __TARGETS__
result = {}
for dirname, want, op in targets:
    rows = []
    for fp in sorted(glob.glob(os.path.join(base, dirname, "filtered_*.jsonl"))):
        with open(fp) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                attrs = d.get("nexus_mind_attributes", {})
                if not isinstance(attrs, dict):
                    continue
                for k, v in attrs.items():
                    if not (isinstance(v, dict) and "weighted_average" in v):
                        continue
                    if k.replace("-", "_") != want:
                        continue
                    raw = v.get("raw_weighted_average")
                    wa = raw if raw is not None else v.get("weighted_average")
                    if not isinstance(wa, (int, float)) or not math.isfinite(wa):
                        continue
                    if wa < op:
                        continue
                    u = d.get("url")
                    gn = 1 if (isinstance(u, str) and "news.google.com" in u) else 0
                    rows.append([round(float(wa), 4), gn, len(d.get("content") or "")])
    result[dirname] = {"op": op, "rows": rows}
print(json.dumps(result))
'''


def fetch(ssh_host: str, remote_base: str) -> dict:
    script = REMOTE_DUMP.replace("__TARGETS__", repr([list(t) for t in TARGETS]))
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", ssh_host, "python3", "-", remote_base],
        input=script, capture_output=True, text=True, timeout=900,
    )
    if proc.returncode != 0:
        sys.exit(f"remote dump failed: {proc.stderr[:2000]}")
    return json.loads(proc.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ssh", default="sadalsuud", help="host holding NexusMind filtered output")
    ap.add_argument("--remote-dir", default="/home/jeroen/local_dev/NexusMind/data/filtered")
    ap.add_argument("--cache", type=Path, help="write/reuse the raw dump here")
    ap.add_argument("--json", type=Path, help="write the result table here")
    args = ap.parse_args()

    if args.cache and args.cache.exists():
        data = json.loads(args.cache.read_text())
    else:
        data = fetch(args.ssh, args.remote_dir)
        if args.cache:
            args.cache.write_text(json.dumps(data))

    out = []
    for name, blob in data.items():
        arr = np.array(blob["rows"], dtype=float)
        scores, gn, lens = arr[:, 0], arr[:, 1].astype(bool), arr[:, 2]
        op = blob["op"]

        with_gn = fit_normalization(scores, name, "", anchor_min=op)
        without_gn = fit_normalization(scores[~gn], name, "", anchor_min=op)

        # Compare on the NON-GN population — what a reader actually sees ranked.
        real = scores[~gn]
        a = apply_normalization_batch(real, with_gn)
        b = apply_normalization_batch(real, without_gn)
        delta = np.abs(a - b)

        crossed = (a >= ENRICHMENT_GATE) != (b >= ENRICHMENT_GATE)
        lost = int(((a >= ENRICHMENT_GATE) & (b < ENRICHMENT_GATE)).sum())
        gained = int(((b >= ENRICHMENT_GATE) & (a < ENRICHMENT_GATE)).sum())

        out.append({
            "filter": name,
            "op_point": op,
            "n_fit": int(len(scores)),
            "gn_in_fit": int(gn.sum()),
            "gn_pct_of_fit": round(100 * float(gn.mean()), 2),
            "gn_median_content_len": float(np.median(lens[gn])) if gn.any() else None,
            "gn_max_content_len": float(lens[gn].max()) if gn.any() else None,
            "gn_median_score": round(float(np.median(scores[gn])), 3) if gn.any() else None,
            "fit_median_score": round(float(np.median(scores)), 3),
            "max_delta": round(float(delta.max()), 3),
            "p99_delta": round(float(np.percentile(delta, 99)), 3),
            "median_delta": round(float(np.median(delta)), 3),
            "pct_moving_ge_0.5": round(float(100 * (delta >= 0.5).mean()), 2),
            "crossing_enrichment_gate": int(crossed.sum()),
            "pct_crossing_enrichment_gate": round(float(100 * crossed.mean()), 3),
            "would_fall_under_gate": lost,
            "would_rise_over_gate": gained,
        })

    hdr = (f"{'filter':<20}{'n_fit':>8}{'GN%':>7}{'maxD':>7}{'medD':>7}"
           f"{'>=0.5':>7}{'cross 4.0':>11}{'':>3}dir")
    print(hdr)
    print("-" * len(hdr))
    for r in out:
        print(f"{r['filter']:<20}{r['n_fit']:>8}{r['gn_pct_of_fit']:>6.1f}%"
              f"{r['max_delta']:>7.2f}{r['median_delta']:>7.2f}"
              f"{r['pct_moving_ge_0.5']:>6.1f}%"
              f"{r['crossing_enrichment_gate']:>8} "
              f"({r['pct_crossing_enrichment_gate']:.2f}%)"
              f"   -{r['would_fall_under_gate']}/+{r['would_rise_over_gate']}")

    if args.json:
        args.json.write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
