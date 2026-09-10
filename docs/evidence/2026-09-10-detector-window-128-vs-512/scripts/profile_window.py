#!/usr/bin/env python3
"""Performance + cost profile of the detector embedding path at 128 vs 512 tokens.

Measures the REAL production shape: SentenceTransformer.encode on
paraphrase-multilingual-mpnet-base-v2, then StandardScaler + MLP predict_proba.
Reports throughput and latency on whichever device is given, plus GPU power draw
where readable, and extrapolates to a per-1,000-article cost.

Texts come from the violence_promotion labelled corpus (real articles, real length
distribution) -- NOT synthetic strings, which would understate the 512 arm because
short texts never reach the cap.
"""
import json, pickle, time, subprocess, sys, statistics as st
from pathlib import Path
import numpy as np, torch
from sentence_transformers import SentenceTransformer

DEVICE = sys.argv[1] if len(sys.argv) > 1 else "cuda"
ROOT = Path.home() / "llm-distillery"
VP = ROOT / "filters/common/violence_promotion/training/training_scored.jsonl"
OBIT = ROOT / "filters/common/obituary_detector"
N_THROUGHPUT = 512          # articles per throughput run
N_LATENCY = 120             # single-article calls
WINDOWS = [128, 512]
BATCHES = [1, 8, 32, 64, 128]

rows = [json.loads(l) for l in open(VP, encoding="utf-8") if l.strip()]
texts = [f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in rows]
texts = [t for t in texts if t][:max(N_THROUGHPUT, N_LATENCY)]

def gpu_power():
    try:
        o = subprocess.run(["nvidia-smi","--query-gpu=power.draw,memory.used",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
        p, m = o.stdout.strip().split(",")
        return float(p), float(m)
    except Exception:
        return None, None

print(f"device={DEVICE} torch={torch.__version__} cuda_avail={torch.cuda.is_available()}")
if DEVICE == "cuda":
    print("gpu:", torch.cuda.get_device_name(0))
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2", device=DEVICE)
sc = pickle.load(open(OBIT/"v5/models/scaler.pkl","rb"))
clf = pickle.load(open(OBIT/"v5/models/mlp_classifier.pkl","rb"))

def sync():
    if DEVICE == "cuda": torch.cuda.synchronize()

out = {"device": DEVICE, "n_throughput": len(texts[:N_THROUGHPUT]), "results": {}}
if DEVICE == "cuda":
    out["gpu_name"] = torch.cuda.get_device_name(0)

for W in WINDOWS:
    model.max_seq_length = W
    out["results"][W] = {}
    # warmup
    model.encode(texts[:64], batch_size=32, show_progress_bar=False); sync()

    for bs in BATCHES:
        sub = texts[:N_THROUGHPUT]
        p0, m0 = gpu_power()
        sync(); t0 = time.perf_counter()
        X = model.encode(sub, batch_size=bs, show_progress_bar=False)
        sync(); dt = time.perf_counter() - t0
        p1, m1 = gpu_power()
        # head cost
        t1 = time.perf_counter()
        clf.predict_proba(sc.transform(np.asarray(X)))[:,1]
        head_dt = time.perf_counter() - t1
        rec = {"rows_per_s": len(sub)/dt, "ms_per_row": 1000*dt/len(sub),
               "total_s": dt, "head_ms_per_row": 1000*head_dt/len(sub)}
        if p1 is not None:
            rec["gpu_power_w"] = max(p0 or 0, p1); rec["gpu_mem_mb"] = max(m0 or 0, m1)
        out["results"][W][f"batch_{bs}"] = rec
        print(f"  W={W:3d} bs={bs:3d}: {rec['rows_per_s']:8.1f} rows/s  "
              f"{rec['ms_per_row']:7.2f} ms/row  head {rec['head_ms_per_row']:.4f} ms/row"
              + (f"  {rec.get('gpu_power_w',0):.0f}W {rec.get('gpu_mem_mb',0):.0f}MiB" if p1 else ""), flush=True)

    # single-article latency (the per-article inference path)
    lat = []
    for t in texts[:N_LATENCY]:
        sync(); t0 = time.perf_counter()
        e = model.encode([t], show_progress_bar=False)
        clf.predict_proba(sc.transform(np.asarray(e)))[:,1]
        sync(); lat.append(1000*(time.perf_counter()-t0))
    lat_s = sorted(lat)
    out["results"][W]["latency_single_ms"] = {
        "p50": lat_s[len(lat_s)//2], "p95": lat_s[int(0.95*len(lat_s))],
        "mean": st.mean(lat_s), "max": lat_s[-1], "n": len(lat_s)}
    print(f"  W={W:3d} single-article latency: p50 {lat_s[len(lat_s)//2]:.2f} ms  "
          f"p95 {lat_s[int(0.95*len(lat_s))]:.2f} ms  max {lat_s[-1]:.2f} ms", flush=True)

# ratio summary at the best batch size
for W in WINDOWS:
    best = max((v["rows_per_s"], k) for k,v in out["results"][W].items() if k.startswith("batch_"))
    out["results"][W]["best"] = {"batch": best[1], "rows_per_s": best[0]}
r128 = out["results"][128]["best"]["rows_per_s"]; r512 = out["results"][512]["best"]["rows_per_s"]
out["slowdown_512_vs_128"] = r128/r512
print(f"\n  best throughput: 128 -> {r128:.0f} rows/s, 512 -> {r512:.0f} rows/s, "
      f"slowdown {r128/r512:.2f}x")
for n in (1000, 10000, 100000):
    print(f"  {n:>7,} articles: 128 = {n/r128:8.1f}s   512 = {n/r512:8.1f}s   "
          f"delta = {n/r512 - n/r128:8.1f}s")
out["extrapolation_s"] = {str(n): {"w128": n/r128, "w512": n/r512} for n in (1000,10000,100000)}

p = Path.home()/f"profile_window_{DEVICE}.json"
json.dump(out, open(p,"w"), indent=1); print("wrote", p)
