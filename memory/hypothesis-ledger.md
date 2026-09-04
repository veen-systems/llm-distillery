---
name: hypothesis-ledger
description: Index of every hypothesis this project has stated, its verdict, and where the experiment and result live. Read to RECALL prior work before proposing a new measurement — it is a pointer index, never a copy.
metadata:
  type: project
---

⭐ **A CONCLUDED experiment also gets a row in `experiments/registry.jsonl`** (adapted from `veen-systems/augur`): stable `EXP-NNN` id, `decision`, `spend_usd`, pointers. This ledger is where a hypothesis lives while it is OPEN and carries the Method; the registry is the cross-project index of what was decided. ⛔ Neither restates a number the evidence directory holds — `scripts/verification/check_experiment_registry.py` enforces that every registry figure is greppable in an artifact it cites.

# Hypothesis ledger

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
| `H-AR1` | The record is 132 fields | **REFUTED** — 132 is a 2-cycle window; 212 at `--cycles 12`. The set grows with the window because `metadata.*` is per-source |
| `H-AR2` | `pop%` is the share of rows a field is present on | **REFUTED, NOW FIXED 2026-08-24** — it was `populated/seen`; `_post_enriched` prints 100.0% on 23 rows. NM#401 |
| `H-AR3` | `distinct` is a distinct-value count | **REFUTED, NOW FIXED 2026-08-24** — censored at 13; `metadata.doi` is 403. NM#401 |
| `H-AR4` | The reader column measures consumers | **REFUTED, NOW MITIGATED 2026-08-24** for ~40% of fields — bare leaf-name grep; 14 fields share a leaf and carry identical counts by construction. NM#401 |
| `H-AR5` | The NexusMind-added layer is declared nowhere | **REFUTED** — Contract A declares 39, Contract B 51; the undeclared set is **20 fields** by container counting — ⚠️ **19 by EXACT-path counting** (2026-08-25), the difference being `nexus_mind_attributes.*.scores.<dims>`, where the container is declared and the per-dimension NAMES are not. Both readings are defensible; say which you used |
| `H-AR6` | `image_analysis.extracted_image_dimensions` is dead (0% populated) | **REFUTED** — nullable dict; its parent path is recorded only on rows where it is null. `.height`/`.width` are 100% |
| `H-AR7` | The 59 census findings are 59 problems | **REFUTED** — ≥16 are not independent (11 by-design per-filter constants, 5 one fact per filter) |
| `H-AR8` | `source_quality` and other lens fields are per-lens | **REFUTED for 13 of 31** — identical across every lens on all 2,495 multi-lens articles, 0 differing. ⚠️ **3 more are invariant only because the VALUE is constant** and must not be hoisted. NM#402 |
| `H-AR9` | Blocked articles can be recovered from the archive | **REFUTED** — `FilteredArchiver` reads `filtered_dir`, which a dropped article never enters. This is what the block ledger fixes |
| `H-AR10` | Enforcing a gate preserves its signal in the record | **REFUTED** — enforcement removes the positives before persistence, so the stamp goes constant-by-construction. Demonstrated by `violence_promotion` on 2026-08-23 |

| `H-AR11` | The block ledger's first flush is ~22,237 rows / ~42 MB | **REFUTED, 7.6× low** — 168,486 rows / 320 MB, measured 2026-08-24 13:05. ⭐ **The SHAPE is the finding: the gate-blocked portion, the only part actually sized, was 22,494 against 22,237 — 1.2% off. All the excess is `freshness.too_old` at 142,899 rows, 85% of the ledger, which the estimate carried as an unquantified prose clause ("plus freshness and dedup rows"). THE BUCKET NOBODY COUNTED HELD SIX SEVENTHS OF THE VOLUME.** A single aggregate would have said "wrong by 7.6×" and hidden that the model of the gates was nearly exact while the model of freshness did not exist |
| `H-AR12` | Enabling the ledger writes a comparable volume EVERY cycle | ✅ **REFUTED 2026-08-24 17:04** — second flush is **3,257 rows / 6.72 MB**, not another 320 MB. The written-id index works: the pipeline's own line reads *"3257 new blocked articles written (3169 with content), 165308 already recorded"*, and 168,486 + 3,257 = 171,743 = the verifier's row count (exit 0, all schema-conformant). The 320 MB first flush was the standing backlog, one-time. **Steady state ≈ 3.3K rows / 6.7 MB per cycle ⇒ ~20K rows / ~40 MB per day at 6 cycles**, so off-site backup is affordable and no reasons-list change is needed. ⚠️ `too_old` is still **87.6% of the increment** (2,852 of 3,257) — the shape from H-AR11 persists at the margin. ⚠️ The index grows **~73.5 bytes/id** (12.36 → 12.59 MB for 3,257 ids) ⇒ **~1.4-1.6 MB/day**. ⛔ **"unbounded" was WRONG, corrected 2026-08-26**: `BlockLedger._prune_index` runs on EVERY flush and drops entries past `index_retention_days` (default 30, not overridden). Nothing had aged out because the ledger was one day old — measured 08-25 17:17: **194,406 entries / 14.25 MB spanning 08-24 11:05 → 08-25 15:17**. The curve seen so far is the FILL phase; arithmetic puts the plateau near **45 MB**. ⚠️ Pruning is by FIRST-SEEN stamp (a hit does not refresh it), which is correct: 30 days > the 14-day raw retention, so no entry is dropped while its article can still be re-read |
| `H-AR13` | The 13 lens fields H-AR8 found identical are article-level facts | **REFUTED for 2 of 13, 2026-08-25** — re-measured over **4,838** multi-lens articles: `content_length` and `original_content_length` differ on **4**, every one an article post-enriched mid-cycle. It is **11**, not 13. ⭐ The 4 differing and the 4 enriched are the SAME 4, 0 unexplained either way |
| `H-AR14` | `_corroboration` is a declared-but-dead field | ⛔ **REFUTED, and it was MY claim** — 0 persisted rows **plus an in-process reader** (`display_ranking._corroboration_boost`) is an INTERMEDIATE. Its description said so all along. Contract B 1.18.1 marks it `x-intermediate`; ⭐ **a description is not a machine-readable fact** |
| `H-AR15` | A nullable object's `pop%` describes how often it is filled | **REFUTED** — `flatten` recorded the parent only when the value was NULL, so the number was the count of its own ABSENCE. `image_analysis.extracted_image_dimensions` read `0 of 1,410` while its own `.height`/`.width` read 100%. Every census run before 2026-08-25 mis-reported nullable dicts by construction |
| `H-AR16` | Post-scoring enrichment reaches every lens, so a lens's `content_length` is comparable across lenses | **REFUTED, and it is SYSTEMATIC** — pooled over 12 cycles / 31,596 multi-lens articles: **18 (0.057%)** differ, median gap **26×** (196 vs 4,559 chars), `solutions` short **18 of 18**. `enabled_filters` is an ORDERED list; the lenses at the front can never benefit from a later fetch. NM#339 |
| `H-AR17` | `source_quality.source_unreliable` is a dead declaration (0 rows) | **REFUTED — it is RARE, and the reason is two repos upstream.** It needs `source_tier == "override"` AND `credibility_score < 3.0`. `override` = a curator entry in FluxusSource `config/domains/credibility.yaml`: 733 entries, exactly **5** below 3.0, of which **3 are `enabled: false` feeds** (editorial, `rss_russian.yaml`, unblock = NM#253) and 2 are in no source config. Over **237,132 distinct articles** (510 files, 08-11 .. 08-25) `override`'s minimum credibility is **3.8** and all **204** sub-3.0 articles are `verified` tier, which the predicate excludes. **The two halves of the AND are anti-correlated by policy.** Marked `x-rare` + FALSIFIER (Contract B 1.18.2). ⛔ **The defect it surfaced is the keeper**: the record schema's `corroboration` is `additionalProperties: false` and the flag was declared in neither that schema nor the dual-write's copied set — the first row carrying it would have been the first to FAIL VALIDATION |
| `H-AR18` | `other_sources[].source_tier` describes the corroborating source | **REFUTED for 51.4% of entries** — a cross-run entry (`cross_run: true`) hardcodes `"unknown"` / `null` because the saved cluster record never persisted quality. **104,201 of 202,893 entries** over 110,645 articles, and **97.7% of the field's `unknown` is bookkeeping** (104,201 of 106,652). Within-run: 70,121 verified / 20,431 override / 5,689 curated / 2,451 genuinely unknown. **Never average credibility over this field.** NM#404 |
| `H-AR19` | `placements` is how many lenses saw the article, so it is always the lens count | **REFUTED — 3 exceptions in 194,405 rows, two mechanisms, both benign.** It is how many lenses filed a LEDGER-REASON block in the cycle where the article was FIRST recorded. (a) An earlier loop dropped it for a non-ledger reason — one article is marked processed in exactly the first three filters and none of the last three (verified against `data/raw/.processed_ids_*.json`, an instrument independent of the ledger). (b) ⭐ **The freshness cutoff MOVES BETWEEN LOOPS**: `load_articles` recomputes `now − max_article_age_days` once per FILTER, so one cycle runs against six cutoffs seconds apart; the other two published **12 s** and **6 s** before the cutoff in force. All three maps are SUFFIXES of `enabled_filters` order (~1-in-720 by chance). ⚠️ Normal is **5** from 2026-08-25, so the pre-pause 5-placement anomaly is no longer distinguishable |
| `H-CX1` | Capping pointer rows in `CLAUDE.md` (#133 option 1) holds the file at a stable size | ⭐ **SPLIT VERDICT 2026-08-29 (`/audit-context`) — the prediction HIT and the mechanism did NOT.** Measured **37,445 B**, 17 B from the predicted 37,462 and well inside ±500. But the number is an artifact of a manual trim landing the day before the audit: with the cap in force the file went **37,149 → 38,204 B in 29.3 h (~864 B/day, ABOVE the ~486 B/day it was meant to stop)**, then `1f78b5b` trimmed it back. Attributing that growth: **pointer table +0 B, rest of file +1,055 B.** So the cap is **CONFIRMED within its own scope** — it holds the rows it governs at exactly zero — and the claim *holds the FILE at a stable size* is **REFUTED**: the growth relocated rather than stopped, and the treadmill continued one section over. ⚠️ **Had the audit run a day earlier it would have read 38,204 and called the same cap a failure** — the verdict was one commit wide, the [[feedback-window-is-part-of-a-source]] shape. Next lever must target the non-pointer body. Source: #133. ⭐ **LEVER FOUND AND PULLED 2026-08-29 (later): 2,047 B of the non-pointer body — 5.5% of the file — was four inline `<!-- verify: -->` GUARD blocks**, i.e. mechanism spending the budget it polices, the same defect that moved `check_index_budget.py` out of `memory/MEMORY.md` on 2026-08-17. Moved to `scripts/verification/check_doc_claims.py`; **37,445 → 35,394 B with nothing removed**. ⚠️ **This is a ONE-OFF, not a cap** — you can only evict the mechanism once. Whether the body then holds is [[H-CX3]]. |
| `H-CX3` | Evicting guard mechanism from `CLAUDE.md` bought runway but not a RATE — the non-pointer body resumes growing at its own pace | ✅ **CONFIRMED 2026-08-30 — the prediction held, and this measurement is not flattering to the measurer.** After the guard-mechanism eviction at `ebfdba5` (08-29 17:09) `CLAUDE.md` was **35,394 B**. Measured today: **35,763 B before this session touched it** (+369 B in ~16 h, across `40e1fd6` +189 and `5481419` +180, neither of them a pointer-table row), and **36,260 B after** — because `/curate` bumped a working rule's occurrence catalogue by **497 B**, which is the body growing at its own pace by exactly the mechanism the hypothesis names. Rate ≈**554 B/day** against the ~486 B/day the 08-27 audit measured, so the eviction bought **runway, not a rate** — as predicted. ⚠️ **Runway is now 3,740 B**, about a week at this rate. ⛔ Table padding is **0.7% (248 B)** and is not a lever here — the pressure is genuine content. ⛔⛔ **TRIGGER FIRED AGAIN 2026-09-04 (evening), a FOURTH time, and the eviction lever is still spent.** Measured by this row's own delta method: **37,463 B (09-03 08:40) → 37,938 B** after this session = **+475 B**, of which **+255 B is `CLAUDE.md` itself** (one occurrence bump, *establish what a source excludes* 17th → 18th, plus a `--no-config-update` warning on the calibration snippet) and the rest earlier the same day. ⭐ **The discipline held where it could**: nine new gotchas and the full 18th-occurrence story went to `memory/gotcha-log.md` and `memory/working-rules.md`, not to the project file — and the file still grew, because an always-loaded *ordinal* cannot be relocated while `check_doc_claims.py` requires both layers to agree. ⚠️ **That is the structural finding this row has been circling: the occurrence counters are the one class of content that CANNOT be evicted**, so they are a monotonic floor on the file's size. ⛔ Table padding is **248 B = 0.7%** and is still not a lever (no markdown formatter is configured, so there is nothing re-padding it either). **Runway 2,062 B.** ⛔⛔ **TRIGGER FIRED 2026-09-03 — `CLAUDE.md` exceeded the 37,000 B threshold this row set, and the prediction held a THIRD time.** Measured by this row's own method (delta across commits, never the level): post-eviction window **35,394 B (08-29 17:09) → 37,463 B (09-03 08:40) = +2,069 B over 111.5 h = 445 B/day** across 8 commits, against ~486 (08-27 audit) and ~554 (08-30). ⭐ **The body is +2,069 B larger than the eviction left it** — runway, not a rate, as predicted, and the eviction lever is spent. ⛔ **The naive whole-window figure is −29 B/day and is an artefact**: it spans the −2,051 B eviction, which is exactly the *quantity sampled only when it is reset* this row warns about — I computed it first and had to discard it. **Runway 2,537 B ≈ 5.7 days at 445 B/day.** Table padding is **248 B = 0.7%** and is still not a lever; the pressure is genuine content. ⚠️ This session added ~520 B to `CLAUDE.md` (one occurrence bump, 16th → 17th) and put the four new gotchas in `memory/gotcha-log.md` rather than the project file — the discipline the row asks for, and it did not stop the trend. **Revisit:** at the next `/audit-context`, and before any further occurrence-catalogue entry is added to `CLAUDE.md` rather than to `memory/working-rules.md`. Original wording follows. **OPEN, stated 2026-08-29 (later), and stated as a PREDICTION OF FAILURE so it cannot be claimed as a success afterwards.** #133's cap holds the pointer table at **+0 B** (confirmed) and H-CX1 showed the growth relocated to the body at **+1,055 B / 29.3 h**. This session removed **2,051 B** from that body — but by eviction, which is exhaustible: there are now **0** `<!-- verify: -->` blocks left in `CLAUDE.md` and a unit test (`test_no_verify_block_has_crept_back_into_claude_md`) stops them returning, so the same lever cannot be pulled twice. **Prediction: at the next `/audit-context`, the pointer table is still +0 B and the body is LARGER than 35,394 B minus whatever that audit trims** — i.e. the treadmill continues, one section over, exactly as H-CX1 found. ⛔ **Do not read a small file at the next audit as confirmation** — H-CX1's verdict was **one commit wide**, and a manual trim landing the day before produced a reading that looked like success. **Measure the DELTA across commits, never the level at audit time**: a quantity sampled only when it is reset cannot show a trend. **Method:** `git log --format='%H %ci' -- CLAUDE.md` then `git cat-file -s` per commit, split pointer-table vs body with `check_index_budget.py`'s own `_pointer_rows`. **Revisit trigger:** the next `/audit-context`, or `CLAUDE.md` exceeding **37,000 B**. ⛔ **The first draft of this row said *'or `--target project` reaching WARN'*, which was ALREADY TRUE when written** — the file stood at 35,394 B against a 35,000 SOFT, so the trigger fired on arrival and would have read as a finding rather than a threshold. *A trigger satisfied by the state that prompted it measures nothing.* Caught during the same session's `/curate`. Source: #133, H-CX1. |
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
| H-D1 | the anomaly is **fabrication**, attributed by a fingerprint that no longer exists | ✅ RESOLVED |
| H-D1a | fabrication via `extract_date_from_rss_entry:106` inventing `now − 2h` | sub-hypothesis of H-D1 |
| H-D1b | timezone misparse (naive local read as UTC) | sub-hypothesis; ⚠️ conflated with H-D1a for most of 2026-08-14 |
| H-D2 | the 6h spike is arXiv **walking with the collection timer**; "6.00h" is a binning artifact | ✅ RESOLVED |

### `enrichment-delta-hypotheses.md` — what enrichment actually moves

| id | claim | verdict |
|---|---|---|
| H-E1 | `nature_recovery v4`'s zero delta is genuine, not a thin-fit artefact | ✅ RESOLVED — it is a *cancellation*; enrichment pays on evidence-quality dimensions |
| H-E2 | Google News stubs would gain **less** than corpus average, not more | not stated in heading |
| H-E3 | DeepSeek and Gemini differ in **slope**, not offset | not stated in heading |
| H-E4 | `discovery_novelty` is where oracle-prompt work pays for cd successors | not stated in heading |

### uplifting / Thriving oracle genre bias — `memory/uplifting-oracle-genre-hypotheses.md`

⛔ **This topic was already recorded on 2026-08-10 in
`datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md` and never opened as
its own item.** `datasets/adverse/` is a hypothesis home no index pointed at until now.

| id | claim | verdict |
|---|---|---|
| H-UP1 | the Thriving FPs are the STUDENT drifting from its labels | REFUTED |
| H-UP2 | the ORACLE PROMPT rates research artefacts on-lens | CONFIRMED — 55.2% vs 30.6%, p = 0.0001 |
| H-UP3 | raising the op-point fixes it | REFUTED, and blocked by `MAX_NORMALIZATION_RAW_MIN` |
| H-UP4 | research abstracts are the dominant FP class | PARTIAL — bounded at 13.6% of surfaced volume |
| H-UP5 | active learning on the current prompt REINFORCES the bias | ⏳ OPEN — the AL grader is the v7 oracle prompt, so it shares the defect it would audit |
| H-UP6 | a `primary_literature` cap removes the class without collateral | ⏳ OPEN — shadow shipped, undeployed, no data |

### human_thriving v8 prompt — order, cost and stability (2026-08-28, `H-V8`)

Home: `docs/evidence/2026-08-28-v8-prompt-order-probe/`. Spend $0.12, 90 calls, n=30, k=1
per arm plus one null arm. ⛔ **No parity claim is established here** — see H-V8-3.

| id | claim | verdict |
|---|---|---|
| H-V8-1 | the v8 prompt's cache ceiling is unreachable in practice (a ceiling is not a rate) | **REFUTED** — 0.0% → **90.2%** median on warm rows against a 95.8% ceiling, on the real call site |
| H-V8-2 | moving the article to the end is content-preserving | **CONFIRMED** — non-blank line multiset differs by one `---` (+5 chars) |
| H-V8-3 | the reorder changes the labels | ✅ **CONFIRMED 2026-08-29, n=200.** It does, and it is **directional**: mean(reordered − as-is) **−0.239** production-mix (95% CI [−0.409, −0.080]), **−0.443** at the boundary ([−0.764, −0.138]); mean \|Δ\| **0.630 between arms vs a 0.312 within-arm null on the same rows**; survives a sign-flip permutation (p=0.0049) and source clustering ([−0.410, −0.078]). ⛔ **NOT multiplicity-robust** — 0.0049 does not clear 0.05/16, the family the script prints; the Bonferroni interval first cited was seed noise (above zero in 408/500 replications) and is removed. No family was pre-registered. The 08-28 probe missed it because its null was *a second run*, not a matched pair-level null with an interval. ⛔ **The "not just the gate" corollary is WITHDRAWN (review 2026-08-29)**: pooled the strata, and conditions on `scope_verdict`, an outcome the treatment changes — per stratum, R n=21 **[−0.516, +0.036] includes zero**. ✅ **RULED 2026-08-30: the reorder is ADOPTED for Phase B — on H-V8-9's LABEL argument, not on cost.** That ordering is the whole ruling: this row is why a cheaper prompt that moves labels could not be adopted for being cheaper. The multiplicity question is **still open and was not answered** — no pre-registered family was ever run. `docs/decisions/2026-08-30-v8-phase-b-rulings.md` §1 |
| H-V8-4 | the v8 prompt is stable run-to-run at k=1 | **REFUTED**, and given an interval 2026-08-29 (n=200). Per-pair scope-binary disagreement **5.3%** production-mix ([2.7%, 8.4%]); at the boundary **6.7%** as-is / **9.3%** reordered — *name the arm, they are different prompts.* ⛔ **NOT "smaller than the probe's 13%"**: 4/30's CI is **[3.8%, 30.7%]** and contains every one of these (Fisher p=0.118; **p=0.4648** against the like-for-like boundary cell — the earlier 0.722 named no cell and used a non-comparable one). The design-weighting story is plausible and **indistinguishable from n=30 noise**. Op-point crossing between identical runs: **2.4%** production-mix, **12.7%** boundary |
| H-V8-5 | that instability is decoder jitter | **REFUTED** — it is the **scope gate**: gate-stable rows move a median **0.100**, gate-flipped **3.750**; 4 of 5 large movers are gate flips, 0 of 25 small movers are |
| **H-V8-6** | `k=4` averaging fixes it (cousin-3 arithmetic) | ✅ **ANSWERED 2026-08-29, $0 — k=3 IS the stopping point, and the answer came early by re-analysis, not at Phase B scale.** `docs/evidence/2026-08-29-v8-k3-residual/`. A beta-binomial fitted across rows (the per-row gate probability is not estimable from 3 draws; `p̂=s/3` asserts certainty the data lacks) gives **P(k-majority ≠ limit verdict)**: arm A production-mix **k=1 3.65% → k=3 2.39% → k=5 1.89%**, 95% CI on k=3 [1.30%, 4.09%] (400 row-cluster bootstraps, refit inside each). ⭐ **k=5 removes 32 rows of 6,590 for 1.67× the bill; k=7 another 20.** The curve is flat because the residual is rows whose gate probability is genuinely ~0.5 — irreducible, the same fact as #135's *1/√k cannot touch a Bernoulli*, now priced. ⚠️ **The k=1→k=3 prize is ~83 rows, not ~860**: the plan argues k≥3 from the FLIP rate (rows that would differ on a re-run); the decision quantity is rows k=3 actually FIXES. The ruling stands, for a reason a third the size. ⭐ Validation: the fit reproduces a quantity it never saw — per-pair gate disagreement **5.21% predicted vs 5.3% measured** (A/R), 5.08 vs 5.3 (B/R), 9.63 vs 9.3 (A/B), 7.24 vs 6.7 (B/B). Recovery + range controls in the script; ⛔ one control's hand value was written wrong (25% for a fair coin; the right value is 50%) and **the estimator was right**. **Neither arm is more stable on the production mix** (2.39 vs 2.32) — stability is not an argument for or against the reorder; at the boundary the reordered arm is worse (4.46 vs 3.31). |
| H-V8-7 | the reorder's saving pays for the k≥3 that H-V8-4 forces | ⚠️ **ARITHMETIC HOLDS, PREMISE DOES NOT — and the numbers were SUPERSEDED 2026-08-29 by H-V8-8.** The figures first recorded here ($0.000519 vs $0.002736 per article; k=3 on 6,590 rows ≈$6.9 vs ≈$21.7) used Phase A's repeat discount, which **does not exist for a corpus pass**: it was measured by re-scoring the SAME 200 articles, so the whole request cached. Measured on never-before-scored rows, each pass costs **$0.000506–0.000534/article** regardless of how many passes precede it. **Corrected: k=3 over 6,590 rows is ≈$10.32 reordered vs ≈$54.08 as-is — still 5.2×, and now measured.** The premise objection is unchanged and is the reason this stays ⚠️ rather than ✅: H-V8-3 established the two arms do not produce the same labels, so this is not a saving on one thing, it is a price difference between two different oracles. Registry `EXP-004`. |
| **H-V8-8** | the k=3 repeat discount survives at corpus scale | ✅ **ANSWERED 2026-08-29, $0.1044, 200 calls, 0 errors — and the answer is NO, for a reason the hypothesis did not anticipate.** `docs/evidence/2026-08-29-v8-cache-ttl/`. **(a) The prefix cache DOES survive**: four 50-row passes of never-before-scored articles at t+0/30/60/90 min hit **exactly 10,368 tokens on every one of 200 calls**, zero cold-prefix rows, rate flat at 88.7–89.4%. **(b) But the repeat discount was never about time.** Phase A's $0.000266/article came from re-scoring THE SAME 200 ARTICLES, so the whole request was cached. A corpus pass scores 6,590 *different* articles each time: only the prefix caches, each article's tokens are re-paid. Measured on fresh rows: **$0.000506–0.000534 per article per pass**. ⛔ **k=3 on 6,590 rows is ≈$10.32 reordered / ≈$54.08 as-is — NOT the $6.92 this project had been quoting**, and it lands on Phase A's own *no-discount* branch. The reorder is **5.2× cheaper at corpus scale, measured**. ⭐ The per-row discriminator was pre-registered and is what makes it readable: prefix-only hits show `hit == prefix` (zero variance) with `miss == the article's own tokens`. ⛔⛔ **THE RETRACTION ITSELF IS REFUTED, MEASURED 2026-09-02: the k=3 corpus total is $6.8853, not $10.32 — the $6.92 this row retracted was RIGHT.** The reasoning above is true of ONE pass and false of k=3, which re-scores **the same** articles: pass 1 hit 88.9% (prefix only, $3.4513), passes 2 and 3 hit **99.4% whole-request cache** and cost **$1.7218 / $1.7122** — half each. ⭐ **A cost model must name whether the repeats are over the same rows or different ones**; 'per pass' and 'per k' are different quantities and this row conflated them. `EXP-010`, `docs/evidence/2026-09-01-phase-b-labels/`. ⛔ Revision 1 was CONFOUNDED — its rows came from the Phase A cohort, scored under this exact prompt the day before, so its 99.5% was whole-request reuse; killed after one pass and the '77.9 minute' reading withdrawn as under-determined. |
| **H-V8-9** | the reorder's stricter labels are BETTER, not merely different | ✅ **ANSWERED 2026-08-29 — YES on the evidence, and the ADOPTION RULING IS STILL THE OWNER'S.** Two steps, $0.0208 total: `docs/evidence/2026-08-29-v8-h-v8-9-adjudication/`. **Step 1 ($0):** all **12** rows whose op-point SIDE differs at k=3, adjudicated against the v8 prompt's own STEP 1 / §5. A(reordered) surfaces **15**, B(as-is) **23** — reconciles exactly with the Phase A `results.txt` §3, so the set is not hand-built. ⭐ **Only 4 of the 12 are STABLE in both arms**; 2 more cross because a SINGLE `out_of_scope` run drags the k=3 mean over (#135, not the reorder), and 6 are magnitude drift with all six runs `in_scope`. On the 4 stable ones the reorder is right **3 of 4** — it drops a 2060 projection study, an ODA funding plan and a mentorship guidebook, each scored `in_scope` by as-is on 3/3 runs; ⛔ **its one stable ADD I judge a false positive** (the WestJet settlement — the *'compensation was paid'* guard does not apply, the claims portal *is being prepared*; ⚠️ **arguable — a court-APPROVED settlement for 3,400 women is a completed occasion, so this is an ADR-023 reader-risk call, not a rule violation**), so **the reorder is not uniformly stricter, it is differently strict.** Cost: 2–3 true positives, all within **0.24** of the op-point. **Step 2 ($0.0208, 27 calls, 0 errors):** the three §5b rows scored under both v8 arms AND the v7 prompt, k=3, **one judge**, full article text. ⭐⭐ **Neither hazard is suppressed: the recovery narrative clears the op-point in both arms (4.900 / 5.350) and on the transitional-justice row the REORDERED prompt is the best of the three (4.367 vs as-is 3.983 vs v7 2.950, i.e. +1.417).** ⛔⛔ **The third row (Rwanda–EU $46M) FAILS `raw > 4.5` under all three prompts including v7 (0.817 / 0.817 / 1.600) — a defect in BLOCKING acceptance criterion 2, not in v8**: its baseline was never established (the file says so), and §5b's *lens overlap* keep collides with the same-day *money committed is not a protection established* ruling, which the headline (*'46 millions mobilisés'*) walks straight into. ✅ **RULED 2026-08-30: the row is DROPPED and REPLACED by two.** ⛔⛔ **The DELTA option offered here is REFUTED, and this row is where the wrong recommendation was made:** v8 − v7 is **−0.783**, which fails a not-lower-than-v7 delta and exceeds the oracle decoder floor (0.436 mean / 0.687 max), so it is not noise. The Unifesp precedent held only because that row sat **above** its baseline — *a precedent is a claim about a mechanism, not a template.* The row fails in **every** form the set can express. Replacements (Fast Company / London ULEZ, en; Welingelichte Kringen / Greek lignite, nl) had their baselines recorded BEFORE their assertions were written, and cleared #107's narrowed predicate rather than merely uplifting v7's scoring behaviour. `docs/decisions/2026-08-30-v8-phase-b-rulings.md` §2, `docs/evidence/2026-08-30-v8-no-regression-replacement/`. ⛔ The money-committed rule was NOT softened — 3 of the 4 stable step-1 crossings depend on it. ⚠️ Side-finding: on the Unifesp row the JUDGE spread (qwen2.5 1.883 / qwen3 0.767 / deepseek 2.950) is **larger than the v8-vs-v7 delta being tested**; and the v7 prompt emits `scope_verdict: __absent__` — **#135's step function is v8-only, so k≥3 is a v8 requirement.** ✅ **CLOSED OUT 2026-08-31 ($0.0205, 36 calls, 0 errors): the whole CURRENT set scored under the adopted prompt — 4 of 4 PASS** (5.100 / delta +1.850 / 6.417 / 5.550; analyser exit 0). ⛔ Until that run the criterion was closed *by construction only*: the two replacements had been chosen from `uplifting v7` **student** scores and had never seen an oracle prompt, and the 08-29 analyser exited 2 on them. ⚠️ Two margins are inside the 0.436/0.687 decoder floor. ⭐ **New control: a k=3 oracle mean moved up to +0.484 between 08-29 and 08-31 with judge, prompt hash, text and weights fixed** — k=3 averages the decoder, it does not pin it, so do not read a ≤0.5 movement of a k=3 mean on this population as an effect. `docs/evidence/2026-08-31-v8-no-regression-gate/` |
| **H-V8-10** | the non-Latin gap above the op-point is a **scoring** property (non-Latin rows score lower for equivalent content), not a **collection** property (few non-Latin sources are in the feed set) | 🔵 **OPEN, raised 2026-08-30, $0 so far.** Observation that raises it (`docs/evidence/2026-08-30-v8-no-regression-replacement/`, scan 3): over 83 cycle files there are **27** non-Latin `uplifting` positives with native text ≥1,000 chars, and **every** cross-lens overlap among them (5 solutions, 2 cultural_discovery, 0 nature_recovery) comes from **one source**, `china_sciencenet_cn`. ⛔ **The scan cannot separate the two explanations** and neither can any count drawn from the same population — that is why this is a hypothesis and not a finding. **Method:** the discriminator is a WITHIN-CONTENT control, because a between-source comparison confounds language with publisher. Two arms are available without new collection: (a) **translated pairs** — articles present in the corpus in two languages under different ids (the id-dedup pass already found 1,450 same-text-different-id rows; extend it to near-duplicates across languages) scored by the same filter, so language varies and content does not; (b) **within-source**, any source publishing in both a Latin and a non-Latin script. If (a) shows no systematic gap, it is collection, and the fix is upstream in FluxusSource, not in the scorer. ⚠️ **Prove the instrument can say yes first**: if the translated-pair set is empty or Latin-only, the negative carries no information — report the pair count before any verdict. ⭐ **Method note added 2026-09-03: the oracle's own `dominant_subject` is written in English whatever the article's language, which makes it a language-independent matching surface that a title regex is not.** Found the hard way — an English title regex counted the Syria cluster at 14 rows / 8 above-op where matching on `dominant_subject` gives **15 / 9**, missing a Japanese row. Arm (a)'s cross-language pairing should key on it. ⭐ **NEW EVIDENCE 2026-09-04 (evening), and it is at a DIFFERENT LAYER than this row asks about.** EXP-016 measured the retrained Stage-1 e5 probe's routing at the adopted 1.75, pooled over both splits, design-weighted: Latin **0.8979** (n=1,187) vs non-Latin **0.8218** (n=131) — gap **0.0762, z = 2.65** (unweighted 0.0693, z 2.53; both SEs binomial, measured Kish deff 1.068 → 2.45). **Non-Latin content is screened harder by the SCREEN**, which is a scoring-side property of the probe — evidence for this row's scoring arm, at Stage 1 rather than Stage 2. ⛔ **It does NOT resolve the row**, for two reasons this row's own Method already names: the probe is a different instrument from the student, and the comparison is still BETWEEN sources, so language and publisher remain confounded. The within-content control (translated pairs, or a single source publishing in both scripts) is still what would settle it. ⚠️ And the recall half is unmeasurable at this n: FN was **0 in every language and script cell**, but on **8** non-Latin positives the rule-of-three upper bound is **0.375** — the instrument could not have said otherwise. `docs/evidence/2026-09-04-v8-probe-calibration/`. **Revisit trigger:** before any non-Latin row enters the no-regression set, and before #141 is closed. Related: **#141**, **#128** (Hebrew median 202 chars — non-Latin rows are thinned twice, once by the 300-char floor and once by scoring low), `memory/google-news-corpus-hypotheses.md` (the GN population the draw excludes is where much short non-Latin mass lives) |

| **H-V8-11** | acceptance criterion 1 is genuinely failing (the nursery row scores above the 3.85 bar) | ⛔⛔ **REFUTED 2026-09-03 — it was a k=3 artefact on a bimodal row, and it drove a full day's work.** Same row, same prompt, same judge: **k=3 → 4.400 (FAIL), k=6 → 3.608 (PASS), k=12 → 2.342 (PASS)**, sd **2.560**, verdicts 3 `in_scope` / 3 off-scope. The margin at k=3 is 0.550 against a band of 2.858, so the verdict never cleared the band **that Gate B-A's own rule requires** — and nobody had computed it, because the gate was prose until that day (the only `.py` files reading `max_acceptable_wa` were two evidence analysers). ⭐ **On a bimodal row a k=3 mean is a sample of a coin flip, not a measurement** — the same fact as #135's *1/√k cannot touch a Bernoulli*, now costing a blocking verdict rather than a price estimate. Closed by `scripts/gate/adverse_suite_gate.py`, which returns **INDETERMINATE, need k≈82** on that exact run. ⚠️ **The ruling it prompted was still worth taking** and the prompt is better for it — but *urgency* was manufactured by an instrument. `docs/evidence/2026-09-03-gate-executable/` |
| **H-V8-12** | prompt clauses are additive: each measured safe alone is safe in combination | ⛔⛔ **REFUTED 2026-09-03, and this is the one that generalises past v8.** Four v8.1 clauses, each at k=6 on the #91 origin row: B 0.917 sd 0.037, C 0.900 sd 0.000, A3 0.900 sd 0.000, D 0.900 sd 0.000, all **0/6 `in_scope`**. Their **union** scores that row **5.921 sd 0.250, 12/12 `in_scope`**, where the labelling prompt pins it at **0.900 sd 0.000**. Leave-one-out isolates a **B×D interaction** — removing either fixes it (0.883 / 0.900), neither causes it alone — and the damage grows **monotonically** with how many other clauses sit alongside them (B+C+D 1.725 → B+A3+D 2.533 → all four 5.921). Mechanism: **D held the only sentence among the four that LICENSES a positive** (*"the release **is** the repair and **scores normally**"*) against B's pointer to §4 for *"repair that someone received"*; deleting that sentence helped (→3.375) and was **not sufficient**. D dropped, so the convict-relief ruling stands unexecuted. ⭐ **Ablate to attribute; validate the artifact you intend to ship.** An ablation answers *which clause caused this*, never *is the combination safe*. `docs/evidence/2026-09-03-v8-1-gate/` PART 2 |
| **H-V8-13** | the §1 leak is caused by clause A's contrast example, or by its length/position in §1 | ⛔ **BOTH REFUTED 2026-09-03, by two arms designed to be able to say yes.** (a) **A2**, A with the *"Lebanon abolishes death penalty — enacted"* contrast removed: 1/6 `in_scope` against A's 2/6 — a 0.84 gap on SEs of ~0.8, i.e. **not distinguishable at n=6**, so the contrast is not the cause. (b) **PLACEBO**, +996 chars of §1 **restatement** introducing no new rule, inserted at A's exact anchor: **0.883 ± 0.037, 6/6 `harm_is_subject`** — indistinguishable from v8's 0.900 ± 0.000, so it is neither length (A was +1,107) nor location. ⚠️ I named the contrast example as the cause **from reading** before either arm ran, and said so as a hypothesis; it was wrong. ⭐ The placebo is the load-bearing arm and the cheapest: ~$0.003 |
| **H-V8-14** | the same rule behaves differently as a §5 CATEGORY than as a §1 TEST | ✅ **CONFIRMED 2026-09-03.** Identical content, two placements: as a **test inside §1** (A, 1,107 chars) it destabilises the #91 origin row to 2.583 sd 2.381, 2/6 `in_scope`; as a **category in §5's exclusion list** (A3, **360 chars**) it leaves the row at **0.900 sd 0.000** and still does its job — the proposal/announcement group moved **4.76 → 3.53**, 8 demoted. With H-V8-13's placebo ruling out length and location, what remains is what the text **does**: ⭐ **a rule stated as a TEST inside a reasoning step becomes a question the model asks of every article; the same rule stated as a CATEGORY in an exclusion list does not.** **Prefer adding an exclusion to adding a test.** ⚠️ n=1 row, one judge, one filter — the mechanism is proposed, not established across prompts. Cheapest next test: repeat on a second knife-edge row |
| **H-V8-15** | v8's low raw recall is improvable from the TRAINING side — by clamping 0→1.0 targets, or by `--use-head-tail` — rather than only by calibration and the probe | ⛔⛔ **TRIGGERED 2026-09-04 (evening) BY ITS OWN REVISIT CONDITION, which read "only if phases 6b/7 leave recall short of the fleet". They did, and the reason is now measured rather than assumed (EXP-016).** The probe is **recall-safe** — 0 FN at the adopted 1.75 on val (31 positives) and test (35) — so Stage 1 was never the constraint. And the calibration is **not a second lever at all**: it is the same ranker as raw (Spearman **0.9977**, 1.95% discordant pairs, AUC **0.9474 → 0.9488**, AP 0.5474 → 0.5648, and at matched flag count every difference is **≤2 articles with inconsistent sign**). ⭐⭐ **So the two cheap levers this row deferred to are spent, and one of them was never a lever** — an isotonic map cannot change discrimination, only which numeric bar corresponds to which operating point. ⛔ **BUT THE CHEAPEST REMAINING MOVE IS STILL NOT THIS ROW: it is the op-point.** 4.5 on the calibrated scale flags **17** test rows where 4.5 raw flags **26** (34.6% less volume), so a re-derivation at phase 8 moves recall with no training at all — indicative sweep, calibrated arm: bar 4.00 → recall **0.514** / spec 0.9760, against raw@4.5's 0.486 / 0.9856. Do that first; then this row. ⚠️ **Recall numbers here are DEVICE- and CALIBRATION-dependent and the 0.514 in this row's original wording is neither labelled**: it was b650-**CUDA**, raw. The CPU raw figure is **0.486** — one article of 35 — and calibrated@4.5 is **0.343**. Any arm compared against "0.514" must state both. **Revisit trigger (replaced):** after the phase-8 op-point re-derivation, if recall at the chosen operating point is still below the fleet's 0.59–0.72 band. Evidence: `docs/evidence/2026-09-04-v8-probe-calibration/`, EXP-016. **Original wording follows.** 🔵 **OPEN, raised 2026-09-04, $0 (no GPU time spent on either arm).** Raised by EXP-015: the trained student is **recall 0.514 / specificity 0.9856** raw on test @4.5 (n=660, 35 positives). Specificity matches or beats every deployed filter; recall is **below all six** (fleet 0.59–0.72, but ⛔ those are **post-calibration** and v8 is not). Two untested levers. **(a) Clamp 0→1.0.** `memory/uplifting-v7-training.md` records unclamped/3 epochs at MAE 0.96 against clamped/6 epochs at 0.78 on a similarly zero-inflated target (v8's train split is 16.7% all-zero rows, per-dimension zeros 16.8–61.1%). ⛔ **That was decided on MAE, which ADR-023 forbids ranking on** — re-judge on recall + specificity at 4.5 with the positive rate stated, never on MAE. **There is no clamping in `train.py` today**, so this arm is a code change, not a flag. **(b) `--use-head-tail`.** Content median is 2,331 chars against a ~2,000-char 512-token window, so a real fraction of every article is truncated; the flag keeps 256 head + 256 tail. **Method:** one variable at a time against the EXP-015 baseline — same corpus, same seed, same 6 epochs, `--select-metric recall_medium` — and compare on recall + specificity at 4.5, **not** MAE. ⚠️ **Prove the bar is reachable before demanding a gain**: the two EXP-015 arms differ by two articles and are not distinguishable, so an arm that moves recall by <~0.06 (2 of 35 positives) is inside the same band and settles nothing. ⚠️ Seed 42 is **not bit-reproducible on CUDA** (0.5601 vs 0.5605 val MAE, same code and data), so a single paired run is not a measurement. **Revisit trigger:** only if phases 6b/7 leave recall short of the fleet — calibration and the probe are aimed at the same number and are cheaper. Related: **#144**, **ADR-023**, `docs/evidence/2026-09-04-v8-checkpoint-selection/` |
| **H-V8-16** | checkpoint selection on `recall_medium` picks a *better* model than selection on aggregate MAE | ⛔ **NOT ESTABLISHED 2026-09-04 — it picks a DIFFERENT one, and the difference is not measurable.** Correcting the inert `--select-metric` (commit `1878e7b`) moved the kept epoch from **6 to 4**, so the defect was not cosmetic. But `recall_medium` **saturates at 0.5806 across epochs 4, 5 and 6**, so the strict `>` tie-break chose the epoch, not the metric (**#144**). Head to head on the untouched test split: epoch 4 leads at 4.5 by **two articles** on recall (0.514 vs 0.457) and two on specificity (0.9856 vs 0.9824), **epoch 6 leads on BOTH at 4.25** (0.500 vs 0.463, 0.9818 vs 0.9802), and they split at 4.0. ⭐ **A model that changes rank under a 0.25 move in the threshold is not distinguishable from its rival.** Reinforced by seed-42 non-reproducibility. ⚠️ **The fix is still correct and still worth having** — it is right for the next filter, where MAE may U-turn; what is refuted is any claim that this checkpoint is better. ⛔ **`recall_medium`'s resolution is `1/n_positives`** — 31 in v8's val, so 3.2% steps, and the per-epoch sequence (0.000 / 0.258 / 0.065 / then flat) is a step function on a thin count, not a model improving and regressing. **Method for a real answer:** a selection metric with usable resolution, or a secondary tie-break key (#144 option 1), judged on test. `docs/evidence/2026-09-04-v8-checkpoint-selection/`, EXP-015 |


⛔ **H-V8-10 is NOT evidence that the v8 corpus is non-Latin-deficient.** The corpus meets its ruled non-Latin target (9.77% against ≥9.76%). What is 0% by construction is the **class-A** signal — `crime_violence` matches 0 of 14,660 non-Latin pool rows — and what H-V8-10 asks is whether the thinness above the op-point has the same cause. Two different populations; do not merge the claims.

⛔ **Two numbers from this run are unquotable and are recorded as such**: the null arm's
**99.4%** cache (it re-sent identical articles, so the whole prompt matched — not the prefix)
and the treatment's **76.0%** aggregate (warm-up dominated; 4 of 30 rows cold).

✅ **Superseded by the n=200 run, 2026-08-29** (`docs/evidence/2026-08-29-v8-phase-a-k3/`):
arm A run 1 measured **89.2%** cache on 200 *distinct* articles against a 95.8% ceiling —
the first cache figure here that a corpus run could reproduce. ⛔ Runs 2–3 of both arms read
**99.4–99.5%** and are the same artifact as the probe's null; only run 1 of each arm is
quotable.

⚠️ H-V8-5's gate was **inferred** from "all six dimensions ≤ 2". The inference is clean on
that run (0 of 25 vs 4 of 5), but it cannot separate a scope refusal from a genuinely dull
in-scope article, and every candidate answer to H-V8-6 needs the verdict itself.

✅ **Persisted 2026-08-29.** `scripts/score_deepseek_production.py` now writes
`scope_verdict` / `dominant_subject` **inside the analysis field**, beside `content_type`
(`tests/unit/test_scope_verdict_stamp.py` — **16 tests, 5 seeded mutations each caught** after a second review found two survivors, including a tautological provenance assertion).
Outcome-proven on the real call site, not on the parser alone: 6 articles from the probe
cohort, **6/6 rows carry both stamps**, and the stamp is not a constant — 3 `out_of_scope`,
3 `in_scope`, which on those 6 agrees exactly with the old inference.

⛔ Three things that run is **not**:
- **not an agreement measurement.** The 6 were *selected by the old inference*, 3 from each
  side. 6/6 shows the two are not anti-correlated; it estimates no rate. The real
  inferred-vs-recorded agreement is a Phase A output.
- **not evidence about H-V8-4.** It is a third identical re-run and gave **0/6** gate flips;
  at a 13% per-row flip rate P(0 of 6) ≈ 0.43, so it neither corroborates nor challenges it.
- **not a cost or cache number.** It re-sent articles already sent on 08-28, so its 99.4%
  cache hit is the *same artifact* the null arm produced, and the $0.0017 it cost cannot size
  anything.

`ground_truth/batch_scorer.py` needed no change — `_parse_json_response` returns the parsed
JSON unfiltered and `analyze_article` only *adds* metadata keys, so a v8 key already survives
into the same nesting (**read-proven, not run-proven** — no v8 run has gone through that path).
⚠️ `scripts/score_ollama_oracle.py` persisted both fields already but at the **record root**,
not inside the analysis field. Read the writer before joining outputs from the two.

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

Related: [[corroboration-feature-hypotheses]], [[calibration-history]], [[working-rules]],
[[cross-repo-prioritization]].
