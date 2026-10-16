"""Re-derive every #177 result from the lab copies of the 15 runs (PREREGISTRATION.md).

    .venv/bin/python docs/evidence/2026-10-16-oracle-canary/analyse.py > docs/evidence/2026-10-16-oracle-canary/result.txt

Checks first that the six baseline files in the lab are the bytes config/canary/human_thriving.baseline.json was
built from (its `runs` sha256 list), then recomputes the noise floor and evaluates P (must FAIL), C (must PASS) and
V (power reading) at k = 1 and k = 3 with ground_truth/oracle_canary.py -- the code the scorers' gate runs.
"""
import hashlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
from ground_truth import oracle_canary as oc  # noqa: E402
import canary as cli  # noqa: E402

LAB = Path(os.environ.get("LD_LAB", Path.home() / "lab" / "llm-distillery")).expanduser()
RUNS = LAB / "experiments/2026-10-16-oracle-canary/runs"
b = json.load(open(oc.CONFIG_DIR / "human_thriving.baseline.json"))
for r in b["runs"]:
    got = hashlib.sha256((RUNS / r["file"]).read_bytes()).hexdigest()
    if got != r["sha256"]:
        raise SystemExit(f"FATAL: {r['file']} in the lab is not the file the baseline was built from")
spec, field = oc.spec_for(b["config"]), cli.field_of(b["config"])
base = [oc.run_scores(RUNS / f"B{i}.jsonl", spec, field)[0] for i in range(1, 7)]
nz = oc.noise(base)
print(f"baseline: 6 runs, prompt {b['prompt_sha256'][:12]}, served {b['served_model']}, "
      f"{sum(s >= oc.OP for s in b['items'].values())}/{len(b['items'])} items >= {oc.OP}, k_ship {b['k_ship']}")
for k in ("k1", "k3"):
    print(f"noise {k}: F={nz[k]['F']} S={nz[k]['S']:.4f}  (each: "
          + ", ".join(f"{c['flips']}/{c['shift']:+.3f}" for c in nz[k]["each"]) + ")")
print(f"bar: FAIL iff flips > F + {oc.FLIP_MARGIN} or |shift| > S + {oc.SHIFT_MARGIN}")
for arm in ("P", "C", "V"):
    for i in (1, 2, 3):
        res, _, _ = cli.evaluate("human_thriving", [RUNS / f"{arm}{i}.jsonl"])
        print(f"{arm}{i} k=1: {res['verdict']}  flips {res['flips']}  shift {res['shift']:+.4f}")
    res, _, _ = cli.evaluate("human_thriving", [RUNS / f"{arm}{i}.jsonl" for i in (1, 2, 3)])
    print(f"{arm} k=3: {res['verdict']}  flips {res['flips']}  shift {res['shift']:+.4f}")
