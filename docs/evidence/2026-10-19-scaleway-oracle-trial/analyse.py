"""Scaleway oracle trial (2026-10-19): every figure in README.md, recomputed from the lab copies.

    PYTHONPATH=. python docs/evidence/2026-10-19-scaleway-oracle-trial/analyse.py > docs/evidence/2026-10-19-scaleway-oracle-trial/result.txt
"""
import collections
import json
import os
import statistics as st
from pathlib import Path

from ground_truth import oracle_canary as oc

LAB = Path(os.environ.get("LD_LAB", Path.home() / "lab" / "llm-distillery")).expanduser()
RAW = LAB / "experiments/2026-10-19-scaleway-oracle-trial/raw"
b = json.load(open(oc.CONFIG_DIR / "human_thriving.baseline.json"))
spec = oc.spec_for(b["config"])


def usage(rows):
    u = [r.get("usage") or {} for r in rows]
    return {"in": sum(x.get("prompt_tokens", 0) for x in u), "out": sum(x.get("completion_tokens", 0) for x in u),
            "cached": sum((x.get("prompt_tokens_details") or {}).get("cached_tokens") or 0 for x in u),
            "reasoning": sum((x.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for x in u)}


print("== probe (5 articles; one article per DeepSeek thinking switch)")
for name in ("scw_probe.jsonl", "scw_probe_r2.jsonl"):
    for r in map(json.loads, open(RAW / name)):
        u = r.get("usage") or {}
        print(f"{r['model_req']:<24} {r['arm']:<22} {r['id'][:28]:<28} {r['status']} {str(r.get('parse')):<12} "
              f"out {u.get('completion_tokens')} reasoning {(u.get('completion_tokens_details') or {}).get('reasoning_tokens')} "
              f"model {r.get('model')} fingerprint {r.get('system_fingerprint')}")
probe = [json.loads(l) for n in ("scw_probe.jsonl", "scw_probe_r2.jsonl") for l in open(RAW / n)]
print("probe usage", usage(probe), "calls", len(probe))

print("\n== 100-item set (human_thriving canary set, baseline = DeepSeek API B1-B6 mean, op 4.5)")
for name in ("scw_ds_none_R1.jsonl", "scw_mistral_R1.jsonl"):
    rows = [json.loads(l) for l in open(RAW / name)]
    s, stamps = oc.run_scores(RAW / name, spec, "human_thriving_analysis")
    c = oc.compare(s, b["items"], b["op"])
    d = [abs(s[i] - b["items"][i]) for i in s]
    errs = collections.Counter(r["error"].split(":")[0] for r in rows if "error" in r)
    print(f"{name}: n {c['n']}  flips {c['flips']}  shift {c['shift']:+.4f}  median|d| {st.median(d):.2f}  "
          f"max|d| {max(d):.2f}  pass>={b['op']}: model {sum(v >= b['op'] for v in s.values())} / baseline "
          f"{sum(b['items'][i] >= b['op'] for i in s)}  served {sorted({m for _, m in stamps})}")
    print(f"   calls {len(rows)}  errors {dict(errs)}  usage {usage(rows)}")
    if c["n"] == len(b["items"]):
        print(f"   as a k=1 canary: {oc.verdict(c, b['noise']['k1'])} (bar flips > {b['noise']['k1']['F']} + "
              f"{oc.FLIP_MARGIN} or |shift| > {b['noise']['k1']['S']} + {oc.SHIFT_MARGIN})")

print("\n== /v1/models (saved 2026-10-19, after the runs)")
models = json.load(open(RAW.parent / "models/v1_models_2026-10-19.json"))
print("ids", sorted(m["id"] for m in models["data"] if "deepseek" in m["id"] or "mistral-medium" in m["id"]))

# ESTIMATE, not billing: infra's reading of Scaleway's list price, no cache discount; USD/EUR assumed.
EUR_IN, EUR_OUT, USD_PER_EUR, DEEPSEEK_CANARY_USD = 0.60, 1.80, 1.16, 0.03   # EXP-052 README: about $0.03 per canary
print("\n== cost estimate (list price, no cache discount)")
allrows = probe + [json.loads(l) for n in ("scw_ds_none_R1.jsonl", "scw_mistral_R1.jsonl") for l in open(RAW / n)]
u = usage(allrows)
eur = (u["in"] * EUR_IN + u["out"] * EUR_OUT) / 1e6
ds = [json.loads(l) for l in open(RAW / "scw_ds_none_R1.jsonl")]
ud = usage(ds)
eur_canary = (ud["in"] * EUR_IN + ud["out"] * EUR_OUT) / 1e6
print(f"all calls {len(allrows)}: EUR {eur:.2f}")
print(f"one 100-item DeepSeek canary here: EUR {eur_canary:.2f} = USD {eur_canary * USD_PER_EUR:.2f} "
      f"= {eur_canary * USD_PER_EUR / DEEPSEEK_CANARY_USD:.0f}x DeepSeek API's ${DEEPSEEK_CANARY_USD}")
