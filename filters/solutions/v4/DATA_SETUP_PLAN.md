# Solutions v4 — Training-Corpus Data-Setup Plan (pre-spend)

**Status: PLAN, not executed. No oracle money spent yet.** Written 2026-07-18
after the corpus-composition diagnostic below. Supersedes the "re-score the old
ST v3 + foresight corpora as-is" step in `calibration_report.md` decision 4.
Reviewed by a multi-model battery (see `## Review` at bottom once complete).

## Why the original plan is unsound (the diagnostic)

The plan of record was: re-score the old **ST v3 (10.6K)** + **foresight r2 (3.5K)**
training corpora with DeepSeek + the v4 prompt → 13,796 unique articles. Those
corpora were screened for the *tech-readiness* and *foresight-governance* lenses.
Under the deployment-focused **Solutions** lens they collapse:

- ~42% are arXiv/science preprints (3,331 `arxiv_cs` alone).
- An 80-article random sample scored under the v4 prompt (DeepSeek, ~$0.09):
  **85% `not_a_solution`**, median weighted-average **0.00**, **1/80 (1%)**
  ovr-visible (≥4.5). Even non-arXiv rows were 41/45 below 3.0.

Re-scoring as-is would (a) burn ~$15 of ~$18 labelling obvious negatives, and
(b) yield a training set that is ~85% all-zero labels — the "student trained on
noise predicts zero" failure (`FILTER_PLAYBOOK §2`). **The prompt and oracle are
validated (calibration_report.md); only the corpus sourcing is broken.**

## Goal

Build a **Solutions-enriched** training corpus (~15–30% positive) with adequate
coverage of **all four solution types** — critically the two the old corpora
lack: the **community** type (near-zero in ST+foresight) and the **high/at-scale
band** (~1% base rate). Then score with DeepSeek+v4, `prepare_data`, train v1,
and close the rare tiers with one active-learning round.

Two enrichment levers, in order (see the exchange that motivated this plan):
1. **e5-seed screening (ADR-011)** — cold-start lever, no model needed. Raises
   the positive base rate from ~1% to ~15–30% *before* any oracle spend.
2. **Active learning (ADR-005)** — second lever, needs v1. Targets v1's weak
   tiers (high band, community). This is the nature_recovery v4→v5 arc repeating.

## Assets in hand

- **Seeds:** 157 gold v4-labelled `solution` positives in
  `datasets/calibration/solutions_v4_calib350_deepseek.jsonl` — by type:
  **tech 73, governance 32, community 27, hybrid 25** (all carry `content`).
- **Screener:** `scripts/screening/embedding_screener.py` (multilingual-e5-small,
  cosine-to-centroid, top-k). **Limitation to design around:** it uses a *single*
  centroid = mean of all positives → blurs a multi-type lens and under-ranks the
  minority community type. → screen **per solution_type** (separate centroids),
  then union.
- **Scorer:** `scripts/score_deepseek_production.py` (v4 config, scrape-junk
  check now wired in, resume-capable).
- **Raw cross-lens pool:** `NexusMind/data/raw` and/or FluxusSource
  `~/local_dev/FluxusSource/data` (1.2 GB) on sadalsuud. NOT the per-lens
  `filtered/` dirs — those carry the same old-lens bias that caused the 85%.
- **Community rare-type reinforcement:** belonging v1 production top-scorers are
  community-shaped — usable as extra community seeds and/or a community pool.

## Pipeline (concrete steps)

> **v2 (2026-07-18):** steps below integrate the HIGH review findings —
> hand-curated high-band community seeds, a near-dup pass, a random unscreened
> TEST holdout, the concreteness (not weighted-avg) high-band axis, a stratified
> pre-spend gate, and a normalization step. Review section at the bottom is the
> provenance. **v2.1** pins the parameters below and de-contradicts the gate
> (second review battery).

### Execution defaults (pinned now — cheap to revise, so execution isn't gated on sign-off)
- **Pool:** union of sadalsuud `NexusMind/data/raw` + FluxusSource/current.
- **Near-dup drop:** e5-cosine ≥ 0.93 vs any of the 350 calib texts (fallback:
  title-shingle Jaccard ≥ 0.8). No in-repo tool yet — a ~30-line script is a
  Step-1 build item.
- **Per-type top-k:** tech 3000 / governance 3000 / community 2000, plus the
  ~20–30 hand-curated high-band community seeds.
- **Negatives:** ~2000 random + ~1000 hard (boundary arXiv/research), sized to
  hold the final mix at 20–30 % positive.
- **Hand-curated high-band community seeds:** ~20–30 deployed / at-scale /
  replicated practices (the one manual-judgment input; ~1 hour).
- **Gate per-type minimums (deterministic, from screening provenance):**
  tech ≥ 2500, governance ≥ 2500, community ≥ 1500 candidates in the assembled input.

### Step 0 — Seeds (free)
Per-type seed files from the 157 calib solutions: `seeds_tech.jsonl` (73),
`seeds_governance.jsonl` (32 native — the 25 `seeds_hybrid` also feed the
governance screen, and governance top-k is raised to 3000; coverage is thickened
via top-k + hybrids, NOT more native seeds, since governance was ~91% of the live
tab and its centroid is the second-thinnest), `seeds_community.jsonl` (27),
`seeds_hybrid.jsonl` (25, folded into both gov and community screens). Fields:
`title`, `content`.
- **High-band community is a known blind spot** (e5 ranks *topical*, not
  *quality*; on-disk only 7/27 community seeds reach concreteness ≥7). Screening
  and active learning both under-serve it. → **Hand-curate a small set of
  high-concreteness community seeds** (deployed, at-scale, replicated practices)
  and, at Step 7, a targeted source hunt. Accept this cell may stay thin; do not
  claim coverage the levers can't deliver.
- **Belonging augmentation only if confirmed solution-shaped** — belonging
  top-scorers are social-connection-shaped and would drift the community centroid
  toward `not_a_solution`. Skip by default.

### Step 1 — Candidate pool + near-dup guard (free)
Assemble the raw cross-lens pool from sadalsuud (`NexusMind/data/raw` +
FluxusSource/current) — NOT the per-lens `filtered/` dirs. Then:
- Dedup by `id`; **exclude the 350 calibration ids**.
- **Near-dup pass (HIGH fix):** drop pool articles that exceed the near-dup
  default (e5-cosine ≥ 0.93 vs any of the 350 calib texts; see Execution
  defaults) — exact-id exclusion does not stop the same story under a different
  source/id from leaking into train+test.
- Apply the `is_scrape_junk` prefilter. Record pool size N.

### Step 2 — Per-type e5 screening (free, ~minutes)
Run the screener **once per type** (separate centroids — the tool uses a single
global centroid, which blurs types):
```
PYTHONPATH=. python scripts/screening/embedding_screener.py \
    --positives datasets/screening/seeds_<type>.jsonl \
    --corpus <pool files...> \
    --output datasets/screening/cand_<type>.jsonl --top-k <K_type>
```
Type-weighted top-k so minority types survive (governance raised; community
padded with the hand-curated high-band seeds). Union + dedup → ~8–12K candidates.

### Step 2.5 — Random unscreened TEST holdout (free) — HIGH fix
Draw a **separate ~1–2K random sample from the raw pool** (NOT e5-screened),
excluded from the screened candidate set. This becomes the **TEST split**, scored
alongside Step 4. Reporting recall against a screened test set is circular — the
model was selected to fit that population. Honest recall must be measured against
production the screener never saw.

### Step 3 — Negative sampling (free)
Bounded random negatives + a slice of hard negatives (boundary arXiv/research).
**High band = `solution_concreteness ≥ 7`** (reaches 8.5), never weighted-avg ≥7
(arithmetically impossible; max wa = 5.80). Keep the final training mix
**20–30 % positive** — the bulk-negative budget must not push it below that.

### Step 4 — Score (THE ONLY PAID STEP, off-peak, ~$13–18)
DeepSeek + v4 prompt (fixed) on the enriched candidates **+ the Step-2.5 holdout**,
scrape-junk check active, resume-capable:
```
PYTHONPATH=. python scripts/score_deepseek_production.py \
    --input datasets/scored/solutions_v4_enriched_input.jsonl \
    --output datasets/scored/solutions_v4.jsonl \
    --config filters/solutions/v4/config.yaml --concurrency 20
```

### Step 5 — prepare_data (free)
`prepare_data.py` (now dedups by id defensively). **TEST split = the Step-2.5
random holdout**, not a slice of the screened corpus. Verify positive rate,
per-type mass, and high-band count before training.

### Step 6 — Train v1 (gpu-server)
Per FILTER_PLAYBOOK. Report recall/precision **against the random holdout**;
inspect the `community_practice_strength` gradient and high-band reachability.

### Step 7 — Active learning round (ADR-005) → v2
Use v1 + `export_active_learning_candidates.py` to surface thin tiers. Note the
ADR-005 caveat: AL enriches the mid-band but does **not** reliably find HIGH
needles — the high-band community cell needs the targeted source hunt from Step 0.

### Step 8 — Normalization at go-live (free-ish) — MED-HIGH fix
v4 replaces BOTH tab scorers, so it must ship with `normalization.json` or it's
mis-ranked for weeks (playbook §6/§7). Fit from a **production-base-rate**
historical rescore — **NOT** this enriched corpus (enrichment skews the CDF harsh;
docs/NORMALIZATION_METHOD.md). The enriched training set is **normalization-off-limits.**

## Multilingual posture (nature_recovery lesson — production is ~29% non-English)

nr v4 had to restart because a runtime prefilter's **English keyword gate**
silently dropped ~22 % of non-English positives (129/598 → 0/571 after the fix,
STATUS.md). Posture for Solutions v4:

- **SAFE — e5 screener** is `multilingual-e5-small` (cross-lingual retrieval, not
  keywords); **seeds are 31 % non-English** (48/157), matching production's 29 %,
  so the centroid is multilingually anchored.
- **SAFE — `is_scrape_junk`** does not false-drop non-English real content (the
  char-count empty gate is language-agnostic; English signatures don't match
  non-English prose). Its junk *recall* is English-only — a non-English cookie
  wall reaches the oracle and is caught by Step-1 (cents, not mislabelling).
  Optional later: add a few high-value non-English boilerplate patterns.
- **SAFE — v4 prompt** mandates original-language evidence quotes; **Step-2.5
  random holdout** carries the true ~29 % non-English mix and will expose any
  screening language gap in held-out recall.
- **DONE (draft) — runtime `prefilter.py`** now exists
  (`SolutionsPreFilterV4`), built on the nr v4 template:
  commerce-only pass-through (ADR-004), no English topic/decline gate, and
  **multilingual `POSITIVE_PATTERNS` (en/es/it/de/nl/pt/fr)** with the
  inflected-forms regression test (it already caught the radical-changing
  `desplegar → despliega` miss). Self-test 4/4 + inflection PASS. Remaining at
  go-live: wire it into the NexusMind loader and confirm the class-name binding.
- **GUARDED — screening seed skew** (69 % English) → the Part-A gate now hard-
  checks the screened set's non-English share (below).

## The pre-spend gate (two parts) — HIGH fix, de-contradicted in v2.1

An aggregate "<50 % not_a_solution" can pass on an untrainable corpus, but a
*hard* block on a rare cell a random draw can miss by chance would make the gate
structurally unpassable (the plan itself says high-band-community may stay thin).
So the gate is split: rare cells are checked **deterministically**, never gated
on a lucky random draw.

**Part A — deterministic pre-scan (FREE, on the assembled Step-4 input, before scoring):**
- **HARD:** all ~20–30 hand-curated high-band-community seeds are present in the
  input (count them directly — passable by construction).
- **HARD:** per-screening-type candidate counts meet the minimums
  (tech ≥ 2500 / governance ≥ 2500 / community ≥ 1500; defaults above).
- **HARD (multilingual — the nature_recovery guard):** the screened candidate
  set's **non-English share is ≥ ~20 %** (production runs ~29 %; seeds are 31 %).
  If e5 screening tilted English-ward and non-English fell well below the pool's
  share, that is the embedding analog of nr's dropped-non-English-positives bug —
  stop and rebalance (per-language screening or a non-English seed top-up) before
  scoring.

**Part B — scored sample (~$0.20, ≥150 random rows of the FINAL input):**
- **HARD:** `not_a_solution` rate < ~50 %.
- **WARNING (log, do NOT block the spend):** thin `solution_type=community` or
  `solution_concreteness ≥ 7` mass → schedule the Step-7 targeted
  community-high-band hunt. This cell is a known soft spot (Step 0); it is
  **tracked, not gated** — blocking $15 on a rare cell a 150-draw can miss by
  chance is the wrong trade.

If a HARD check fails, stop and rethink seeds/pool — do not spend the full $15.

## Cost & timing

| Step | Cost | Where |
|---|---|---|
| 0–3 screening/sampling | $0 | local / gpu-server e5 |
| pre-spend gate | ~$0.10 | DeepSeek |
| 4 full score (~10–15K) | ~$13–18 | DeepSeek, off-peak after ~noon CEST |
| 5–7 | $0 (+ GPU time) | gpu-server |

## Open decisions for the engineer

1. **Community seed augmentation:** pull N belonging v1 top-scorers into
   `seeds_community.jsonl`? (Recommended — 27 native community seeds is thin.)
2. **Pool choice:** `NexusMind/data/raw` vs FluxusSource/current vs both — pick
   at Step 1 after confirming sizes/format/dedup state.
3. **Type-weighted top-k values** (Step 2) and **negative budget** (Step 3) —
   set after the Step-1 pool size and a quick screen-similarity histogram.

## Review (multi-model battery, 2026-07-18 — 4 reviewers / Opus+Sonnet)

Verdict across all four: **direction sound, execute after fixes — no redesign.**
Every finding is additive. Must-fix before the paid Step 4:

**Plan gaps (design + hygiene reviewers):**
- **[HIGH] Test-split circularity.** Candidates are chosen *because* they
  resemble known positives; if the TEST split is drawn from that same screened
  pool, held-out recall is fiction. → Carve the TEST split from a **random,
  unscreened production holdout** (~1–2K, scored alongside Step 4), report recall
  against *that*.
- **[HIGH] `prepare_data.py` has no dedup** (confirmed by grep). Exact-id
  exclusion (Step 1) does not stop *near-duplicate* articles (same story, other
  source/id) that pass the e5 screen. → Add a near-dup pass (title/URL-shingle or
  cosine vs the 350 calib texts) before Step 4; add defensive id-dedup in
  `prepare_data.py`.
- **[HIGH] Pre-spend gate is composition-blind.** `<50% not_a_solution` on an
  80-row random sample cannot detect an empty high-band or thin community cell.
  → Stratify: require min per-type counts + a non-zero **high-band-community**
  count, ≥150 sample, run on the **final Step-4 input** (post-negatives).
- **[HIGH] High-band community may be reachable by neither lever.** e5 similarity
  is *topical, not quality*; community solutions are intrinsically low-concreteness
  (on-disk: 7/27 seeds ≥7, max 7.5), and ADR-005 evidence (uplifting v6: "HIGH
  found: 0") says active learning does not find needles. → Hand-curate
  high-concreteness community seeds / targeted source hunt; do **not** rely on
  screening or AL for this cell. Be honest this cell may stay thin.
- **[MED-HIGH] No normalization / cold-start step**, and v4 replaces BOTH tab
  scorers. → Add: fit `normalization.json` from a **production-base-rate**
  historical rescore before go-live (playbook §6; NOT from the enriched corpus).
  State in the plan that the enriched set is normalization-off-limits.
- **[MED] Governance under-coverage** (32 seeds, thinnest after community) risks
  the tab-volume collapse the calib report flagged (foresight was ~91% of the
  tab). → Raise governance top-k / thicken governance seeds.
- **[MED] Belonging augmentation may drift the community centroid** toward
  social-connection (not solution) shapes. → Only add belonging articles
  independently confirmed solution-shaped, or skip.
- **[fix] "High band" axis:** use **concreteness ≥7** (reaches 8.5), never
  weighted-average ≥7 (arithmetically impossible; max wa = 5.80). Negative budget
  must keep positive rate in the 20–30% band, not below it.

**Code bugs in the committed scrape-junk check (`d7888e2`) — must fix before any
multilingual spend:**
- **[HIGH] CJK/Thai false-drop.** `content.split()` on non-space-delimited
  languages yields ~1 "word" → genuine Chinese/Thai articles dropped as
  `empty_or_stub_content`. The corpus is multilingual. → Gate the empty check on
  **character count** (`len(content.strip()) < ~25`), not whitespace tokens.
- **[MED] Short in-lens briefs false-dropped.** A <120-word genuine brief that
  legitimately mentions "cookie consent" / "subscribe to continue" / "404 error"
  (all plausible Solutions/governance topics) is dropped. → Require the signature
  near the body **start**, or ≥2 distinct signatures, or boilerplate-dominance
  ratio — not mere presence.

**Claims audit (verification reviewer):** seed counts VERIFIED (157; 73/32/27/25);
corpus ~42% arXiv/science + 3,331 `arxiv_cs` VERIFIED; cost ~$13–18 VERIFIED
(cache-hit caveat could push higher); pool/tooling VERIFIED. **One gap:** the 85%
not_a_solution headline came from an *ephemeral scratch* run — **not reproducible
from committed artifacts.** → Commit the diagnostic sample + scorer output (or
re-run and commit) so the number that justifies this whole plan is reproducible.

**Code that is CLEAN (confirmed):** tests 11/11 pass; resume/skip plumbing
correct (skipped rows never become false-zero labels; never double-counted);
the 3 prompt edits are internally consistent (new Flag-A-default does not touch
the opinion-author exception).

### v2.1 — second battery (2026-07-18), verdict: code CLEAN, plan de-contradicted

Round-2 battery (3 reviewers / Opus+Sonnet) on the fixed state:
- **Code fixes CONFIRMED clean** (42 tests pass): CJK char-gate fixes the
  false-drop; two-tier WEAK design does not overcorrect (single-weak >8-word
  walls reach the oracle, where Step-1 still catches them — a few cents, not
  mislabelling); `prepare_data` dedup correct (last-wins, order stable, no-id
  handled). No bugs.
- **Plan gaps it caught and this v2.1 fixes:**
  - The stratified gate's *hard* block on high-band-community was
    self-contradictory (unpassable) → **split into Part A deterministic /
    Part B warning** so it can't become a permanent blocker.
  - Unpinned parameters (near-dup threshold, top-k, negatives, community seed
    count, pool) → **Execution defaults block** pins revisable defaults.
  - "governance thickened (32)" was 32→32, a false claim → **corrected** to
    "thickened via top-k + hybrids, not more native seeds."
  - Stale `calibration_report.md` BLOCKER → **superseded pointer added.**
- **Deliberately NOT changed:** `_STUB_WORD_CEIL` stays 8 (raising it to catch
  more junk risks re-dropping genuine short briefs — dropping real content is the
  worse error; a few cents of junk reaching the oracle is caught by Step-1).

**State: code clean + committed-ready; plan executable pending the pinned
defaults' final sign-off. No paid step until Part A + Part B(HARD) pass.**
