---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

⛔ **Dated board snapshots, refreshes, orderings and chain verifications (2026-08-01 → 08-12) are in [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md)** — moved verbatim, order kept, 2026-09-27 (TODO item −1 step 3), with the 8 `verify:` count probes that lived in them. Kept here: the query, the topology rule, the chains, rankings, batches, standing decisions. ⚠️ Chains and rankings are themselves August state: re-query before acting on one.
⚠️ **2026-10-12 (item 2b, date rule): the chains whose newest date predates 2026-09-01 moved there too** — 1, 3, 5, 8–11, 13, 15–17 and the stale-dependency sweep. Their headings stay below as hooks; chains 2, 4, 6, 7, 12 and 14 are still live here.

## ⛔ THE BOARD COUNT IS NOT IN THIS FILE. RUN THE QUERY.

**Removed on purpose, 2026-08-17. Do not restore a current-state count table
here, in `memory/MEMORY.md`, or in `docs/TODO.md` — regenerating one out of habit
is the failure this removal exists to prevent.** There is nothing to update; there
is a command to run, and its output is quoted with the timestamp you ran it at.

```
tot=0; for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news \
  ducroq/FluxusSource veen-systems/persuasion-scorer veen-systems/pipeline-atlas \
  ducroq/augmented-engineering; do
  n=$(gh issue list -R $r --state open --limit 400 --json number --jq 'length')
  echo "$r: $n"; tot=$((tot+n)); done; echo "TOTAL: $tot"
```

**Every dated section (now in `archive/cross-repo-prioritization-archive.md`) is a SNAPSHOT, not state.** They are kept because
their columns are *not* re-derivable — `gh` returns *now*, and nothing recovers
"open on 2026-08-09, touched ≤2d" or a sediment count against a stated cutoff.
**Read them as history and never refresh one in place**: a snapshot edited to
today's numbers stops being provenance and becomes a mirror again.

⚠️ **The count was never the main drift.** Over this file's own text on
2026-08-17: **17 self-corrections, of which 4 concern counts and 13 concern the
narrative** — a chain reframed, a link marked ✅ while open, a peer-reported fact
that decayed. ⛔ **The SPLIT is the finding; the TOTAL is an artifact of the word
list** — this is a hand-built population, a keyword grep chosen by a participant
over one file, and a broader list run by a peer returned 72 hits. What is hard is
the classification: two classifiers, the second blind, agreed on all 17 including
the one borderline (a retracted claim about a *ground-truth* count, not a board
count — narrative). ⚠️ **Reproduce with the command below and no other** — the
pattern names its own markers, so running it over the whole file counts this block
too and reads 20. Anchoring past the heading is what makes it measure the history rather
than itself. Deleting the table addresses the smaller class. The rule that
addresses the larger one is in the archived 2026-08-12 section, restated here, and is the one that matters: **before
ranking, recommending or describing work in a repo that is not this one, query
that repo** (2026-08-12), and **stamp a peer-reported fact as peer-reported, with
its date**.

```
{ awk '/^## Board snapshot/,0' memory/archive/cross-repo-prioritization-archive.md; \
  awk '/^## Cross-Repo Dependency Chains/,0' memory/cross-repo-prioritization.md; } | grep -cE \
  "was wrong|were wrong|CORRECTED|corrected me|retract|was false|already stale|consecutive pass|which was true when written|decayed"
```

---

### The topology rule (2026-08-03)

**An issue belongs in the repo that will contain the fix, not the repo where the
symptom appeared.** In a pipeline — FluxusSource → NexusMind → ovr.news, with
llm-distillery feeding filters in sideways — those are almost never the same
place, which is how one defect becomes two or three issues.

Evidence from a single reader complaint about ovr.news on 2026-08-03, which
decomposed into three defects in three repos, none of them ovr.news:

| symptom seen on ovr.news | actually owned by |
|---|---|
| article shows a "Get it on Google Play" badge as its image | **NexusMind#290** — hero extraction has no cross-domain check; reproduces *with* NM#287 in place |
| two same-story articles show no corroboration | **NexusMind#291** — cross-source threshold 0.88 vs measured 0.8355 for genuine same-story pairs |
| (found while investigating) `años` rendered `a√±os` | **FluxusSource#124** — UTF-8→MacRoman at collection, 5.0% of articles, non-English only |

Same shape earlier the same day: NM#284 and NM#285 were both filed in NexusMind
and the fix was **LD#93** in llm-distillery. One defect, three issues, two repos.

## The cloud angle — what a Claude Code cloud session can close (2026-09-29)

⛔ **Standing rules only — the triage, the three pilot records and the cloud-environment facts were retired
VERBATIM 2026-09-29 to [`archive/project_session_2026_09_29_cloud_pilots.md`](archive/project_session_2026_09_29_cloud_pilots.md)
§ *Retired verbatim*.** Pilots **STOPPED** by the owner the same day (focus: NexusMind#395 migration).

- **Class decides dispatch.** C = inputs in git, done = a test → cloud. D = code self-contained, outcome needs a
  cycle/data → cloud draft, prove locally. L = GPU, oracle spend, production data, deploys, owner rulings → never.
  The C/D/L issue lists are a 2026-09-29 08:31 snapshot, triaged from titles — re-read each issue first.
- **A cloud PR is a draft; the review needs THIS machine.** 2 of 3 pilot PRs carried a defect only a local
  review found (a fail-open deploy-guard bypass, twice; 4 false placeholder marks); the 3rd shipped a suite count its branch could not produce. Never merge on its own evidence.
- **Every cloud prompt names:** the fresh-clone baseline (`pytest tests/ -q` → 18 failed, 48 skipped on `main`:
  missing gitignored keys + models) and **targeted tests only** (the full suite hung ~2 h in the cloud).
- **Follow via the `View:` link. `--teleport` is NOT a view** — it pulls the session onto this machine and into
  the shared checkout (pilots 1 and 2 both ran locally because of it).
- **Measured cost:** $2.13 (#162) and $4.76 (#136, incl. two fix rounds); pilot 3 not read. Whether it drew on
  the $100 credit or the subscription: **not established**.

## Cross-Repo Dependency Chains

`→` means "blocked on" or "feeds into."

### Chain 1: Obituary Detector — **CORRECTED 2026-08-07: NOT complete** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 2: Violence Promotion — shadow, enforcement gated
```
LD#73 (OPEN, but done — close it) → NM#274 ✅ → NM#281 gate wiring ✅ (inert)
   → LD#82 (audit) + NM#286 item 3 → enforce
```
**Two hard gates before any flip:** LD#82 (v1 recall 0.55 → enforcing gates ~half
of true positives) and NM#286 item 3 (violence stamping skipped in 3 run modes).

**LD#73 was marked ✅ and is open — bookkeeping only.** The classifier shipped
under a different name (`filters/common/violence_promotion/v1/`, verified
present in this checkout), its ADR-004 stamp-only question was answered, and
its downstream NM#274 is closed. Close LD#73 as done; nothing in Chain 2
depends on it.

### Chain 3: Normalization Refits — **CLOSED 2026-08-01** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 4: Prefilter Resurrection — **MEASURED 2026-08-02; RE-ROOTED**
```
NM#284 (stage 1 shadow) ✅ → NM#285 (measured, Option B shipped 89f2e5b) ✅
   → NEW ROOT: split the length floor out of prefilters into a cap/penalty
                              → LD#86 (cd enforce — measured, DO NOT FLIP)
                              → LD#87 (cd v6 op-point) → LD#90 (harmonization)
```
**Truncation was NOT the problem** — measured at +0.0000 (nr, solutions) to
+0.0097 (ir) on the production-relevant population. Option C declined: its cost
saving came almost entirely from the length floor, which is the rule we now
don't want to enforce. Option A buys a rounding error.

**The real findings.** (1) `nature_recovery v4` and `solutions v6` prefilters are
pure length floors by design (`EXCLUSION_PATTERNS = {}`); their
`expected_pass_rate` is deleted, not corrected — 0.644 is a corpus statistic.
(2) A **larger, opposite-signed denominator bias**: the shadow counts articles
`source_filter` discards post-scoring — ir logs 0.642 vs 0.770 on articles that
can actually surface. (3) "Enforce the prefilter" = "enforce a 300-char length
floor" for 87–100% of blocking on four of six filters.

**LD#86 is now measured and the answer is NO:** enforcing cd's gate costs 15.5%
of surfacing articles (135/871 over 20 cycles), skewed non-English (19.9% vs
13.0% English, p≈0.01). ⚠️ *Retracted framing (corrected 2026-08-02, `memory/prefilter-length-floor-hypotheses.md` item 7): pooled "non-English 19.9%" describes no real population — German 4.9% and French 5.3% sit BELOW English's 13.0%; the gap is `no_cultural_topic_signal` keyword coverage. Moot since per-lens prefilters were deleted 2026-10-01.* Zero high-tier losses. `no_cultural_topic_signal` is 86%
of the loss — fix its multilingual coverage, then re-run the check.

### Chain 5: Solutions Lens — largely complete — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 6: Commerce — resolved, but contract gap reopened
```
LD#80 ✅ (v1 forced, verified) → NM#286 items 1+2 (no enforce key + consumer-side drop) ← MOVE TOGETHER
```
Watch signal: `_commerce_model == "gpu-server-unpinned"` in production means the
LD#80 guard regressed.

### Chain 7: Summarizer — **RE-SEQUENCED (was wrong)**
```
ovr#277 (non-destructive re-gate) ← PREREQUISITE
   → ovr#235 (held-out validation gate) → ovr#270 (gemma3:27b → gpt-oss:20b)
   ↔ ovr#267 (audit findings) ↔ ovr#276 (temp=0 non-determinism) ↔ ovr#286 (397 summary backfill)
```
Without ovr#277, measuring the after-side destroys the before-side. ovr#276
(lost byte-identical reproducibility) independently weakens any A/B.

### Chain 8: Google News — **DEADLINE-DRIVEN** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 9: Hero Images — **NEW; grew again 08-03** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 10: Dedup / Corroboration — **RE-ROOTED 2026-08-07 on NM#301** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 11: Score Provenance / Publication Floor — **CLOSED 2026-08-07** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 12: Source Classification (dormant)
```
FluxusSource source_classification → NM#253
```
Neither side urgent.

### Chain 13: Score Reproducibility — **NEW 2026-08-03, cross-cutting** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 14: Non-English Content Quality — **NEW 2026-08-03; root = NM#292**
```
NM#292 (tracking root, filed 2026-08-03)
FS#124 (mojibake at collection, 5.0%, non-English-concentrated) — FIXED ea25ae8,
  but RELOCATED to NM#338 (same defect in NexusMind's enricher, 5.639% introduced,
  6.86x non-English skew) — the limb is LIVE, not closed
   → NM#231 (uplifting under-scores non-English documented-outcome news, 19 panel-confirmed)
   → NM#291 (dedup threshold misses cross-language same-story pairs at 0.836)
   → LD#86 (cd prefilter enforce would cost 19.9% non-English vs 13.0% English, p≈0.01 — RETRACTED framing, see item 7 of memory/prefilter-length-floor-hypotheses.md; moot since 2026-10-01)
   ↔ LD#93 (sub-300 population is dominated by gn_* / spanish_* / french_* / gn_africa_*)
   ↔ FS#128 ✅ CLOSED 2026-08-06 (rferl_kazakh never collected Kazakh — both feeds
              hit a generic endpoint). The *class* survives it as FS#126 (also closed):
              the collection stage failing *before* text quality
   ↔ FS#129 / FS#130 / FS#131 (language tagging: two conventions; langdetect
              confidently wrong on 8 regional languages; use the feed's declared
              language when there is no profile) ← the live non-English links
   ↔ ovr#299 ✅ CLOSED COMPLETED 08-05 (headline-only summaries 83.4% invented).
              **Not verified here what shipped** — only that it closed as completed;
              the proposed fix was an input-scaled output budget
```
**Four independent measurements in four repos, all pointing the same way, none
of them owned as one problem.** Each was filed where its fix lives — correctly,
per the topology rule — but the result is that no single issue states the
pattern: non-English content is disadvantaged at collection (corrupted text),
scoring (under-scored), dedup (never clustered), and gating (over-blocked).

**Root filed 2026-08-03 as NM#292** — in NexusMind because it is the stage that
composes all four effects (consumes FluxusSource text, runs the scorers, owns
dedup). The reader-visible symptom is on ovr.news — a feed that
under-represents the non-Anglophone world — but no *fix* belongs there, which is
why this went unnoticed until the four were placed side by side.

**NM#292 asserts nothing beyond direction.** The four numbers come from separate
studies on separate populations and are **not reconciled to a common
denominator** — they must not be multiplied together. The shared-root hypothesis
(English-centric training data, English-first rules, English-tuned thresholds)
is a hypothesis, not a finding. The next step NM#292 proposes is the one
measurement that would settle it: English vs non-English surfacing rate, mean
score and corroboration rate on **one** denominator, controlling for source
type. ~~Small gap → close won't-do; large gap → pull FS#124 and NM#291
forward.~~ **DROPPED 2026-08-07.** The decision rule no longer discriminates:
⚠️ **this rationale rests on a premise now PARTLY WITHDRAWN (2026-08-12) — see NM#338: the defect relocated rather than closed, and FluxusSource's post-fix rate is 0.081%, not 0.000%.** As written 2026-08-07: FS#124's collection defect is fixed (verified 0.00% on the first run after
`ea25ae8`) and NM#291 is already prioritised inside the dedup programme, which
is proceeding on merged-pair precision rather than on language. A large gap
would now say "do what you are already doing". NM#292 stays open, retargeted as
the stage index plus the cross-cutting constraint list — first constraint: any
corroboration confidence bar must be **per-language-pair aware**. Also note the
obvious way to run that measurement (`filtered_*.jsonl`) is 100% passers by
construction and drops source-type-excluded rows, so it would flatter the
pipeline.

### Chain 15: Lens Commensurability — **NEW 2026-05-28** *(re-dated 2026-08-07; was filed here as "NEW 2026-08-05")* — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 16: persuasion-scorer verification track — **NEW 2026-08-07, was never banded** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Stale cross-repo dependencies — the full sweep, 2026-08-07 (night) — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

### Chain 17: NER Enrichment — **NEW 2026-08-07; one blocked root, five dependents** — MOVED to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) (2026-10-12)

## Rankings, batches and standing decisions — RETIRED 2026-09-29

⛔ P0–P4, the coverage table, work batches A–F, housekeeping and the standing operator decisions were **August 2026 state** and moved VERBATIM to [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md) § *Retired 2026-09-29*. **Current priorities live in `docs/TODO.md` ▶ START HERE**; for another repo, query that repo (`gh issue list`) before ranking anything in it.

## Related Memories

- [[project_session_2026_08_05]] — LD#92 identified, GN evidence into FS#120, ovr#299 filed
- [[project_session_2026_08_03]] — LD#93 ship + sync, LD#95, the three upstream defects
- [[project_session_2026_08_01]] — the session the prior update followed
- [[project_session_2026_07_31]] — Chain 3 deploys
- [[project-obituary-detector]] — Chain 1 details
- [[filter-status]] — per-filter MAE/status
- [[calibration-history]] — Dead Ends (read before calibration/scorer work)
