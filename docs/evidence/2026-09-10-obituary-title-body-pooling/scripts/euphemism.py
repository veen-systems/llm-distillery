#!/usr/bin/env python3
"""How much of the obituary detector's verdict is carried by the TITLE, and how big is
the euphemistic-title failure class in a real labelled population?

Motivated by ovr.news: "The quiet architect of a revolution in medicine" scores 0.0001
on v5. That is a frozen-embedding lexical-coverage weakness a shallow head cannot fix --
IF the class is common. Nobody has measured how common.

Deliberately uses NO hand-built death-word lexicon: an English/European keyword list
returns zero on Greek, Korean and Arabic BY CONSTRUCTION, which would manufacture a
"euphemistic" finding out of instrument coverage (CLAUDE.md: prove the instrument could
say yes). The contrast is defined by the model itself -- score(title alone) vs
score(title+content) -- and script is detected from the characters, not read off the
unreliable `language` field.

Population: the obituary heldout, scored with the SHIPPED v5 pickle (reproduces recorded
scores to max |d| 1.7e-06, verified 2026-09-10).
"""
import json, pickle, unicodedata, collections
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

OBIT = Path.home() / "llm-distillery/filters/common/obituary_detector"
OP = 0.85
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2", device="cuda")
model.max_seq_length = 128
sc = pickle.load(open(OBIT / "v5/models/scaler.pkl", "rb"))
clf = pickle.load(open(OBIT / "v5/models/mlp_classifier.pkl", "rb"))

def script_of(ch):
    try: n = unicodedata.name(ch)
    except ValueError: return None
    for s in ("LATIN","GREEK","HANGUL","CJK","CYRILLIC","ARABIC","HIRAGANA","KATAKANA",
              "HEBREW","DEVANAGARI","ARMENIAN"):
        if n.startswith(s): return s
    return None

def dom_script(t):
    c = collections.Counter(x for x in (script_of(ch) for ch in t) if x)
    return c.most_common(1)[0][0] if c else "NONE"

rows = [json.loads(l) for l in open(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl",
                                    encoding="utf-8") if l.strip()]
def score(texts):
    X = np.asarray(model.encode(texts, batch_size=64, show_progress_bar=False))
    return clf.predict_proba(sc.transform(X))[:, 1]

full  = score([f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in rows])
title = score([(r.get('title') or '').strip() for r in rows])
body  = score([(r.get('content') or '').strip() for r in rows])
y = np.array([1 if r["label"] == "positive" else 0 for r in rows])
shipped = np.array([r["v5_score"] for r in rows])
print(f"control: full-text rescore vs recorded v5_score  max|d|={np.abs(full-shipped).max():.2e}")
print(f"heldout n={len(rows)}  positives={int(y.sum())}  negatives={int((1-y).sum())}\n")

pos = y == 1
print("=== Q1. Is the verdict carried by the TITLE? (positives only, n=%d) ===" % pos.sum())
print(f"  corr(title-only score, full score) = {np.corrcoef(title[pos], full[pos])[0,1]:.4f}")
print(f"  corr(body-only  score, full score) = {np.corrcoef(body[pos],  full[pos])[0,1]:.4f}")
print(f"  median |full - title_only| = {np.median(np.abs(full[pos]-title[pos])):.4f}")
print(f"  median |full - body_only|  = {np.median(np.abs(full[pos]-body[pos])):.4f}")
hi = pos & (title >= OP); lo = pos & (title < 0.15)
print(f"\n  positives whose TITLE ALONE scores >= {OP}: n={hi.sum():3d} -> "
      f"{100*(full[hi]>=OP).mean():.1f}% pass on full text")
print(f"  positives whose TITLE ALONE scores <  0.15: n={lo.sum():3d} -> "
      f"{100*(full[lo]>=OP).mean():.1f}% pass on full text")

print(f"\n=== Q2. How big is the failure class? (v5 false negatives at {OP}) ===")
fn = pos & (full < OP)
print(f"  positives {int(pos.sum())}, false negatives {int(fn.sum())} "
      f"({100*fn.sum()/pos.sum():.1f}% of positives)  -> recall {1-fn.sum()/pos.sum():.4f}")
print(f"  of those {int(fn.sum())} FNs, title-alone score < 0.15: "
      f"{int((fn & (title<0.15)).sum())} ({100*(title[fn]<0.15).mean():.1f}%)")
print(f"  of those {int(fn.sum())} FNs, BODY-alone score >= {OP}: "
      f"{int((fn & (body>=OP)).sum())} ({100*(body[fn]>=OP).mean():.1f}%)"
      "   <- signal present in the body but lost")
print(f"  median title-only score among FNs: {np.median(title[fn]):.4f}")
print(f"  median title-only score among TPs: {np.median(title[pos & (full>=OP)]):.4f}")

print("\n=== Q3. Script breakdown of the false negatives (detected, not tagged) ===")
scripts = np.array([dom_script((r.get('title') or '') + ' ' + (r.get('content') or '')) for r in rows])
print(f"  {'script':<12}{'positives':>10}{'FNs':>6}{'FN rate':>10}")
for s in sorted(set(scripts[pos])):
    m = pos & (scripts == s)
    if m.sum() == 0: continue
    print(f"  {s:<12}{int(m.sum()):>10}{int((m & fn).sum()):>6}{100*(fn[m]).mean():>9.1f}%")

print("\n=== Q4. The 12 worst-missed positives (lowest full score) ===")
order = np.argsort(np.where(pos, full, 9))[:12]
for i in order:
    print(f"  full {full[i]:.4f} | title-only {title[i]:.4f} | body-only {body[i]:.4f} | "
          f"{scripts[i][:6]:<6} | {(rows[i].get('title') or '')[:78]}")

json.dump({"n": len(rows), "positives": int(pos.sum()), "fn_at_op": int(fn.sum()),
           "op": OP,
           "corr_title_full": float(np.corrcoef(title[pos], full[pos])[0,1]),
           "corr_body_full": float(np.corrcoef(body[pos], full[pos])[0,1]),
           "fn_title_below_0.15": int((fn & (title<0.15)).sum()),
           "fn_body_above_op": int((fn & (body>=OP)).sum()),
           "pass_rate_title_hi": float((full[hi]>=OP).mean()),
           "pass_rate_title_lo": float((full[lo]>=OP).mean()),
           "n_title_hi": int(hi.sum()), "n_title_lo": int(lo.sum()),
           "by_script": {s: {"positives": int((pos&(scripts==s)).sum()),
                             "fns": int((pos&(scripts==s)&fn).sum())}
                         for s in sorted(set(scripts[pos]))}},
          open(Path.home()/"euphemism_results.json","w"), indent=1)
print("\nwrote ~/euphemism_results.json")
