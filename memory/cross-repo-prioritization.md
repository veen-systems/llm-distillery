---
name: cross-repo-prioritization
description: Master cross-repo issue prioritization across llm-distillery, NexusMind, ovr.news, and FluxusSource — dependency chains, P0-P4 rankings, sequenced work batches
metadata:
  type: project
---

# Cross-Repo Prioritization

## Board count 2026-08-11 **12:56** — **251 open**. The count is not the finding; the distribution is.

| repo | open | touched ≤7d | touched ≤2d | oldest untouched since | Δ vs midday |
|---|---|---|---|---|---|
| ducroq/ovr.news | **89** | 17 | **0** | 2026-02-09 | — |
| ducroq/NexusMind | 51 | 21 | 11 | 2026-04-13 | — |
| veen-systems/llm-distillery | 40 | 25 | 13 | 2026-03-07 | **−1** (#102 closed) |
| ducroq/augmented-engineering | 34 | **0** | **0** | 2026-03-16 | — |
| ducroq/FluxusSource | 17 | **16** | 10 | 2026-08-02 | — |
| veen-systems/persuasion-scorer | 12 | **0** | **0** | 2026-08-02 | — |
| veen-systems/pipeline-atlas | 8 | **8** | 7 | 2026-08-07 | — |
| **TOTAL** | **251** | 87 | 41 | | **−1** |

**Already stale, in this same session: llm-distillery is 41 and the total 252**,
after #108 was split out of #105 an hour later. Left visible rather than silently
patched — this is the sixth consecutive pass where the number moved between being
written and being read, which is the point the paragraph below makes.

**Only 41 of 251 issues (16%) have been touched in two days, and they sit in four
repos.** That is the number worth acting on, not the total.

- **`ovr.news` is the largest board (89 — 35% of everything open) and has had
  nothing touched in two days.** Its live-ish items (#304, #305, #287, #296) are
  mostly downstream consequences of NexusMind defects, which reads as work having
  moved upstream rather than the board being abandoned. Its oldest untouched issue
  dates to 2026-02-09 — six months.
- **`persuasion-scorer` (12) and `augmented-engineering` (34) are frozen** —
  46 issues, 18% of the total, nothing touched in over a week. Neither is a
  pipeline blocker; the first is the split-out research project (its DR-003), the
  second is mandated output on no board.
- **`FluxusSource` is where the energy is**: 16 of 17 issues touched this week.

`updatedAt` counts any edit including a label change, so it measures touch, not
progress. **Six local repos have no GitHub remote at all** (`art`, `brainstorm`,
`busara`, `infra`, `research`, `sandbox`) and `admin` is on a sadalsuud git
remote — none has an issue tracker, so work there is structurally invisible to
every count in this file. PRs are not counted.

**The count moved 246 → 249 → 252 inside the midday session**, and only 3 of the 6
moves were that session's. **This is the fifth consecutive pass where the total and
its own narrative disagreed at some point.** With three sessions filing
concurrently the number is only true at the instant it is read: quote it with a
timestamp, and re-query immediately before acting on it, never at the top of a
session.

<!-- verify: tot=0; for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer veen-systems/pipeline-atlas ducroq/augmented-engineering; do n=$(gh issue list -R $r --state open --limit 400 --json number --jq 'length'); echo "$r: $n"; tot=$((tot+n)); done; echo "TOTAL: $tot" -->

### The four chains in the live work (2026-08-11 afternoon)

Grouped from titles, then **corrected by the FluxusSource and NexusMind peer
sessions**, who refuted a status claim each. Both corrections are recorded here
because the uncorrected versions are the intuitive readings and will be
re-derived otherwise.

**A. Google News / short content.** FS#145 → NM#310 → NM#309 → LD#106 / LD#105 / LD#92.
**FS#145 is an ENABLER, not a root cause — my first framing was wrong.** It
harvests the publisher *host* from `<source url>`, not the article URL, so it does
**not** make GN items enrichable (NM#310 stands) and the **GN share does not fall
when it lands**. It takes publisher identification from 45.6% to ~100%; the share
only moves later via ADR-007 native-feed migration, one editorial call per outlet.
Do not schedule anything on "GN share falls when FS#145 closes". The corpus
argument is untouched and is the reason to do it: 0–4.9% GN in training against
25.7% of production.

**B. Enrichment corrupts bodies.** **NM#314 is BUILT, not unstarted** — PR #317,
merged-pending, reviewed. The gate is **merge + deploy**: sadalsuud was on
`main @ 6f45633` with no `src/enrichment/decision_log.py` as of 2026-08-11, so
every measurement sequenced behind it is blocked on a pull, not on code. NM#315
(duplicate-body guard, ≥5 headlines/body-hash: 90.3% precision / 92.5% recall
blind-labelled, vs 25.9% for the current affinity signal) **shipped as PR #321**,
stacked on #317. Then NM#306, NM#319, downstream ovr#287/#305.

**Neither #317 nor #321 has run a cycle, and sadalsuud has neither.** The number to
demand once both land is `quality_rejected_duplicate_body` over
`duplicate_body_groups_seen` **from a real run** — a green suite proves the
predicate, which is exactly what NM#300 says not to accept.

**What NM#315 is actually for, which its issue text does not say**: the NM#306 guard
already refuses obvious boilerplate first (`refused_title_link`, affinity 0.0), so
those never reach the duplicate guard. Its real population is the ~18% affinity
misses — **one body under several genuinely plausible headlines, affinity 0.8–1.0,
accepted by every per-article check**. Recurrence across the corpus is the only
evidence that can see it, which is why no per-article rule can substitute.

**And that is exactly what BOUNDS it — do not read 90.3% precision as coverage of the
defect class.** Recurrence being the only evidence means the guard is **blind to a
wrong-but-plausible pairing that occurs once**, and per the NM session the singleton
is **most of the population by count**, not a tail case. NM#315 catches the
syndicated/boilerplate shape *because it repeats*; nothing in PR #321 addresses the
singleton. **The residual lands on us and nothing on our side can see it either**: a
coherent body about the wrong story is a real article attached to the wrong headline,
so it scores like one — no threshold, calibration or op-point reaches it, and the
#95 band is irrelevant because the score is not wrong, the pairing is. Treat this as
an open, unowned class rather than something #315 closes.

**C. The measurements are not trusted.** NM#303 / NM#304 (contract tests validate
fixtures, never production output), NM#312 (two integration tests have never run),
LD#104 (every accuracy number is CPU-measured while production serves on GPU).

**D. Collection efficiency.** FS#142 (cross-run dedup leaking 12.9%), FS#133,
FS#156, FS#157 — the last has a measured downstream cost: the #144 regeneration
changed `investment_risk v6`'s input composition mid-cycle and confounded the
secondary expectation of the 2026-08-11 op-point verification.

### The ordering, against the owner's stated stopping condition

The condition is **not** "the pipeline is in good shape" — against 249 issues that
is never true. It is **"the corpus a retrain would be labelled on is
trustworthy"**, which is about a dozen issues. Ranked 2026-08-11:

| # | item | repo | why here |
|---|---|---|---|
| 1 | **FS#145** harvest the real publisher from GN's `<source url>` | FS | 100% coverage, free, feedparser already parses it, **never read**. Name-guessing is **45.6%** on the `gn_*` country proxies ADR-007 targets. Closes **58%** of the 25%/5% corpus-vs-training gap — population A. |
| 2 | **Bulk native repointing for population B** | FS | The other 10.8% of the corpus, identical defect, **ADR-007 does not cover it**. `scripts/gn_to_native_upgrade.py` exists — a run, not a build. |
| 3 | **#105** two filters trained on corpora >50% refused by today's gate | LD | Directly answers the stopping condition. Gates `human_thriving` v8. |
| 4 | **NM#315** duplicate-body guard at ≥5 headlines | NM | 90.3% precision / 92.5% recall on a **blind** hand-labelled n=150 with a sealed key — best-evidenced fix on the board. Needs NM#314 first. |
| 5 | **FS#142** cross-run dedup leaking 12.9%, seen-hash store collapsed | FS | Duplicates over-weight labels; an **active regression**, not a standing defect. |
| 6 | **NM#188** story dedup | NM | Reader-visible now: Nepal's tiger census published **six times** in `nature_recovery`. |
| 7 | **FS#146/#149** language ID | FS | Corpus composition; real but smaller than the GN cluster. |
| — | ~~#93 step 4~~ | LD | **Re-measured 2026-08-11: gate still closed, do not set the cap.** No action. |

**Two levers for GN, not one** — this corrects the 2026-08-11 morning framing that
FS#145 alone closes the gap. Population A (14.9% of corpus) needs `<source url>`
harvesting; population B (10.8%) already knows its publisher and needs repointing.

### Method note that cost real work this session

**Seven errors were caught between this session and `fluxussource-85`, roughly
evenly split, and none would have been caught solo.** The recurring shape on both
sides was *asserting a population without measuring it* — a feed count read as item
mass, a label asserted unused, a surfacing share read as reader exposure. The
working pattern: **evidence posted to issues, not instructions to sessions**; each
side measuring only what it could reach; every rate carrying its denominator.

---

## Board count 2026-08-09 (later) — **195 open**

| repo | open | Δ vs 08-07 |
|---|---|---|
| ducroq/ovr.news | 89 | — |
| ducroq/NexusMind | 43 | +1 |
| veen-systems/llm-distillery | 35 | −1 |
| ducroq/FluxusSource | 13 | **−3** |
| veen-systems/persuasion-scorer | 12 | — |
| veen-systems/pipeline-atlas | 3 | — |
| **TOTAL** | **195** | **−3** |

FluxusSource fell because its own parallel session closed FS#143 and others the
same day. NexusMind is net +1 despite **NM#296 closing via PR #299** — new issues
were filed against it in the same window.

**One chain item moved and it is the biggest one:** NM#296 (load-time source-blind
title drop) is **CLOSED** — `8ed8139`. That was the largest of three source-blind
deletion points, and it had been merge-ready and unmerged for six days past its own
expired hold. **Merged is not deployed** — the deploy-and-verify step is the open
half. See [[project_session_2026_08_09_later]].

*Standing trap, unchanged and demonstrated again this session: the decision list
drifts faster than the issue list. Two "measured" facts in the inherited handoff
brief were false, and both had already driven an owner decision before anyone
re-derived them.*

<!-- verify: tot=0; for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer veen-systems/pipeline-atlas; do n=$(gh issue list -R $r --state open --limit 400 --json number --jq 'length'); tot=$((tot+n)); done; echo "TOTAL: $tot" -->

---

**Last updated: 2026-08-07 (night)** — chain placements, seven stale entries corrected and the total fixed to **198**. Previously: full re-query against GitHub, then a
**second pass that re-queried every link in every chain**. Read the
[2026-08-07 ordering](#ordering-2026-08-07--re-queried-full-board) first, then
[chain verification](#chain-verification-2026-08-07-late--every-link-re-queried)
— the latter corrects **two chain links that were marked ✅ while open**, one of
them substantively. The P0–P4 tables further down are the 08-05 state and
several of their entries have moved or closed. The older
**[Board refresh 2026-08-05](#board-refresh-2026-08-05-late--re-queried-against-github)**
section is kept as history.

---

## 2026-08-08 morning — the deadline item is GONE, and a parallel session took it

<!-- verify: tot=0; for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer veen-systems/pipeline-atlas; do n=$(gh issue list -R $r --state open --limit 400 --json number --jq 'length'); echo "$r: $n"; tot=$((tot+n)); done; echo "TOTAL: $tot" -->

**Board: 196 at session close** — LD **36** · NM **43** · ovr **89** · FS **13** ·
ps **12** · atlas **3**. Sediment (untouched 30d+, cutoff 2026-07-09): **74** —
LD 10 · NM 19 · ovr 45 · FS 0 · ps 0 · atlas 0. *Quote the cutoff date with that
number; it moves on its own and the 81/82 recorded on 08-07 was against a
different window.*

> It read **195** mid-session. The delta is **NM#303** and **FS#138**, filed by
> this session, minus **FS#134**, closed by the parallel session at 07:38Z. So
> the count moved **198 → 199 → 195 → 196** in one day and every move was ours —
> which is the fourth consecutive pass where the total and its own narrative
> disagreed at some point. **Re-count after filing, and re-query before quoting.**

**The count went 198 → 199 → 195 inside two hours, and both moves were ours.**
199 because the 08-07 night pass filed LD#101 after taking its own count (third
consecutive pass to do that). Then **five FluxusSource issues closed between
08:15 and 08:55 CEST** — and LD#101 closed here — taking it to 195.

**Chain 8 (Google News) is CLOSED. `ADR-007` accepted 2026-08-08 (`ff6932b`),
FS#120 + FS#119 closed, gate decided six days early.** Also closed the same hour:
FS#132, FS#130, FS#124, FS#105. Decision: **retire the 55 GN country proxies and
all three eval arms; native-first.** H1 confirmed by *topical precision* rather
than usable-article rate — `gn_chad` carries **2 on-topic items in 462 (0.4%)**,
the rest being US sports outlets, obituaries for men named Chad and a UK paper
called *the Chad*. H2 failed (quota; no article body, median 58–60 chars; 93% of
GDELT's Madagascar rows are `storm.mg`, Taiwanese, via the `.mg` ccTLD). H3
reformulated: NewsData filters publisher *location*, GNews only *topic*. H4 moot.

**So the only calendar-bound item on this board is gone**, and the ordering table
below now starts at NM#301.

### The session-collision lesson, because it cost a wrong public comment

`veen-systems/pipeline-atlas`-style parallelism is now normal here:
`ListAgents` showed **three** peer sessions live, one (`fluxussource-9c`) 12 hours
into FluxusSource. It wrote ADR-007 at 08:54:31 and closed FS#120 at 08:54:57. I
posted a comment on that issue at **09:24** saying the baseline contamination
"needs an owner call before the ~08-14 gate" — from a board state read at 08:05.
The *finding* was identical to theirs; the *disposition* was wrong, and theirs was
better (the collision is evidence about the thing being retired, not noise in a
comparison). Corrected in-thread rather than deleted.

**Rule: re-query issue state immediately before commenting or closing, not at the
top of the session.** The existing "a pass that files issues must re-count after
filing them" is the same rule one step earlier; this is the version that bites
when someone else is working.

**Also true of working trees:** FluxusSource had four files modified mid-session
by that peer (`requirements.txt`, `scheduled_collection.sh`, `content_hasher.py`,
`requirements-lock.txt`). Nothing there may be committed, stashed or checked out
from here — see the whole-tree git verbs rule in CLAUDE.md.

### LD#101 confirmed live and closed

Verified by **outcome** on the 08:49–08:55 cycle: `eval_aggregator` rows in each
filter's `filtered_*.jsonl` went **21 → 0** across all six, with the control that
the same cycle's input carried **22** such articles. The change is now committed
(`ducroq/NexusMind@9fb441a`) — it had been running as **uncommitted working-tree
edits on sadalsuud**, invisible to the repo.

**The check originally pre-registered for it would have reported failure**: the
`source_filter excluded N` log line read **86** against a "must exceed 121"
baseline, because that count swings with corpus composition (69 → 121 → 86 in one
day). Recorded in the assistant's memory as `feedback-check-must-be-specific`.

Residual, ovr.news side, owned by nobody yet: the **~30 already-published** eval
rows, including a funeral/murder story at tier `high`.

---

## Coverage pass 2026-08-07 (late) — what the board does NOT cover

<!-- verify: for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer veen-systems/pipeline-atlas; do gh issue list -R $r --state open --limit 400 --json number --jq 'length'; done -->

Re-queried: LD **36** · NM **42** · ovr **89** · FS **14** · ps **12** ·
pipeline-atlas **2** = **195**, sediment **81**. **Nothing opened or closed since
the previous pass's own closures**, so the Ordering section below stands
unchanged. This pass tested *coverage* instead: which open issues appear nowhere
in this memo. LD, FS and ps are fully covered; **26 ovr engineering issues and 11
NexusMind issues are not.**

> **Count corrected 2026-08-07 (night): the real total was 198, not 195.** Re-running
> the verify command above gives FS **16** (not 14) and pipeline-atlas **3** (not 2).
> The FS gap is exactly **FS#133 and FS#134** — the two issues *this same pass filed* and
> never added to its own total; the atlas gap is **pipeline-atlas#3**, filed after the
> pass. So the claim "LD, FS and ps are fully covered" was true of the prose and false of
> the count it cited. A pass that files issues has to re-count after filing them.

### Chain 17: NER enrichment

**Promoted 2026-08-07 (night) into the canonical chain list — see
[Chain 17: NER Enrichment](#chain-17-ner-enrichment--new-2026-08-07-one-blocked-root-five-dependents)
under Cross-Repo Dependency Chains, which is where every other chain is looked up.**
The draft that sat here is superseded; it named **four** dependents (there are five)
and cited **NM#213** as the live matching-model consumer, **which has been
CLOSED/COMPLETED since 2026-05-23**. The live thread is NM#188 / NM#301. That error
is the same trap the draft itself documents, which is why it is recorded rather
than silently dropped.

### Chain 15 is 71 days old, not 2 — NM#225 stated it first

**NM#225** ("Audit cross-filter score comparisons; document policy as ADR") was
created **2026-05-28T16:42**, has zero comments and is banded nowhere. LD#96 and
ovr#296 were created **2026-08-05** (07:09 / 06:34). So Chain 15's note that
"two repos derived the same defect independently on the same day" misses a third,
earlier derivation — **and it is the most actionable of the three**, naming the
audit targets (tier assignment mixing filters, **lens routing in ovr.news** =
`toCanonicalLens`, "primary topic" logic) and asking for the ADR. The unmeasured
share-under-0.16 that Chain 15 wants is a subset of NM#225 step 1.

**NM#226** (same author, same day, also unbanded) belongs to **Chain 13**: its
"which invariant changed at which step" is exactly what NM#289 and LD#95 are
stuck on.

### Chain 16 is missing its NexusMind link

**NM#254** (content-level propaganda-technique extractor) was updated
**2026-08-02** — the same day all 12 persuasion-scorer issues were — and carries
the cross-post holding the taxonomy decision: **SemEval-2023 Task 3, score the 6
coarse categories, not the 23 fine** (α = 0.342 vs a 0.667 threshold). Chain 16
was assembled from ps *titles* only and so missed the sibling with the decision
in it. Pairs with **ovr#253**, also unbanded.

### A number this memo previously declined to quote

Under the stated rule `-positioning -outreach -community -content`, **ovr.news
engineering is 63 of 89** (26 of them banded nowhere; the other 24 unbanded are
the labelled go-to-market set, excluded by design).

### A seventh repo takes mandated output from this chain and is on no board

**`ducroq/augmented-engineering`: 34 open, 1 closed ever, last closure
2026-04-14.** CLAUDE.md instructs this repo to file evidence there, and ~10 of
the 34 are llm-distillery-derived and filed within the last month. It is a
write-only queue. Not a pipeline stage, so arguably not "the chain" — but it is
the same coverage-hole shape persuasion-scorer had before 08-07. **Owner call.**

### Filed this pass

- **ducroq/FluxusSource#133** — collection dedup drops on
  `md5(title + content[:500])` **with no source comparison**, so the same wire
  copy from two outlets is deleted before NexusMind sees it. Same source-blind
  shape as **NM#296**, one stage upstream, which means NM#296's population is
  already depleted and a fix there cannot recover them. Instrument shipped and
  deployed (`4994d61`); count is a floor for ~30 days.
- **ducroq/FluxusSource#134** — MinHash + Jaccard implemented, `datasketch`
  pinned, **zero call sites**. Either wire it up as a corroboration feature or
  delete it and drop the dependency.
- Comments on **NM#296**, **NM#232**, **NM#223**, **ovr#222**.

---

## Ordering 2026-08-07 — re-queried, full board

<!-- verify: for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer; do gh issue list -R $r --state open --limit 300 --json number --jq 'length'; done -->

Open, re-queried **2026-08-07 after the day's own filings**: llm-distillery
**38** · NexusMind **43** · ovr.news **90** · FluxusSource **14** ·
persuasion-scorer **12** = **197**. **83 have not been touched in 30+ days** —
LD 13 · NM 22 · ovr 48 · FS 0 · ps 0.

> **Superseded the same day by the late re-query: 196** (ovr.news **89**), and
> sediment **82** (LD **12**). The drop is ovr#303, which **this section itself
> records as closed** two paragraphs down — the count was taken before the
> closure and the prose after it, so the two disagreed by one within one
> section. Same shape as the ✅-but-open links found below: a number and its own
> narrative drifting apart inside a single pass. FluxusSource and persuasion-scorer have
no sediment at all; **53% of ovr.news's own issues are sediment** (48/90 — an
earlier draft said 59%, which is 48/82, ovr's share *of the board's* sediment,
a different quantity).

*The engineering-only count is deliberately not given here.* The label filter
yields 64, 60 or 55 depending on whether `content` is excluded, and no
canonical rule is written down. Either state the rule beside the number or do
not quote one.

Closed since the 08-06 morning re-query: LD#99, ovr#295, ovr#302. Filed since:
LD#100, NM#300, NM#301, NM#302, ovr#301, ovr#303, **and ovr#304, ovr#305,
ovr#306 filed by this session**: ovr#304 = the `displayScoreThreshold` inversion (finding 2 below), ovr#305 = the `image_source='og'` ambiguity (Chain 9's old blocker), **ovr#306 = the threat-FMEA gap** — no entry for a third-party URL in a hotlinked content field, plus a stale D02. ovr#306 belongs to **Chain 9 / Batch C**; naming it here so it is not filed-and-unplaced, which is the failure the 08-03 pass called out. FS#125/#126/#128
closed and FS#129–#132 opened *before* the 08-06 morning re-query and are
already booked there — do not count them twice.

### What changed the ordering

**1. A new cluster head appeared, and it is the strongest live item on the
board: NM#301.** Merged-pair corroboration precision on 2-article clusters —
the durable, cap-immune stratum and the one production actually runs — is
**0.560**, against `INTEGRITY.md`'s "attribution is non-negotiable". So when we
name a second outlet, we are right a little over half the time.

**Use 0.560, not the 0.283 headline.** 0.283 was measured with the production
25-member cap **disabled**, and the `giant` (51+) stratum that is unreachable
under the live cap carries **82.6%** of its weight; that population also
self-liquidates via the 14-day TTL around 2026-08-18. 0.283 [0.163–0.445] also
overlaps its own candidate comparison 0.360 [0.265–0.467] and is recorded in
the V&V registry as **not significant**. An earlier draft of this section
quoted 0.283 and glossed it as "most sources credited did not report it" —
at 0.560 a majority *did*, so the sentence inverted its own evidence.

**The ranking half is NOT fixed — this was wrong in an earlier draft and it
matters.** `1bbadb5` bounded *NexusMind's* `display_ranking.py` boost to a flat
1.10× for [2,10]. But **ovr.news never reads NexusMind's `display_rank`.** It
recomputes `_displayRank` locally as `score × decay × language_boost ×
recency_boost` (`src/lib/ranking.ts`, `src/lib/data/pipeline.ts:91`) with **no
corroboration term**, and the corroboration reordering readers actually get is
ovr.news's own editor rule — **1.3× at ≥1, 1.5× at ≥2, 1.7× at ≥3**
(`src/lib/data/editor/rules/corroboration-boost.ts:33-37`), untouched, keyed on
the same 0.560-precision clustering. That is ~6× the promotion the NexusMind
fix removed, and it is still live. **Open owner decision.**

**ovr#303** is the published-claims twin (the under-the-hood page documents
boost values NexusMind has never computed) and **LD#100** (event-identity
encoder) is the real upstream fix. This absorbs Chain 10 and outranks it.

**2. Three llm-distillery blockers were cleared by the 08-06 owner decisions**
— #95 step 2 (noise floor became a printed band), #94, #98 criterion 4. So
**#87 and #93 step 4 are movable for the first time**, and cd v6 is two
mechanical steps from cutover (a Hub repo that does not exist; a
`normalization.json` that must be fitted from a historical rescore).

**3. FS#120 is now 7 days out** and is still the only calendar-bound item. Its
harness was built 08-06; it needs one run and one decision.

**4. NM#300 re-opens the #93 stamp half.** `content_length` is populated on
**0 of 50,605** persisted rows although the deployed scorer is md5-identical to
this repo's. Fifth instance of the repo's defining failure shape.

### The order

| # | Item | Repo | Why here |
|---|---|---|---|
| 1 | **FS#120** GN eval readout + ADR-007 gate | FS | Only hard date (~2026-08-14). ~~Harness exists; one run + one decision.~~ **Understated — corrected 08-07 from the issue's 13 comments.** Two of four hypotheses are already answered *without* eval data: **H2 FAILED 08-03** (gdelt_constructive 0 items on 12 of 19 ticks, 63% against a >50% failing threshold; free tier measured ~1 req/~2 min per IP) and **H4 answered 08-06** (**0 of 14,198** GN-proxy rows ever enriched, vs 0.0–19.9% column-C failure for the three eval arms). H1 on track (GN proxies 27.6% published share vs 90.8% for the other 366 sources). **The live remainder is bigger than one run:** the last comment argues **240 of the 312 GN sources are `q=… site:<domain>` single named outlets, not proxies for anything**, and that this reframing must land *before* the gate. `scripts/gn_to_native_upgrade.py` already exists, so that half is a **run, not a build**. **Critical path re-checked 2026-08-07 night — three things sit on it that no chain named.** (a) **FS#132 is a gate blocker, not housekeeping**: `gdelt_constructive` is phase-locked so each country is only ever sampled at two fixed hours, and that arm is unchanged while `gdelt`'s FS#125 fix moved **nothing measurable** (see below — the "76%→66%" was refuted; full record is 66.4% pre → 76.9% post, p=0.546). Its arm cannot be window-comparable to the others; it is currently filed under "mentioned but in no chain". (b) **The usable common window is ~6 days, not 14**: it starts at the *last* config change across all arms — GNews `country_queries` 08-05, FS#125 08-06, FS#128 08-06 — at a censored 30 items/run. (c) **LD#101**: the eval arms are scored and published, so the checklist's "share reaching the site" metric depends on a decision that has not been taken. |
| 2 | **NM#301** corroboration precision **0.560** at 2 sources (+ **ovr#303**) | NM/ovr | Live, reader-visible, violates a published principle. **Wording half SHIPPED 08-07**; the ranking half is open as decision 7 — and it is ovr's OWN 1.3/1.5/1.7x rule, not the NexusMind boost `1bbadb5` bounded. |
| 3 | **LD#91** uplifting ranks a trafficking investigation 6th of 3,530 | LD | Reputational, live, untouched since 08-01. Fold into **`human_thriving` v8** as an acceptance criterion rather than patching v7. |
| 4 | **cd v6 cutover** (#98 → #87) | LD | Closest to done: 7/7 verify. Blocked only on creating `cultural-discovery-filter-v6` on the Hub and fitting normalization from a historical rescore. |
| 5 | **NM#300** content_length stamp lost | NM | Cheap; FS#120 and #93 step 4 both want the field. |
| 6 | **LD#93 step 4** fit the solutions short-content cap | LD | Newly unblocked (#92 identified, #95 decided). Must carry the 0.16 band. |
| 7 | **LD#82 + NM#286 item 3** violence audit → enforce flip | LD/NM | Once audited, enforcement is a config flip; recall 0.55 is the trade to decide. |
| 8 | **NM#302** circuit-breaker telemetry is false | NM | 33% of cap-blocked articles are deleted; the dedup work in tier 9 leans on this telemetry. |
| 9 | **Dedup programme**: NM#228 complete-linkage shadow → NM#278 retune; ovr#280 ingestion; LD#100 encoder. **NM#296 lands AFTER NM#188 has a root cause** (see the 08-04 section — an earlier draft of this row had it before) | NM/ovr/LD | Sequenced, not fast. Do **not** let LD#100 (a training project) block the cheap links. |
| 10 | **Legal**: ovr#284 **exposure-window recovery** (the record itself was written 08-05); ~~LD#97~~ **CLOSED 08-07**; ovr#274/#278. Live remainder from LD#97: **schedule the TDM scan** and **fix the 117 fail-open errors** — both ovr-side | ovr | Not "who writes the record" — that was stale when written. |
| 11 | **Measurement trust residue**: NM#289 CDF upper tail; Chain 15's missing count (share of lens placements decided under 0.16); LD#96/ovr#296; LD#61 | all | Unmeasured; decides how urgent Chain 15 is. |
| 12 | **Chain 14 non-English**: **ovr#291** (474 stored mojibake rows — FS#124's *cause* is fixed), FS#129/#130/#131 language tagging, **NM#231** (the one live stage, now a `human_thriving` v8 criterion) | all | Four repos, one pattern. NM#292's aggregate measurement is **dropped**, not pending; the tracker is retargeted as the stage index plus the per-language-pair-bar constraint. |

Below that: 83 stale issues, 48 of them in ovr.news. Age is not a reason to
close a true statement (08-03 finding: 7 of 8 sampled stale ovr issues were
genuinely unimplemented).

### Owner decisions — ALL SIX TAKEN 2026-08-07

Walked one at a time with the owner. Two of the six were **stale as listed**,
which is the reusable lesson: this board's decision list drifts faster than its
issue list, because a decision can be taken and recorded in a repo the board
does not read.

| # | Question as listed | Decision |
|---|---|---|
| 1 | **NM#301** — stop crediting, stop boosting, or both | **Hedge the wording.** "{n} sources" → "{n} related sources" / "{n} gerelateerde bronnen", every link kept, and the ✓-in-circle glyph swapped for a link glyph. **The boosting half is NOT closed** — see above: `1bbadb5` fixed NexusMind's boost, which ovr.news does not read. ovr's own 1.3/1.5/1.7× editor rule still stands. **A seventh decision is now open.** |
| 2 | **ovr#283** publication floor | **Close won't-do.** Keep storing `raw_weighted_average`. |
| 3 | **ovr#284** — who writes the Art. 5(2) record | *Stale — the record was written 2026-08-05* (`docs/security/incident-2026-08-01-comscore-beacon.md`). Real decision: **ad-tech deny-list in ovr's image path, off-domain host as a STAMP not a block, no allowlist, recover the exposure window.** |
| 4 | **ovr#287** — wrong-story heroes | **Blank what is still buildable, leave the rest.** Scope is computed per row, not per pattern: that is **6** today, not the 5 first stated — review caught one vanguard row at normalized 9.10 still reader-visible. **Stays OPEN** until the R2 round-trip clears them. |
| 5 | **ovr#292 → LD#28** — do the 333 domains bind us | *Stale — decided 2026-08-05, ADR-043, they do not.* Real decision: **say nothing on `/accountability`.** |
| 6 | **NM#292** — measure or close Chain 14's root | **Keep open, retarget.** Drop the aggregate measurement as its next step; transfer the scoring stage into `human_thriving` v8's acceptance criteria. |

**Three findings came out of the walk-through, none of which was the decision
being discussed:**

1. **NM#301's own comment says readers are shown no corroboration claim. They
   are.** The comment searched for the field `corroborating_sources` and the
   string "N sources reported this". That exact string does not exist, but the
   *field* does (`types.ts:49`, `transform.ts:42`) — what is absent is a
   rendered claim keyed on it. The same cluster membership reaches readers by
   another route: `source_quality.other_sources` → `getIndependentSources()` →
   the badge block in `[lang]/artikel/[id].astro` (~:506-528; cite the block,
   not a line — this session's own comment insertion moved it), rendering a
   badge plus named, hyperlinked publisher domains. **Textbook "establish what
   your source excludes": a grep for one field name proved absence of a
   feature.**
2. **A publication floor already exists, on the wrong quantity.**
   `config.ts:388` `displayScoreThreshold: 4.5` is read at `pipeline.ts:75` and
   applied at `:82` to the **normalized** score — the one that means "rank in
   batch". ADR-022 says visibility should key on `raw >= op-point`. 193 of
   21,905 stored rows sit below it, but it **binds 18**: `getArticlesForBuild`
   also joins `summaries` and applies the 10-day window, and 34 of the 193 are
   `sustainability_technology`, a filter removed 2026-08-03 that can never
   build. All 15 raw-carrying rows are `nature_recovery` (op-point **3.75**) at
   4.44-4.76 — so it is not "the highest was dropped anyway", **all 15 clear
   their op-point by 0.69-1.01 and are dropped anyway**, far outside the 0.16
   band. A single-filter normalization artifact, not a cross-filter floor.
   **Filed (ovr#304) rather than fixed.**
3. **Decision 5 was over-engineered and the owner was right to push back.**
   Recommended disclosing the TDM sweep on `/accountability`; the argument
   rested on the finding being publicly discoverable. **`ducroq/ovr.news` is
   PRIVATE.** With that leg gone, disclosure has no audience and solicits
   removal requests nobody would otherwise make. What survives is operational,
   not cosmetic: ADR-043 promises that a reservation *addressed to us* removes
   the source — a promise that needs the scan **scheduled** (it has run once)
   and the **117 fail-open errors** fixed, since a publisher behind a WAF that
   403s non-browser agents is the one most likely to be reserving.

**Carry into the dedup work regardless:** any confidence bar on corroboration
must be **per-language-pair aware**. Cross-lingual pairs sit structurally lower
on the similarity scale — 72.9% of what we compare, 23.5% of what we accept,
recall 38.7% vs 68.5% — so one global bar suppresses exactly the international
coverage the product exists to surface. That constraint is NM#292's most
valuable output and belongs to no single stage, which is the case for keeping
it open.

---

*The 2026-08-03 evening pass, third pass that day. What shipped after the 16:35 pass:*

| What | Where | State |
|---|---|---|
| Commerce provenance fix — the already-scored guard keyed on `_commerce_score` alone, so 205,444 of 237,813 corpus rows (86.4%) had a verdict with no model version and could never be back-filled | NexusMind `c696ea3` | **DEPLOYED.** One-time cost bounded by the age check: 21,024 rows re-scored, ~15 min, then drains to zero |
| Seeded per-run shuffle — `random.shuffle` was unseeded, so a cycle could not reproduce its own scores | NexusMind `f7fef85` | **DEPLOYED.** Replay via `NEXUSMIND_RUN_SEED`, logged in the start banner. **Replay, not stability** |
| Score noise floor recorded | LD `efab69d` | `FILTER_PLAYBOOK` §7 + `ground_truth_gate.py` docstring + CLAUDE.md hard constraint |
| sustech v3 + foresight v1 packages removed; 333 MB of production output archived then deleted | LD `289bda1` | Archive: sadalsuud `~/retired_filters_foresight_sustech_20260803.tar.gz`. **#64 closed** as superseded |
| Chain 14 root filed | NM#292 | Non-English thread now has an owner-visible root |

**Verify on the next cycle:** a `Run seed: … (from clock)` banner line, and the commerce line showing `processed` ≈ 21,000 once, then normal.

**Call path settled (was an open worry):** the gpu-server scorer unit sets
`PYTHONPATH=/home/hcl/NexusMind`, so it loads `/home/hcl/NexusMind/filters/` —
which *does* carry the #93 changes. `/home/hcl/llm-distillery/` is on no path; it
is a stale decoy that reads as authoritative. Worth deleting.

**#90 is not ready to start.** Both `nature_recovery v4` (recall 0.65 / prec 0.85
/ F1 0.736, n=391) and `solutions v6` (0.67 / 0.82 / F1 0.739, n=1032) already
passed ground-truth gates, so "do the latest scorers work?" is answered. The
open question is **which template elements are load-bearing** — #94 (gatekeeper
never binds in 191,616 articles) and #92 (short-content defect) say at least two
of the six things #90 proposes copying do not do what the config claims. Audit
before spreading.

---

*Previous pass, 2026-08-03 16:35 — second pass the same day.* The 16:25 curate
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

Open, **re-counted 2026-08-05 (late)**: llm-distillery **36** · NexusMind **40** ·
ovr.news **90** (63 engineering, after the label filter) · FluxusSource **13** ·
persuasion-scorer **12** = **191**.
*Previous count, 2026-08-03: 36 · 39 · 80 · 10 · 12 = 177. All growth is
downstream — ovr.news +10, FluxusSource +3, NexusMind +1; nothing new filed in
llm-distillery since LD#96.*
Repos: veen-systems/{llm-distillery,persuasion-scorer}, ducroq/{NexusMind,ovr.news,FluxusSource}.
Note the org: FluxusSource and NexusMind are under **ducroq**, not veen-systems —
`gh issue list -R veen-systems/NexusMind` fails with "could not resolve".

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

## Count refresh 2026-08-06 — re-queried before quoting anything

Open, re-counted **2026-08-06 morning**: llm-distillery **36** · NexusMind
**40** · ovr.news **87** · FluxusSource **14** · persuasion-scorer **12** =
**189** (was 191 on 08-05).

Closed since the 08-05 refresh: **LD#28** (TDM position recorded — but see
**LD#97**, filed the same day, which carries the unfinished half), **ovr#292,
#293, #294, #300** (the whole compliance arc from the 08-05 evening session)
and **ovr#299**; **FS#125, #126, #128** closed 2026-08-06 06:14–06:15Z. Nothing
closed in NexusMind or persuasion-scorer.

llm-distillery's own count was 36 at the morning re-query (#28 closed, **#97**
opened the same day — swap #28 for #97 in the *Infra / hygiene / writing* row
below). **#98 was then filed on 08-06, taking it to 37** — cultural_discovery
v6's *architecture* strand, split out of #87 on an owner directive: move topic
screening from the 453-stem keyword gate to a `multilingual-e5-small` probe,
the way `nature_recovery v4` and `solutions v6` already do. Belongs in the
*Lens architecture* group and sits directly under #90.

Measured the same day and worth carrying into #90's audit: `nature_recovery
v4` and `solutions v6` prefilters are **inert**, not merely loose — four junk
articles pass both — while cultural_discovery's gate removes ~70% of the
firehose. So the current template's empty prefilter is a *consequence* of
having a probe, not a design to copy on its own.

FluxusSource went **13 → 14** despite three closures, so five were filed there;
re-read that repo before sequencing Chain 8. The **Coverage** section further
down is still computed against the old **177** and remains stale — do not band
anything off it.

---

## Board refresh 2026-08-05 (late) — re-queried against GitHub

Not a work session: the board was re-read from the tracker because the owner
asked whether it was still current. It was not, in two places.

<!-- verify: gh issue list -R ducroq/ovr.news --state open --limit 300 --json number --jq 'length' -->
<!-- verify: for r in ducroq/NexusMind ducroq/FluxusSource ducroq/ovr.news veen-systems/llm-distillery veen-systems/persuasion-scorer; do gh issue list -R $r -s closed --search "closed:>=2026-08-03" --json number,title; done -->

### Corrections — two banded entries are closed

| Entry | Band it still sits in | Actual state |
|---|---|---|
| **ovr#285** (orphan reclamation NULLs `raw_weighted_average` + `source_quality`) | **P0**, and Batch B item 2 | **CLOSED 2026-08-03.** So **ovr#283** (publication floor) is unblocked — it is now a decision waiting on the owner, not on code. |
| **NM#290** (hero extractor still picks third-party chrome post-#288) | **P1**, and Chain 9's live link, and Batch B item 6 | **CLOSED 2026-08-03.** |

Also closed since the 08-03 pass and referenced above as open or in-flight:
**NM#293** and **NM#295** (the latter is the deploy-then-revert already recorded
in the 08-04 section), **FS#121** (banded P2), **LD#64**.

**ovr#299 was filed *and* closed COMPLETED on 2026-08-05** (`closedAt
15:27Z`) — the 08-05 session table above records it as new, which was true when
written. Its closing comment cross-links **ovr#298**; the two touch the same
generation step from opposite ends (how much is invented vs. what gets led with).

### llm-distillery's own 36, grouped

Because "what is open here" had no single view on this board — the P-bands
interleave five repos.

| Group | Issues | n |
|---|---|---|
| Live / blocking | #95, #92, #93, #91, #94, #86, #87, #82 | 8 |
| Lens architecture | #90, #96, #61, #66, #52, #48 | 6 |
| Filter quality / retrain | #23, #25, #55, #56, #60, #70, #71, #84, #85 | 9 |
| New filters & lenses | #38, #40, #73, #78, #79 | 5 |
| Infra / hygiene / writing | #24, #28, #30, #33, #42, #81, #88, #89 | 8 |

**14 of the 36 have not been touched in 30+ days** — #23, #24, #25, #28, #30,
#33, #38, #40, #42, #48, #52, #55, #56, #66. The live backlog here is ~22.
(#93 stays open by design: steps 1–3 shipped, step 4 — sizing the cap — is the
part still blocked, on #95.)

### Two clusters the chains do not model yet

**A. Lens commensurability.** LD#96 and **ovr#296** were filed independently the
same day and are the same defect from both ends: LD#96 says lens placement
compares scorer outputs that are not the same construct; ovr#296 says
`toCanonicalLens` breaks near-ties between exactly those outputs — its case is
*Kixikila lost Belonging to Discovery by **0.043***. That margin is well inside
**LD#95**'s measured |Δ| ≤ 0.16 batch-composition noise floor, so the placement
was decided by noise. **LD#61** (cross-filter trajectory mis-lensing) is the
same family, and **ovr#298** (summary framing can make a qualifying story read
as disqualifying) is its reader-visible end.

```
LD#95 (noise floor) ⟂ LD#96 (constructs not commensurable)
   → ovr#296 (toCanonicalLens near-ties, 0.043 < 0.16)
   ↔ LD#61 (trajectory mis-lensing)  ↔ ovr#298 (framing flips the read)
   → gates LD#90 (harmonization assumes one comparable score)
```
**Partly measured, and better than this memo first said.** ovr.news's hypothesis
log already carries the numbers (2026-08-05): **16.1%** of published articles are
scored by 2+ filters, and among those the **median top-two margin is 0.479**, with
**52.6% decided under 0.5** on a 0–10 scale. So "decided by a small margin" is
established. What is *not* measured is the share under **0.16** specifically — the
LD#95 noise floor — which is the number that says whether these are close calls or
coin flips. ovr#296's sizing work (the tie-break epsilon) is the natural place for it.

**B. Legal / compliance, upstream half. — RESOLVED; all four issues CLOSED.**
~~ovr#292 (333 of 1,357 domains signal an AI opt-out — decide whether they bind
us), ovr#293 (AI Act art. 50), ovr#294 (art. 4 / EMFA art. 6 / the Code of
Practice), and LD#28 (TDM for training data) as one programme headed by
ovr#292.~~ Decided **2026-08-05**: **ADR-043 — the directives do not bind our
fetcher**, and training got its own record rather than inheriting that one.
ovr#293/#294 closed 08-06. The 08-07 follow-on ("should `/accountability`
disclose the sweep?") was answered **no**: ovr.news is a private repo, so the
finding is not publicly discoverable, and disclosure would solicit removal
requests nobody would otherwise make. What survives is operational — **schedule
the scan** (run once) and **fix the 117 fail-open errors**, since ADR-043
promises that a reservation *addressed to us* removes the source and that
promise needs someone to look.

### Unbanded new issues

Filed since the 08-03 pass, placed nowhere:

- **NM#294** — hero validation cap (200) leaves ~79% of extracted heroes unvalidated. **Chain 9.**
- **ovr#295** / **ovr#297** — domain og-reuse cache blind to upstream images (publisher logo on 68 articles); `looksLikePublisherLogo` misses `logo300.png` and `/images/`. **Chain 9**, and they are the concrete residue NM#290's closure did not cover.
- **ovr#288**, **ovr#289**, **ovr#290** — orphan re-enrichment decision; `COALESCE` guards `undefined` but not `'{}'`; obituary-summary funeral exclusion is comma-dependent. The last is **Chain 1**'s only new link.
- **FS#128** — `rferl_kazakh` has never collected Kazakh; both RFE/RL feeds point at a generic endpoint. **Chain 14** — a non-English source that produces no non-English content is the collection stage failing silently.
- ~~**FS#125**~~ / ~~**FS#126**~~ / **FS#127** — gdelt firehose collects nothing in ~75% of runs; a zero-yielding aggregator raises no alarm; feed-cadence metric unreliable for 2/3 of OVER_POLLED feeds. FS#126 is the general case of FS#121 *and* FS#128: **nothing notices a source that stops producing.** **FS#125 and FS#126 CLOSED/COMPLETED 2026-08-06 06:15; only FS#127 is open** (verified 2026-08-07 — this line contradicted the same file's own lines 378 and 921).
  **Re-measured 2026-08-07 (night), twice, and BOTH of my readings were wrong.** I first reported 72.6% zero-yield over a window straddling the FS#125 fix; then a per-source "76% → 66%" improvement. An adversarial re-derivation over the **full 135-run record** refutes the second and reverses its sign: pre-fix **81/122 = 66.4%**, post-`0fa9ffa` **10/13 = 76.9%**, post-`61be1b1` **8/10 = 80.0%**, Aug-7-only 4/6 = 66.7% (my "66%"). **Fisher p = 0.546**; items/run 19.1 → 10.0. My "76% pre" was the issue's last-8-runs snapshot; my "66% post" dropped four post-fix Aug-6 runs that all yielded zero. I also split on the GitHub **close time** rather than the deploy time (`git reflog`: `0fa9ffa` 08-05 18:09, `61be1b1` 08-06 07:49 — two commits, the first still phase-locked). And `3c08a6d` (08-03) raised `gdelt_constructive`'s `budget_sec` 120→300 on the shared quota, moving firehose zero-yield 64.7%→91.7% inside my "pre-fix" window. **What holds:** FS#125's *coverage* half is real (`protests`/`geopolitical` now reachable); the *yield* half cannot move — an external per-IP quota shared by two identities, and `docs/GN-REPLACEMENT-PLAN.md` already sets ~50% zero as designed behaviour. **H2's real question is whether the free tier is viable at all** (FS#125 Option 3, undecided). `gdelt_constructive` still gated on **FS#132**.

**Not re-run on this refresh:** the Coverage table's unbanded set (it was computed
against the 177 total and is now stale by at least these 14), and the ovr
non-engineering list (the label filter now yields 63 engineering / 27 not, vs 56/24
on 08-03).

## Changes since the 2026-08-05 session

| What | Now |
|------|-----|
| **LD#92** | **IDENTIFIED.** Both discriminating tests run with predictions pre-registered: D1 (≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and **D3 is the largest**. `gemini-2.5-flash` cross-check on the same sample: **−1.351** — two oracles, different absolute bias, same gap. Harness + fixtures committed (`tests/fixtures/ld92/`), so the claim is re-derivable for the first time in three attempts. **Chain 4's cap value is now blocked only on Batch F.1 (#95).** |
| **Batch F.1 (#95)** | Unchanged and now the *sole* blocker on the solutions cap. Promoted in practice: every threshold decision on this board waits on it. |
| **FS#120** | **Strengthened, and it is still the only calendar-bound item (~2026-08-14).** Measured: GN is 14–17% of articles but **48–56% of all sub-300-char stubs**. Retiring the proxies drains *three* separately-measured problems — LD#92's stub population, ovr#299's summary population, and part of Chain 14. Suggested a new readout column: **enrichable rate** per candidate per country. |
| **ovr#299 (NEW)** | Summaries of headline-only articles are 83.4% material absent from the source (vs 31.6% for full articles), monotone across four buckets. Mechanism: the model has a fixed output length target (medians 1159/968/875/1065 against a 40× input range) and fills it. Fix is an input-scaled output budget, **not** skipping the summary — refusing would hit non-English readers hardest, i.e. Chain 14. Joins Chain 14 and sits downstream of FS#120. |
| **Framework** | llm-distillery was pinned at agent-ready-projects **v1.10.6**, four releases behind; now **v1.14.0** with `review-changes` adopted and re-mapped to this repo's paths. Its first run found five defects, four of them same-day errors of mine. |

**Method note.** Twice this session a conclusion of mine was overturned — once by
the owner (skipping summaries for stubs would harm the population Chain 14
protects), once by the newly-adopted review skill (p-values I had publicly
corrected and then re-introduced into memory). Both were caught *before* anything
depended on them. The pattern worth carrying: the errors were never in the
measurements, always in how the evidence was stated.

## Changes since the 2026-08-04 evening session (NexusMind corroboration thread)

| What | Now |
|------|-----|
| **NM#295** | **DEPLOYED THEN REVERTED** (`3b25373` → `88a681b`, 5 production cycles). Restoring article body to the dedup embedding did what the n=384 measurement said — a five-language cluster formed that was structurally impossible before — but roughly doubled an existing over-merging defect (clusters ≥20 up 2.01× per-1000-articles after normalisation). **Do not re-land before NM#278.** Operational trap recorded: a plain revert is insufficient, because the staleness check is `version < EMBEDDING_VERSION`, so clusters saved at the *higher* version pass as current into the older space — the store must be cleared too. |
| **Dedup sequence: LINKAGE first, then NM#278** | An earlier read of this same replay said NM#278 leads, on the grounds that tightening `cross_source_threshold` 0.88 → 0.90 drops the largest cluster 427 → 210 with no code change. **That was overturned the same day.** Size metrics are blind to cross-language loss — dropping those pairs *improves* every number in the grid. Measured directly: tightening 0.88 → 0.90 → 0.92 destroys **94% of cross-language corroboration** (450 → 184 → 26 pairs), which NM#291 had already located at 0.836-0.845. A refit chosen on size metrics would have fixed NM#188 by breaking NM#291/#295. **Complete-linkage at UNCHANGED thresholds dominates**: comparable size control (largest 76, ≥20 32 vs 101/25), comparable entity quality, ~3× the cross-language pairs retained, NM#170's calibration intact. Sequence is therefore: complete-linkage via **NM#228**'s shadow-mode protocol, *then* re-assess NM#278 on the new geometry — where 0.88 finally becomes a guarantee about real article pairs rather than about a centroid. |
| **NM#296 (NEW)** | Load-time `duplicate_title` drop was source-blind and ran *before* dedup embedded anything, deleting 1,189 genuinely cross-outlet corroboration pairs per 7-day window (46.7% of title collisions). PR #299 open, green at 1047 tests, **deliberately held** — it routes more articles into a clusterer that is currently mis-clustering. |
| **NM#188** | Root cause **still open**, but a within-run centroid-chaining diagnosis was proposed and **retracted the same day** — 71 of 85 clusters ≥50 members form on the *pinned* seed path where drift is impossible. Live candidates are NM#278 (uncalibrated thresholds) and the issue's original register-collapse hypothesis. A cluster-size circuit breaker (`max_cluster_members: 25`, `d13ef5b`) is deployed as a blast-radius bound only. |
| **NM#291 (was "unplaced")** | Placed. Its dedup-stage member is **not** a Chain 14 non-English effect in the way assumed: the load-time defect found alongside it (NM#296) skews **English** — 1.42× over-represented, with every major non-English language except Swedish *under*-represented. So NM#291's contribution to Chain 14 stands undiluted rather than being partly reattributed. |
| **Article pitch (NEW)** | `NexusMind/docs/articles/percolation-in-similarity-clustering-pitch.md`, indexed here as **Track D** in `docs/articles/README.md`. Blocked on one measurement — complete-linkage declines ~39% of what production merges and nothing yet separates false merges refused from real corroboration destroyed. |

**Sequencing consequence:** the linkage change (complete-linkage) precedes NM#278, not the other way
round — a threshold refit decided on size metrics would destroy the cross-language corroboration
NM#291/#295 exist to recover. NM#228 holds the pre-committed shadow-mode protocol and is the vehicle.
NM#296 lands after NM#188 has a root cause, not before.

**Method note worth carrying across repos:** the same size-only metrics produced a confident
recommendation that was overturned within hours, *after* the trap had been explicitly named. Any
dedup/clustering/threshold decision here needs a retention axis for the population it is most likely
to silently drop — for us that is cross-language pairs, which are marginal by construction and so
look like noise to every similarity-based screen, including token-overlap ones.

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

## Chain verification 2026-08-07 (late) — every link re-queried

<!-- verify: for r in veen-systems/llm-distillery ducroq/NexusMind ducroq/ovr.news ducroq/FluxusSource veen-systems/persuasion-scorer; do gh issue list -R $r --state open --limit 400 --json number --jq 'length'; done -->

Every issue named in Chains 1–15 was fetched with `gh issue view` rather than
read off this memo. **The narrative was broadly right; the diagrams were not.**

Open, re-queried: llm-distillery **38** · NexusMind **43** · ovr.news **89** ·
FluxusSource **14** · persuasion-scorer **12** = **196**. One below the
morning's 197 because **ovr#303 closed after that count was taken** — the
ordering section's own text already records the closure, so the number and the
prose disagreed by one. Sediment (untouched 30+ days) recounts to **82**, not
83: LD 12 · NM 22 · ovr 48 · FS 0 · ps 0.

### Two links were marked ✅ while OPEN

| Link | Marked | Actual | Verdict |
|---|---|---|---|
| **LD#73** (Chain 2 head) | ✅ | **OPEN**, untouched since 2026-07-28 | **Bookkeeping — closable as done.** |
| **NM#185** (Chain 1) | ✅ | **OPEN**, untouched since 2026-07-27 | **NOT bookkeeping — it carries an unstarted half.** |

**LD#73 is closable.** The deliverable shipped under a different name:
`filters/common/violence_promotion/v1/` exists in this checkout, LD#73's own
2026-07-28 comment records the shadow deploy (OOF precision 0.936 / recall 0.550
@ 0.95), and its one blocking design question — *"confirm ADR-004 stamp-only
before training"* — was answered stamp-only. Its downstream **NM#274 is
closed**, which is how a head issue outlived the chain hanging off it.

**NM#185 is not.** It bundles two filters and only one of them shipped:

- *Obituary blocker* — done, enforcing at v5@0.85, verified live.
- *Commerce prefilter v3 retrain* — **never started.**
  `filters/common/commerce_prefilter/` holds **v1 and v2 only**, and v1 is the
  force-pinned one (LD#80) precisely because v2 underperformed on production
  traffic. There is no v3 and no training run.

So **Chain 1 is not "complete except one cosmetic link."** And the commerce
half's evidence has decayed underneath it: the 2026-06-25 reader-flag audit
inside NM#185 found the miss set was **100% scored by
`sustainability_technology`** — a filter **deleted 2026-08-03**. Whatever v3
should catch has to be re-measured against `solutions v6`, which absorbed that
content. That re-measurement is the actual next step, not a training run.

**Consequence for ovr#204:** its title reads *"Remove hardcoded obituary
detection (after NexusMind#185 ships)"*. That dependency **is satisfied for the
obituary half** — enforcement has been live since 07-30 — so ovr#204 is
actionable today. But a reader of either issue would conclude it is blocked.
This is the topology rule's failure mode inverted: one issue holding two
filters means neither can be closed and the dependency it advertises is
unreadable.

### Coverage hole: persuasion-scorer is counted but never banded

All **12** of `veen-systems/persuasion-scorer`'s open issues appear in **no
chain, no P0–P4 band, and no row of the Coverage table** — which enumerates
unbanded issues for the other four repos and lists none for this one. They are
counted in every total on this board and sequenced nowhere. All were last
touched **2026-08-02**, so they are not sediment; they are a stalled block.
Banded below.

### Diagrams carrying closed links

The prose records these closures, the ASCII chains did not: **ovr#295** (closed
08-06, drawn as a live Chain 9 link) and **FS#128** (closed 08-06, drawn as a
live Chain 14 link). Both struck below. Still **mentioned but placed in no
chain**: **ovr#301** (Chain 7 material), **FS#127**, **FS#132**.

### Acted on the same day — four issues closed, two comments filed

| Issue | Action |
|---|---|
| **LD#73** | **CLOSED done.** Deliverable shipped as `violence_promotion v1`; ADR-004 stamp-only question resolved. Remaining work is LD#82 + NM#286 item 3, which are already banded. |
| **LD#97** | **CLOSED.** All three questions discharged; appendix committed `0cc3382`, remedy `d558a40`. Live remainder is ovr-side and operational (schedule the scan, fix the 117 fail-open errors). |
| **NM#204** | **CLOSED superseded** by shipped `solutions v6`. Untouched since 2026-05-11. |
| **NM#185** | **Comment filed.** Not closable — the commerce v3 half is real, unstarted work. Recommended splitting it out so ovr#204's dependency reads true, and re-measuring before any training run. |
| **ovr#204** | **Comment filed** — not blocked; the half it depends on shipped 5 weeks ago. |

**Board after: LD 36 · NM 42 · ovr 89 · FS 14 · ps 12 = 193, plus a sixth repo.**

### Sixth repo on the board: veen-systems/pipeline-atlas

Created 2026-08-07. The whole-chain architecture site, written as a signal path,
replacing ovr.news's hand-maintained `/ops/architecture` (deleted, ovr `83e0b7c`).
Two open issues: **#1** fill the eight stage stubs, **#2** cross-link it from the
four repos it describes and decide whether their own `ARCHITECTURE.md` files
should shrink.

Served from **sadalsuud on Tailscale** (`http://100.78.93.76:8099/`), not GitHub
Pages — `veen-systems` is on the free plan, where Pages serves public repos only,
and the site carries internal host names and a defect inventory. Unit files live
in the repo under `ops/`, not only in `/etc`, which is the thing FS#105 is open
about.

**Why it exists, in one line:** eight partial architecture documents across four
repos, no whole-chain view, and at least two of the eight were found stating
things that were no longer true.

### Two issues confirmed closable

- **LD#97** — the ordering section says "looks closable"; verified it is. All
  three questions discharged: **zero of the 333 opted-out domains carry a
  `User-agent: *` reservation**; the Q2 remedy shipped (`d558a40`, 834 rows /
  1,889,627 chars truncated); the appendix is committed (`0cc3382`).
- **NM#204** ("scope a dedicated solutions lens") — superseded by shipped
  `solutions v6`. Chain 5 already says "closable as superseded"; nothing has
  changed since, and it has not been touched since 2026-05-11.

### Method note

The two ✅-but-open links were found by fetching state per issue rather than
trusting the diagram, and the substantive one (NM#185) was invisible from the
issue's *title* — it reads as an obituary issue. **A chain link whose ✅ was
earned by one half of a bundled issue looks identical to a finished one.** The
generalisation for this board: mark chain links against *deliverables*, not
against issues, whenever one issue carries two.

---

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
   ↔ gotcha-log 2026-07-30 cross-box skew |0.16| — same magnitude, different cause
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
FS#124 (mojibake at collection, 5.0%, non-English-concentrated)
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
FS#124's collection defect is fixed (verified 0.00% on the first run after
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
| ~~**FS#124**~~ | FluxusSource | UTF-8→MacRoman mojibake | **FIXED `ea25ae8`, verified not assumed**: 0.60–2.38%/run before, **0.00%** on the first run after, 0.78/run since. Residual ~5/day is publisher-caused and deliberately not repaired. Chain 14's root is **NM#292**, not this. Stored rows still need **ovr#291**. |

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
> ovr#283 twice. See [Ordering 2026-08-07](#ordering-2026-08-07--re-queried-full-board).
> **All seven are now taken.** Item 7 was created by this session's own review and closed the same day.

- ~~**7. ovr.news's own corroboration boost**~~ — **DECIDED + SHIPPED
  2026-08-07** (`1ecf853`): **bounded to a flat 1.3× for 2–10 total sources,
  1.0× above**, matching NexusMind's shape in `1bbadb5`. The ladder was removed
  rather than retuned because precision is **not monotone** in cluster size and
  no band beats the 2-source case (0.560). Subtractive by construction.
  `under-the-hood/ranking.astro` updated in the same commit — and while there,
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
