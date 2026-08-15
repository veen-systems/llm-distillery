# Session 2026-08-14 late → 2026-08-15 — two hypotheses closed, four retractions, nothing deployed

**Assignment:** pick up the Contract A savepoint. **Outcome: no filter package was
touched, nothing was deployed, no spend.** Eight commits, all findings and
documentation, `041cc10` → `24d5ff2`, pushed to `main`.

⚠️ **Three of the savepoint's own claims were stale.** That is the headline process
fact: the brief was written hours earlier by sessions that then kept working.

---

## H-D2 CLOSED — the 6h gap spike is arXiv, walking with the collection timer

The open question was a flat contradiction: NexusMind measured a **6.00h spike on
13.99% of 7,478 rows**; FluxusSource found **no 6h spike at all** in 152,422 rows. Both
sessions had deliberately deferred the discriminating measurement for a day.

**It cost four `ssh` reads.** Condition the gap on `source`.

- The 7,478 population is **exactly two NexusMind raw deliveries** (3,835 + 3,643).
  Re-running the bins on those two files reproduces the recorded table **digit for
  digit** — 6.0 → 1,046 / 13.99%, 10.0 → 237, 2.0 → 236. Same instrument, same bytes.
- **974 of the 1,046 rows in the 6.0 bin (93.1%) are arXiv**, each source 100% of its
  rows in the file, 983 sharing one `published_date`: `2026-08-14T04:00`.
- **The gap walks with the timer**: 14.08h → 2.06h → 6.12h → 10.10h across four
  consecutive deliveries, **+4h each**. arXiv publishes at a fixed instant, so the gap
  only measures how long ago that was when the collector ran.

**Two windows photographing one phenomenon at different phases.** FluxusSource's own
*"the 11h spike is 84% `science_arxiv_cs`"* was the same batch at their cadence.

⚠️ **"6.00h" was never a whole-hour spike** — real gaps ran 5.875–6.124, and only 5 of
1,046 sat within ±72s of 6.00. **A round number in a binned histogram is a property of
the bins.**

### The dangerous half — the artifact passes through 2h once a day

That is the `now − 2h` fabrication signature's own bin. **And the coincidence is
scheduled**: arXiv announces 04:00 UTC, the timer fires 06:00 UTC (08:00 Amsterdam,
FS#132) — exactly 2h, six ticks a day. The only separator is **how long a run takes to
reach that aggregator**: 216s in my delivery, **452s** in FluxusSource's.

⭐ **Two different margins is the finding.** A separation that changes between runs is
not a property of arXiv or of the fabrication — it is latency, and nothing fixes it.

---

## The 2h bin has THREE contributors, and a fourth mechanism hides a FALSE NEGATIVE

| mechanism | how it makes ~2h | status |
|---|---|---|
| fabrication | `extract_date_from_rss_entry:106` writes `now − 2h` | the defect (FS#173) |
| fixed announcement | arXiv 04:00 UTC vs the 06:00 UTC tick | benign (H-D2) |
| local-clock `collected_date` | 8 of 768 sources stamp local, **+2.00h** | **FS#176** |

⭐ **`DateParser.ensure_valid_date:217` is a SECOND fabrication site**, serving the
`news_api`/`github`/`academic`/`patent` aggregators — several of which are the skewed
ones. Fabricated-in-UTC **plus** collected-on-local-clock ⇒ **`gap = 4h`, two hours
outside FS#173's detection window.**

**Verified independently: 46 rows at `4h ± 5s` over 155,513; 32 `semantic_scholar`;
32/32 carrying microseconds** on `published_date`, published and collected agreeing to
~35µs — *one instant stamped from two clocks*:

```
published=2026-08-09T12:04:32.536201
collected=2026-08-09T16:04:32.536236
```

⇒ **FS#173 undercounts fabrication.** A detector keyed on a fixed gap is keyed on the
**producer's clock** — a new constant per aggregator, **and another after every DST
transition** (4h in CEST, 3h in CET). Strongest argument yet for stamping at the point
of fabrication.

⚠️ **STANDING DATA RULE, no backfill coming:** `collected_date` is on the host local
clock (**+2h CEST**) for `newsapi_general`, `github`, `hackernews`, `stackoverflow`,
`ourworldindata`, NASA APOD and two Dev.to author-named sources. The other ~760 are
UTC; `published_date` is unaffected. In `data/current/` **and** the archives. Recorded
in [[nexusmind-data-sources]].

---

## #114 opened — the 300-char floor's rationale has never been measured

Asked whether to start implementing. **Answer for this repo: not yet**, and the reason
outvalued the code.

The only implementable item was the `#93` consumer of `content_meta.kind`. Two blocks:
`kind` is emitted on **0 of 14,409** production rows (dead code with green tests), and
**the floor's premise is unmeasured.** *"Short articles make the oracle analyse the
evaluation framework"* appears in `batch_scorer.py:146`, in #93 and in the hypothesis
file — **and nowhere as a measurement.** Load-bearing for a year.

It matters because retiring the floor on `kind` assumes the floor was about
*completeness*. **Leakage is a function of how much text the oracle sees.** A 143-char
`feed_summary` still hands the oracle 143 chars. Confirmed with the producer: the whole
derivation is `'headline_only' if not body or body == title else 'feed_summary'` and
**never looks at length**; and they **do not truncate RSS bodies at all**, which
dissolves the truncation question **against** `kind` — truncation was never the risk,
**insufficiency** is.

⭐ **Three repos hold three views of why the floor exists and none has evidence** — ours
(length), Contract A's `kind` description (*"a guess the producer does not have to
make"*), and FluxusSource's schema, which ships **"Length was never the property being
measured"** into a machine-readable contract as a flat assertion about *our* rationale.

**Free natural experiment run, inconclusive.** `solutions v4` carries sub-300 labels
(911/10,297 trainval, 413/1,500 holdout). Short rows score lower and flatter — **not
leakage evidence**; that is what correct scoring of thin content looks like, and
leakage would predict drift toward the *middle*. Fully confounded with topicality.
Settling it needs a **paired** design ⇒ oracle spend ⇒ owner decision.

---

## Contract A: declared, emitting nothing, and `content_meta` disagrees three ways

**0 of ~20 declared fields emitted across 14,409 rows.** Everything declared is
optional, so the schema validates clean — **a check that examines nothing reports
success**, which is what the unbuilt canary would distinguish.

`content_meta` is `additionalProperties: false`, declaring exactly `echoes_title`,
`kind`, `truncated`:

1. ⛔ **`content_meta.error` is undeclared** — the producer emits it on derivation
   fault. **HARD VALIDATION FAILURE.** The path added so a fault stays *visible* is the
   path that turns a fault into a contract violation. **The only one that fails closed.**
2. 🔇 **`kind` has no `enum`** — description names four notions, producer emits two.
3. 🔇 **`echoes_title` is a split the producer collapsed** (`headline_only` fuses *empty*
   OR *echoes-title*). **The schema's model is the better one**, and both halves already
   exist in the producer's one line.

⭐ **`7bc20a0`'s deploy gate reads "not until NexusMind's envelope declaration merges."
It merged** — so the gate reads green while all three stand. **A gate written as "wait
for X to merge" tracks whether X happened, never whether the two shapes agree.**

### A gap in BOTH directions, only one on anyone's list

- **`source_group`** — emitted every row, **declared nowhere** (W2.2, blocked on canary).
- **`content_meta.truncated`** — **declared, no producer.** Its description
  (*"whether the **source** truncated the body… as opposed to the body simply being
  short"*) is a real distinction, unanswerable from a feed: detecting it needs the feed
  body compared against the full article, and full-text fetch lives downstream.
  **Declared against the wrong producer, not uselessly.** ⚠️ I first suggested deleting
  it, **before reading its description** — withdrawn.

**Neither is visible to a validator.**

---

## Category G — grain decision taken; it needed a decision, not an implementer

The savepoint called it "spec-ready and unassigned". `CONTRACTS_PLAN.md`'s own status
table said `⏸ spec needs the per-tier grain decision`. **The decision was already
written in § Round 3 and nobody had taken it.**

⭐ **The grain problem is not intrinsic to G — it arrived with four fields that were
never G's.** Move `health_state`/`raw_item_count`/`items_emitted` out to A–F; keep
`poll_interval_actual_h` (the only field that can expose FS#121); name `refusal_reason`
an aggregate; write `outcome` at the refusal site. **Now needs an implementer.**

---

## ⚠️ FOUR RETRACTIONS, all mine, all caught by a peer re-deriving

**This is the session's most important record.** Every one was caught because
FluxusSource **re-derived instead of adopting** — four times running. Nothing else
caught anything.

1. **"0 non-canonical across all three timestamp fields."** **Two of three fields were
   vacuous** (0/200 present), and a fourth I never checked was 88/88 dirty. The check
   incremented a violation counter and **never a presence counter**, so absent and clean
   produce identical output — `CLAUDE.md`'s own *"the validator counts errors, not
   rows"*, which I had quoted earlier the same session.
2. **"A latent false-positive collision at ~1.98h."** Wrong twice: the 1.98h was an
   artifact of comparing to the **run median** when NewsAPI *runs first* (true offset
   exactly 2h), and for a skewed producer `gap = true_age + 2h`, so a real article hits
   `2h ± 5s` only if under **5 seconds** old. The real interaction is the **false
   negative** above.
3. **"Delete `content_meta.truncated`."** Made **before reading the field's
   description**.
4. **"Our own code says otherwise"** on H-L1. `batch_scorer.py:146` **asserts** the
   rationale; it does not establish it. The honest state is **two candidate rationales,
   neither established** — conceded in both directions.

⭐ **And one instrument killed publicly.** Probing leakage by checking whether each
`evidence` string appears in the article read **76.0%/75.3% "ungrounded" on trainval
and 93.3%/89.6% on holdout** — essentially identical in both arms, because the oracle
paraphrases. **A number that does not move between treatment and control is measuring
the instrument.**

---

## Promoted patterns that RECURRED (the promotion did not take)

- **Unreachable mechanism** — twice more: the vacuous confirmation (*measurement* form)
  and the merge-gate that tracks an event rather than a property.
- **Establish what a source EXCLUDES** — the vacuous field check.
- **Every measurement error is a HAND-BUILT POPULATION** — twice: the run-median
  construction behind +1.98h, **and a `paste`-misaligned per-file table built during
  this very curate run**. ⚠️ **A promoted rule recurred inside the ritual that exists to
  track it.**

## Kept from peers

- **Grep for the VALUE, not the function.** FluxusSource cleared the fabrication/skew
  interaction on a disjointness argument and had already acted on it; it died to a
  **second call site** of the same fabricating function.
- **A glob that cannot match is indistinguishable from one still waiting** —
  `collection_202608092*` cannot match `collection_20260809_…` because the next
  character is `_`. Five days alive.

## Next session

1. **#114** needs a spend decision (paired oracle measurement).
2. **`CLAUDE.md` 37.4k vs 35k** — **0 recoverable padding bytes**, so content must go.
   `## Before You Start` is 28% of the file. ⚠️ **`memory/MEMORY.md` is 47.7k in 89
   lines** and is the bigger problem. Recommend `/audit-context`.
3. **Category G** needs an implementer, not a decision.
4. Not ours: the three `published.*` fields, the `kind` deploy, `clock_source`
   (FluxusSource); the canary (NexusMind).
