"""Measure the EXISTING human_thriving v8 checkpoint (epoch 6) on val+test.

Reuses train.py's own FilterDataset/evaluate/compute_metrics so this is the same
program that trained, not a reimplementation. Read-only: loads the adapter, never
resaves it (old-key-format constraint).
"""
import json, sys, torch, yaml
from pathlib import Path
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from peft import PeftModel

sys.path.insert(0, str(Path.home() / "llm-distillery"))
from training.train import FilterDataset, evaluate
from filters.common.model_loading import load_base_model_for_seq_cls

FILTER = Path("filters/human_thriving/v8")
DATA = Path("datasets/training/human_thriving_v8")
cfg = yaml.safe_load(open(FILTER / "config.yaml"))
dims = list(cfg["scoring"]["dimensions"].keys())
weights = [cfg["scoring"]["dimensions"][d]["weight"] for d in dims]
meta = json.load(open(FILTER / "training_metadata.json"))
print(f"base={meta['model_name']}  dims={len(dims)}  weights={weights}  sum={sum(weights):.3f}")

tok = AutoTokenizer.from_pretrained(meta["model_name"])
base = load_base_model_for_seq_cls(meta["model_name"], num_labels=len(dims),
                                   problem_type="regression", torch_dtype=torch.float32)
import os
MODEL_DIR = os.environ.get("MODEL_DIR", "model")
print(f"MODEL_DIR={MODEL_DIR}")
model = PeftModel.from_pretrained(base, FILTER / MODEL_DIR)
dev = "cuda" if torch.cuda.is_available() else "cpu"
model.to(dev).eval()
print(f"device={dev}")

class Wrap(torch.nn.Module):
    def __init__(s, m): super().__init__(); s.m = m
    def forward(s, **kw): return s.m(**kw)
wrapped = Wrap(model)

for split in ("val", "test"):
    ds = FilterDataset(DATA / f"{split}.jsonl", tok, max_length=meta["max_length"],
                       prompt=None, use_head_tail=False)
    dl = DataLoader(ds, batch_size=8, shuffle=False)
    m = evaluate(wrapped, dl, dev, dims, weights)
    print(f"\n===== {split.upper()} (n={len(ds)}) =====")
    print(f"  MAE {m['mae']:.4f}   RMSE {m['rmse']:.4f}")
    for k in ("recall_at_10", "recall_at_20", "recall_at_50", "ndcg_at_10"):
        if k in m: print(f"  {k:14s} {m[k]:.3f}")

    # ADR-023: recall + specificity at the op-point, always with the positive rate.
    preds, labs = [], []
    with torch.no_grad():
        for b in DataLoader(ds, batch_size=8, shuffle=False):
            o = wrapped(input_ids=b["input_ids"].to(dev),
                        attention_mask=b["attention_mask"].to(dev),
                        labels=b["labels"].to(dev))
            preds.append(o.logits.cpu()); labs.append(b["labels"])
    P = torch.cat(preds); L = torch.cat(labs)
    w = torch.tensor(weights, dtype=P.dtype)
    pwa, twa = (P * w).sum(1), (L * w).sum(1)
    print(f"  pred WA: min {pwa.min():.2f} p50 {pwa.median():.2f} max {pwa.max():.2f}")
    print(f"  true WA: min {twa.min():.2f} p50 {twa.median():.2f} max {twa.max():.2f}")
    for thr in (4.0, 4.25, 4.5):
        tp = ((pwa >= thr) & (twa >= thr)).sum().item()
        fp = ((pwa >= thr) & (twa < thr)).sum().item()
        fn = ((pwa < thr) & (twa >= thr)).sum().item()
        tn = ((pwa < thr) & (twa < thr)).sum().item()
        pos = tp + fn; neg = tn + fp
        rec = tp / pos if pos else float("nan")
        spec = tn / neg if neg else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        print(f"  @{thr}: recall {rec:.3f}  specificity {spec:.4f}  precision {prec:.3f}"
              f"  | TP {tp} FP {fp} FN {fn} TN {tn} | positive rate {pos/len(ds)*100:.2f}% ({pos}/{len(ds)})")
