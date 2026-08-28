---
name: hypothesis-ledger
description: Index of every hypothesis this project has stated, its verdict, and where the experiment and result live. Read to RECALL prior work before proposing a new measurement — it is a pointer index, never a copy.
metadata:
  type: project
---

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
| `H-CX1` | Capping pointer rows in `CLAUDE.md` (#133 option 1) holds the file at a stable size | **OPEN, stated 2026-08-27.** Prediction: with the cap in force, size at the next `/audit-context` is within ±500 B of 37,462, vs ~486 B/day unmanaged. **Refuted if** it grows past ~39,000 anyway — which would mean lessons are landing in the rows regardless of the cap, and the routing rule is not the lever. Source: #133 |
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
| H-V8-3 | the reorder changes the labels | ⏳ **UNRESOLVED, and the instrument is the reason.** The treatment sits inside its own null arm (null sd 1.44 / 5 op-point flips; treatment 1.57 / 3). *"No effect detectable above noise"* ≠ *no effect* |
| H-V8-4 | the v8 prompt is stable run-to-run at k=1 | **REFUTED** — 5/30 (17%) op-point crossings between identical runs |
| H-V8-5 | that instability is decoder jitter | **REFUTED** — it is the **scope gate**: gate-stable rows move a median **0.100**, gate-flipped **3.750**; 4 of 5 large movers are gate flips, 0 of 25 small movers are |
| H-V8-6 | `k=4` averaging fixes it (cousin-3 arithmetic) | ⏳ OPEN and probably **NO** — `1/√k` assumes additive symmetric error; this is a Bernoulli on a binary verdict. A majority vote on `scope_verdict` is the candidate, untested |
| H-V8-7 | the reorder's saving pays for the k≥3 that H-V8-4 forces | **CONFIRMED (arithmetic)** — k=3 reordered $10.16 vs k=1 as-is $18.00 per 6,590 rows |

⛔ **Two numbers from this run are unquotable and are recorded as such**: the null arm's
**99.4%** cache (it re-sent identical articles, so the whole prompt matched — not the prefix)
and the treatment's **76.0%** aggregate (warm-up dominated; 4 of 30 rows cold).

⚠️ H-V8-5's gate was **inferred** from "all six dimensions ≤ 2" — `scope_verdict` and
`dominant_subject` are not persisted by `scripts/score_deepseek_production.py`. The inference
is clean here (0 of 25 vs 4 of 5) but persist the two fields before the calibration run.

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
