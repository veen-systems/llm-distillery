"""If class A is a pooling failure, scoring the title SEPARATELY and taking the max should
recover it. What does that cost in specificity? (ADR-023: specificity is the budget.)
Evaluated on the whole heldout, both classes, at the live 0.85."""
import json, pickle, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
OBIT=Path.home()/"llm-distillery/filters/common/obituary_detector"; OP=0.85
m=SentenceTransformer("paraphrase-multilingual-mpnet-base-v2",device="cuda"); m.max_seq_length=128
sc=pickle.load(open(OBIT/"v5/models/scaler.pkl","rb")); clf=pickle.load(open(OBIT/"v5/models/mlp_classifier.pkl","rb"))
rows=[json.loads(l) for l in open(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl",encoding="utf-8") if l.strip()]
def s(t): return clf.predict_proba(sc.transform(np.asarray(m.encode(t,batch_size=64,show_progress_bar=False))))[:,1]
full=s([f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in rows])
tit =s([(r.get('title') or '').strip() for r in rows])
y=np.array([1 if r["label"]=="positive" else 0 for r in rows])
def rep(name,p,th):
    pred=p>=th; tp=int((pred&(y==1)).sum()); fp=int((pred&(y==0)).sum())
    fn=int((~pred&(y==1)).sum()); tn=int((~pred&(y==0)).sum())
    print(f"  {name:<34} recall {tp/(tp+fn):.4f}  spec {tn/(tn+fp):.4f}  prec {tp/(tp+fp):.4f}"
          f"   (tp {tp} fp {fp} fn {fn})")
    return tp/(tp+fn), tn/(tn+fp), fp
print(f"heldout n={len(rows)} positives={int(y.sum())} negatives={int((1-y).sum())}, threshold {OP}\n")
r0,s0,f0 = rep("current: full text",            full, OP)
r1,s1,f1 = rep("max(title, full)",              np.maximum(tit,full), OP)
print()
for t in (0.90,0.95,0.99):
    rep(f"max(title@{t}, full@{OP})", np.maximum(np.where(tit>=t,tit,0),full), OP)
print(f"\n  delta vs current for plain max(): recall {r1-r0:+.4f}, specificity {s1-s0:+.4f} "
      f"({f1-f0:+d} false positives on {int((1-y).sum())} negatives)")
