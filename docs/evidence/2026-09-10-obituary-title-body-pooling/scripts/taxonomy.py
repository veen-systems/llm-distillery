import json, pickle, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
OBIT=Path.home()/"llm-distillery/filters/common/obituary_detector"; OP=0.85
m=SentenceTransformer("paraphrase-multilingual-mpnet-base-v2",device="cuda"); m.max_seq_length=128
sc=pickle.load(open(OBIT/"v5/models/scaler.pkl","rb")); clf=pickle.load(open(OBIT/"v5/models/mlp_classifier.pkl","rb"))
rows=[json.loads(l) for l in open(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl",encoding="utf-8") if l.strip()]
pos=[r for r in rows if r["label"]=="positive"]
def s(t): return clf.predict_proba(sc.transform(np.asarray(m.encode(t,batch_size=64,show_progress_bar=False))))[:,1]
full=s([f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in pos])
tit =s([(r.get('title') or '').strip() for r in pos])
bod =s([(r.get('content') or '').strip() for r in pos])
fn=full<OP
print(f"positives {len(pos)}  false negatives at {OP}: {int(fn.sum())} (recall {1-fn.mean():.4f})\n")
A = fn & (tit>=OP)                       # strong title, dragged under
B = fn & (tit<OP) & (bod>=OP)            # weak title overrode a strong body
C = fn & (tit<OP) & (bod<OP)             # neither reads as obituary
print("MECHANISM TAXONOMY of the 77 misses (computed, not hand-labelled):")
for lab,msk,desc in (("A",A,"title alone PASSES, full text does not -> BODY DILUTION"),
                     ("B",B,"title fails, body alone PASSES        -> TITLE OVERRIDES BODY"),
                     ("C",C,"neither title nor body passes         -> no signal either way")):
    print(f"  {lab}: {int(msk.sum()):3d} ({100*msk.sum()/fn.sum():4.1f}% of misses)  {desc}")
print(f"\n  A: median title {np.median(tit[A]):.4f} -> median full {np.median(full[A]):.4f} "
      f"(median drop {np.median(tit[A]-full[A]):.4f}); median body-only {np.median(bod[A]):.4f}")
print(f"  Of the {int((tit>=OP).sum())} positives with a passing TITLE, "
      f"{int(A.sum())} ({100*A.sum()/(tit>=OP).sum():.1f}%) are dragged below {OP} by their body.")
print("\n  class A rows (strong title, diluted under):")
for i in np.where(A)[0][np.argsort(full[A])]:
    print(f"    title {tit[i]:.4f} -> full {full[i]:.4f} (body {bod[i]:.4f}) | {(pos[i].get('title') or '')[:70]}")
json.dump({"positives":len(pos),"fn":int(fn.sum()),"A_body_dilution":int(A.sum()),
           "B_title_overrides":int(B.sum()),"C_no_signal":int(C.sum()),
           "n_passing_title":int((tit>=OP).sum()),
           "pct_passing_titles_diluted_under":float(A.sum()/(tit>=OP).sum())},
          open(Path.home()/"taxonomy_results.json","w"),indent=1)
