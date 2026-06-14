#!/usr/bin/env python3
"""
Phase 1 oracle-labeling — DeepSeek labels raw death-adjacent candidates as
obituary / not_obituary / borderline (build-plan Phase 1, NM#185 / llm-distillery#51).

DeepSeek is chosen as the ORACLE (not gemini) because it is independent of the
3-lab Ollama AUDIT panel (gemma3 / qwen3 / phi4) — preserving the cross-check that
caught v1 — and runs on the owner's DeepSeek credits rather than the podcast-reserved
gemini budget. gemini is thereby freed to sit on the Phase-2 held-out validation panel,
keeping the oracle independent from every validation lab.

Same endorsed labeling rule as relabel_gemini.py. OpenAI-compatible endpoint,
temperature 0, JSON response. RESUMABLE: re-running skips ids already in --out, so a
balance shortfall / rate-limit mid-run loses nothing — just top up and re-run.

verdict -> label mapping for the trainer (which keys on label=="positive"):
    obituary    -> positive
    not_obituary-> negative
    borderline  -> negative   (kept verbatim in deepseek_verdict for later review)

Usage:
    python relabel_deepseek.py \
        --in  artifacts/raw_candidates_corpus.jsonl \
        --out artifacts/deepseek_labeled_corpus.jsonl
"""
import argparse, json, re, time, os, urllib.request
from concurrent.futures import ThreadPoolExecutor

def _load_key():
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    # llm-distillery credential store
    import configparser
    secrets = r"C:/local_dev/llm-distillery/config/credentials/secrets.ini"
    if os.path.exists(secrets):
        cp = configparser.ConfigParser()
        cp.read(secrets, encoding="utf-8")
        if cp.has_option("api_keys", "deepseek_api_key"):
            return cp.get("api_keys", "deepseek_api_key").strip()
    return None

KEY = _load_key()
URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

# SHARPENED-BROAD rule (owner decision 2026-06-14): block death-EVENT reporting of a
# specific PERSON (obituary, accident, crime, disaster), but DO NOT block politics /
# policy / opinion / advocacy / reaction pieces that merely use a death as their subject,
# nor animal/non-person deaths. The decisive test is PRIMARY PURPOSE.
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

def call(prompt, t=90):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "max_tokens": 120,
    }
    last = None
    for i in range(5):
        try:
            req = urllib.request.Request(
                URL, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
            out = json.loads(urllib.request.urlopen(req, timeout=t).read().decode())
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            # 402 = insufficient balance: stop fast, the run is resumable
            if "402" in str(e):
                raise RuntimeError("DeepSeek 402 insufficient balance — top up and re-run (resumable)")
            if i == 4:
                raise
            time.sleep(2 * (2 ** i))
    raise last

def label(row):
    pr = PROMPT.format(title=row.get("title") or "",
                       content=(row.get("content") or "")[:1600])
    try:
        txt = call(pr)
        o = json.loads(re.search(r"\{.*\}", txt, re.DOTALL).group(0))
        v = str(o.get("verdict", "")).lower().strip()
        if v not in ("obituary", "not_obituary", "borderline"):
            v = "parse_error"
        return v, str(o.get("reason", ""))[:160]
    except RuntimeError:
        raise
    except Exception as e:
        return "error", str(e)[:120]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all (debug cap otherwise)")
    args = ap.parse_args()

    if not KEY:
        raise SystemExit("DEEPSEEK_API_KEY not found in env or llm-distillery secrets.ini [api_keys]")

    rows = [json.loads(l) for l in open(args.inp, encoding="utf-8") if l.strip()]
    if args.limit:
        rows = rows[: args.limit]

    # resume: skip ids already labeled in --out
    done_ids = set()
    if os.path.exists(args.out):
        for l in open(args.out, encoding="utf-8"):
            if l.strip():
                try: done_ids.add(json.loads(l)["id"])
                except Exception: pass
    todo = [r for r in rows if r["id"] not in done_ids]
    print(f"candidates={len(rows)}  already_labeled={len(done_ids)}  to_label={len(todo)}")

    out_fh = open(args.out, "a", encoding="utf-8")
    done = 0
    halted = False

    def work(r):
        nonlocal done, halted
        if halted:
            return None
        try:
            v, reason = label(r)
        except RuntimeError as e:
            halted = True
            print(f"\n!! {e}")
            return None
        r["deepseek_verdict"] = v
        r["deepseek_reason"] = reason
        r["label"] = "positive" if v == "obituary" else "negative"
        done += 1
        if done % 200 == 0:
            print(f"  {done}/{len(todo)}")
        return r

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(work, todo):
            if r is not None:
                out_fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                out_fh.flush()
    out_fh.close()

    # tally over the full out file
    import collections
    verdicts = collections.Counter()
    for l in open(args.out, encoding="utf-8"):
        if l.strip():
            verdicts[json.loads(l).get("deepseek_verdict")] += 1
    print("\n=== deepseek verdict totals (full out file) ===")
    for k, n in verdicts.most_common():
        print(f"  {k:<13} {n}")
    pos = verdicts.get("obituary", 0)
    print(f"\nobituary positives so far: {pos}")
    if halted:
        print("RUN HALTED (balance/error) — re-run the same command to resume.")

if __name__ == "__main__":
    main()
