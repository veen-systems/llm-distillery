import json, pickle, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
OBIT=Path.home()/"llm-distillery/filters/common/obituary_detector"
m=SentenceTransformer("paraphrase-multilingual-mpnet-base-v2",device="cuda"); m.max_seq_length=128
sc=pickle.load(open(OBIT/"v5/models/scaler.pkl","rb")); clf=pickle.load(open(OBIT/"v5/models/mlp_classifier.pkl","rb"))
rows=[json.loads(l) for l in open(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl",encoding="utf-8") if l.strip()]
pos=[r for r in rows if r["label"]=="positive"]
def s(t): return clf.predict_proba(sc.transform(np.asarray(m.encode(t,batch_size=64,show_progress_bar=False))))[:,1]
full=s([f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in pos])
body=s([(r.get('content') or '').strip() for r in pos])
fn=[(full[i],body[i],pos[i]) for i in range(len(pos)) if full[i]<0.85]
fn.sort(key=lambda x:x[0])
print(f"{len(fn)} false negatives at 0.85\n")
print("--- body-only ALSO below 0.85 (title and body both read as non-obit) ---")
for f,b,r in fn:
    if b<0.85: print(f"  {f:.4f}/{b:.4f} | {(r.get('title') or '')[:95]}")
print("\n--- body-only >= 0.85 (BODY reads as obituary, title overrode it) ---")
for f,b,r in fn:
    if b>=0.85: print(f"  {f:.4f}/{b:.4f} | {(r.get('title') or '')[:95]}")
