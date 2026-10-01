# Session — 2026-09-25 (10:10) → 09-26 (~11:30): v9 retrained, audited, LIVE; Nature recovery audited; tab rule fixed

*Every number is quoted from the evidence READMEs named here; open the README before reusing one.*

**Spend:** oracle $0 in this part (the NR re-judge, relabel pilot, band audits and lens benchmark were all Claude
judges, $0; the owner approved oracle spend for NR moved-in rows, but that step never ran because the pilot failed).
GPU: b650 RTX 5090, three retrains plus two week-long production rescorings. **Deploys:** NexusMind#530 (v9),
NexusMind#531 (harm cap), ovr.news#372 (tab rule).

## What shipped
1. **human_thriving v9** (= adj3: v8's student retrained on adjudicated labels + 186 positives + 439 hard negatives).
   - Gate WIN: FP 11 → 1 on v8's test ids, under both label sets.
   - Live-week audit WIN: junk share 33.8% → 14.9%.
   - Cut-off 4.5 (owner). Normalization fitted at packaging from its production-week scores.
   - LIVE in NexusMind, **replacing v8** in the reader-invisible slot (owner). First cycle clean (3,643 rows `9.0`,
     24 passers). Thriving still reads uplifting v7: **#151 not decided**.
2. **Harm detector cap 3000 → 6000** (owner: "I don't want that cap"; NexusMind#531). Proof = the next cycle's
   `(cap 6000)` line. **Not yet observed at session end.**
3. **ovr.news narrow lens first** (#372): Recovery > Discovery > Belonging > Solutions > Thriving decides a
   multi-lens article's tab. Benchmark vs judges: 78% vs 66%; Recovery 18/21 vs 3/21. **Owner confirmation pending.**

## What was measured and NOT shipped
- **Two band audits of adj3's [3.5, 4.5) FAILED drift** (0.844, 0.887): the band is ambiguous. Owner rulings 4
  (sport OUT unless more) and 5 (teasers OUT) came out of it.
- **NR miss audit under NR-1** (owner 18/20): ~36 misses/week, 13 at the cut-off, 22 in the model band; via the
  probe none observed (upper bound ~55).
- **NR relabel pilot FAILED** (owner 3/10 vs judges, 8/10 vs oracle) → **relabel dropped**; the audit's ~47%
  precision is SUSPECT.

## Mistakes of mine, and what caught them
- **Lost context.** The NR audit, NR-1 ruling and re-judge happened in this session, but my context had no record
  of them. I told the owner twice that the audit "hadn't started". Caught by background task notifications and
  `git log`. Three re-judge batches (A06/B01/B02) had **never been launched**. ⭐ Lesson: when a notification names
  work you don't remember, read `git log` and the evidence dir before saying anything about its state.
- **Degenerate bootstrap:** the NR analysis printed `0 [0, 0]` for zero-positive strata, and I had written "none via
  the probe" in a commit. Corrected to N × Wilson bounds in both READMEs.
- **Summaries as the owner's input:** my one-line summary of a Nigerian pardon omitted "human parts for rituals",
  and a translated excerpt cut before the pension amount. Owner checks now show translated FULL text.
- **Pre-registration clock times were guesses** ("~13:05") and wrong; corrected to cite commits.
- **v9 `FILTER_VERSION` left at "8.0"**: caught by `verify_filter_package.py`, not by my own new test. Now tested.
- **`exit=$?` after a pipe** read `tail`'s exit status once more (the smoke test). Re-ran for the real code.
- **The first NexusMind watcher was keyed on the wrong PID** (the ssh wrapper's shell): caught before it fired.

## Judges vs owner (for the next rubric work; the owner is "NOT SURE" about turning these into rulings)
The owner is BROADER on nature (counts, translocations, colonisation, natural recoveries) and on everyday good
things (lifestyle, contests, pilots); STRICTER on relief-from-harm (released detainee, migrant rescue, airlift,
consumer compensation, the last conflicting with ruling 1). Candidate rulings, NOT given: "population and breeding
counts count as Nature recovery"; "relief from a harm is not Thriving".

## Next session
`docs/TODO.md` ▶ START HERE items A (verify the three live changes by outcome) then B (owner decisions).
