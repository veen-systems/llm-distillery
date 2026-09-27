# Session 2026-09-09 — the corpus that cannot exhibit its own failure, and a review that found 5 blockers in my write-up of it

**Spend: $0.** No oracle calls, no training, no deployment. **NexusMind untouched; nothing to
deploy; no merge** (clean `main`). Almost all of the session was a cross-session consult with the
NexusMind session (`nexusmind-4a`), which proposed supplying a production-sourced pool of adverse
examples for a `human_thriving v9` retrain. What shipped is `EXP-032`, six hypotheses, one Dead End,
six gotchas, one checker fix and a corrected TODO.

⛔ **Read the second half of this record before quoting the first.** A four-lens review found
**5 blockers and 8 warnings** in my initial write-up, including one that refuted my own headline
absolute and three defects inside the analysis script. Every figure below is the corrected form.

## ⭐⭐ THE KEEPER — 1,253 harm rows and none of the one that matters

`datasets/scored/human_thriving_v8/labels_v84_merged.jsonl` (n=6,586) holds **1,253
`harm_is_subject` rows** — **19.03% sample share, 20.96% design-weighted**. The obvious read, and
the peer's first read, is *"not short of harm data."* It is backwards:

- **max `weighted_mean_all` among those 1,253: 2.7667.** Rows at ≥4.0: **0** (asserted).
- **All 316 rows at or above the 4.50 op-point are `in_scope`** — 4.798% sample, **2.709%
  design-weighted** (asserted).

The failure mode `#156` and v9 must learn is harm content **the student** scores ≥4.5 (#150: oracle
gates at wa 0.80–0.90 where the student returns 4.66–4.85). ⇒ **The corpus's FINAL LABELS cannot
exhibit student/oracle disagreement, because they ARE the oracle's output.**

⭐ **The general form, mirroring a rule already in `CLAUDE.md`:** *prove the instrument could have
said yes* guards a **negative**. Here a **positive count of 1,253** carried just as little — and the
big reassuring number is the harder half, because nobody interrogates it. Name what the labelling
process **cannot emit**; cross-tabulate the verdict against the **score band**, not the verdict.

## ⛔ WHERE I OVERSHOT — the review refuted my own absolute

I published *"zero examples and **cannot have any**"* and *"a production-scored population is the
**only** route."* Both false, from fields in the same JSON object my script never read:

- **178** rows carry ≥1 `harm_is_subject` run-vote with a non-harm final verdict; **1** of them
  above the op-point (5.367, votes 5×`in_scope` + 1×`harm_is_subject`).
- **1,079** rows are `scope_flipped`; **178** `harm_is_subject` rows have split run votes.
- A **$0** detector arm — #156's positives are 1,011/105/137 across the splits, evaluable against
  EXP-031's 9/32 judge-flagged rows — was never costed before the pool was called "the only route".

⭐ **An absolute is a measurement, and mine went further than the thing I had measured — in the same
paragraph that named the rule.** (One review lens reported 6 such rows above the op-point; that used
the broken aggregate below. Measured under the declared one it is **1**. I used my own number.)

## ⛔ THREE DEFECTS INSIDE THE ANALYSIS, none caught by any checker

1. **A convenience fallback unioned two labelling generations.** `wa()` preferred
   `weighted_mean_major` and fell back to `weighted_mean_all`, publishing **351 = 5.3%**. The corpus
   **declares its own aggregate** — `aggregate_used == "all"` on **6,586/6,586** — so the correct
   figure is **316 = 4.798%**. The 456 rows lacking `weighted_mean_major` are not a shape quirk but
   `prompt-v8-4.md` (k=6) against `prompt-candidate-tail.md` (k=3). ⭐ **The repo's shape rule passed
   and its semantics rule failed:** the `isinstance` guard CLAUDE.md asks for was present and
   correct, and a field being *present* said nothing about it being the one the producer used.
   `aggregate_used` appeared in **no document in the repo**.
2. **The headline was a hardcoded `print`.** Four unconditional `print()` calls with `351` typed in.
   Two lenses independently **mutated the DATA** and the script emitted *"ALL 351 rows … ZERO
   training examples and cannot have any"* verbatim, exit 0, while the computed line above it
   disagreed. Now six assertions; **mutation-tested six ways, all six killed, control passes**, and
   the `in_scope` assert proven to fire independently of the ≥4.0 one.
3. **Every share was unweighted on a 25.1× stratified draw**, and `check_claim_shapes.py` **PASSED**
   because the labels file is a **sixth path alias** for that draw and was absent from
   `DESIGN_WEIGHTED`. Added — which made **5 more previously-invisible reads** appear, one of them a
   genuine pre-existing gap in `training/prepare_data.py`.

⛔ **And the above-op population is ONE PROMPT ARM, not a corpus rate:** all **316** come from the
456-row relabel set (**69.30%** above-op, itself selected for being above-op under an earlier pass)
while the **6,130**-row majority arm has **0**. `H-V8-30` measured that exact prompt swap moving
`in_scope` by **+0.1774** (McNemar p=0.0034) — it moves the variable being cross-tabulated.

## κ 0.375 was the wrong statistic — and the κ rescue fails too

The screen argument rests **only on nesting**: DeepSeek **9** ⊂ Gemini **32**, **0** reversals, and
it nests **within every stratum** (v7_only 2⊂14, both 3⊂8, v8_only 4⊂10). ⛔ **The binary-`harmful`
κ is 0.3749 — indistinguishable from the 4-class 0.3753**, so "that's the 4-class figure" implies a
better binary number that does not exist.

⚠️ **Two limits, both now printed.** P = 7.83e-07 tests **independence between two judges reading
the same 137 articles** — guaranteed false, so it establishes correlation, **not screen safety**. And
safety is **0 misses in 9**: rule-of-three 95% upper bound on the miss rate **33%**. "Recall-safe" is
**bounded, not shown**. Adopted by the peer regardless, which is defensible — but the bound travels.

## The fluency finding is substantially COMPOSITION

Pooled, `fits` falls **−15.1pp** (DeepSeek) / **−12.3pp** (Gemini) en→non-en with `misleading`
absorbing it, both families. ⛔ **Within stratum the sign REVERSES under both judges:**

| stratum | n | English | DeepSeek `fits` Δ | Gemini `fits` Δ |
|---|---|---|---|---|
| v7_only | 60 | 45.0% | −7.1pp | −2.4pp |
| both | 40 | 70.0% | **−40.5pp** | **−39.3pp** |
| v8_only | 37 | 62.2% | **+12.4pp** | **+13.7pp** |

The panel is stratified and English share varies with stratum, so *"both families, same direction,
same rows"* **does not survive the panel's own design variable**. `H-AP1` stays OPEN; its method now
has a **fourth arm** (stratum control). `harmful` flatness is weak too — **6 vs 3 rows**.

⛔ **And I mis-cited a rate in the entry about mis-citing rates: DeepSeek's k=3 split-vote rate is
43.1% (59/137), not 45.8%.** 45.8% is the **non-English** rate. The correct figure was in the
sibling evidence README the same commit edited.

## Four catches in the peer's pre-registration; two of my own suggestions were wrong

1. ⭐⭐ **A control whose failure mode is silence.** `judge.py`'s resume cache keys on `(id, pass)`
   in `<out.json>.partial.jsonl`, so an arm reusing the main output path returns cached verdicts with
   **no API call** and flips at **exactly 0%** — which the verdict rule read as *"the contrast is
   sound and earned."* **The reassuring answer is the one the bug produces.** ⚠️ **And my fix needed
   a fix:** a *file-total* line count still passes for an interrupted-then-rerun arm at its own path.
   Count lines appended by **this process**, or assert a non-zero call counter.
2. **A void condition that assumed what its own design prevents** (blind judge, one row per article,
   so a verdict cannot track a lens). Withdrawn. Measured headroom was thin: on-promise already runs
   1.35×/1.55× on the `both` stratum against a 2:1 bar.
3. ⛔ **My replacement failed the same test** and the peer declined it, correctly. Slot left empty —
   three conditions that can fail beat four with one that cannot.
4. ⛔ **I borrowed a noise floor across the judge AND its sampling structure.** At k=1 a split-vote
   rate does not exist. Fix: measure the floor inside the arm at k=2, read `unanimous`, never
   `majority`.

## Two more findings

**Lexical adverse-example selection is DEAD for the thriving family** (`H-AP6`; Dead End in
`calibration-history.md`). An uplifting story about overcoming adversity necessarily names the
adversity, so a harm-keyword filter preferentially surfaces what the lens exists to find. ⚠️ **Scoped
on review** — it does **not** forbid keyword corpus work elsewhere (violence-promotion v2,
`BasePreFilter.EXCLUSION_PATTERNS` under ADR-018/019 both run and are unaffected). ⚠️ Peer-reported
and **not adjudicated**; no artifact path, so it is a mechanism, not a citable measurement.

**⚠️ EXP-031 cannot be replayed FROM THIS DIRECTORY.** `panel_frame.jsonl` has no `content` field on
any of 137 rows. ⚠️ **Not "unrecoverable"** — `archive_retention_days: 730` on sadalsuud and EXP-030's
registry entry names the four source files; **the archive was never checked.** ⭐ **Persist the exact
model input, not the outputs plus a frame you believe reconstructs it.**

## ▶ NEXT SESSION

**Lane C, `#156`, starting at TODO Step 0b, and Step 2's framing is amended.** ⛔ **Cost the two $0
routes before the ~$3.2–3.6 spend**: the per-run scope-disagreement population, and a detector on the
existing positives evaluated against EXP-031's 9/32 rather than only on the test split. The open
question for the owner is whether the production pool is a **prerequisite** or an **enhancement** —
and after this review it is honestly the latter until the free arms are run.
