---
name: project_session_2026_08_29
description: Phase A k=3 resolved H-V8-3 against the plan; two review passes found 14 then 8 blockers in the same day's work, including a multiplicity "fix" that was seed noise
---

# 2026-08-29 — the reorder is not label-neutral, and both of my fixes needed fixing

**Spend $0.869** (1,200 calls + a 6-row stamp check; DeepSeek off-peak, 0 errors).
**No model trained, no threshold moved, nothing in `filters/`, nothing deployed** — deploy is
N/A, not skipped. Nine commits, `75fe9a9..98e7473`, **not pushed**.

## What shipped

1. **`scope_verdict` / `dominant_subject` are persisted** (#135 prerequisite). The scope gate
   had only ever been *inferred* from "all six dims ≤ 2", which cannot separate a refusal
   from a dull in-scope article.
2. **Phase A k=3 ran**: n=200, two strata, two arms, six interleaved passes.
3. **`prompt_hash` / `prompt_file`** now stamp every persisted row.

## ⛔⛔ THE FINDING — H-V8-3 resolved, against what the plan assumed

Moving the article to the end of the v8 prompt **changes the labels**. Production-mix stratum:
mean(reordered − as-is) **−0.239**, 95% CI [−0.409, −0.080], sign-flip permutation
**p = 0.0049**, source-clustered [−0.410, −0.078]. Boundary stratum **−0.443** (p = 0.0063).
Rows above the op-point at k=3, **per stratum**: 8/150 vs 11/150 and 7/50 vs 12/50.

⛔ **NOT multiplicity-robust.** p=0.0049 clears 0.05 and 0.05/2 but not 0.05/16, the family
the script prints. **No family was pre-registered** — that is the defect and no arithmetic
repairs it afterwards.

The n=30 probe could not see this because its null was *a second run*, not a matched
pair-level null with an interval. The reordered prompt is **~5.27× cheaper on the paying
call and a different, stricter oracle** — so it cannot be adopted as a cost optimisation.
**Still not adopted; that is the owner's call and it is the one open decision.**

Evidence: `docs/evidence/2026-08-29-v8-phase-a-k3/`. Pre-registration in `ff88b56`, one
commit ahead of the results and unchanged since — four of its seven predicted ranges missed.

## Two review passes, 22 blockers, all in my own same-day work

**First pass (5 lenses, 14 blockers).** Four claims withdrawn: the −0.235 "not just the gate"
finding (pooled the strata its own pre-registration forbids, *and* conditioned on an outcome
the treatment changes — a collider); "15 vs 23 above the op-point" (same pooling); "smaller
than the probe's 13%" (4/30's CI is [3.8%, 30.7%] and covers every new estimate); and every
cost figure, carried from a `$0.02f` rounded display instead of the token counts in the same
file — spend is **$0.867**, not $0.85.

**Second pass (5 lenses, 8 blockers) — because a fix commit is where over-correction lands.**

⭐⭐ **THE KEEPER: my multiplicity fix was itself noise.** The Bonferroni bound I added put
each end on a **single order statistic** (α=0.05/21 on 4,000 draws indexes element 4). Its
Monte-Carlo sd is ~0.014 against a reported −0.010; it sits above zero in **24/30** and
**408/500** replications. `seed=17` decided the published verdict. And the script's own
permutation test had been contradicting it in the same file the whole time. Removed, not
recomputed. **A resampling estimator has a resolution, and the correction needing the deepest
tail is exactly where it runs out.**

⭐ **Two mutations survived the suite I called mutation-tested** — including
`prompt_file == "prompt-candidate.md"` where the harness only ever passed that prompt. A
**tautological assertion, re-introduced in the commit that deleted two of them.** Now 16
tests driving both prompts; five mutations re-seeded, five caught.

⭐ **`p = 0.722` was cherry-picked.** It named no cell, and both readings that produce it use
a non-comparable cell *and* give the larger p — the one supporting the conclusion. The
like-for-like cell gives **p = 0.4648**.

## ⛔ Five of mine

1. **The retraction sweep stopped at the repo boundary.** Nine surfaces corrected and
   announced "finished properly"; still live in `~/.claude/projects/.../memory/`, which loads
   every session. **14th occurrence of *establish what a source excludes*.**
2. **I read an experiment's ARM LABEL as a description of production** — and so had the
   2026-08-10 evidence document, which is where I inherited it. Corrected at the source.
3. **`ls -d */` and `ls | grep venv` skip dotdirs**: I reported "no venv here" with a `.venv`
   present. Results identical on both interpreters, so nothing I reported changed.
4. **`check_index_budget.py --target pointers` passed on a file it does not read.** Found by
   padding the row 200 chars and watching it still pass.
5. **`pip list` hides torch's `+cu130` local tag** — nearly reported gpu-server as CPU-only,
   the *same wrong conclusion* as #2 by a completely independent route.

## Also

- **`/update-drift`: 0 releases behind** (agent-ready-projects v1.36.1, remote read directly —
  58 tags). Three user-global skills **byte-identical** to the v1.36.1 reference install.
  ⚠️ Standing gap, not drift: the re-mapped `review-changes` fork lacks upstream's
  size-driven tier rules, available since **v1.16.0**, including *"a new executable is HIGH"*.
- Peer traffic with the NexusMind session corrected claims **in both directions**; it
  confirmed cd v5 still live, `investment_risk` still paused, `min_score` still 4.0.
- **`venv-prodparity` verified current** against gpu-server *live*, all eight pins.

## Session close

- **`CLAUDE.md` 38,204 → 37,445.** Three trims, each verified homed first. ⛔ The `uplifting`
  row was **not** trimmable — `grep -c "107" memory/filter-status.md` returned **0**, so the
  #107 finding lived only in the always-loaded file. Written into `filter-status.md` as its
  own section *before* the row was shortened. #133 is CLOSED and its routing rule is the
  adopted remedy; I had wrongly called it an open question.
- One footer atom was **wrong, not merely stale**: "byte-identical to v1.35.0 apart from the
  installer's header" — today's drift check measured **0 differing lines against the v1.36.1
  reference install**, and v1.35.0 is the release that established there is no install-time
  transform at all.
- **Hypotheses:** H-V8-8 (k=3 repeat discount at corpus scale — an assumption carrying a ~$15
  decision) and **H-V8-9** (are the reorder's stricter labels *better*, not merely different —
  nothing measures either arm against ground truth) opened with Methods and Revisit triggers;
  H-V8-6 gained one. Six ⏳ open.
- **`memory/stamp-contract-integrity.md` gained a scope boundary**: the four stamps added
  today are on **oracle output rows**, not article records — no Contract, no census, never
  production. That file is what `CLAUDE.md` tells you to read before adding a stamp, and it
  would otherwise have miscategorised them.
- **Issues:** #135 (prerequisite done, flip rate given an interval, 13% explicitly *not*
  refuted), #104 (the "cross-box" name retired — and its own table cites the retired 4.0
  op-point), #95, #134, #136. **augmented-engineering#39** filed per `CLAUDE.md`'s standing
  cross-repo instruction.
- **Merge N/A** (no feature branch). **Deploy N/A, not skipped** — nothing in `filters/`
  across all commits. **Pushed.**

## Next session

1. ⛔ **OWNER: adopt the reordered prompt or not** — it blocks everything below. If you want
   evidence first, H-V8-9 is cheap: adjudicate only the ~21 rows that cross the op-point
   between arms against §5b's no-regression set.
2. Corpus size, stage on b650, `corpus_manifest.json` (#127) — budget k=3 off H-V8-8, not off
   the unproven repeat discount.
3. #134 step 2 and #136 — hygiene.
4. ⚠️ Stale branch `docs/event-identity-encoder-plan` (1 commit, `0c283c6`, the #100 plan) —
   land it or drop it; not mine to delete.
