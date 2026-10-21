"""EXP-057: bands and paired deltas from the run's JSON (lab experiments/2026-10-21-obituary-maxrule-multiseed/run).
    python make_result.py > result.txt"""
import json, os
d = json.load(open(os.path.expanduser("~/lab/llm-distillery/experiments/2026-10-21-obituary-maxrule-multiseed/run/maxrule_multiseed.json")))
print(f"eval n={d['eval_n']} (leaked dropped {d['leaked_dropped']}), positives {d['positives']}; control seed42 vs shipped v5: {d['control_seed42_vs_shipped']}")
P = d["per_seed"]
for rule in ("full", "max_title_full", "max_title099_full"):
    r = [P[s][rule]["recall"] for s in P]; sp = [P[s][rule]["specificity"] for s in P]
    print(f"{rule:18s} recall band [{min(r):.4f}, {max(r):.4f}]  spec band [{min(sp):.4f}, {max(sp):.4f}]")
print("\npaired vs full, per seed (Δrecall / Δspecificity / ΔFP):")
for rule in ("max_title_full", "max_title099_full"):
    rows = [(s, P[s][rule]["recall"] - P[s]["full"]["recall"], P[s][rule]["specificity"] - P[s]["full"]["specificity"],
             P[s][rule]["fp"] - P[s]["full"]["fp"], P[s][rule]["tp"] - P[s]["full"]["tp"]) for s in P]
    print(f"  {rule}: " + "; ".join(f"seed {s}: {a:+.4f} / {b:+.4f} / {c:+d} FP, {t:+d} TP" for s, a, b, c, t in rows))
    print(f"    Δrecall range [{min(x[1] for x in rows):+.4f}, {max(x[1] for x in rows):+.4f}], positive at {sum(x[1] > 0 for x in rows)}/5;"
          f" Δspec range [{min(x[2] for x in rows):+.4f}, {max(x[2] for x in rows):+.4f}]")
