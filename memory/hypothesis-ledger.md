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

| `H-CX4` | Mechanising a defect SHAPE reduces what an adversarial review lens then finds | **OPEN, stated 2026-09-05 (third session), and stated as the thing NOT claimed by `EXP-025` so it cannot be assumed later.** Four claim-shape checks were built from four of the five defects a `/review-changes` round found in `EXP-024` (`agent-ready-projects#127`; that round cost **557,442 tokens / 148 tool calls**, `agent-ready-projects#126`). ⛔ **What is measured**: the checks flagged **19 real sites** on a tree that had just passed the whole battery. ⛔ **What is NOT measured, and is this row**: that having them reduces the count or the cost of the NEXT review. ⚠️ **The first evidence points the other way** — the review OF the checks found **3 blockers and 10 warnings**, including that the flagship file survived its own mutation and that one of my fixes deleted a trigger instead of a defect. A mechanism is a new surface to get wrong, so the honest prior is *no reduction, possibly an increase, in the round that introduces it.* **Method:** at the next two `/review-changes` runs on work of comparable size, record (a) blockers+warnings found, (b) how many are of a shape a committed check already covers, and (c) the round's token and tool-call cost from the same source `#126` used. **Confirmed if** (b) trends to zero while (a) does not rise. ⛔ **Refuted, or at least not supported, if a check-covered shape keeps appearing** — that would mean the check is passing work the lens still catches, which is the `M5-survived` failure generalised. **Revisit trigger:** after the second qualifying `/review-changes` run, or immediately if any review finds a defect of one of the four registered shapes. ⭐ **ROUND 2 RECORDED, same day, and it is the round that BUILT the checks** — so it is a baseline, not yet a test of the hypothesis. (a) findings **3 blockers + 10 warnings**; (b) of a shape a committed check already covers: **0** — every one was a defect IN the new checks (a scan root matching zero files, a guard passing on a mention, a fix that deleted a trigger), which is a different population from the documents the checks police; (c) cost not captured in the same units as `agent-ready-projects#126` — **that is a gap in the method and the next round must record it**, or (c) is unfalsifiable. ⚠️ The honest reading of round 2 is that it says nothing either way about the hypothesis and everything about the prior: a mechanism is a new surface to get wrong. Round 3 is the first that can count. Source: `EXP-025`, `agent-ready-projects#127`, and the adopter comments filed on `#127`/`#126` 2026-09-05. |
| `H-CX2` | The adopted v1.31.0 #52 frontmatter fix is latent here, not dead | **OPEN, stated 2026-08-27.** 0 of the `SKILL.md` files on this machine have a pipe in a `description:` that is the LAST frontmatter key, so the fix currently fires on nothing. **Confirmed if** any future run reports it; **suspect the adoption** if a year passes with 0. Source: `docs/decisions/framework-adoption-history.md` |

Prose notes on the archived H-AR rows (H-AR11, H-AR2–4, H-AR8) and the `H-CX3` row: `archive/hypothesis-ledger-archive.md` § *Moved 2026-10-14*.

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
| cd-v6 H4 | `train_probe.py`'s reported val FN is optimistic by construction | stated in file, verdict in body |
| cd-v6 H1–H3, H5–H7 | *closed (CONFIRMED / REFUTED) — moved 2026-10-12 to [`archive/hypothesis-ledger-archive.md`](archive/hypothesis-ledger-archive.md)* | |

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

All eight rows (sol-v6 H1–H4, R1–R4) are closed (CONFIRMED / REFUTED) — moved 2026-10-12 to [`archive/hypothesis-ledger-archive.md`](archive/hypothesis-ledger-archive.md).

### `prefilter-length-floor-hypotheses.md` — the 300-char floor (#93)

Uses `## Refuted` / `## Confirmed` / `## Open questions` sections rather than ids.
One identified open hypothesis:

| id | claim | verdict |
|---|---|---|
| H-L1 | the framework-leakage rationale for the floor | ⏳ **OPEN — asserted everywhere, measured nowhere.** The free natural experiment was run and is INCONCLUSIVE; the groundedness instrument was **invalid** and is recorded so nobody rebuilds it. Settling it needs oracle spend + owner approval |

### `google-news-corpus-hypotheses.md` — the GN population

Sectioned `UNTESTED` / **`THE INSTRUMENT TRAP`**; its `CONFIRMED` / `REFUTED` / `CONFIRMED BY MIGRATION` sections MOVED
2026-10-12 to `archive/google-news-corpus-hypotheses-archive.md`. ⛔ Five claims refuted there, **four of them denominator
errors**. Its `H4` is a cross-reference, not a local hypothesis — do not cite it bare.

### Files with sections but no identifiers — ⛔ unreferenceable

| file | structure | consequence |
|---|---|---|
| `obituary-v4-hypotheses.md` | Confirmed · Learned · two v5 production-FN addenda · Open questions | claims can only be cited by quoting |
| `opinion-genre-hypotheses.md` | Traps · Population · Result · Open · Reproducing | ditto. ⛔ #121's issue body scores `solutions` at op-point 4.0; it is **2.25** |
| `violence-promotion-v1-hypotheses.md` | (closed sections MOVED 2026-10-12 to `archive/violence-promotion-v1-hypotheses-archive.md`; was:) Confirmed · Settled 2026-08-01 (NM#281) · Settled 2026-08-23 (Q5/Q6/Q9/Q10) · **Settled 2026-08-26 (the shadow-log window)** · Open questions (incl. **Q11**, flagged volume rising) · Design decisions | ditto. ⛔ **Do not quote its flagged-but-kept share from memory** — it moved 90.6% → **88.3% pooled / 72.5–92.9% per cycle** the moment it was measured over more than one cycle; re-run `NexusMind/scripts/research/measure_shadow_kept_share.py` |

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
| `H-HD14` | a downstream consumer can act on a NexusMind stamp cheaply — the *"cheap field check"* the cross-repo dependency rows assume | ⏳ **OPEN — DOWNGRADED 2026-09-22 from a ⛔ REFUTED I had no standing to write.** The claim (ovr.news's ingest is a whitelist at both boundaries, so a top-level stamp never reaches them) arrived **second-hand via a review session**, and a REFUTED status column is read as measured. ✅ **What I then verified on disk** (`/home/jeroen/repos/veen-systems/ovr.news`, one grep away the whole time): the whitelist is real in the sense that a NexusMind top-level field must be **explicitly declared and read** — `src/lib/data/types.ts:80` declares `content_quality` with the comment *"Pre-computed by NexusMind"*. ⛔ **But the precedent does NOT say what I recorded it as saying**: `content_quality` is **read** (`scripts/summarize.ts:476-478`), so it is evidence for the COST of a new field, not for unreachability. *"They cannot read these fields"* is too strong; *"they cannot read one they have not declared"* is what is supported. ⚠️ Still unverified here: the `metadata` projection and `ArticleInsert` claims, and the build-time-DB-read claim. Their counter-proposal (one namespaced object passed through whole, one migration instead of N) is **undecided**. ⛔ **No `EXP-` id and no evidence directory: this is not an experiment, it is a report plus a partial check** — stated so the missing citation is not read as an oversight |
| `H-HD17` | Belonging's 10.9% harm-flag rate is off-lens junk that a per-lens cap should remove | ⏳ **OPEN — hand-check DONE 2026-10-01, cap decision pending.** Verdicts (Claude's TITLE-ONLY calls, accepted by the owner wholesale) in the TSV below: **belonging 35/50 junk (70%) at harm ≥ 0.5, 15/18 (83%) at ≥ 0.8; human_thriving v9 4/19 (21%)** — supports a cap on belonging only. ⚠️ belonging is a 50-of-136 sample; title-only judgment. **Owner ruled 2026-10-01: belonging cap = SHADOW FIRST** (stamp-only, logs what a cap would drop; threshold decided later on that real population, not this sample); **v9: NO cap.** ⚠️ **The cap does not reach ovr EXP-025's weak belonging picks** (grievance/threat framing): "San communities call for ownership" is belonging 9.99, harm **0.22**; three others are unstamped. The fix is **belonging v2 to the #130 ruling** (owner agreed 2026-10-01; `docs/TODO.md` START HERE item 0); the shadow cap is its before/after instrument. *(History:)* raised 2026-09-28. The committed ≥ 0.7 sample (12 rows) reads mostly harm-dominated — missing flood victims, a robbery, vandalism, a fire — with a memorial and an anti-racism mobilisation as the plausibly constitutive ones. **Test:** hand-label ~50 belonging rows at harm ≥ 0.5 above 4.0 as junk / fits-the-lens (list pulled 2026-09-28, `docs/evidence/2026-09-28-per-lens-harm-rates/harm_handcheck_list.tsv`, awaiting the owner); a cap only if most are junk, at a threshold chosen on that sample. The same check on the 18 `human_thriving v9` rows (only the 8 at ≥ 0.7 were read: mostly good-outcome stories) — the `uplifting v7` cap is moot, Thriving reads v9 since 2026-09-26 |

*`H-HD11` (NOT ANSWERED — the instrument could not say yes) and `H-DEV2` (UNFALSIFIABLE as written) — MOVED to [`archive/hypothesis-ledger-archive.md`](archive/hypothesis-ledger-archive.md) § *Moved 2026-10-16*.*

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
| **H-CTX-3** | halving the always-loaded project file (`CLAUDE.md` 38,141 → 17,749 chars, 2026-09-26) loses no behaviour: every operative clause survives there or one pointer away | 🔶 **OPEN — untested in use.** Measured only at write time: every backticked span, issue id and number dropped is still present in the pointed file, and a review lens restored the five operative CLAUSES the token check could not see. **Method:** over the next ~10 sessions, count review findings or owner corrections whose root cause is a rule that USED to be spelled out in `CLAUDE.md` (diff `git show 83ddf6b:CLAUDE.md`). **Refuted if** ≥2 such; **supported if** 0 and the session-start read cost stays down. **Revisit:** 2026-10-15 or at the next `/audit-context`. |

### Thriving v9, lens assignment and the judge-vs-owner gap — `H-TV` / `H-LA` / `H-JO` (2026-09-25/26)

| id | hypothesis | status |
|---|---|---|
| `H-JO1` | Claude judges under the written rubric read a lens the way the owner does | ⛔ **REFUTED for Nature recovery** (owner vs judges 3/10, owner vs ORACLE 8/10: the judges are stricter on population counts, translocations, natural recoveries, colonisation, reserve expansion); **partial for Thriving** (14–16/20 blind; the owner is broader on everyday good things and stricter on relief-from-harm). ⚠️ Consequence: the NR miss audit's ~47% precision is SUSPECT. `docs/evidence/2026-09-25-nature-recovery-relabel/PILOT_RESULT.md` |
| `H-LA2` | "narrow lens first" places multi-lens articles where a reader would | ⏳ **SUPPORTED vs the JUDGES, NOT the owner**: 78% vs 66% (Recovery 18/21 vs 3/21); the owner delegated the labelling. Merged in ducroq/ovr.news#372 on 2026-09-26. ▶ Test: the owner's reaction to articles on the live site — when the owner pastes one that looks mis-tabbed, find it in that day's five-lens page capture (2026-10-15..11-15, `~/lab/llm-distillery/inbox/ovr-lens-pages/`, `docs/TODO.md` item 0a) and record expected vs actual tab. Known weak spot: Belonging ranks above Solutions/Thriving (2/10). |
| `H-TV5` | v9 alone keeps the Thriving tab adequately full once uplifting v7's articles age out | ⏳ **OPEN — the owner's call, not a metric.** **Owner 2026-10-01: "seems all right"** (mid-drain; final look ~2026-10-06). Measured: over 5 cycles v9 put 62 on site vs v7's 681; the live tab held 706 Thriving articles 2026-09-27, mostly v7's. Test: the owner watches the tab over the ~10-day drain. If thin but right → seed band + one negative-ratio run; if wrong stories → labels/prompt (compensation ruling is not in v9's prompt) |
| `H-DP2` | the sklearn that unpickles obituary v5 / violence v1 in production is the one they were built with | ⏳ **UNTESTABLE as recorded** — neither `training_config.json` records `sklearn_version` (manifest `build_stack_unrecorded`). Test: rebuild under the #158 banded trainer (records it), or recover it from the pickles' `_sklearn_version` state without unpickling |

### Belonging v2 to the #130 ruling — `H-BV` (2026-10-01/02, `docs/evidence/2026-10-01-belonging-v2-test-set/`)

All verdicts are Claude's labels; the owner has not reviewed them. Every oracle figure is ONE run per arm
unless it says otherwise. The one repeat measured: 3/110 verdicts flip with the same prompt.

| id | hypothesis | status |
|---|---|---|
| H-BV1 | The v1 ORACLE prompt (not only the student) rewards the topic and the grievance shape | **SUPPORTED, one run.** The v1 prompt on Gemini Flash passes 41/65 F rows, including all 5 EXP-025 rows and 23/31 hand-check F rows. The student is copying its oracle here |
| H-BV2 | The student surfaces off-lens content that the v1 oracle rejects: a defect separate from the student's known false-positive rate | ⏳ **OPEN, NOT established (review 2026-10-02).** 15/28 rejections is consistent with the documented false-positive rate (spec 0.985 at a low base rate). 5 of the 15 sit within 0.16 of 4.0, and the oracle and student read different windows (560+240 words vs 512 tokens). A v2 relabel and retrain would replace the student anyway |
| H-BV3 | A prompt that defines community_fabric by the ruling (STEP 1b), with the code gatekeeper doing the gating, cuts F passers without losing P | **DEV score only, NOT on held-out.** The test set leaked into the prompt's examples (review 2026-10-02), so 41 → 11–14/65 F is a development score. v1 recall is 8/8 on the original P rows; 11 easy rows were added for v1 score ≥ 6.15. Held-out sample (150 student-surfaced rows): v1 passes 121, v2 passes 71, and Claude read 33 of those 71 as junk. Drafts 1 and 2 cannot be ranked |
| H-BV5 | A stronger oracle removes the residual junk | ⏳ **OPEN, weakly supported (probe B).** Pro passes 15/33 of the junk that Flash passed, and 15/16 fits. The baseline is circular, Pro's false positives on Flash's rejects are unmeasured, and cost is not measured. Test: Pro on all 150 rows plus a Flash re-run control. ⏸ PARKED 2026-10-02 with the v2 prompt: the next lever is the training data (`docs/TODO.md` item 0) |
| H-BV6 | Much of the residual "junk" is a DEFINITION gap: a prosocial event or act (a donation, a homecoming, a crew that works well) vs a community's own lasting bonds as the subject | ✅ **RULED 2026-10-02 (owner): MIDDLE.** Ordinary people acting together count (a volunteer clean-up, neighbours helping). One-off gifts by a person/company/official and crowds at an event do not. Robinvale P; marches after harm qualify when the gathering is the story (Morwell P; Charleville B in the test set, still adverse). Later the same day the owner added the "doing" test (ovr.news `docs/BRAND.md:84`) to the training rubric, then ruled three boundaries at the exemplar review: festivals only when people carry them, the doing test beats ruling (c) for training, programmes only when the participants build. Evidence README § *Owner rulings*; `docs/evidence/2026-10-02-belonging-adjudication/rubric_belonging.md` |
| H-BV7 | Belonging's off-lens surfacing is rooted in v1's TRAINING DATA (positives mostly feel-good stories from positive-news feeds, 794/7,370), so a v9-style reshape (adjudicated labels + production positives and hard negatives) moves the reader-facing junk share where prompt rules did not | ⏳ **OPEN — SUPPORTED offline, reader side pending (2026-10-09):** the reshape alone (v1_adj1) FAILED held-out set 1; adding 135 hard negatives (c2b = **v3**) PASSED set 3 (Δspec +0.350 [+0.322, +0.376], partly by band construction) and is LIVE since 2026-10-09. On ovr EXP-028's 40 published stories v3 passes 9/27 panel-weak, keeps 9/13 panel-good. ▶ **Decisive test: ovr's 2026-10-23 panel on v3-scored rows only** — and, since 2026-10-10, the owner's top-of-page bar (H-BB6: ≤ 6 single-person in the top 30) (rollback rule, `filters/belonging/v3/STATUS.md`). *(Earlier:)* SUPPORTED on the label side (2026-10-02 evening): blind judges keep **4/66** (rubric v1) and **1/39** (rubric v2) of v1's ≥ 4.0 rows in scope; one-off/single-person moments are the largest out class (27/66). The retrain itself is not started (plan revised, `~/.claude/plans/splendid-purring-acorn.md`). The count is measured; "mostly feel-good" is Claude's read of 60 titles. Test: `docs/TODO.md` item 0, phases 6–7 (gate on v1's test ids, live junk audit). Evidence `docs/evidence/2026-10-02-belonging-reader-snapshot/` |
| H-BV8 | Belonging under-RANKS the external curator's community-action stories rather than missing them: they reach scoring but cannot win ovr's top-50-per-lens cap | ⏳ **OPEN, partly measured.** 17 of 46 matched picks pass (4.09–6.72 raw); 6 sit below the lowest stored score of the window (5.62); whether any won a slot is NOT checked. The curator data is local-only (`datasets/external_curator/`). Test: phase 7 re-ranks them under the retrained student. ⚠️ **Demoted 2026-10-02 (owner):** the curator is a generalist feed (its picks pass uplifting 38/45, solutions 32/45, belonging 17/46; `docs/evidence/2026-10-02-belonging-adjudication/README.md`); it is no longer belonging's yardstick, a footnote at most |
| H-BV10 | Lived belonging (rubric v2) is RARE in what the student passes | ⏳ **SUPPORTED, small n, judge-relative, rubric v2.0:** random passers **1/58 = 1.7% [0.3%, 9.1%]** (pilot v2 prod 0/30 + pilot v3 random 1/28; population excludes off-lens, GN, < 300 chars). Retrieved candidates 2/48 is a stratum rate, not a passer rate. v2.1 widened the line, so the v2.1 rate is unmeasured. Claude's title-based predictions overshot three times (15–35%, 25–50%, 25–50%). ⚠️ Judges are Claude; n=76 for the rate. Evidence `docs/evidence/2026-10-02-belonging-adjudication/README.md` |
| H-BV12 | An LLM scope oracle given rubric v2 can screen for belonging candidates | ⏳ **OPEN, promising:** on 242 judged rows (post-override labels, `cannot_judge` excluded), Gemini Flash spec **0.954** / recall **0.889**; Claude Opus 5.5 (subagents) 0.986 / 0.778; DeepSeek 0.991 / 0.556 (rubric v2.0). Supported: Gemini over DeepSeek only; recall is anchored to Claude's exemplars, not to the owner. On rubric v2.1 Gemini reads **0.921** against STALE v2.0 labels. ⚠️ recall n=17 (13 exemplars); Claude's figure shares the judges' bias. **Next test:** re-label the set under v2.1, recompute. Evidence `docs/evidence/2026-10-02-belonging-adjudication/CALIBRATION.md` |

### Belonging adj1 build and gate — `H-BB` (2026-10-07, `docs/evidence/2026-10-07-belonging-adj1-build/`, `docs/evidence/2026-10-03-belonging-heldout/GATE.md`)

| id | hypothesis | status |
|---|---|---|
| H-BB3 | Run-to-run (row order) score noise above the 0.16 floor is driven by long texts that fill the 512-token window | ⏳ **OPEN, suggestive:** v1 forward vs reversed max \|Δ\| 0.453; 10 of 12 rows with \|Δ\| > 0.01 are cut (long) rows, which are 45% of the set. 0 verdict flips. Unisolated from the device term |
| H-BB4 | Commerce v1 @0.95 blocks mostly journalism, and 0.990 releases it without letting commerce reach readers | ✅ **CONFIRMED by outcome (NM#527, 2026-10-08):** ~70% of blocks were journalism (two judges, n=230); after 0.990 blocks per cycle 34,385 → 13,597 (39.5%, predicted 38.9%). ⚠️ Reader-side effect after deploy NOT measured (pre-deploy: 4 of 228 sampled blocked rows would have reached a reader — 3 journalism, 1 commerce) |
| H-BB5 | v3's pass rate at ovr's normalized ≥ 4.5 display gate (among its raw ≥ 4.0 rows) stays inside v1's per-file range until the refit, because both versions map through v1's curve (4.5 normalized ≈ raw ~5.1) | ⏳ **OPEN, SUPPORTED on 3 files:** v1's last 7 files 469/872 = 54% (47–66% per file); v3's first three files (2026-10-09 01:20 / 05:14 / 09:36) 12/19, 17/27, 11/19 = **40/65 = 62%**, inside v1's range. v3 volume over those files: 65 of 11,608 rows raw ≥ 4.0 (0.56%; per file 0.39–0.86%). 0 `stage1_low` rows at raw ≥ 4.0 (probe never surfaces, re-checked after the version bump). An earlier "< 100%" trigger compared ovr.db's published top-50 with all raw ≥ 4.0 rows and fired falsely. **Test:** same measure over several v3 files; clearly below 47% → earlier refit WITH ovr (`docs/TODO.md` item 0) |
| H-BB6 | belonging v3 over-surfaces single-person / single-family stories at the TOP of ovr.news's Belonging page, because (a) its 135 new hard negatives were all `out_gift_official` / `out_harm_is_story` and the 121 `out_one_moment` ones were left out (owner, 2026-10-08), and/or (b) v3's calibration caps community_fabric, so ranking among passes is decided by the other dimensions | ⏳ **OPEN, the effect is MEASURED, the cause is not (2026-10-12).** The owner counted 10 personal of the live page's top 30 (9 pre-registered + 1 corrected slip) against the ruled bar of ≤ 6, so v3 fails it. The `focus` tag replaces `out_one_moment` (owner ruling). Its local tagger qwen3.8:27b agreed with the owner on 26/30 but undercounts (7 vs the corrected 10), so a qwen count is a floor. Cause (a) was tested by c2c (EXP-048, personal training rows scaled down) and c2d (EXP-050, cap-aware): both FAILED the recall guard; lever CLOSED 2026-10-15 (H-BB8). See H-BB7 and H-BB8. Evidence `docs/evidence/2026-10-12-belonging-personal-tag/`; llm-distillery#170. Earlier status text: archive, 2026-10-12. Next: `docs/TODO.md` item 0a |
| H-BB7 | The page's personal-story excess comes partly from how ovr.news RANKS (normalized score, recency, editor), not only from v3's raw score | ✅ **MECHANISM MEASURED (2026-10-13): RECENCY.** ovr.news's formula (normalized × 0.85^days × 1.3 if < 24 h; the editor's reorders are undone by a re-sort) reproduces the live page 507/507 and the owner-labelled 10-12 page's top 30 at 30/30 (the build time is fitted). 29–30 of the top 30 are < 24 h old (10-12: 43 fresh rows in a 758-row window), and 0 are in the top 30 by score alone. So the bar ≈ the personal share of one day's passes. `docs/evidence/2026-10-13-belonging-site-ranking/`. Earlier: all 30 rows of the site-ranked page are in the 33,393-row draw, but only 7 are in v3's raw top 30. The raw top 30 holds 5 personal by qwen; the page held 7 by qwen and 10 by the owner. Which site term reorders it is not measured. **Test:** a pre-registered count on the site's own ranking (ovr.db build query), v3 vs a candidate re-ranked the same way. **Owner ruled 2026-10-14:** default ranking → H (5 strongest < 24 h first, then score within age bands; ovr.news ships it), a reader selector later; the bar is a WEEKLY AVERAGE, re-baselined on H. **H LIVE 2026-10-15** (ovr.news commit `07cdb7e0`, ducroq/ovr.news#391); offline replay EXP-049; on-site re-baseline ≥ 2026-10-22 (`docs/TODO.md` item 0a) |
| H-BB8 | Scaling personal training rows down lowers personal stories without costing community stories | ❌ **REFUTED twice (c2c EXP-048, c2d EXP-050); lever CLOSED by the owner 2026-10-15.** Full row: `archive/hypothesis-ledger-archive.md` § *Moved 2026-10-15* |

### Student base model — `H-SB` (2026-10-15, llm-distillery#180)

| id | hypothesis | status |
|---|---|---|
| H-SB1 | A Kev decision-model base (Qwen3.5 + pointer head, open weights) beats Gemma-3-1B on specificity at matched recall, and the gain comes from decision pre-training, not the newer base (Qwen3.5-0.8B-Base arm is the control) | ⏳ **OPEN, filed not scheduled (owner 2026-10-15).** Not tested. Prior pick (ADR-006, MAE, 1.2% gap) does not settle it under ADR-023. Method: #180 |

### Oracle canary and data practice — `H-OC` (2026-10-16, #177 / #176, `EXP-051` / `EXP-052`)

| id | hypothesis | status |
|---|---|---|
| `H-OC1` | the human_thriving canary at k = 1 FAILS a REAL oracle model swap, not only the simulated one-point drift | ⏳ **OPEN — untestable until a swap.** EXP-052 showed a simulated ~0.5-point drift fails (16–20 flips vs 7); EXP-042's V4→V4.1 swap moved 3 of 12 hand-picked rows, a different population. **Method:** on the next vendor model notice (DeepSeek or Gemini), run `canary.py run` within a day and keep the record. **Refuted if** a notified swap PASSES. |
| `H-OC2` | an unchanged oracle FAILS (or NO-VERDICTs) the k = 1 canary less than 1 run in 10 | ⏳ **OPEN — 5 out-of-sample clean runs so far, max 5 flips.** **Method:** over the next 10 canary records with an unchanged `served_model`, count FAIL + NO-VERDICT. **Refuted if** ≥ 2. A false alarm costs a re-investigation, never a label. **Revisit:** at the 10th record (`datasets/canary/human_thriving/passes/`). |
| `H-OC3` | DeepSeek's `system_fingerprint` moves when the served model changes, and only then | ⏳ **OPEN (#157).** `aeb56401ca74…` on every call 2026-10-12 → 10-16. **Method:** the canary records carry it (`served`); compare across records, and at the next swap. |
| `H-ND1` | near-duplicate leakage inflates the live gates' numbers (#176) | ❌ **REFUTED at e5 ≥ 0.93 (EXP-051):** v9's gate without its 5–6 leaks is still a WIN; belonging v3's gate set has 0 rows ≥ 0.93. ⚠️ 0.93 misses rewritten copies (control 0.83–0.98). |

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
