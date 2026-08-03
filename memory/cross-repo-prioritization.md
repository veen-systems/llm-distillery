---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

**Last updated: 2026-08-03 16:35** — second pass the same day. The 16:25 curate
pass recorded the *narrative* correctly but left **nine issues from the last 22
hours unplaced** in the chains and priority tables: LD#94, LD#95, NM#289,
NM#290, NM#291, FS#122, FS#124, ovr#287, and ovr#254 (closed 14:01). All are
placed below; two new chains (13, 14) exist because of them.

(Earlier that day: Chain 4 root **#93 shipped, synced and deployed**; three
reader-reported defects filed upstream; ovr.news triaged.) Counts re-run
2026-08-03 — see below.

> The "Changes since the 2026-08-01 morning update" table below is a historical
> changelog — its NM#285 and LD#92 rows record what was believed on 08-01, and
> both were **overturned on 08-02**. Chain 4 and the P0 table are current.

Open, **re-counted 2026-08-03**: llm-distillery **36** · NexusMind **39**
(38 + NM#292, filed on this pass) · ovr.news **80** · FluxusSource **10** ·
persuasion-scorer **12** = **177**.
Repos: veen-systems/{llm-distillery,persuasion-scorer}, ducroq/{NexusMind,ovr.news,FluxusSource}.

> **The count is not the workload — 102 of these had not been touched in 30+ days.**
> Throughput is ~41 closed/month across the big three, so the *live* backlog is
> roughly 72 issues ≈ under two months. The rest is sediment, and it is what
> makes the tracker feel unmanageable.
>
> **ovr.news is a special case, triaged 2026-08-03: 24 of its 57 stale issues
> are not engineering at all** — Mastodon/LinkedIn accounts, Google News
> submission, NLnet grant rounds, conference attendance, student outreach. A
> go-to-market plan in a code tracker. All are now labelled
> `positioning`/`outreach`/`community`/`content`; the engineering view is
> `is:open is:issue -label:positioning -label:outreach -label:community -label:content`
> → **55, not 81**. Of the 33 remaining stale ones, 8 were checked against the
> code and 7 are genuinely unimplemented — so **closing them would be theatre**.
> Age is not a reason to close a true statement.

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

## Where we stand — one paragraph

Chain 3 (calibration/normalization) is **closed and verified live**. Chain 1
(obituary) has one cosmetic link left (ovr#204). Chain 8 (Google News) had both
FluxusSource links **close 07-31** and now hangs on a **calendar deadline
(FS#120, ~2026-08-14)** whose ovr-side dependency shipped. What replaced them is
a new cluster of **contract/plumbing defects found by adversarial review of the
same day's own work** — NM#284/#285/#286, ovr#277/#285 — all of the shape
"the mechanism exists, is configured, and cannot fire." Nothing in that cluster
is live-breaking today; **all of it gates decisions that are queued behind it.**
The one genuinely new *product* problem is **LD#91** (uplifting ranked a
child-trafficking investigation 6th of 3,530).

**Added on the 16:35 pass:** a second cluster of the same kind, but one level
down — **not "the mechanism cannot fire" but "the measurement cannot be
trusted."** LD#95 (batch composition flips 7–9% of near-boundary verdicts),
NM#289 (percentile CDFs inflating the upper-middle), LD#94 (a gatekeeper that
has never bound in 191,616 articles). Chain 13 collects them. They sit *under*
Chain 4's enforce flips and Chain 3's refits, which is why Batch F now precedes
the remaining threshold work. Separately, Chain 14 records a four-repo
non-English quality pattern that no single issue currently states.

## Changes since the 2026-08-01 morning update

| What | Now |
|------|-----|
| **Chain 3 (calibration)** | **CLOSED** — verified live; NM#279/#280, LD#74/#76 closed. |
| **Chain 8 (Google News)** | **FS#118 + FS#119 both CLOSED 07-31.** ovr#275's resolver shipped (`623cc82`) and its per-source attribution surface shipped (`8ab610a`), unblocking **FS#120 — the only calendar deadline on the board, ~2026-08-14.** |
| **NM#284 (prefilters never ran)** | Stage 1 shadow deployed + verified. **Now blocked by NM#285.** |
| **NM#285 (NEW — P0)** | Shadow measures a **truncated `Article`** (title+content only) — url/source/description rules can never fire, so every observed pass rate is biased high by an unknown per-filter amount. **Gates every NM#284 enforcement decision, therefore gates LD#86, LD#87, LD#90.** Recommendation on file: **Option C — run prefilters pipeline-side.** |
| **NM#286 (NEW — P1)** | ADR-022 gaps: commerce has no `enforce` key, a consumer-side commerce drop in `enrich_survivors.py`, violence stamping skipped in 3 run modes. Items 1+2 **must move together**; item 3 must land **before any violence enforce flip**. |
| **NM#281** | Deployed + same-day corrected (`b85a467`). **4 first-time-in-production checks still unverified** — see Batch A.1. |
| **LD#91 (NEW — P0)** | uplifting scored a child-trafficking investigation raw 6.77 = **99.9th pct of 3,530**; it led the homepage with a trafficking price list as pull quote. Not a threshold problem — the scorer rewards narrative fragments over dominant subject. Sibling of LD#61, NM#231. |
| **ovr#284 (NEW — P0, legal)** | Comscore beacon served as hero on 13 articles → visitor IP/UA sent to a third-party analytics vendor with no basis. Needs an **Art. 5(2) record**, not just a code fix. |
| **ovr#285 (NEW — P0)** | Orphan reclamation **NULLs `raw_weighted_average` + `source_quality` every cycle**. Proven with before/after rows. **Blocks the ovr#283 floor decision** — that decision would otherwise be taken on null data. |
| **ovr#277 (NEW — P1, sequencing)** | `editorial_decisions` PK lacks `prompt_version`, so re-gating **destroys the before-side of any before/after comparison**. **Prerequisite for ovr#235 and therefore for ovr#270.** Chain 7 was previously sequenced wrong. |
| **ovr#280 cluster_id** | Diagnosis **REFUTED** — cluster_id IS on the wire (7,629/16,128 rows). Break is **downstream in ovr.news ingestion**; NM#278 is the real fix for the reader-visible symptom. |
| **NM#206** | Was already CLOSED — dropped from all batches. |

## Cross-Repo Dependency Chains

`→` means "blocked on" or "feeds into."

### Chain 1: Obituary Detector — COMPLETE except one link
```
LD#51 ✅ → LD#77 ✅ → NM#185 ✅ → v4 ✅ → LD#83 (v5 + ENFORCE @0.85) ✅ → ovr#204 ← ONLY LINK LEFT
```
Enforcement live + verified (1,158 blocked). Carryover washes out ~Aug 2–6 by
window. LD#85 (v6 relabel) PARKED indefinitely by owner.

### Chain 2: Violence Promotion — shadow, enforcement gated
```
LD#73 ✅ → NM#274 ✅ → NM#281 gate wiring ✅ (inert) → LD#82 (audit) + NM#286 item 3 → enforce
```
**Two hard gates before any flip:** LD#82 (v1 recall 0.55 → enforcing gates ~half
of true positives) and NM#286 item 3 (violence stamping skipped in 3 run modes).

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
LD#43 ✅ → v4 ✅ → v6 (gate passed, normalized) ✅ → LD#84 (prompt router, v7 only) → NM#204 (closable as superseded)
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
   → NM#290 (STILL WRONG post-fix: no cross-domain check — allAfrica ships a Google Play badge)
   → ovr#287 (backfill ~36 already-stored wrong-story rows) ← DECISION NEEDED
```
ovr#281 measured: of 25 rescuable, 11 would succeed today (stickiness), 12 are
`validateImageUrl` false-rejects, 2 fetch failures. ~10% of articles affected.

**The NM#287 fix stops new bad rows; it does not repair stored ones** — 33 of 40
recent `vanguardngr.com` articles carry a sidebar-rendition image from a
different story, 67% of that publisher's last 60 days, ~36 rows DB-wide. ovr#287
needs an operator call: **re-extract** (correct hero, N fetches, some 404s) vs
**blank** (cheap, certain, loses ~36 heroes). NM#288's own principle — *a missing
image beats a confidently wrong one* — argues blanking is sufficient and
re-extraction is a bonus. **Blocker on targeting:** `image_source='og'` is
stamped on upstream-supplied *and* self-extracted rows, so the backfill cannot
currently tell them apart; fix that stamp first or the backfill re-fetches
everything.

### Chain 10: Dedup / Corroboration — **NEW; NM#291 gives NM#278 its number**
```
ovr#280 (ovr-side ingestion of cluster_id — data IS on the wire) → NM#278 (threshold retune for title-only E5)
   ← NM#291 (cross-source threshold 0.88 vs measured 0.836 for genuine cross-language same-story pairs)
   ↔ NM#188 / NM#170 / NM#215 / NM#275(closed)
```
Do the ovr ingestion fix first — it is cheap and the data already exists.
**Caution on NM#278:** NexusMind *removes* rather than *labels* (~32%/run);
anything removed upstream can never surface as an "N sources" badge.

**NM#291 is the measured input NM#278 was missing** — the retune is no longer a
"pick a number" task. Note the failure is *cross-language*: see Chain 14.

### Chain 11: Score Provenance / Publication Floor — **NEW**
```
ovr#285 (stop NULLing raw_weighted_average) → ovr#283 (floor: decide or close won't-do)
   ← informed by LD#91 (a floor would NOT have caught it — raw 6.77 is genuinely 99.9th pct)
```

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
   ↔ gotcha-log 2026-07-30 cross-box skew |0.16| — same magnitude, different cause
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
ADR-021 gate compare exactly this quantity. Cheapest mitigation is pinning the
production batch size — that does not remove the noise but makes a cycle
reproducible.

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
FS#124 (mojibake at collection, 5.0%, non-English-concentrated)
   → NM#231 (uplifting under-scores non-English documented-outcome news, 19 panel-confirmed)
   → NM#291 (dedup threshold misses cross-language same-story pairs at 0.836)
   → LD#86 (cd prefilter enforce would cost 19.9% non-English vs 13.0% English, p≈0.01)
   ↔ LD#93 (sub-300 population is dominated by gn_* / spanish_* / french_* / gn_africa_*)
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
type. Small gap → close won't-do and let the four proceed on their own merits;
large gap → pull FS#124 and NM#291 forward.

## Priority Rankings

### P0 — Now

| ID | Repo | Title | Why P0 |
|----|------|-------|--------|
| **(carryover)** | NexusMind | Verify the post-14:04 cycle: 4 first-time-in-production checks | NM#281's corrected gate has never been observed live. `gpu-server-unpinned` = LD#80 regression. |
| ~~NM#285~~ | NexusMind | ~~Shadow measures a truncated Article~~ | **RESOLVED 2026-08-02** — Option B shipped (`89f2e5b`). Truncation ≤0.01; no longer blocks LD#86/#87/#90. |
| **NEW: length floor → cap** | both | Split `MIN_CONTENT_LENGTH` out of per-filter prefilters into a cap/penalty (ADR-022 shape) | Replaces NM#285 as Chain 4's root. Blocks every NM#284 enforce flip: for 4 of 6 filters "enforce the prefilter" is 87–100% "enforce a length floor". |
| **LD#91** | llm-distillery | uplifting ranks child-trafficking investigation top-6 of 3,530 | Reputational, reader-visible, live. Scorer fidelity, not threshold. |
| **LD#92** | llm-distillery | ~~uplifting~~ **solutions** over-scores sub-300-char stubs | **CORRECTED 2026-08-02 at n=60/group.** uplifting does NOT replicate (DiD +0.44; P(original result from n=15)=0.0000). The effect is in **solutions v6** (DiD −1.13 [−1.74,−0.52], MAE 1.51×), ~49 FPs/8 cycles — not 460. Root cause of the original: op-point mix-up (2.25 is solutions', uplifting's is 4.0). Retitle/relocate. |
| **LD#95** | llm-distillery | Inference scores depend on batch composition (max \|Δ\| 0.162) | **Same shape that made NM#285 a P0: it gates the validity of decisions queued behind it.** Measured to flip 7.1% / 9.1% of near-boundary articles. Every op-point flip, cap fit, refit and ADR-021 gate on this board compares this quantity. Pinning the production batch size is cheap and buys reproducibility today. |
| **ovr#284** | ovr.news | Comscore beacon as hero image | Real processing-without-basis event; needs an Art. 5(2) record. Legal, not just code. |
| **ovr#285** | ovr.news | Orphan reclamation NULLs raw_weighted_average + source_quality | Silent per-cycle data loss; blocks ovr#283. |

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
| **NM#290** | NexusMind | Hero extractor still picks third-party chrome post-#288 | The fix shipped and the class survived it — no cross-domain check. Reader-visible. |
| **ovr#287** | ovr.news | Backfill ~36 wrong-story heroes | Reader-visible and *already stored*; needs an operator call (re-extract vs blank) and the `image_source` stamp fixed first. |
| **NM#291** | NexusMind | Cross-source dedup threshold 0.88 vs measured 0.836 | Unblocks NM#278 with a measured number instead of a guess. |
| **NM#289** | NexusMind | Medium fixture scores into high on the three percentile filters | Possible upper-tail counterpart to the Chain 3 crush; if the CDFs are stale this is an llm-distillery refit, not a NexusMind fix. Check refit dates first — cheap. |
| **FS#124** | FluxusSource | UTF-8→MacRoman mojibake, 5.0% of articles | Corrupts text *at collection*, so every downstream stage scores and dedups damaged input. Root of Chain 14. |

### P2 — This month

| ID | Repo | Title |
|----|------|-------|
| **LD#86 / LD#87 / LD#90** | llm-distillery | cd prefilter enforce → cd v6 op-point → lens harmonization (**all downstream of NM#285**) |
| **ovr#235 → ovr#270** | ovr.news | Held-out gate, then summarizer swap (behind ovr#277) |
| **ovr#286** | ovr.news | Backfill 397 metadata-absence summaries |
| **ovr#276** | ovr.news | Editorial gate no longer byte-identical at temp=0 |
| **NM#231** | NexusMind | uplifting under-scores non-English documented-outcome news (sibling of LD#91) |
| **LD#61** | llm-distillery | Cross-filter trajectory-framing mis-lensing (sibling of LD#91) |
| **ovr#283** | ovr.news | Publication floor — decide or close won't-do (behind ovr#285) |
| **FS#121** | FluxusSource | fda/patent aggregators never run (hardcoded `all_sources`) |
| **LD#84** | llm-distillery | solutions oracle prompt router self-contradictory |
| **LD#94** | llm-distillery | solutions v6 `concreteness_gatekeeper` inert — 0 binds in 191,616 articles (benign NM#284 shape: a config key that declares an enforcement point with no runtime effect). Recommend remove-or-document; raising the threshold is a real behavior change needing an ADR-021 recall check. **Run the same two-condition count on `nature_recovery v4`'s `recovery_evidence`** — the redundancy argument generalizes. |
| **LD#81** | llm-distillery | Align sklearn across training + inference |
| **LD#89** | llm-distillery | Share frozen-mpnet embed pass between obituary + violence |
| **LD#23 / LD#70 / LD#71** | llm-distillery | cd evidence_quality; nr protection scope; nr v5 recall |
| **ovr#214 / ovr#255 / ovr#256** | ovr.news | Language leak; academic stock photos; US-centric abbreviations |
| **NM#221 / NM#220 / NM#96** | NexusMind | GPU multi-tenancy, Ollama coexistence, sustainable hosting |

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

LD#38, LD#40, LD#43, LD#24, LD#78, LD#79, ovr#232, ovr#223, ovr#211, ovr#213,
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
| NexusMind | 6 | 104, 225, 226, 228, 229, 251 |
| ovr.news | 42 (20 of them non-engineering) | engineering: 41, 59, 68, 115, 177, 180, 207, 210, 224, 228, 229, 230, 233, 234, 239, 243, 245, 247, 248, 263, 265, 271 |
| FluxusSource | 0 | — |

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
2. **ovr#285** → then **ovr#283** decision.
3. **ovr#280** ingestion fix → **NM#278** retune, now with **NM#291**'s measured 0.836.
4. **ovr#281** — stock heroes (two independent halves: stickiness, validate false-rejects).
5. **ovr#204** — remove hardcoded obituary filter.
6. **NM#290** — hero cross-domain check; the class survived NM#288.
7. **ovr#287** — hero backfill, after the `image_source` stamp is disambiguated.

### Batch C — Legal / compliance
1. **ovr#284** — Art. 5(2) record + a hero-image egress control that is deliberate rather than accidental.
2. **ovr#274** — full threat-surface security review (standing).
3. **ovr#278** — safe-fetch defence-in-depth leftovers.

### Batch D — Deadline track
1. **FS#120** — eval readout, ADR-007 gate, **~2026-08-14**. Start the readout script well before the date; ovr#275's attribution export is live.
2. Close **ovr#275** after the ~Aug 2 backlog washout check.

### Batch E — Summarizer (strictly sequenced)
1. **ovr#277** (non-destructive re-gate) → 2. **ovr#276** (determinism) → 3. **ovr#235** (gate) → 4. **ovr#270** (swap) → 5. **ovr#286** (backfill).

### Batch F — Measurement trust (NEW 08-03; **precedes any threshold decision**)
Listed last but sequenced first: Batch A.5 and every Chain 4 enforce flip depend
on it.
1. **LD#95** — pin the batch size, or state the measured noise floor where
   claims get made against it (`docs/FILTER_PLAYBOOK.md`, the ground-truth gate).
2. **NM#289** — check the three percentile CDFs' refit dates against current
   production raw percentiles. Cheap; may reopen Chain 3 at the upper tail.
3. **LD#94** — remove or document the inert gatekeeper, and run the same
   two-condition count on `nature_recovery v4`.
4. Only then: **LD#93 step 4** (fit the solutions short-content cap) and any
   Chain 4 enforce flip. Both are threshold fits that inherit LD#95's noise.

## Housekeeping (opportunistic)

- Delete retired sustech/foresight dirs (post-drain — due now).
- Sync `score_normalization.py` (44-line divergence LD ↔ NM).
- LD#49 / LD#48 — remove superseded filter versions; normalize Hub naming.
- FS#105 — version systemd units in-repo (ovr#254, its twin, **closed 08-03**).
- NM#91 sadalsuud healthcheck drift (operator decision).

## Standing Operator Decisions (Jeroen's call)

- ~~NM#285 Option C~~ — DECLINED 2026-08-02 on the measurement (Option B shipped). Reopen only if prefilters regain lens rules worth enforcing.
- **ovr#283** — publication floor: yes/no/won't-do.
- **ovr#284** — how the Art. 5(2) record is written and by whom.
- **ovr#287 (NEW)** — the ~36 wrong-story heroes: **re-extract or blank?**
  Blanking is cheap, certain, and consistent with NM#288's own stated principle.
- **LD#95 (NEW)** — pin the production batch size for reproducibility? It does
  not remove the noise, only makes a cycle repeatable. The alternative is a
  noise margin around each op-point, which is a bigger change.
- ~~**Chain 14** — file a root issue?~~ **DONE 2026-08-03 — NM#292.** The open
  call is now the one NM#292 asks for: run the common-denominator English vs
  non-English comparison, or close it won't-do on the grounds that the four
  constituent issues are already banded.
- **LD#85** obituary v6 relabel — PARKED; reactivate on obit-flag or over-block harm.
- NM#91 healthcheck drift; uplifting v7 NO_HUB backup; cd v5 config-schema exemptions.
- FluxusSource: 71 DEAD disable candidates; OVER_POLLED audit; global-broadening yield check.

## Related Memories

- [[project_session_2026_08_03]] — LD#93 ship + sync, LD#95, the three upstream defects
- [[project_session_2026_08_01]] — the session the prior update followed
- [[project_session_2026_07_31]] — Chain 3 deploys
- [[project-obituary-detector]] — Chain 1 details
- [[filter-status]] — per-filter MAE/status
- [[calibration-history]] — Dead Ends (read before calibration/scorer work)
