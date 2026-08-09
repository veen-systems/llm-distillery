---
name: project_session_2026_08_09_later
description: Sent to certify INST-10; the certification's finding was a refusal, and the owner's layering question found three source-blind deletion points with a six-day-old merge-ready fix for the biggest.
metadata:
  type: project
---

# 2026-08-09 (later) — the deletion happens three layers up

**One line:** the brief's top item ("certify INST-10 and turn time on") was two
gates presented as one and I could only clear the first — but the owner's own
question about repo layering turned out to be worth more than the whole brief.

## What shipped

| | |
|---|---|
| **NexusMind `8ed8139`** | PR #299 merged — load-time `duplicate_title` drop is now source-aware. Closes NM#296 |
| **NexusMind `b90ba9e`** | INST-10 certified (non-author), INST-10/INST-11 registered in V&V §2, two instrument defects fixed |
| **llm-distillery `43815bb`** | corroboration corrections — FS#143 and Contract A both refuted |

**Nothing deployed.** PR #299 is merged but sadalsuud runs its own checkout.

## The refusal, which was the real INST-10 result

The brief said the temporal term was *"blocked ONLY on review by someone who is
not its author."* It is blocked on two things and the second is a whole untested
half.

**Reproduced INST-10 exactly** from source on the v2 frame: unweighted AUC
**0.798** (production) / **0.767** (candidate), `med_D > med_S` in **6/6** strata,
Kish ESS 36.1, permutation control clean, robust to the date-only confound
(0.798 → 0.794). Certified — **for the precision side and nothing else.**

**Why that cannot authorise the flip.** PROP-1's pre-registered falsification is
*"fails to improve **recall** at fixed largest-cluster size."* INST-10's first
declared blind spot is recall, entirely — every pair it sees is one the system
already merged. The config comment above the flag says it outright: *"Do not score
it on precision alone — that is the one-sided error this whole investigation is a
record of."* **That test has never been run.**

**And the shipped σ is the refuted one.** `config/app.yaml` carries
`temporal.sigma_hours: 72.0`:

| σ (h) | %S gaining | %D losing | both > 50% |
|---|---|---|---|
| 6 | 52.1 | 98.2 | yes |
| 18 | 83.6 | 85.9 | yes |
| 36 | 97.8 | 56.8 | yes |
| **72 (shipped)** | 99.1 | **20.6** | **NO** |
| 120 | 100.0 | 9.2 | NO |

At σ=72 the term nudges 99.1% of true pairs *and 79.4% of false merges* upward —
a merge-more lever aimed at a population measured at precision 0.173. Two-sided
window is **σ ∈ [6, 36]**.

**Two instrument defects found.** The docstring's weighted figures never
reproduced (0.902/0.748 claimed, **0.915/0.756** actual — carry-over from the
pre-`9c3baeb` crashing runs). And stratum weights were computed before exclusions,
which flattered the `--exclude-date-only` **robustness check specifically**
(candidate 0.756 → **0.719**, ESS 83 → 31) — see the gotcha, because I first
sized that bug by comparing two runs of the buggy code.

## The owner's question, which was the better thread

> *"FluxusSource is supposed to do dedup only… then NexusMind will do
> corroboration. Are we on the right level together?"*

No — and there are **three source-blind deletion points in series**:

| # | Where | Volume | State |
|---|---|---|---|
| 1 | FluxusSource content hash | ~20 cross-source/run flagged (**provisional**, post-FS#142 reset) | FS#133 open |
| 2 | NexusMind `_is_duplicate`, **at load** | **5,405 dup-title/cycle**, ~46.7% cross-outlet | **FIXED, not deployed** |
| 3 | NexusMind `story_dedup` | ~1,500/cycle | unaddressed |

**Point 2 was invisible from this repo and mattered most.** It runs *before a
single embedding is computed*, so no threshold or representation change can reach
it — and it censors the corroboration programme's own measurement population.
Every number in the V&V registry, the 0.173 precision included, is computed on a
corpus whose easiest positives were deleted first. It also picked survivors by
**file order**, so in 216 measured cases a `news.google.com` redirect survived and
the real publisher was binned.

**Point 3 is the design flaw the question actually names.** One clustering pass,
one threshold, two jobs with opposite risk profiles: it deletes ~1,500
articles/cycle *and* emits the `corroborating_sources` count that drives ovr.news
ranking. A wrong merge silently bins a distinct article **and** inflates a trust
signal. How many of those deletions are wrong is **unmeasured** — INST-12's row
says so explicitly.

## PR #299, which had been merge-ready for six days

Found via a backlog line while looking for something else. Its stated hold
("until #298 has run 2–3 clean cycles") expired **2026-08-03**; it had since gone
`CONFLICTING`.

- **Rebase was one documentation row** — `scripts/main.py` and tests auto-merged;
  only `memory/MEMORY.md` conflicted, because `c3ba75b` split the decisions table
  into `memory/decisions.md`. Diffstat unchanged at 446/22.
- **Tests, same command both sides**: main **1021**, branch **1038**. +17, zero
  failures. CI green.

Three checks run before recommending it:
- **Full-host identity is load-bearing.** Independent classification of
  FluxusSource's cross-source drops: **46% Google News feeds colliding with each
  other, 42% real distinct outlets, 11% mixed** — so a naive "keep anything
  cross-source" preserves more junk than signal. Full-host collapses all of it.
  Replicates the PR's own 53.3/46.7 split on a different mechanism.
- **Generic-headline false-corroboration risk is absent**: 21,570 titles, 282
  cross-host collisions, median length 69 chars, **1 of 282 under 30 chars**.
- **O(n²) safety net is fine**: 60 ms at 8,000 articles at 40% duplicates.

## Three claims this repo gave the owner that were false

Two drove owner decisions. All corrected in `corroboration-feature-hypotheses.md`.

1. **FS#143** — *"removes 100% of the duplicate class; 0 titles in ≥2 category
   feeds."* Both false: the category feeds duplicate **each other 738× in 7 days**
   (`cs_lg`×`cs` 452, `cs`×`math` 64, `cs`×`physics` 41), and **123 titles were
   unique** to the dropped feed. The drop was right anyway — 82.8% overlap.
   **Consequence: 738 pairs/7 days remain, larger than what was removed.**
2. **Contract A** — *"`additionalProperties: false`, so collection-stamping needs a
   schema change."* False; `metadata` is open in **both** contracts.
3. **The post-enrichment recommendation** — 65/65 recall measured on 2,178 rows,
   but that sample held **zero arXiv rows**, and `arxiv_announce` is the largest
   evidence class by 4× *and* reads 0.000 after enrichment. **The gap was named
   when the decision was put to the owner and recommended past anyway.**

## Cross-session coordination

A FluxusSource session was live in the same checkout throughout. I touched no
FluxusSource file. Exchanged measurements instead: they took my cross-source
classification for FS#133 (correcting my `gn_`-prefix method, which named only one
of three Google News populations), and corrected three of my claims. They
**declined to execute FS#143 on my relay of the owner's decision** — right call;
authority for a live-source config change has to reach them from the owner
directly. Lesson taken.

## Deploy verification — 12:01 CEST cycle, read the same day

Deployed to sadalsuud 11:12 CEST (`bb0f93b`), idle window, `git pull --ff-only`;
no requirements or systemd change. Cycle ran 12:01:55, completed, **0 errors**.

**Mechanism: CONFIRMED.**

| | 08:11 (pre) | 12:11 (post) |
|---|---|---|
| `dup-title` | **5,543** | **2,921** `[+2,634 cross-outlet kept for dedup]` |
| total title collisions | 5,543 | 5,555 |
| **kept instead of deleted** | 0 | **2,634 = 47.4%** |

Predicted 46.7%. The safety net fired **once** ("1 title-collisions collapsed by
fallback") — a near-no-op on the healthy path, exactly as the PR claimed.

**Outcome: NOT ESTABLISHED, and the absolutes point the wrong way.** `Loaded`
**fell** 3,374 → 3,054, clusters **fell** 2,258 → 1,944, corroborated rows
**fell** 1,056 → 956. All of that is corpus movement — `old` alone rose by 3,851
as the 3-day window advanced, and FluxusSource shipped FS#143 plus 7 new archive
feeds and a 12h cadence change into the same cycle. Normalised:

| | pre | post |
|---|---|---|
| corroborated share | 47.4% | **49.7%** |
| mean sources | 7.2 | **7.4** |

Right direction, **too small and too confounded to call an effect** — one
uncontrolled before/after across two different corpora, with a second repo's
deploy inside it. Under this project's own #95 standard that is not
distinguishable. **Next controlled read: accumulate several cycles and compare
like-for-like.**

Two gotchas came out of this verification and are in [[gotcha-log]]: the
pre-registered probe named the *code symbol* (`cross_outlet_title_kept`) while
the log emits `cross-outlet kept for dedup`, so a literal grep returned **0** —
the exact failure signal it was written to detect; and a counter firing is the
mechanism, not the outcome.

## Phase 1 of the #299 A/B — run same day, and it qualifies the win

*Owner's correction: waiting several cycles was observation; the instrument
wanted was a same-input experiment, and 292k rows plus an idle 3090 Ti were
already sitting there. Replay imports `_normalize_title`, `_normalize_url` and
`_outlet_identity` from `scripts.main` rather than re-implementing them —
a prior measurement in this programme drifted exactly that way.*
Script: `NexusMind/scripts/research/replay_296_ab.py`; output
`data/research/replay_296_ab/`.

**Over 292,007 raw rows / 14 days (2026-07-26 → 08-09):**

| | |
|---|---|
| dup-url skipped | 33,627 |
| title collisions | **11,084** |
| old rule deleted | 11,084 (all of them) |
| new rule deletes (same outlet — correct) | 5,594 |
| **preserved by #299** | **5,490** — ~392/day |

**Calibration control PASSES.** Replay kept-share **49.5%** vs production's
measured **47.4%** → Δ 2.1 pp. So the replay tracks production despite not
replicating `already_processed` / commerce / obituary / dup-id.

**The qualification, which nobody had flagged: 77% of what #299 preserves has a
Google News redirect on one side.**

| | pairs | share |
|---|---|---|
| Google News on ONE side | 4,230 | **77.0%** |
| Google News on BOTH | 0 | 0.0% |
| **neither side GN — unambiguous cross-outlet** | **1,260** | **23.0%** |

`_outlet_identity` reads the URL host, so a GN redirect is `news.google.com`
whatever publisher it actually resolves to. **For 77% of preserved pairs the true
publisher of one side is unknown from the data.** They may be genuine
corroboration or the same publisher reached twice — and under the
counting/deleting conflation a wrong one both deletes an article *and* credits a
source. `both = 0` is the documented known limitation showing up exactly as
predicted: two publishers *both* via GN collapse to one outlet and are still
dropped.

**The unambiguous 23% is excellent**, and is textbook corroboration — different
newspapers, same country, same story:

| n | pair |
|---|---|
| 85 | `en.yna.co.kr` ↔ `koreatimes.co.kr` |
| 78 | `en.yna.co.kr` ↔ `koreaherald.com` |
| 62 | `aftonbladet.se` ↔ `sydsvenskan.se` |
| 24 | `businessday.co.za` ↔ `timeslive.co.za` |
| 23 | `gva.be` ↔ `nieuwsblad.be` |
| 15 | `stern.de` ↔ `zeit.de` |
| 12 | `dhnet.be` ↔ `lalibre.be` |
| 10 | `derstandard.at` ↔ `diepresse.com` |

**Do not read the 77% as junk.** Spot-checked examples are cross-outlet on their
face — `us_news_ap_news` ↔ `science_phys_org`, `south_african_timeslive` ↔
`us_news_ap_news` — where the GN-ness is a redirect wrapper, not the publisher.
The point is it is **unverifiable from the URL**, not that it is wrong.
Resolving it needs the true publisher URL, which is what enrichment already
fetches and what FS#144 touches.

**Phase 2/3 are unchanged and now better targeted**: cluster both article sets on
b650, then adjudicate the merges that exist only because of #299 —
**stratified on GN-on-one-side vs neither**, because those two strata have
completely different verifiability.

## Phase 2 — every preserved pair merges, and that is what makes the product question urgent

`NexusMind/scripts/research/phase2_296_cosine.py`, run on b650's 3090 Ti
(`~/llm-distillery/venv`, torch 2.13+cu130). Embedded the **raw** titles of all
5,490 preserved pairs with `intfloat/multilingual-e5-large` under
`query: {title}` — the deployed representation, title-only, verified against the
running file. Pairs share a *normalized* title; the raw title is what gets
embedded, so the gap had to be measured, not assumed.

| population | n | median cos | ≥0.88 | ≥0.92 | identical |
|---|---|---|---|---|---|
| **ALL preserved** | 5,490 | **1.0000** | **100.0%** | **100.0%** | 87.7% |
| GN on one side | 4,230 | 1.0000 | 100.0% | 100.0% | 90.8% |
| neither GN | 1,260 | 1.0000 | 100.0% | 100.0% | 77.2% |
| **random-pair control** | 2,733 | **0.7626** | **0.2%** | 0.0% | 0.0% |

Separation 0.2374, so the instrument discriminates — the 100% is not an artefact
of e5 putting all headlines close together.

**Answer to the phase-2 question: YES, mechanically certain.** Every preserved
pair clears the 0.88 cross-source bar *and* the stricter 0.92. #299 does not add
near-duplicates to the feed; it converts ~392 deletions/day into ~392 merges,
each emitting a corroboration credit. For a two-member merge the centroid **is**
the survivor's embedding, so pair cosine is exactly the decision variable here —
it stops being exact at three-plus members.

**And that is precisely why NM#301 is now the binding question, not a side issue.**
The rescued population is same-headline by construction, and 87.7% are
byte-identical. The 676 non-identical ones are punctuation and casing variants of
one headline, not independent write-ups:

| cos | pair |
|---|---|
| 0.990 | `japan_times` / `japan_today` — curly vs straight apostrophe |
| 0.997 | `bbc_news` / `myjoyonline` — quote marks |
| 0.995 | `japan_times` / `al_monitor` — "U.S." vs "US" |
| 0.962 | `france24` / `le_parisien` — emoji prefix |
| 0.987 | `bioengineer` / `nature_machine_intelligence` — same paper, two feeds |

**So what #299 recovers is carriage and syndication, not independent reporting.**
That is the same signature this file already records for the academic merges —
*"byte-identical titles… duplication, not corroboration."* Crediting BBC **and**
MyJoyOnline as two sources when the second is republishing the first is exactly
the attribution question NM#301 raises. **Whether that should count is a product
decision and belongs to the owner** — "two outlets carried this" is true and
arguably useful; "two outlets independently corroborate this" is not what the
data supports.

**Phase 3 accordingly changes shape.** Adjudicating "same story?" is pointless at
cosine 1.0 — the answer is obviously yes. The open question is **independence**,
and its biggest single unknown is the 77% with a Google News redirect on one
side, where the real publisher is unknown from the URL. Resolving that means
following those redirects — an outward-facing fetch against Google, so it needs
the owner's say-so rather than being run unilaterally. Enrichment already follows
them in production, and FS#144 touches the same ground.

## Next session

1. **Deploy PR #299, then prove the outcome** — read `cross_outlet_title_kept` off
   the first cycle: expect ~2,000–2,500 against ~5,400 `dup-title`. **0 while
   `dup-title` is unchanged means the deferral is not reached** (NM#284/#300 shape).
2. **Run PROP-1's actual falsification** — INST-4 with temporal off vs on at
   σ ∈ [6, 36] at fixed largest-cluster size, on the b650 harness. Free, no labels.
3. **Correct `CLAUDE.md` line 237** — still carries the two refuted claims. Left
   deliberately: the correction came from a peer session.
4. **Separate counting from deleting in `story_dedup`** — the design fix.
5. PROP-2 ratio-margin; deepen panel-v3's giant stratum.

Related: [[corroboration-feature-hypotheses]], [[nexusmind-data-sources]],
[[score-batch-shape-noise]], [[gotcha-log]].
