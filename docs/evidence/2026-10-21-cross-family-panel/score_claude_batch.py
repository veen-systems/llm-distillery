"""EXP-055 P2: score the human_thriving canary set with Claude Sonnet 5.5 through the Message Batches API.
Evaluation only (PREREGISTRATION.md, amendment 2026-10-21): its outputs never become training labels.

    python score_claude_batch.py count  <workdir>     # count_tokens on 3 items, projected worst-case cost
    python score_claude_batch.py submit <workdir>     # refuses unless the projection is <= CAP_USD
    python score_claude_batch.py collect <workdir>    # when the batch has ended: writes <workdir>/P2.jsonl

The key is read from ~/.config/anthropic/api_key per run and passed to the client: never exported, never printed.
The request reuses the oracle's prompt + build_prompt, and each reply goes through the oracle's own parse_response
(score_deepseek_production.py) inside the same envelope, so the parse and the provenance checks are identical.
"""
import json
import re
import sys
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import score_deepseek_production as sdp  # noqa: E402

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 4096
PRICE_IN, PRICE_OUT = 1.00, 5.00          # Batch $/MTok, checked at the source 2026-10-21
CAP_USD = 5.00                            # owner, 2026-10-21
CONFIG = ROOT / "filters/human_thriving/v9/config.yaml"
PROMPT = ROOT / "filters/human_thriving/v9/prompt-compressed.md"
SET = ROOT / "datasets/canary/human_thriving/set.jsonl"
SKIP = "cross-family panel EXP-055 P2 (#177): evaluation only"
FENCE = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n?```\s*$", re.S)


def client():
    key = (Path.home() / ".config/anthropic/api_key").read_text().strip()
    return anthropic.Anthropic(api_key=key)


def setup():
    dims, field, version, _ = sdp.load_filter_spec(CONFIG)
    sdp.DIMENSIONS = dims
    template = PROMPT.read_text(encoding="utf-8")
    articles = [json.loads(l) for l in open(SET, encoding="utf-8")]
    return dims, field, template, sdp.prompt_sha256(template), articles


def params(template, article):
    return {"model": MODEL, "max_tokens": MAX_TOKENS, "thinking": {"type": "between_tools"},
            "messages": [{"role": "user", "content": sdp.build_prompt(template, article)}]}


def count(work):
    _, _, template, _, articles = setup()
    c = client()
    n = [c.messages.count_tokens(model=MODEL, thinking={"type": "between_tools"},
                                 messages=params(template, a)["messages"]).input_tokens for a in articles[:3]]
    avg = sum(n) / len(n)
    worst = len(articles) * (avg * PRICE_IN + MAX_TOKENS * PRICE_OUT) / 1e6
    likely = len(articles) * (avg * PRICE_IN + 1500 * PRICE_OUT) / 1e6
    out = {"counted": n, "avg_input": avg, "items": len(articles), "worst_usd": round(worst, 3),
           "likely_usd_at_1500_out": round(likely, 3), "cap_usd": CAP_USD}
    (Path(work) / "count.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out))
    return out


def submit(work):
    work = Path(work)
    est = json.loads((work / "count.json").read_text())
    if est["worst_usd"] > CAP_USD:
        raise SystemExit(f"REFUSED: worst case ${est['worst_usd']} > cap ${CAP_USD}")
    if (work / "batch.json").exists():
        raise SystemExit(f"REFUSED: {work}/batch.json exists; a batch was already submitted")
    _, _, template, _, articles = setup()
    for a in articles:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", a["id"]):
            raise SystemExit(f"id {a['id']!r} is not a valid custom_id")
    b = client().messages.batches.create(requests=[
        Request(custom_id=a["id"], params=MessageCreateParamsNonStreaming(**params(template, a))) for a in articles])
    (work / "batch.json").write_text(json.dumps({"id": b.id, "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime()), "n": len(articles)}))
    print(f"submitted batch {b.id}: {len(articles)} requests")


def collect(work):
    work = Path(work)
    bid = json.loads((work / "batch.json").read_text())["id"]
    c = client()
    b = c.messages.batches.retrieve(bid)
    if b.processing_status != "ended":
        raise SystemExit(f"batch {bid}: {b.processing_status} ({b.request_counts})")
    dims, field, _, sha, articles = setup()
    by_id = {a["id"]: a for a in articles}
    rows, tin, tout, bad = [], 0, 0, 0
    for r in c.messages.batches.results(bid):
        if r.result.type != "succeeded":
            rows.append({"id": r.custom_id, "error": f"batch result {r.result.type}"}); bad += 1
            continue
        m = r.result.message
        text = "".join(b.text for b in m.content if b.type == "text")
        f = FENCE.match(text)
        env = {"choices": [{"message": {"content": f.group(1) if f else text}}], "model": m.model,
               "usage": {"prompt_tokens": m.usage.input_tokens, "completion_tokens": m.usage.output_tokens}}
        tin += m.usage.input_tokens; tout += m.usage.output_tokens
        p = sdp.parse_response(env)
        if "error" in p:
            rows.append({"id": r.custom_id, "error": p["error"], "raw": p.get("raw", "")[:300],
                         "stop_reason": m.stop_reason}); bad += 1
            continue
        a = {d: {"score": p["dims"][d], "evidence": p["evidence"].get(d, "")} for d in dims}
        a.update(content_type=p["content_type"], scope_verdict=p["scope_verdict"],
                 dominant_subject=p["dominant_subject"], prompt_sha256=sha, prompt_hash=sha[:12],
                 served_model=p["served_model"], system_fingerprint=p["system_fingerprint"],
                 analyzed_by=f"claude-batch-{MODEL}", canary={"skipped": SKIP}, stop_reason=m.stop_reason,
                 analyzed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        rows.append({"id": r.custom_id, "title": by_id[r.custom_id].get("title", "")[:200], field: a,
                     "usage": env["usage"]})
    rows.sort(key=lambda x: x["id"])
    (work / "P2.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    cost = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
    print(f"P2: {len(rows) - bad} scored, {bad} failed; tokens in {tin:,} out {tout:,}; cost ${cost:.3f} (Batch card)")


if __name__ == "__main__":
    {"count": count, "submit": submit, "collect": collect}[sys.argv[1]](sys.argv[2])
