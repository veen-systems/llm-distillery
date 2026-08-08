"""Corroboration step 4: does a cross-lingual extractor give a real fingerprint?

Baseline being tested against (recorded, spaCy en_core_web_sm):
  median 2 entities/article -> unrelated articles reach entity_jaccard 1.000
  on Latin-script token collision; ej learned NEGATIVE in 7 of 8 LOCO folds.
"""
import json, statistics as st, itertools, random, sys, time
import torch
from transformers import pipeline

MODEL = "xlm-roberta-large-finetuned-conll03-english"
rows = [json.loads(l) for l in open("/tmp/ner_sample.jsonl") if l.strip()]
print(f"{len(rows)} articles; loading {MODEL} ...", flush=True)
t0 = time.time()
ner = pipeline("token-classification", model=MODEL, aggregation_strategy="simple",
               device=0 if torch.cuda.is_available() else -1)
print(f"loaded in {time.time()-t0:.0f}s on {'cuda' if torch.cuda.is_available() else 'cpu'}", flush=True)

ents_by_id, lang_of = {}, {}
t0 = time.time()
for i, r in enumerate(rows):
    text = (r["title"] + ". " + r["content"])[:5000]   # same 5000-char budget as V1
    try:
        out = ner(text)
    except Exception as e:
        print(f"  !! {r['id']}: {type(e).__name__}", flush=True); out = []
    ents = {e["word"].strip() for e in out if e.get("word") and len(e["word"].strip()) > 1}
    ents_by_id[r["id"]] = ents
    lang_of[r["id"]] = r["lang"]
    if (i+1) % 60 == 0:
        print(f"  {i+1}/{len(rows)}  ({time.time()-t0:.0f}s)", flush=True)

counts = {k: len(v) for k, v in ents_by_id.items()}
allc = sorted(counts.values())
print("\n=== ENTITIES PER ARTICLE ===")
print(f"overall: median={st.median(allc)}  mean={st.mean(allc):.1f}  "
      f"p10={allc[len(allc)//10]}  p90={allc[9*len(allc)//10]}  min={allc[0]} max={allc[-1]}")
print(f"{'lang':6s} {'n':>4s} {'median':>7s} {'mean':>6s} {'% with <3':>10s}")
for lang in sorted(set(lang_of.values())):
    c = sorted(counts[i] for i in counts if lang_of[i] == lang)
    lo = 100.0*sum(1 for x in c if x < 3)/len(c)
    print(f"{lang:6s} {len(c):4d} {st.median(c):7.1f} {st.mean(c):6.1f} {lo:9.1f}%")
print("\n  spaCy en_core_web_sm baseline (recorded): median 2 entities/article")

def jac(a, b):
    if not a and not b: return 1.0          # the '' == '' trap, kept explicit
    if not a or not b:  return 0.0
    return len(a & b) / len(a | b)

ids = list(ents_by_id)
random.seed(20260808)
pairs = random.sample(list(itertools.combinations(ids, 2)), 4000)
vals = [jac(ents_by_id[a], ents_by_id[b]) for a, b in pairs]
vals_s = sorted(vals)
print("\n=== entity_jaccard over 4,000 RANDOM (assumed unrelated) PAIRS ===")
print(f"median={st.median(vals_s):.4f}  p90={vals_s[3600]:.4f}  p99={vals_s[3960]:.4f}  max={max(vals_s):.4f}")
for t in (0.3, 0.5, 0.8, 1.0):
    n = sum(1 for v in vals if v >= t)
    print(f"  >= {t:.1f}: {n:5d} / 4000 = {100.0*n/4000:6.3f}%")
print("\n  The V1 failure mode was unrelated pairs reaching ej = 1.000.")
print("  A usable feature needs the >=1.0 bucket at ~0 and a low p99.")

cross = [(a,b) for a,b in pairs if lang_of[a] != lang_of[b]]
cv = [jac(ents_by_id[a], ents_by_id[b]) for a,b in cross]
if cv:
    print(f"\ncross-language pairs only (n={len(cv)}): median={st.median(cv):.4f} max={max(cv):.4f}")
