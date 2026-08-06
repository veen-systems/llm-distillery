#!/usr/bin/env python3
"""LD#98: extract the rows needed to A/B the cd v6 e5 probe against the v5 keyword gate.

Companion to `measure_topic_gate_ab.py`. That script compares two *rule*
prefilters, both of which are pure Python and can run anywhere. The v6 candidate
is an embedding probe, which needs a GPU to be practical over a production
window — so the comparison is split in two:

  1. THIS script, on sadalsuud (where data/filtered/ lives): walk the window
     once, compute the BASELINE keyword-gate decision for every scored row
     exactly, and write out the article text the probe will need.
  2. `score_probe_ab.py`, on gpu-server: embed those rows, apply the probe, and
     print the A/B table.

Splitting it does NOT reintroduce the two-runs-cannot-be-compared problem that
`measure_topic_gate_ab.py` exists to avoid: both arms are still derived from a
single frozen pass over one file list, and rows are joined by article id.

Baseline exactness vs probe sampling
------------------------------------
The baseline gate is cheap, so its numbers are computed over EVERY scored row in
the window and written to the summary — no sampling anywhere in the baseline.

The probe is not cheap, so the rows file carries the union of:
  * every SURFACING row (raw >= the op-point) — criterion 1 (recall cost) is
    therefore exact, on the full 2.7k surfacing set, not a sample;
  * a seeded uniform sample of all scored rows — criterion 2 (screen-out
    fraction over the firehose) is an estimate, and `score_probe_ab.py` prints
    it with a CI and labels it as sampled.

`--gate` must point at the gate you actually mean to compare against. As of
2026-08-06 the NexusMind checkout on sadalsuud still carries the PRE-#86 gate
(235 topic stems); llm-distillery carries the post-`80dd399` gate (453). The
baseline for #98 is the post-fix gate, so stage that file across and pass it
here rather than letting the script find a local one.

Usage (on sadalsuud, from the NexusMind repo root):
    python3 extract_probe_ab_rows.py \
        --gate /tmp/cd_v5_gate_postfix.py \
        --cycles 64 --offset 15 \
        --sample 30000 --seed 42 \
        --out /tmp/cd_v6_ab_rows.jsonl --summary /tmp/cd_v6_ab_summary.json
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import random
import sys
from collections import Counter, defaultdict

NAME, OP, HIGH = "cultural_discovery", 4.0, 7.0

# e5-small truncates at 512 tokens. 4000 characters is comfortably beyond that
# in every language in this corpus (CJK is far denser per character), so the
# embedding is identical to one computed on the untruncated article while the
# file that crosses the network is a fraction of the size.
MAX_CHARS = 4000


def load_prefilter(path):
    """Load a prefilter module by file path and instantiate its filter class."""
    root = os.getcwd()
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location(f"pf_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = next(o for o in vars(mod).values()
               if isinstance(o, type) and getattr(o, "__module__", None) == mod.__name__
               and callable(getattr(o, "apply_filter", None)))
    return cls()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", required=True,
                    help="path to the BASELINE prefilter.py (see module docstring)")
    ap.add_argument("--version", default="5.0",
                    help="only score rows stamped with this filter version")
    ap.add_argument("--cycles", type=int, default=64)
    ap.add_argument("--offset", type=int, default=15)
    ap.add_argument("--sample", type=int, default=30000,
                    help="uniform sample of all scored rows, for the probe pass rate")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="/tmp/cd_v6_ab_rows.jsonl")
    ap.add_argument("--summary", default="/tmp/cd_v6_ab_summary.json")
    args = ap.parse_args()

    base = load_prefilter(args.gate)
    n_stems = len(getattr(base, "TOPIC_GATE_PATTERNS", []))
    print(f"baseline gate: {args.gate}  ({n_stems} topic stems)", file=sys.stderr)

    files = sorted(glob.glob(f"data/filtered/{NAME}/filtered_2026*.jsonl"))
    if args.offset:
        files = files[:-args.offset]
    files = files[-args.cycles:]
    print(f"window: {len(files)} cycles  {files[0][-24:]} .. {files[-1][-24:]}", file=sys.stderr)

    rng = random.Random(args.seed)

    n = surf = high = 0
    base_pass = base_blocked = base_high_blocked = 0
    per_lang = defaultdict(lambda: {"surf": 0, "base": 0})
    reasons = Counter()

    # Reservoir sample over all scored rows, so the sample is uniform without
    # needing to know the row count up front or hold the corpus in memory.
    reservoir = []
    seen = 0

    out = open(args.out, "w", encoding="utf-8")
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                a = r.get("nexus_mind_attributes", {}).get(NAME, {})
                raw = a.get("raw_weighted_average")
                if raw is None or str(a.get("version")) != args.version:
                    continue

                n += 1
                bp, br = base.apply_filter(dict(r))
                base_pass += bool(bp)

                lang = (r.get("language") or "??").lower()
                is_surf = raw >= OP
                is_high = raw >= HIGH

                if is_surf:
                    surf += 1
                    high += is_high
                    per_lang[lang]["surf"] += 1
                    if not bp:
                        base_blocked += 1
                        base_high_blocked += is_high
                        per_lang[lang]["base"] += 1
                        reasons[str(br)] += 1

                rec = {
                    "id": r.get("id"),
                    "title": r.get("title") or "",
                    "content": (r.get("content") or "")[:MAX_CHARS],
                    "language": lang,
                    "raw": raw,
                    "base_pass": bool(bp),
                    "base_reason": str(br),
                    "surfacing": is_surf,
                    "high": bool(is_high),
                }

                if is_surf:
                    # every surfacing row is written; criterion 1 is exact
                    rec["in_sample"] = False
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                else:
                    seen += 1
                    if len(reservoir) < args.sample:
                        reservoir.append(rec)
                    else:
                        j = rng.randrange(seen)
                        if j < args.sample:
                            reservoir[j] = rec

    for rec in reservoir:
        rec["in_sample"] = True
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    out.close()

    summary = {
        "window_cycles": len(files),
        "window_first": os.path.basename(files[0]),
        "window_last": os.path.basename(files[-1]),
        "gate_path": args.gate,
        "gate_topic_stems": n_stems,
        "filter_version": args.version,
        "n_scored": n,
        "n_surfacing": surf,
        "n_high": high,
        # Baseline numbers below are EXACT over all scored rows, not sampled.
        "base_pass_rate": base_pass / n if n else None,
        "base_surfacing_blocked": base_blocked,
        "base_surfacing_blocked_pct": base_blocked / surf if surf else None,
        "base_high_blocked": base_high_blocked,
        "base_block_reasons": dict(reasons),
        "per_lang": {k: dict(v) for k, v in per_lang.items()},
        # Sampling applies to the probe arm only.
        "n_nonsurfacing_seen": seen,
        "n_nonsurfacing_sampled": len(reservoir),
        "sample_seed": args.seed,
        "max_chars": MAX_CHARS,
    }
    with open(args.summary, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"scored rows {n:,}   surfacing {surf:,}   high {high}", file=sys.stderr)
    print(f"baseline: pass rate {base_pass/n:.4f}   surfacing blocked "
          f"{base_blocked} ({base_blocked/surf:.1%})   high blocked {base_high_blocked}",
          file=sys.stderr)
    print(f"wrote {args.out} and {args.summary}", file=sys.stderr)


if __name__ == "__main__":
    main()
