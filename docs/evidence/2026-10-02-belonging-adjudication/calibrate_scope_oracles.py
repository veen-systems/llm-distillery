#!/usr/bin/env python3
"""Belonging scope-oracle calibration: Gemini Flash vs DeepSeek V4.1 Flash vs Claude Opus 5.5, on the same prompt,
against the Claude-judge consensus (rubric_belonging_v2.md). See CALIBRATION.md.

    .venv/bin/python docs/evidence/2026-10-02-belonging-adjudication/calibrate_scope_oracles.py build
    .venv/bin/python docs/evidence/2026-10-02-belonging-adjudication/calibrate_scope_oracles.py run --oracle deepseek [--limit 5]
    .venv/bin/python docs/evidence/2026-10-02-belonging-adjudication/calibrate_scope_oracles.py analyse

build    the calibration set: every row judged under rubric v2 (pilots v2 and v3, both passes; their 4 controls are exemplar rows, kept once)
         and the v2 exemplars except B. Label = judge consensus (pilots) or Claude's exemplar code (exemplars); rows
         where the two passes split are kept with label `split` and reported apart. Each row carries the exact text
         the judges saw. Writes calib_key.jsonl (committed: ids + labels) and the gitignored calib_set.jsonl.
run      calls one oracle on every row not yet in its output (resume-safe), recording verdict, quote, reason, model,
         token usage and latency. A row whose reply is not a valid verdict is recorded with an `error`, never guessed.
analyse  per oracle: specificity and recall against the label (Wilson 95% intervals), per source set, the split rows,
         pairwise oracle agreement, and cost from the recorded tokens at the prices in PRICES (named per prompt).
"""
import argparse
import json
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "datasets" / "belonging_adjudication"
OUT = DATA / "calib"
VERDICTS = ["in_scope", "out_gift_official", "out_one_moment", "out_harm_is_story", "out_culture_topic",
            "out_event_spectated", "out_other", "cannot_judge"]
MODELS = {"gemini": "gemini-2.5-flash", "deepseek": "deepseek-chat", "claude": "claude-opus-5-5"}
# $ per 1M tokens, as recorded in memory/oracle-pricing-scheduling.md (Gemini, DeepSeek; DeepSeek OFF-PEAK
# cache-miss input) and the claude-api skill's model table (2026-09-25). Thinking tokens bill as output.
# Owner rulings made at calibration (2026-10-02, rubric v2.1): label overrides, and the rows rubric v2.1 now
# describes in its own examples (reported apart: an oracle reading v2.1 has been told the answer for them).
OWNER_OVERRIDES = {"pilot3:british_irish_bbc_northern_ireland_dc99721a35e2": "in"}
NAMED_IN_RUBRIC_V2_1 = {"pilot3:british_irish_bbc_northern_ireland_dc99721a35e2",
                        "exemplar:pan_african_alwihda_info_001ee450862f", "exemplar:new_zealand_rnz_ea40d98aca4b",
                        "exemplar:positive_news_upworthy_7475185b4e12", "exemplar:australian_abc_au_3e493327e09f",
                        "exemplar:belgian_gazet_van_antwerpen_c8ce317be3c6", "exemplar:new_zealand_rnz_5fff0c2b0765",
                        "exemplar:south_african_the_citizen_41a1e118ea3d"}
PRICES = {"gemini": (0.30, 2.50), "deepseek": (0.15, 0.60), "claude": (4.00, 20.00)}


def build():
    rows, key = [], []
    for pilot, keyfile in (("pilot2", "key_v2.jsonl"), ("pilot3", "key_v3.jsonl")):
        k = {json.loads(l)["id"]: json.loads(l) for l in open(HERE / keyfile)}
        verdicts, text = {}, {}
        for p in ("A1", "A2", "B1", "B2"):
            for l in open(DATA / pilot / p / "out.jsonl"):
                r = json.loads(l)
                verdicts.setdefault(r["id"], []).append(r["verdict"])
            for l in open(DATA / pilot / p / "input.jsonl"):
                r = json.loads(l)
                text[r["id"]] = r
        for i, kk in k.items():
            v = verdicts[i]
            if len(v) != 2:
                raise SystemExit(f"{pilot} {i}: {len(v)} verdicts, expected 2")
            a, b = (x == "in_scope" for x in v)
            label = ("in" if a else "out") if a == b else "split"
            if kk["stratum"] == "control":
                continue  # every control is also an exemplar row below; counting it twice would inflate n
            rows.append(dict(text[i], calib_id=f"{pilot}:{i}"))
            key.append(dict(calib_id=f"{pilot}:{i}", id=i, source_set=f"{pilot}_{kk['stratum']}", label=label,
                            label_kind="judge_consensus"))
    for l in open(DATA / "exemplars_v2_full.jsonl"):
        r = json.loads(l)
        if r["code"] == "B":
            continue
        rows.append(dict(id=r["id"], title=r["title"], url=r["url"], source=r["source"], content=r["content"],
                         calib_id=f"exemplar:{r['id']}"))
        key.append(dict(calib_id=f"exemplar:{r['id']}", id=r["id"], source_set="exemplar",
                        label="in" if r["code"] == "P" else "out", label_kind="claude_exemplar_owner_lines"))
    for k in key:
        if k["calib_id"] in OWNER_OVERRIDES:
            k.update(label=OWNER_OVERRIDES[k["calib_id"]], label_kind="owner_ruling_2026-10-02")
        k["named_in_rubric_v2_1"] = k["calib_id"] in NAMED_IN_RUBRIC_V2_1
    missing = (set(OWNER_OVERRIDES) | NAMED_IN_RUBRIC_V2_1) - {k["calib_id"] for k in key}
    if missing:
        raise SystemExit(f"override/named ids not in the set: {sorted(missing)}")
    ids = [k["calib_id"] for k in key]
    if len(set(ids)) != len(ids) or len({k["id"] for k in key}) != len(key):
        raise SystemExit("duplicate calib_id or the same article twice")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "calib_set.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(HERE / "calib_key.jsonl", "w") as f:
        for k in key:
            f.write(json.dumps(k) + "\n")
    from collections import Counter
    print(len(key), "rows;", dict(Counter(k["label"] for k in key)), dict(Counter(k["source_set"] for k in key)))


def prompt_for(row, rubric, template):
    return (template.replace("{RUBRIC}", rubric).replace("{TITLE}", row.get("title") or "")
            .replace("{SOURCE}", row.get("source") or "").replace("{CONTENT}", row.get("content") or ""))


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    d = json.loads(m.group(0))
    if d.get("verdict") not in VERDICTS:
        raise ValueError(f"verdict {d.get('verdict')!r} not a category")
    return d


def call(oracle, prompt, keys):
    t0 = time.time()
    if oracle == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=keys["gemini"])
        resp = client.models.generate_content(
            model=MODELS["gemini"], contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=1024,
                                               response_mime_type="application/json",
                                               thinking_config=types.ThinkingConfig(thinking_budget=0)))
        um = resp.usage_metadata
        usage = dict(input=um.prompt_token_count, output=(um.candidates_token_count or 0) + (um.thoughts_token_count or 0))
        return resp.text, usage, MODELS["gemini"], time.time() - t0
    if oracle == "deepseek":
        import requests
        from ground_truth.deepseek_models import assert_safe_deepseek_model
        assert_safe_deepseek_model(MODELS["deepseek"], "https://api.deepseek.com/v1/chat/completions")
        body = {"model": MODELS["deepseek"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.0,
                "max_tokens": 1024, "response_format": {"type": "json_object"}}
        for attempt in range(4):
            r = requests.post("https://api.deepseek.com/v1/chat/completions", json=body, timeout=120,
                              headers={"Authorization": f"Bearer {keys['deepseek']}"})
            if r.status_code == 200:
                j = r.json()
                u = j["usage"]
                usage = dict(input=u["prompt_tokens"], output=u["completion_tokens"],
                             cache_hit=u.get("prompt_cache_hit_tokens", 0))
                return j["choices"][0]["message"]["content"], usage, j.get("model", MODELS["deepseek"]), time.time() - t0
            if r.status_code in (401, 402, 403):
                raise RuntimeError(f"FATAL HTTP {r.status_code}: {r.text[:200]}")
            time.sleep(2 ** attempt)
        raise RuntimeError(f"HTTP {r.status_code} after retries")
    if oracle == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=keys["claude"])
        schema = {"type": "object", "additionalProperties": False, "required": ["verdict", "quote", "reason"],
                  "properties": {"verdict": {"type": "string", "enum": VERDICTS},
                                 "quote": {"type": "string"}, "reason": {"type": "string"}}}
        resp = client.messages.create(
            model=MODELS["claude"], max_tokens=4000, messages=[{"role": "user", "content": prompt}],
            extra_body={"output_config": {"effort": "low", "format": {"type": "json_schema", "schema": schema}}})
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"refusal: {getattr(resp, 'stop_details', None)}")
        text = next(b.text for b in resp.content if b.type == "text")
        usage = dict(input=resp.usage.input_tokens, output=resp.usage.output_tokens)
        return text, usage, resp.model, time.time() - t0
    raise SystemExit(f"unknown oracle {oracle}")


def run(oracle, limit, workers, rubric_file="rubric_belonging_v2_0.md", tag=""):
    from ground_truth.secrets_manager import get_secrets_manager
    sm = get_secrets_manager()
    import configparser  # DeepSeek is not in the secrets manager; read it as score_deepseek_production.py does
    cp = configparser.ConfigParser()
    cp.read(ROOT / "config" / "credentials" / "secrets.ini")
    keys = {"gemini": sm.get_llm_key("gemini"), "claude": sm.get_llm_key("claude"),
            "deepseek": cp.get("api_keys", "deepseek_api_key", fallback=None)}
    if not keys[oracle] and oracle != "claude":  # Claude: None lets the SDK resolve ANTHROPIC_API_KEY / an `ant` profile
        raise SystemExit(f"no API key for {oracle}")
    import hashlib
    rubric = (HERE / rubric_file).read_text()
    template = (HERE / "oracle_scope_prompt.md").read_text()
    prompt_sha = hashlib.sha256((rubric + "\x00" + template).encode()).hexdigest()[:16]
    rows = [json.loads(l) for l in open(OUT / "calib_set.jsonl")]
    out_path = OUT / f"{oracle}{tag}.jsonl"
    done = set()
    if out_path.exists():
        old = [json.loads(l) for l in open(out_path)]
        shas = {r.get("prompt_sha") for r in old if "error" not in r}
        if shas - {None, prompt_sha} or (None in shas and old):
            if not (shas == {None} and rubric_file == "rubric_belonging_v2_0.md"):
                raise SystemExit(f"{out_path.name} holds verdicts from a different prompt/rubric; use another --tag")
        done = {r["calib_id"] for r in old if "error" not in r}
    todo = [r for r in rows if r["calib_id"] not in done][: limit or None]
    print(f"{oracle}: {len(done)} done, {len(todo)} to call", flush=True)

    def one(r):
        rec = dict(calib_id=r["calib_id"], oracle=oracle, rubric_file=rubric_file, prompt_sha=prompt_sha,
                   ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        try:
            text, usage, model, secs = call(oracle, prompt_for(r, rubric, template), keys)
            rec.update(model=model, usage=usage, seconds=round(secs, 2), raw=text)
            d = parse(text)
            rec.update(verdict=d["verdict"], quote=d.get("quote", ""), reason=d.get("reason", ""))
        except Exception as e:  # recorded, never guessed; a rerun retries it
            rec["error"] = f"{type(e).__name__}: {e}"[:300]
            if "FATAL" in str(e):
                raise
        return rec

    with open(out_path, "a") as f:
        ex = ThreadPoolExecutor(max_workers=workers)
        try:
            for fut in as_completed([ex.submit(one, r) for r in todo]):
                rec = fut.result()
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
        finally:  # a FATAL (auth/balance) must not keep calling and billing the queued rows
            ex.shutdown(wait=True, cancel_futures=True)
    recs = [json.loads(l) for l in open(out_path)]
    print(f"{oracle}: {sum('error' not in r for r in recs)} ok, {sum('error' in r for r in recs)} error lines in file")


def import_subagents():
    """Claude oracle via Claude Code subagents (no Anthropic API key on this machine; owner, 2026-10-02).
    Five blind batches C1-C5 under calib/claude_subagent/, opaque ids mapped back by id_map.json. Writes claude.jsonl."""
    base = OUT / "claude_subagent"
    id_map = json.load(open(base / "id_map.json"))
    recs = []
    for b in sorted(base.glob("C*")):
        inp = [json.loads(l)["id"] for l in open(b / "input.jsonl")]
        out = [json.loads(l) for l in open(b / "out.jsonl")]
        if [r["id"] for r in out] != inp:
            raise SystemExit(f"{b.name}: ids are not the input ids in input order")
        for r in out:
            if r["verdict"] not in VERDICTS:
                raise SystemExit(f"{b.name}: {r['id']} verdict {r['verdict']!r}")
            recs.append(dict(calib_id=id_map[r["id"]], oracle="claude", model="claude-opus-5-5 (Claude Code subagent)",
                             usage=None, batch=b.name, verdict=r["verdict"], quote=r.get("quote", ""),
                             reason=r.get("reason", "")))
    if sorted(r["calib_id"] for r in recs) != sorted(id_map.values()):
        raise SystemExit("subagent outputs do not cover the calibration set exactly once")
    with open(OUT / "claude.jsonl", "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(recs), "claude rows imported")


def wilson(k, n):
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def analyse(tag="", exclude_named=False, labels="calib_key.jsonl"):
    key = {json.loads(l)["calib_id"]: json.loads(l) for l in open(HERE / labels)}
    print(f"labels: {labels}; {len(key)} rows")
    if exclude_named:
        print(f"(excluding {sum(k['named_in_rubric_v2_1'] for k in key.values())} rows named in rubric v2.1's examples)")
        key = {c: k for c, k in key.items() if not k["named_in_rubric_v2_1"]}
    res = {}
    for o in MODELS:
        p = OUT / f"{o}{tag}.jsonl"
        if not p.exists():
            continue
        latest = {}
        for l in open(p):
            r = json.loads(l)
            if "error" not in r:
                latest[r["calib_id"]] = r
        res[o] = latest
    for o, R in res.items():
        missing = [c for c in key if c not in R]
        print(f"\n=== {o} ({MODELS[o]}): {len(R)} judged, {len(missing)} missing")
        for scope_name, pred in (("all", lambda k: True), ("pilots only", lambda k: k["source_set"] != "exemplar")):
            pos = [c for c, k in key.items() if k["label"] == "in" and pred(k) and c in R and R[c]["verdict"] != "cannot_judge"]
            neg = [c for c, k in key.items() if k["label"] == "out" and pred(k) and c in R and R[c]["verdict"] != "cannot_judge"]
            tp = sum(R[c]["verdict"] == "in_scope" for c in pos)
            tn = sum(R[c]["verdict"] != "in_scope" for c in neg)
            sl, sh = wilson(tn, len(neg))
            rl, rh = wilson(tp, len(pos))
            print(f"  [{scope_name}] specificity {tn}/{len(neg)} = {tn/max(1,len(neg)):.3f} [{sl:.3f}, {sh:.3f}]   "
                  f"recall {tp}/{len(pos)} = {tp/max(1,len(pos)):.3f} [{rl:.3f}, {rh:.3f}]")
        fp = [c for c, k in key.items() if k["label"] == "out" and c in R and R[c]["verdict"] == "in_scope"]
        fn = [c for c, k in key.items() if k["label"] == "in" and c in R and R[c]["verdict"] != "in_scope"]
        print(f"  false in ({len(fp)}): {fp}")
        print(f"  missed in ({len(fn)}): {fn}")
        cj = sum(r["verdict"] == "cannot_judge" for c, r in R.items() if c in key)
        print(f"  cannot_judge (excluded from both denominators): {cj}")
        split = [c for c, k in key.items() if k["label"] == "split" and c in R]
        print(f"  split rows: {[(c, R[c]['verdict']) for c in split]}")
        if any(not r.get("usage") for r in R.values()):
            print("  cost: no per-call token counts (Claude Code subagents; see CALIBRATION.md for subagent tokens)")
            print(f"  models seen: {sorted({r['model'] for r in R.values()})}")
            continue
        billed = [json.loads(l) for l in open(OUT / f"{o}{tag}.jsonl")]
        billed = [r for r in billed if r.get("usage")]  # every billed call, incl. rows whose reply failed to parse
        tin = sum(r["usage"]["input"] for r in billed)
        tout = sum(r["usage"]["output"] for r in billed)
        pi, po = PRICES[o]
        cost = tin / 1e6 * pi + tout / 1e6 * po
        print(f"  tokens in {tin:,} out {tout:,}; cost at list price ${cost:.3f} "
              f"(${cost/max(1,len(R))*1000:.2f} per 1,000 articles, THIS prompt: rubric v2 + article, judge text)")
        print(f"  models seen: {sorted({r['model'] for r in R.values()})}")
    names = list(res)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = res[names[i]], res[names[j]]
            common = [c for c in key if c in a and c in b]
            agree = sum((a[c]["verdict"] == "in_scope") == (b[c]["verdict"] == "in_scope") for c in common)
            print(f"agreement {names[i]} vs {names[j]} (binary): {agree}/{len(common)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run")
    r.add_argument("--oracle", required=True, choices=list(MODELS))
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--rubric", default="rubric_belonging_v2_0.md")
    r.add_argument("--tag", default="")
    an = sub.add_parser("analyse")
    an.add_argument("--tag", default="")
    an.add_argument("--exclude-named", action="store_true")
    an.add_argument("--labels", default="calib_key.jsonl", help="calib_key_v2_1.jsonl = the blind v2.1 relabel")
    sub.add_parser("import-subagents")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.oracle, a.limit, a.workers, a.rubric, a.tag)
    elif a.cmd == "analyse":
        analyse(a.tag, a.exclude_named, a.labels)
    else:
        {"build": build, "import-subagents": import_subagents}[a.cmd]()
