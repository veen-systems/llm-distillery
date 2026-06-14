#!/usr/bin/env python3
"""
Phase 2 prep — split the broad-rule DeepSeek-labeled corpus into a TRAIN split and
a disjoint HELD-OUT split (build-plan Phase 2).

The held-out split is graded later by an independent 4-lab panel (gemini + 3 Ollama),
NOT by the DeepSeek oracle — so block precision is measured against ground truth that
never saw the training labels (no circularity; the lesson-2 method).

Stable, deterministic split by a hash of the id (no RNG, resume-safe), stratified so
positives and negatives are split at the same held-out fraction. borderline -> negative
(matches the trainer's label==positive keying).

Usage:
    python build_train_split.py \
        --in ../validation/artifacts/deepseek_labeled_corpus.jsonl \
        --train-out ../validation/artifacts/train_split_corpus.jsonl \
        --heldout-out ../validation/artifacts/heldout_corpus.jsonl \
        --heldout-frac 0.12
"""
import argparse, json, hashlib
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--train-out", required=True)
ap.add_argument("--heldout-out", required=True)
ap.add_argument("--heldout-frac", type=float, default=0.12)
args = ap.parse_args()

rows = [json.loads(l) for l in open(args.inp, encoding="utf-8") if l.strip()]

def bucket(cid):
    # stable 0..9999 from id; held-out if below frac*10000
    h = int(hashlib.sha1(cid.encode()).hexdigest()[:8], 16) % 10000
    return h < args.heldout_frac * 10000

train, heldout = [], []
for r in rows:
    # normalize label (trainer keys on label=="positive")
    r["label"] = "positive" if r.get("deepseek_verdict") == "obituary" else "negative"
    (heldout if bucket(r["id"]) else train).append(r)

def stats(name, rs):
    c = Counter(r["label"] for r in rs)
    print(f"{name}: {len(rs)}  positive={c['positive']}  negative={c['negative']}  "
          f"({100*c['positive']/max(len(rs),1):.1f}% pos)")

with open(args.train_out, "w", encoding="utf-8") as f:
    for r in train:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(args.heldout_out, "w", encoding="utf-8") as f:
    for r in heldout:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"total {len(rows)}")
stats("train  ", train)
stats("heldout", heldout)
print(f"-> {args.train_out}")
print(f"-> {args.heldout_out}")
