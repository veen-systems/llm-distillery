#!/usr/bin/env python3
"""Convert a box_parity.py prediction dump into ground_truth_gate.py model input.

WHY THIS EXISTS
---------------
`datasets/parity/*.jsonl` holds **uncalibrated** per-dimension logits. The deploy
gate (ADR-021) must judge what production actually surfaces, which is the
*calibrated, clamped* score. Comparing the raw `wavg` field against a threshold
reproduces neither the gate nor production -- see `datasets/parity/README.md`.

So this applies the filter's committed `calibration.json` per dimension and
clamps to 0-10, then emits `{"id": ..., "scores": {dim: calibrated}}`. Run
`ground_truth_gate.py --recompute-model-wa` on the result so the weighted average
and the gatekeeper come from the filter's own `config.yaml` on BOTH sides of the
comparison.

It exists so a threshold sweep costs seconds instead of ~30 minutes of CPU on the
serving box, which is only free between pipeline cycles.

Usage
-----
    PYTHONPATH=. python scripts/verification/parity_dump_to_gate_input.py \
        --dump datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl \
        --calibration filters/uplifting/v7/calibration.json \
        --out /tmp/uplifting_v7_gate_input.jsonl
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True, help="box_parity.py dump (first line is _meta)")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import numpy as np
    from filters.common.score_calibration import load_calibration, apply_calibration

    cal = load_calibration(args.calibration)
    if not cal:
        raise SystemExit(f"no calibration loaded from {args.calibration} -- refusing to emit "
                         "uncalibrated scores as gate input (_load_calibration fails silent, #98)")

    meta = None
    rows = []
    with open(args.dump, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            if "_meta" in o:
                meta = o
                continue
            rows.append(o)
    if meta is None:
        raise SystemExit("dump has no _meta line -- cannot know the dimension order")
    dims = meta["dims"]

    n = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for o in rows:
            raw = np.asarray([o["raw"][d] for d in dims], dtype=float)
            cs = apply_calibration(raw, cal, dims)
            scores = {d: max(0.0, min(10.0, float(v))) for v, d in zip(cs, dims)}
            out.write(json.dumps({"id": o["id"], "scores": scores}) + "\n")
            n += 1

    e = meta["_meta"]
    print(f"{n} rows -> {args.out}")
    print(f"source box: {e['host']} py {e['python']} torch {e['torch']} "
          f"transformers {e['transformers']} peft {e['peft']} device={meta.get('device')}")
    print("run the gate with --recompute-model-wa so weights + gatekeeper match the config")


if __name__ == "__main__":
    main()
