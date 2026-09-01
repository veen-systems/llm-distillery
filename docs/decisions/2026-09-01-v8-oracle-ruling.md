# The Phase B oracle — **DeepSeek**, and the run is authorised

**2026-09-01. Owner ruling.** Two decisions, taken together after the measurement in
`docs/evidence/2026-09-01-v8-oracle-choice/` (`EXP-009`).

⛔ **No oracle spend was incurred producing this record.** Every number below is read off work
already done and cited.

---

## 1. Oracle — **DeepSeek (`deepseek-chat`)**

**Ruled.** This is the fifth v8 decision and it was **never on the 2026-08-30 list** (which
covered prompt / row / ratio / size). Until today every v8 measurement used DeepSeek by
**momentum** — that is how a default gets adopted without anyone choosing it, and it is now
chosen.

### The evidence it rests on

Two bake-offs, both through the real call site (`scripts/score_deepseek_production.py`, with
`--base-url` / `--key-name` / `--model` for the Gemini arm — a price or behaviour with no call
site is not an option this project can pick, #103):

| | DeepSeek | Gemini 2.5 Flash |
|---|---|---|
| Gate B-A, 9 class-A rows, k=3, **full text** | **8/9** | 7/9 |
| STEP 1 applied (majority verdict ≠ `in_scope`) | **8/9** | 7/9 |
| the #91 origin row, *"Celebrated at birth, pushed into sex work"* | **0.900**, `harm_is_subject` 3/3 | **7.158**, `in_scope` 3/3 |
| cost | ~7× cheaper; the ≈$10.32 estimate is built on its prefix cache | endpoint exposes no cache field |

⚠️ **8 vs 7 on n=9 is ONE ROW.** The ruling does not rest on the margin — it rests on *which*
row. Gemini's extra loss is **stable across 3/3 runs** and it is the article that led the
ovr.news homepage and caused this filter version to exist. DeepSeek's single loss is a coin toss
that **both** oracles share (§3 below).

⛔ **And the margin is softer than the score line looks.** Read in full, the origin row is
genuinely two-sided: it opens on a former sex worker whose two daughters escaped into an NGO job
and medical-entrance study, and closes on a youth committee that stopped the practice in its
village. **Gemini's `in_scope` is defensible on the text.** The precise claim this ruling rests
on is therefore narrower than *"DeepSeek is right and Gemini is wrong"*: **DeepSeek reproduces
the owner's adjudication**, which is the job an oracle has here. Recorded rather than smoothed
over: `docs/evidence/2026-09-01-classA-full-read/`.

### ⛔ What this ruling explicitly does NOT rest on

- **Not on the 2026-08-23 argument.** That run chose DeepSeek because on *"Five men arrested…
  for raping a minor"* it capped to 3.00 while Gemini rose to **7.43**. Under the **adopted**
  reordered prompt that row is **DeepSeek 1.050 / Gemini 1.025**, `harm_is_subject` 3/3 on both.
  **The disagreement that decided it is gone.** Anyone citing *"Gemini ignores Step 1"* against
  `prompt-candidate-tail.md` is citing a measurement of a different prompt.
- **Not on the n=3 reading that stood in the plan until today** (*"Gemini is the stricter arm,
  3/10 caps vs 1/10"*, 2026-08-20). It was superseded on 08-23 and never corrected in place;
  it is now marked stale rather than deleted, so the correction is dateable.
- **Not on cost.** The 5.2× reorder saving is **DeepSeek prefix caching** and does not transfer:
  Gemini's OpenAI-compatible endpoint returns no `prompt_cache_hit_tokens` at all, so the
  script's *"Cache hit rate: 0.0%"* for it is a **construction artifact, not a measurement**.
  Cost is a tiebreak here, not a reason.

---

## 2. Phase B — **authorised**

6,590 rows, `prompt-candidate-tail.md`, **k=3**, from the workstation, staged to `datasets/`
(gitignored, real disk — **not `/tmp`, which is tmpfs**), started **off-peak**.

⚠️ **≈$10.32 is a CEILING.** H-V8-8 multiplied one pass by three on reasoning that describes a
pass over *different* articles; k=3 re-scores the *same* ones, and whole-request caching was
observed surviving two days. Whether 6,590 **distinct** prompts stay cached is a **capacity**
question nobody has measured — it will be read off pass 2 rather than predicted.

Preconditions discharged before launch (`docs/evidence/2026-09-01-v8-phase-b-preflight/`):
the v8 `config.yaml` exists so the labels are not stranded; `aggregate_k_runs.py` keeps the
scope verdicts; the acceptance-gate rows are full text; the corpus is hash-verified against the
manifest (`5e2cf729…`) after staging.

---

## 3. ⛔ Criterion 1 is a SEPARATE blocker, and the owner ruled it adjudicated AFTER the run

**Gate B-A passes on neither oracle.** Both fail *"Parents of baby girl killed at nursery"*, and
on both it is a **scope-gate coin toss**:

| | k=3 | runs | verdicts |
|---|---|---|---|
| DeepSeek | 4.400 | 6.10 / **0.90** / 6.20 | in_scope / response_to_harm / in_scope |
| Gemini | 5.133 | 7.20 / 7.15 / **1.05** | in_scope / in_scope / harm_is_subject |

Each oracle gets it right on one run of three. ⛔ And `--aggregate majority` makes it **worse**
on both — the majority verdict is `in_scope`, so restricting the mean to the agreeing runs
**deletes the one run that got it right** (all=4.400 → major=**6.150**; all=5.133 →
major=**7.175**).

⛔ **CORRECTED the same day, after reading the article in full.** This was first written up as
*"#135's step function, not a prompt defect, so no amount of prompt-writing reaches it"*. That
is wrong: §2 of the prompt names the article's exact shape **twice** — *"a policy change…
made after the fact"* and *"a warning that a practice is widespread"* — and the piece is both,
with a September cot ban, tripled Ofsted inspections and £8m attached. ⭐ **The leak is the
qualifier** *"especially as a trailing sentence"*, written for a throwaway mention, while here
the policy change is about a third of the body. The gate is flipping on a clause that invites
an exception this article satisfies, not at random. ⛔ **Not fixable now** — Phase B is running
against `prompt_hash 003cd35a5122` and editing the prompt would invalidate the corpus. It is a
**v8.1** item, testable for ~6 calls. ⚠️ And the fix is not obviously right: a bereaved family
securing a funded national regulation *is* a process going well for people on most readings, so
the §2 clause and the #107 predicate are doing the same work in two places — an owner question,
not a wording bug. `docs/evidence/2026-09-01-classA-full-read/`.

**Ruled: adjudicate after Phase B, from the run's own data**, which is cheaper than resolving it
first — the k=3 corpus pass measures the corpus-wide flip rate as a by-product. Candidate fixes,
none chosen: a higher k, an aggregation rule, or a §5 clause covering bereaved-parent
safety-campaign stories.

⚠️ **Acceptance criterion 1 therefore remains FAILING at the moment Phase B starts, knowingly.**
That is a recorded decision, not an oversight, and it must not be quietly read as passed later.

---

## 4. What is still open after this

- **The 47-row class-A supplement** — `tp_fp_status: adjudication-pending` in the manifest. They
  are rows 1–47 of the corpus file; re-measure the scope-flip rate across all 47 while
  adjudicating (measured **2/8** on a head sample, **1/9** on the class-A adverse rows).
- **B5's reading half.** The 18 adverse rows are full text again, but nobody has re-read them.
  The rule is *"three of five drafts reversed on a full read"*, and five of the class-A labels
  were adjudicated on 300-char excerpts — so a re-read can **change** a label, not merely
  confirm one.
- **Plan §9 Q4** (`social_cohesion_impact` at 0.20). ⭐ Does **not** gate anything: a weight
  change needs no re-labelling (ADR-001), and dropping a dimension is free. Only *adding* one
  would force a re-score.
