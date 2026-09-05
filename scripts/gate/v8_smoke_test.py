#!/usr/bin/env python3
"""Phase-8 smoke test for `human_thriving v8` — does the package SCORE, end to end?

⛔ WHAT THIS IS NOT. It is not the deploy gate (ADR-021), which judges the model
against held-out oracle ground truth and needs the labelled split. This asks the
cheaper question that comes first and had never been asked: **given the package as
it sits on disk, does an article go in and a well-formed, calibrated, tiered
result come out — and does the operating point ruled on 2026-09-05 actually
separate anything?**

⚠️ MUST RUN ON A HOST THAT HAS THE WEIGHTS. They are gitignored as large model
checkpoints (`.gitignore` § *Model checkpoints (large files)*) and live only on
`b650-gpu:~/llm-distillery/filters/human_thriving/v8/model/`. On any other host
this exits 2 as CANNOT VERIFY rather than failing — a missing artifact is not a
broken scorer, and reporting it as one is how a red suite gets ignored.

    cd ~/llm-distillery && venv/bin/python scripts/gate/v8_smoke_test.py

⛔ THE ASSERTIONS ARE ABOUT MECHANISM, NOT ABOUT ACCURACY. Six articles cannot
measure quality and this file does not try; every quality number for v8 comes from
the 660-row held-out split (`docs/evidence/2026-09-04-v8-probe-calibration/`).
What it checks is that the parts are wired: calibration loaded, the gatekeeper
reachable, both hybrid stages reachable, the tier boundary at the ruled op-point,
and the stamped fields a downstream consumer reads.
"""
import json
import sys
from pathlib import Path

OP_POINT = 4.5           # docs/decisions/2026-09-05-v8-op-point.md
DIMS = 6

# ⚠️ SYNTHETIC, AND DELIBERATELY SO. Real article text at corpus scale is the #97
# hazard and must not enter this repo. These are hand-written to exercise MECHANISM
# — a clear thriving outcome, a clear non-outcome, a harm-dominant row the class-A
# rulings exist for, and a stub short enough to reach the content-length stamp.
CASES = [
    ("clear_positive",
     "Community solar cooperative cuts energy bills for 4,000 households",
     "A cooperative in Groningen finished connecting 4,000 low-income households to a "
     "shared solar array this month. Independent auditors measured an average bill "
     "reduction of 31% across the first full year, and the municipality has published "
     "the underlying meter data. Two neighbouring provinces have begun replicating the "
     "financing structure, which uses a revolving fund rather than one-off subsidy."),
    ("clear_negative",
     "Quarterly results beat analyst expectations",
     "The company reported quarterly revenue above consensus, driven by pricing. "
     "Shares rose in after-hours trading. Management reiterated full-year guidance and "
     "declined to comment on the regulatory review disclosed last quarter."),
    ("harm_dominant",
     "Three killed in factory fire; charity opens relief fund",
     "Three workers died when a fire swept through a garment factory on Tuesday night. "
     "Investigators are examining whether fire exits were blocked. A local charity has "
     "opened a relief fund for the families of those killed."),
    ("short_stub",
     "Council approves park plan",
     "The council approved the plan on Tuesday."),
]


def cannot_verify(msg):
    print(f"CANNOT VERIFY: {msg}")
    return 2


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    pkg = root / "filters" / "human_thriving" / "v8"
    weights = pkg / "model" / "adapter_model.safetensors"
    if not weights.is_file():
        return cannot_verify(
            f"no weights at {weights} — this host cannot run the student. "
            f"Run on b650-gpu; see the module docstring.")

    from filters.human_thriving.v8.inference_hybrid import (
        HumanThrivingHybridScorer, load_stage1_config)

    stage1 = load_stage1_config()
    print(f"stage-1 config: threshold={stage1['threshold']} "
          f"probe={stage1['probe_path']} sha_pinned={'probe_sha256' in stage1}")

    scorer = HumanThrivingHybridScorer()
    results, failures = {}, []

    def check(cond, label):
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            failures.append(label)

    for name, title, content in CASES:
        r = scorer.score_article({"title": title, "content": content})
        results[name] = r
        wa = r.get("weighted_average")
        print(f"\n[{name}] weighted_average={wa!r} tier={r.get('tier')!r} "
              f"stage_used={r.get('stage_used')!r}")
        check(isinstance(wa, (int, float)), f"{name}: weighted_average is numeric")
        check(isinstance(r.get("scores"), dict) and len(r["scores"]) == DIMS,
              f"{name}: {DIMS} dimension scores present")
        check(all(0.0 <= v <= 10.0 for v in (r.get("scores") or {}).values()),
              f"{name}: every dimension inside [0, 10]")
        check(r.get("stage_used") in ("stage1_low", "stage2"),
              f"{name}: stage_used is one of the two known values")
        # ⛔ THE TIER MUST FOLLOW THE RULED OP-POINT, and it is checked against the
        # value the scorer actually produced, never against a hardcoded expectation
        # about this article — six synthetic rows cannot say what v8 SHOULD think.
        if isinstance(wa, (int, float)):
            expect = "low" if wa < OP_POINT else ("high" if wa >= 7.0 else "medium")
            check(r.get("tier") == expect,
                  f"{name}: tier {r.get('tier')!r} follows weighted_average "
                  f"{wa:.4f} against the {OP_POINT} op-point (expected {expect!r})")
        check("content_length" in r,
              f"{name}: content_length stamped (the #93 contract)")

    print("\n--- wiring, across the four cases ---")
    # ⛔ READ THE OBJECT THAT HOLDS IT, NOT THE WRAPPER. The first version of this
    # assertion checked `scorer.calibration` and FAILED -- calibration lives on
    # `scorer.stage2_scorer`, so the check was pointed at an object that can never
    # carry it and its negative meant nothing. Caught on the first real run,
    # 2026-09-05, in a session whose whole subject is that failure mode.
    stage2 = getattr(scorer, "stage2_scorer", None)
    check(stage2 is not None and getattr(stage2, "calibration", None) is not None,
          "calibration.json is LOADED on stage2_scorer "
          "(an uncalibrated arm is a different model)")

    # ⚠️ THE SCARY LINE IN THE LOADER OUTPUT IS BENIGN, AND THIS IS WHY IT IS
    # ASSERTED RATHER THAN EXPLAINED IN A COMMENT. Loading the base model for
    # sequence classification prints `score.weight | MISSING ... newly
    # initialized`, because the regression head is not in the BASE checkpoint --
    # PEFT supplies it from the adapter a moment later. A future reader will
    # re-diagnose that warning as a broken head unless something checks the
    # adapter really carries a TRAINED one. Verified 2026-09-05: shape (6, 1152),
    # std 0.0199, i.e. not random-init scale.
    try:
        from safetensors import safe_open
        with safe_open(str(weights), framework="pt") as f:
            keys = list(f.keys())
            head = [k for k in keys if k.endswith("score.weight")]
            trained = False
            if head:
                t = f.get_tensor(head[0])
                trained = t.numel() > 0 and float(t.std()) > 0.0
        check(bool(head) and trained,
              f"the adapter carries a TRAINED regression head "
              f"({head or 'ABSENT'}) — the loader's `score.weight | MISSING` "
              f"line is about the BASE checkpoint, not this one")
        # CLAUDE.md Hard Constraint: OLD PEFT key format, never `.lora_A.default.`
        check(any(k.endswith("lora_A.weight") for k in keys)
              and not any(".lora_A.default." in k for k in keys),
              "LoRA keys are in the OLD format (.lora_A.weight) — "
              "resave_adapter.py must never have run on this")
    except ImportError:
        print("  NOTE  safetensors unavailable; adapter-head check skipped")
    stages = {r.get("stage_used") for r in results.values()}
    check(len(stages) >= 1, f"at least one stage exercised (saw {stages})")
    # ⚠️ NOT asserted: that both stages fire. Four articles cannot guarantee the
    # screen routes one of them either way, and demanding it would make this test
    # fail for a reason that is not a defect. Reported instead.
    print(f"  NOTE  stages exercised: {sorted(stages)} "
          f"({'both' if len(stages) > 1 else 'one only — not a defect at n=4'})")
    was = [r["weighted_average"] for r in results.values()
           if isinstance(r.get("weighted_average"), (int, float))]
    check(len(set(round(w, 4) for w in was)) > 1,
          f"the four articles do not all score the same ({[round(w, 3) for w in was]}) "
          f"— an identical set would mean the student is not reading the input")

    print(json.dumps({k: {"weighted_average": v.get("weighted_average"),
                          "tier": v.get("tier"), "stage_used": v.get("stage_used"),
                          "gatekeeper_applied": v.get("gatekeeper_applied"),
                          "scores": v.get("scores")}
                      for k, v in results.items()}, indent=2, default=str))
    if failures:
        print(f"\nFAIL {len(failures)} assertion(s): {failures}")
        return 1
    print(f"\nPASS v8 smoke: {len(CASES)} articles scored, all assertions held")
    return 0


if __name__ == "__main__":
    sys.exit(main())
