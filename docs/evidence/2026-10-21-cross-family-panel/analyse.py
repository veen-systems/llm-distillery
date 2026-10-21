"""EXP-055 analysis: the cross-family panel against the human_thriving oracle (#177 step 6). Measures and
controls as pre-registered in PREREGISTRATION.md (committed before any panel call).

    python docs/evidence/2026-10-21-cross-family-panel/analyse.py \
        --member P1=<lab>/P1.jsonl --member L1=<lab>/L1/results.jsonl ...

A member file is either score_deepseek_production.py output (scores under `human_thriving_analysis`) or
score_ollama_oracle.py output (`dims` at the root, one row per item per `run`). Scores go through the deploy
gate's own weighted average (oracle_canary.spec_for / ground_truth_gate._wa), the same arithmetic as the
oracle's baseline. Writes nothing; prints the report.
"""
import argparse
import json
import random
import statistics
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from ground_truth import oracle_canary as oc                      # noqa: E402
from ground_truth.agreement import cohen_kappa, gwet_ac1, krippendorff_alpha   # noqa: E402

FIELD = "human_thriving_analysis"
PROMPT_SHA = "c4705408c477a511e4b7835b24b8d6cc13c161e5e6f572739be67ed97be42dcd"
SELF_FLIP_BAR = 7          # the canary's fail line (EXP-052): a member noisier than this cannot judge
CONSTANT_BAR = 95          # a member passing or blocking >= 95 of 100 cannot disagree
PARSE_BAR = 0.95
GOOGLE = {"L2", "P1"}      # gemma3 and gemini: one family, reported both ways


def read_member(path, spec):
    """{run: {id: score}}, plus the prompt digests seen. Error rows are absent."""
    g = oc._gate_module()
    runs, shas = defaultdict(dict), set()
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if FIELD in r:
            a = r[FIELD]
            dims = {d: (v["score"] if isinstance(v, dict) else v) for d, v in a.items() if d in spec["dims"]}
            runs[1][r["id"]] = g._wa(dims, spec)
            shas.add(a.get("prompt_sha256"))
        elif r.get("dims"):
            runs[r.get("run", 1)][r["id"]] = g._wa({d: r["dims"][d] for d in spec["dims"]}, spec)
            shas.add(r.get("prompt_sha256"))
    return dict(runs), shas


def spec_recall(pred, truth, ids):
    tp = sum(pred[i] and truth[i] for i in ids)
    tn = sum(not pred[i] and not truth[i] for i in ids)
    pos = sum(truth[i] for i in ids)
    neg = len(ids) - pos
    return (tn / neg if neg else float("nan")), (tp / pos if pos else float("nan")), pos, neg


def boot(pred, truth, ids, n=2000, seed=20261021):
    rng = random.Random(seed)
    s, r = [], []
    for _ in range(n):
        b = [rng.choice(ids) for _ in ids]
        sp, rc, pos, neg = spec_recall(pred, truth, b)
        if pos and neg:
            s.append(sp); r.append(rc)
    q = lambda v: (sorted(v)[int(0.025 * len(v))], sorted(v)[int(0.975 * len(v)) - 1])
    return q(s), q(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", action="append", required=True, help="ID=path")
    a = ap.parse_args()
    b = json.load(open(oc.CONFIG_DIR / "human_thriving.baseline.json"))
    assert b["prompt_sha256"] == PROMPT_SHA
    spec, op = oc.spec_for(ROOT / b["config"]), b["op"]
    items = sorted(b["items"])
    oracle = b["items"]

    print(f"EXP-055 — {len(items)} items, op {op}; oracle = 6-run baseline mean ({b['served_model']}), "
          f"{sum(oracle[i] >= op for i in items)} at >= op\n")
    members, eligible = {}, []
    print("member   runs  parsed  pass@op  self-flips  prompt  eligible")
    for spec_arg in a.member:
        mid, path = spec_arg.split("=", 1)
        runs, shas = read_member(path, spec)
        mean = oc.mean_scores(list(runs.values()))
        parsed = len(mean) / len(items)
        passes = sum(mean[i] >= op for i in mean)
        flips = (oc.compare(runs[1], runs[2], op)["flips"] if len(runs) >= 2 else None)
        ok = (parsed >= PARSE_BAR and CONSTANT_BAR > passes > len(mean) - CONSTANT_BAR
              and (flips is None or flips <= SELF_FLIP_BAR) and shas == {PROMPT_SHA})
        members[mid] = mean
        if ok:
            eligible.append(mid)
        print(f"{mid:8s} {len(runs):4d}  {parsed:6.2f}  {passes:7d}  {str(flips):>10s}  "
              f"{'ok' if shas == {PROMPT_SHA} else 'WRONG ' + str(shas):6s}  {'yes' if ok else 'NO'}")

    def units(ids_, who, binary):
        return [[(members[m][i] >= op if binary else members[m][i]) if i in members[m] else None for m in who]
                for i in ids_]

    print("\nKrippendorff alpha (nominal = pass/block at op; interval = weighted average)")
    members["ORACLE"] = oracle
    for label, who in [("panel (eligible)", eligible), ("panel + oracle", eligible + ["ORACLE"]),
                       ("panel, Google as one (P1 dropped)", [m for m in eligible if m != "P1"])]:
        if len(who) >= 2:
            print(f"  {label:36s} nominal {krippendorff_alpha(units(items, who, True)):.3f}   "
                  f"interval {krippendorff_alpha(units(items, who, False), 'interval'):.3f}   {who}")

    print("\nPairwise (pass/block): AC1 / kappa / raw, n")
    for x, y in combinations(eligible + ["ORACLE"], 2):
        ids = [i for i in items if i in members[x] and i in members[y]]
        ax, ay = [members[x][i] >= op for i in ids], [members[y][i] >= op for i in ids]
        print(f"  {x:6s} {y:6s}  AC1 {gwet_ac1(ax, ay, [True, False]):.3f}  kappa {cohen_kappa(ax, ay):.3f}  "
              f"raw {sum(p == q for p, q in zip(ax, ay)) / len(ids):.3f}  n={len(ids)}")

    print("\nOracle against the panel majority (eligible members, oracle left out)")
    for label, who in [("all eligible", eligible), ("Google as one (P1 dropped)", [m for m in eligible if m != "P1"])]:
        maj, ties = {}, 0
        for i in items:
            votes = [members[m][i] >= op for m in who if i in members[m]]
            if 2 * sum(votes) == len(votes):
                ties += 1
                continue
            maj[i] = 2 * sum(votes) > len(votes)
        ids = sorted(maj)
        if not who or not ids:
            print(f"  {label:28s} no eligible member — no majority")
            continue
        pred = {i: oracle[i] >= op for i in ids}
        sp, rc, pos, neg = spec_recall(pred, maj, ids)
        (sl, sh), (rl, rh) = boot(pred, maj, ids)
        print(f"  {label:28s} n={len(ids)} (ties {ties}), panel positive rate {pos / len(ids):.2f} ({pos})\n"
              f"    oracle SPECIFICITY {sp:.3f} [{sl:.3f}, {sh:.3f}]   recall {rc:.3f} [{rl:.3f}, {rh:.3f}]  "
              f"(priority: specificity, ADR-023)")
        fp = [i for i in ids if pred[i] and not maj[i]]
        fn = [i for i in ids if not pred[i] and maj[i]]
        print(f"    oracle passes the panel blocks: {len(fp)}; oracle blocks the panel passes: {len(fn)}")
        print(f"    mean signed (oracle - panel mean score): "
              f"{statistics.fmean(oracle[i] - statistics.fmean(members[m][i] for m in who if i in members[m]) for i in ids):+.3f}")


if __name__ == "__main__":
    main()
