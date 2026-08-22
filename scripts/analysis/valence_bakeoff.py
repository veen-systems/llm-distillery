"""Three-oracle bake-off on the uplifting v7 adverse set: does the ORACLE share
the student's valence failure?

REPRODUCE (2026-08-20 run: docs/evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md):

  1. Assemble articles. The repo holds only 300-char excerpts (#97), so full text
     comes from the NexusMind archive on sadalsuud
     (~/local_dev/NexusMind/data/filtered/uplifting/*.jsonl, ~14-day window) keyed
     by the `id` in datasets/adverse/uplifting.jsonl; anything older is refetched
     from `url`. Write one JSONL with {id,title,content,source,published_date,
     klass,src_file} to a SCRATCHPAD path. NEVER commit the text.
     Reject any row recovering <90% of `content_original_length` -- a paywalled
     refetch is an extraction defect, not the article (2026-08-10 adjudication).
  2. Run each arm:
       python3 scripts/analysis/valence_bakeoff.py --arm gemini   --articles A.jsonl --out g.jsonl
       python3 scripts/analysis/valence_bakeoff.py --arm deepseek --articles A.jsonl --out d.jsonl
       ssh -f -N -L 11435:localhost:11434 b650-gpu     # ollama is localhost-only there
       python3 scripts/analysis/valence_bakeoff.py --arm ollama --model qwen3:14b --articles A.jsonl --out q.jsonl
     Needs the NexusMind venv (google-genai + requests):
       ~/repos/veen-systems/NexusMind/venv/bin/python3

  WARNING: single-run oracle scores are NOISY -- mean |d| 0.82, max 2.25 measured
  against the same oracle's recorded values 10 days earlier. Average k runs before
  treating any single number as a measurement (feedback-oracle-bias-vs-noise).

Question (llm-distillery#125 follow-up, 2026-08-20): the student scores
harm-adjacent stories at human_wellbeing_impact 6.66-7.75. We have never asked
the oracle. If the oracle also scores them high, the v8 prompt rewrite can fix
class A. If only the student does, the prompt rewrite cannot reach it.

Same prompt (uplifting v7), same clean/compress/sanitize path, same temperature
(0.3) across all three arms. Article text is the EXACT text the scorer saw for
the 8 pulled from the NexusMind archive.

Full text lives in the scratchpad only -- never the repo (#97).
"""
import argparse, json, os, sys, time
from pathlib import Path
import requests

LD = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(LD))
from ground_truth.text_cleaning import (
    clean_article as clean_article_comprehensive,
    sanitize_text_comprehensive,
)

PROMPT_PATH = LD / "filters" / "uplifting" / "v7" / "prompt-compressed.md"
PLACEHOLDER = "[Paste the summary of the article here]"
DIMS = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact",
        "evidence_level", "benefit_distribution", "change_durability"]
WEIGHTS = {"human_wellbeing_impact": 0.30, "social_cohesion_impact": 0.20,
           "justice_rights_impact": 0.15, "evidence_level": 0.10,
           "benefit_distribution": 0.10, "change_durability": 0.15}
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# WEIGHTS duplicates filters/uplifting/v7/base_scorer.DIMENSION_WEIGHTS on purpose
# (this script must run without importing the filter package). Verified equal
# 2026-08-21; _assert_weights_match() below re-checks at runtime so a drift in the
# deployed weights cannot silently change what this script reports.


def _assert_weights_match():
    """Fail loudly if the deployed weights have drifted from the copy above."""
    import yaml
    cfg = yaml.safe_load(open(LD / "filters" / "uplifting" / "v7" / "config.yaml",
                              encoding="utf-8"))
    live = {k: v["weight"] for k, v in cfg["scoring"]["dimensions"].items()}
    if live != WEIGHTS:
        raise SystemExit(f"ERROR: weight drift.\n  script: {WEIGHTS}\n  config: {live}")


def secret(key, required=True):
    """Read a credential. RAISES on absence when required.

    It used to return None, which produced a silent all-error run: every row got
    an HTTP 401 recorded in rec["error"], weighted_average stayed None, the output
    file was written and the process exited 0. A run that scored nothing was
    indistinguishable from a run that found nothing.
    """
    import configparser
    cp = configparser.ConfigParser()
    path = LD / "config" / "credentials" / "secrets.ini"
    if not path.exists():
        raise SystemExit(f"ERROR: {path} not found — cannot run a cloud arm.")
    cp.read(path)
    val = cp.get("api_keys", key, fallback=None)
    if required and not val:
        raise SystemExit(f"ERROR: api_keys.{key} missing from {path}.")
    return val


def smart_compress(content, max_words=800):
    words = content.split()
    if len(words) <= max_words:
        return content
    s, e = int(max_words * 0.7), int(max_words * 0.3)
    return f"{' '.join(words[:s])}\n\n[...content compressed...]\n\n{' '.join(words[-e:])}"


def build_prompt(tpl, article):
    a = clean_article_comprehensive(dict(article))
    body = sanitize_text_comprehensive(smart_compress(a.get("content", "") or ""))
    head = (f"Title: {sanitize_text_comprehensive(a.get('title') or 'N/A')}\n"
            f"Source: {sanitize_text_comprehensive(a.get('source') or 'N/A')}\n"
            f"Published: {sanitize_text_comprehensive(str(a.get('published_date') or 'N/A'))}\n\n{body}")
    return tpl.replace(PLACEHOLDER, head)


def dim_score(v):
    if isinstance(v, dict):
        v = v.get("score")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse(text):
    text = text.strip()
    if text.startswith("```"):
        # split(...)[1] IndexErrors on an unterminated fence; take what follows the
        # opening fence and let the brace-slice below find the object.
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text[3:]
        text = text[4:] if text.lower().startswith("json") else text
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        text = text[i:j + 1]
    p = json.loads(text)
    out = {d: dim_score(p.get(d)) for d in DIMS}
    out["content_type"] = p.get("content_type")
    return out


def wa(scores):
    if any(scores.get(d) is None for d in DIMS):
        return None
    return round(sum(scores[d] * WEIGHTS[d] for d in DIMS), 4)


# ---------- arms ----------
def call_gemini(prompt):
    from google import genai
    from google.genai import types as gt
    key = secret("gemini_billing_api_key", required=False) or secret("gemini_api_key")
    cl = genai.Client(api_key=key)
    last = None
    for attempt in range(6):
        try:
            r = cl.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
                config=gt.GenerateContentConfig(temperature=0.3, max_output_tokens=4096,
                                                thinking_config=gt.ThinkingConfig(thinking_budget=0)))
            return r.text.strip()
        except Exception as e:
            msg = str(e)
            if "429" in msg or "503" in msg or "UNAVAILABLE" in msg or "RESOURCE_EXHAUSTED" in msg:
                last = e
                time.sleep(min(60, 5 * (2 ** attempt)))
                continue
            raise
    raise last


def call_deepseek(prompt):
    r = requests.post(DEEPSEEK_URL,
                      headers={"Authorization": f"Bearer {secret('deepseek_api_key')}",
                               "Content-Type": "application/json"},
                      json={"model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.3, "max_tokens": 4096,
                            "response_format": {"type": "json_object"}}, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_ollama(prompt, model, host):
    r = requests.post(f"{host}/api/generate",
                      json={"model": model, "prompt": prompt, "stream": False,
                            "format": "json", "think": False,
                            "options": {"temperature": 0.3, "num_ctx": 16384,
                                        "num_predict": 4096}}, timeout=900)
    r.raise_for_status()
    return r.json()["response"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["gemini", "deepseek", "ollama"])
    ap.add_argument("--model", default="qwen3:14b")
    ap.add_argument("--host", default="http://localhost:11435")
    ap.add_argument("--articles", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    _assert_weights_match()
    tpl = PROMPT_PATH.read_text(encoding="utf-8")
    arts = [json.loads(l) for l in open(a.articles, encoding="utf-8") if l.strip()]
    label = a.model if a.arm == "ollama" else ("gemini-2.5-flash" if a.arm == "gemini" else "deepseek-chat")

    errors = 0
    with open(a.out, "w", encoding="utf-8") as fh:
        for art in arts:
            prompt = build_prompt(tpl, art)
            rec = {"id": art["id"], "arm": label, "klass": art.get("klass"),
                   "title": art.get("title"), "n_chars": len(art.get("content") or ""),
                   "text_provenance": art.get("src_file")}
            t0 = time.time()
            try:
                raw = {"gemini": call_gemini, "deepseek": call_deepseek}.get(a.arm, lambda p: call_ollama(p, a.model, a.host))(prompt)
                rec.update(parse(raw))
                rec["weighted_average"] = wa(rec)
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
            rec["seconds"] = round(time.time() - t0, 1)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if "error" in rec:
                errors += 1
            hwb = rec.get("human_wellbeing_impact")
            print(f"  [{label}] {rec.get('klass','?')} hwb={hwb!s:>5} wa={rec.get('weighted_average')!s:>7} "
                  f"ct={str(rec.get('content_type'))[:18]:18s} {rec.get('error','')[:60]}  {rec['title'][:34]}",
                  flush=True)

    if arts and errors == len(arts):
        raise SystemExit(
            f"ERROR: every one of {len(arts)} rows errored — this is a failed run, not a "
            f"result. Output at {a.out} is unusable; do not read numbers off it."
        )
    if errors:
        print(f"WARNING: {errors} of {len(arts)} rows errored", flush=True)


if __name__ == "__main__":
    main()
