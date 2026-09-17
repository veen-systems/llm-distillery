#!/usr/bin/env python3
"""Every ADR-021 gate artifact says which DEVICE produced its numbers (llm-distillery#104).

The gate decides deploys. Its numbers were produced on some device, and `EXP-041` measured that
the device is not free: at `uplifting v7`'s 4.5 op-point, CPU and CUDA disagree on **2 rows of
660**, both on the false-positive side, moving specificity 0.9687 -> 0.9642 -- and specificity is
the metric ADR-023 decides on.

⛔ **THE POINT IS THE MIXTURE, NOT THE MAGNITUDE.** Before this check the tree held four CPU gates,
one CUDA gate (`human_thriving v8`) and two that recorded nothing, so an ADR-021 comparison across
filters was already mixing devices with nothing saying so. 0.0045 is small; a comparison that does
not know which side it is on is not.

⚠️ WHAT THIS DOES NOT CHECK: that the recorded device is TRUE, that the gate was re-measured, or
that anyone read it. It converts "nobody thought to ask" into "the file has to answer" -- the same
narrow claim `check_detector_metric_bands.py` makes.

⭐ `UNRECORDED` is allowed and is not a loophole: for a gate written before #104 the device cannot
be established without guessing, and a guessed `cpu` would be a hand-built fact. It must be paired
with a `device_unrecorded_why`, so the honest answer costs a sentence and the dishonest one is not
available.

    python3 scripts/verification/check_gate_device_stamp.py
    python3 scripts/verification/check_gate_device_stamp.py --root <dir>

Exit 0 when every gate answers, 1 otherwise -- including when it examined NO gate, which in this
repo is the signature failure of a guard that passes because it looked at nothing.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ISSUE = "llm-distillery#104"


def check_gate(path: Path) -> list:
    try:
        gate = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"CANNOT VERIFY {path}: {exc}"]
    if not isinstance(gate, dict):
        return [f"CANNOT VERIFY {path}: top level is {type(gate).__name__}, want an object"]

    prov = gate.get("provenance")
    if not isinstance(prov, dict):
        return [f"FAIL {path}: no `provenance` object, so nothing says which device produced "
                f"these numbers — {ISSUE}"]
    device = prov.get("device")
    if not isinstance(device, str) or not device.strip():
        return [f"FAIL {path}: `provenance.device` is missing or empty — {ISSUE}"]
    if device.strip() == "UNRECORDED" and not str(prov.get("device_unrecorded_why", "")).strip():
        return [f"FAIL {path}: `provenance.device` is UNRECORDED with no "
                f"`device_unrecorded_why` — say why it cannot be established"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO / "filters"))
    args = ap.parse_args()

    root = Path(args.root)
    gates = sorted(root.glob("**/ground_truth_gate.json"))
    if not gates:
        print(f"CANNOT VERIFY gate-device-stamp: no ground_truth_gate.json under {root} — a guard "
              f"that examined nothing is not a passing guard")
        return 1

    problems, devices = [], []
    for g in gates:
        problems.extend(check_gate(g))
        try:
            prov = json.loads(g.read_text(encoding="utf-8")).get("provenance") or {}
        except Exception:
            continue
        dev = str(prov.get("device", "")).strip()
        if dev:
            # Long hand-written prose lives in this field on some gates; the first clause is what
            # identifies the device, and truncating is honest as long as the file keeps the rest.
            devices.append((g, dev.split("--")[0].split(".")[0].strip()[:40]))

    for p in problems:
        print(p)
    rel = lambda p: str(p.relative_to(REPO)) if REPO in p.parents else str(p)
    if problems:
        print(f"FAIL gate-device-stamp: {len(problems)} problem(s) over {len(gates)} gate(s)")
        return 1
    print(f"PASS gate-device-stamp: {len(gates)} gate(s) examined, all name a device")
    for g, dev in devices:
        print(f"  {rel(g):52s} {dev}")
    # ⛔ The census is the finding: a tree where every gate answers can still be a tree that mixes
    # devices, and mixing is what breaks an ADR-021 comparison.
    distinct = {d.lower() for _, d in devices}
    if len(distinct) > 1:
        print(f"  NOTE: {len(distinct)} distinct devices across these gates — an ADR-021 comparison "
              f"across filters is comparing measurements taken on different hardware paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
