---
name: project_session_2026_08_21
description: human_thriving v8 planned end-to-end. Class A (harm-adjacent) ruled the priority; a prompt-only v8 fixes ~1/3 of it. Three owner rulings, 5 adverse examples promoted, prefilter dropped, probe to be retrained. No spend, nothing deployed.
metadata:
  type: project
---

# 2026-08-21 — the v8 plan, and three of my own findings that did not survive review

**Zero oracle spend. No model trained. Nothing deployed.** Output is a plan
(`docs/HUMAN_THRIVING_V8_PLAN.md`, 952 lines), two evidence files, a reusable harness,
5 promoted adverse examples, and llm-distillery#126.

## The arc, which was a sequence of my framings being narrowed by the owner

1. I opened with #125 (academic register) as *the* defect — it was yesterday's finding.
2. Owner: *"the ones flagged by reader are actually far far worse."* → **two classes**, and
   the academic one is the lesser. Class A raw **5.86–6.85** (one normalizes to **8.284**,
   top of feed) vs class B **4.06–5.12**, barely over a 4.5 op-point.
3. Owner: *"we want stricter, cause FP … is way worse than missed detections."* → settles
   **ADR-020 §3 vs ADR-023 in ADR-023's favour**, scoped to harm.
4. Owner: *"why don't you pick adverse examples that are truly FP"* — I had been escalating
   line calls. ⭐ **A row with a serious true-positive reading is a bad gate probe by
   construction**: it tests the boundary, and the boundary is where noise makes the test
   meaningless.
5. Owner: *"bring them to the dataset we will use for training"* — I had been cataloguing,
   not promoting.
6. Owner: *"if so, that would explain why the probe passes so many"* → the prefilter question,
   → ruling 3: **drop the keyword prefilter, retrain the probe**.

## ⭐⭐ The finding that shaped the plan

**A prompt-only v8 fixes about a THIRD of class A.** Three-oracle bake-off (Gemini /
DeepSeek / qwen3:14b on b650), same v7 prompt, same text: **1 of 3 rows fails on all three
oracles** (label defect) and **2 of 3 are the student alone** (no prompt reaches those).
Hence Phase B2 — playbook §4b hard negatives, $0 oracle. `H-UP7` in
`memory/uplifting-oracle-genre-hypotheses.md`.

⚠️ **A fourth noise floor: oracle run-to-run is 0.82 mean / 2.25 max** (n=7), 5× the #95
batch floor. **A single-run oracle score is not a measurement**; every oracle-side gate is
now a k-run mean.

## What I got wrong, and how each was caught

1. ⛔ **H-CV1.** I claimed the keyword prefilter depleted the corpus of harm content, then
   claimed the opposite when the numbers came back 4.70% vs 3.26%. **Both were wrong**: the
   matching corpus rows are *override survivors of the filter under test*, so the comparison
   cannot see depletion at all. Checker and checked are the same object. Now **UNTESTED**,
   with a method for testing it properly. Caught by the adversarial review lens.
2. ⛔ **The cap mechanism.** I said `cap_applied` is null because `content_type` is an
   oracle-only field. The runtime path never reads `content_type` — `_TRIGGER_REGISTRY` is
   **empty by design** since 2026-07-14. The stamp is correct; the mechanism is disarmed, not
   dead. Caught by the reachability lens. ⚠️ I also over-promoted caps three replies running;
   the owner asked why, and the honest answer is **it was the one thing I could grep for**.
3. ⛔ **Two adverse rows shipped each other's rationale** — a hand-keyed dict with two
   transposed IDs, on rows tagged `HARD NEGATIVE`. Caught by the adversarial lens.
4. ⛔ **Corrupted the plan file twice** with backwards index-slices, once to 16.5 MB. Both
   recovered exactly. See `memory/gotcha-log.md`.

⭐ **The review battery earned its keep and the lenses failed non-overlappingly**:
claim-verification re-derived all 30 bake-off weighted averages with **0 mismatches** while
adversarial found the rationale swap that no arithmetic check could see.

## State

- **B1 CLEARED**: v7 corpus is on **gpu-server**, 6,590 rows, full text.
- Adverse slice: class A **4 → 9**; 6 rows parked/rejected/demoted with reasons.
- `memory/filter-doc-standard.md`: core **7 → 6 files**, `prefilter.py` optional.
- ⚠️ **Only 2 of 6 filter packages are complete** (`nature_recovery v4`, `cultural_discovery v5`).
  `belonging v1` — the template the standard was written from — fails its own core.

## Next session

Read the plan, not this file. Start at **Phase 0** (corpus) and **test H-CV1 properly**.
⚠️ **b650's GPU diverges from production at 4.5, this filter's op-point** — train on GPU,
gate on CPU. Still undeployed from 08-20: NexusMind's `primary_literature_cap` shadow.
