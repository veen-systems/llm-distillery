# 2026-08-24 midday — the census's own columns, and a gate-ordering rule

**No spend. No model. Session still OPEN at the time of writing: the block ledger
deployed at 08:54 has NOT been outcome-verified.** The first cycle since the pull is
12:00:14; `scripts/verify_block_ledger.py` is item 🅐 and nothing below replaces it.

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

## Next session

**🅐 VERIFY THE BLOCK LEDGER** — `ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind &&
venv/bin/python scripts/verify_block_ledger.py'`. Expect ~22,237 rows (~42 MB) on the
first flush; **exit 2 means the stage never ran, which is the finding, not a pass.** Then
reconcile against the cycle's own `N × 6` placement counters. Then 🅑 the register, now
that its instrument is fixed, and 🅒 migration step 3.
