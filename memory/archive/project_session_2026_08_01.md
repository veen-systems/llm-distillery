---
name: project_session_2026_08_01
description: "Session 2026-08-01 — post-deploy verification: refits + NM#280 tier gate VERIFIED live; cd topic gate found INERT, exposing that per-filter prefilters have never run in production (NM#284); shadow stage implemented"
metadata: 
  node_type: memory
  type: project
  originSessionId: 855e56e0-303e-41e6-846b-8bf1ce5b4401
  modified: 2026-08-01T12:12:55.445Z
---

# Session 2026-08-01

## Post-deploy verification (the carried-over first task)

Three checks against `filtered_20260801_08xx`. Two green, one red.

- **Refits (NM#279) PASS.** uplifting raw 5.00 → norm ≈5.18 (was ~3.0); belonging
  MEDIUM+ p90 norm 8.71 (n=205 / 3 cycles); `percentile` on 2647/2647 rows.
- **NM#280 tier gate PASS.** `count(tier != low) == count(raw >= op-point)` holds
  *exactly* for all six live filters across six consecutive cycles — live from the
  07-31 12:5x cycle; the two before it show the double-cut. Restored visibility:
  uplifting +196%, belonging +82%, ir +70%, cd +67%, solutions +33%, nr +33%.
  **Caveat: 0 caps applied in these cycles, so the cap carve-out path is untested
  in production.** nr's +33% "matching" the predicted 27–37% is on a base of 3
  articles — coincidence, not confirmation.
- **cd topic gate (LD#86) FAIL — and it wasn't a cd problem.**

Closed: NM#279, NM#280, LD#74, LD#76. LD#86 stays open.

## The finding: per-filter prefilters have never run in production

`deploy/gpu-server/main.py` builds every scorer with `use_prefilter=False` (L915)
and calls `score_batch(skip_prefilter=True)` (L1318) — since `66582e7`,
**2026-02-10**. All eight deployed filters stamp 0 prefilter blocks, every cycle,
while every `config.yaml` declares `prefilter.enabled: true` with an
`expected_pass_rate`. Filed **NM#284**.

**Scope precisely** (the first phrasing was too broad and the owner rightly
pushed back): what is dead is the **per-filter rule prefilter layer**
(`filters/{name}/v{N}/prefilter.py`, ADR-018/019 `BasePreFilter` subclasses) **in
the production scoring path only**. Still working normally: the commerce
prefilter (ADR-004, separate model at `/commerce/predict`), the obituary and
violence gates (separate `src/preprocessing/` stages), and the same per-filter
prefilters in the llm-distillery **training/oracle** path (`batch_scorer.py`,
`calibrate_oracle_1k.py`, `calibrate_prefilter.py`, `train_scope_probe.py` all
call `apply_filter()`). That last part is *why it survived six months* — the
layer is real and load-bearing where oracle spend is measured.

**⚠️ The first evidence was invalid and was retracted the same day** (owner asked
"what is that prefilter? not the e5-probe I hope?" — checking properly exposed it).
The claim "all 8 filters stamp 0 prefilter blocks per cycle" came from counting
`passed_prefilter` in `data/filtered/*/filtered_*.jsonl`. That file only receives
rows where `passed_prefilter` is true (`scripts/main.py:1151`) — **100% passers by
construction**, can never contain a block. The replay-vs-stamped-rate comparison
(28.8% vs 100%) inherited the same artifact. Retracted in NM#284
issuecomment-5151154862 and corrected across CLAUDE.md, FILTER_PLAYBOOK §0b,
filter-status, gotcha-log, calibration-history.

Reality: the pipeline reports **~350–360 prefiltered per lens per cycle** — the
NM#189 source-type allowlist (enforced) + validation failures, *not* lens rules.
Five lenses with different rules landing within 10 of each other was the tell;
investment_risk differs at 821 because it also excludes `academic` + `social`.

**What the finding actually rests on** (all still valid):
1. **Code** — `use_prefilter=False` makes `if self.use_prefilter and not
   skip_prefilter` false in *both* `filter_base_scorer` and `hybrid_scorer`.
2. **In-path shadow measurement (the load-bearing proof)** — cd reports
   `observed_pass=0.244` over 1,300 articles *at the scorer*; if the gate were
   enforcing upstream the scorer would see only the ~24% that passed and the same
   measurement would read ≈1.000.
3. **Magnitude** — cd's gate blocks 71% on replay; 15.6% is actually dropped.

**Verified NOT affected** (each checked, not assumed): **e5 probe** runs (Phase 2
of `hybrid_scorer.score_batch`, ungated by `skip_prefilter`; live log
`stage1_low=7..19, stage2=77..85` per 100); commerce/obituary/violence run
(separate `src/preprocessing/` stages); NM#189 source-type allowlist runs
(`shadow_mode: false`).

**Lesson: a reproduction is only as good as the population you reproduce it on.**
Before using a data source as a denominator, establish what it is filtered on.
Here it was one `if` at `scripts/main.py:1151`.

### Sizing — the speedup is mostly one shared rule, not six lens gates

| filter | n | length floor | lens-specific | total |
|---|---|---|---|---|
| uplifting | 2647 | 853 (32.2%) | 114 (4.3%) | 36.5% |
| belonging | 2647 | 853 (32.2%) | 74 (2.8%) | 35.0% |
| cultural_discovery | 2647 | 0 | **1884 (71.2%)** | 71.2% |
| nature_recovery | 2647 | 853 (32.2%) | **0** | 32.2% |
| solutions | 2647 | 853 (32.2%) | **0** | 32.2% |
| investment_risk | 2075 | 383 (18.5%) | 76 (3.7%) | 22.1% |
| **total** | **15310** | **3795 (24.8%)** | **2148 (14.0%)** | **38.8%** |

- 24.8 of the 38.8 points is `content_too_short` — a `BasePreFilter` rule blocking
  *the identical 853 articles* for every filter. So the right fix is **one global
  short-content gate before fan-out**, not six per-filter gates. ~32% of
  production articles are below the length floor and scored by Gemma-3-1B anyway,
  once per filter.
- Lens-specific blocking is **88% cultural_discovery**. Across the other five
  filters lens rules block 264 articles total (~2%).
- **`NatureRecoveryPreFilterV4.EXCLUSION_PATTERNS == SolutionsPreFilterV6.EXCLUSION_PATTERNS`
  is `True`** and both block zero on lens rules. **First read ("both copied from
  the template, never specialized") was wrong and is corrected on LD#90:**
  - *nature_recovery v4 is deliberate* — its config documents that topic/decline
    gates were REMOVED in v4 (English-only, cost 21.6% recall), screening moved to
    the multilingual e5 probe. Declares 0.85, observes ~0.68. Working as designed.
  - *solutions v6 is the real mismatch* — it inherited nr v4's pass-through while
    keeping a description claiming a "broad solutions keyword net" and declaring
    0.2, against ~0.68 observed.
  - So the LD#90 criterion is **not** "lens block rate must be non-zero" (that
    would wrongly fail nr). It is: **observed must match declared, and the
    `description` must match what the prefilter actually does.**

## NM#284 stage 1 (shadow) — implemented

Owner chose shadow-first. Implemented in `src/scoring/production_scorer.py`:
evaluate each filter's prefilter after scoring, **log** observed pass rate vs the
declared `expected_pass_rate`, enforce nothing. Env lever
`NM_FILTER_PREFILTER_SHADOW=0`. 6 new tests, 38/38 in the file pass.

**Deployed 2026-08-01 ~11:59 CEST** (`cd4fc6d` + `5d53774`), verified live in the
scorer journal. The first live run immediately exposed two defects in the new
code, both fixed and redeployed:
- the post-deploy smoke test scores **one** article per filter, so drift was
  judged at n=1 and flagged all six filters "gate appears inert" — six false
  alarms in the first six lines. Now guarded by `MIN_SHADOW_SAMPLE = 50`.
- `expected_pass_rate: ~0.25` (cd v4/v5, uplifting v6) is a YAML **string**, not
  a float — a strict isinstance check silently dropped it, so the filters the
  LD#86 work makes most interesting logged no declared rate at all.

*Lesson: both defects were invisible in unit tests and obvious in the first six
lines of real output. Deploy the observability, then read it.*

**Why it logs instead of stamping `passed_prefilter`:** that field is consumed as
a **drop signal** — `scripts/main.py:1151` skips the output-file write entirely,
`src/enrichment/article_fetcher.py:819` skips enrichment. Writing the truthful
verdict there would have been full enforcement distributed across consumers, the
exact ADR-022 anti-pattern. Per-row JSONL stamping needs new fields plumbed
through gpu-server `main.py` → `gpu_client.py` → `scripts/main.py` — deferred as
stage 1b, partly because `scripts/main.py` holds someone else's uncommitted WIP
(image-classifier thresholds, NM#282).

## First real cycle (12:46) — shadow data

| filter | observed | n | declared | verdict |
|---|---|---|---|---|
| cultural_discovery | **0.244** | 1300 | 0.25 | **matches — LD#86 gate validated** |
| uplifting | 0.525 | 2100 | 0.20 | mismatch |
| solutions | 0.591 | 2099 | 0.20 | mismatch (LD#90) |
| investment_risk | 0.589 | 2099 | *(none)* | no contract |

belonging + nature_recovery not in the captured log window. Three independent
measurements of the cd gate now agree: 0.245 offline (14,923 rows) / 0.288 replay
(2,647 rows) / **0.244 in-path** (1,300 rows) — against 1.000 stamped.

Refinement noted on NM#284: the log is **per batch (100 articles)**, not per
cycle, so ~21 lines/filter/cycle need aggregating. Fine as a decision input;
a per-cycle rollup would be better as a standing check.

## Gotchas banked

- `git stash push` + long pytest in one chained command hit the 2-min Bash
  timeout **between** the stash and the pop — work sat in the stash. Run
  baseline-vs-change comparisons as two separate backgrounded commands.
- **The "35 pre-existing NexusMind test failures" never existed.** `python` on
  situla resolves to system `/usr` (no `trafilatura`) so `import scripts.main`
  raises and every module touching it errors. The repo's `venv/` has everything:
  `venv/bin/python -m pytest tests/ --ignore=tests/integration` → **969 passed,
  0 failed**. **Always use `venv/bin/python` for NexusMind tests.** The bogus
  baseline had propagated into NM#280's and NM#284's commit messages, the
  07-31 session memory, and a gotcha-log entry that asserted it was
  "environmental and permanent" — all corrected 2026-08-01. The trap: the
  workaround (diff failure sets before/after) genuinely worked, so nothing ever
  forced a re-examination of why the baseline was non-zero.
- **`memory/filter-status.md`'s CLAUDE.md-reconciliation verify was wrong-shaped**
  — a raw `diff` of two differently-formatted tables, so it could only ever emit
  MANUAL CHECK NEEDED, never PASS. Reshaped 2026-08-01 to a `comm` on
  (name, version) pairs that tolerates filter-status's extra historical rows.
  Third wrong-shaped-verify instance in the gotcha log; a check that can never
  pass teaches everyone to ignore it.

## NM#281 gate-contract harmonization — DONE + DEPLOYED

`0fd462b` (+ llm-distillery `290ab29` for the shared file), deployed ~13:35 CEST.
Ships **inert** (`enforce: false`).

- `_commerce_model` stamp. Local path → `MODEL_VERSION` ("v1"); the gpu-server
  branch (dead under the LD#80 guard, and its response carries no version) →
  `"gpu-server-unpinned"` rather than a hardcoded "v2" that could become a lie.
  **Seeing that string in production means the LD#80 guard regressed.**
- `_violence_model` read off `ViolencePromotionFilterV1.MODEL_VERSION`; added
  `MODEL_ID`/`MODEL_VERSION` to that class in BOTH repos (byte-identical file —
  re-diffed after).
- `pipeline.violence_promotion.enforce` (default false) → same central gate as
  obituary. Replaced the config comment that prescribed consumer-side exclusion.
  Recorded the LD#82 caveat inline: v1 recall 0.55 → enforcing gates ~half of
  true positives.
- `violence_blocked` counter in stats + the Loaded log line.

## Cross-repo: ovr#280's cluster_id diagnosis is wrong

ovr#280 claimed "upstream never sends cluster_id" and proposed an upstream fix.
**Refuted:** 7,629 / 16,128 rows (~47%) carry
`nexus_mind_attributes.<lens>.source_quality.cluster_id`, with
`corroborating_sources` + `other_sources` on exactly the same rows; present in
07-22 files too. The diagnosis sampled `metadata.quality` — FluxusSource's block,
whose key list (`bias_category, credibility_score, source_tier,
type_classification`) the issue quotes verbatim. cluster_id lives one level
deeper, per-lens.

**Same failure shape as my own prefilter error earlier today**: two
similarly-named structures, sampled the wrong one, got a clean-looking zero.
No NexusMind work needed; the break is downstream in ovr.news ingestion.
NM#278 (threshold re-tune) is the real fix for the reported symptom — clustering
runs on source text pre-summarization, so cross-outlet paraphrases look far
apart. Caution left on NM#278: NexusMind *removes* rather than *labels* (32%/run)
and anything removed upstream can never surface as an "N sources" badge.

## Five-lens adversarial battery over the SAME DAY's own work — the highest-yield hour

Lenses: violence-gate failure modes, shadow hot-path safety, claim verification,
ADR-022 conformance + cross-repo drift, doc accuracy. Found **2 blockers and
~10 warnings/notes, all in code I wrote today**, three of them in code written
*to fix* the previous defect.

**Blocker 1 — the NM#281 violence gate could never fire.** Placed in
`_is_duplicate`, which runs inside `load_articles` (called from
`_run_shared_dedup`) *before* `_run_violence_promotion_prefilter` stamps
anything. `enforce: true` would have dropped **zero** while logging
`0 violence` — a false all-clear. Commerce/obituary work there only because
their preprocessors rewrite the input JSONL earlier. Fixed `b85a467`: drop moved
to `_enforce_violence_promotion()` immediately after stamping (NOT the reverse —
violence runs on the *enriched* superset and moving it earlier would cost recall
on a 0.55 gate); dead check removed; ordering asserted via AST.

**Blocker 2 — the shadow loader armed a dead enforcement branch.** Leaving
`target.prefilter` populated makes `HybridScorer`'s guard
`... and self.stage2_scorer.prefilter` truthy. Reviewer reproduced against the
real class: wrapping flips a `use_prefilter=True` hybrid from `scored=2/2` to
`scored=1/2` with null scores. Now restored to `None` after capture.

Also fixed: `getattr(..., "MODEL_VERSION", "v1")` — **the default was itself the
bug the stamp exists to prevent** (→ `"unknown"`); `shadow_error:` was dead code
so a broken shadow logged *nothing* and partial failures shrank the denominator
silently (→ `errors=N`); digit-collapsing fragmented the histogram it existed to
unify (→ `re.sub(r"\d+","N")`). **978 tests green** (was 969).

**Filed, not fixed:** NM#285 (shadow measures a truncated `Article` —
title+content only, so url/source rules can never fire; four filters cluster at
~0.59 by artifact; cd's 0.255 survives, ir's does not — **gates all enforcement
decisions**) and NM#286 (commerce has no `enforce` key; consumer-side commerce
drop in `enrich_survivors.py`; violence stamping skipped in 3 run modes).

**Recommendation recorded on NM#285: Option C — run prefilters pipeline-side.**
A prefilter exists to avoid the expensive call; running it inside the scorer
means the article was already serialised, shipped and queued, so it captures
almost none of the saving. Pipeline-side also has whole articles (dissolves
NM#285), matches how commerce/obituary/violence already work, and lands stamps
in the JSONL for free (closes stage 1b). ~19 s sadalsuud CPU/cycle, and it stops
blocking the FastAPI event loop (~323 ms per cd chunk today). **Measure the
per-filter truncation effect before committing.**

## Doc-side recursion worth remembering

- The `filter-status.md` verify I reshaped this morning **broke one commit
  later** — I renamed the heading its awk range anchored on, so the range ran to
  EOF and still printed PASS. My *first fix* was also wrong: `grep -q
  'prod-filters-table:end'` matches the verify's own copy of that literal, so
  the guard could never fire. Now `grep -qxF` on sentinel lines, tested in all
  four directions.
- `scripts/main.py:1151` cited 7× → now line 1165 (NM#281 inserted 20 lines
  above it the same day). Replaced with content-anchored references.
- `0.244` vs `0.255`: one lens called it fabricated, another reproduced it
  exactly. **Both right** — it is a legitimate 13-batch partial read; full cycle
  is 0.255 (n=2099). I over-corrected when first reporting this.

## Next session — FIRST: verify the cycle after 14:04 CEST

Four things, all first-time-in-production:
1. `_commerce_model` on every commerce-scored row, reading **`v1`**.
   **`gpu-server-unpinned` would mean the LD#80 guard regressed.**
2. `_violence_model` present (reads `v1`; `unknown` means a v2 shipped without
   the constant).
3. `violence_blocked` **gone** from the Loaded line — it moved out of load time.
4. belonging + nature_recovery finally landing in the shadow log; `errors=N`
   appearing if anything raises.

Then, in this order (the order is forced, not chosen):
1. **NM#285 measurement** — per-filter diff of in-path shadow vs offline replay
   over full rows. Gates every enforcement decision. Then decide Option C.
2. **NM#286** — commerce `enforce` key and its consumer-side twin must move
   together; violence run-mode gaps before any flip.
3. **LD#82** violence audit — what `enforce: false` is actually waiting on.
4. LD#90 program, LD#87 op-point re-derivation (both downstream of NM#284).

Dropped from the queue: **NM#206 was already CLOSED**. NM#284 stage 1b is
subsumed by Option C if that is chosen.

## The lesson this session actually taught

Every claim verified against production held. Every claim reasoned about did
not. Four of my own defects, three in code written to fix the previous defect,
plus four overbroad claims — and **every correction that mattered came from the
owner asking a short question or from an adversarial reviewer, never from
noticing it myself.** A correct conclusion supplies no pressure to check the
reasoning that reached it. Budget for review of one's own same-day work.

## Related Memories

- [[project_session_2026_07_31]] — prior session (the deploys verified here)
- [[gotcha-log]] — "Every filter's prefilter was dead in production" entry
- [[cross-repo-prioritization]] — Chain 3 closed; NM#284 is a new chain head
