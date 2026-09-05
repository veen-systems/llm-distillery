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
`embedding_stage.py:112`, read back at `:214`), with no device in the key. So a second `EmbeddingStage(...,
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

⚠️ `--arm` is REQUIRED and there is no all-arms mode, by construction: see the cache note
above. The merge step is part of the command, not a manual tidy-up — a hand-merged summary
is a file no command produces.

    D=docs/evidence/2026-09-05-scorer-device-throughput
    for A in e5small-probe-gpu e5small-probe-cpu e5large-encoder-gpu student-gpu; do
        PYTHONPATH=. HF_HUB_OFFLINE=1 venv/bin/python $D/benchmark_devices.py \
            --arm $A --out $D/$A.json
    done
    python $D/benchmark_devices.py --merge $D --out $D/devices.json
"""

# design-weights: NOT APPLICABLE. The split is a fixed WORKLOAD for timing, not a
# population to estimate from; every number published is ms/article for a model on a
# device. ⚠️ It would matter if a timing were broken down by a row property the draw
# stratifies on (score band, script, class A); it is not.

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
    out = fn()                             # warm-up: model load, CUDA context, allocator
    # Every arm here ends in a device-to-host copy (`convert_to_numpy=True`, `.cpu().numpy()`),
    # which synchronises implicitly, so no explicit `torch.cuda.synchronize()` is needed. That
    # is a property of the ARMS, not of this function — an arm returning a live CUDA tensor
    # would time kernel launches only and read 10-100x too fast, silently. So check it.
    try:
        import torch
        if torch.is_tensor(out) and out.is_cuda:
            raise SystemExit("this arm returned a live CUDA tensor, so the timing below would "
                             "measure kernel launches rather than work. Add a .cpu() to it.")
    except ImportError:
        pass
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


# Every model an arm constructs registers here, so the device can be read back off the OBJECT
# rather than trusted from the argument that was passed. The first version of this script read
# back only models in EmbeddingStage's cache, which left the encoder-only and student arms
# reporting "no embedding model in this arm" — the same blind spot that produced the corrupted
# CPU reading, disclosed but not closed.
_OBJECTS: list = []


def _where():
    """Where did the models ACTUALLY end up? `device` is a request, not a fact — a cache hit
    ignores it (see the docstring). Reads every registered model plus EmbeddingStage's cache."""
    from filters.common.embedding_stage import EmbeddingStage
    seen = set()
    cands = list(_OBJECTS) + list(EmbeddingStage._embedding_models.values())
    for m in cands:
        try:
            seen.add(str(next(m.parameters()).device))
        except Exception:
            seen.add("unknown")
    if not seen:
        # An arm that registered nothing has NOT been verified; say so rather than pass.
        return ["UNVERIFIED — no model registered by this arm"]
    return sorted(seen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--merge", type=Path, default=None,
                    help="combine the per-arm JSONs in this directory into --out and exit. "
                         "Exists so the summary file is TOOL OUTPUT rather than a hand-merge "
                         "nothing can reproduce.")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--gpu-repeats", type=int, default=5)
    ap.add_argument("--cpu-repeats", type=int, default=3)
    ap.add_argument("--large-probe", type=Path,
                    default=Path("rescued_probes/probe_e5large.pkl"),
                    help="the EXP-018/019 e5-large probe head, rescued from /tmp on b650")
    ap.add_argument("--student-cpu-rows", type=int, default=128,
                    help="the student on CPU is ~1.5 s/article; a full pass is ~16 min")
    ap.add_argument("--arm", default=None,
                    help="exactly one of: e5small-probe-gpu, e5small-probe-cpu, "
                         "e5large-encoder-gpu, e5large-encoder-cpu, student-gpu, "
                         "student-cpu. ONE PER PROCESS — see the docstring.")
    args = ap.parse_args()

    if args.merge:
        merged = {"env": None, "arms": {}}
        files = sorted(f for f in args.merge.glob("*.json")
                       if f.resolve() != args.out.resolve())
        if not files:
            raise SystemExit(f"no per-arm JSONs in {args.merge} — nothing to merge, which "
                             f"is not the same as one empty result")
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            if "arms" not in d or "env" not in d:
                continue                      # not one of ours; skip rather than corrupt
            if merged["env"] is None:
                merged["env"] = d["env"]
            elif merged["env"] != d["env"]:
                # Merging arms measured under different environments would manufacture a
                # comparison across two populations — the defect this directory is about.
                raise SystemExit(f"{f.name} was measured under a DIFFERENT environment than "
                                 f"the others; refusing to merge them into one record")
            for k, v in d["arms"].items():
                if k in merged["arms"] and merged["arms"][k] != v:
                    raise SystemExit(f"two different results for arm {k!r}; refusing to "
                                     f"silently keep one")
                merged["arms"][k] = v
        if not merged["arms"]:
            raise SystemExit(f"{len(files)} JSON file(s) in {args.merge}, none of them a "
                             f"benchmark result")
        merged["env"]["one_arm_per_process"] = True
        merged["env"]["merged_from"] = [f.name for f in files]
        args.out.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        print(f"merged {len(merged['arms'])} arm(s) from {len(files)} file(s) -> {args.out}")
        return
    if not args.arm:
        raise SystemExit("--arm is required (or --merge). ONE ARM PER PROCESS — see the "
                         "module docstring for why there is no all-arms mode.")

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
        return lambda: st.screen_batch(arts, batch_size=args.batch_size)   # cache covers it

    def encoder_arm(model_name, device):
        """⚠️ ENCODER ONLY — for comparison against the full-probe arm, never as a stand-in.

        ⛔ The first version built `f"query: {title} {content}"[:4000]`, which no consumer
        feeds the model: `EmbeddingStage._prepare_text` uses `f"{title}\n\n{content}"` with NO
        truncation and no `query:` prefix. 27.7% of the split exceeds 4000 chars (median 2463,
        p90 6527, max 76768) and tokenisation runs on the whole string before the 512-token
        cap, so the cut removed real work — measured 20.5 ms/article truncated against 34.9
        untruncated, a 1.70x understatement. Use the consumer's own text.
        """
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(model_name, device=device)
        _OBJECTS.append(m)
        texts = [EmbeddingStage._prepare_text(a) for a in arts]
        return lambda: m.encode(texts, batch_size=args.batch_size,
                                show_progress_bar=False, convert_to_numpy=True)

    def large_probe_arm(device):
        """The FULL e5-large probe. ⛔ Its head was on b650 the whole time — `/tmp/probe_e5large.pkl`,
        now `~/llm-distillery/rescued_probes/` — and the first version of this file said it was
        "never retained" on the strength of a `find` rooted at `filters/**`, a location that
        could not have produced a positive. Eleven probes were in that `/tmp`, including both
        EXP-019 regression heads and the seed-42/seed-7 pair."""
        st = EmbeddingStage(embedding_model_name="intfloat/multilingual-e5-large",
                            probe_path=args.large_probe, threshold=1.75,
                            dimension_weights=C.DIMENSION_WEIGHTS,
                            dimension_names=C.DIMENSION_NAMES, device=device)
        return lambda: st.screen_batch(arts, batch_size=args.batch_size)

    def student_arm(device, rows):
        from filters.human_thriving.v8.inference import HumanThrivingScorer
        sc = HumanThrivingScorer(device=device)
        _OBJECTS.append(sc.model)
        sub = arts[:rows]
        return lambda: sc.score_batch(sub, batch_size=args.batch_size), len(sub)

    ARMS = {
        "e5small-probe-gpu":   ("e5-small probe, GPU", lambda: probe_arm("cuda"), n, args.gpu_repeats),
        "e5small-probe-cpu":   ("e5-small probe, CPU", lambda: probe_arm("cpu"), n, args.cpu_repeats),
        "e5large-encoder-gpu": ("e5-large encoder-only, GPU",
                                lambda: encoder_arm("intfloat/multilingual-e5-large", "cuda"),
                                n, args.gpu_repeats),
        "e5large-encoder-cpu": ("e5-large encoder-only, CPU",
                                lambda: encoder_arm("intfloat/multilingual-e5-large", "cpu"),
                                n, args.cpu_repeats),
        "e5large-probe-gpu":   ("e5-large probe, GPU", lambda: large_probe_arm("cuda"),
                                n, args.gpu_repeats),
        "e5large-probe-cpu":   ("e5-large probe, CPU", lambda: large_probe_arm("cpu"),
                                n, args.cpu_repeats),
    }
    STUDENT = {"student-gpu": ("student, GPU", "cuda", n, args.gpu_repeats),
               "student-cpu": ("student, CPU", "cpu", args.student_cpu_rows,
                               args.cpu_repeats)}
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

    # ⛔ RECORDING THE DEVICE IS NOT CHECKING IT. The previous version wrote `device_verified`
    # into the JSON and never compared it to what the arm asked for, so a future all-arms
    # wrapper would re-create #146 exactly: the CPU arm would record ["cuda:0"], print a
    # number, and exit 0. A field that is written and never asserted is a report, not a guard.
    r["device_verified"] = _where()
    expected = "cuda" if args.arm.endswith("-gpu") else "cpu"
    bad = [d for d in r["device_verified"] if not d.startswith(expected)]
    if bad:
        raise SystemExit(
            f"{args.arm} asked for {expected!r} and the loaded model(s) report "
            f"{r['device_verified']}. This is llm-distillery#146 happening: the device "
            f"argument was a request and something ignored it. Refusing to publish a timing "
            f"labelled with a device it did not run on.")
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
