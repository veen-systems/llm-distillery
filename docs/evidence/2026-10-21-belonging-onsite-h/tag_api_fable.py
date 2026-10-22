"""Tag `focus` with a cloud model, same system.txt + user message shape as tag_qwen.py. Resumable by id.
usage: python3 tag_api.py <dir> fable|mistral [limit]   (reads <dir>/input.jsonl + system.txt, appends <dir>/out.jsonl)
Fable: claude-fable-5-1, effort low, no fallbacks (a fallback model would be a different instrument), refusal -> focus null.
Mistral: mistral-large-4-0, temperature 0, JSON mode. Keys read from ~/.config/{anthropic,mistral}/api_key, never exported."""
import json, sys, os, urllib.request
d, which = sys.argv[1], sys.argv[2]; limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
system = open(os.path.join(d, "system.txt")).read()
outp = os.path.join(d, "out.jsonl")
done = {json.loads(l)["id"] for l in open(outp)} if os.path.exists(outp) else set()
key = open(os.path.expanduser(f"~/.config/{'anthropic' if which == 'fable' else 'mistral'}/api_key")).read().strip()
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["focus", "quote", "reason"],
          "properties": {"focus": {"type": "string", "enum": ["personal", "group"]}, "quote": {"type": "string"}, "reason": {"type": "string"}}}
if which == "fable":
    import anthropic
    client = anthropic.Anthropic(api_key=key)
n = 0
for line in open(os.path.join(d, "input.jsonl")):
    r = json.loads(line)
    if r["id"] in done: continue
    if limit is not None and n >= limit: break
    user = f"Title: {r['title']}\n\nContent:\n{r['content']}"
    usage = None
    if which == "fable":
        model = "claude-fable-5-1"
        resp = client.messages.create(model=model, max_tokens=16000, system=system,
                                      output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
                                      messages=[{"role": "user", "content": user}])
        usage = {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens, "stop": resp.stop_reason}
        raw = next((b.text for b in resp.content if b.type == "text"), "")
    else:
        model = "mistral-large-4-0"
        body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        req = urllib.request.Request("https://api.mistral.ai/v1/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        resp = json.load(urllib.request.urlopen(req, timeout=600))
        raw = resp["choices"][0]["message"]["content"]
        usage = {"in": resp["usage"]["prompt_tokens"], "out": resp["usage"]["completion_tokens"]}
    try: v = json.loads(raw)
    except Exception: v = {"focus": None, "raw": raw}
    rec = {"id": r["id"], "focus": v.get("focus"), "quote": v.get("quote"), "reason": v.get("reason"), "model": model, "usage": usage}
    with open(outp, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(r["id"], rec["focus"], usage, flush=True); n += 1
print("DONE", flush=True)
