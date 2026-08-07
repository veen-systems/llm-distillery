---
name: project_session_2026_08_07
description: Six owner decisions walked one at a time (two stale as listed), then two review rounds that found 5 code defects and ~20 doc errors, nearly all in the same day's own work
metadata:
  type: project
---

# Session 2026-08-07 — decisions, then two rounds of being wrong about them

**Shape of the day:** the owner asked to go through the open owner decisions one
at a time. Six were on the board. **Two were stale as listed** — already decided
in a repo the board does not read. Of the four that were real, one was
over-engineered and the owner pushed back and was right. Then two rounds of the
review battery found **five code defects and roughly twenty documentation
errors, nearly all in work written the same day.**

## The six decisions

| # | Issue | Decision |
|---|---|---|
| 1 | ducroq/NexusMind#301 corroboration claim | **Hedge the wording.** `"{n} sources"` → `"{n} related sources"` / `"{n} gerelateerde bronnen"`, every link kept, ✓-in-circle → link glyph. |
| 2 | ovr#283 publication floor | **Close won't-do.** Keep storing `raw_weighted_average`. |
| 3 | ovr#284 Comscore beacon | **Deny-list now, off-domain host as a STAMP not a block, no allowlist, recover the exposure window.** |
| 4 | ovr#287 wrong-story heroes | **Blank what is still buildable, leave the rest.** |
| 5 | `/accountability` TDM sweep | **Say nothing.** |
| 6 | ducroq/NexusMind#292 non-English root | **Keep open, retarget.** Transfer the scoring stage into `human_thriving` v8. |

**Decision 7 was created by the review and taken the same day** (`1ecf853`):
ovr.news's **own** corroboration boost, `1.3× / 1.5× / 1.7×`, **bounded to a
flat 1.3× for 2–10 total sources, 1.0× above**. The ladder was removed rather
than retuned — precision is not monotone in cluster size and no band beats the
2-source case (0.560), so under the old ladder the *best*-measured band got the
*smallest* boost. Subtractive by construction. **This is the first time the
reader-facing promotion has ever been bounded**, because NexusMind's `1bbadb5`
never reached readers.

## What the walk-through itself produced (none of it was the decision being asked)

1. **ducroq/NexusMind#301's own comment says readers see no corroboration
   claim. They do.** The comment grepped for the field `corroborating_sources`
   and the string "N sources reported this". The field exists; the string does
   not; the claim reaches readers by a *different* route —
   `source_quality.other_sources` → `getIndependentSources()` → a badge plus
   named, hyperlinked publisher domains.
2. **A publication floor already exists, on the wrong quantity.**
   `displayScoreThreshold: 4.5` gates publication on the **normalized** score,
   against ADR-022. Filed as **ovr#304**. Binds 18 rows today, all
   `nature_recovery` — a single-filter normalization artifact, not a
   cross-filter floor.
3. **Decision 5 was over-engineered.** I recommended disclosing the TDM sweep on
   `/accountability`; the argument rested on the finding being publicly
   discoverable. **`ducroq/ovr.news` is PRIVATE.** With that leg gone,
   disclosure has no audience and solicits removal requests nobody would
   otherwise make. What survives is operational: **schedule the scan** (run
   once) and **fix the 117 fail-open errors**.

## What the review battery found — five code defects

Two rounds, four lenses then three. **Every one of these is in work written the
same day.**

1. **The deny-list would have been undone within the same pipeline run.**
   `summarize.ts` Step 5 runs *after* Step 4's validation and re-sent
   `rawArticle.image_url`; `upsertArticle` merges with `COALESCE`. 123 stored
   rows already carry the signature.
2. **The caller-side fix for (1) was a complete no-op, proven by execution** — a
   *second* commit point in the cache branch short-circuited before the
   "final" guard, whose comment claimed it was the only one.
3. **Decision 4 left a reader-visible defect.** One vanguard row, normalized
   **9.10 on `solutions`**, was still inside the build window. I reasoned about
   the group's date range instead of computing per row, and the script
   hardcoded `aged: true` so it structurally could not notice. 5 rows → 6.
4. **The deny-list was inverted against its own rationale** — it denied each
   vendor's *JavaScript* host and omitted the sibling serving tracking
   *images*. Measured: 14 of 15 mirrored entries have never matched a row.
5. **Leading whitespace defeated the protocol-relative fix**, reopening the
   pre-write window it existed to close.

Plus: the audit's `--days` filter was 50% wrong at short windows (`T` vs space
separator), and `registrable()` collapsed every `.co.uk`/`.com.br` publisher
into one, blinding the exact signal the audit ranks on.

## And ~20 documentation errors

Notably: quoting corroboration precision as **0.283** and glossing it "most
sources credited did not report it" — the durable figure is **0.560**, at which
a majority *did*, so the sentence inverted its own evidence. And telling the
owner NexusMind's `1bbadb5` had fixed the ranking half when **ovr.news never
reads NexusMind's `display_rank`**.

The first board sweep repaired the chains and batches and reported done; round 2
found the **priority tables** — the part an operator reads first — still
recommending an action three other sections had just been corrected to call
impossible.

## Commits — ALL PUSHED

- **ovr.news** (`master`): `85811f2`, `a2974cc`, `68db118`, `420eb74`,
  `1ecf853`, `80a8401`. Note the first four were **rebased** onto three
  automated `Update summary/translation cache from sadalsuud` commits that
  landed on the remote mid-session — zero file overlap, my commits were
  unpushed and held by nobody, so the rebase was safe. The pre-rebase hashes
  (`5f7feb3`, `55b2e06`, `dc1fc9c`, `2da519f`) no longer exist.
- **llm-distillery** (`main`): `ff79cfb`, `261ec2f`, `54c3cef`, `1ccb9f1`, +
  this curate pass.

Tests: **1,187 pass** (+33 today).

**Deploy:** ovr.news is a static Astro build; pushing `master` is what ships it,
so decision 1 (wording + glyph), decision 7 (bounded boost) and the corrected
`ranking.astro` are live on the next build. Nothing was deployed to sadalsuud or
gpu-server — no filter package changed.

## NEXT

1. **The 6 rows are not cleared.** Needs the R2 round-trip:
   `npm run db:download` → `npx tsx scripts/clear-wrong-story-heroes.ts` →
   `npm run db:upload`. Not durable alone — if NexusMind still holds the bad
   `extracted_image_url`, the next ingest writes it back.
2. **ovr#284 exposure window** — approved, not started. The one UNKNOWN that
   could reopen the Art. 33 conclusion.
3. **FS#120** is 7 days out (~2026-08-14) and remains the only calendar item.
4. **~2026-08-18**: re-measure corroboration precision on the **capped** system.
   Both new hypothesis-log entries hang off that date.
5. The glyph change is **unverified on a real device** — and that is the whole
   premise of decision 1's icon swap.

## Related

- [[cross-repo-prioritization]] — the board, with all seven decisions
- [[gotcha-log]] — four new entries, incl. the 6th/7th signature-defect instance
- [[score-batch-shape-noise]] — the 0.16 band that decision-adjacent claims inherit
