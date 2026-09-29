---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

⛔ **Dated board snapshots, refreshes, orderings and chain verifications (2026-08-01 → 08-12) are in [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md)** — moved verbatim, order kept, 2026-09-27 (TODO item −1 step 3), with the 8 `verify:` count probes that lived in them. Kept here: the query, the topology rule, the chains, rankings, batches, standing decisions. ⚠️ Chains and rankings are themselves August state: re-query before acting on one.

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
VERBATIM 2026-09-29 to [`project_session_2026_09_29_cloud_pilots.md`](project_session_2026_09_29_cloud_pilots.md)
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

### Chain 1: Obituary Detector — **CORRECTED 2026-08-07: NOT complete**
```
LD#51 ✅ → LD#77 ✅ → NM#185 obituary half ✅ → v4 ✅ → LD#83 (v5 + ENFORCE @0.85) ✅
   → ovr#204 (remove the hardcoded filter) ← ACTIONABLE NOW, not blocked
   → NM#185 commerce half ← OPEN AND UNSTARTED (no v3 exists)
```
The obituary strand is done: enforcement live + verified (1,158 blocked),
carryover washed out ~Aug 2–6 by window. LD#85 (v6 relabel) PARKED indefinitely
by owner.

**NM#185 was marked ✅ here and is open.** It bundles the obituary blocker
*and* a **commerce prefilter v3 retrain that was never started** —
`filters/common/commerce_prefilter/` has v1 and v2 only, with v1 force-pinned
(LD#80) because v2 underperformed. Before any v3 work: its evidence is stale.
The commerce miss set recorded in NM#185 was **100% `sustainability_technology`
articles**, and that filter was **deleted 2026-08-03**. Re-measure against
`solutions v6` first; the retrain may not be warranted on the surviving lens
set.

**ovr#204 is not blocked.** Its title says "after NexusMind#185 ships", which is
true of the half it depends on.

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

### Chain 3: Normalization Refits — **CLOSED 2026-08-01**
Verified live across six consecutive cycles. No open links.

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
13.0% English, p≈0.01). Zero high-tier losses. `no_cultural_topic_signal` is 86%
of the loss — fix its multilingual coverage, then re-run the check.

### Chain 5: Solutions Lens — largely complete
```
LD#43 ✅ → v4 ✅ → v6 (gate passed, normalized) ✅ → LD#84 (prompt router, v7 only) → NM#204 ✅ CLOSED superseded 08-07
```
~~solutions v6 is the real LD#90 mismatch (declares 0.20, passes 0.59).~~
**RESOLVED 2026-08-02** — not drift: solutions v6's prefilter has no lens rules
at all (`EXCLUSION_PATTERNS = {}` by design), so there was no gate to miss.
`expected_pass_rate` deleted rather than corrected. solutions v6 *is* now the
filter carrying the LD#92 short-content defect (DiD −1.13).

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

### Chain 8: Google News — **DEADLINE-DRIVEN**
```
FS#118 ✅ → FS#119 ✅ → ovr#275 resolver ✅ (623cc82) + attribution surface ✅ (8ab610a)
   → FS#120 eval readout + ADR-007 decision gate ← DUE ~2026-08-14
```
The only calendar-bound item on the board. Eval identities collecting since
07-31; needs ~2 weeks. ovr#275 itself is closable after the ~Aug 2 backlog
washout check.

### Chain 9: Hero Images — **NEW; grew again 08-03**
```
NM#282 ✅ (ML logo classifier dead since 06-16) → ovr#281 (stock sticky + validateImageUrl false-rejects ~half)
   → ovr#284 (Comscore beacon: legal record + non-accidental control) → ovr#255 (academic stock photos)
   ↔ NM#227 / NM#222 / NM#183 / NM#182

NM#287 ✅ (lazy-load: any src= beat the hero) → fixed by NM#288 ✅
   → NM#290 ✅ CLOSED 08-03 (cross-domain check — allAfrica Google Play badge)
   → ovr#287 (backfill wrong-story rows) ← DECIDED 2026-08-07: BLANK, scoped per row
   → NM#294 (validation cap 200 ⇒ ~79% of heroes unvalidated) ← NEW, unbanded
   → ovr#295 ✅ CLOSED 2026-08-06 (og-reuse cache blind to upstream images)
   → ovr#302 ✅ CLOSED 2026-08-06 (author byline portraits as heroes, pv-magazine)
   → ovr#297 (looksLikePublisherLogo misses logo300.png and /images/) ← still OPEN
   → ovr#305 (image_source='og' collapses self-extracted and upstream-supplied)
   → ovr#306 (threat-FMEA: no entry for a third-party URL in a hotlinked field)
```
**Refreshed 2026-08-05:** NM#290 closed, but the class did not close with it —
ovr#295/#297 are publisher-logo heroes reaching readers by a *different* route
(upstream-supplied images the cache never sees), and NM#294 says ~79% of heroes
are never validated at all. Chain 9 is the longest-lived chain on the board and
each fix has so far revealed one more path to the same reader-visible symptom.
ovr#281 measured: of 25 rescuable, 11 would succeed today (stickiness), 12 are
`validateImageUrl` false-rejects, 2 fetch failures. ~10% of articles affected.

**The NM#287 fix stops new bad rows; it does not repair stored ones** — 33 of 40
recent `vanguardngr.com` articles carry a sidebar-rendition image from a
different story, 67% of that publisher's last 60 days, ~36 rows DB-wide. ovr#287
needs an operator call: **re-extract** (correct hero, N fetches, some 404s) vs
**blank** (cheap, certain, loses ~36 heroes). NM#288's own principle — *a missing
image beats a confidently wrong one* — argues blanking is sufficient and
re-extraction is a bonus. ~~**Blocker on targeting:** fix the `image_source`
stamp first or the backfill re-fetches everything.~~ **Not a blocker at the
scope decided 08-07.** The stamp ambiguity blocks a *DB-wide re-fetch*; it does
not block blanking a handful of known ids, which is what shipped — targeting is
by URL pattern, per row, with buildability computed rather than assumed. The
stamp is still worth disambiguating before the next backfill and is now
**ovr#305**.

### Chain 10: Dedup / Corroboration — **RE-ROOTED 2026-08-07 on NM#301**
```
NM#301 (merged-pair precision 0.560 at 2 sources — the reader-facing claim)  ← NEW ROOT
   ↔ ovr#303 (the site publishes boost values NexusMind has never computed)
   → LD#100 (event-identity encoder: production is beaten on F1 by merging everything)
   → OPEN DECISION 7 (ovr.news's OWN 1.3/1.5/1.7x boost — NOT fixed by NM's 1bbadb5)
ovr#280 (ovr-side ingestion of cluster_id — data IS on the wire) → NM#278 (threshold retune for title-only E5)
   ← NM#291 (cross-source threshold 0.88 vs measured 0.836 for genuine cross-language same-story pairs)
   ↔ NM#228 (complete-linkage shadow — SEQUENCED BEFORE NM#278, see the 08-04 section)
   ↔ NM#188 / NM#170 / NM#215 / NM#275(closed)
```
**Why NM#301 roots this and is not just another link:** every other member is
about *which articles get merged*. NM#301 is about *what we tell the reader we
merged* — live today at ~0.560 precision, and actionable without waiting on any
retune. Its wording half shipped 2026-08-07; its ranking half is open.

Do the ovr ingestion fix first — it is cheap and the data already exists.
**Caution on NM#278:** NexusMind *removes* rather than *labels* (~32%/run);
anything removed upstream can never surface as an "N sources" badge.

**NM#291 is the measured input NM#278 was missing** — the retune is no longer a
"pick a number" task. Note the failure is *cross-language*: see Chain 14.

### Chain 11: Score Provenance / Publication Floor — **CLOSED 2026-08-07**
```
ovr#285 ✅ (stop NULLing raw_weighted_average) → ovr#283 ✅ CLOSED won't-do 08-07
   ← informed by LD#91 (a floor would NOT have caught it — raw 6.77 is genuinely 99.9th pct)
```
**No floor.** Measured before deciding: no stored row carries a raw score below
4.03, so a floor binds nothing — and the monitoring alternative is
*mis-specified against its own motivating case*, since LD#91's article scored
6.77 (6th highest) and a low-raw-at-high-rank alert stays silent through it.
`raw_weighted_average` keeps being stored; it costs nothing and is the input to
any future check.

**Reopened one level down as ovr#304**: a floor already exists
(`displayScoreThreshold: 4.5`) and keys on the *normalized* score, against
ADR-022. Different defect, different issue.

### Chain 12: Source Classification (dormant)
```
FluxusSource source_classification → NM#253
```
Neither side urgent.

### Chain 13: Score Reproducibility — **NEW 2026-08-03, cross-cutting**
```
LD#95 (batch composition moves a score up to 0.162; 7.1% / 9.1% of near-boundary
       articles flip verdict or tier)
   → undermines: ADR-021 ground-truth gates · normalization CDF fitting (Chain 3)
                 · before/after deploy checks · op-point comparisons (Chain 4)
   ↔ NM#289 (medium fixture scores into high on the three percentile-normalized filters)
   ↔ gotcha-log 2026-07-30 "cross-box skew |0.16|" — ⛔ BOTH HALVES RETIRED 2026-08-29:
     the HOST term is 0.0000 (660/660), and the real terms are the library STACK
     (0.2008) and the DEVICE CPU→CUDA (0.1956), both ABOVE 0.16. See
     docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md
   ↔ NM#226 (document raw → isotonic → percentile → tier as a chain of transformations
              with a stated invariant per step)  ← created 2026-05-28, zero comments,
              banded nowhere until 2026-08-07; documentation-only scope
```
**This one is not a defect in a component, it is a noise floor under the
measurements the rest of the board is made of.** Same model, same weights, same
box, same process — only `batch_size` differs. The follow-up measurement answered
the question the original could not: it *does* change decisions, at 7.1%
(solutions v6, 2/28 in band) and 9.1% (uplifting v7, 3/33 in band) of articles
within ±0.30 of the op-point. Flips occur within 0.077 / 0.039 of the op-point.

Consequence for everything else here: **a run-to-run delta below ~0.1 near an
op-point is currently indistinguishable from batch noise, and nothing on the
board states that.** Chain 4's enforce flips, Chain 3's refits, and every
ADR-021 gate compare exactly this quantity. ~~Cheapest mitigation is pinning
the production batch size.~~ **Not available — settled 2026-08-06.**
`DEFAULT_BATCH_SIZE` is already fixed at 16; the variable is batch
*composition*, which a size pin cannot touch. What shipped instead: a seeded
per-cycle shuffle (`f7fef85`) giving **replay, not stability** — the next cycle
reshuffles and the article moves again — plus the floor as a **band the deploy
gate prints** (`--noise-floor`, default 0.16). Two models whose bands overlap
are NOT DISTINGUISHABLE.

**NM#226 placed here 2026-08-07 — it is this chain's missing write-up artefact.**
Filed by the owner on 2026-05-28T16:42 (34 seconds after NM#225, Chain 15's
root), open, zero comments. It asks for the four-step pipeline — raw model output
→ isotonic calibration → percentile normalization → tier thresholding — to be
documented as a sequence of transformations with a stated invariant per step, so
that *"which invariant changed at which step"* becomes a localised question
instead of implicit knowledge. That is precisely what LD#95 and NM#289 are stuck
on: LD#95 shows the **raw** step carries no batch-invariance guarantee, and
NM#289 shows the **percentile** step stretching the upper-middle — neither was
localisable because the invariants were never written down. NM#226 already states
three of them (isotonic preserves order and discards absolute distance;
percentile preserves rank and is population-relative; tiers are discrete cutoffs
on that population-relative space). Scope is documentation only, so it is cheap.

**NM#289 may be the same family seen from the other end.** Chain 3 was closed on
the *lower* boundary (good content crushed below medium); NM#289 reports the
three `norm=percentile` filters — uplifting, cultural_discovery, belonging, the
same three from the LD#76 crush list — pushing a deliberately middling fixture to
wa 7.7–9.7 on raw 5.7–6.8. Raw scores are unremarkable; the percentile mapping
is stretching the upper-middle. **Chain 3 is closed for the boundary it was
opened on, not for the CDF as a whole.**

### Chain 14: Non-English Content Quality — **NEW 2026-08-03; root = NM#292**
```
NM#292 (tracking root, filed 2026-08-03)
FS#124 (mojibake at collection, 5.0%, non-English-concentrated) — FIXED ea25ae8,
  but RELOCATED to NM#338 (same defect in NexusMind's enricher, 5.639% introduced,
  6.86x non-English skew) — the limb is LIVE, not closed
   → NM#231 (uplifting under-scores non-English documented-outcome news, 19 panel-confirmed)
   → NM#291 (dedup threshold misses cross-language same-story pairs at 0.836)
   → LD#86 (cd prefilter enforce would cost 19.9% non-English vs 13.0% English, p≈0.01)
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

### Chain 15: Lens Commensurability — **NEW 2026-05-28** *(re-dated 2026-08-07; was filed here as "NEW 2026-08-05")*
```
NM#225 (audit every cross-filter score comparison; document the policy as an ADR)
        ← ROOT, open, created 2026-05-28T16:42, zero comments, banded nowhere for 71 days
   ⟂ LD#95 (noise floor |Δ| ≤ 0.16)
   ⟂ LD#96 (lens placement compares scorer outputs that are not the same construct)
   → ovr#296 (toCanonicalLens breaks near-ties: Kixikila lost Belonging to
              Discovery by 0.043 — inside the noise floor)
   ↔ LD#61 (cross-filter trajectory-framing mis-lensing)
   ↔ ovr#298 (summary framing makes a qualifying story read as disqualifying)
   → gates LD#90 (harmonization presumes one comparable score across lenses)
```
**Re-dated 2026-08-07: this chain is 71 days old, not 2.** The previous text said
"two repos derived the same defect independently on the same day, which is the
topology rule working". There are **three** derivations and the earliest is
**NM#225**, filed 2026-05-28T16:42 with zero comments. LD#96 (2026-08-05T07:09)
and ovr#296 (2026-08-05T06:34) came 69 days later. Verified with
`gh issue view 225 --repo ducroq/NexusMind --json state,createdAt,comments`.

**NM#225 is also the most actionable of the three**, because it names audit
*targets* rather than one instance: tier assignment that mixes filters, **lens
routing in ovr.news** (`toCanonicalLens`), and any "primary topic" logic that
picks the highest-scoring filter — plus the deliverable, an ADR stating which
comparison method is used, on what assumptions, and what changes when any filter
is recalibrated. ovr#296 is one instance of its second target, found
independently 69 days later.

**The unmeasured quantity is the one that decides how urgent this is: what share
of lens placements is settled by a margin smaller than 0.16?** Nobody owns that
count — but it is a **subset of NM#225 step 1**, so scope it inside that audit
rather than filing it separately. Until it exists, Chain 15 is a hypothesis with
three filed symptoms and one filed root, not a finding.

### Chain 16: persuasion-scorer verification track — **NEW 2026-08-07, was never banded**

```
ps#4 (verify the Gemini backend against the live API)  ← SPEND GATE
ps#2 (DR-011 Pass 2: outside review of all 34 registry rows) ← PHASE GATE, "before Phase 3, not after"
   ↔ ps#10 (re-derive the 0–10 shape: degree vs presence was never decided, only inherited)
      → ps#12 (S5-2 thresholds: absolute deltas reward the flat scale they should catch)
      → ps#9  (reader-facing rendering for #79-B: raw 0–10 must not ship)
      → ps#5  (re-map the six guard cases to the six coarse dimensions)
   ↔ ps#8  (probe: test–retest / paraphrase / mirrored-framing consistency modes for S5-2)
ps#3 / ps#6 (source work: Sproule 2001 + Roozenbeek 2022; NLP4IF-2019 licence, Maarouf 2024, Sahitaj 2025)
ps#7 / ps#11 / ps#13 (DR numbering collision at DR-008; ADR citations; the pre-commitment-override protocol)

── the NexusMind + ovr.news side, added 2026-08-07 ──
NM#254 (content-level propaganda-technique extractor — reader signals, never a verdict)
   ← HOLDS THE TAXONOMY DECISION, in a 2026-08-02 cross-post FROM persuasion-scorer
   → constrains ps#10 / ps#12 / ps#9 / ps#5 (scale shape, thresholds, rendering, guard-case mapping)
   ↔ ovr#253 (summary-fidelity: surface provenance/confidence) ← NM#254's stated pair, also unbanded
```

**Why this exists: all 12 of persuasion-scorer's open issues were counted in
every total on this board and sequenced in nothing.** The Coverage table
enumerates unbanded issues for the other four repos and has no row for this
one. They are not sediment — every one was last touched **2026-08-02** — they
are a block that stopped moving five days ago.

**Two are gates and should be read as such before any work there resumes:**
**ps#4** blocks corpus spend (the Gemini backend has never been checked against
the live API), and **ps#2** says the outside review of all 34 registry rows
belongs *before* Phase 3. **ps#10** is the one that could invalidate the others
— whether the 0–10 scale measures degree or presence "was never decided, only
inherited", and ps#12, ps#9 and ps#5 all assume an answer.

**NM#254 added 2026-08-07 — the chain had no NexusMind link, and the taxonomy
decision lives there.** NM#254 (open, created 2026-06-28, last updated
2026-08-02 — the same day all 12 ps issues were) is the enrichment-path sibling
of this work. Its second comment is a cross-post *from* persuasion-scorer
carrying the decision: use the canonical **SemEval-2023 Task 3** taxonomy and
score the **6 coarse categories, not the 23 fine** — inter-annotator agreement on
the fine labels is Krippendorff **α = 0.342** against the organisers' own 0.667
threshold, and LLMs fail hardest exactly there (GPT-4 macro-F1 0.13–0.16 vs 0.67
for a supervised baseline). Three further constraints in that comment bind
ps#10/#12/#9/#5 directly: annotations **overlap and nest**, so a single-label
contract is wrong; **zero-technique articles are real**, not an edge case; and
**SemEval-2023 / PTC licensing bars any shipped training use** (prompt validation
only). It also records US 12,223,265 B2 as patent-adjacent to per-sentence labels
in a reader UI. **ovr#253** (summary-fidelity provenance, open since 2026-06-26)
is NM#254's stated pair and is likewise banded nowhere; it joins here as the
reader-facing end.

**Scope caveat:** this chain is assembled from issue *titles* only. Nothing in
persuasion-scorer's own docs was read, and the arrows are inferred, not
confirmed by that repo. Treat the grouping as a placement so the block stops
being invisible, not as a verified sequence. Per CLAUDE.md the dependency runs
one way — persuasion-scorer depends on this repo's distillation machinery and
must never vendor a copy — so nothing here blocks llm-distillery work.

### Stale cross-repo dependencies — the full sweep, 2026-08-07 (night)

**Enumerated, not just counted** — this board's own rule is that a findings list
is a sample unless it names its members and its method, and the previous pass
reported "13 instances" without either.

**Method** (re-runnable): `gh issue list -R <repo> --state all --limit 1000 --json
number,title,state,stateReason,body` for all seven repos, extract cross-repo
references from **issue bodies**, join against actual state. Counts returned:
LD 100 · NM 273 · ovr 288 · FS 117 · ps 13 · pipeline-atlas 3 ·
augmented-engineering 35. **Not covered: issue *comments*, docs, and code
comments** — NM#254's taxonomy decision arrived by comment cross-post and this
method would have missed it. Rate limit never hit.

| # | Citing (OPEN) | Cites | State of cited | Corrected? |
|---|---|---|---|---|
| 1 | NM#223 | FS#85 | CLOSED NOT_PLANNED | yes (08-07 late) |
| 2 | ovr#222 | FS#85 | CLOSED NOT_PLANNED | yes (08-07 late) |
| 3 | ovr#223 | FS#85 | CLOSED NOT_PLANNED | **yes (08-07 night)** |
| 4 | ovr#231 | FS#85 | CLOSED NOT_PLANNED | **yes (08-07 night)** |
| 5 | ovr#231 | NM#224 | CLOSED NOT_PLANNED — **abandoned, not re-homed** ("superseded by v3: frozen embeddings alone achieve 0 FPs") | **yes (08-07 night)** |
| 6 | ovr#232 | FS#85 | CLOSED NOT_PLANNED (soft — body also says "not gated on NER bundle") | **yes (08-07 night)** |
| 7 | **LD#38** | NM#108 | CLOSED COMPLETED 2026-05-10 — and LD#38 asserts it is *"open, waiting on this"*, which is the filter's whole justification | **yes (08-07 night)** |
| 8 | **LD#56** | NM#161 | CLOSED COMPLETED 2026-05-11 (parent closed, child open) | **yes (08-07 night)** |
| 9 | **LD#23** | NM#88 | CLOSED COMPLETED 2026-03-06 — *same defect*, closed upstream 5 months ago | **yes (08-07 night)** |
| 10 | ovr#177 | NM#126 | CLOSED COMPLETED 2026-04-06 ("awaiting upstream fix" — it landed) | no |
| 11 | ovr#210 | LD#62 | CLOSED COMPLETED 2026-06-01 (step 7 reads as pending; is actionable) | no |
| 12 | **FS#133** | NM#213 | CLOSED COMPLETED 2026-05-23 | **yes — mine, filed 08-07 late** |
| 13 | **FS#134** | NM#213 | CLOSED COMPLETED 2026-05-23 | **yes — mine, filed 08-07 late** |

**Rows 12 and 13 were filed by the same pass that documented this trap.** Knowing
a failure mode does not prevent it; only checking your own work against it does.

**Also stale, inside this file** (all corrected 08-07 night): NM#213 cited as the
live matching-model consumer, NM#220 (closed 07-07), NM#91 (closed 03-06 **and
mis-described** — it is "Pipeline-run summary notification", not healthcheck
drift), LD#43 (closed 07-28), LD#49 (closed 07-27), FS#125/#126 (closed 08-06).
**And one non-issue:** NM#288, cited at two places, is a merged **pull request**,
not an issue — `gh issue view` returns a PR object, which is why it reads as one.

**Still open, not chased:** rows 10 and 11 are in ovr.news and were left for a
session working in that repo.

### Chain 17: NER Enrichment — **NEW 2026-08-07; one blocked root, five dependents**
```
NM#232 (NER as an early enrichment stage; persist per-article entities)
        ← BLOCKED ROOT, open, created 2026-06-14, untouched 54 days until 2026-08-07
        ← re-homed from FS#85, CLOSED NOT_PLANNED 2026-06-14 (reads as satisfied — it is not)
   → NM#223 (entity-density as additive signal to commerce_prefilter) — open, 2026-05-27
        → NM#185's commerce v2 → v3 half
   → NM#185 (obit-classifier NER feature input) — open, 2026-04-22
   → ovr#222 (corroboration explainability: shared-entity evidence in the rationale) — open
        ← cites the CLOSED FS#85 as its prerequisite
   → ovr#223 (/places/{country} discovery surface across all five lenses) — open
        ← needs canonical country IDs, i.e. entity *disambiguation*, which NM#232 scopes OUT
   ⟂ the story-dedup matching model — NM#188 (open) / NM#301 (open); NM#213 is CLOSED
        ← THE FIFTH CONSUMER, and it appears nowhere in NM#232's own list
⊘ gate: ovr.news SUSTAINABILITY.md Tier 1 track #1 "Finish donation pathway"
        (pipeline-stability + audience-signal) — inherited from FS#85, not chosen here
```
**Verified 2026-08-07: no NER exists anywhere in the NexusMind pipeline.** grep
for spacy/gliner/stanza/nltk over `src/` and requirements returns nothing; spaCy
appears only under `scripts/research/`. `ovr.news/src/lib/db-schema.ts:385`
creates an `entities` table plus two indexes with **no writer and no reader** —
the same present-configured-unreachable shape as NM#284 and NM#300.

**Careful: two different sets of five.** The diagram's five are *consumers of
NM#232* (NM#223, NM#185, ovr#222, ovr#223, the matching model). The trap below
lists *citers of the closed FS#85* (NM#223, ovr#222, ovr#223, ovr#231, ovr#232).
**ovr#231 and ovr#232 are FS#85 citers but not NM#232 consumers**, which is why
they appear in one list and not the other.

**Two traps recorded here.** (1) **NM#223, ovr#222, ovr#223, ovr#231 and ovr#232
all name `FluxusSource#85` as their prerequisite and it is CLOSED**, so a reader
concludes they are unblocked. This is the inverse of this board's "✅ while open"
finding: there a link looked done and was not; here a blocker looks cleared and
is not. Both come from reading an issue's *state* instead of its *deliverable*.
Correcting comments filed on all five, 2026-08-07. (2) **NM#232's consumer list
is not the inventory of consumers.** The story-dedup matching model is the only
consumer with code, a trained model and a readout, and NM#232 does not mention
it — so prioritising NM#232 off its own list prioritises it wrong. Note the
numbering: **NM#213 is CLOSED**; the live thread is NM#188 and NM#301 (Chain 10's
root). A full plan written off NM#232's list was refuted by a six-lens review the
same day — see [[corroboration-feature-hypotheses]].

**Recommendation on file (NM#232 comment, 2026-08-07): do not build as
specified.** The highest-value consumer wants an *offline re-run with a
cross-lingual extractor*, not a CPU pipeline stage. Cross-references Chain 10
(corroboration precision) and Chain 14 (any entity work must be
per-language-pair aware).

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
