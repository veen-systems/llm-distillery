# 2026-08-23 night → 08-24 — the article record got a definition, and the block ledger got built

**No spend. No model. Nothing deployed** — a production cycle was mid-run at wrap-up, so the
deploy is the first item of the next session. All code lands in **NexusMind**; this repo carries
the spec and the evidence.

Started at *"we are going to work backwards. First we need to define the article record properly."*

---

## 1. The investigation the owner did not want, and the one they did

⛔ **My first answer was wrong in kind, not in content.** Asked to define a data record, I
delivered a ten-finding audit of `stamp_census.py`'s instrument. Owner: *"i have no idea what you
are talking about. I want a well-defined datarecord."* The audit was correct and is kept
(`docs/evidence/2026-08-23-article-record-instrument-audit.md`) — it just was not the deliverable.
**Lesson: an instrument audit is a prerequisite I chose to narrate instead of a proposal I was
asked to write.**

The audit's findings, all measured over **165,196 rows / 72 files / 6 filters /
`filtered_20260821_205726` → `filtered_20260823_165255`**:

- ⭐⭐ **"132 fields" is a property of a 2-cycle window.** `--cycles 12` → **212**. `metadata.*`
  is per-source vocabulary, so a longer window sees more source types. Three documents stated 132
  as the size of the record.
- ⭐⭐ **`pop%` is not what `ARTICLE_RECORD.md` says it is** — the column it calls *"the point of
  this document"*. Code computes `populated/seen`, where `seen` counts only rows carrying the key.
  `_post_enriched` prints **100.0%** and the finding text says *"populated on 100% of rows"*; it
  is present on **23 of 165,196 (0.014%)**. `_academic_gate.*` prints 100.0% on **35 rows**.
- **`distinct` is censored at 13.** `metadata.doi` prints 13; the true count is **403**.
- **The reader column is a bare leaf-name grep.** 14 fields (7 pairs) share a leaf and therefore
  carry *identical* counts by construction — `content_quality.score` and `metadata.score` both 765.
- ⛔ **"Declared nowhere" was FALSE.** Contract A v1.35.0 declares 39 of the 212, Contract B
  v1.18.0 declares 51. The genuinely undeclared NexusMind set is **20 fields**, not 132.
- **Contract B declares `_corroboration`; it is on 0 of 165,196 rows** — and NM#399 already has
  the cause: it is `pop`ped ~34 lines before anything reads it.
- **`image_analysis.extracted_image_dimensions` is not dead** — a nullable dict, whose parent path
  is recorded only on the rows where it is null. Its "population" is the count of its own absence.
- **16 of the 59 findings are not independent** — 11 are by-design per-filter constants, 5 are one
  fact reported once per filter.

## 2. Owner rulings

1. **PRESCRIPTIVE**, not descriptive. I recommended descriptive; owner overruled, and was right —
   the record now says what it should be, and the migration is staged behind it.
2. **"Starting from contract A, and then adding what nexusmind brings"** — which made the schema
   a *composition*: `allOf: [$ref Contract A, nexusmind_layer]`. Producer fields have one
   definition and cannot drift.
3. **Ledger + gates dual-write**, chosen over ledger-only, so blocked and kept rows read alike.

## 3. What was built

`NexusMind/contracts/article-record.schema.json` v0.4.0, `src/archiving/block_ledger.py`,
`scripts/verify_block_ledger.py`, wiring in `scripts/main.py`, blocked archiving in
`filtered_archiver.py`, config in `app.yaml`, 46 tests.

**Offline proof on real production input** (`content_items_20260823_161050.jsonl`, 3,074 rows,
six filter loops): **430 blocked articles**, 406 with content, every row `placements: 6`, tallies
reconciling exactly — `commerce 1,698 = 283 × 6`, `obituary 330 = 55 × 6`, `too_old 408 = 68 × 6`,
`duplicate_title 144 = 24 × 6` — and 283 is the input file's own `_is_commerce: true` count. All
430 validate against the schema; a negative control (`stamped: true` with a null score) produces
2 errors, so the schema is not merely permissive.

**Three deliberate deviations from `BLOCK_LEDGER_SPEC.md` §3**, each recorded there:
prescriptive shape instead of flat `_blocked_by`; **an own written-id index instead of
mark-processed** (that changes admission behaviour, the ledger does not — and without an index it
would rewrite ~19,000 rows every four hours, because the spec's "300–500/cycle" quietly assumed
mark-processed had landed); and `already_processed` writes no row.

## 4. ⛔ Four self-corrections

1. ⭐⭐ **A mutation survived because MY OWN TEST asserted something that could not fail.** I wrote
   that the cleanup glob deliberately protected the ledger index — the index is `.json`, the glob
   is `*.jsonl`, so they can never collide. **Mutation testing caught it; my own review had not.**
   Fixed the fragility rather than the test: the index is now rebuildable from the rows on disk.
2. ⭐⭐ **I declared `gates.academic_merge` in the schema and never emitted it** — declared-but-
   never-written, the exact defect class the record exists to catch, one hour old. **The owner
   caught it, with "just checking: academic is also a flag, right?"** It also turned out to need
   different semantics (`evaluated`, not `stamped`): it judges only PL-vs-PL candidates, so
   "not evaluated" is the normal case at 165,161 of 165,196 rows, and it refuses a MERGE, not an
   article — `blocked: true` on a kept row is correct.
3. **The dual-write cost was +501 bytes when I first quoted it and +593 after `academic_merge`** —
   10.1% of a 5,844-byte median row. Requote after any layer change.
4. **My first wiring attempt referenced `filter_name` where it was not in scope.** The tests
   caught it; the drop points live in `_read_and_filter_articles`, not `load_articles`.

## 5. Traps worth keeping

- ⚠️ **The service runs `--skip-cleanup`.** Cleanup is a separate `OnSuccess` unit
  (`nexusmind-cleanup.service`, `--cleanup-only`). Reading only the main unit's `ExecStart` would
  have said "cleanup never runs" and sent me to fix a non-problem. **Verify the unit graph.**
- ⚠️ **Stage ordering caps what a blocked row can say.** A `load_articles` drop was never judged
  by violence_promotion (stamps later) or the academic gate (runs in dedup). Violence-enforced
  drops *can* carry both, since `_enforce_violence_promotion` (line 3556) runs after
  `_run_shared_dedup` (3457). The blocked population is not uniform in what it can tell you.
- ⚠️ **`filtered/` and `raw/` are swept unconditionally by cleanup; both are reproducible from
  upstream. A blocked article is not.** So ledger deletion is gated on the archive step having
  succeeded — a divergence from the surrounding code, on purpose.
- **Local test runs need `venv/bin/python`** — the system Python lacks `trafilatura`, so every
  `main.py`-importing test errors and it looks like a broken suite.

## Next session

`docs/TODO.md` top block. **🅐 deploy the ledger and verify after one cycle** (the only item with
a clock), then **🅑 fix `stamp_census.py`'s columns before generating any register**, then
**🅒 migration step 3** (free) and step 4 (paid, own issue).
