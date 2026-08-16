# Session 2026-08-16 — #119 ruled, and a context audit that cut CLAUDE.md under budget

**This repo shipped no filter, no model and no deploy.** Two decisions, one audit,
three retractions of my own, and an unusual amount of cross-repo coordination.

---

## 1. #119 RULED — `id` is identity, `content_hash` detects the edit, last-write-wins

Owner ruled **twice on the same day**, because the cost I quoted the first time was
wrong. Full record on the issue; the durable shape is in `docs/TODO.md`.

**The ruling.** Identity is `id`. `content_hash` is a **change-detector, not an
identity** — a differing hash on a known `id` means EDITED upstream, a case distinct
from *duplicate*. On a repeat id with a new hash: **replace, last-write-wins.**

⚠️ **The sentence needed an ordering clause it did not have.** NexusMind found it by
running the real pair through the real load path over four simulated cycles:
`data/raw` is re-read whole every run, so the older copy of an edited pair arrives on
every subsequent cycle carrying a hash that differs from the stored one, reads as a
fresh edit, and re-stamps the store with the old version. **The pair re-scores itself
every 4 hours, forever.** Final text: a differing `content_hash` **AND a strictly
newer `collected_date`** — the producer's, not the consumer's receipt time.

**Scope, after two corrections.** Not what I first told the owner:

1. **NexusMind** admits the superseded row. ⚠️ *Not* a branch in `_is_duplicate` —
   wrong altitude: it returns into a loop that can only `continue`/`append`, and
   across runs the earlier copy was already scored into a prior `filtered_*.jsonl`.
2. ~~propagate `content_hash`~~ — **it was already on the wire.** Contract B `:67`,
   `main.py:1772`, verified on a live row. ovr's `articles.content_hash` at **0 of
   22,191** is a gap in **ovr's ingest projection**. It is two fields, not one:
   `collected_date` dies at the same type boundary (`RawArticle`, `types.ts:64-95`).
3. **ovr** invalidates the summary cache on a hash change — its summary is keyed on
   **article id alone**, so steps 1+2 alone yield a **pre-edit headline pointed at a
   post-edit URL**. That outcome was not among the three options the owner first chose
   from, which is what forced the re-ask.
   ⛔ **ovr cannot implement the ordering guard from the column it has**: its
   `collected_date` is *ovr's own clock* (`db-articles.ts:142`) and frozen at first
   insert by `COALESCE` (`:81`), so every later row looks strictly newer and the guard
   degenerates into the bare hash test it exists to prevent — **it would read as
   implemented and do nothing.**

**Landed elsewhere by end of session:** FluxusSource `ae52470` (pushed) documents what
`id` survives, per family. NexusMind opened NM#388 and PR #389 (Contract A **1.33.0** +
code, merge and deploy authorized by its own owner). Nothing deployed from here.

### ⛔ Three retractions, all mine, all published before they were checked

1. **"RSS cannot produce this signal at all."** RSS `id = md5(f"{source}_{url}")[:12]`
   is keyed on the **raw URL**, so a content edit at a stable URL **keeps the id**. The
   class reaches ~95% of rows whenever the producer's ~7.7-day seen-URL cache has
   evicted the item — inside the 10- and 19-day feed cutoffs. **Open right now.**
2. **"0 of 3,456 reader-visible rows."** `live_articles` is a legacy view off ovr's
   build path. Re-measured on the `articles` superset (22,191 rows, 2026-04-04 →
   08-16): conclusion held, population was wrong.
3. **"~95% of rows" is not what I said it was.** I proposed replacing FluxusSource's
   vague parenthetical with *"all rows whose id is not an upstream item id"* — which
   sweeps in **3.40%** (5,263 rows, ~19 aggregators) whose id derivation nobody has
   characterised. My fix would have promoted an unknown into a documented family.

⭐ **The keeper is (1)'s diagnosis, not (1).** My zero could not have been anything
else: the on-disk collection span (~8 days) is the same length as the eviction window
(~7.7 days), so a repeat requiring eviction had no room to appear. **That population
must return 0 whatever the truth is.** Recorded as the **8th occurrence** of *establish
what a source excludes* — the new clause is **a window is part of a source**.

⭐ And on (3): **the question did the work, not the answer, and it only worked because
it was specific enough to be wrong.** "Name the quantity" alone would have produced
95.18% and left the 3.40% undiscovered.

---

## 2. `/audit-context` — CLAUDE.md 39,177 → 33,829 chars, under budget

**Step 1's measurement was scoped wrong in our favour.** The 35k budget is applied to
`CLAUDE.md` alone, but Claude Code also auto-loads the *user-level* `MEMORY.md`
(16,163 bytes). **The real auto-loaded burden is 55,650 bytes**; the budget governs 71%
of it. Trajectory: 14.7k (07-26) → 36.6k (08-11) → 37.4k (08-15) → 39.5k (08-16),
~500 bytes from the 40k warning line before the cut.

**Step 4 reported 0 findings and I distrusted it.** The fixture harness passes 24/24; I
also seeded two fabricated paths into the live `CLAUDE.md`, confirmed both were caught,
and reverted. The 0 was real — **over 3 of 84 in-repo context documents.** `refcheck.py`
now scans the 26 live topic files too, which surfaces **51 unresolved references**
(85 more in session records, excluded by default as frozen accounts). Mostly unmarked
cross-repo paths: `scripts/main.py` means NexusMind's, and a reader here looks locally
and finds nothing. **Triage backlog, not a clean-up done.**

**Three correctness defects, each re-derived rather than taken from the sweep:**

- `CLAUDE.md` said Contract A was at **1.20.0**; the smoke run measured **1.32.2**. The
  nav row no longer carries a version at all — it now says to read it off a delivered row.
- `memory/filter-status.md` said cd v6's Hub repo *"DOES NOT EXIST YET"* and the cutover
  was *"blocked on two things"*, two days after CLAUDE.md recorded the cutover failing
  and being reverted. Reconciled, and **probed** so the two layers cannot drift silently
  again.
- A rule marked **⭐⭐ PROMOTED** — *"a failing check may be the CONTROL working"* —
  never arrived in CLAUDE.md. Now promoted.

**42 verify annotations in the live topic files, and nothing ran them.**
`scripts/verification/run_verify_annotations.py` now does: 46 blocks, **17 pass, 0 fail**,
18 skipped, 3 remote, **8 no-assertion**. Three findings shaped it:

- ⚠️ **A block that exits non-zero must not halt the run** — executing them concatenated
  stopped at the first `exit 1` and silently never reached the last two.
- ⚠️ **Counting annotations is not counting mechanisms** — half are prose, empty spans,
  or idiom templates. Skipped **and counted**; a silent skip reads exactly like a pass.
- ⛔ **A block that prints a number and asserts nothing is not a check** — eight of them.

⚠️ **Its classifier judges by SPELLING, which is the weaker method**, and the docstring
says so. pipeline-atlas built the same gate independently and its first draft was an
instance of the defect it was written against. Their fix — decide from the command's
*output* by re-running it with the asserted token swapped — is not implemented here, so
the obligation stays manual: **seed a break and confirm FAIL before trusting a PASS.**
Both new probes were seed-tested that way, and **the first draft of one passed for the
wrong reason** (it read the second ordinal in the whole file, 13, where the answer was 8).

---

## 3. The instrument defect found before anything else

`scripts/contracts/contract_a_smoke.py` — the script that establishes Contract A is
implemented — printed **`FIELDS EMITTED: 0/18`** and **`CLEAN (0 errors over 0 rows)`**
when given a bare collection name that globbed nothing. **A wrong path and a fully
conformant delivery produced the same verdict, and the wrong one produced the reassuring
word.** Now aborts. `a78b0ea`.

Re-verified after the fix: **17/18 on three deliveries**, 0 errors against both schemas.
The latest collection reads **15/18** and that is also correct — `fetch.charset_detected`
and `charset_detected_confidence` fire only where a fetch declared no charset, which none
in that collection did (they carry 20–41 values in three of the last six).

---

## 4. What the cross-repo exchange actually produced

Six confident cross-layer claims between llm-distillery and ovr.news, **six corrected.**
⭐ **Every one fell to dumping the live object; not one fell to reading source.** The
sharpest instance is structural and permanent: ovr's deployed `live_articles` view
carries `tier IN ('high','medium')` while `db-schema.ts:793` says
`weighted_average >= 4.5` — because `createViews()` is `CREATE VIEW **IF NOT EXISTS**`
and `recreateViews()` is exported and **never called from anywhere**. Two people reading
"the view" are reading **two different objects**, and no code path can make them one.

**A bare issue number resolves silently to whichever repo the reader is standing in.**
Two instances today: my `#167` was recorded as NM#167 (unrelated, closed) when the thread
was FS#170; and FluxusSource's insert nearly collided with its own FS#119. Both were
caught by someone re-deriving from the other side, neither by reading.

---

## Open after this session

- **NM#389 MERGED AND DEPLOYED** (`fdffc4b`, pulled to sadalsuud; first cycle 12:0x CEST).
  Contract A **1.33.0** live with it — ⚠️ the next contract-check fire reports a new
  contract `sha256`/`commit`; **expected, not an anomaly.** Watch is dated **2026-08-23**,
  recorded in three places with falsification criteria fixed in advance.
  ⛔ **An early zero will be the RAMP, not the mechanism**: all six stores went in with
  ~111k ids and **zero version records**, and those ids never gain one — they are dropped
  as `already_processed` and age out on the 6-day expiry. **Coverage is partial until
  ~08-22.** ⭐ That is the **third** guaranteed zero of the day, after my eviction-window
  corpus and the rule's 0-fires-on-stored-data. Same shape every time: *the observation
  window is shorter than the mechanism's period.*
  ⚠️ **And the verify probe shipped in that PR was itself unreachable** — `grep -q
  "superseded_reprocessed" scripts/main.py`, a word appearing 9 times in that file
  including in a docstring, so it stayed **green with the feature forced off**. Written
  two hours after we had agreed in the same thread that a mechanism must be the thing
  that fails. **Knowing the rule, and having just stated it, is not protection.**
  Generalisation via pipeline-atlas: **restricting file type does not separate a mention
  from an invocation** — an absence check needs a third mutation direction in which prose
  must not turn it green.
- **ovr** — project `content_hash` + `collected_date` on ingest, then summary-cache
  invalidation. Needs a version-of-the-summary timestamp, not the article's.
- **FS#183** — record-only by owner ruling.
- **51 unresolved references** in the live topic files, newly visible. Mostly want a
  repo marker, not a path fix.
- **#114, #116, #118** and the rest of the backlog untouched.
- ⛔ **Distribution drift stays NOT next.** No evidence it is biting us.
