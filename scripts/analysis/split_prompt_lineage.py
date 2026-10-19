#!/usr/bin/env python3
"""Recover the oracle prompt behind each row of a training split that carries no provenance (#179).

Every live split predates per-row provenance: rows hold only `id, title, content, url, labels,
dimension_names`. This joins the split's ids to every upstream `*.jsonl` row that stamps a
`prompt_hash`, under the given roots, and reports per row:

  hashes       which prompt hashes ANY upstream copy of the id carries
  label-match  which of those copies carry the split's labels EXACTLY

A row whose labels match no stamped copy was changed after the oracle (adjudication caps,
k-run means): its lineage is the prompt that scored it, its LABEL is not that prompt's output.
"All <= 2.0" is reported separately because adjudication caps moved-out rows at 2.0.

    python3 scripts/analysis/split_prompt_lineage.py datasets/training/human_thriving_v8_adj3 \
        --roots datasets/scored ~/lab/llm-distillery

⚠️ A join can only find what the roots hold: a "none" is a file not found, not a row with no prompt.
"""
import argparse
import collections
import glob
import json
import os


def stamped_blocks(obj):
    """(prompt_hash[:12], block) for every dict in `obj` that carries a prompt_hash."""
    if isinstance(obj, dict):
        if obj.get("prompt_hash"):
            yield str(obj["prompt_hash"])[:12], obj
        for v in obj.values():
            yield from stamped_blocks(v)


def block_labels(block, names):
    out = []
    for n in names:
        v = block.get(n)
        if v is None and isinstance(block.get("dims"), dict):
            v = block["dims"].get(n)
        if isinstance(v, dict):
            v = v.get("score")
        out.append(v)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("split_dir")
    ap.add_argument("--roots", nargs="+", default=["datasets/scored"])
    args = ap.parse_args()

    rows = {}
    for part in ("train", "val", "test"):
        for line in open(os.path.join(args.split_dir, f"{part}.jsonl"), encoding="utf-8"):
            r = json.loads(line)
            rows[r["id"]] = r
    names = next(iter(rows.values()))["dimension_names"]

    hits = collections.defaultdict(list)
    for root in args.roots:
        for f in glob.glob(os.path.join(os.path.expanduser(root), "**", "*.jsonl"), recursive=True):
            if not os.path.isfile(f):          # a directory named *.jsonl exists in the lab inbox
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if '"prompt_hash"' not in line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(r, dict) and r.get("id") in rows:
                        for h, blk in stamped_blocks(r):
                            hits[r["id"]].append((h, block_labels(blk, names)))

    counts = collections.Counter()
    for i, r in rows.items():
        want = [float(x) for x in r["labels"]]
        hs = sorted({h for h, _ in hits.get(i, [])})
        match = sorted({h for h, lab in hits.get(i, []) if None not in lab
                        and all(abs(float(a) - b) < 1e-6 for a, b in zip(lab, want))})
        shape = ""
        if hs and not match:
            capped = max(want) <= 2.0 and any(abs(x - 2.0) < 1e-9 for x in want)
            shape = " (all <= 2.0, capped)" if capped else " (other)"
        counts[f"hashes={'+'.join(hs) or 'none'} | label-match={'+'.join(match) or 'none'}{shape}"] += 1

    print(f"{args.split_dir}: {len(rows)} rows; roots: {', '.join(args.roots)}")
    for k, v in counts.most_common():
        print(f"{v:6d}  {k}")


if __name__ == "__main__":
    main()
