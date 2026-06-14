#!/usr/bin/env python3
"""
Phase 1 oracle audit — validate DeepSeek's obituary labels with the 3-lab Ollama
panel (gemma3:27b / qwen3:14b / phi4:14b), all independent of the DeepSeek oracle.

Agreement = the 3-lab panel MAJORITY (of obituary/not_obituary votes) matches
DeepSeek's verdict on a stratified sample. Build-plan gate: require >=95% before
trusting the full corpus. Mirrors panel_audit.py (the gemini-era audit) but keyed
to deepseek_verdict / content / deepseek_labeled_corpus.jsonl.

The block class (obituary) is oversampled: a false positive (wrongly blocking a
constructive story) is the costly error, so the audit weights that side.

Usage (panel labs live on gpu-server Ollama):
    python panel_audit_deepseek.py --n-pos 20 --n-neg 10
"""
import argparse, json, re, time, urllib.request, random, collections
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "artifacts" / "deepseek_labeled_corpus.jsonl"
OUT = HERE / "artifacts" / "audit_result_deepseek.json"
GRADES = HERE / "artifacts" / "audit_grades_deepseek.jsonl"
OLLAMA = "http://gpu-server:11434/api/generate"
SEED = 7

# Same question DeepSeek answered (oracle prompt), so the panel adjudicates the
# identical task. SHARPENED-BROAD rule (owner decision 2026-06-14) — must match relabel_deepseek.py.
PROMPT = """You label articles for a CONSTRUCTIVE news feed.

DECISIVE TEST: Is this article PRIMARILY telling readers that a specific PERSON has recently died -- who they were, how they died, the loss? If yes -> "obituary". If the death is instead a hook for politics, policy, law, opinion, activism, or society -> "not_obituary".

BLOCK (label "obituary"):
- obituaries, death notices, mourning, tribute and memorial pieces for a person who recently died;
- hard-news reports whose MAIN SUBJECT is a specific person's recent death: fatal accidents, crime / homicide / shootings, disasters -- where the story is about that person dying.

KEEP (label "not_obituary"):
- political, electoral, legislative, or governmental stories, even when triggered by or reacting to a recent death (e.g. a party's seat math after a member dies, a politician's floor speech about a killing);
- opinion, advocacy, activism, protest, or commentary that uses a death to argue a broader point;
- justice / legal / investigation / inheritance / estate follow-ups and consequences of a death;
- commemoration or anniversaries of long-past deaths, and legacy tributes to figures who died long ago;
- profiles of people who are still alive;
- aggregate death tolls or mass-casualty counts with no single specific individual at the center;
- deaths of animals or other non-persons;
- any story that merely mentions death in passing.

If genuinely ambiguous, label "borderline".

Reply ONLY as JSON: {{"verdict":"obituary|not_obituary|borderline","reason":"one short sentence"}}

TITLE: {title}

ARTICLE:
{content}
"""

MODELS = [("gemma3:27b", None), ("qwen3:14b", False), ("phi4:14b", None)]

def post(url, p, t=200):
    for i in range(5):
        try:
            req = urllib.request.Request(url, data=json.dumps(p).encode(),
                                         headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=t).read().decode())
        except Exception as e:
            if i == 4:
                return {"__err__": str(e)[:60]}
            time.sleep(3 * (2 ** i))

def ask(model, prompt, think=None):
    p = {"model": model, "prompt": prompt, "stream": False, "format": "json",
         "options": {"temperature": 0}}
    if think is not None:
        p["think"] = think
    r = post(OLLAMA, p)
    return r.get("response", r.get("__err__", "?"))

def verdict(raw):
    try:
        v = json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group(0)).get("verdict", "?").lower()
        return v if v in ("obituary", "not_obituary", "borderline") else "?"
    except Exception:
        return "?"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-pos", type=int, default=20)
    ap.add_argument("--n-neg", type=int, default=10)
    args = ap.parse_args()
    random.seed(SEED)

    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8") if l.strip()]
    pos = [r for r in rows if r.get("deepseek_verdict") == "obituary"]
    neg = [r for r in rows if r.get("deepseek_verdict") == "not_obituary"]
    random.shuffle(pos); random.shuffle(neg)

    # diversify negatives across source categories
    by_cat = collections.defaultdict(list)
    for r in neg:
        by_cat[r.get("source_category") or "?"].append(r)
    neg_div, cats = [], list(by_cat)
    random.shuffle(cats)
    i = 0
    while len(neg_div) < min(args.n_neg, len(neg)):
        c = cats[i % len(cats)]
        if by_cat[c]:
            neg_div.append(by_cat[c].pop())
        i += 1
        if i > 10000:
            break

    sample = pos[:args.n_pos] + neg_div[:args.n_neg]
    random.shuffle(sample)
    print(f"corpus pos={len(pos)} neg={len(neg)} | audit sample={len(sample)} "
          f"(pos={min(args.n_pos,len(pos))}, neg={min(args.n_neg,len(neg))})")

    panel = {}
    for name, think in MODELS:
        print(f"  panel: {name}")
        for r in sample:
            pr = PROMPT.format(title=r.get("title") or "", content=(r.get("content") or "")[:1600])
            panel.setdefault(r["id"], {})[name] = verdict(ask(name, pr, think))

    grades_fh = open(GRADES, "w", encoding="utf-8")
    agree = 0
    disagree = []
    for r in sample:
        vs = [panel[r["id"]][m] for m, _ in MODELS]
        c = collections.Counter(v for v in vs if v in ("obituary", "not_obituary"))
        maj = c.most_common(1)[0][0] if c else "?"
        ok = (maj == r["deepseek_verdict"])
        agree += ok
        grades_fh.write(json.dumps({
            "id": r["id"], "title": r.get("title"), "deepseek": r["deepseek_verdict"],
            "panel_majority": maj, "votes": dict(zip([m for m, _ in MODELS], vs)),
            "agree": ok,
        }, ensure_ascii=False) + "\n")
        if not ok:
            disagree.append((r, vs, maj))
    grades_fh.close()

    frac = agree / len(sample) if sample else 0.0
    print(f"\n=== panel(3-lab) vs DeepSeek agreement: {agree}/{len(sample)} = {frac:.0%} ===")
    print(f"   gate: >=95% to trust the corpus")
    for r, vs, maj in disagree:
        print(f"  deepseek={r['deepseek_verdict']:<13} panel={maj:<13} "
              f"votes={'/'.join(vs)}  :: {(r.get('title') or '')[:55]}")
    json.dump({"agreement": frac, "n": len(sample), "agree": agree,
               "n_pos": min(args.n_pos, len(pos)), "n_neg": min(args.n_neg, len(neg))},
              open(OUT, "w"))
    print(f"\nwrote {GRADES.name} + {OUT.name}")

if __name__ == "__main__":
    main()
