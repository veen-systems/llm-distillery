---
name: project_session_2026_08_13_evening
description: Contracts session — five repos in parallel; the estate has four contract validators and none watches the failure. Plan drafted and reviewed round 1. Nothing executed, nothing deployed.
metadata:
  type: project
---

# 2026-08-13 evening — the contracts session

**Assignment:** state of ovr, its feeding chain and this repo; then, scoped by the
owner, **contracts only**. Five sessions ran in parallel (llm-distillery,
FluxusSource, NexusMind, ovr.news, pipeline-atlas).

**NOTHING WAS EXECUTED, MERGED OR DEPLOYED — in any of the five repos.** No filter
package changed, no model, no config. The only writes are this repo's docs and
memory. No oracle spend.

## The finding

**The estate has four contract validators and none of them watches the thing that
broke.** Measurements, traps and the full table: `stamp-contract-integrity.md`
§ *The contracts layer*. Plan and round-1 review: `docs/CONTRACTS_PLAN.md`.

**The through-line, which is the durable output: greenness is not evidence that a
schema tracks reality.** Four independent demonstrations, so it is a pattern.
The strongest is runnable in ten seconds — Contract A declares
`format: "date-time"` on three timestamp fields, 99.4% of rows violate it, nobody
saw it because `jsonschema` does not assert `format` by default, **and passing
`FormatChecker()` still changes nothing without `rfc3339-validator` installed**.
The fix looks like a fix and turns nothing on.

## What is actually wrong with Contract A — and it was already filed

**NM#304 has had three of the four defects since 2026-08-08.** This session
re-derived them five days later and nearly presented them as a discovery. The
honest framing is *confirmed still live and quantified on current data*, which
five days on nobody knew.

## My errors — seven, all caught, none by me alone

Recorded because the pattern is more useful than the items.

1. **The headline premise was false.** "Nothing anywhere runs a consumer schema
   against real producer bytes." ovr.news has done exactly that since
   2026-03-03. **I grepped for one script name, not for the behaviour** — the
   error this plan exists to fix, committed while writing the plan. A follow-up
   sweep then found two more validators in a `NexusMind/validate/` directory I had
   never opened.
2. **A hand-built population, again.** Attributed `priority: 9` to
   `youtube_channels.yaml` / `vimeo_channels.yaml` by grepping configs. Those
   files **emit nothing**; all 2,774 rows are `source_type: rss` across 107
   mainstream feeds. I chose a population instead of measuring one, in a contracts
   audit.
3. **Read a tool's output as rows when it counts errors.** "1,195 rows missing
   `word_count`" was 1,195 *errors* across 928 rows over *two* fields.
4. **Proposed deleting 7 zero-reader fields.** The owner's correction —
   `source_category` had zero readers for months *because* it was undeclared —
   inverted it to *declare more, cut nothing*.
5. **Proposed declaring `language` as BCP 47** — a wider-than-emitted declaration,
   the identical defect to Contract A's `email`/`web`/`patent`, arrived at from
   the opposite direction, while writing that defect up as the problem.
6. **Proposed nesting the language diagnostics.** Two of the five are *inputs*
   read by the producer to make the decision, so nesting inverts the dataflow —
   and would have relabelled `language_hint`, the exact trap it aimed to fix.
7. **Reported `metadata.hashes` as a defect** (it is declared optional) and
   **"34 keys declared by neither" as a violation surface** (Contract A's
   `metadata` is open).

**Peers made errors of the same shape and retracted them the same way** — NexusMind
inferred the `_get_priority` collision from a docstring and measured it away;
ovr's "70 sort inversions" was their own host-TZ artefact, i.e. the defect under
discussion; FluxusSource inherited FS#164's rationale from a CLAUDE.md instead of
checking it. **The recurring shape across all five sessions: a claim inherited or
inferred rather than measured.**

## Two decisions with the right outcome and the wrong reason on record

Same shape twice in one plan, which is why it is worth naming:

1. **FluxusSource#164** keeps ~8 months of archives on the stated grounds that
   *"llm-distillery trains on this depth."* **We do not read `data/archived/` at
   all** — we train on point-in-time copies of raw ingest. The retention is right
   for a reason recorded in *this* repo (`docs/TODO.md`): it is the only surviving
   copy of a displaced body, hence NM#306's only repair path. **Correct the
   reason, keep the retention.** Do not propose a retention change — deletion is
   irreversible and 1.2 GB is cheap.
2. **ovr's `WebPage`-not-`NewsArticle`** was cited as closing the schema.org
   question. It is a choice of type *within* schema.org made while **adopting**
   it — as evidence about vocabulary it points the other way. The scope call
   stands on other grounds; the justification does not.

## Live findings, not contracts

- **A live 2-hour defect at ovr.news.** ECMAScript reads a naive ISO date-time as
  local. `summarize.ts` runs on sadalsuud (**CEST**), so ~25 articles/day lose the
  `recencyBoost: 1.3` step two hours early — ranked ~30% below where they belong,
  **while Cloudflare ranks the same articles correctly**. The 0.6% of rows that
  carry an offset are read correctly, so ovr's corpus is internally inconsistent.
- **The Cloudflare build host is UTC** — measured by ovr without build-log access:
  RSS `pubDate` is build-host-computed, JSON-LD `datePublished` is the raw string,
  so their difference *is* the offset (8/8 zero shift). **Nothing pins that TZ**,
  so ovr's correctness rests on a Cloudflare default nobody chose.
- **Fixing the timestamps *creates* a hazard.** `'…+02:00' > '…T19:00:00'`
  lexicographically while being earlier in real time, across an index and ~20
  `ORDER BY published_date` sites; in `story-dedup.ts` it pushes genuine duplicate
  pairs outside the window so **both publish**. Hence new prerequisites W2.7 and
  W3.4, both of which draft 1's ordering missed.
- **The 16:04 cycle failed** (cd v6 cutover, reverted; v4/v5 only on both hosts,
  verified). Scoring recovered by hand — 17,383 rows. But **`OnSuccess=` cannot
  fire for a failed unit**, so that batch went unpublished until the next
  summarize. It self-heals because `readLocalArticles` globs every `*.jsonl`
  inside `ranking.maxAgeDays = 10` — checked mtime ordering across all six filter
  dirs for the newest-mtime-wins dedup, no inversion. **The recovery property
  lives in a window on the consumer, not in the clocking**: two independently-owned
  numbers in two repos with no declared relationship.

## Next session

1. **Spec the result artefact** — path, timestamp, per-defect-class counts,
   version stamp. **Blocking pipeline-atlas**, who can then write the snapshot
   reader before the check exists. Smallest useful thing.
2. **Re-run the hand-rolled-validator sweep across all 20 `veen-systems/` repos**
   before any of this reaches the atlas. Two were missed; assume more.
3. **Round 2** — peers have not re-reviewed the corrected premise.
4. **Owner decisions 1, 2, 4** in `docs/CONTRACTS_PLAN.md` remain open (the
   envelope; its additive path; `eval_query`).
5. Unrelated and untouched: **cd v6 is fixed (`dcf2860`) and NOT redeployed** —
   guard D blocks it, correctly.
