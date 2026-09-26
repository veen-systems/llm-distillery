---
name: project_session_2026_08_02
description: "Session 2026-08-02 — NM#285 measured (truncation refuted as cause), LD#92 uplifting claim refuted and relocated to solutions, NM#286 items 1+2 shipped"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2cb9121d-3096-4153-9a52-c8e887ceca4f
  modified: 2026-08-02T08:10:16.602Z
---

# Session 2026-08-02

> ⚠️ **Read §6 first.** A close-of-session review battery overturned three
> numbers written in §1–§5. Where they conflict, **§6 wins**. Marked inline
> below; §1–§5 are left intact as the record of what was believed and when.

Three priorities, all delivered. **Two of the three findings this session were
refutations of the previous session's own conclusions** — both P0 issues written
up 08-01/08-02 turned out to have the mechanism right and the target wrong.

## 1. NM#285 measured — truncation is real but ~1pp, not the cause

Same-row A/B: each filter's prefilter run over FULL rows vs `{title, content}`
(what `Article` at `deploy/gpu-server/main.py:338` reconstructs). 4 cycles,
n=8,283.

Truncation inflation on the production-relevant population: investment_risk
**+0.0097**, uplifting +0.0028, belonging +0.0008, cultural_discovery +0.0005,
nature_recovery and solutions **0.0000**. So the 0.638–0.649 cluster is **not**
a truncation artifact — it survives the full contract. NM#285's *mechanism*
claim (url/source rules inert in-path) is confirmed, but it is worth tens of
articles, not hundreds. Option A cannot be justified on accuracy.

**The cluster's real cause:** `nature_recovery v4` and `solutions v6` declare
`EXCLUSION_PATTERNS = {}` **by design** (commerce upstream, ADR-004), and their
`POSITIVE_PATTERNS` are force-pass overrides — a no-op with nothing to override.
Both reduce to `validate_article()` + `MIN_CONTENT_LENGTH`, which is why they
produce byte-identical results (5,688/8,762 in-path; 0.6438 in replay). Their
declared `expected_pass_rate` (0.85 / 0.20) describes a gate that does not exist
— do NOT "correct" it to 0.64, which is just "fraction of articles ≥300 chars".

**Bigger defect found underneath:** the shadow denominator counts articles the
pipeline discards (source-type exclusions, applied post-scoring). See
[[reference-nexusmind-data-sources]].
⚠️ **§6: 0.129 is an UPPER BOUND, not a measured bias** — the excluded rows'
pass rate is unmeasured.

**Reframing for NM#284:** "enforce the prefilter" means, to 87–100% for four of
six filters, "enforce a 300-char length floor". Length's share of blocks: nr
100%, solutions 100%, belonging 96.8%, ir 92.6%, uplifting 86.3%, cd 0%. cd is
the only filter doing real lens work.

## 2. LD#92 refuted for uplifting — the defect is in solutions

Widened to n=60/group across all six filters (660 articles, deepseek-chat, 0
errors, ~$1.3). Difference-of-differences, bootstrap CI.

| filter | DiD | 95% CI | MAE ratio |
|---|---|---|---|
| **solutions v6** | **−1.13** | **[−1.74, −0.52]** | **1.51×** |
| uplifting v7 | +0.44 | [+0.01, +0.87] | 0.88× |
| others | +0.26 … +0.79 | mostly spans 0 | ~1.0× |

**uplifting shows no effect at any bar** (clears short/long: 90/88 @2.25,
87/87 @3.0, 67/65 @4.0) — the robust part.
⚠️ **§6: the +0.44 is NOT significant** (permutation p=0.054, fails Holm), the
**P=0.0000 bootstrap is WITHDRAWN** (true 8.0e-5, wrong resampling, wrong
question), and **solutions' −1.13 is NOT IDENTIFIED** (selection artifact
reaches −0.82…−1.61). Do not fit a cap from this table.

**Root cause hypothesis: a filter mix-up.** LD#92 states uplifting's tier
threshold as **2.25**, which is *solutions'* op-point; uplifting's is **4.0**
(verified in production: tier `low` tops at raw 3.999, `medium` starts 4.003).
The "924 / 15.0%" scale figure reproduces exactly at a 2.25 bar (910 / 14.8%)
and collapses to **117 / 1.9%** at 4.0. And the effect reported for uplifting
(−1.24, 2.3× MAE) is present in solutions at almost exactly that size.

**"~460 bad articles per 8 cycles" does not survive** — both terms were wrong.
Corrected solutions exposure: ~49 false positives per 8 cycles (~6/cycle).

Also: sub-300 content is *under*-represented above the op-point in every filter
(0.09×–0.95× relative rate), the opposite of "damage concentrated in the upper
tail". And **investment_risk has the largest short-content exposure by far**
(635/8 cycles clearing op-point) **with no length effect at all** — exposure and
defect are not the same thing.

## 3. NM#286 items 1+2 shipped, item 3 assessed

Branch `nm286-adr022-gaps`, commit `23a9068`, **unpushed**. 918 unit tests pass.
Added `pipeline.commerce_prefilter.enforce` (default **true**, unlike obituary's
false — a config predating the key must not silently open a live gate), and made
`enrich_survivors.py` read the same key rather than re-deciding.

Item 3 (violence stamping skipped in 3 run modes) verified in code but **live
blast radius is zero today**: production runs `main.py --skip-cleanup` with all
six filters (so shared dedup runs), and violence `enforce: false`. Current
defect is missing stamps in ad-hoc single-filter / `--no-dedup` reruns. Still a
hard prerequisite for any enforce flip.

## Lesson

Both refutations came from **widening a sample and reconciling a denominator** —
neither needed new tooling or cleverness. The 08-01 session's own lesson was
"establish what a source excludes"; this session's two errors were the same
shape one level down (a log and a file counted different sets; raw and scored
content differed by a fetch step). The pattern to watch: a *mechanism* that is
correctly identified gets attached to the *first plausible target*, and being
right about the mechanism supplies no pressure to check the target.

## 4. Acted on the recommendations (same session)

- **NM#285 → Option B shipped** (`89f2e5b`, NexusMind main). Option C **declined
  on the measurement**: its cost saving came almost entirely from the length
  floor, the rule we now don't want to enforce; Option A buys a rounding error.
  Every shadow line now carries `contract=title+content`, `pre_source_filter=true`,
  and `INCOMPLETE(inert:url,source)` derived from declared rule containers.
  Verified against all six real prefilters: flags exactly the four with non-zero
  measured truncation effect. (A `MagicMock` test caught that a bare `getattr`
  truthiness check marks *everything* INCOMPLETE — detection now requires a
  non-empty container.)
- **`expected_pass_rate` deleted** from nature_recovery v4 + solutions v6 in both
  repos (`3ed47e1` LD, in `89f2e5b` NM), with comments recording that the absence
  is deliberate. solutions' prefilter `description` also claimed blocking it has
  never done. Value-level YAML diff confirmed only the intended keys changed.
- **NM#286 items 1+2 merged to main** (`23a9068`). Item 3 verified but left:
  live blast radius is zero (production runs multi-filter; violence
  `enforce: false`), so it's an audit gap, not admitted violence.
- **LD#86 answered: DO NOT FLIP.** Enforcing cd's prefilter costs **15.5% of
  surfacing articles** (135/871 over 20 cycles), 0% of high tier.
  ⚠️ **§6: the "19.9% non-English vs 13.0% English" framing is WRONG** — de 4.9%
  and fr 5.3% sit *below* English. The gap is entirely
  `no_cultural_topic_signal` (uneven `TOPIC_GATE_PATTERNS` coverage), not
  language. I noticed the anecdote overstated the skew and still published the
  pooled number my own table contradicted.

## 5. Deployed (2026-08-02 10:1x CEST) — ⚠️ "verified live" was verified at **n=1**

`bash scripts/remote_deploy.sh` — code revision hash matched local↔gpu-server,
scorer healthy, **all 6 post-deploy smoke tests passed**. The smoke test's own
shadow lines gave the verification immediately (gpu-server logs **UTC**):

```
nature_recovery:    ... contract=title+content                          ... pre_source_filter=true
belonging:          ... declared=0.15 ... contract=title+content INCOMPLETE(inert:url)    ...
solutions:          ... contract=title+content                          ... pre_source_filter=true
uplifting:          ... declared=0.20 ... contract=title+content INCOMPLETE(inert:url)    ...
cultural_discovery: ... declared=0.25 ... contract=title+content INCOMPLETE(inert:url)    ...
investment_risk:    ... contract=title+content INCOMPLETE(inert:source) ... pre_source_filter=true
```

⚠️ **§6: these are the n=1 SMOKE TEST only.** Cycles run :10→:59, so the last
real cycle ended 08:59 CEST — 70 min *before* the 10:08 deploy. No real batch
had run. All four checks pass at n=1: contract marker on all six; `pre_source_filter=true` on all
six; `INCOMPLETE` on exactly the four filters with a measured non-zero truncation
effect (and the right family each); **no `declared=` on nature_recovery or
solutions**, confirming the deleted key in production.

**Also found and fixed while deploying:** `scripts/remote_deploy.sh`'s
unpushed-commits pre-flight (added 2026-04-19 to stop stale-filter deploys) had
`NEXUSMIND_LOCAL` hardcoded to `C:/local_dev/NexusMind`, so on the Linux
workstation it fell to a `WARNING: … skipping` branch and **continued**. Inert on
every run from this box. Same shape as the session's main findings — configured,
present, unable to fire, failing via a log line rather than an error (`623505b`).

## 6. Review battery (4 lenses, 2 models) — found 3 of my own claims wrong

Run at session close on the day's own diff. **Every one of the three statistical
errors erred toward the conclusion I was arguing.** The load-bearing conclusions
all survived on independent evidence; three supporting numbers did not.

**Withdrawn / corrected:**
- **uplifting "+0.44 SIGNIFICANT"** → *no detectable length effect*. Exact
  permutation p=0.054; fails Holm across the 6 filters tested.
- **"P(DiD ≤ −1.24) = 0.0000"** → **withdrawn**. Sampled *without* replacement
  (FPC deflates sd by √(1−15/60)); true value **8.0e-5**; and resampling the
  40-cycle window cannot answer a question about an 8-cycle window. Conclusion
  (op-point mix-up) stands on three independent lines.
- **solutions −1.13 → NOT IDENTIFIED.** Selection on the dependent variable with
  differential severity; under differential noise the artifact alone reaches
  −0.82 to −1.61. **Do not fit a cap.** Discriminating test: re-run at a second
  op-point — an artifact moves with the threshold, a real effect does not.
- **LD#86 "skewed non-English" → wrong framing.** de 4.9% / fr 5.3% are *below*
  en 13.0%; z is 2.3 not 2.6 with source clustering. The whole gap is
  `no_cultural_topic_signal` (9.9% en vs 19.2% non-en) while the other three
  rules fire *more* on English → uneven `TOPIC_GATE_PATTERNS` coverage. Sharper
  and actionable. 15.5% headline unchanged.
- **NM#285 denominator**: "replay agrees with shadow to ≤0.006" withdrawn as
  validation (different populations, verified per cycle: 8,759 vs 8,283). The
  excluded rows' pass rate is **unmeasured** — 0.008 came from pre-enrichment
  raw, 0.647 is circular. **0.129 is an upper bound, not a measured bias.**

**Survived, independently re-run:** the whole truncation measurement
(+0.0000…+0.0097), every op-point and gatekeeper triple, all LD#92 arithmetic.

**New defects found and FIXED (`4f09ecc`, deployed 11:0x CEST):**
- **NM#244 root cause** — server `Article` uses pydantic `max_length` (rejects,
  not truncates) with no client-side clamp, so ONE 1,603-char title 422'd a
  whole 100-article chunk for all six filters + obituary: **~600 lost scorings
  per affected cycle**, 40 such 422s since 07-30. Clamped + logged + tested.
- **The `INCOMPLETE` flag shipped that morning had a false negative** (both code
  reviewers, independently): uplifting v6 runs 18 url rules under non-standard
  attribute names. Widened to a source scan. ⚠️ My *first* fix used
  `inspect.getsource`, which raises OSError for every prefilter here (loaded via
  `spec_from_file_location`, never in `sys.modules`) — it silently found nothing
  on all 7. **I rebuilt the exact defect I was fixing**, caught only because the
  test asserted a positive rather than absence of error.
- **`remote_deploy.sh` pre-flight guard** was pinned to a Windows path → inert on
  Linux since 2026-04-19 (`623505b`).
- **solutions v6 docstring** claimed a ~2.64 raw surfacing floor; stale since
  NM#280, production says 2.252.

**Operator decisions outstanding:** gpu-server root fs at **97% (7.6 GB)**; a
standalone deploy leaves the scorer holding the GPU with `ollama.service` down
until the next cycle's teardown (~2h50m today).

**Pre-existing, found, not fixed:** LD `tests/unit/test_filter_config_schema.py`
`ACTIVE_FILTERS` omits `solutions` entirely (the flagship LIVE filter has never
been schema-validated) and still lists retired sustech v3 / parked foresight v1.
And `investment_risk/v6/prefilter.py` has diverged LD↔NM since 2026-05-18 (NM
blocks arxiv/mastodon_/bluesky, LD does not) — training and production filter
differently, uncovered by the empty `.nexusmind-owns`.

## Next session

1. **Split the length floor out of prefilters** as a cap/penalty (ADR-022 shape)
   — **#93**. Chain 4's new root; blocks LD#86/#87/#90.
2. **Confirm the ~12:45 CEST cycle** is unchanged after `23a9068`: the pipeline's
   `N commerce` count should match pre-deploy (the enforce key is
   behaviour-preserving, default true).
3. **solutions cap is NOT justified yet** — re-run the LD#92 test at a second
   op-point (or matched percentile bands) to separate the effect from the
   selection artifact. Only then consider a cap.
4. Fix `no_cultural_topic_signal` multilingual coverage, then re-run
   `scripts/measure_prefilter_recall_cost.py` — falsifies whether LD#86's
   language skew is the gate or the corpus.
5. NM#286 item 3, then LD#82, before any violence enforce flip.

## Related

- [[project_session_2026_08_01]] — the session whose two P0 conclusions this one corrected
- [[reference-nexusmind-data-sources]] — the two denominator traps
- [[cross-repo-prioritization]] — needs updating: NM#285 no longer blocks LD#86/#87/#90 on truncation grounds
