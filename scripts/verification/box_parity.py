#!/usr/bin/env python3
"""Cross-box parity harness for the Gemma-3-1B student path.

WHY THIS EXISTS
---------------
`memory/b650-gpu.md` told sessions to "re-run the parity harness before trusting
any new box/version pair" — and no such harness existed. The e5 probe had been
checked ad hoc (max |Δ| 4.2e-6, clean); the student had never been checked at
all, while `filters/uplifting/v7/ground_truth_gate.json` carried an accuracy
record measured on a box that is NOT the serving one.

First run, 2026-08-09, uplifting v7 over its 660-row held-out split:
gpu-server serving venv vs b650 — **0 verdict flips at the 4.0 op-point and an
identical confusion matrix**, but only 2.3% of rows bit-identical and a max
calibrated |Δ| of 0.2008, which EXCEEDS the #95 |0.16| noise floor. Three rows
flip at 4.5.

⛔ CORRECTED 2026-08-29: that 0.2008 is NOT a box term, and this docstring
presented it as one. The stacks were unmatched in that run. The 2026-08-10
four-run decomposition isolates each variable: HOST 0.0000 (660/660
bit-identical), library STACK 0.2008, DEVICE CPU->CUDA 0.1956. Match the pins
and the device and the box is free; the thing that is cleared "at a threshold,
never in general" is a (stack, device, threshold) triple.

⚠️ THIS SCRIPT TAKES NO THRESHOLD. It only dumps predictions. The threshold
lives on diff_box_parity.py (--threshold / --alt-threshold), which is what
actually reports flips. Two docs told readers to "re-run box_parity.py at your
threshold"; they now name diff_box_parity.py.

WHAT IT CONTROLS FOR
--------------------
Everything except the interpreter. Before trusting a comparison, verify by md5
that BOTH boxes have identical: adapter weights + tokenizer (`*/model/*`),
`inference.py`, `base_scorer.py`, `config.yaml`, `calibration.json`,
`filters/common/{model_loading,filter_base_scorer,text_preprocessing}.py`, and
the data split. Then copy THIS repo's `scripts/calibration/fit_calibration.py`
to both boxes and pass it via --fit-calibration, so the inference code is
provably the same object on both sides rather than "the same file, probably".

CPU-only on purpose: the point is to isolate the library stack, and on
gpu-server the GPU is claimed by ollama between pipeline cycles
(`nexusmind-scorer.service` has `Conflicts=ollama.service`), so a GPU run there
would either fight the service or require stopping it. NOTE this means the
result is stack parity ON CPU — CPU-vs-CUDA on the student is a separate,
still-unmeasured axis.

USAGE
-----
    # production side (read the interpreter off `systemctl cat nexusmind-scorer`,
    # never `which python3` — the system python is a different stack entirely)
    ssh gpu-server 'CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 \
        PYTHONPATH=/home/hcl/NexusMind \
        /home/hcl/gpu-server/nexusmind-scorer/venv/bin/python /tmp/parity/box_parity.py \
          --fit-calibration /tmp/parity/fit_calibration.py \
          --filter /home/hcl/NexusMind/filters/uplifting/v7 \
          --data /home/hcl/llm-distillery/datasets/training/uplifting_v7/test.jsonl \
          --out /tmp/parity/preds-gpuserver.jsonl'

    # then diff with scripts/verification/diff_box_parity.py

Long runs: launch with `setsid nohup ... </dev/null >log 2>&1 &`. Do NOT judge
progress from the log — this script's stderr buffers when redirected, so the
"Inference progress" line goes stale while work continues. Check the CPU-time
delta instead: `awk '{print $14+$15}' /proc/<pid>/stat` twice, 15 s apart.
"""

import argparse
import importlib.util
import json
import platform
import socket
import sys
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def env_report() -> dict:
    import torch

    out = {
        "host": socket.gethostname(),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }
    for mod in ("transformers", "peft", "sentence_transformers", "sklearn", "numpy"):
        try:
            out[mod] = importlib.import_module(mod).__version__
        except Exception:
            out[mod] = "MISSING"
    return out


def main():
    ap = argparse.ArgumentParser(description="cross-box parity dump for a filter's student model")
    ap.add_argument("--fit-calibration", required=True,
                    help="path to a copy of scripts/calibration/fit_calibration.py "
                         "(md5 it on both boxes first)")
    ap.add_argument("--filter", required=True, help="filter package dir, e.g. .../filters/uplifting/v7")
    ap.add_argument("--data", required=True, help="JSONL split with id/title/content")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch-size", type=int, default=16,
                    help="must match on both boxes; #95 skew is batch-composition sensitive")
    ap.add_argument("--limit", type=int, default=None, help="smoke-test a prefix")
    args = ap.parse_args()

    fc = load_module(Path(args.fit_calibration), "_parity_fit_calibration")

    filter_dir = Path(args.filter)
    config = fc.load_filter_config(filter_dir)
    dims = fc.get_dimension_names(config)
    # uplifting v7 and friends carry the weight inside each dimension, not in a
    # separate scoring.weights map — support both shapes.
    weights = config.get("scoring", {}).get("weights", {}) or {
        d: v.get("weight", 0)
        for d, v in config.get("scoring", {}).get("dimensions", {}).items()
    }

    articles = fc.load_data(Path(args.data))
    if args.limit:
        articles = articles[: args.limit]

    env = env_report()
    print(json.dumps(env, indent=2), flush=True)
    print(f"articles={len(articles)} dims={dims} batch_size={args.batch_size}", flush=True)

    scorer = fc.load_scorer(filter_dir)
    print(f"device={scorer.device}", flush=True)

    raw = fc.run_inference_raw(scorer, articles, dims, batch_size=args.batch_size)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": env, "dims": dims, "weights": weights,
                            "n": len(articles), "batch_size": args.batch_size,
                            "device": str(scorer.device)}) + "\n")
        for i, a in enumerate(articles):
            row = {d: float(raw[i, j]) for j, d in enumerate(dims)}
            f.write(json.dumps({
                "idx": i,
                "id": a.get("id"),
                "raw": row,
                "wavg": sum(row[d] * float(weights.get(d, 0)) for d in dims),
            }) + "\n")
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
