"""Oracle canary (#177): re-score a frozen set before every labelling run and refuse to label if the oracle moved.

Design and owner rulings: docs/proposals/oracle-canary-177.md. Bar and its derivation:
docs/evidence/2026-10-16-oracle-canary/PREREGISTRATION.md.

Files per filter:
  config/canary/<filter>.json           committed manifest of the frozen set (ids + sha256, no article text)
  config/canary/<filter>.baseline.json  committed baseline: per-item mean score, prompt_sha256, the noise bar
  datasets/canary/<filter>/set.jsonl    the article text (gitignored: the repo is public, the text is publishers')
  datasets/canary/<filter>/passes/      one record per canary run, keyed by prompt digest

A scorer calls `gate(prompt_sha256, skip_reason, oracle)` before its first oracle call. A baseline matches the prompt
by its RAW or STRIPPED digest (batch_scorer hashes the stripped template; review 2026-10-16 found it unguarded).
  - `skip_reason` given                                                       -> stamp {"skipped": reason}
  - no baseline for this prompt                                               -> stamp {"verdict": "no-set"} + banner
  - a baseline, but for ANOTHER oracle (model / endpoint / scorer)            -> REFUSE: no canary covers this oracle
  - the latest record is an unconsumed PASS younger than FRESH_HOURS          -> stamp {"verdict": "PASS"}, and the
    record is CONSUMED: one PASS admits one labelling run ("every labelling run", owner 2026-10-16)
  - anything else (no record, FAIL, NO-VERDICT, consumed, stale)              -> REFUSE
"""
import hashlib
import json
import statistics
import sys
import time
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config" / "canary"
DATA_DIR = ROOT / "datasets" / "canary"
FRESH_HOURS = 6          # backstop only: a PASS is single-use (consumed by the run it admits) AND at most this old
OP = 4.5
FLIP_MARGIN, SHIFT_MARGIN = 1, 0.15   # fixed in the pre-registration


class CanaryRefused(SystemExit):
    pass


def oracle_key(endpoint, model):
    """What a canary PASS covers: the endpoint (or scorer) and the model name a run REQUESTS. A PASS for one key
    never admits a run on another (review 2026-10-16: a flash PASS must not admit --model X or a Gemini base URL)."""
    return f"{endpoint}|{model}"


# --- scoring: the deploy gate's own arithmetic ---------------------------------------------------------------

def _gate_module():
    sys.path.insert(0, str(ROOT / "scripts" / "gate"))
    import ground_truth_gate as g  # noqa: E402
    return g


def spec_for(config_path):
    # load_scoring_spec returns None on ANY error, and its callers then fall back to nature_recovery's
    # weights -- silently the wrong filter. Here a missing spec raises.
    spec = _gate_module().load_scoring_spec(str(config_path))
    if spec is None:
        raise ValueError(f"no scoring spec in {config_path}")
    return spec


def run_scores(run_path, spec, field):
    """{id: weighted score} from one score_deepseek_production.py output file. Error/skip rows are absent."""
    g = _gate_module()
    out, stamps = {}, set()
    for line in open(run_path, encoding="utf-8"):
        r = json.loads(line)
        a = r.get(field)
        if not a:
            continue
        dims = {d: (v["score"] if isinstance(v, dict) else v) for d, v in a.items() if d in spec["dims"]}
        out[r["id"]] = g._wa(dims, spec)
        stamps.add((a.get("prompt_sha256"), a.get("served_model")))
    return out, stamps


# --- the comparison -------------------------------------------------------------------------------------------

def mean_scores(runs):
    ids = set.intersection(*(set(r) for r in runs))
    return {i: statistics.fmean(r[i] for r in runs) for i in ids}


def compare(canary, baseline, op=OP):
    """flips = verdict changes at the op-point; shift = mean signed delta. Over the items both carry."""
    ids = sorted(set(canary) & set(baseline))
    if not ids:
        raise ValueError("no common items")
    flips = sum((canary[i] >= op) != (baseline[i] >= op) for i in ids)
    shift = statistics.fmean(canary[i] - baseline[i] for i in ids)
    return {"n": len(ids), "flips": flips, "shift": round(shift, 4)}


def noise(base_runs, op=OP):
    """F1/S1: each run vs the mean of the others. F3/S3: each split of 6 runs into two triples (pre-registration)."""
    k1 = [compare(r, mean_scores([o for o in base_runs if o is not r]), op) for r in base_runs]
    idx = range(len(base_runs))
    k3 = []
    for t in combinations(idx, 3):
        rest = [i for i in idx if i not in t]
        if t[0] != 0:          # each split once
            continue
        k3.append(compare(mean_scores([base_runs[i] for i in t]), mean_scores([base_runs[i] for i in rest]), op))
    return {"k1": {"F": max(c["flips"] for c in k1), "S": max(abs(c["shift"]) for c in k1), "each": k1},
            "k3": {"F": max(c["flips"] for c in k3), "S": max(abs(c["shift"]) for c in k3), "each": k3}}


def verdict(cmp, bar):
    fail = cmp["flips"] > bar["F"] + FLIP_MARGIN or abs(cmp["shift"]) > bar["S"] + SHIFT_MARGIN
    return "FAIL" if fail else "PASS"


# --- the frozen set ---------------------------------------------------------------------------------------------

def verify_set(filter_name):
    """The set's bytes must match the committed manifest, or nothing it scores means anything."""
    man = json.load(open(CONFIG_DIR / f"{filter_name}.json"))
    p = DATA_DIR / filter_name / "set.jsonl"
    if not p.exists():
        raise CanaryRefused(f"CANARY: {p} missing — restore it from the lab (manifest set_sha256 "
                            f"{man['set_sha256'][:16]}…)")
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != man["set_sha256"]:
        raise CanaryRefused(f"CANARY: {p} sha256 {got[:16]}… != manifest {man['set_sha256'][:16]}…")
    return p, man


# --- the gate a scorer calls -------------------------------------------------------------------------------------

def baseline_for(prompt_sha256):
    for b in sorted(CONFIG_DIR.glob("*.baseline.json")):
        d = json.load(open(b))
        if prompt_sha256 in (d["prompt_sha256"], d.get("prompt_sha256_stripped")):
            return d
    return None


def record_path(filter_name, rec):
    return DATA_DIR / filter_name / "passes" / rec["record"]


def latest_record(filter_name, prompt_sha256):
    d = DATA_DIR / filter_name / "passes"
    recs = sorted(d.glob(f"{prompt_sha256[:16]}_*.json")) if d.exists() else []
    return json.load(open(recs[-1])) if recs else None


def gate(prompt_sha256, skip_reason=None, now=None, oracle=None):
    """oracle: the run's oracle key, e.g. "https://api.deepseek.com/chat/completions|deepseek-chat"."""
    now = time.time() if now is None else now
    if skip_reason:
        print(f"⚠️  CANARY SKIPPED: {skip_reason!r} — stamped on every label of this run")
        return {"skipped": skip_reason}
    b = baseline_for(prompt_sha256)
    if b is None:
        print(f"⚠️  CANARY: no frozen set for prompt {prompt_sha256[:12]}… — this run is NOT guarded against a "
              f"silent oracle change (#177). Stamping canary=no-set.")
        return {"verdict": "no-set"}
    if oracle != b.get("oracle"):
        raise CanaryRefused(
            f"REFUSED by the oracle canary (#177): prompt {prompt_sha256[:12]}… is guarded for oracle "
            f"{b.get('oracle')!r}, and this run uses {oracle!r} — no canary covers it.\n"
            f"  Override: --skip-canary \"<reason>\" (stamped on every label)")
    rec = latest_record(b["filter"], b["prompt_sha256"])
    age_h = (now - rec["time"]) / 3600 if rec else None
    if rec is None or rec["verdict"] != "PASS" or rec.get("consumed") or age_h > FRESH_HOURS:
        why = ("no canary run on record" if rec is None else
               f"the latest canary run is {rec['verdict']} ({rec.get('reason') or str(rec.get('flips')) + ' flips'})"
               if rec["verdict"] != "PASS" else
               f"the latest PASS was already used by a labelling run ({rec['consumed']['at_utc']})"
               if rec.get("consumed") else f"the latest PASS is {age_h:.1f} h old (> {FRESH_HOURS} h)")
        raise CanaryRefused(
            f"REFUSED by the oracle canary (#177): {why} for {b['filter']} prompt {prompt_sha256[:12]}….\n"
            f"  Run:      python scripts/oracle/canary.py run --filter {b['filter']}\n"
            f"  Override: --skip-canary \"<reason>\" (stamped on every label)")
    rec["consumed"] = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "oracle": oracle}
    p = record_path(b["filter"], rec)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1) + "\n")
    tmp.replace(p)                       # atomic: a second run sees it consumed, never half-written
    return {"verdict": "PASS", "record": rec["record"], "flips": rec["flips"], "shift": rec["shift"],
            "age_h": round(age_h, 2)}


def write_record(filter_name, prompt_sha256, result, served, now=None):
    now = time.time() if now is None else now
    d = DATA_DIR / filter_name / "passes"
    d.mkdir(parents=True, exist_ok=True)
    name = f"{prompt_sha256[:16]}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.json"
    rec = dict(result, time=now, record=name, prompt_sha256=prompt_sha256, served=sorted(served))
    (d / name).write_text(json.dumps(rec, indent=1) + "\n")
    return rec
