"""Oracle canary CLI (#177). Library and rules: ground_truth/oracle_canary.py.

  baseline  python scripts/oracle/canary.py baseline --filter human_thriving --runs B1.jsonl ... B6.jsonl --k-ship 3
            -> config/canary/<filter>.baseline.json (per-item mean score + the noise bar; commit it)
  evaluate  python scripts/oracle/canary.py evaluate --filter human_thriving --runs X1.jsonl [X2 X3]
            -> prints flips / shift / PASS|FAIL against the bar for k = number of runs; writes nothing
  run       python scripts/oracle/canary.py run --filter human_thriving
            -> scores the frozen set k_ship times with the baseline's prompt, evaluates, writes a pass record
               under datasets/canary/<filter>/passes/; exit 0 PASS, 1 FAIL. This is what a scorer's gate reads.
"""
import argparse, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ground_truth import analysis_field_name  # noqa: E402
from ground_truth import oracle_canary as oc  # noqa: E402

import yaml  # noqa: E402

MAX_PASSES = 4


def field_of(config):
    return analysis_field_name(yaml.safe_load(open(config))["filter"]["name"])


def load_runs(paths, spec, field, want_sha=None):
    runs, stamps = [], set()
    for p in paths:
        s, st = oc.run_scores(p, spec, field)
        runs.append(s); stamps |= st
    shas = {a for a, _ in stamps}
    if len(shas) != 1 or (want_sha and shas != {want_sha}):
        raise SystemExit(f"FATAL: runs carry prompt_sha256 {shas}, expected one{' = ' + want_sha if want_sha else ''}")
    return runs, stamps


def cmd_baseline(a):
    man = json.load(open(oc.CONFIG_DIR / f"{a.filter}.json"))
    spec, field = oc.spec_for(a.config), field_of(a.config)
    runs, stamps = load_runs(a.runs, spec, field)
    if len({m for _, m in stamps}) != 1:
        raise SystemExit(f"FATAL: baseline runs were served by more than one model: {stamps}")
    ids = {i["id"] for i in man["items"]}
    short = [p for p, r in zip(a.runs, runs) if set(r) != ids]
    if short:
        raise SystemExit(f"FATAL: runs missing items (resume them first): {short}")
    nz = oc.noise(runs)
    sha = next(iter(stamps))[0]
    text = (ROOT / a.prompt).read_text(encoding="utf-8")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != sha:
        raise SystemExit(f"FATAL: {a.prompt} is not the prompt the baseline runs were scored with")
    out = {"filter": a.filter, "config": a.config, "prompt": a.prompt, "prompt_sha256": sha,
           # batch_scorer hashes the stripped template: the same prompt must be recognised there too
           "prompt_sha256_stripped": hashlib.sha256(text.strip().encode("utf-8")).hexdigest(),
           "oracle": oc.oracle_key(a.base_url, a.model),
           "served_model": next(iter(stamps))[1], "set_sha256": man["set_sha256"], "op": oc.OP,
           "k_ship": a.k_ship, "runs": [{"file": Path(p).name, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()}
                                        for p in a.runs],
           "noise": {k: {"F": v["F"], "S": v["S"]} for k, v in nz.items()},
           "items": {i: round(s, 4) for i, s in sorted(oc.mean_scores(runs).items())}}
    p = oc.CONFIG_DIR / f"{a.filter}.baseline.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    for k in ("k1", "k3"):
        print(f"noise {k}: F={nz[k]['F']} S={nz[k]['S']:.4f}  each: "
              + " ".join(f"{c['flips']}/{c['shift']:+.3f}" for c in nz[k]["each"]))
    above = sum(s >= oc.OP for s in out["items"].values())
    print(f"baseline: {len(out['items'])} items, {above} at >= {oc.OP}; served {out['served_model']}; wrote {p}")


def evaluate(filter_name, run_paths):
    b = json.load(open(oc.CONFIG_DIR / f"{filter_name}.baseline.json"))
    spec, field = oc.spec_for(ROOT / b["config"]), field_of(ROOT / b["config"])   # cwd-independent
    runs, stamps = load_runs(run_paths, spec, field)
    k = {1: "k1", 3: "k3"}.get(len(runs))
    if k is None:
        raise SystemExit("FATAL: the bar exists for k = 1 and k = 3 only")
    cmp = oc.compare(oc.mean_scores(runs), b["items"])
    if cmp["n"] != len(b["items"]):
        raise SystemExit(f"FATAL: {cmp['n']} of {len(b['items'])} items scored; an incomplete canary is not a verdict")
    v = oc.verdict(cmp, b["noise"][k])
    return dict(cmp, k=len(runs), bar=b["noise"][k], verdict=v), stamps, b


def cmd_evaluate(a):
    res, stamps, _ = evaluate(a.filter, a.runs)
    print(f"{res['verdict']}  flips {res['flips']} (bar {res['bar']['F']} + {oc.FLIP_MARGIN})  "
          f"shift {res['shift']:+.4f} (bar {res['bar']['S']:.4f} + {oc.SHIFT_MARGIN})  k={res['k']}  "
          f"stamps {sorted(stamps)}")


def cmd_run(a):
    b = json.load(open(oc.CONFIG_DIR / f"{a.filter}.baseline.json"))
    endpoint, model = b["oracle"].rsplit("|", 1)

    def no_verdict(reason):
        # A canary that cannot reach a verdict must not leave an OLDER PASS standing (review 2026-10-16).
        oc.write_record(a.filter, b["prompt_sha256"], {"verdict": "NO-VERDICT", "reason": reason}, set())
        raise SystemExit(f"FATAL: {reason}; recorded NO-VERDICT, so no labelling run is admitted")

    set_path, _ = oc.verify_set(a.filter)
    with tempfile.TemporaryDirectory() as td:
        paths = []
        want = set(b["items"])
        for i in range(b["k_ship"]):
            out = Path(td) / f"canary_{i}.jsonl"
            # The scorer exits 1 when any row errored, and the oracle returns malformed JSON on ~1% of rows
            # (2026-10-16: 20 malformed rows in 1,520 calls, concentrated on a few articles). Resume -- the scorer
            # skips ids already scored -- until every item is in; otherwise no verdict.
            for attempt in range(1, MAX_PASSES + 1):
                r = subprocess.run([sys.executable, str(ROOT / "scripts/score_deepseek_production.py"), "--input",
                                    str(set_path), "--output", str(out), "--config", str(ROOT / b["config"]),
                                    "--prompt", str(ROOT / b["prompt"]), "--model", model, "--base-url", endpoint,
                                    "--concurrency", "8", "--skip-canary", "canary self-run"])
                if r.returncode == 2:
                    no_verdict("the scorer aborted the run (account or endpoint)")
                done = ({json.loads(l)["id"] for l in open(out) if "error" not in json.loads(l)}
                        if out.exists() else set())
                if want <= done:
                    break
            else:
                no_verdict(f"{len(want - done)} items still unscored after {MAX_PASSES} passes")
            paths.append(out)
        res, stamps, _ = evaluate(a.filter, paths)
    if {s for s, _ in stamps} != {b["prompt_sha256"]}:
        no_verdict("the canary scored a different prompt than its baseline")
    served = {m for _, m in stamps}
    if served != {b["served_model"]}:
        # Flips cannot see a reroute that happens to score alike; the served model is checked directly.
        res = dict(res, verdict="FAIL", reason=f"served {sorted(served)} != baseline {b['served_model']!r}")
    rec = oc.write_record(a.filter, b["prompt_sha256"], res, stamps)
    print(f"CANARY {res['verdict']}: flips {res['flips']}, shift {res['shift']:+.4f}, k={res['k']}"
          + (f" ({res['reason']})" if res.get("reason") else "") + f"; record {rec['record']}")
    sys.exit(0 if res["verdict"] == "PASS" else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("baseline"); s.add_argument("--filter", required=True); s.add_argument("--runs", nargs="+", required=True)
    s.add_argument("--config", required=True); s.add_argument("--prompt", required=True)
    s.add_argument("--k-ship", type=int, choices=(1, 3), required=True)
    s.add_argument("--base-url", default="https://api.deepseek.com/v1/chat/completions",
                   help="the endpoint the baseline runs used (score_deepseek_production.py's default)")
    s.add_argument("--model", default="deepseek-chat", help="the model the baseline runs REQUESTED")
    s = sub.add_parser("evaluate"); s.add_argument("--filter", required=True); s.add_argument("--runs", nargs="+", required=True)
    s = sub.add_parser("run"); s.add_argument("--filter", required=True)
    a = ap.parse_args()
    {"baseline": cmd_baseline, "evaluate": cmd_evaluate, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
