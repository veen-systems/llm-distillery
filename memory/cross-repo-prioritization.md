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

**Owner, 2026-09-29: $100 of Claude Code cloud budget; which part of the backlog can be fixed from there?**
⚠️ A SNAPSHOT: issue sets from the `gh` loop at **2026-09-29 08:31 +02:00** (≈410 open, 6 repos),
triaged mostly **from titles** — read each issue before dispatching it. Two rows spot-checked in code
(LD#145 `prepare_data.py:183` still an unweighted mean; LD#144 `train.py:1116` still strict `<`).

**What a cloud session cannot reach** (docs, via claude-code-guide, 2026-09-29 — code.claude.com
`claude-code-on-the-web`, `costs`): Anthropic-managed VM, GitHub repos only (several per session; private
via the GitHub App), push + PR yes, network default *Trusted* allowlist. **Not documented, so assume NO:
Tailscale, SSH to sadalsuud/gpu-server/b650, any GPU.** Measured from this checkout: `datasets/*`,
`data/`, `filters/**/model/` are gitignored — **no oracle-scored data, no training splits, no student
weights** in a clone (probe `.pkl`s are tracked). Also missing in cloud: the USER-GLOBAL skills
(`/review-changes`, `/curate`, `/audit-context`) and the auto-memory `feedback-*` rules in `~/.claude` —
a cloud session reads `CLAUDE.md` and repo `memory/` only.

**So the working rule decides the split: a cloud session can prove the PREDICATE (a test), almost never
the OUTCOME** (a production cycle, a flip count, a recall figure). Three classes:

| class | what it means | ship as |
|---|---|---|
| **C — closes in cloud** | inputs in git, done = a test or a static check | PR; merge after a local read |
| **D — draft in cloud, prove locally** | the code change is self-contained, the outcome needs a cycle or data | PR + an outcome line written into the PR body; the local session runs it |
| **L — local only** | GPU, oracle spend, production data, a deploy, or an owner ruling | not dispatched |

**C — candidates (read the issue first):**
- **llm-distillery**: #162 (registry test writes into the tracked registry), #144 (checkpoint ties),
  #146 (EmbeddingStage cache key lacks device), #115 (merge-script date sort), #136 (commit-msg guard
  can't read negation), #134 (refcheck skips `docs/`), #160 (ADR-013 Dutch-name sweep), #140 (two stale
  guides), #117 (license NOASSERTION), #118 (dependabot half only — the lockfile half needs the prod
  venv, #81). TODO item 2 (cd v5 `raw_min` 4.0006 vs 4.0) if the answer is "record the tolerance".
- **FluxusSource**: FS#240 (caption becomes summary), FS#239 (tag twins), FS#243 (comments feed picked),
  FS#200 (notes silently replaced), FS#179 (CEST → LMT offset), FS#198 (two ticked-but-absent tests),
  FS#168 (requests charset), FS#170 (mojibake conjunction detector — detector only, never a repair run).
- **ovr.news**: ovr#354 (mobile nav), ovr#320 (`startsWith` on compound names), ovr#297 (size-suffixed
  logos), ovr#289 (COALESCE vs `'{}'`), ovr#243 (safeId allowlist), ovr#362 (voice-ab REGISTER_CURRENT),
  ovr#369 (Gemini fallback docs), ovr#19 / ovr#63 / ovr#55 (tests + CI).
- **persuasion-scorer** doc/process rows: #23, #21, #18, #16, #11, #7.
- **pipeline-atlas**: #58 (SVG note wrap), #56, #12, #4, #85 (estate page deleted by render).

**D — draft in cloud, prove locally:** LD#145 (weighted overall_score — changes every future training
split; needs an owner nod), LD#165 / NM#556 (detector manifest + sha256 — weights live on the Hub, needs
an HF token in the cloud env), **TODO item 1b (execute decision 0: delete per-lens prefilters)** — the
deletion is repo-local, the "batch_scorer passes the rows it used to drop" proof needs data. NexusMind
code bugs with a production outcome: NM#506, NM#524, NM#526, NM#472, NM#525, NM#532, NM#487, NM#466,
NM#465, NM#459, NM#399, NM#355, NM#352, NM#350, NM#344, NM#362, NM#302, NM#518. ovr.news: ovr#376,
ovr#342, ovr#341, ovr#361. ⛔ Anything that syncs into NexusMind still goes through the diff-first rule
(`deploy_to_nexusmind.sh --dry-run`) locally.

**L — never dispatch:** training/seeds (LD#85, #71, #98, #100, #158, #104), oracle spend (LD#156 adverse
pool, #124, persuasion #4), production reads (LD#141, #128, #135, #147, #153, harm hand check), owner
rulings (LD#130, #159, #116, H-HD17), deploys/cutovers (LD#151, NM#395), and **FS source-health rows
(FS#232, NM#509/#510)** — a cloud VM's IP is a different fetcher, so its 403s answer a different question.
LD#163 (the read surface) is text-only and fits the VM, but its method needs `/curate`'s rules and the
owner's keep-rule calls — pair it, don't dispatch it.

**Budget — nothing here is measured yet.** Cloud usage is metered like any Claude usage (`/usage` in the
session); the docs give no per-session figure. ⚠️ GUESS, not measured: a C-class fix with tests is a few
dollars, so $100 is on the order of 15–30 C rows. **First step: dispatch 2–3 C rows, read `/usage` per
session, then set the pace from those numbers** — and record them here with the date.

**Pilot 1 — #162 → PR #166 (2026-09-29). ⛔ NOT A CLOUD RUN.** Launched with `claude --cloud`, but a
`claude --teleport <session>` process started ~08:37 (pid 20998, `ps` etime) and the work ran in the
LOCAL main checkout (reflog: checkout to the fix branch 09:18, commit 09:25, back to `main` 09:26 — the
checkout another session was using). So the cloud environment (setup script, allowlist, no secrets) is
still **untested**; only the model cost carries over. ⛔ **Never run the `--teleport` line `--cloud`
prints** — it pulls the session onto this machine. Review (`/review-changes`, 4 lenses incl. reachability +
claim-verification): **0 blockers, 3 warnings**; the code held under 5 mutations re-run locally. Cost
(`/usage` in the cloud session, owner-pasted): **$2.13** — Opus 5.5, 17.9k output, 3.7M cache-read tokens,
3m21s API time over 3h44m wall (idle ~3h after the PR, which matches PR creation 09:25). ⚠️ `$` is the
API-equivalent figure; the same panel shows plan-limit bars (session 14%, week 22%), so whether this
drew on the $100 credit or on the subscription is **not established** — check the billing page.
The local `/review-changes` (4 subagents) is extra and was not metered here. On this one sample,
$100 ≈ 45 fixes of #162's size — one sample, a small and well-specified issue. ⚠️ **A fresh clone is NOT the local baseline**: measured on a clean
`origin/main` worktree (`9d7304e`, `.venv/bin/python -m pytest tests/ -q`) — **18 failed, 48 skipped**
vs the profile's 25 skipped. All 18 fail identically on `main` itself: missing gitignored API keys
(`secrets.ini`) and detector model files (`test_scorer_run_fatal` 7, `test_preflight_deploy_guards` 6,
`test_harm_detector_contract` 3, `test_deepseek_model_guard` 2). **Put this baseline in every cloud
prompt**, or a session either "fixes" environmental failures or reports a suite count it cannot have
produced — PR #166's `1104 passed, 25 skipped` came from the local tree (keys and models present), not the branch.

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

## Priority Rankings

### P0 — Now

| ID | Repo | Title | Why P0 |
|----|------|-------|--------|
| **(carryover)** | NexusMind | Verify the post-14:04 cycle: 4 first-time-in-production checks | NM#281's corrected gate has never been observed live. `gpu-server-unpinned` = LD#80 regression. |
| ~~NM#285~~ | NexusMind | ~~Shadow measures a truncated Article~~ | **RESOLVED 2026-08-02** — Option B shipped (`89f2e5b`). Truncation ≤0.01; no longer blocks LD#86/#87/#90. |
| **NEW: length floor → cap** | both | Split `MIN_CONTENT_LENGTH` out of per-filter prefilters into a cap/penalty (ADR-022 shape) | Replaces NM#285 as Chain 4's root. Blocks every NM#284 enforce flip: for 4 of 6 filters "enforce the prefilter" is 87–100% "enforce a length floor". |
| **LD#91** | llm-distillery | uplifting ranks child-trafficking investigation top-6 of 3,530 | Reputational, reader-visible, live. Scorer fidelity, not threshold. |
| **LD#92** | llm-distillery | ~~uplifting~~ **solutions** over-scores sub-300-char stubs | **CORRECTED 2026-08-02 at n=60/group.** uplifting does NOT replicate (DiD +0.44; P(original result from n=15)=0.0000). The effect is in **solutions v6** (DiD −1.13 [−1.74,−0.52], MAE 1.51×), ~49 FPs/8 cycles — not 460. Root cause of the original: op-point mix-up (2.25 is solutions', uplifting's is 4.0). Retitle/relocate. |
| **LD#95** | llm-distillery | Inference scores depend on batch composition (max \|Δ\| 0.162) | **Same shape that made NM#285 a P0: it gates the validity of decisions queued behind it.** Measured to flip 7.1% / 9.1% of near-boundary articles. Every op-point flip, cap fit, refit and ADR-021 gate on this board compares this quantity. ~~Pinning the production batch size is cheap.~~ **SETTLED 08-06 — pinning was never available**: `DEFAULT_BATCH_SIZE` is already 16 and the variable is *composition*. Shipped instead: seeded replay (`f7fef85`) and the floor as a **band the deploy gate prints**. |
| **ovr#284** | ovr.news | Comscore beacon as hero image | **Record DISCHARGED 2026-08-05**; control shape decided 08-07 (deny-list shipped, off-domain host stamped not blocked, allowlist declined). **Live remainder: recover the exposure window** — the one UNKNOWN that could reopen the Art. 33 conclusion. |
| ~~**ovr#285**~~ | ovr.news | ~~Orphan reclamation NULLs raw_weighted_average + source_quality~~ | **CLOSED 2026-08-03.** ovr#283 (publication floor) is unblocked and is now an owner decision. |

### P1 — This week

| ID | Repo | Title | Why P1 |
|----|------|-------|--------|
| **NM#286** | NexusMind | ADR-022 gaps (commerce enforce key, consumer-side drop, violence run-modes) | Items 1+2 must move together; item 3 blocks Chain 2. |
| **ovr#277** | ovr.news | editorial_decisions destructive on re-gate | Prerequisite for the whole of Chain 7. |
| **LD#82** | llm-distillery | violence v1 shadow audit | Defines what `enforce: false` is waiting on. |
| **FS#120** | FluxusSource | #119 eval readout + ADR-007 gate | **Hard date ~2026-08-14.** Dependency now shipped. |
| **ovr#280 → NM#278** | both | cluster_id ingestion, then dedup retune | Reader-reported: 5 articles = ~10% of a 52-article lens. |
| **ovr#281** | ovr.news | Stock heroes on ~10% of articles | Measured, decomposed, fixable in two independent halves. |
| **ovr#204** | ovr.news | Remove hardcoded obituary detection | Chain 1's last link; upstream verified. |
| **ovr#262** | ovr.news | Data archiving lossy & unreliable | Irreplaceable editorial signal lost forever. |
| **NM#244** | NexusMind | gpu-server 422s drop whole chunks, reason not logged | Silent data loss in scoring. |
| ~~**NM#290**~~ | NexusMind | ~~Hero extractor still picks third-party chrome post-#288~~ | **CLOSED 2026-08-03.** The *class* outlived it — see Chain 9: NM#294, ovr#295, ovr#297. |
| **ovr#287** | ovr.news | Backfill wrong-story heroes | **DECIDED 08-07: BLANK**, scoped per row to what is still buildable (6 today, incl. one at normalized 9.10 that a per-pattern flag had missed). The `image_source` stamp blocked a DB-wide re-fetch, not blanking known ids → **ovr#305**. Open until the R2 round-trip runs. |
| **NM#291** | NexusMind | Cross-source dedup threshold 0.88 vs measured 0.836 | Unblocks NM#278 with a measured number instead of a guess. |
| **NM#289** | NexusMind | Medium fixture scores into high on the three percentile filters | Possible upper-tail counterpart to the Chain 3 crush; if the CDFs are stale this is an llm-distillery refit, not a NexusMind fix. Check refit dates first — cheap. |
| ~~**FS#124**~~ | FluxusSource | UTF-8→MacRoman mojibake | **FIXED `ea25ae8`, verified not assumed**: 0.60–2.38%/run before, **0.00%** on the first run after. ⚠️ **The "0.78/run since, residual ~5/day is publisher-caused" claim is WITHDRAWN 2026-08-12 — that residual was 100% FALSE POSITIVES (FS#167), and the genuine residual is 0.** `’` is `0xD5` in MacRoman, a valid UTF-8 lead byte, so `l’é` / `c’è` forms a valid 2-byte sequence and the detector "repairs" correct French and Italian into Armenian (`l’éclipse` → `lՎclipse`). **Note the shape: the artefact was load-bearing** — it was the reason to believe a live collection-stage effect survived `ea25ae8`, which is part of why #124 stayed plausible as a #292 stage. An instrument's bias did not merely add noise; it kept a stage alive. Independently corroborated from our side: over 302,592 rows the defect fires **730 times, en 24 (0.012%) vs non-en 706 (0.67%) — 55×** — and **every hit is between 2026-07-29 and 2026-08-03, zero after**, matching FluxusSource's deploy boundary from a different instrument in a different repo. So #124 was real and strongly non-English-specific *while live*, and is now historical. ⚠️ **RETRACTED SAME DAY (2026-08-12): the collection stage is NOT historical and FS#166 does NOT replace it.** The defect **RELOCATED into NexusMind's enricher** — **NM#338**. `article_fetcher.py:291` does `.decode(resp.encoding or "utf-8")`, and `requests` gives a charset-less `text/*` response `ISO-8859-1`, **not `None`**, so the guard is dead code. Corrected measurement (120 files, 20 per lens, 08-10→08-12, peer-sourced from the NexusMind session): **1,466 / 25,996 = 5.639% introduced by enrichment**, English **1.341%** vs non-English **9.202%** — **6.86×**; by codec arm cp1252 1,210 / mac_roman 256. ⚠️ **And FluxusSource is NOT at 0.000%** — that figure came from a detector blind to cp1252 smart quotes (83% of the population); corrected it is **21 / 25,996 = 0.081%**. **So: FS#124's fix holds and the limb is live again at a different stage, in a different repo.** FS#166 (source acquisition) stands entirely on its own and is a *separate* collection-stage fact, not a replacement. Chain 14's root is **NM#292**. 🛑 **ovr#291 (repair ~474 stored rows) IS NOT SAFE TO RUN WITH THIS DETECTOR** — ours is warn-only so a false positive costs a wrong line in a report, but a *repair pass* silently and irreversibly converts correct French and Italian into Armenian codepoints. ✅ **SUPERSEDED 2026-08-13 — the repair question is MOOT.** Owner: *repairment should not be necessary; if it is, there are bugs upstream.* **ovr#291 is now RE-DERIVE FROM UPSTREAM, not repair.** A repairer needs a detector, a detector must *guess*, and the guess is the only reason FS#167's 2,030 false-positive pairs ever mattered. A clean copy of every row sits one hop upstream (`original_content`, 0.000% through a three-round challenge), so **nothing need be inferred and there is no false-positive class at all.** Two conditions, both measured: **NM#338 is fixed** (raw bytes to trafilatura), so the corrupted set is bounded and the job terminates rather than becoming a treadmill; and **U+FFFD — the one irreversibly-lossy class, which re-derivation ALONE can cure** — is **4 of 21,316 rows, 0 of 160 cache rows**. The old repairer spec survives as the **verification** spec, where a false positive costs a second look instead of a destroyed row. ⚠️ **Everything below is retained as HISTORY** — the reasoning recurs, and the record of what a guess would have required is worth keeping. ⚠️ **DATE-SCOPING IS NOT A SUFFICIENT MITIGATION — I wrote that here first and it is wrong.** Measured by the ovr.news session over their 21,174 rows: **449 flagged, 7 of them the false-positive class** (`l’âme`, `cos’è`, `l’Égypte`, `l’étang`), and **all 7 pre-date the 2026-08-03 cutoff** — so a date-scoped repair would still have destroyed every one of them. **Only the pattern exclusion saves them — and NO VALIDATED EXCLUSION EXISTS YET, so ovr#291 CANNOT BE SAFELY RUN AT ALL TODAY.** ⚠️ **A round-trip confirmation does NOT fix this, and I claimed it would — wrongly, about a destructive operation.** Verified here 2026-08-12, 5 of 5 cases survive: `'l’éclipse solaire'.encode('mac_roman').decode('utf-8')` → `'lՎclipse solaire'` — **different, valid, and wrong**. Also `cos’è`→`cosՏ`, `l’âme`→`lՉme`, `l’Égypte`→`lՃgypte`, `121\xa0°C`→`121ʡC`. **The round-trip IS the operation that produces the false positives**, so it cannot detect them; that is why FS#167 is open rather than solved. **What actually makes a detector safe is the CONJUNCTION: an unambiguous signature (candidate generation on marker classes — `Ã â √ ‚ ¬`, which `’` is not in) AND a clean inversion, then hand-review the residue.** NexusMind's detector is safe because of its *candidate* stage, not its round-trip stage — and getting that backwards is what would license the destructive run. Do not route "round-trip makes it safe" anywhere without this distinction attached. FS#167 is **open, not pending**: the obvious guard (reject repairs introducing a foreign script) scores 6/8 and fails both ways — rejects genuine emoji repairs on the variation selector, and *accepts* `121\xa0°C` → `121ʡC` because U+02A1 is Latin by name and category. The class is also far wider than first recorded: not apostrophe-elision but **2,030 firing pairs** (48 UTF-8 lead chars × 64 continuations — `«` `»` `—` `“` `…` `€` `√` and NBSP as leads; accented vowels plus `°` `µ` `©` `™` `≤` as continuations), i.e. European typography *and* scientific units. Date-scoping remains useful for *reducing blast radius* (448 before the cutoff vs 1 after) but must never be the only guard. Current state: **ovr#291 is OPEN with no repair script written, so nothing has been destroyed.** The single post-cutoff row is a `RaÃºl` in a Times of India row collected 08-07 and may be publisher-origin rather than a leak in `ea25ae8` — not to be treated as a counterexample without checking the feed. |

### P2 — This month

| ID | Repo | Title |
|----|------|-------|
| **LD#86 / LD#87 / LD#90** | llm-distillery | cd prefilter enforce → cd v6 op-point → lens harmonization. ~~all downstream of NM#285~~ — **NM#285 RESOLVED 08-02**; #87 was unblocked 08-06 by the #95 band decision. |
| **ovr#235 → ovr#270** | ovr.news | Held-out gate, then summarizer swap (behind ovr#277) |
| **ovr#286** | ovr.news | Backfill 397 metadata-absence summaries |
| **ovr#276** | ovr.news | Editorial gate no longer byte-identical at temp=0 |
| **NM#231** | NexusMind | uplifting under-scores non-English documented-outcome news (sibling of LD#91) |
| **LD#61** | llm-distillery | Cross-filter trajectory-framing mis-lensing (sibling of LD#91) |
| ~~**ovr#283**~~ | ovr.news | **CLOSED won't-do 2026-08-07** — no stored row is below raw 4.03, so a floor binds nothing, and the monitoring alternative is mis-specified against its own motivating case. Reopened one level down as **ovr#304**. |
| ~~**FS#121**~~ | FluxusSource | ~~fda/patent aggregators never run~~ — **CLOSED 08-03.** Generalized by **FS#126**: nothing alarms on a zero-yielding aggregator, so FS#121, FS#125 and FS#128 are three instances of one missing check. |
| **LD#84** | llm-distillery | solutions oracle prompt router self-contradictory |
| **LD#94** | llm-distillery | solutions v6 `concreteness_gatekeeper` inert — 0 binds in 191,616 articles (benign NM#284 shape: a config key that declares an enforcement point with no runtime effect). Recommend remove-or-document; raising the threshold is a real behavior change needing an ADR-021 recall check. **Run the same two-condition count on `nature_recovery v4`'s `recovery_evidence`** — the redundancy argument generalizes. |
| **LD#81** | llm-distillery | Align sklearn across training + inference |
| **LD#89** | llm-distillery | Share frozen-mpnet embed pass between obituary + violence |
| **LD#23 / LD#70 / LD#71** | llm-distillery | cd evidence_quality; nr protection scope; nr v5 recall |
| **ovr#214 / ovr#255 / ovr#256** | ovr.news | Language leak; academic stock photos; US-centric abbreviations |
| **NM#221 / ~~NM#220~~ / NM#96** | NexusMind | GPU multi-tenancy, ~~Ollama coexistence~~, sustainable hosting — **NM#220 CLOSED/COMPLETED 2026-07-07, verified 2026-08-07** |

### P3 — Backlog

LD#52, LD#66, LD#48, LD#88 (hygiene batch), NM#196, NM#82, NM#23, NM#185,
NM#187, NM#188, NM#170, ovr#63, ovr#55, ovr#19, ovr#278 (safe-fetch defence in
depth), FS#105 (systemd units — **ovr#254, the other half, closed 08-03 14:01**),
FS#11, FS#103, FS#107, FS#114, FS#122.

**FS#122 is a closed question, not an open task.** It began as an "economy lens"
proposal for ovr.news and the measurement answered it: `solutions v6` already
surfaces cooperative/commons/ownership material at **6× the corpus rate**
(29.8% ≥ op-point vs 4.9%) — there is simply almost none of it (104 strict
matches in 191,616, 0.054%). **The gap is source selection, not scoring, so no
new lens is warranted** — this belongs with FluxusSource source acquisition, and
it should be cited before anyone re-proposes an economy lens (cf. LD#40).

### P4 — Future

LD#38, LD#40, LD#24, LD#78, LD#79, ovr#232, ovr#223, ovr#211, ovr#213,
ovr#242, ovr#133, FS#19, plus the ovr non-engineering track.

**That track is now 25 issues, and it is no longer the `#137–#160` range** the
previous pass described — it has grown a second cluster at `#216–#221` (NLnet
future round, HAN student outreach). Full list, re-run 2026-08-03:
`61 137 138 139 140 143 145 146 147 150 151 152 153 154 157 158 159 160 216
217 218 219 220 221 255`. **Caveat: `ovr#255` is in that list only because it
carries the `content` label — it is a real hero-image bug and is banded at P2.**
So the label filter over-counts by one: **24 non-engineering, 56 engineering.**

## Coverage — what this memo does *not* band

Stated explicitly so the priority tables are not mistaken for full coverage.
**57 of the 177 open issues appear in no chain and no P0–P4 band**, of which
~37 are engineering:

| repo | unbanded | numbers |
|---|---|---|
| llm-distillery | 9 | 25, 28, 30, 33, 42, 55, 56, 60, 64 |
| NexusMind | 4 | 104, 228, 229, 251 — *225 → Chain 15 and 226 → Chain 13, 2026-08-07 night. **This row is independently stale**: it omits 232, 223 and 254, while the same-day coverage pass says **11** NexusMind issues are uncovered — two different definitions, never reconciled.* |
| ovr.news | 42 (20 of them non-engineering) | engineering: 41, 59, 68, 115, 177, 180, 207, 210, 224, 228, 229, 230, 233, 234, 239, 243, 245, 247, 248, 263, 265, 271 |
| FluxusSource | 0 | — |
| **persuasion-scorer** | **12 → 0** | **This row did not exist until 2026-08-07 and the omission was the point: all 12 were counted in every total and banded nowhere. Now [Chain 16](#chain-16-persuasion-scorer-verification-track--new-2026-08-07-was-never-banded).** |

**Also mentioned somewhere on this board but placed in no chain and no band
(checked 2026-08-07):** ovr#301 (Chain 7 material — the re-summarisation test
that picks between the two #29x candidates), FS#127, FS#132.

This is sediment, not a hidden backlog — most predates the current chains. Two
are worth a second look, though, because they are *methodology* items the last
month has independently re-derived: **NM#229** (agreement-gate for scorer
retrains, catching K-shape over-demotion before deploy) and **ovr#234**
(schema-constrained gate output with per-finding confidence). Both were filed
2026-06-04 from the vmodel pattern; Chain 13 is now arguing for that same kind
of gate from measurement rather than from principle. Their sibling **ovr#235**
is already banded, in Chain 7.

## Sequenced Work Batches

### Batch A — status after 2026-08-02
1. ~~Verify the post-14:04 cycle~~ **DONE — all 4 checks PASS.**
2. ~~NM#285 measurement + Option C decision~~ **DONE — Option B shipped (`89f2e5b`); C declined on the measurement.**
3. ~~NM#286 items 1+2~~ **DONE (`23a9068`, on main).** Item 3 still open, still blocks any violence flip.
4. **LD#82** violence audit — next, with NM#286 item 3.
5. **NEW ROOT: length floor → cap/penalty.** LD#93 steps 1-3 shipped (`4d17e75`)
   and are synced; **step 4 (fit the solutions cap) is blocked on LD#92's
   second-op-point re-run AND now on Batch F.1** — it is a threshold fit, so it
   inherits LD#95's noise. Step 5 (re-run the NM#284 shadow) needs the sync
   verified in a cycle. Blocks LD#86/#87/#90.
6. **Verify next cycle** after `89f2e5b`: shadow lines carry `contract=title+content` + `pre_source_filter=true`, four filters show `INCOMPLETE(inert:…)`, and nature_recovery/solutions log **no** `declared=` (key deleted).

### Batch B — Reader-visible quality (can run in parallel with A)
1. **LD#91** — uplifting dominant-subject failure. Read alongside LD#61 and NM#231; likely one shared mechanism.
2. ~~ovr#285~~ **CLOSED 08-03** → **ovr#283** decision is unblocked and is the owner's.
3. **ovr#280** ingestion fix → **NM#278** retune, now with **NM#291**'s measured 0.836. *(Sequencing: complete-linkage via NM#228 first — see the 08-04 section.)*
4. **ovr#281** — stock heroes (two independent halves: stickiness, validate false-rejects).
5. **ovr#204** — remove hardcoded obituary filter.
6. ~~NM#290~~ **CLOSED 08-03** → replaced by **NM#294** (~79% of heroes unvalidated) and **ovr#295 / ovr#297** (publisher logos via the upstream-supplied path).
7. ~~**ovr#287** — hero backfill, after the `image_source` stamp is disambiguated.~~ **DONE differently 2026-08-07:** the stamp was a blocker for a DB-wide re-fetch, not for blanking known ids. Blanking targets by URL pattern; the stamp ambiguity went to **ovr#305**.

### Batch C — Legal / compliance — **grew 08-04/08-05**
> **Mostly CLOSED as of 2026-08-07.** Items 2-5 are all closed issues; the
> batch's framing ("sequence it before anything that fits a distribution")
> is void. Only 1, 6 and 7 carry live work.

1. **ovr#284** — record DISCHARGED 2026-08-05; control shape decided 08-07 (deny-list shipped, off-domain host stamped not blocked). **Live remainder: recover the exposure window**, the one UNKNOWN that could reopen the Art. 33 conclusion.
2. ~~**ovr#292** TDM opt-out sweep~~ — **CLOSED 2026-08-05, ADR-043: the directives do not bind our fetcher.** Live remainder is operational, not policy: **schedule the scan** (it has run once) and **fix the 117 fail-open errors** — a publisher behind a WAF that 403s non-browser agents is the one most likely to be reserving.
3. ~~**LD#28** TDM for training data~~ — **CLOSED 2026-08-05**, its own record rather than inheriting ovr#292's. See **LD#97** for the already-trained-models half.
4. ~~**ovr#293** AI Act art. 50~~ — **CLOSED 2026-08-06.**
5. ~~**ovr#294** unassessed obligations~~ — **CLOSED 2026-08-06.**
6. **ovr#274** — full threat-surface security review (standing).
7. **ovr#278** — safe-fetch defence-in-depth leftovers.

Batch C was three code-adjacent items; it is now the only batch on the board
whose head item (ovr#292) is a **policy decision with a corpus-wide consequence**
— 333 domains is 24.5% of sources, and dropping them changes what every lens
downstream can see. Sequence it before anything that fits a distribution.

### Batch D — Deadline track
1. **FS#120** — eval readout, ADR-007 gate, **~2026-08-14**. Start the readout script well before the date; ovr#275's attribution export is live.
2. Close **ovr#275** after the ~Aug 2 backlog washout check.

### Batch E — Summarizer (strictly sequenced)
1. **ovr#277** (non-destructive re-gate) → 2. **ovr#276** (determinism) → 3. **ovr#235** (gate) → 4. **ovr#270** (swap) → 5. **ovr#286** (backfill).

### Batch F — Measurement trust (NEW 08-03; **precedes any threshold decision**)
Listed last but sequenced first: Batch A.5 and every Chain 4 enforce flip depend
on it.
1. ~~**LD#95** — pin the batch size~~ **SETTLED 2026-08-06: the second half only.**
   Pinning was never available — `DEFAULT_BATCH_SIZE` is already fixed at 16
   and the variable is batch *composition*. The floor is now a **band the
   deploy gate prints** (`--noise-floor`, default 0.16), and two models whose
   bands overlap are NOT DISTINGUISHABLE. This is what unblocked #87 and #93
   step 4.
2. **NM#289** — check the three percentile CDFs' refit dates against current
   production raw percentiles. Cheap; may reopen Chain 3 at the upper tail.
3. **LD#94** — remove or document the inert gatekeeper, and run the same
   two-condition count on `nature_recovery v4`.
4. Only then: **LD#93 step 4** (fit the solutions short-content cap) and any
   Chain 4 enforce flip. Both are threshold fits that inherit LD#95's noise.
5. **NEW 08-05 — Chain 15's missing count:** what share of lens placements is
   decided by a margin smaller than **0.16**? Already known: 16.1% of published
   articles are scored by 2+ filters and 52.6% of those are placed under a 0.5
   margin (ovr.news hypothesis log). The sub-0.16 slice is the part that is not
   measured, and it is the part that distinguishes a close call from a coin flip.
   ovr#296's tie-break epsilon is where it belongs. Same family as items 1–3: it
   says whether a comparison means anything before anyone acts on one.

## Housekeeping (opportunistic)

- Delete retired sustech/foresight dirs (post-drain — due now).
- Sync `score_normalization.py` (44-line divergence LD ↔ NM).
- ~~LD#49~~ / LD#48 — remove superseded filter versions; normalize Hub naming. **LD#49 CLOSED/COMPLETED 2026-07-27** (verified 2026-08-07); LD#48 still open.
- FS#105 — version systemd units in-repo (ovr#254, its twin, **closed 08-03**).
- ~~NM#91 sadalsuud healthcheck drift~~ — **CLOSED/COMPLETED 2026-03-06, and the description was wrong**: NM#91 is *"Pipeline-run summary notification on success (not just failure)"*, nothing to do with healthcheck drift (verified 2026-08-07). If healthcheck drift is still a live operator concern it has no issue.

## Standing Operator Decisions (Jeroen's call)

> **CLEARED 2026-08-07 — every item that was open here has been decided.**
> This section is the one an operator reads as the live to-do list, and it had
> drifted furthest: it still listed all six of the 08-07 decisions as open, two
> of them (ovr#283, ovr#292/LD#28) against issues already CLOSED on GitHub, and
> ovr#283 twice. See *Ordering 2026-08-07* in [`archive/cross-repo-prioritization-archive.md`](archive/cross-repo-prioritization-archive.md).
> **All seven are now taken.** Item 7 was created by this session's own review and closed the same day.

- ~~**7. ovr.news's own corroboration boost**~~ — **DECIDED + SHIPPED
  2026-08-07** (`1ecf853`): **bounded to a flat 1.3× for 2–10 total sources,
  1.0× above**, matching NexusMind's shape in `1bbadb5`. The ladder was removed
  rather than retuned because precision is **not monotone** in cluster size and
  no band beats the 2-source case (0.560). Subtractive by construction.
  ovr.news `under-the-hood/ranking.astro` updated in the same commit — and while there,
  **a separate published defect**: decay published as **0.95** against a
  configured **0.85** (0.70 vs 0.32 at 7 days), so the worked table understated
  decay roughly twofold. ovr#303 closed. **Still open in the hypothesis log:
  whether the remaining 1.3× is earned at all — decidable ~2026-08-18**, once
  the TTL drains the oversized clusters and precision can be measured on the
  *capped* system.
- ~~NM#285 Option C~~ — DECLINED 2026-08-02 on the measurement (Option B shipped). Reopen only if prefilters regain lens rules worth enforcing.
- ~~**ovr#283** publication floor~~ — **CLOSED won't-do 2026-08-07.** Listed twice here; both are dead.
- ~~**ovr#284** who writes the Art. 5(2) record~~ — **stale when written**; the record was authored 2026-08-05. The live decision was the control shape, taken 08-07: deny-list, stamp not block, no allowlist.
- ~~**ovr#292 / LD#28** do the 333 domains bind us~~ — **DECIDED 2026-08-05, ADR-043: they do not.** Both issues CLOSED. The 08-07 follow-on (disclose on `/accountability`?) was answered **no**.
- ~~**ovr#287** re-extract or blank~~ — **BLANK, 2026-08-07**, scoped to rows still inside the build window.
- ~~**LD#95** pin the production batch size~~ — **not available and superseded.** Batch size is already fixed at 16; the variable is *composition*. Settled 08-06: the floor became a band the deploy gate prints, and two models whose bands overlap are not distinguishable.
- ~~**Chain 14** run the common-denominator comparison, or close won't-do~~ — **NEITHER, 2026-08-07:** NM#292 stays open and is retargeted as the index plus the cross-cutting constraint list; the aggregate measurement is dropped.
- **LD#85** obituary v6 relabel — PARKED; reactivate on obit-flag or over-block harm.
- ~~NM#91 healthcheck drift~~ (closed 2026-03-06, and mis-described — see above); uplifting v7 NO_HUB backup; cd v5 config-schema exemptions.
- FluxusSource: 71 DEAD disable candidates; OVER_POLLED audit; global-broadening yield check.

## Related Memories

- [[project_session_2026_08_05]] — LD#92 identified, GN evidence into FS#120, ovr#299 filed
- [[project_session_2026_08_03]] — LD#93 ship + sync, LD#95, the three upstream defects
- [[project_session_2026_08_01]] — the session the prior update followed
- [[project_session_2026_07_31]] — Chain 3 deploys
- [[project-obituary-detector]] — Chain 1 details
- [[filter-status]] — per-filter MAE/status
- [[calibration-history]] — Dead Ends (read before calibration/scorer work)
