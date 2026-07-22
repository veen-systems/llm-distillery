import json, sys, time, os
sys.path.insert(0, "/home/hcl/llm-distillery")
from collections import Counter
import statistics as st
from filters.common.commerce_prefilter.v1.inference import CommercePrefilterSLM
from filters.common.commerce_prefilter.v2.inference import CommercePrefilterV2

TH = 0.95
arts = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(f"loaded {len(arts)} articles", flush=True)

t = time.time()
v2 = CommercePrefilterV2(threshold=TH, device="cpu")
print("scoring v2 (batch)...", flush=True)
v2res = v2.batch_predict(arts)
s2 = [r["score"] for r in v2res]
print(f"v2 done in {time.time()-t:.0f}s", flush=True)

t = time.time()
v1 = CommercePrefilterSLM(threshold=TH)
print("scoring v1...", flush=True)
s1 = [v1.is_commerce(a)["score"] for a in arts]
print(f"v1 done in {time.time()-t:.0f}s", flush=True)

n = len(arts)
b1 = [s >= TH for s in s1]; b2 = [s >= TH for s in s2]
f1 = sum(b1); f2 = sum(b2)
agree = sum(1 for i in range(n) if b1[i] == b2[i])
v1only = [i for i in range(n) if b1[i] and not b2[i]]   # v1 flags, v2 misses (v2 under-blocks)
v2only = [i for i in range(n) if b2[i] and not b1[i]]   # v2 flags, v1 misses (v2 over-blocks)

m1, m2 = st.mean(s1), st.mean(s2)
cov = sum((s1[i]-m1)*(s2[i]-m2) for i in range(n))
sd1 = (sum((x-m1)**2 for x in s1))**.5; sd2 = (sum((x-m2)**2 for x in s2))**.5
pear = cov/(sd1*sd2) if sd1 and sd2 else float("nan")
mad = st.mean(abs(s1[i]-s2[i]) for i in range(n))
clen = lambda i: len(arts[i].get("content") or "")

print("="*56)
print(f"SHADOW COMPARISON  n={n}  threshold={TH}")
print(f"v1 flagged commerce: {f1} ({100*f1/n:.1f}%)")
print(f"v2 flagged commerce: {f2} ({100*f2/n:.1f}%)")
print(f"binary DECISION agreement: {agree}/{n} = {100*agree/n:.2f}%")
print(f"  v1 flags / v2 MISSES (v2 under-blocks): {len(v1only)}")
print(f"  v2 flags / v1 misses (v2 over-blocks):  {len(v2only)}")
print(f"raw-score pearson r: {pear:.3f}   mean|s1-s2|: {mad:.3f}")
allmed = sorted(clen(i) for i in range(n))[n//2]
if v1only:
    print(f"v2-miss content chars: median {sorted(clen(i) for i in v1only)[len(v1only)//2]} (overall median {allmed})")
print("v1-only (v2 under-block) langs:", dict(Counter(arts[i].get('language') for i in v1only)))
print("v2-only (v2 over-block)  langs:", dict(Counter(arts[i].get('language') for i in v2only)))

def show(idxs, label, k=8):
    print(f"--- {label} (up to {k}) ---")
    for i in idxs[:k]:
        a = arts[i]
        print(f"  s1={s1[i]:.2f} s2={s2[i]:.2f} len={clen(i):4d} {a.get('language')} | {(a.get('title') or '')[:66]}")
show(sorted(v1only, key=lambda i:-clen(i)), "v1 flags, v2 MISSES  [sorted longest-first: 128-tok suspects]")
show(v2only, "v2 flags, v1 misses  [v2 over-blocks]")

prod = [a.get("_prod_commerce") for a in arts]
okp = [i for i in range(n) if isinstance(prod[i], (int, float))]
if okp:
    dmad = st.mean(abs(s2[i]-prod[i]) for i in okp)
    print(f"[sanity] fresh-v2 vs production _commerce_score: mean|delta|={dmad:.3f} over {len(okp)} (expect ~0)")
