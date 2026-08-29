# `human_thriving` v8 — build journal

**What this is.** One row per step of the v8 build, in the order it happened, with the
question the step asked, the verdict in one line, what it cost, and where the evidence lives.

**Why it exists.** Nine v8 evidence directories accumulated before this file did, with no
index and no ordering, so nothing said which finding superseded which. Every expensive failure
this project has had was a **lost decision, not a lost result** — a prefilter nobody could
prove ran, an assertion whose baseline was never established, a corpus whose provenance took
git archaeology plus a three-arm experiment to reconstruct. The filter package
(`memory/filter-doc-standard.md`, 6 files) documents the *finished* filter and is the right
shape for that job; it has no place to put *how the filter came to be that way*. This does.

⛔ **Rules for this file, because a journal decays faster than a plan.**
1. **A row is written when the step happens, not afterwards.** Retro-narration from memory is
   how confident-but-wrong history gets written. Rows for steps that predate this file
   (2026-08-20 → 2026-08-28) **link and quote their own headline**; they do not narrate.
2. **The verdict column is one line and it names the outcome, not the activity.** "Refuted:
   the prefilter never ran on this corpus" — not "investigated the corpus".
3. **Spend is stated for every row, including `$0`.** A `$0` row is a claim that no oracle was
   called and is checkable.
4. **A superseded row is struck through and left in place**, with the row that replaced it
   named. Deleting it loses the only record that the earlier reading was ever believed.
5. **This file is an index, not a summary.** If a number matters, it lives in the evidence
   document with its command; this file points at it.

---

## Phase 0 / Phase A — the prompt, the corpus, and what the oracle actually does

| # | Date | Question | Verdict | Spend | Evidence |
|---|---|---|---|---|---|
| 1 | 08-20 | Does the v7 oracle carry a genre bias? | *"…oracle genre bias"* — see doc | — | [`2026-08-20-uplifting-v7-oracle-genre-bias.md`](evidence/2026-08-20-uplifting-v7-oracle-genre-bias.md) |
| 2 | 08-20 | Which valence framing best separates class A? | class-A valence bake-off | — | [`2026-08-20-uplifting-v7-class-a-valence-bakeoff.md`](evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md) |
| 3 | 08-22 | Was the v7 training corpus keyword-prefiltered? | **REFUTED, premise and all** — *"The v7 corpus was never prefiltered — and it is missing the class-A shape"* | $0 | [`2026-08-22-uplifting-v7-corpus-provenance.md`](evidence/2026-08-22-uplifting-v7-corpus-provenance.md), runs in [`2026-08-22-hcv1-runs/`](evidence/2026-08-22-hcv1-runs) |
| 4 | 08-23 | Does the v8 prompt beat v7 on the two defect classes? | *"the prompt works on class B, not yet on class A"* | **$0.4711** | [`2026-08-23-gate-a-two-oracle-run.md`](evidence/2026-08-23-gate-a-two-oracle-run.md) |
| 5 | 08-23 | Can a free local judge run the gate? | *"the §5b no-regression set, assembled — and the free local judge fails it"* | $0 | [`2026-08-23-no-regression-set-and-local-judge.md`](evidence/2026-08-23-no-regression-set-and-local-judge.md) |
| 6 | 08-23 | What would a minimum-length floor cost, by script? | measured over **1,332,648** production rows | $0 | [`2026-08-23-length-floor-by-script.md`](evidence/2026-08-23-length-floor-by-script.md) |
| 7 | 08-23 | Why did Step 1 of the prompt fail on Gemini? | *"the blocker was five contradictions, not the wording"* | see doc | [`2026-08-23-step1-rewrite-r2-r3.md`](evidence/2026-08-23-step1-rewrite-r2-r3.md) |
| 8 | 08-28 | What population would a v8 draw actually sample? | **The Gate 0 targets were stated against the wrong population** — every target moved once `news.google.com` (22.1%) came out | $0 | [`2026-08-28-v8-phase0-drawable-population.md`](evidence/2026-08-28-v8-phase0-drawable-population.md), runs in [`2026-08-28-v8-phase0-runs/`](evidence/2026-08-28-v8-phase0-runs) |
| 9 | 08-28 | Is the v8 prompt's cache ceiling reachable, and is the reorder safe? | ceiling reachable (**0.0% → 90.2%**); reorder **inside its own null** at n=30 — superseded by #11 | $0.12 | [`2026-08-28-v8-prompt-order-probe/`](evidence/2026-08-28-v8-prompt-order-probe) |

## Phase A — the reorder decision (2026-08-29)

| # | Date | Question | Verdict | Spend | Evidence |
|---|---|---|---|---|---|
| 10 | 08-29 | Is the reorder label-neutral, at n=200 with a matched null? | ⛔ **NO — it changes the labels.** mean(reordered − as-is) **−0.239** [−0.409, −0.080] production-mix; **not** multiplicity-robust, no family pre-registered | **$0.867** | [`2026-08-29-v8-phase-a-k3/`](evidence/2026-08-29-v8-phase-a-k3) |
| 11 | 08-29 | Are the reorder's stricter labels **better**, or just lower? | **Better, narrowly.** Of 12 op-point crossings only **4 are stable**; on those the reorder is right **3 of 4** (drops a 2060 projection, an ODA funding plan, a mentorship guidebook) and its one stable add is a judged false positive | $0 | [`2026-08-29-v8-h-v8-9-adjudication/`](evidence/2026-08-29-v8-h-v8-9-adjudication) § step 1 |
| 12 | 08-29 | Does the reorder suppress either §5b hazard? | ✅ **No.** Recovery narrative clears the op-point in both arms; on the transitional-justice row the reorder is **best of three prompts** (+1.417 over v7). ⛔ Third row fails under **v7 too** → a defect in acceptance criterion 2 | **$0.0208** | [`2026-08-29-v8-h-v8-9-adjudication/`](evidence/2026-08-29-v8-h-v8-9-adjudication) § step 2 |
| 13 | 08-29 | Is **k=3** enough repetition, and what would k=5 buy? | **k=3 is the stopping point.** Residual **2.39%** (reordered, production-mix); k=5 removes **32 rows of 6,590** for 1.67× the bill. ⚠️ The k=1→k=3 prize is **~83 rows**, a third the size the plan's flip-rate argument implies | $0 | [`2026-08-29-v8-k3-residual/`](evidence/2026-08-29-v8-k3-residual) |
| 14 | 08-29 | Does the prompt-cache discount survive the gap between corpus passes? | ⏳ **running** — P0 found the prefix still hot after **77.9 min** of inactivity, which reframes the question: a corpus pass calls continuously and never lets the prefix cool | ~$0.05 | [`2026-08-29-v8-cache-ttl/`](evidence/2026-08-29-v8-cache-ttl) |

## Open decisions this journal is waiting on

1. **Adopt the reordered prompt, or not** (owner). Evidence: rows 10–12. Everything downstream
   — corpus sizing, the b650 staging run, the corpus manifest (llm-distillery#127, not yet
   written) — is costed against it.
2. **Acceptance criterion 2 is failing today, against v7** (owner). Row 12. Drop the Rwanda–EU
   row from the no-regression set, or convert its assertion to a delta.

## What is deliberately NOT here

- **Numbers.** Every figure above is a pointer to a document that carries the figure *with the
  command that reproduces it*. Two hand-maintained copies of a number disagree the moment one
  is updated — the reason `CLAUDE.md` states no counts either.
- **The plan.** `docs/HUMAN_THRIVING_V8_PLAN.md` says what v8 *will* be and is edited as
  rulings land. This file says what was *done* and is append-only.
