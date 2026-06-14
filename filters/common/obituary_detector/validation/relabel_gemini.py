#!/usr/bin/env python3
"""Relabel the obituary seed corpus with gemini-flash using the owner-endorsed rule.
Replaces contaminated gate-reason-substring labels with oracle obituary judgments."""
import json, re, time, urllib.request, sys
from concurrent.futures import ThreadPoolExecutor

ENV={}
for line in open(r"C:/local_dev/ovr.news/.env",encoding="utf-8"):
    if "=" in line and not line.strip().startswith("#"):
        k,_,v=line.partition("="); ENV[k.strip()]=v.strip().strip('"').strip("'")
GK=ENV.get("GEMINI_BILLING_API_KEY") or ENV.get("GEMINI_API_KEY")

PROMPT="""You label articles for an obituary detector used by a CONSTRUCTIVE news feed.

BLOCK (label "obituary"): fresh obituaries / death notices / mourning pieces whose PRIMARY purpose is to mark a specific person's recent death.

KEEP (label "not_obituary"): memorial events, anniversary/commemoration pieces, legacy tributes, laws or programs prompted by a death, profiles of living people, and any story that merely mentions death in passing.

If genuinely ambiguous, label "borderline".

Reply ONLY as JSON: {{"verdict":"obituary|not_obituary|borderline","reason":"one short sentence"}}

TITLE: {title}

ARTICLE:
{content}
"""

def post(url,p,t=90):
    for i in range(5):
        try:
            req=urllib.request.Request(url,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
            return json.loads(urllib.request.urlopen(req,timeout=t).read().decode())
        except Exception as e:
            if i==4: raise
            time.sleep(2*(2**i))

def label(row):
    pr=PROMPT.format(title=row.get("title") or "", content=(row.get("content_start") or row.get("content") or "")[:1600])
    u=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GK}"
    try:
        out=post(u,{"contents":[{"parts":[{"text":pr}]}],"generationConfig":{"temperature":0,"response_mime_type":"application/json"}})
        txt=out["candidates"][0]["content"]["parts"][0]["text"]
        o=json.loads(re.search(r"\{.*\}",txt,re.DOTALL).group(0))
        v=str(o.get("verdict","")).lower().strip()
        if v not in ("obituary","not_obituary","borderline"): v="parse_error"
        return v,str(o.get("reason",""))[:160]
    except Exception as e:
        return "error",str(e)[:120]

rows=[json.loads(l) for l in open("seed_local.jsonl",encoding="utf-8") if l.strip()]
print(f"relabeling {len(rows)} rows with gemini-2.5-flash ...")
done=0
def work(r):
    global done
    v,reason=label(r); r["gemini_verdict"]=v; r["gemini_reason"]=reason
    done+=1
    if done%100==0: print(f"  {done}/{len(rows)}")
    return r
with ThreadPoolExecutor(max_workers=6) as ex:
    rows=list(ex.map(work,rows))

with open("seed_relabeled.jsonl","w",encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")

import collections
# cross-tab old (gate-derived) label vs new gemini verdict
ct=collections.Counter((r["label"],r["gemini_verdict"]) for r in rows)
print("\n=== old gate-label  x  gemini verdict ===")
for (old,new),n in sorted(ct.items()): print(f"  {old:<9} -> {new:<13} {n}")
print("\ngemini verdict totals:", dict(collections.Counter(r["gemini_verdict"] for r in rows)))
PY = None
