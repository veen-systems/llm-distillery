---
name: project_session_2026_08_07_late
description: Board coverage pass found a blocked prerequisite with four dependents; a six-lens review refuted my own NM#232 plan; FluxusSource cross-source dedup stamp shipped and deployed
metadata:
  type: project
---

# 2026-08-07 (late) — the plan that lost, and the drop nobody had counted

Third context on 2026-08-07. The previous two were the six owner decisions and
the chain re-verification / pipeline-atlas build. This one started as "investigate
open issues on the entire chain" and ended with a shipped instrument in a repo
nobody expected to touch.

## Board state: unchanged, so the value was in coverage, not counts

Re-queried: llm-distillery **36** · NexusMind **42** · ovr.news **89** ·
FluxusSource **14** · persuasion-scorer **12** · pipeline-atlas **2** = **195**,
sediment (untouched 30+ days) **81**. Nothing opened or closed since the previous
session's own closures, so the 08-07 ordering stands. What was worth finding was
what the board does not cover.

### 1. A blocked prerequisite with four dependents, modelled by no chain

- **FluxusSource#85** (NER at ingest) is CLOSED `NOT_PLANNED` — **re-homed to
  ducroq/NexusMind#232**, which is open and untouched since the minute it was
  created (54 days).
- **No NER exists in NexusMind.** `grep` for spacy/gliner/stanza/nltk over `src/`
  and requirements: zero. Every apparent `entities` hit across three repos is a
  false positive — "identities", HTML entities, a comment.
- `ovr.news/src/lib/db-schema.ts:385` creates an `entities` table **plus two
  indexes**. No writer, no reader.
- Four dependents, all banded nowhere: NM#223 (commerce entity-density, which
  feeds NM#185's unstarted commerce v3 half), NM#185's obit NER input, ovr#222,
  and a `/places/{country}` surface.
- **NM#223 and ovr#222 both still cite `FluxusSource#85`** — a closed issue — as
  their dependency. Both read as unblocked. Inverse of the previous session's
  "✅ while open" finding; same root, reading state instead of deliverable.

### 2. Chain 15 is 71 days old, not 2

**NM#225** ("Audit cross-filter score comparisons; document policy as ADR",
created **2026-05-28T16:42**, zero comments, banded nowhere) states the
lens-commensurability defect precisely — naming tier assignment that mixes
filters, **lens routing in ovr.news**, and "primary topic" logic. LD#96 and
ovr#296 were created **2026-08-05** (07:09 and 06:34). So the board's
"two repos derived the same defect independently the same day, which is the
topology rule working" misses that a third derivation came first, is the most
actionable of the three, and sat idle. **NM#226** (same author, same day) is the
Chain 13 companion: "which invariant changed at which step" is exactly what
NM#289 and LD#95 are stuck on. Also unbanded.

### 3. Chain 16 is missing its NexusMind link

**NM#254** (content-level propaganda-technique extractor) was last updated
**2026-08-02** — the same day all 12 persuasion-scorer issues were — and carries
the cross-post holding the taxonomy decision (SemEval-2023 Task 3, score the
**6 coarse categories, not the 23 fine**; α = 0.342 against a 0.667 threshold).
Chain 16 was assembled from ps issue *titles* only, so it missed the sibling with
the decision in it. Pairs with ovr#253, also unbanded.

### 4. Coverage numbers

**26 ovr.news engineering + 11 NexusMind issues appear nowhere in the board
memo.** LD, FS and ps are fully covered. And a number the memo declines to
quote can now be stated with its rule: under
`-positioning -outreach -community -content`, ovr.news engineering is **63 of 89**.

**A seventh repo takes mandated output from this chain and is on no board:**
`ducroq/augmented-engineering` — **34 open, 1 closed ever, last closure
2026-04-14**. CLAUDE.md instructs this repo to file evidence there; ~10 of the 34
are llm-distillery-derived and filed in the last month. A write-only queue.

## The NM#232 plan, and the six reviewers who took it apart

Wrote a full plan for NM#232, then ran a **six-lens multi-model battery**
(fact-check, adversarial, verifiability, NLP-domain, sequencing, completeness).
**The central recommendation did not survive, and three of my stated facts were
wrong.** Detail in [[corroboration-feature-hypotheses]]; the short version:

- **My "cheaper alternative" (entity overlap inside dedup) is dead** on five
  confirmed grounds. Decisive: **85.5% of credited corroboration sources are an
  integer with no record at all**, 7.8% have full text — so the promised output
  is unbuildable. And the intervention was already measured here as **anti-signal**.
- **I picked the wrong consumer.** ovr#222 is display-layer and cannot improve
  the decision it renders; at 0.560 precision it makes a wrong claim look
  *evidenced*. The consumer that matters — the matching model, NM#213 — **is not
  on NM#232's list at all** and is the only one with code and a readout.
- **Dutch**: I claimed only English gets the rich label set. A reviewer installed
  spaCy and printed it — **English and Dutch both carry the full 18-label set**;
  de/fr/es/it/pt carry the coarse four. But Dutch has the *worst* accuracy
  (0.715 vs English 0.855). Same conclusion, different cause and different fix.
- **The contention worry was fictional** — the Gemma-3 scorer runs on a different
  machine. Measured cost is 1.5–7 min/cycle.
- **My superset measurement was accidentally cherry-picked** — `logs/*.log`
  skipped 30 days of rotated files. See the gotcha log.
- Missed by everyone until the completeness lens: **persisting a searchable index
  of named persons is plausibly a new processing purpose** on a project with an
  active GDPR/EMFA/AI-Act track. Also absent: backfill (NM#232's own stated
  rationale), failure handling, kill switch, tests, observability, retention.
- **What survived**: the proposed placement is safe from the NM#300 loss path —
  verified, an existing field using the same pattern is present on
  **37,779 of 37,779** rows — but the plan never said *why*, and the tempting
  nested alternative would have recreated the bug exactly.

## What shipped: the cross-source dedup stamp (FluxusSource `4994d61`)

The owner's question — "FluxusSource dedup is hash-based, so it wouldn't give
useful features?" — was right about features and turned up something bigger.

`_deduplicate_by_hash` drops on `md5(title + content[:500])` **with no source
comparison**. Two outlets carrying the same syndicated wire copy collide and the
second is dropped: different URL, different publisher, same story. **The
strongest corroboration evidence there is, deleted before NexusMind embeds
anything** — the same source-blind shape as NM#296, one stage upstream. The
docstring claimed the check was a "fallback (for items without URLs)"; it has
always run for every item.

**Shipped as instrument only** — drop behaviour unchanged, collision now
source-aware and counted, report promoted DEBUG → INFO with worked examples.
Content-hash entries went from a bare timestamp to `[timestamp, source]`.
Filed as **ducroq/FluxusSource#133**; **#134** filed separately for MinHash
(`compute_minhash`/`jaccard_similarity` implemented, `datasketch` pinned, **zero
call sites**).

**Total collection drop is 41.1%** (422,778 of 1,028,946 over 233 runs) but most
of that is the URL branch doing its job; the cross-source share was unmeasurable
because the split line was DEBUG. **The count is a floor for ~30 days** while the
36,577 legacy source-less entries age out.

Proved by execution, not tests alone: real production `seen_hashes.json` loads
unchanged (36,577 in / out); save-reload preserves both entry shapes;
`_deduplicate_by_hash` on real article text gives
`{'by_content': 2, 'by_content_cross_source': 1}` on a Reuters/AP pair plus a
same-outlet repost. Full suite **793 passed**.

## Also this session

- **pipeline-atlas outage diagnosed**: served 200 on-box, timed out everywhere
  else. Host firewall fully open, `tcpdump` captured **zero packets** — a tailnet
  ACL closing all TCP except 22. Owner reopened 8099; verified from off-box.
  **The atlas smoke test runs on-box and passes throughout such an outage.**
- **Phase 4a of the corroboration plan is already discharged** — checked rather
  than assumed: hedge live in both languages, boost ladder replaced by flat 1.3×
  capped at 9.

## NEXT SESSION

1. **Read the cross-source number** off the 20:00+ collection runs:
   `ssh sadalsuud 'grep "Dedup: " /home/jeroen/local_dev/FluxusSource/logs/aggregator.log | tail'`.
   Treat it as a floor until ~2026-09-06. That number decides FS#133.
2. **Corroboration track, in its own order**: step 2 (settle title vs title+body,
   no new labels), then **step 3 — mine the labels already held** (hours of
   compute; this is the unblocker, everything is starved at n=23), then step 4
   (cross-lingual NER swap, no new labels, decides whether a campaign is needed).
   **But FS#133's number lands first** — step 3 mines a corpus that may be
   pre-depleted.
3. **FS#120 is ~7 days out (2026-08-14)** and is still the only calendar-bound
   item on the board. It competes with all of the above.
4. **Board maintenance not yet done**: place NM#225 in Chain 15 (and re-date it),
   NM#226 in Chain 13, NM#254 in Chain 16, and open the NER cluster as its own
   chain rooted on NM#232.
5. **Open question for the owner**: does `ducroq/augmented-engineering` (34 open,
   1 ever closed) belong on the board, given CLAUDE.md mandates filing into it?
