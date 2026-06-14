#!/usr/bin/env python3
"""
Multi-model BLIND panel for the obituary held-out worksheet (NM#185 validation).

Four independent labs vote on each article (title+content only — blind to the
obituary model's score and the gate's label):
  - gemini-2.5-flash   (Google,    REST API)
  - gemma3:27b         (Google,    Ollama @ gpu-server)
  - qwen3:14b          (Alibaba,   Ollama @ gpu-server)
  - phi4:14b           (Microsoft, Ollama @ gpu-server)

Majority vote = ground truth (computed in the roll-up, not here). Adding DeepSeek
later: add one MODELS entry with kind="openai" once DEEPSEEK_API_KEY is set.

Output: grades_panel_obit.jsonl, one row per (model, article).
Pure stdlib (urllib) — no SDKs.
"""
import json, os, re, time, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).parent
WORKSHEET = HERE / "worksheet_obit.jsonl"
OUT = HERE / "grades_panel_obit.jsonl"
OLLAMA = "http://gpu-server:11434/api/generate"

# load GEMINI key from ovr.news/.env (run this panel LOCALLY: gemini REST + Ollama@gpu-server)
ENV = {}
_envp = Path(r"C:/local_dev/ovr.news/.env")
if _envp.exists():
    for line in _envp.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            ENV[k.strip()] = v.strip().strip('"').strip("'")
GEMINI_KEY = ENV.get("GEMINI_BILLING_API_KEY") or ENV.get("GEMINI_API_KEY", "")

MODELS = [
    {"name": "gemma3:27b",       "kind": "ollama"},
    {"name": "qwen3:14b",        "kind": "ollama", "think": False},  # disable thinking -> valid JSON
    {"name": "phi4:14b",         "kind": "ollama"},
    {"name": "gemini-2.5-flash", "kind": "gemini"},
    # {"name": "deepseek-chat",  "kind": "openai", "base": "https://api.deepseek.com", "key_env": "DEEPSEEK_API_KEY"},
]

# SHARPENED-BROAD rule (owner decision 2026-06-14) — must match relabel_deepseek.py /
# panel_audit_deepseek.py so the held-out panel grades the trained definition.
PROMPT = """You screen articles for a CONSTRUCTIVE news feed (progress, recovery, community, solutions).

DECISIVE TEST: Is this article PRIMARILY telling readers that a specific PERSON has recently died -- who they were, how they died, the loss? If yes -> "obituary". If the death is instead a hook for politics, policy, law, opinion, activism, or society -> "not_obituary".

BLOCK ("obituary"):
- obituaries, death notices, mourning, tribute and memorial pieces for a person who recently died;
- hard-news reports whose MAIN SUBJECT is a specific person's recent death: fatal accidents, crime / homicide / shootings, disasters -- where the story is about that person dying.

KEEP ("not_obituary"):
- political, electoral, legislative, or governmental stories, even when triggered by or reacting to a recent death (e.g. a party's seat math after a member dies, a politician's floor speech about a killing);
- opinion, advocacy, activism, protest, or commentary that uses a death to argue a broader point;
- justice / legal / investigation / inheritance / estate follow-ups and consequences of a death;
- commemoration or anniversaries of long-past deaths, and legacy tributes to figures who died long ago;
- profiles of people who are still alive;
- aggregate death tolls or mass-casualty counts with no single specific individual at the center;
- deaths of animals or other non-persons;
- any story that merely mentions death in passing.

"borderline" = genuinely ambiguous.

Reply with ONLY a JSON object, no prose:
{{"verdict":"obituary|not_obituary|borderline","confidence":"low|med|high","reason":"one short sentence"}}

TITLE: {title}

ARTICLE:
{content}
"""

def post(url, payload, timeout=120):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def post_retry(url, payload, timeout=120, tries=4):
    """Retry on transient 429/500/503 with exponential backoff."""
    last = None
    for i in range(tries):
        try:
            return post(url, payload, timeout)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 503):
                time.sleep(2 * (2 ** i))  # 2,4,8,16s
                continue
            raise
        except Exception as e:
            last = e
            time.sleep(2 * (2 ** i))
    raise last

def call_ollama(model, prompt, think=None):
    payload = {"model": model, "prompt": prompt, "stream": False,
               "format": "json", "options": {"temperature": 0}}
    if think is not None:
        payload["think"] = think
    out = post_retry(OLLAMA, payload)
    return out.get("response", "")

def call_gemini(model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    out = post_retry(url, {"contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"temperature": 0, "response_mime_type": "application/json"}})
    return out["candidates"][0]["content"]["parts"][0]["text"]

def parse(raw):
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        o = json.loads(m.group(0) if m else raw)
        v = str(o.get("verdict", "")).lower().strip()
        if v not in ("obituary", "not_obituary", "borderline"):
            v = "parse_error"
        return v, str(o.get("confidence", "")).lower().strip(), str(o.get("reason", ""))[:200]
    except Exception as e:
        return "parse_error", "", f"RAW:{raw[:120]}"

rows = [json.loads(l) for l in open(WORKSHEET, encoding="utf-8") if l.strip()]
print(f"worksheet: {len(rows)} articles x {len(MODELS)} models = {len(rows)*len(MODELS)} calls")

results = []
for m in MODELS:
    name, kind = m["name"], m["kind"]
    print(f"\n=== {name} ({kind}) ===")
    for i, r in enumerate(rows):
        prompt = PROMPT.format(title=r.get("title") or "", content=(r.get("content") or "")[:1600])
        t0 = time.time()
        try:
            raw = call_ollama(name, prompt, m.get("think")) if kind == "ollama" else call_gemini(name, prompt)
            verdict, conf, reason = parse(raw)
        except Exception as e:
            verdict, conf, reason = "error", "", str(e)[:160]
        results.append({"model": name, "id": r["id"], "bucket": r["bucket"],
                        "verdict": verdict, "confidence": conf, "reason": reason})
        print(f"  [{i+1:>2}/{len(rows)}] {verdict:<13} {r['id'][:40]:<40} ({time.time()-t0:.1f}s)")

with open(OUT, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"\nwrote {len(results)} grades -> {OUT}")
