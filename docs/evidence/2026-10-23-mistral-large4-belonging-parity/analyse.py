"""EXP-060 analysis: M1-M3 against belonging's committed Gemini baseline, by the canary's own evaluate().
Usage (from the checkout): .venv/bin/python analyse.py RAW_DIR > result.txt"""
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
import canary  # noqa: E402
from ground_truth import oracle_canary as oc  # noqa: E402

PRICE_IN, PRICE_OUT, USD_PER_EUR = 1.36, 4.18, 1.16    # web aggregators via infra, UNVERIFIED; the bill is Mistral's page
raw = Path(sys.argv[1])
runs = [raw / f"M{i}.jsonl" for i in (1, 2, 3)]
b = json.load(open(ROOT / "config/canary/belonging.baseline.json"))
op = b["op"]

print(f"baseline: {b['oracle']} served {b['served_model']}, op {op}, "
      f"{sum(v >= op for v in b['items'].values())}/{len(b['items'])} at >= op")
print("\n== PRIMARY: mean of M1-M3, k=3 bar")
res, stamps, _ = canary.evaluate("belonging", [str(p) for p in runs])
print(f"{res['verdict']}  n {res['n']}  flips {res['flips']} (fail > {res['bar']['F']} + {oc.FLIP_MARGIN})  "
      f"shift {res['shift']:+.4f} (fail |.| > {res['bar']['S']:.4f} + {oc.SHIFT_MARGIN})  stamps {sorted(stamps)}")

print("\n== SECONDARY: each run alone, k=1 bar")
for p in runs:
    r, _, _ = canary.evaluate("belonging", [str(p)])
    print(f"{p.stem}: {r['verdict']}  flips {r['flips']}  shift {r['shift']:+.4f}")

spec, field = oc.spec_for(ROOT / b["config"]), canary.field_of(ROOT / b["config"])
scores = [oc.run_scores(p, spec, field)[0] for p in runs]
print("\n== Mistral against itself: each run vs the mean of the other two")
for i, s in enumerate(scores):
    c = oc.compare(s, oc.mean_scores([o for j, o in enumerate(scores) if j != i]), op)
    print(f"M{i+1}: flips {c['flips']}  shift {c['shift']:+.4f}   (Gemini's own k=1 F = {b['noise']['k1']['F']})")

m = oc.mean_scores(scores)
ids = sorted(set(m) & set(b["items"]))
up = sum(m[i] >= op and b["items"][i] < op for i in ids); down = sum(m[i] < op and b["items"][i] >= op for i in ids)
d = sorted(abs(m[i] - b["items"][i]) for i in ids)
print(f"\nflips by direction: Mistral passes / Gemini blocks {up}; Mistral blocks / Gemini passes {down}")
print(f"at >= op: Mistral mean {sum(m[i] >= op for i in ids)}, Gemini {sum(b['items'][i] >= op for i in ids)} (same {len(ids)} items)")
print(f"|delta| median {d[len(d)//2]:.2f}  max {d[-1]:.2f}")

print("\n== instrument")
for p in runs:
    rows = [json.loads(l) for l in open(p)]
    ok = [r for r in rows if "belonging_analysis" in r]
    tin = sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in rows)
    tout = sum((r.get("usage") or {}).get("completion_tokens", 0) for r in rows)
    reas = sum(((r.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens", 0) for r in rows)
    print(f"{p.stem}: calls {len(rows)}  scored {len(ok)}  errors {Counter(r['error'][:20] for r in rows if 'error' in r)}  "
          f"finish {Counter(r.get('finish_reason') for r in rows)}  served {Counter(r.get('served_model') for r in ok)}  "
          f"tokens in {tin:,} out {tout:,} reasoning {reas}")

allrows = [json.loads(l) for p in sorted(raw.glob("*.jsonl")) for l in open(p)]
tin = sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in allrows)
tout = sum((r.get("usage") or {}).get("completion_tokens", 0) for r in allrows)
usd = (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
calls = sum(1 for r in allrows if r.get("usage"))
print(f"\n== cost ESTIMATE (every call incl. probes, at ${PRICE_IN}/${PRICE_OUT} per M, UNVERIFIED price)")
print(f"billed calls {calls}  tokens in {tin:,} out {tout:,}  ${usd:.2f} ~ EUR {usd / USD_PER_EUR:.2f}")
mrows = [json.loads(l) for p in runs for l in open(p) if json.loads(l).get("usage")]
per = sum(r["usage"]["prompt_tokens"] * PRICE_IN + r["usage"]["completion_tokens"] * PRICE_OUT
          for r in mrows) / 1e6 / USD_PER_EUR / len(mrows)
print(f"per article (M1-M3 calls, reasoning off) EUR {per:.4f}  -> about {int(25.5 / per):,} articles "
      f"per EUR 25.50 monthly allowance")
