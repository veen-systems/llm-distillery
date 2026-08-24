# 2026-08-24 midday — the census's own columns, and a gate-ordering rule

**No spend. No model.** The block ledger deployed at 08:54 was outcome-verified at
**14:08**, after the 12:00 cycle wrote its first flush at 13:05 — see §6, added at the end
of the session. Everything in §1–§5 was written while that was still pending.

Started at *"where were we?"*, so the first act was reading state rather than acting on it.

---

## 1. What shipped: `stamp_census.py`'s three mis-defined columns

NexusMind `e73c5ef`, deployed to sadalsuud and verified there by running it.

| column | was | is |
|---|---|---|
| `pop%` | `populated / seen` under a name `ARTICLE_RECORD.md` defined as *presence* | **`pres%`** (present / all rows) + **`fill%`** (populated / rows present), plus a `RARE-FIELD` flag |
| `distinct` | the 12-entry display sample reused as cardinality — saturated at 13 | exact to `DISTINCT_CAP=5000`, then `>=5000`; hashes the FULL value (the old one truncated to 28 chars first) |
| `rdrs` | bare leaf-name grep | qualified with the parent segment where that finds hits; else `RDRS-AMBIGUOUS` |

The run now prints its **window** beside the field count.

**Outcome on 145,301 production rows** (`filtered_20260822_124557` .. `filtered_20260824_084855`):

```
                          OLD                  NEW
_post_enriched            100.0    1      0.03 / 100.00      1   RARE-FIELD
metadata.doi              100.0   13      1.05 / 100.00    288   RARE-FIELD
content_hash              100.0   13    100.00 / 100.00 >=5000
content_quality.score     100.0    6    100.00 / 100.00      6      <- control, unmoved
```

Shared leaves reproduce the audit exactly: **7 leaves, 14 of 212 fields.** One is
`type_classification`, whose zero-consumer defect (#101) is the kind a well-read
namesake hides.

Verification: 15 tests, **12 fail against the previous script** (checked in a worktree
at `main`); full NexusMind unit suite 1,431 passed.

## 2. ⛔ Four self-corrections, all mine

1. ⭐⭐ **I introduced a regression while fixing one, and found it by asking why a test
   passed against the OLD code.** My first ambiguity cut marked *every* shared leaf
   ambiguous, which suppressed legitimate no-reader findings. A shared count of **zero**
   is an upper bound on all its members, so it proves absence and stays attributable.
   Killed by `test_shared_leaf_with_zero_readers_still_raises_for_both`.
2. ⭐⭐ **I wrote a derived number into a doc as if it were measured.** `_post_enriched`
   at "0.03%" of 145,301 → I wrote **44**. An independent `grep -c` says **46**. A
   number read off a rounded percentage is not a measurement.
3. ⭐ **The scratchpad script and the tidied committed script were not the same
   program.** I dropped a `sys.path.insert` while tidying; the committed version died
   with `ModuleNotFoundError` on its first real run. *Run the artifact you shipped.*
4. **I guessed an issue number before filing** — wrote `#125` into a script docstring
   and a commit message; it is **#130**. The commit message cannot be edited in place.

## 3. A gate-ordering rule, from a question about crime

Owner asked whether commerce should be the template and the other blockers sequential,
short-circuiting once blocked. Conclusion, with the disagreements stated:

⭐ **A topic is headline-detectable; a stance needs the body.** Commerce and obituary are
topics and drop pre-enrichment. Violence-promotion is a stance — `_run_violence_promotion_prefilter`
runs *on the enriched superset*, which is why the load-gate violence check that was tried
once was a no-op. Moving it up is a retrain, not a reorder.

- **Obituary stays pre-enrichment, structurally**: its embedder has a 128-token limit, so
  it sees ~the first 100 words and cannot read an enrichment anyway.
- **Short-circuit, split in two.** "Already processed → skip" is right and the mechanism
  already exists: `_mark_processed` has exactly two callers (`main.py:2101` after scoring,
  `main.py:3389` for content-quality rejects) and **no gate uses it**. That is the ~22,000
  re-evaluations per cycle. "Already blocked → skip remaining STAMPS" is wrong: it is what
  the ledger explicitly refuses, because it makes gate overlap unanswerable forever.
- ⛔ **There is no `_is_crime`.** Grepped across five repos: "crime" appears only as prompt
  text and as `crime_violence`, an exclusion category in per-lens prefilters — dead in
  production since 2026-02-10 (NM#284).

## 4. #130 filed: crime in belonging, measured

**llm-distillery#130** — *does belonging count harm-answered-only cohesion as belonging?*
The belonging counterpart of #107's uplifting ruling.

Measured over 12 cycles, 25,156 scored rows per lens, one corpus so the base rate is the
control. Probe committed at **NexusMind `scripts/research/crime_in_lens_probe.py`**:

| | uplifting (op 4.5) | belonging (op 4.0) |
|---|---|---|
| crime-matching, whole corpus | 854 (3.4%) | 854 (3.4%) |
| crime AND above op-point | 59 (3.5%) | 46 (6.3%) |
| **enrichment vs base rate** | **1.04×** | **1.87×** |

Bands do not overlap at 2 SE. All above-op rows were `stage_used: stage2`, so no Stage-1
probe estimates are mixed in. `uplifting`'s consumer lens already narrowed to exclude
**harm-answered-only** (ovr.news `BRAND.md` `a70609b`, scoped into v8 `human_thriving`);
`belonging` has no such narrowing and is where the effect is concentrated.

⚠️ The regex is a screen with **unmeasured recall** — every count is a floor. A match is
not a verdict: "Indonesia marks fourth year without terrorist attacks" matches and is
legitimately on-lens.

## 5. Traps worth keeping

- ⚠️ **A research script's own selector was the defect, and it failed loudly only by luck.**
  `next(v for v in vars(mod) if hasattr(v, "EXCLUSION_PATTERNS"))` selected `BasePreFilter`,
  whose dict is empty. It raised `KeyError` — had the category been present-but-empty it
  would have screened on nothing and looked like a result. The committed version requires
  **exactly one** carrier and exits otherwise.
- ⚠️ **Deploying a non-pipeline file still moves the checkout SHA.** Every pull this
  session was checked with `git diff --name-only <deployed-sha>..HEAD` to prove the
  pipeline path was untouched, so the pending 12:00 ledger verification still tests what
  was deployed at 08:54.

## 6. 🅐 RESOLVED — the ledger works, and my sizing did not

`verify_block_ledger.py` exits **0**: 168,486 rows, index present, all conformant to
`article-record.schema.json v0.4.0`, one row per article. **Every mechanism reconciles
exactly against the pipeline's own counters** from the same cycle's journal line
(`Loaded 4809 articles (skipped: ...)`) — a per-bucket check against a *different*
instrument, not closed accounting:

```
gate.commerce           18,930  =  18,930      dedup.title            3,024  =  3,024
gate.obituary            3,325  =   3,325      freshness.too_old    142,899  = 142,899
gate.violence_promotion    239  (later stage)  freshness.future_date     69  =      69
```

⛔ **The sizing estimate was wrong by 7.6× and the SHAPE of the error is the keeper.**
Predicted ~22,237 rows / ~42 MB; actual 168,486 rows / 320 MB. The portion I actually
sized — gate-blocked — came in at **22,494 against 22,237, 1.2% off**. The rest is
`freshness.too_old` at **142,899 rows, 85% of the ledger**, which my estimate carried as an
unquantified prose clause: *"plus freshness and dedup rows"*. **The bucket nobody counted
held six sevenths of the volume.** A pre-registered prediction is what made this legible:
one aggregate number would have said "wrong by 7.6×" and hidden that the model of the gates
was nearly perfect and the model of freshness did not exist.

⏳ **Still open, and deliberately not acted on today:** whether the SECOND flush (16:00) is
a few hundred rows or another 320 MB. The written-id index holds 168,486 ids and should
suppress the `too_old` re-reads, but **one cycle is not a growth rate**. If it recurs that
is 1.9 GB/day. Held behind that number: moving `.ledger_index.json` (12.3 MB, sitting where
cleanup sweeps, surviving only because the glob is `*.jsonl` and it is `.json`), and the
`placements: {6: 168485, 3: 1}` outlier, undiagnosable at n=1.

⛔ **No ledger code changed today.** There is exactly one verified baseline and it is hours
old — the same reason the census fix was kept off the pipeline path this morning.

## 7. Wrap-up actions

- **NM#401 CLOSED** — the census columns, with the before/after table and the verify command.
- **NM#403 commented** (block-ledger off-site backup): it now has measured volumes instead of
  projections, plus the warning that a backup policy must be sized against `too_old`
  dominating, and that **one cycle is not a growth rate**.
- **llm-distillery#123 commented** — the index-budget guard went from deferred to acute: the
  nine-step trim table from this session, and four options for the owner. Six older entries
  were compressed to buy room for one session's writing; the lever is nearly spent.
- **H-AR11 / H-AR12 added** to `memory/hypothesis-ledger.md`.
- **sadalsuud synced** `8eed8d9` → `7f57708`; it had been one commit behind since 10:40 and I
  had reported it as current without checking.

## Next session

⚠️ **The ledger writes ~66 minutes INTO a cycle** (12:00:15 → 13:05:57), so the next timer at
**16:02:29** puts the second flush near **17:08**. Check `ls -la data/blocked/` for a SECOND
`blocked_*.jsonl` before trusting the verifier — opening at 16:00 re-reads the first flush.

**Then re-run `verify_block_ledger.py`** — that one number decides
one-time-backfill from 1.9 GB/day, and settles both held items above. Then 🅑b the register
(its instrument is fixed) and 🅒 migration step 3.
