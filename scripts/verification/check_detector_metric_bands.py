#!/usr/bin/env python3
"""Every detector metric in a shipped artifact is a BAND, or says out loud that it is not.

llm-distillery**#158**: `early_stopping=True` lets `random_state` choose the internal validation
split, so a head trained with everything else fixed is one draw. Measured (`EXP-033`/`EXP-034`):
obituary heldout recall at the live 0.85 op-point spans **0.6599-0.8081** across five seeds, and
v3/v4/v5 finish in three different orders. Every number published before 2026-09-17 was one draw
and nothing in the artifact said so.

⛔ **THE CHECK IS ON THE ARTIFACT, NOT ON THE PROSE.** A rule written in a doc is a rule nobody
runs. This reads TWO sites and requires, for every published metric:

  * a `<metric>_band` sibling carrying min/median/max and the SEEDS it was computed over, and a
    `seed_set` matching those seeds -- or
  * an explicit `single_seed` declaration naming the seed and the issue.

⭐ The second branch is not a loophole: it is how a pre-#158 artifact tells the truth about itself
without being retrained. An artifact that says "this is one draw from seed 42" is honest; one that
publishes 0.6002 bare is not. ⛔ A NEW build cannot reach for it silently -- the trainers write
bands now, so `single_seed` only ever appears where a human put it.

⭐ **BOTH SITES, and the second one is the one that ships.** `models/` is gitignored for the
obituary detector (the pickles are out-of-band), so `v{3,4,5}/models/training_config.json` exists
only on the boxes that built it -- while `v{N}/calibration_report.json` is TRACKED and embeds the
same numbers under `training_config`. Checking only `models/` would have left every copy a reader
can actually open unguarded. ⚠️ The two copies are written by one trainer in one run, so they
cannot drift on their own; they can only be edited apart by hand.

⚠️ WHAT THIS DOES NOT CHECK: whether the band is CORRECT, whether the seed set is a good one, or
whether anybody read it. It converts "nobody thought to ask" into "the file has to answer".

    python3 scripts/verification/check_detector_metric_bands.py
    python3 scripts/verification/check_detector_metric_bands.py --root <dir>

Exit 0 when every artifact passes, 1 otherwise -- including when it examined NO artifact, which in
this repo is the signature failure of a guard that reports success because it looked at nothing.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: A published metric: the key claims model quality AND the value is a rate.
#: ⛔ The prefix alone is not enough, and the first version of this file proved it by flagging
#: `test_samples: 190` — a COUNT — as an unbanded metric. A name is an assertion, and `test_` is
#: an assertion about the SPLIT, not about what the number measures.
#: ⚠️ STATED LIMIT: a rate stored as the integer 0 or 1 is not seen. That is deliberate — the
#: alternative is a denylist of count-shaped names, and a denylist is the shape this repo keeps
#: getting wrong. A saturated metric that matters should be written as a float.
METRIC_KEY = re.compile(r"^(?:oof|test|heldout|val)_.*", re.I)
BAND_KEYS = ("min", "median", "max", "seeds")
ISSUE = "llm-distillery#158"


def published_metrics(cfg: dict) -> list:
    """Keys that claim a quality number. A band is a dict, so it can never be one itself."""
    return sorted(k for k, v in cfg.items()
                  if METRIC_KEY.match(k) and isinstance(v, float)
                  and 0.0 <= v <= 1.0 and not k.endswith("_band"))


def sites(root: Path):
    """[(path, label, config)] — every place a detector publishes quality numbers."""
    out = []
    for f in sorted(root.glob("**/models/training_config.json")):
        try:
            cfg = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            out.append((f, "training_config.json", exc))
            continue
        out.append((f, "training_config.json", cfg))
    for f in sorted(root.glob("**/calibration_report.json")):
        try:
            rep = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            out.append((f, "calibration_report.json:training_config", exc))
            continue
        if isinstance(rep, dict) and isinstance(rep.get("training_config"), dict):
            out.append((f, "calibration_report.json:training_config", rep["training_config"]))
    return out


def check_config(path: Path, label: str, cfg) -> list:
    if isinstance(cfg, Exception):
        return [f"CANNOT VERIFY {path}: {cfg}"]
    if not isinstance(cfg, dict):
        return [f"CANNOT VERIFY {path}: top level is {type(cfg).__name__}, want an object"]

    metrics = published_metrics(cfg)
    if not metrics:
        return []

    declared = cfg.get("single_seed")
    if declared is not None:
        problems = []
        if not isinstance(declared, dict):
            return [f"FAIL {path}: `single_seed` must be an object naming the seed and the issue"]
        seed = declared.get("seed")
        # ⛔ "UNRECORDED" is allowed and is NOT the same as omitting the field: commerce v2's
        # shipped head does not match the trainer in the tree (`classifier_type` MLPClassifier
        # against a transformers Trainer), so its seed cannot be established without guessing.
        # A guessed 42 there would be a hand-built fact; an explicit UNRECORDED is the finding.
        if not (isinstance(seed, int) and not isinstance(seed, bool)) and seed != "UNRECORDED":
            problems.append(
                f"FAIL {path}: `single_seed.seed` must be the integer seed that ran, or the "
                f"string \"UNRECORDED\" with a `why` that says why it cannot be established")
        if ISSUE not in str(declared.get("issue", "")):
            problems.append(f"FAIL {path}: `single_seed.issue` must name {ISSUE}")
        if not str(declared.get("why", "")).strip():
            problems.append(f"FAIL {path}: `single_seed.why` must say why it was not rebuilt")
        return problems

    problems = []
    seed_set = cfg.get("seed_set")
    if not isinstance(seed_set, list) or len(seed_set) < 2:
        problems.append(
            f"FAIL {path}: publishes {len(metrics)} metric(s) with no `seed_set` of at least two "
            f"seeds and no `single_seed` declaration — {ISSUE}")
        seed_set = None
    for m in metrics:
        b = cfg.get(f"{m}_band")
        if not isinstance(b, dict):
            problems.append(f"FAIL {path}: `{m}` has no `{m}_band` — a point metric is one draw")
            continue
        missing = [k for k in BAND_KEYS if k not in b]
        if missing:
            problems.append(f"FAIL {path}: `{m}_band` is missing {missing}")
            continue
        if seed_set is not None and list(b["seeds"]) != list(seed_set):
            # A band computed over a different set is not comparable to the file's other bands,
            # and reading them side by side is how an ordering gets published backwards.
            problems.append(
                f"FAIL {path}: `{m}_band` was computed over seeds {b['seeds']}, but the file "
                f"declares seed_set {seed_set}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO / "filters"))
    args = ap.parse_args()

    root = Path(args.root)
    found = sites(root)
    if not found:
        print(f"CANNOT VERIFY detector-metric-bands: no training_config.json and no "
              f"calibration_report.json carrying one under {root} — a guard that examined "
              f"nothing is not a passing guard")
        return 1

    rel = lambda p: str(p.relative_to(REPO)) if REPO in p.parents else str(p)
    problems, with_metrics, banded, declared_rows = [], 0, 0, []
    for path, label, cfg in found:
        if isinstance(cfg, dict) and published_metrics(cfg):
            with_metrics += 1
            if cfg.get("single_seed") is not None:
                declared_rows.append((path, label, cfg["single_seed"]["seed"]))
            else:
                banded += 1
        problems.extend(check_config(path, label, cfg))

    for p in problems:
        print(p)
    if problems:
        print(f"FAIL detector-metric-bands: {len(problems)} problem(s) over {len(found)} "
              f"site(s), {with_metrics} of which publish metrics")
        return 1
    print(f"PASS detector-metric-bands: {len(found)} site(s) examined, {with_metrics} publish "
          f"metrics — {banded} banded, {len(declared_rows)} declared single-seed ({ISSUE})")
    for path, label, seed in declared_rows:
        print(f"  single-seed, declared: {rel(path)} [{label}] (seed {seed})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
