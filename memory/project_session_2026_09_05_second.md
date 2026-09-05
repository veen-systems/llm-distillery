# Session — 2026-09-05 (second): the op-point table, and four of its own claims retracted

**Spend $0.** No oracle calls, no GPU, no training. **Deploy N/A, not skipped** — verified:
`ls ~/local_dev/NexusMind/filters/` on sadalsuud has no `human_thriving`; v8's weights are
gitignored (#97) and live only on `b650-gpu`; phases 8 and 9 have not run.

Commits `293c09d`, `458c209`, `f275094`. Continues `project_session_2026_09_05.md`.

---

## What was asked

Architecture and the op-point, with a stated goal: *"If we can [make] the scorers faster,
that will help if we are going to use many."* Then the owner proposed a specific cascade —
e5-small probe as gate, e5-large **regression** probe as Stage 2 — and asked which route to
take, adding *"i wouldn't want to lose too much on quality. Especially I do not want false
positives."*

That is ADR-023's criterion — **specificity at the operating point** — and no artifact here
had computed it for a probe arm. EXP-018/019/020 all ranked on AUC or average precision.

## The answer to the throughput question, first

**Speed is not the constraint and will not be for a long time.** Score costs **52.1 min per
29.17 h**, 53.5% of a **5.57% duty cycle** (EXP-021); each additional filter adds ~**78 s per
cycle**, ~0.60 pp of duty. What scales badly is **per-filter fixed cost**: `MAX_LOADED_FILTERS
= 3` (`NexusMind/deploy/gpu-server/main.py:758`) against 5 deployed filters guarantees
evict+reload every cycle, and every filter re-runs its own encode pass although 14 configs
name `multilingual-e5-small`. Those two are the zero-quality-cost levers and remain untouched.

## EXP-024 — what stands

660-row test split, 35 positives, matched flag count so `FP = k − TP` identically.

⭐ At k=17 the two regression probe arms differ by **6 articles, CI [+1,+9]** excluding zero,
while their whole-split AUCs are **not** separable — **the operating-point test separates them
where the ranking metric cannot.** `probe_reg_large` against the student: CI includes zero at
all eight k.

## ⛔⛔ THE KEEPER — four claims retracted before commit, and the battery caught none

The mechanical battery — registry check, both budget guards, doc-claims, 21/21 annotations,
**667 tests** — was **entirely green**. A four-lens `/review-changes` then found:

1. ⛔ ***"AUC would have picked the wrong arm"* was a coin flip published as an ordering.**
   Δ **+0.0014**, CI **[−0.0448, +0.0476]**, **P = 0.523** — band ~30× the gap. Labelled ⭐⭐
   THE REUSABLE FINDING in four places. ⚠️ **And the converse kills the generalisation**: AUC
   separates the student from `probe_reg_large` (**P = 0.995**) where the op-point test cannot,
   so *"the op-point test is underpowered"* is not excluded by anything measured.
2. ⛔ ***"The gate buys nothing — identical TP at all eight k"* was FORCED.** Max screened
   score **1.4921**, k-th highest **2.7787 at k=60**; smallest k at which B could differ from C
   is **140**, grid stops at **60**. ⭐ *The instrument could not have said no* — the first
   working rule, **21st occurrence**, one day after the 20th, in a document written about the
   20th. ⚠️ The harder shape: **the conclusion was right** (0/35 positives screened; 85.7%
   break-even), so nothing downstream was wrong and nothing pressed anyone to check.
3. ⛔ **The paired bootstrap froze its top-k masks** and emitted a **zero-width 95% CI**
   (`[+0,+0]`); **90.6%** of replicates did not surface k rows. Replaced with a re-selection
   bootstrap **plus a null control** that must return `[0,0]`.
4. ⛔ **Every figure was UNWEIGHTED** on a split drawn under a **25.1×** design. Weighted, the
   positive rate is **3.1638%** not **5.3030%**, and **the student leads at every share tested**
   (0.529 vs 0.478 of the positive mass). ⭐ **The headline was a property of the sample.**

Also: *"6 of 8 k"* and *"grows monotonically"* were both wrong (**8 of 8** with ≥, **4 of 8**
strictly, non-decreasing only from k=26 — and 6 of 8 is `student_raw`'s figure, a different
arm), one table cell mixed the gated view into an ungated row, and EXP-018 ruled e5-large out
on **cost**, not on AUC.

## ⛔ A fifth, found during session close

**The arms are on different devices.** Student dumps are the **CPU** pass (recall **0.4857**,
matching EXP-015's CPU 0.486 against CUDA 0.514); probe dumps are **GPU**. CPU→CUDA is max |Δ|
**0.1956**, 3 flips at 4.5 (#104). ⭐ Conservative **by luck** — CUDA gains the student a TP, so
the CPU pass understates it and the "not distinguishable" result is weaker, not stronger.
Found by following up the open-issue list, not by the review.

## What did not happen

⭐ **A "drift" report I did not file.** `foresight` and `sustainability_technology` are still on
sadalsuud although CLAUDE.md records both REMOVED 2026-08-03. Reading
`NexusMind/config/app.yaml:492-497` first: they are **disabled in `enabled_filters` and the
packages deliberately retained** so last-scored articles drain from ovr's 10-day window. Not
drift. **Reading the config before reporting the anomaly was the whole difference.**

## State

- **Recommendation to the owner: keep the student for v8**, op-point **4.5 calibrated**.
  `probe_reg_large` matches it only unweighted, on one seed, with no `calibration.json`, in a
  test AUC suggests may lack power. It is the **Nth-scorer** lever, not a phase-8 input.
- `H-V8-22` registered with four preconditions; `H-V8-20` back-points to it and disambiguates a
  colliding "6 of 35" (screen at a val threshold vs final scorer at matched volume).
- `dump_manifest.sha256` pins all twelve input dumps — **bytes, not origin**; the
  probe→dump mapping is still off-repo, and `rescued_probes_manifest.txt` records the recall and
  regression e5-large probes **both** as `1024 6 mlp`.
- Commented llm-distillery **#104**, **#127**, **#98**.

▶ **NEXT: phase 8 — unchanged. The op-point is the owner's values call; nothing here moves it.**
