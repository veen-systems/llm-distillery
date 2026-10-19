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
