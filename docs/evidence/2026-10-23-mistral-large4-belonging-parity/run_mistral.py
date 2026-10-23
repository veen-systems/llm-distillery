"""Score belonging v3's 100-item canary set on mistral-large-4-0; rows in the shape canary.evaluate reads (EXP-060).
Usage (from the checkout): .venv/bin/python run_mistral.py OUT.jsonl [--extra JSON] [--limit N] [--offset N]
Prompt bytes come from batch_scorer's own build_prompt (the baseline's scorer). Resumes: ids already scored in OUT
are skipped. Raw usage, finish_reason, served model and thinking length kept per row. Key: ~/.config/mistral/api_key."""
import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests, yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from ground_truth import oracle_canary as oc  # noqa: E402
from ground_truth.batch_scorer import GenericBatchScorer  # noqa: E402
from ground_truth.oracle_provenance import prompt_sha256  # noqa: E402
from score_ollama_oracle import extract_dim_score  # noqa: E402

URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-large-4-0"
FATAL = (401, 402, 403)

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--extra", default="{}")
ap.add_argument("--limit", type=int); ap.add_argument("--offset", type=int, default=0)
a = ap.parse_args()
extra, out_path = json.loads(a.extra), Path(a.out)

b = json.load(open(ROOT / "config/canary/belonging.baseline.json"))
set_path, _ = oc.verify_set("belonging")                      # raises unless the set's bytes match the manifest
bs = GenericBatchScorer.__new__(GenericBatchScorer)           # no client, no gate: only its prompt builder
bs.prompt_path = ROOT / b["prompt"]
bs.prompt_template = bs._load_prompt_template()
SHA = prompt_sha256(bs.prompt_template)
if SHA != b["prompt_sha256_stripped"]:
    raise SystemExit(f"FATAL: template digest {SHA} != baseline's stripped {b['prompt_sha256_stripped']}")
DIMS = list(yaml.safe_load(open(ROOT / b["config"]))["scoring"]["dimensions"])
KEY = open(os.path.expanduser("~/.config/mistral/api_key")).read().strip()
SET = [json.loads(l) for l in open(set_path, encoding="utf-8")][a.offset:]
stop = {"status": None}


def one(article):
    if stop["status"]:
        return {"id": article["id"], "error": f"aborted: HTTP {stop['status']} earlier"}
    body = {"model": MODEL, "messages": [{"role": "user", "content": bs.build_prompt(article)}],
            "temperature": 0.3, "max_tokens": 8192, "response_format": {"type": "json_object"}, **extra}
    r = None
    for attempt in range(5):
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {KEY}"}, json=body, timeout=600)
        except requests.RequestException as e:
            time.sleep(2 ** attempt * 3); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt * 3); continue
        break
    row = {"id": article["id"], "status": getattr(r, "status_code", None), "extra": extra}
    if r is None or r.status_code != 200:
        if r is not None and r.status_code in FATAL:
            stop["status"] = r.status_code
        return dict(row, error=f"HTTP {row['status']}: {(r.text if r is not None else 'no response')[:300]}")
    j = r.json()
    msg = j["choices"][0]["message"].get("content") or ""
    parts = msg if isinstance(msg, list) else [{"type": "text", "text": msg}]
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    thinking = sum(len(json.dumps(p.get("thinking", ""))) for p in parts if p.get("type") == "thinking")
    row.update(usage=j.get("usage"), finish_reason=j["choices"][0].get("finish_reason"), thinking_chars=thinking,
               served_model=j.get("model"))
    try:
        p = json.loads(text)
        sc = {d: extract_dim_score(p.get(d)) for d in DIMS}
        if any(v is None for v in sc.values()):
            return dict(row, error="missing dims", raw=text[:300])
    except (ValueError, AttributeError):
        return dict(row, error="bad json", raw=text[:300])
    row["belonging_analysis"] = dict({d: {"score": v} for d, v in sc.items()}, prompt_sha256=SHA,
                                     served_model=j.get("model"))
    return row


done = set()
if out_path.exists():
    done = {r["id"] for r in map(json.loads, open(out_path)) if "belonging_analysis" in r}
todo = [x for x in SET if x["id"] not in done][:a.limit]
print(f"{MODEL} extra={extra}: {len(done)} done, {len(todo)} to score", flush=True)
tin = tout = 0
with ThreadPoolExecutor(4) as ex, open(out_path, "a", encoding="utf-8") as f:
    for row in ex.map(one, todo):
        f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
        u = row.get("usage") or {}
        tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
        if "error" in row:
            print("ERR", row["id"], row["error"][:160], flush=True)
print(f"tokens in {tin:,} out {tout:,}", flush=True)
if stop["status"]:
    sys.exit(2)
