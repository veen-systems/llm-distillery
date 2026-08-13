# Session record — 2026-08-12 (late / fifth context)

**Shape of the session: cross-repo coordination as the assignment, four sessions in
parallel, and every quantitative claim any of us made failed under checking.**
Nothing deployed, no oracle spend, no model weights touched. 17 files changed
(15 modified, 2 new), 335 tests passing.

---

## The primary finding, and it is not a number

**Every quantitative claim made by any of the four sessions failed under checking —
and not one failed where its author was looking.**

Catalogue, mine and the peers' alike:

- A stage-mix figure retracted because `stage_used` is **per-filter, not
  per-article** (82% of rows disagree across filters) — found by its author
  auditing their own assumption, *not* by the adversarial lens aimed at it.
- My Google News mechanism claim over-generalized from one fetcher to the URL
  scheme — refuted by a repo nobody thought to ask, **after** it had propagated
  into that repo's issue as a premise.
- An op-point resolver that returned `None` and printed `visible% = 0.0` for every
  cohort — caught only because all-zero was implausible.
- "ADR-022 does not exist", produced by running `ls docs/adr/` **in the wrong
  repo**, where a populated directory made the wrong answer look right.
- A survival rate whose numerator and denominator had **different exclusion lists**.
- A counterfactual replay over stored rows presented as an observed attrition rate.

**In every case the object checked and the object that was wrong were different
objects**, so no amount of care applied to the first could reach the second.

**And the structure underneath: every single error was a hand-built population.**
Someone chose a file, a window, a join key or a directory, and the *choice* carried
the defect while attention went to the arithmetic. NexusMind's scorer already logs
`Loaded 4577 articles (skipped: 114464 processed, 17845 commerce, 3232 obituary,
22472 dup-url, 3442 dup-title, 140870 old …)` every cycle — the aggregate decomposed
by mechanism, thrown away. **The one artefact nobody got wrong was the log line,
because nobody built it.**

Corollary worth keeping: **an outside reviewer is only one way to make the checker
and the checked different objects, and it was not the way that caught either of the
two errors that mattered most.** Auditing your own assumption list arranges it too,
and cheaper.

---

## NexusMind#292 largely dissolved — a real result, not a deflation

#292 claimed non-English content is disadvantaged at four compounding stages. After
four sessions measured their own stage and one adversarial lens attacked the
instrument:

| stage | verdict |
|---|---|
| **gating** (our #86) | **COUNTERFACTUAL** — the per-filter prefilters have never run in production (NM#284, dead since 2026-02-10). The gate has never fired. Also stale: `80dd399` (2026-08-06) took the ratio 1.56× → 1.19×, z 5.02 → 1.75, and closing #99's English-only `DISCOVERY_PATTERNS` back door **reverses the sign** (English blocks at ~22%, above non-English) |
| **collection** (FS#124) | ⚠️ **"HISTORICAL" RETRACTED SAME DAY — see below.** FluxusSource's `ea25ae8` holds **unqualified** (0.000%, and their zero survived a three-round challenge), but the defect **RELOCATED into NexusMind's enricher** and kept its non-English skew — **NM#338 v3: 4.655% introduced, 7.429% non-English, 5.68× skew.** The limb is LIVE, at a different stage, in a different repo |
| **scoring** (NM#231) | observed but **filter-dependent and both-signed** |
| **dedup** (NM#291) | live — but see the split below |

**Replaced by a bigger, live collection-stage fact (FluxusSource#166):** across
51,640 emissions, `ar` **3** rows, `hi` **2**, `fa` **1**, `ta` **1**. Asian, African
and MENA publishers are acquired in their **English editions** (196 English : 38
native) while European publishers are acquired natively (25 : 288). ~97% of emissions
are English or European. **So the "non-English" arm in every number any of us
computed is European-language content**, and a language-stratified rate partly
measures *source acquisition*, not downstream treatment. It is upstream of every
stage and **no downstream threshold can recover it.**

**On the corrected criterion the direction inverts.** Measured on
`raw_weighted_average >= each filter's own op-point` (what production uses; the probe
had used normalized ≥ 4.0), non-English is **visible 10.0pp MORE often**, sign-stable
across 8 cohorts, sd 3.4, control −0.10 — and it survives including
`cultural_discovery`, the filter most likely to run the other way.

---

## Dedup and corroboration are NOT one finding (owner correction)

I told NexusMind the survival and corroboration effects were "one finding measured
twice". **Wrong, and the owner caught it.** They share one cause — story clustering —
but they are different products of it:

- **Dedup** decides whether an article *survives*. Non-English survives **more** (it
  has fewer same-language siblings to be deduped against). Benign, arguably good.
- **Corroboration** decides what a reader is *told about a story's standing*, and
  feeds `display_rank` via a bounded boost live since 2026-08-06
  (`NexusMind/src/scoring/display_ranking.py:95-138`). Non-English is credited
  **less** (#291: threshold 0.88 vs cross-language pairs at 0.836). **This is the
  harm.**

**One cause, two effects, only one of them a harm.** And the evidence inverts
awkwardly: the *survival* gap is sign-stable across cycles, while the *corroboration*
gap is 4.2pp raw and **1.3pp conditioned on stage2 — inside the ~7pp single-cycle
noise band** (two independent constructions agreed: sd 6.2 and sd 7.1). Two of six
NexusMind cycles reversed it outright.

**So the arm that matters cannot yet be demonstrated, and the arm that can be
demonstrated is not a harm.** Prioritisation note: a language gap in corroboration
sits on top of a feature at **precision 0.283** (NM#301) that is already boosting
ranking. #301 is larger, reader-facing and language-independent.

---

## My own errors, and what they cost

**1. The Google News over-generalization — the one that travelled.** The measurement
("NexusMind's `pre_enrich` attempted 35,229 GN rows, replaced zero") is right. The
absolute attached to it — *"a property of the URL scheme, so no fetcher change moves
it"* — was scoped to one fetcher and stated of the scheme. **ovr.news resolves these
URLs** via Google's private `batchexecute` (`src/lib/google-news.ts:43,106-107`) and
enriched **74 of 103**, most recent success the same morning. It had already
propagated into **ovr#312 line 20** as a premise about a different resolver, and it
licensed a *"don't fix the GN resolver"* recommendation that would have retired a
capability carrying **22 of 38** published articles. Corrected in six files.

**2. "Documentation only" — I found one reader and stopped.** Adding a `tiers:` block
to `cultural_discovery` config is **not** inert: **eight** llm-distillery tools read
`scoring.tiers`. `training/prepare_data.py` flips `use_score_bins` False, so a future
retrain's splits stratify by **tier** instead of score bins. The normalization fit
floor is unchanged (4.0 both ways) — but on `nature_recovery` (3.75),
`investment_risk` (4.25), `uplifting` (4.5) or `solutions` (2.25) the same edit would
**move the ADR-021 gate threshold**.

**3. "The deploy and the cutover are the same keystroke" — false, and I put it in a
🛑 block.** `NexusMind/scripts/deploy_filters.sh` sits between the checkout and
gpu-server: `git archive HEAD`, hard-exits on uncommitted/untracked scorer files,
rsyncs, restarts. Our own `docs/FILTER_PLAYBOOK.md` documents the chain **three lines
below the section I cited**. What *is* true and worth keeping: there is **no
version-selection step** — `_find_latest_version()` serves the highest `vN`, so
nothing ever names a version and there is no activation step to forget.

**4. My guards shipped with three defects of their own**, all found by the review
battery: a documented `.ps1` deploy path bypassed them entirely; a regex silently took
the *first* of multiple `TIER_THRESHOLDS` blocks where this repo's own
`fit_normalization.py` already uses AST and fails closed; and guard C could not abort
— deploying *below* the highest version printed a note, exited 0, and let the script
commit and push a provable no-op.

**The pattern a peer named, which I would not have seen: on both corrected claims the
stale copy sat closer to the reader than the correction did** — `CLAUDE.md`'s routing
row before the hypotheses file; a `CONFIRMED` heading 17 lines above its own
`REFUTED` block.

---

## Shipped

**Deploy pre-flight guards** (`scripts/deployment/preflight_deploy_guards.py`, 34
tests), wired as Step 0.5 of **both** `deploy_to_nexusmind.sh` and `.ps1`, before the
`cp -r` so it can abort:

- **A — manifest scope.** `.nexusmind-owns` cannot protect per-filter files; an entry
  naming one is accepted and does nothing. Now an allowlist (`^filters/common/.+`)
  that also rejects Windows separators and `./` prefixes the consumer rejects.
- **B — tiers documented.** AST-parsed, collects *every* `TIER_THRESHOLDS` and fails
  on disagreement; compares tier **key sets** before values.
- **C — cutover.** Warns when a deploy starts a version cutover; **aborts** when the
  version is below NexusMind's highest, or `NEXUSMIND_ROOT` does not exist.

Each guard proven to fire on the real historical defect and stay quiet on the healthy
case. All 7 shipped packages pass with correct op-points.

**`cultural_discovery` v5 and v6 both gained `tiers:` blocks** (7.0/4.0/0.0, matching
`base_scorer.py`; no threshold moved). They were the only two without. Removing the
now-stale exemption from `test_filter_config_schema.py` was **required in the same
commit** by that file's own lockstep rule — and the exemption's comment had reasoned
correctly about the runtime while being wrong about the cost.

**Framework adopted to v1.25.0** (was v1.23.0). 3 adopted / 0 declined / 1 n-a / 3
already in force. Notably: the v1.25.0 absolutes rule was adopted **on this repo's own
same-day evidence** rather than upstream's, and the gotcha log's "2–3 lines" rule was
withdrawn upstream *citing this log as the evidence* (203 entries, median ~1,200
chars, 35% >1,500).

**H-E1 resolved** — see `memory/enrichment-delta-hypotheses.md` and #71.
`nature_recovery`'s +0.023 aggregate is a **cancellation**: five dimensions up,
`protection_durability` **−0.173** (24 of 48 down). The finding that travels:
**enrichment's dominant effect is on evidence-quality-type dimensions**
(`cultural_discovery`'s `evidence_quality` **+1.433**, 46 of 47 rows positive), and
`nature_recovery v4` has no evidence dimension.

**#109 Arm B gap 1 closed** — judges named (**Qwen3:14b + Phi4:14b**, local,
non-Gemini, **$0** on b650), both-must-agree, per-judge planted-error gate first. Cost
was never the blocker; the default judge having *made* the labels was.

**#108 retitled** — the "de-facto language filter" reading is **not established**,
because three stages measure length on different text and nobody had named the stage.

---

## Then `/audit-context` — and its own instrument was the thing that broke

Monthly structural pass, run after the curate commit. Six findings, all fixed
(`fad38af`). Two outcomes worth carrying:

**The reference checker's loosening had to be tested on what it PERMITS.** Porting
v1.23.0's `<!-- placeholder -->` skip passed the existing harness **12/12
immediately**, which read as a safety proof and was not one — a harness written
before a change can only test what the change preserves. Seeding the newly-permitted
failures found **two defects in the port**: `PATH_RE` did not admit `<`/`>`, so
angle-bracket placeholders were **never extracted** ("not reported" silently meaning
"never checked"); and the stale-marker check tested the bracketed string, so a real
path wrapped in `<>` skipped instead of being flagged as a mislabel. Harness
12/12 → **18/18**. Logged as its own gotcha entry.

**A straight swap of a shared instrument was a regression.** Upstream's `refcheck.py`
is 365 lines to our adapted 172 — but ours carries a *generic-artifact-name* class
upstream lacks, and the swap re-reported 33 `config.yaml` matches as collisions.
Reverted; the feature was **ported into our copy** instead. Newer is not the same as
better when the local copy encodes local knowledge.

Also: references 18 → **7** (the remainder are correct — 2 genuine collisions and 1
ambiguous cross-repo `main.py`; **zero is not the target**), `CLAUDE.md` 38,743 →
**34,658** chars with the working rules' *evidence* moved to
`memory/working-rules.md` while the imperatives stayed (they were deliberately
promoted into the project file and moving them wholesale would reverse that),
duplicated numbers 7 → 3, and one orphaned topic file
(`memory/enrichment-delta-hypotheses.md` — today's own H-E1 result, which no session
would have loaded).

## Two same-day retractions arriving after this record was written

**1. NM#338 — the collection limb of #292 was NOT fixed; it RELOCATED into
NexusMind's enricher, and kept its non-English skew.** FluxusSource's `ea25ae8`
holds (**0 / 23,638** in their text). But `NexusMind/src/enrichment/article_fetcher.py:291`
does `.decode(resp.encoding or "utf-8", errors="replace")`, and in `requests` a
`text/*` response with **no declared charset** gets `resp.encoding = "ISO-8859-1"`,
not `None` — so the `or "utf-8"` guard is **dead code** and UTF-8 pages decode as
Latin-1.

⚠️ **The figures went through THREE revisions in one evening. Use v3 — the first two
are superseded:**

```
                        v1        v2 (derived)   v3 (cp1252+latin-1)  <- USE THIS
introduced by NexusMind 4.751%    5.639%         4.655%
non-English rate        7.448%    9.202%         7.429%
skew                    5.91x     6.86x          5.68x
BEFORE (FluxusSource)   0.000%    0.081%         0.000%   <- their zero SURVIVED
```

**The relocation finding is unaffected** — it was never a threshold question — and
FluxusSource's `ea25ae8` stands **unqualified**. The v2 "FluxusSource is at 0.081%"
figure, which I relayed to them, is **withdrawn**: all 21 rows were false positives of
the peer's mac_roman arm (`el` 19, `fr` 1, `vi` 1), and all 21 were **also dirty in
`data/raw` as received**, which independently rules out "introduced by NexusMind's
ingestion". Windows, verified here: `«π`→`ǹ` ×19, `«à`→`ǈ`, `‘ô`→`ԙ` — **punctuation
followed by a letter, i.e. ordinary prose.** The peer dropped the mac_roman arm
entirely rather than patch it, on the grounds that it cannot separate prose
punctuation from corruption without a signature stage.

**The finding that outranks the numbers: deriving the character class fixed coverage
on the arm they were blind to (cp1252) and SIMULTANEOUSLY manufactured false positives
on the arm they thought they had fixed (mac_roman).** Their hand-written v1 was roughly
right *by accident* — a narrow class costs coverage *and* buys precision, and nobody
had noticed it was doing both. So "derive, don't hand-write" is a **coverage** fix and
never a discriminator.

**My prediction was right in family, wrong in specifics.** I said punctuation
immediately before an *accented vowel*, and guessed French/Italian/Belgian/Swiss. It is
punctuation before a *letter*; the characters are `«` `“` `‘` and NBSP, not `’`; the
languages are Greek, Portuguese, Spanish. `’` was **one member of a family neither of
us had enumerated**, and naming the wrong member made a correct hypothesis look weaker
than it was — my own top-5-sources check cut *against* the reading that turned out to
be right.


⚠️ **RETRACT the "FluxusSource is clean at 0.000%" figure — I routed it onward as
"the cleanest evidence anyone produced for `ea25ae8`".** With the corrected detector
it is **21 rows / 0.081%**, not zero. It does not change who introduced the other
1,466 and it does not weaken the relocation finding, but it was stated more strongly
than the evidence now supports.

**How it was found, and this is the part worth keeping.** I queried a **6-row
denominator gap** (10,312 + 13,332 = 23,644 against a stated 23,638) during
`/review-changes`. Pulling that thread found **three** defects, none visible in the
number itself:

1. **A sliding `[-N:]` glob is not a fixed population.** The total and the split were
   separate invocations minutes apart; new cycle files landed in between, so the two
   commands measured two different file sets. *That* was the 6 rows.
2. **`sorted(glob("data/filtered/*/filtered_*.jsonl"))[-40:]` sorts by PATH**, which
   groups by filter directory — so it selected **40 `uplifting` files and nothing
   else**, not "the last 40 cycles". Sort by basename for a cross-lens window.
3. **The detector was blind to 83% of the population.** Its continuation class was
   hand-written as `U+0080-U+00BF` — correct for latin-1, which renders bytes
   `80-9F` as C1 controls, but **cp1252 renders those same bytes as printable
   punctuation** (`U+2019`, `U+20AC`, `U+201C`), so every smart-quote corruption
   (`donâ€™t`) was invisible. ovr.news hit the identical hole from the other side the
   same day.

**The generalisation, which is the peer's and is better than my own entry:
hand-built populations and hand-built character classes are the same failure with
different nouns.** The fix is not a *wider* class but a **derived** one —
`bytes(range(0x80,0xC0)).decode(codec)` **is** the continuation set, by construction,
so it cannot drift from the codec it models. Concentrated in
`baltic_lrt` 432, `romanian_adevarul` 100, `balkan_nova_rs` 96, `polish_polsat` 85.

**So "collection is historical, reattribute to FS#166" is retracted.** FS#166 (the
source-acquisition gap) stands on its own; the mojibake limb is **live again at a
different stage**. The generalisable rule, which neither repo's fix covers:
**never trust `requests`' charset default — hand raw bytes to the parser and let it
read `<meta charset>`.**

**2. The *"should ovr.news enrich at all?"* decision is CLOSED (owner, 2026-08-12):
enrichment moves upstream.** ovr deletes its pass; NexusMind's `pre_enrich` becomes
the single enrichment point (NM#339). The GN resolver is **explicitly not ported** —
Google News is being retired, so that half dies with the source.

⚠️ **And this is the part to learn from, because I got the withdrawal wrong.** I
recommended *"don't fix the GN resolver — it is a workaround for a source under
retirement"*, then **withdrew the whole recommendation** when the peer refuted the
mechanism claim I had attached to it (*"no fetcher change moves it"* — false, ovr
resolves 74 of 103). The mechanism claim deserved withdrawing. **The recommendation
did not: it never rested on that claim**, it rested on the retirement, and the owner
has now decided exactly that. **When a supporting claim is refuted, check whether the
conclusion actually stood on it before retracting the conclusion too** — I conceded a
correct call because a neighbouring sentence of mine was wrong.

The structural argument that decided it was one neither side had stated: **ovr's pass
is the only enrichment in the chain that cannot RESCORE**, because ovr has no scorer.
NexusMind's `enrich_articles` enriches *and* re-scores. So the ordering problem was
never "enrichment happens downstream of scoring" — it was "one specific pass changes
the text without redoing the decision".

Also worth carrying: the four "correctly refused" cases I reported from the 68-id
lookup (Mediapart cookie wall, West Australian paywall, France24 video block, Globe &
Mail under the floor) **did more work in that decision than the 38-article headline
did** — ovr "succeeded" on all four only because it accepts any text longer than what
it had, with no consent-wall detector and no minimum-gain check.

## The owner's ruling that retired most of the evening's work (2026-08-13)

*"The fix isn't 'move enrichment upstream'. Repairment should not be necessary. If it
is, there are bugs upstream."*

**Correct, and it dissolves the FS#167 thread rather than mitigating it.** Four
sessions spent hours making a *repairer* safe — candidate classes, arm independence,
a pair requirement, a signature conjunction, a hand-review residue. All of that exists
because a repairer must **guess** which strings were corrupted, and the guess is where
the 2,030 false-positive pairs live.

**Nobody asked whether the guess was necessary.** A clean copy of every corrupted row
sits one hop upstream: NexusMind stores `original_content` per article
(`article_fetcher.py:840`), FluxusSource's text, 0.000% corrupt through a three-round
challenge. **Re-derivation has no false-positive class**, because nothing is inferred.

Two conditions checked before accepting it:

- **NM#338 is already fixed** — raw bytes to trafilatura — so the corrupted set is
  **bounded and no longer growing**, which is what makes re-derivation terminate rather
  than become a treadmill.
- **U+FFFD is the one damage class re-derivation is the ONLY cure for** (mojibake is a
  reversible mis-decode; U+FFFD threw the bytes away). My mechanism claim that ovr's
  `response.text()` decodes UTF-8 regardless of declared charset was **right and I
  flagged it as unmeasured** — measured by ovr: **4 of 21,316 rows, 0 of 160 cache
  rows.** Near-empty, but it was the single finding that could have made re-derivation
  insufficient.

ovr#291 is now *"re-derive from upstream"*, with the repairer spec retained as the
**verification** spec. Same instrument; a false positive now costs a second look
instead of a destroyed row.

**And a risk in a decision I had already agreed to.** NM#339 routes **all** enrichment
through NexusMind's decoder — the one that had the charset bug when the decision was
made. Nobody checked it first; it held **by luck of timing**. Now posted to NM#339 as
an explicit precondition. ovr's addition is the durable half and is better than my
framing: **the redundancy being removed was also, incidentally, error-detection.**
NM#338 was found by pairing against a second copy. Remove the second path and the same
fault reaches everything with nothing positioned to notice — so it wants a *standing*
probe, not a one-time check. The U+FFFD count is the cheap one: it is 4, and 4 is
exactly what moves if the surviving decoder regresses.

## Verify

<!-- verify: test -f scripts/deployment/preflight_deploy_guards.py && PYTHONPATH=. python3 -m pytest tests/unit/test_preflight_deploy_guards.py -q 2>&1 | tail -1 -->
<!-- verify: grep -c preflight_deploy_guards scripts/deploy_to_nexusmind.sh scripts/deploy_to_nexusmind.ps1 -->
<!-- verify: PYTHONPATH=. python3 -c "import yaml;print(yaml.safe_load(open('filters/cultural_discovery/v6/config.yaml'))['scoring']['tiers']['medium']['threshold'])" -->
<!-- verify: grep -q "framework: agent-ready-projects v1.25.0" CLAUDE.md && echo PASS || { echo FAIL; exit 1; } -->

## Carries

- [[feedback-claim-requires-verify]] — an **endorsement** is a claim too; praising a
  peer's number suppresses the re-check that would have caught it.
- **Name the population, not just the number.** The measurement had one; the
  generalization dropped it.
- **An instrument chosen to avoid a known bias is not thereby unbiased** (FS#167:
  2,030 firing pairs, and *no validated fix exists* — ovr#291 cannot be safely run).
- **A characterisation of a defect inherits the shape of the sample it was found in,
  and reads as complete regardless.**
