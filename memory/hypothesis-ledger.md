---
name: hypothesis-ledger
description: Index of every hypothesis this project has stated, its verdict, and where the experiment and result live. Read to RECALL prior work before proposing a new measurement — it is a pointer index, never a copy.
metadata:
  type: project
---

⭐ **A CONCLUDED experiment also gets a row in `experiments/registry.jsonl`** (adapted from `veen-systems/augur`): stable `EXP-NNN` id, `decision`, `spend_usd`, pointers. This ledger is where a hypothesis lives while it is OPEN and carries the Method; the registry is the cross-project index of what was decided. ⛔ Neither restates a number the evidence directory holds — `scripts/verification/check_experiment_registry.py` enforces that every registry figure is greppable in an artifact it cites.

# Hypothesis ledger

⛔ **CLOSED ROWS ARE IN [`archive/hypothesis-ledger-archive.md`](archive/hypothesis-ledger-archive.md) — grep BOTH before concluding an id does not exist.** 74 rows whose verdict opens REFUTED / CONFIRMED / RESOLVED (and carries no open marker) moved there verbatim, order kept, on 2026-09-27 (TODO item −1 step 3). Kept here: every open, partial, triggered or ⚠️ row, the 2026-09-25/26 section, and `H-CTX-*`. Any prose paragraphs stayed in place, so a note here may refer to an archived row.

**Created 2026-08-17**, because the question *"what have we already hypothesised, tested
and settled?"* had no answer short of reading **203 KB across 10 files in two repos**.

**This is an INDEX, not a store.** Every row points; no row restates a finding. The
one-home rule applies — a copy here would diverge from its source within a week, which is
the failure this project has already had with a duplicated article draft. If a row and
its source disagree, **the source wins and this row is the bug.**

## ⛔ What this file does NOT prove

*(Added 2026-08-17 after an index built the same day nearly caused four correct records to
be deleted. An index that invites a wrong inference is worse than no index, because it
arrives looking like evidence.)*

- **A verdict column is a REPORT of what the source file says, not a verification of it.**
  Rows reading `not stated in heading` mean the verdict was not retrievable by scanning —
  they do not mean "unresolved."
- **Two entries sharing a topic, a paper or an author are NOT duplicates.** Check the
  *claim*, never the citation. A shared-source sweep is a **candidate screen**; its output
  is "worth checking", never "confirmed". Getting this wrong on 2026-08-17 produced a list
  of seven apparent duplications of which **one** was real, and acting on it as given would
  have collapsed four correct registry rows.
- **Absence from this file is not absence from the project.** It indexes ten files in two
  repos; anything outside them is invisible here.
- ⚠️ **A claim that proposes DELETING something needs a higher bar than one that proposes
  believing something.** A reviewer's default of "plausible, proceed" is recoverable for a
  belief and irreversible for a deletion. Nothing in this project stated that rule before
  2026-08-17.

---

## ⚠️ Read first: the identifier namespace is not global

- ⛔ **`H4` is defined in FOUR different files** — `cd-v6-probe`, `google-news-corpus`,
  `prefilter-length-floor`, `solutions-v6-dimension`. A bare "H4" silently resolves to
  whichever file the reader has open and reads as correct. Same shape as
  `feedback-bare-issue-number-resolves-locally`. **Always qualify: `cd-v6 H4`.**
- ⛔ **`H1`, `H2`, `H3` collide between `cd-v6-probe` and `solutions-v6-dimension`.**
- Three schemes are in use with no convention: bare `H1..H7`, prefixed `H-D1` / `H-E1` /
  `H-L1`, and refutation-numbered `R1..R4`.
- ⛔ **Three hypothesis files carry NO identifiers at all** — `obituary-v4`,
  `opinion-genre`, `violence-promotion-v1`. Their claims cannot be cited except by
  quoting them, so they are effectively unreferenceable from anywhere else.

**Rule going forward: new hypotheses get a file-prefixed id** (`H-CD8`, `H-SOL5`), never
a bare number. Existing ids are NOT renamed — renaming would break every citation.

---

## Ledger

Status vocabulary is the source file's own. `not stated in heading` means the verdict may
be in the body but is not retrievable by scanning — a defect in the source, recorded here
rather than guessed at.

### The article record / block ledger — measurements, with a `H-AR` prefix

Added 2026-08-24. These are **stated-then-measured claims about the pipeline's own record**,
not about article content, so they sit apart from the lens hypotheses above. Source:
`docs/evidence/2026-08-23-article-record-instrument-audit.md` (F1–F10) and
`NexusMind/docs/ARTICLE_RECORD.md`. Population for every row: **165,196 rows / 72 files /
6 filters**, `filtered_20260821_205726` → `filtered_20260823_165255`.

| id | claim | verdict |
|---|---|---|

| `H-CX1` | Capping pointer rows in `CLAUDE.md` (#133 option 1) holds the file at a stable size | ⭐ **SPLIT VERDICT 2026-08-29 (`/audit-context`) — the prediction HIT and the mechanism did NOT.** Measured **37,445 B**, 17 B from the predicted 37,462 and well inside ±500. But the number is an artifact of a manual trim landing the day before the audit: with the cap in force the file went **37,149 → 38,204 B in 29.3 h (~864 B/day, ABOVE the ~486 B/day it was meant to stop)**, then `1f78b5b` trimmed it back. Attributing that growth: **pointer table +0 B, rest of file +1,055 B.** So the cap is **CONFIRMED within its own scope** — it holds the rows it governs at exactly zero — and the claim *holds the FILE at a stable size* is **REFUTED**: the growth relocated rather than stopped, and the treadmill continued one section over. ⚠️ **Had the audit run a day earlier it would have read 38,204 and called the same cap a failure** — the verdict was one commit wide, the [[feedback-window-is-part-of-a-source]] shape. Next lever must target the non-pointer body. Source: #133. ⭐ **LEVER FOUND AND PULLED 2026-08-29 (later): 2,047 B of the non-pointer body — 5.5% of the file — was four inline `<!-- verify: -->` GUARD blocks**, i.e. mechanism spending the budget it polices, the same defect that moved `check_index_budget.py` out of `memory/MEMORY.md` on 2026-08-17. Moved to `scripts/verification/check_doc_claims.py`; **37,445 → 35,394 B with nothing removed**. ⚠️ **This is a ONE-OFF, not a cap** — you can only evict the mechanism once. Whether the body then holds is [[H-CX3]]. |
| `H-CX3` | Evicting guard mechanism from `CLAUDE.md` bought runway but not a RATE — the non-pointer body resumes growing at its own pace | ⭐⭐ **2026-09-05 (third session) — THE MONOTONIC FLOOR THIS ROW NAMED IS GONE, and the measurement is the cleanest this row has had.** The session added **two** occurrence entries (*prove the outcome changed* 18th, *establish what it excludes* 22nd) — the exact content class the row called un-evictable — and `CLAUDE.md` moved **+0 B** (35,471 B before and after; last touched by `9a289dc`, an earlier session). All **+3,182 B** went to `memory/working-rules.md` (52,373 → 55,555). ⭐ **What changed is not discipline, it is the CONTRACT**: `check_doc_claims.py`'s `rule-ordinals` was INVERTED on 2026-09-04 so `CLAUDE.md` must NOT restate the count, and a copy that does not exist cannot grow. The row's own diagnosis — *the occurrence counters cannot be evicted while the check requires both layers to agree* — named the requirement, and removing the requirement removed the floor. ⚠️ **This does not confirm the row's headline**: the body can still grow for other reasons, and one session at +0 B is a single point, not a rate. **Trigger did NOT fire** — 35,471 B against the 37,000 B threshold, **runway 2,529 B**. Table padding measured again today: **−12 B**, i.e. the tables are already minimal and there is still no formatter configured. ✅ **CONFIRMED 2026-08-30 — the prediction held, and this measurement is not flattering to the measurer.** After the guard-mechanism eviction at `ebfdba5` (08-29 17:09) `CLAUDE.md` was **35,394 B**. Measured today: **35,763 B before this session touched it** (+369 B in ~16 h, across `40e1fd6` +189 and `5481419` +180, neither of them a pointer-table row), and **36,260 B after** — because `/curate` bumped a working rule's occurrence catalogue by **497 B**, which is the body growing at its own pace by exactly the mechanism the hypothesis names. Rate ≈**554 B/day** against the ~486 B/day the 08-27 audit measured, so the eviction bought **runway, not a rate** — as predicted. ⚠️ **Runway is now 3,740 B**, about a week at this rate. ⛔ Table padding is **0.7% (248 B)** and is not a lever here — the pressure is genuine content. ⛔⛔ **TRIGGER FIRED AGAIN 2026-09-04 (evening), a FOURTH time, and the eviction lever is still spent.** Measured by this row's own delta method: **37,463 B (09-03 08:40) → 37,938 B** after this session = **+475 B**, of which **+255 B is `CLAUDE.md` itself** (one occurrence bump, *establish what a source excludes* 17th → 18th, plus a `--no-config-update` warning on the calibration snippet) and the rest earlier the same day. ⭐ **The discipline held where it could**: nine new gotchas and the full 18th-occurrence story went to `memory/gotcha-log.md` and `memory/working-rules.md`, not to the project file — and the file still grew, because an always-loaded *ordinal* cannot be relocated while `check_doc_claims.py` requires both layers to agree. ⚠️ **That is the structural finding this row has been circling: the occurrence counters are the one class of content that CANNOT be evicted**, so they are a monotonic floor on the file's size. ⛔ Table padding is **248 B = 0.7%** and is still not a lever (no markdown formatter is configured, so there is nothing re-padding it either). **Runway 2,062 B.** ⛔⛔ **TRIGGER FIRED 2026-09-03 — `CLAUDE.md` exceeded the 37,000 B threshold this row set, and the prediction held a THIRD time.** Measured by this row's own method (delta across commits, never the level): post-eviction window **35,394 B (08-29 17:09) → 37,463 B (09-03 08:40) = +2,069 B over 111.5 h = 445 B/day** across 8 commits, against ~486 (08-27 audit) and ~554 (08-30). ⭐ **The body is +2,069 B larger than the eviction left it** — runway, not a rate, as predicted, and the eviction lever is spent. ⛔ **The naive whole-window figure is −29 B/day and is an artefact**: it spans the −2,051 B eviction, which is exactly the *quantity sampled only when it is reset* this row warns about — I computed it first and had to discard it. **Runway 2,537 B ≈ 5.7 days at 445 B/day.** Table padding is **248 B = 0.7%** and is still not a lever; the pressure is genuine content. ⚠️ This session added ~520 B to `CLAUDE.md` (one occurrence bump, 16th → 17th) and put the four new gotchas in `memory/gotcha-log.md` rather than the project file — the discipline the row asks for, and it did not stop the trend. **Revisit:** at the next `/audit-context`, and before any further occurrence-catalogue entry is added to `CLAUDE.md` rather than to `memory/working-rules.md`. Original wording follows. **OPEN, stated 2026-08-29 (later), and stated as a PREDICTION OF FAILURE so it cannot be claimed as a success afterwards.** #133's cap holds the pointer table at **+0 B** (confirmed) and H-CX1 showed the growth relocated to the body at **+1,055 B / 29.3 h**. This session removed **2,051 B** from that body — but by eviction, which is exhaustible: there are now **0** `<!-- verify: -->` blocks left in `CLAUDE.md` and a unit test (`test_no_verify_block_has_crept_back_into_claude_md`) stops them returning, so the same lever cannot be pulled twice. **Prediction: at the next `/audit-context`, the pointer table is still +0 B and the body is LARGER than 35,394 B minus whatever that audit trims** — i.e. the treadmill continues, one section over, exactly as H-CX1 found. ⛔ **Do not read a small file at the next audit as confirmation** — H-CX1's verdict was **one commit wide**, and a manual trim landing the day before produced a reading that looked like success. **Measure the DELTA across commits, never the level at audit time**: a quantity sampled only when it is reset cannot show a trend. **Method:** `git log --format='%H %ci' -- CLAUDE.md` then `git cat-file -s` per commit, split pointer-table vs body with `check_index_budget.py`'s own `_pointer_rows`. **Revisit trigger:** the next `/audit-context`, or `CLAUDE.md` exceeding **37,000 B**. ⛔ **The first draft of this row said *'or `--target project` reaching WARN'*, which was ALREADY TRUE when written** — the file stood at 35,394 B against a 35,000 SOFT, so the trigger fired on arrival and would have read as a finding rather than a threshold. *A trigger satisfied by the state that prompted it measures nothing.* Caught during the same session's `/curate`. Source: #133, H-CX1. |
| `H-CX4` | Mechanising a defect SHAPE reduces what an adversarial review lens then finds | **OPEN, stated 2026-09-05 (third session), and stated as the thing NOT claimed by `EXP-025` so it cannot be assumed later.** Four claim-shape checks were built from four of the five defects a `/review-changes` round found in `EXP-024` (`agent-ready-projects#127`; that round cost **557,442 tokens / 148 tool calls**, `agent-ready-projects#126`). ⛔ **What is measured**: the checks flagged **19 real sites** on a tree that had just passed the whole battery. ⛔ **What is NOT measured, and is this row**: that having them reduces the count or the cost of the NEXT review. ⚠️ **The first evidence points the other way** — the review OF the checks found **3 blockers and 10 warnings**, including that the flagship file survived its own mutation and that one of my fixes deleted a trigger instead of a defect. A mechanism is a new surface to get wrong, so the honest prior is *no reduction, possibly an increase, in the round that introduces it.* **Method:** at the next two `/review-changes` runs on work of comparable size, record (a) blockers+warnings found, (b) how many are of a shape a committed check already covers, and (c) the round's token and tool-call cost from the same source `#126` used. **Confirmed if** (b) trends to zero while (a) does not rise. ⛔ **Refuted, or at least not supported, if a check-covered shape keeps appearing** — that would mean the check is passing work the lens still catches, which is the `M5-survived` failure generalised. **Revisit trigger:** after the second qualifying `/review-changes` run, or immediately if any review finds a defect of one of the four registered shapes. ⭐ **ROUND 2 RECORDED, same day, and it is the round that BUILT the checks** — so it is a baseline, not yet a test of the hypothesis. (a) findings **3 blockers + 10 warnings**; (b) of a shape a committed check already covers: **0** — every one was a defect IN the new checks (a scan root matching zero files, a guard passing on a mention, a fix that deleted a trigger), which is a different population from the documents the checks police; (c) cost not captured in the same units as `agent-ready-projects#126` — **that is a gap in the method and the next round must record it**, or (c) is unfalsifiable. ⚠️ The honest reading of round 2 is that it says nothing either way about the hypothesis and everything about the prior: a mechanism is a new surface to get wrong. Round 3 is the first that can count. Source: `EXP-025`, `agent-ready-projects#127`, and the adopter comments filed on `#127`/`#126` 2026-09-05. |
| `H-CX2` | The adopted v1.31.0 #52 frontmatter fix is latent here, not dead | **OPEN, stated 2026-08-27.** 0 of the `SKILL.md` files on this machine have a pipe in a `description:` that is the LAST frontmatter key, so the fix currently fires on nothing. **Confirmed if** any future run reports it; **suspect the adoption** if a year passes with 0. Source: `docs/decisions/framework-adoption-history.md` |

⭐⭐ **`H-AR11` is why a pre-registered prediction earns its cost even when it is badly
wrong.** The prediction was made in `docs/TODO.md` before the deploy, so the error could be
*decomposed*; without it the 320 MB would have been a number with nothing to compare
against, and the real defect — an unsized bucket riding along in prose — would not have
been visible at all. See `feedback-predict-the-range-first` and
`feedback-closed-accounting-is-not-attribution` in the Claude Code auto-memory.

✅ **H-AR2, H-AR3 and H-AR4 were repaired on 2026-08-24** in NexusMind `e73c5ef`: `pop%` split into
`pres%` + `fill%`, `distinct` made exact to a visible cap, and the reader search qualified with
`RDRS-AMBIGUOUS` where it cannot attribute. 15 tests, 12 of which fail against the previous script.
The measured numbers above stand as the record of what the instrument was reporting when the
hypotheses were stated — they are NOT what it reports now.

⚠️ **`H-AR8`'s three exceptions are the row to read before acting on it.** Measured
invariance and article-level-ness are different properties, and `passed_prefilter` is
invariant for the same reason `_is_commerce` is: the rows that would vary it are gone.

### Corroboration / story matching — the active programme

⭐ **This topic's hypotheses do NOT live in the `H-n` scheme.** They live as
`INST-n` / `OBS-n` / `ART-n` / `MECH-n` / `PROP-n` / `ARG-n` in the **NexusMind V&V
registry**, `NexusMind/docs/vv/corroboration-dedup-registry.md` — **the only place in
either repo that records instrument certification**, i.e. whether the thing that produced
a number could have seen the failure it rules out.

| register | count (2026-08-17) | what it holds |
|---|---|---|
| `INST-1..15` | 15 | instruments, each with its **blind spot**, designer, certifier, degenerate baseline |
| `OBS-1..38` | 38 | claims from own data |
| `ART-1..30` | 30 | prior art |
| `MECH-1..7` | 7 | causal-mechanism claims |
| `PROP-1..7` | 7 | recommendations |
| `ARG-1..2` | 2 | reasoning chains |

- **Binding registry rule:** no own-data claim may rate above `EMERGING` while its
  instrument is `CERTIFIED: no`. Everything filed 2026-08-17 is therefore EMERGING.
- **Open competing hypotheses for this topic are pre-registered**, with predictions and
  decision rules stated *before* measurement:
  `NexusMind/docs/investigation/2026-08-17-cdcr-hypothesis-set-prereg.md` —
  **H-LINK** (transitive closure) · **H-GEOM** (embedding geometry / hubness) ·
  **H-REL** (topic ≠ event identity, llm-distillery#100) · **H-DEC** (a scalar threshold
  is the wrong decision rule) · **H-POP** (the corpus is pre-depleted upstream).
- Narrative + literature for the same topic: `corroboration-feature-hypotheses.md`.
- Publication track (pitch stage, **not a draft**):
  `NexusMind/docs/articles/percolation-in-similarity-clustering-pitch.md`.

### `cd-v6-probe-hypotheses.md` — cultural_discovery v6 probe (#98)

| id | claim | verdict |
|---|---|---|
| cd-v6 H1 | a multilingual embedding probe removes the per-language coverage gap | CONFIRMED |
| cd-v6 H2 | the probe beats the gate on **oracle** ground truth, not just agreement | REFUTED — screening is a regression vs the gate |
| cd-v6 H3 | the probe is batch-invariant; #95 has no probe analogue | CONFIRMED |
| cd-v6 H4 | `train_probe.py`'s reported val FN is optimistic by construction | stated in file, verdict in body |
| cd-v6 H5 | "the probe screens at least as much as the gate" | REFUTED (labelled in file) |
| cd-v6 H6 | "63.7% is fine because it matches nature_recovery v4's ~64%" | REFUTED (labelled) |
| cd-v6 H7 | "the 5 positives the lower threshold recovers are recall wins" | REFUTED — 4 of 5 are off-lens |

### `date-error-recency-boost-hypotheses.md` — `published_date` and the 1.3× under-24h boost

| id | claim | verdict |
|---|---|---|
| H-D1a | fabrication via `extract_date_from_rss_entry:106` inventing `now − 2h` | sub-hypothesis of H-D1 |
| H-D1b | timezone misparse (naive local read as UTC) | sub-hypothesis; ⚠️ conflated with H-D1a for most of 2026-08-14 |

### `enrichment-delta-hypotheses.md` — what enrichment actually moves

| id | claim | verdict |
|---|---|---|
| H-E2 | Google News stubs would gain **less** than corpus average, not more | not stated in heading |
| H-E3 | DeepSeek and Gemini differ in **slope**, not offset | not stated in heading |
| H-E4 | `discovery_novelty` is where oracle-prompt work pays for cd successors | not stated in heading |

### uplifting / Thriving oracle genre bias — `memory/uplifting-oracle-genre-hypotheses.md`

⛔ **This topic was already recorded on 2026-08-10 in
`datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md` and never opened as
its own item.** `datasets/adverse/` is a hypothesis home no index pointed at until now.

| id | claim | verdict |
|---|---|---|
| H-UP4 | research abstracts are the dominant FP class | PARTIAL — bounded at 13.6% of surfaced volume |
| H-UP5 | active learning on the current prompt REINFORCES the bias | ⏳ OPEN — the AL grader is the v7 oracle prompt, so it shares the defect it would audit |
| H-UP6 | a `primary_literature` cap removes the class without collateral | ⏳ OPEN — shadow shipped, undeployed, no data |

### human_thriving v8 — `H-V8` (RETIRED 2026-09-29 → `archive/hypothesis-ledger-archive.md` § *Retired 2026-09-29*)

⛔ v8 was superseded by v9 on 2026-09-25; the whole section moved verbatim. **Still OPEN there, and method questions beyond v8 — read the full row in the archive before acting:**

- **H-V8-10** — the non-Latin gap above the op-point is a *scoring* property, not a *collection* one.
- **H-V8-21** — the 1.60× b650 throughput swing has a loggable cause (clock/thermal or host contention).
- **H-V8-22** — at the OP-POINT an `e5-large` probe is not distinguishable from the Gemma student (viable Stage-2 replacement).
- **H-V8-23** — the one-article raw-recall gap (0.514 vs 0.486) is the dtype: bf16 in production vs fp32 in eval. ⚠️ Relevant to any box move (NexusMind#395).
- **H-V8-25** — the plain FP count is the wrong ADR-023 objective; weight FPs by `scope_verdict` (llm-distillery#149).
- **H-V8-27** — the 2026-09-07 outage is fully explained by a new filter's cold start (llm-distillery#152).
- **H-V8-39** — HALF-CONFIRMED: the bimodality was met before, but the documented fix does NOT transfer (the load-bearing half fails).

*H-V8-15 (triggered) and H-V8-16 (not established) are v8-training-specific and moot under v9; full text in the archive.*

### Adverse-pool consult / judge instrument — `H-AP` (2026-09-09, `docs/evidence/2026-09-09-adverse-pool-consult/`)

Opened while answering the NexusMind session's v9 adverse-example proposal. **$0, no oracle calls** —
re-analysis of EXP-031's committed panel plus the v8 label corpus. ⛔ **A four-lens review found 5
blockers and 8 warnings in the first draft of this section; every row below is the corrected form.**

⛔ **Before quoting any figure here:** the corpus score is `weighted_mean_all` (the producer's own
`aggregate_used`, `"all"` on 6,586/6,586 — an earlier `weighted_mean_major` fallback published
351/5.3% for the correct 316/4.798%); shares are **sample** shares unless marked design-weighted
(the draw spans 25.132×); the 4.50 op-point is **calibrated** while these labels are **raw**, so
every band is the permissive one; and `labels_v84_merged.jsonl` is **gitignored** (sha256
`b085b01b07d8…`).

| id | claim | verdict |
|---|---|---|
| H-AP1 | the harm rubric's `fits` clause (*"if you cannot name who is better off… it is not `fits`"*) leaks **judge fluency**, so on-promise rates are not comparable across language | ⏳ **OPEN, and WEAKER than first written.** Pooled `fits` falls **−15.1pp** (DeepSeek) / **−12.3pp** (Gemini) en→non-en. ⛔ **Within stratum the sign REVERSES under both judges** — v7_only −7.1/−2.4, both **−40.5/−39.3**, v8_only **+12.4/+13.7** — and the panel is stratified with English share varying by stratum (45.0 / 70.0 / 62.2%). **The pooled effect is substantially COMPOSITION**; *"both families, same direction"* does not survive the design variable. Method must stratify |
| H-AP2 | `harmful` is language-flat, so harm-rate work is unaffected by H-AP1 | ⏳ **OPEN, weakly supported.** DeepSeek 7.7%→5.1% (**6 vs 3 rows** — establishes very little), Gemini 24.4%→22.0% (19 vs 13). **Do not upgrade on this n** |

<!-- verify: R=/home/jeroen/repos/veen-systems/llm-distillery; L=$R/datasets/scored/human_thriving_v8/labels_v84_merged.jsonl; if [ ! -f "$L" ]; then echo "CANNOT VERIFY: $L absent (datasets/* is gitignored)"; else python3 $R/docs/evidence/2026-09-09-adverse-pool-consult/analyze.py >/dev/null && echo "H-AP5 core holds: analyze.py asserted 0 harm rows at >=4.0 and all above-op rows in_scope" ; fi -->

⛔ **H-AP5's core is a PROBE, not prose.** The annotation above runs `analyze.py`, whose six
assertions fail the run if a harm row reaches 4.0, if an above-op row carries any verdict but
`in_scope`, if `aggregate_used` stops being uniform, or if a row loses its design weight. It reports
**CANNOT VERIFY** when the gitignored corpus is absent rather than certifying the claim against a
missing file. Mutation-tested six ways on 2026-09-09: all six killed, control passes.

**Method pinned for H-AP1/H-AP2, before any call** — a **four**-arm competence check (the fourth is
the stratum control the review forced), each arm at **k=2** reading `unanimous` (never `majority`:
`Counter.most_common` on an even-k tie returns vote order dressed as a verdict):

1. ~50 **unchanged English** rows → the instrument's own reproducibility floor.
2. ~50 **unchanged non-English** rows → reproducibility on the population of interest.
3. ~50 **translated non-English** rows → the treatment.
4. ⛔ **All three arms drawn WITHIN a single stratum, or stratum-balanced and reported per stratum.**
   Pooling is what produced the sign reversal above.

**Directional prediction:** fluency predicts translation moves the flip rate **DOWN toward the
English floor**. A *reduction* is the positive signal. If arm 2 already flips above arm 1, that is
the signal on its own and arm 3 is confirmatory — arm 3 alone cannot separate fluency from
translationese.

⛔ **A positive control on the control is REQUIRED, and the FILE-TOTAL form is not enough.**
`judge.py`'s resume cache keys on `(id, pass)` in `<out.json>.partial.jsonl` (`judge.py:60-71`,
`:76-78`), so an arm reusing the main run's output path returns cached verdicts with **no API call**
and flips at **exactly 0%** — which the verdict rule would read as *"the contrast is sound and
earned."* **The reassuring answer is the one the bug produces.** Requirements:
- a distinct `<out.json>` per arm, and per-arm id suffixes so a merge cannot collide them;
- ⛔ **count lines APPENDED BY THIS PROCESS, or assert a non-zero call/spend counter — not the
  file's total.** An interrupted-then-rerun arm at its own path has exactly `n × k` lines with zero
  API calls and reproduces the same reassuring 0%. **A zero has to be earned, not inherited.**

⛔ **Do not borrow a floor across arms.** 45.8% is the **non-English** split-vote rate; DeepSeek's
own k=3 rate is **43.1%** (59/137) and Gemini at k=1 has no such quantity at all. Measure the floor
inside the arm on the same instrument. See `feedback-noise-floor-per-population` in the assistant
auto-memory.

### `solutions-v6-dimension-hypotheses.md` — `community_practice_strength` and re-weighting

| id | claim | verdict |
|---|---|---|
| sol-v6 H1 | the dimension is real, just **rare** | CONFIRMED |
| sol-v6 H2 | the student learns it *better* than the other six | CONFIRMED |
| sol-v6 H3 | the score ceiling really does differ by solution type | CONFIRMED |
| sol-v6 H4 | the concreteness gatekeeper is inert on the training corpus too (#94) | CONFIRMED |
| sol-v6 R1 | "the dimension is dead" | REFUTED three ways |
| sol-v6 R2 | "re-weighting would recover the ceiling" | REFUTED — inert at matched volume |
| sol-v6 R3 | "re-weighting fixes NM#319 enrichment starvation" | REFUTED — the gate reads the **normalized** score; a percentile CDF undoes any monotone rescale |
| sol-v6 R4 | a decomposition of the 83.1% into "40.0% tech-shaped + 43.1% …" | REFUTED |

### `prefilter-length-floor-hypotheses.md` — the 300-char floor (#93)

Uses `## Refuted` / `## Confirmed` / `## Open questions` sections rather than ids.
One identified open hypothesis:

| id | claim | verdict |
|---|---|---|
| H-L1 | the framework-leakage rationale for the floor | ⏳ **OPEN — asserted everywhere, measured nowhere.** The free natural experiment was run and is INCONCLUSIVE; the groundedness instrument was **invalid** and is recorded so nobody rebuilds it. Settling it needs oracle spend + owner approval |

### `google-news-corpus-hypotheses.md` — the GN population

Sectioned `CONFIRMED` / `REFUTED` / `CONFIRMED BY MIGRATION` / `UNTESTED` / **`THE
INSTRUMENT TRAP`**. ⛔ Five claims already refuted there, **four of them denominator
errors**. Its `H4` is a cross-reference, not a local hypothesis — do not cite it bare.

### Files with sections but no identifiers — ⛔ unreferenceable

| file | structure | consequence |
|---|---|---|
| `obituary-v4-hypotheses.md` | Confirmed · Learned · two v5 production-FN addenda · Open questions | claims can only be cited by quoting |
| `opinion-genre-hypotheses.md` | Traps · Population · Result · Open · Reproducing | ditto. ⛔ #121's issue body scores `solutions` at op-point 4.0; it is **2.25** |
| `violence-promotion-v1-hypotheses.md` | Confirmed · Settled 2026-08-01 (NM#281) · Settled 2026-08-23 (Q5/Q6/Q9/Q10) · **Settled 2026-08-26 (the shadow-log window)** · Open questions (incl. **Q11**, flagged volume rising) · Design decisions | ditto. ⛔ **Do not quote its flagged-but-kept share from memory** — it moved 90.6% → **88.3% pooled / 72.5–92.9% per cycle** the moment it was measured over more than one cycle; re-run `NexusMind/scripts/research/measure_shadow_kept_share.py` |

---

### Detector architecture — the frozen-mpnet pre-scorers (2026-09-10, `EXP-033`–`EXP-036`)

⛔ **Before quoting any figure here:** all four studies are on `paraphrase-multilingual-mpnet-base-v2` at the production 128-token window unless stated; obituary figures are the **heldout**, whose denominator differs by study (**1,562** raw / **1,537** leakage-free / the published **1,529** graded-excluded) — the exclusion is part of the figure. Evidence: `docs/evidence/2026-09-10-*` (four directories).

| id | claim | verdict |
|---|---|---|
| H-DET5 | `max(title, full)` recovers the body-dilution class at acceptable cost | ⏳ **OPEN — measured once, one model, one seed, NOT recommended.** Plain max +0.0494 recall / −0.0131 specificity; gated at 0.99, +0.0174 / −0.0016. **Recall-first (owner 2026-07-30) and ADR-023 point at different variants**, so it is an owner decision. Method to close it: re-measure across the `EXP-033` seed set before any config change. `EXP-035` |

### Cross-lens harm detector — `H-HD` (2026-09-10, `EXP-037`, `docs/evidence/2026-09-10-harm-detector/`)

| id | hypothesis | status |
|---|---|---|
| `H-HD1` | a detector trained on the v8 corpus's `harm_is_subject` labels transfers to harm **reaching readers**, not only to harm the oracle already catches | ⏳ **PARTLY CONFIRMED, and the pre-registered decision rule's middle bucket.** Primary: **2.0 of 9** both-judge-flagged panel rows (band **0–3**, 5 seeds) at the pre-registered threshold rule, against a shuffled-label null arm of **0.0 of 9** firing at **twice** the rate. ⛔ **Read it against the null, not against zero.** Test recall 0.4599–0.5766. ⇒ *stamp anyway (free, ADR-022); the $3.2–3.6 pool spend becomes a RANKED OPTION, not the only route.* `EXP-037` |
| `H-HD11` | the **178** minority-vote rows are a trainable positive class on their own | ⛔ **NOT ANSWERED — the instrument could not say yes.** Arm C caught **0 of 9**, but its test recall is **0.0417–0.0833** and it flags **0.00%** of the panel at every threshold ≥0.40, so the pre-registration's own positive control **fails**. ⭐ **That zero is about 136 positives being too few for this architecture, not about what the rows contain** — the `feedback-prove-the-bar-is-reachable` shape, caught by a control written before the run. Re-asking it needs a bigger positive class or a different head, and a new bar. `EXP-039` |
| `H-DEV2` | a lower op-point sits deeper in the score mass, so `solutions v6` (2.25) flips at least as often as the median filter | ⚠️ **UNFALSIFIABLE AS WRITTEN, and that is the keeper.** The median filter flipped **0** and `solutions v6` flipped **0**, so *"≥ median"* had no failing branch — the idea got no test at all. ⭐ **A comparative prediction against a statistic that can land on the floor cannot fail. Predict an absolute, or name the value that would refute it.** Same family as `feedback-prove-the-bar-is-reachable`, one level up: not an unreachable bar but an unmissable one. `EXP-041` |
| `H-HD14` | a downstream consumer can act on a NexusMind stamp cheaply — the *"cheap field check"* the cross-repo dependency rows assume | ⏳ **OPEN — DOWNGRADED 2026-09-22 from a ⛔ REFUTED I had no standing to write.** The claim (ovr.news's ingest is a whitelist at both boundaries, so a top-level stamp never reaches them) arrived **second-hand via a review session**, and a REFUTED status column is read as measured. ✅ **What I then verified on disk** (`/home/jeroen/repos/veen-systems/ovr.news`, one grep away the whole time): the whitelist is real in the sense that a NexusMind top-level field must be **explicitly declared and read** — `src/lib/data/types.ts:80` declares `content_quality` with the comment *"Pre-computed by NexusMind"*. ⛔ **But the precedent does NOT say what I recorded it as saying**: `content_quality` is **read** (`scripts/summarize.ts:476-478`), so it is evidence for the COST of a new field, not for unreachability. *"They cannot read these fields"* is too strong; *"they cannot read one they have not declared"* is what is supported. ⚠️ Still unverified here: the `metadata` projection and `ArticleInsert` claims, and the build-time-DB-read claim. Their counter-proposal (one namespaced object passed through whole, one migration instead of N) is **undecided**. ⛔ **No `EXP-` id and no evidence directory: this is not an experiment, it is a report plus a partial check** — stated so the missing citation is not read as an oversight |
| `H-HD16` | the harm flag rate above the op-point is HIGHEST on Solutions and Nature Recovery (both are about harm and its repair) and lowest on the Thriving lenses | ⛔ **REFUTED for Solutions, 2026-09-28** (`EXP-044`, `docs/evidence/2026-09-28-per-lens-harm-rates/`; prediction written before the run). At harm ≥ 0.5, rows ≥ each lens's own op-point, filtered population 2026-09-26..28: belonging **10.9%** (128/1,176), human_thriving 7.7% (18/235), uplifting 5.7% (143/2,496), nature_recovery 5.3% (**2/38 — undecidable**), solutions **1.9%** (22/1,153), cd 1.2% (7/589). ⛔ **Flag rates, not harm rates**: the detector's precision off the Thriving lenses is unmeasured. *Gloss, from 12 titles per lens, unlabelled:* solutions' flags read as responses to harm (supports "no cap"); belonging's read mostly harm-dominated (≥ 0.7 sample only; an earlier unsaved sample read "mixed" — corrected same day) |
| `H-HD17` | Belonging's 10.9% harm-flag rate is off-lens junk that a per-lens cap should remove | ⏳ **OPEN — hand-check DONE 2026-10-01, cap decision pending.** Verdicts (Claude's TITLE-ONLY calls, accepted by the owner wholesale) in the TSV below: **belonging 35/50 junk (70%) at harm ≥ 0.5, 15/18 (83%) at ≥ 0.8; human_thriving v9 4/19 (21%)** — supports a cap on belonging only. ⚠️ belonging is a 50-of-136 sample; title-only judgment. **Owner ruled 2026-10-01: belonging cap = SHADOW FIRST** (stamp-only, logs what a cap would drop; threshold decided later on that real population, not this sample); **v9: NO cap.** ⚠️ **The cap does not reach ovr EXP-025's weak belonging picks** (grievance/threat framing): "San communities call for ownership" is belonging 9.99, harm **0.22**; three others are unstamped. The fix is **belonging v2 to the #130 ruling** (owner agreed 2026-10-01; `docs/TODO.md` START HERE item 0); the shadow cap is its before/after instrument. *(History:)* raised 2026-09-28. The committed ≥ 0.7 sample (12 rows) reads mostly harm-dominated — missing flood victims, a robbery, vandalism, a fire — with a memorial and an anti-racism mobilisation as the plausibly constitutive ones. **Test:** hand-label ~50 belonging rows at harm ≥ 0.5 above 4.0 as junk / fits-the-lens (list pulled 2026-09-28, `docs/evidence/2026-09-28-per-lens-harm-rates/harm_handcheck_list.tsv`, awaiting the owner); a cap only if most are junk, at a threshold chosen on that sample. The same check on the 18 `human_thriving v9` rows (only the 8 at ≥ 0.7 were read: mostly good-outcome stories) — the `uplifting v7` cap is moot, Thriving reads v9 since 2026-09-26 |

⭐ **The methodological keeper is the NULL ARM, not the headline.** The real arm flags **2.04%** of
the panel and the null flags **4.09%** — so a raw catch count would have flattered a detector that
fires more. **A catch count is only interpretable beside the firing rate of a signal-free arm at
the same threshold rule.** Same family as `feedback-prove-the-bar-is-reachable`, inverted: prove
the bar is not reachable *by accident*.

⚠️ **The panel is `uplifting v7` / `human_thriving v8` display-eligible rows only.** It says nothing
about `solutions`, `belonging`, `nature_recovery` or `cultural_discovery` — which `#156` also wants
stamped, and where the same content may be **constitutive** rather than harmful.

⚠️ **What none of H-DET1–H-DET5 can see: all 344 obituary heldout positives are Latin-script.** That corpus would return a guaranteed zero on any multilingual question, which is why H-DET6 had to go to production data instead. ⛔ **This is the instrument register these five rows would otherwise lack** — see the structural gap noted below.

| **H-CTX-1** | writing a lesson down prevents its recurrence | ⛔ **REFUTED 2026-09-22, and this is the row that should change how this project works.** The NM#319 in-sample-percentile tautology was recorded in **THREE** places on the task's own routing path — `memory/gotcha-log.md:7209` (a dated entry with that exact title), `docs/RUNBOOK.md`'s Phase E section, and `filters/human_thriving/v8/STATUS.md:149` — and a session recomputed the same number on 15× the rows and published it as a **correction**. ⭐ **Three written warnings, zero fired.** The prose remedy is not weakly effective here, it is uncorrelated: what caught it was `/review-changes`, at ~900 K subagent tokens. **A fourth copy is not the fix.** Method for the successor: a check that fires without being read — the three `proposed` rows in `memory/gotcha-log.md` § *Mechanized*, each needing a seeded positive. Revisit when any of them goes `live`. **#163** |
| **H-CTX-2** | the always-loaded layer is where context rot happens, so capping it is the fix | ⛔ **REFUTED 2026-09-22 — `#133` capped the right file and the growth moved next door.** Measured: the bare-"continue" path is **605,198 B / 7,362 lines** before any work starts, of which `docs/TODO.md` alone is **546,771 B / 6,977 lines**; `memory/gotcha-log.md` is **715,093 B**; `CLAUDE.md` routes to **30** topic files. The always-loaded budget PASSES (51,681 of 60,000) while the pointed-at layer has no budget at all — by design, because budgeting it would push the growth one level further out, which is what `#133` did. ⚠️ **Open, and the successor hypothesis is unstated on purpose**: it is not obvious that a budget anywhere is the right instrument, versus retiring dated records out of the routed path. Owner's four verbs 2026-09-22: **prune, thin, mechanize, retire**. **#163** |
| **H-CTX-3** | halving the always-loaded project file (`CLAUDE.md` 38,141 → 17,749 chars, 2026-09-26) loses no behaviour: every operative clause survives there or one pointer away | 🔶 **OPEN — untested in use.** Measured only at write time: every backticked span, issue id and number dropped is still present in the pointed file, and a review lens restored the five operative CLAUSES the token check could not see. **Method:** over the next ~10 sessions, count review findings or owner corrections whose root cause is a rule that USED to be spelled out in `CLAUDE.md` (diff `git show 83ddf6b:CLAUDE.md`). **Refuted if** ≥2 such; **supported if** 0 and the session-start read cost stays down. **Revisit:** 2026-10-15 or at the next `/audit-context`. |

### Thriving v9, lens assignment and the judge-vs-owner gap — `H-TV` / `H-LA` / `H-JO` (2026-09-25/26)

| id | hypothesis | status |
|---|---|---|
| `H-JO1` | Claude judges under the written rubric read a lens the way the owner does | ⛔ **REFUTED for Nature recovery** (owner vs judges 3/10, owner vs ORACLE 8/10: the judges are stricter on population counts, translocations, natural recoveries, colonisation, reserve expansion); **partial for Thriving** (14–16/20 blind; the owner is broader on everyday good things and stricter on relief-from-harm). ⚠️ Consequence: the NR miss audit's ~47% precision is SUSPECT. `docs/evidence/2026-09-25-nature-recovery-relabel/PILOT_RESULT.md` |
| `H-LA2` | "narrow lens first" places multi-lens articles where a reader would | ⏳ **SUPPORTED vs the JUDGES, NOT the owner**: 78% vs 66% (Recovery 18/21 vs 3/21); the owner delegated the labelling. Merged in ovr.news #372 on 2026-09-26. ▶ Test: the owner's reaction to shared articles on the live site (TODO item A1). Known weak spot: Belonging ranks above Solutions/Thriving (2/10). |
| `H-TV5` | v9 alone keeps the Thriving tab adequately full once uplifting v7's articles age out | ⏳ **OPEN — the owner's call, not a metric.** **Owner 2026-10-01: "seems all right"** (mid-drain; final look ~2026-10-06). Measured: over 5 cycles v9 put 62 on site vs v7's 681; the live tab held 706 Thriving articles 2026-09-27, mostly v7's. Test: the owner watches the tab over the ~10-day drain. If thin but right → seed band + one negative-ratio run; if wrong stories → labels/prompt (compensation ruling is not in v9's prompt) |
| `H-DP2` | the sklearn that unpickles obituary v5 / violence v1 in production is the one they were built with | ⏳ **UNTESTABLE as recorded** — neither `training_config.json` records `sklearn_version` (manifest `build_stack_unrecorded`). Test: rebuild under the #158 banded trainer (records it), or recover it from the pickles' `_sklearn_version` state without unpickling |

## Where the *experiments* live, as opposed to the hypotheses

| kind | home |
|---|---|
| instruments + blind spots + **certification** | `NexusMind/docs/vv/corroboration-dedup-registry.md` §2 (dedup/corroboration only) |
| pre-registered predictions & decision rules | `NexusMind/docs/investigation/*-prereg.md` |
| runnable scripts | `NexusMind/scripts/research/` — `nm188_*` are 2026-08-17's, each with a provenance header carrying run date, batch, md5 discipline, results and scope limits |
| dead ends, so they are not retried | `calibration-history.md` § Dead Ends |
| the failure catalogue behind the working rules | `working-rules.md`, `gotcha-log.md` |

⛔ **No equivalent of the V&V registry exists for the FILTER work.** Nine of the ten
hypothesis files above have no instrument register, so for those topics "what could this
measurement not have seen" is nowhere recorded. That is the largest structural gap in the
project's evidence base, and it is why `feedback-hand-built-population` keeps recurring.

## Maintenance

Add a row **when a hypothesis is created**, not when it resolves — an unresolved
hypothesis nobody can find is the case this file exists for. Keep every row to one line;
if a row needs a paragraph, the paragraph belongs in the source file.

⚠️ **Audited 2026-09-12 (`/audit-context` + `/curate`): 31 rows, 0 past-due `Review by:`,
and THREE whose verdict is not retrievable by scanning — `H-E2`, `H-E3`, `H-E4`** (all in
the `enrichment-delta` / oracle-slope cluster). The verdict may be in the body of the source
file; it is not in the heading, so a scan cannot recover it and every future audit will
re-report them. **Surfaced, not resolved** — resolving means reading each source and applying
its Method, which is the engineer's call. ⛔ Not a defect in this file: it is recorded above
that `not stated in heading` means exactly this, and the source is what needs the heading.

⚠️ **That session created NO new hypotheses.** It was framework/tooling work (drift adoption,
structural audit, curation) with no empirical claim about the pipeline, so there is nothing
to add. Recorded because *"no rows added"* and *"nobody checked"* are otherwise
indistinguishable.

Related: [[corroboration-feature-hypotheses]], [[calibration-history]], [[working-rules]],
[[cross-repo-prioritization]].
