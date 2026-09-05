"""Per-article throughput of every v8 scoring arm, by device, with REPEATS.

⛔ WHY THIS EXISTS RATHER THAN THE 2026-09-04 NUMBERS. The device timings quoted in
`EXP-019` (e5-small 3.74 GPU / 47.2 CPU, e5-large 26.79 GPU / 511.2 CPU, student 43.70 GPU,
~1455 CPU) were measured by a script that:

  - was cited as an artifact by NO registry entry;
  - wrote NO output file, so the figures survive only as prose in a markdown document;
  - recorded the host, device, batch size and load-exclusion only in its own docstring,
    never in the experiment's `population`;
  - ran ONCE per arm. A timing with n=1 has no spread, and this repo's own rule is that
    two numbers whose bands overlap are not distinguishable.

⚠️ AND THE e5-LARGE ARMS CANNOT BE REPRODUCED AT ALL. Those probes were trained during
EXP-018/019 and were never retained — the only `.pkl` on b650-gpu for this filter is the
shipped `embedding_probe_e5small.pkl`. So e5-large is measured here ENCODER-ONLY and is
labelled as such: it is not the same quantity as a full probe pass, though the head is a
small MLP over a pooled vector and the encoder dominates. Do not silently compare an
encoder-only figure with a full-probe one.

⛔⛔ ONE ARM PER PROCESS, AND THAT IS NOT TIDINESS. `EmbeddingStage` caches loaded models
in a class-level singleton keyed on the MODEL NAME ALONE (`_embedding_models[model_name]`,
`embedding_stage.py:213`), with no device in the key. So a second `EmbeddingStage(...,
device="cpu")` in the same process silently reuses the CUDA-resident model and the `device`
argument does nothing. The first version of this script ran GPU then CPU in one process and
reported **e5-small CPU at 2.37 ms/article against GPU's 2.34** — a CUDA measurement wearing
a CPU label, and the giveaway was only that the two agreed to within 1%. Each arm now runs
in its own interpreter (`--arm`), so the cache starts empty. llm-distillery#146.

⚠️ b650-gpu is NOT gpu-server. This box is a non-production RTX 3090 Ti. Ratios should
travel; absolute numbers should not be quoted as production. Production's own end-to-end
figure is 18.08 ms/article (`EXP-021`, gpu-server, 146,433 articles).

What is held constant: the same 660-row test split, the same batch size, model load
excluded via a warm-up pass, and the same process per arm.

    PYTHONPATH=. python benchmark_devices.py --out devices.json
"""

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")

SPLIT = Path("datasets/training/human_thriving_v8/test.jsonl")


def load_articles():
    if not SPLIT.is_file():
        raise SystemExit(f"{SPLIT} is missing — this must run on a box with the split "
                         f"(b650-gpu), not in a fresh clone.")
    rows = [json.loads(l) for l in open(SPLIT, encoding="utf-8") if l.strip()]
    if not rows:
        raise SystemExit(f"{SPLIT} is empty — a zero-row timing is not a fast one.")
    return rows


def timed(fn, n_rows, repeats):
    """Warm up once (excluded), then time `repeats` passes. Report the spread, because a
    single timing cannot be distinguished from a slow one."""
    fn()                                   # warm-up: model load, CUDA context, allocator
    per_article = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        per_article.append(1000 * (time.perf_counter() - t) / n_rows)
    return {
        "repeats": repeats,
        "ms_per_article_median": round(statistics.median(per_article), 3),
        "ms_per_article_min": round(min(per_article), 3),
        "ms_per_article_max": round(max(per_article), 3),
        "ms_per_article_all": [round(x, 3) for x in per_article],
        "spread_pct_of_median": round(
            100 * (max(per_article) - min(per_article)) / statistics.median(per_article), 2),
    }


def _where(arm):
    """Where did the model ACTUALLY end up? The `device` argument is a request, not a fact —
    a cache hit ignores it (see the docstring), so read it back off the loaded module."""
    import torch
    from filters.common.embedding_stage import EmbeddingStage
    seen = set()
    for m in EmbeddingStage._embedding_models.values():
        try:
            seen.add(str(next(m.parameters()).device))
        except Exception:
            seen.add("unknown")
    return sorted(seen) or ["no embedding model in this arm"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--gpu-repeats", type=int, default=5)
    ap.add_argument("--cpu-repeats", type=int, default=3)
    ap.add_argument("--student-cpu-rows", type=int, default=128,
                    help="the student on CPU is ~1.5 s/article; a full pass is ~16 min")
    ap.add_argument("--arm", required=True,
                    help="exactly one of: e5small-probe-gpu, e5small-probe-cpu, "
                         "e5large-encoder-gpu, e5large-encoder-cpu, student-gpu, "
                         "student-cpu. ONE PER PROCESS — see the docstring.")
    args = ap.parse_args()

    import torch
    arts = load_articles()
    n = len(arts)

    env = {
        "host": platform.node(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cpu_threads": torch.get_num_threads(),
        "batch_size": args.batch_size,
        "rows": n,
        "split": str(SPLIT),
        "note": "model load EXCLUDED via a warm-up pass; b650-gpu is NOT gpu-server",
    }
    print(json.dumps(env, indent=2))

    from filters.common.embedding_stage import EmbeddingStage
    from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer as C
    PROBE = "filters/human_thriving/v8/probe/embedding_probe_e5small.pkl"
    results = {}

    def probe_arm(device):
        st = EmbeddingStage(embedding_model_name="intfloat/multilingual-e5-small",
                            probe_path=PROBE, threshold=1.75,
                            dimension_weights=C.DIMENSION_WEIGHTS,
                            dimension_names=C.DIMENSION_NAMES, device=device)
        return lambda: st.screen_batch(arts, batch_size=args.batch_size)

    def encoder_arm(model_name, device):
        # ⚠️ ENCODER ONLY — the matching probe head was never retained (see the docstring).
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(model_name, device=device)
        texts = [f"query: {a.get('title','')} {a.get('content','')}"[:4000] for a in arts]
        return lambda: m.encode(texts, batch_size=args.batch_size,
                                show_progress_bar=False, convert_to_numpy=True)

    def student_arm(device, rows):
        from filters.human_thriving.v8.inference import HumanThrivingScorer
        sc = HumanThrivingScorer(device=device)
        sub = arts[:rows]
        return lambda: sc.score_batch(sub, batch_size=args.batch_size), len(sub)

    ARMS = {
        "e5small-probe-gpu":   ("e5-small probe, GPU", lambda: probe_arm("cuda"), n, args.gpu_repeats),
        "e5small-probe-cpu":   ("e5-small probe, CPU", lambda: probe_arm("cpu"), n, args.cpu_repeats),
        "e5large-encoder-gpu": ("e5-large encoder-only, GPU",
                                lambda: encoder_arm("intfloat/multilingual-e5-large", "cuda"),
                                n, args.gpu_repeats),
        "e5large-encoder-cpu": ("e5-large encoder-only, CPU",
                                lambda: encoder_arm("intfloat/multilingual-e5-large", "cpu"), n, 1),
    }
    STUDENT = {"student-gpu": ("student, GPU", "cuda", n, 3),
               "student-cpu": ("student, CPU", "cpu", args.student_cpu_rows, 1)}
    if args.arm not in ARMS and args.arm not in STUDENT:
        raise SystemExit(f"unknown --arm {args.arm!r}; choose one of "
                         f"{sorted(list(ARMS) + list(STUDENT))}")
    if args.arm.endswith("-gpu") and not torch.cuda.is_available():
        raise SystemExit(f"{args.arm} asks for CUDA and torch.cuda.is_available() is False "
                         f"— refusing rather than silently timing the CPU")

    if args.arm in ARMS:
        label, build, rows, reps = ARMS[args.arm]
        print(f">>> {label}  ({rows} rows, {reps} repeats)", flush=True)
        r = timed(build(), rows, reps)
        r["rows"] = rows
    else:
        label, device, rows, reps = STUDENT[args.arm]
        print(f">>> {label}  ({rows} rows, {reps} repeats)", flush=True)
        fn, actual = student_arm(device, rows)
        r = timed(fn, actual, reps)
        r["rows"] = actual
        if actual != n:
            r["caveat"] = f"measured over {actual} of {n} rows"

    # Prove the arm ran where it claims. A device label is an assertion like any other.
    r["device_verified"] = _where(args.arm)
    results[label] = r
    print(f"    median {r['ms_per_article_median']} ms/article  "
          f"[{r['ms_per_article_min']}, {r['ms_per_article_max']}]  "
          f"spread {r['spread_pct_of_median']}% of median")
    print(f"    device actually used: {r['device_verified']}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"env": env, "arms": results}, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
