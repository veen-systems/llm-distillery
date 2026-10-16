"""The pre-registered recompute (#176): v9's gate with A1's leaked rows EXCLUDED, through the gate's own code.

    .venv/bin/python gate_excluded.py SCRATCH_DIR > gate_excluded.txt

Runs scripts/gate/ground_truth_gate.py exactly as docs/evidence/2026-09-25-v8-adj-retrain-gate/ did (adjudicated
labels = human_thriving_v8_adj1/test.jsonl, --recompute-model-wa, op 4.5, gatekeeper cap 3.0, floor 0.16; arms v8
and adj3 = v9) twice: on ALL 660 rows — a CONTROL that must reproduce gate_adjudicated.json's tp/fp/tn/fn for both
arms, or nothing else is read — and with EXCLUDE removed from labels and both score files. Then applies that gate's
pre-registered WIN rule (retrain spec lo > v8 spec hi AND retrain recall hi >= v8 recall lo).

EXCLUDE is the UNION of both leak instruments (README.md): the 5 that classify_pairs.py's full-text share calls a
leak (one is a template — NYT Connections, different puzzle) plus AIM-9X (an agency rewrite at share 0.13 that a
reader calls the same article). The union is the conservative set: more rows out than either instrument alone.
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
EXCLUDE = {
    "community_social_hackernews_front_277debae3939", "us_media_mashable_c3886fc7158b",
    "east_asian_japan_today_7c585120c422", "science_helmholtz_23e36b84ee95",
    "science_sciencedaily_0959ebb7b676", "east_asian_yonhap_en_8e7f2a520a1a",
}
LABELS = ROOT / "datasets/training/human_thriving_v8_adj1/test.jsonl"
ARMS = {a: ROOT / f"datasets/gate/ht_v8_adj_2026-09-25/{a}/scores_calibrated.jsonl" for a in ("v8", "adj3")}
PUBLISHED = json.load(open(ROOT / "docs/evidence/2026-09-25-v8-adj-retrain-gate/gate_adjudicated.json"))["models"]


def filtered(src, tag):
    rows = [json.loads(l) for l in open(src) if l.strip()]
    keep = [r for r in rows if r["id"] not in EXCLUDE]
    if len(rows) - len(keep) != len(EXCLUDE):
        raise SystemExit(f"FATAL: {src} holds {len(rows) - len(keep)} of the {len(EXCLUDE)} excluded ids")
    p = OUT / f"{tag}_{src.parent.name}_{src.name}"
    p.write_text("".join(json.dumps(r) + "\n" for r in keep))
    return p


def gate(labels, arms, report):
    cmd = [sys.executable, str(ROOT / "scripts/gate/ground_truth_gate.py"), "--labels", str(labels),
           "--config", str(ROOT / "filters/human_thriving/v9/config.yaml"), "--threshold", "4.5",
           "--gatekeeper-cap", "3.0", "--noise-floor", "0.16", "--recompute-model-wa", "--report", str(report)]
    for a, p in arms.items():
        cmd += ["--model", f"{a}={p}"]
    subprocess.run(cmd, check=True, capture_output=True)
    return json.load(open(report))["models"]


def line(tag, m):
    return (f"  {tag:5} n={m['n']} pos={m['positives']} tp={m['tp']} fp={m['fp']} tn={m['tn']} fn={m['fn']}  "
            f"spec {m['specificity']:.4f} [{m['specificity_band'][0]:.4f}, {m['specificity_band'][1]:.4f}]  "
            f"recall {m['recall']:.4f} [{m['recall_band'][0]:.4f}, {m['recall_band'][1]:.4f}]")


allm = gate(LABELS, ARMS, OUT / "all.json")
print("CONTROL — all 660 rows vs the published gate_adjudicated.json:")
for a in ARMS:
    got = {k: allm[a][k] for k in ("tp", "fp", "tn", "fn")}
    want = {k: PUBLISHED[a][k] for k in ("tp", "fp", "tn", "fn")}
    print(line(a, allm[a]), " REPRODUCES" if got == want else f" MISMATCH published {want}")
    if got != want:
        raise SystemExit("FATAL: the control does not reproduce the published gate; nothing else is read")
exc = gate(filtered(LABELS, "x"), {a: filtered(p, "x") for a, p in ARMS.items()}, OUT / "excluded.json")
print(f"EXCLUDED — {len(EXCLUDE)} leak rows removed:")
for a in ARMS:
    print(line(a, exc[a]))
v8, r = exc["v8"], exc["adj3"]
win = r["specificity_band"][0] > v8["specificity_band"][1] and r["recall_band"][1] >= v8["recall_band"][0]
print(f"WIN rule on the excluded set: adj3 spec lo {r['specificity_band'][0]:.4f} > v8 spec hi "
      f"{v8['specificity_band'][1]:.4f} and adj3 recall hi {r['recall_band'][1]:.4f} >= v8 recall lo "
      f"{v8['recall_band'][0]:.4f} -> {'WIN (unchanged)' if win else 'NOT WIN'}")
