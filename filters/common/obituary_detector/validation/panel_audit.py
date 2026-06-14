#!/usr/bin/env python3
"""Audit gemini's relabels with the 3 Ollama models (gemini excluded from its own audit).
Agreement = the 3-lab panel majority matches gemini's verdict."""
import json, re, time, urllib.request, random, collections
random.seed(7)

rows=[json.loads(l) for l in open("seed_relabeled.jsonl",encoding="utf-8") if l.strip()]
kept_pos=[r for r in rows if r["label"]=="positive" and r["gemini_verdict"]=="obituary"]
flipped =[r for r in rows if r["label"]=="positive" and r["gemini_verdict"]=="not_obituary"]
negs    =[r for r in rows if r["label"]=="negative" and r["gemini_verdict"]=="not_obituary"]
random.shuffle(kept_pos); random.shuffle(flipped); random.shuffle(negs)
sample = kept_pos[:14] + flipped[:10] + negs[:6]
print(f"audit sample: {len(sample)} (kept_pos=14, flipped=10, neg=6)")

TMPL=re.search(r'PROMPT="""(.*?)"""', open("relabel_gemini.py",encoding="utf-8").read(), re.DOTALL).group(1)
def post(url,p,t=200):
    for i in range(5):
        try:
            req=urllib.request.Request(url,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
            return json.loads(urllib.request.urlopen(req,timeout=t).read().decode())
        except Exception as e:
            if i==4: return {"__err__":str(e)[:50]}
            time.sleep(3*(2**i))
def ask(model,prompt,think=None):
    p={"model":model,"prompt":prompt,"stream":False,"format":"json","options":{"temperature":0}}
    if think is not None: p["think"]=think
    r=post("http://gpu-server:11434/api/generate",p); return r.get("response",r.get("__err__","?"))
def verdict(raw):
    try:
        v=json.loads(re.search(r"\{.*\}",raw,re.DOTALL).group(0)).get("verdict","?").lower()
        return v if v in ("obituary","not_obituary","borderline") else "?"
    except: return "?"

MODELS=[("gemma3:27b",None),("qwen3:14b",False),("phi4:14b",None)]
panel={}
for name,think in MODELS:
    print(f"  panel: {name}")
    for r in sample:
        pr=TMPL.format(title=r.get("title") or "", content=(r.get("content_start") or "")[:1600])
        panel.setdefault(r["id"],{})[name]=verdict(ask(name,pr,think))

agree=0; disagree=[]
for r in sample:
    vs=[panel[r["id"]][m] for m,_ in MODELS]
    c=collections.Counter(v for v in vs if v in ("obituary","not_obituary"))
    maj=c.most_common(1)[0][0] if c else "?"
    ok = (maj==r["gemini_verdict"])
    agree+=ok
    if not ok: disagree.append((r,vs,maj))
print(f"\n=== panel(3-lab) vs gemini agreement: {agree}/{len(sample)} = {agree/len(sample):.0%} ===")
for r,vs,maj in disagree:
    print(f"  gemini={r['gemini_verdict']:<13} panel={maj:<13} votes={'/'.join(vs)}  :: {(r.get('title') or '')[:55]}")
json.dump({"agreement":agree/len(sample),"n":len(sample)}, open("audit_result.json","w"))
