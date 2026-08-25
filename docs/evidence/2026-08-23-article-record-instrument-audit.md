# The Article Record — auditing the instrument before generating the register

**2026-08-23, late.** No spend, no deploy, nothing written to production. Read-only measurement
against the running box (`sadalsuud`, `/home/jeroen/local_dev/NexusMind`, `25d0ae2`).

`NexusMind/docs/ARTICLE_RECORD.md` settles the *shape* of the register and hands the machine half
to `scripts/stamp_census.py`. This file checks whether that instrument can produce the columns the
document promises. **It cannot yet — three of its four columns mean something other than what the
document says they mean.** Fix the instrument first; a register generated now would ship wrong
numbers with a register's authority.

## The window this was measured in

```
ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && python3 scripts/stamp_census.py --cycles 12'
```

**165,196 rows · 72 files · 6 filters · `filtered_20260821_205726` → `filtered_20260823_165255`
(~44 h).** Survivors only — `filtered_*.jsonl` receives `passed_prefilter: true` rows and drops
source-type-excluded ones.

---

## F1 — the record has no fixed size; **132 is a property of a 2-cycle window**

`--cycles 2` → **132** fields. `--cycles 12` → **212** fields. Same code, same box, same day.

The growth is `metadata.*`: FluxusSource emits per-source vocabularies (`arxiv_id`, `nct_id`,
`author_did`, `question_id`, `mesh_terms`…), so a longer window observes more source types and
therefore more fields. 121 of the 212 are `metadata.*`.

⛔ `ARTICLE_RECORD.md`, `llm-distillery/docs/BLOCK_LEDGER_SPEC.md` §0 and `docs/TODO.md` all state
**132 fields** as if it were the size of the record. It is the size of a 2-cycle observation.
**The register must print its window and treat absence as "not observed in this window".**

## F2 ⛔⛔ — `pop%` is not the share of rows the field is present on

`ARTICLE_RECORD.md` defines it as *"share of rows on which the field is **present**"* and calls it
*"the point of this document"*. The code computes `populated[field] / seen[field]`, and `seen`
counts **only rows where the key appeared**. So a field that is rare but always filled reads
**100.0%**, and the findings text says so in words.

Measured over the same 165,196 rows:

| field | census says | actually present on |
|---|---|---|
| `_post_enriched` | `100.0` — *"populated on 100% of rows"* | **23 rows — 0.014%** |
| `_academic_gate.{blocked,enforced,reason}` | `100.0` | **35 rows — 0.021%** |
| `metadata.doi` | `100.0` | 2,190 rows — 1.33% |
| `metadata.arxiv_id` | `100.0` | 1,370 rows — 0.83% |
| `metadata.mobile_url` | `27.6` | 29 rows — 0.018% (8 non-null) |

Two different denominators are mixed in one table and only one of them is printed. `_is_commerce`
reading `100.0` is true against all rows; `_post_enriched` reading `100.0` is true against 23.
**Nothing in the output distinguishes them.**

⇒ The register needs **two** columns: `present%` (of all rows in the window) and `nonnull%` (of
rows where present). One number cannot express "rare but always filled" vs "everywhere but often
null", and the whole purpose of the column is to tell those apart.

## F3 — `distinct` is censored at 13

`if len(values[field]) <= 12: values[field][...] += 1` stops recording new values, so the column
saturates. `metadata.doi` reports **13**; the true count in this window is **403**.
`metadata.pmid` reports 13; true **282**. `metadata.openalex_id` reports 13; true **139**.

**Every `13` in the table means "≥13".** As printed it is a truncated count presented as a count.

## F4 — the `readers` column is a bare leaf-name grep

`count_readers(field.split(".")[-1])` searches `\bleaf\b` as text. For distinctive names
(`_violence_promotion_score`, `pipeline_run_id`) it is informative. For the rest it measures how
common an English word is in the codebase: `fetch.at` → **731**, `_academic_gate.reason` → **231**,
`content_quality.score` → **765**.

**14 fields (7 pairs) collide on their leaf name and therefore carry identical reader counts by
construction:**

```
content_quality.score                            765  ==  metadata.score                        765
metadata.quality.source_tier                      19  ==  nexus_mind_attributes.*.source_quality.source_tier        19
metadata.quality.type_classification              15  ==  nexus_mind_attributes.*.source_quality.type_classification 15
metadata.quality.credibility_score / …source_quality.credibility_score   (12 == 12)
content_quality.reason / _academic_gate.reason · metadata.{issue,volume} / metadata.biblio.{issue,volume}
```

The identical numbers are the proof: they are not measurements of those fields.

## F5 — `WRITER_PATHS` is 5 files; the real writers are more, and the assignment regex misses how gates stamp

`WRITER_PATHS` = `scripts/main.py`, `deploy/gpu-server/main.py`, `filters/common/{filter_base_scorer,hybrid_scorer,base_prefilter}.py`.

Verified writers **not** in that set:

| field | writer |
|---|---|
| `_is_commerce`, `_commerce_score`, `_commerce_model` | `src/preprocessing/commerce.py:126,268,297` |
| `_is_obituary`, `_obituary_score` | `src/preprocessing/obituary.py:171,199` |
| `_academic_gate.*` | `src/preprocessing/story_dedup.py:1576` |
| `content_quality.*` | `src/preprocessing/content_quality.py` |
| `image_analysis.*` | `src/preprocessing/image_analysis.py` |
| `nexus_mind_attributes.*.primary_literature_*` | `src/scoring/primary_literature_cap.py` |

Two consequences: writer files are counted as **external readers**, so `NO-EXTERNAL-READER` is
false-negative-prone; and `declared_stamps()` matches only `(?:result|analysis|res)["x"] =`, which
never matches `article["_is_commerce"] = …` or `articles[idx]["_is_obituary"] = …` — **the form the
gates actually use**. Check A therefore cannot see the gate stamps at all.

A mechanical writer scan is feasible but not sufficient: `nexus_mind_attributes.*.primary_literature_cap_value`
is populated on 34.6% of rows and **no name-based scan finds its writer**, because
`primary_literature_cap.py:84` assigns through the constant `STAMP_CAP_VALUE`. The `writer` column
must be machine-**proposed** and human-**confirmed**, with `-NONE-` printed rather than blank.

## F6 ⛔ — "declared nowhere" is wrong: two contracts already declare most of it

| | fields |
|---|---|
| census fields (12-cycle window) | **212** |
| declared in **Contract A** v1.35.0 | 39 |
| declared in **Contract B** v1.18.0 | 51 |
| declared in neither | 128 — of which **108 are `metadata.*`** producer passthrough riding `additionalProperties: true` |

**The genuinely undeclared NexusMind-added set is 20 fields**, not 132:

```
_academic_gate.blocked          _academic_gate.enforced       _academic_gate.reason
_commerce_model                 _is_obituary                  _is_violence_promotion
_obituary_model                 _obituary_score               _original_content_length
_post_enriched                  _post_enriched_from           _violence_model
_violence_promotion_score
nexus_mind_attributes.*.enriched_at
nexus_mind_attributes.*.primary_literature_cap_value
nexus_mind_attributes.*.primary_literature_cap_would_apply
nexus_mind_attributes.*.primary_literature_detected
nexus_mind_attributes.*.scores.<dims>
nexus_mind_attributes.*.stage1_estimate
nexus_mind_attributes.*.stage_used
```

Contract B already declares `_commerce_score`, `_is_commerce`, `_corroboration`, `content_quality`,
`image_analysis`, `display_rank`, `pipeline_run_id`, `resolved_url`, `original_content` and 19 lens
fields. ⇒ The register's per-field `scope` column (`A` / `B` / `neither`) is not decoration: it is
what stops the register from re-declaring somebody else's fields and drifting from them.

## F7 — Contract B declares `_corroboration`; it is on **0 of 165,196 rows**

A ghost the census structurally cannot report: `declared_stamps()` reads only
`properties.nexus_mind_attributes.additionalProperties.properties` — the **lens** level — and never
the schema's top-level properties. Check A found one ghost this run (`short_content_cap_applied`);
this is a second, and it was invisible.

## F8 — of the four `NEVER-POPULATED` findings carried into `ARTICLE_RECORD.md`, one is an artifact and one moved

- ⛔ **`image_analysis.extracted_image_dimensions` is not dead.** It reads `NEVER-POPULATED (0 of
  1,410)` while `image_analysis.extracted_image_dimensions.height` and `.width` read **100.0%**.
  `flatten()` walks into a dict and records the parent path only when the value is *not* a dict —
  i.e. only on the rows where it is null. The parent's population is the count of its own absence.
  **Nullable dicts are mis-reported by construction.**
- `content_quality.reason` moved from `NEVER-POPULATED` to `NEARLY-EMPTY` at 12 cycles.
- Surviving at 165,196 rows: `nexus_mind_attributes.*.cap_applied`, `nexus_mind_attributes.*.prefilter_reason`
  (the NM#284 shape).

## F9 — the finding count is not a count of problems

59 findings at `--cycles 12`. At least **16 of them are not independent**:

- **11 structural false positives.** Each `filtered_*.jsonl` carries exactly one lens (verified:
  2,495 of 2,495 rows in `uplifting/filtered_20260823_164812.jsonl` have `nexus_mind_attributes`
  keys `('uplifting',)`). So `nexus_mind_attributes.*.version` being "constant per filter" and
  `scores.<dims>` being "constant per filter" are **by design** — a filter has one version and one
  dimension count — and produce 6 findings each.
- **5 findings for one fact:** `collected.clock_source` constant `'utc'` reported once per filter.

The register needs a by-design suppression list and finding de-duplication before any count is
quotable. ⚠️ The 2-cycle run also reported 59. Different composition, same number — treat that as
coincidence, not stability.

## F10 — `_academic_gate.blocked` means a **merge** was refused, not an article blocked

`story_dedup.py:1576`, via `setdefault` (first writer wins). In this window: **35 rows, all
`solutions`, all `{'blocked': True, 'enforced': True, 'reason': 'both_primary_literature'}`** —
clinical-trial registrations. The article survives; the *merge* did not. A register row that says
`blocked | bool | 100.0%` will be read as article-level suppression by the next person.
**Semantics belong in the `meaning` line, and this is the proof that they are load-bearing.**

---

## What "define it properly" now requires

1. **Fix the instrument before generating anything.** F2, F3, F4, F5, F8 each produce a *confidently
   wrong* register row. Minimum: split `pop%` into `present%` + `nonnull%`; uncensor `distinct`
   (or print `≥13` honestly); qualify the reader search by dotted path and complete `WRITER_PATHS`;
   record parent paths for nullable dicts; read top-level schema properties in Check A.
2. **Scope the register to what NexusMind actually owns** — the 20 undeclared fields, plus the 51
   Contract B already declares (referenced, not restated). `metadata.*` is FluxusSource's and
   belongs in Contract A's changelog, not here.
3. **Print the window** — rows, files, filters, first/last file — on every generated register, and
   state that the field set grows with it.
4. **Two populations, not one.** The register describes survivors. `data/prefiltered_out/violence_promotion/`
   (6.1 M of flagged rows) and the 19 G archive are the only places the blocked side exists, and
   the block ledger is what will make that side measurable.

## Verify commands

```bash
ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && python3 scripts/stamp_census.py --cycles 12'   # F1 (212), F9 (59)
ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && python3 scripts/stamp_census.py --cycles 2'    # F1 (132)
# F2/F3: count presence and distinct against ALL rows, not against `seen`
# F6/F7: cross-check the census field list against both contracts' properties
```

---

# Resolution — 2026-08-25 (NexusMind `97677b3`)

The register is generated: `NexusMind/docs/ARTICLE_RECORD_REGISTER.md`, from
`scripts/stamp_census.py --cycles 12 --emit-register …` joined to
`docs/article_record_status.yaml` (**109 fields classified by hand**).

| finding | state |
|---|---|
| **F1** window is a property of the count | **FIXED** — the census prints its window; the register prints it in its header and says the count belongs to it. Live proof this session: 260 fields at 12 cycles, **229 at 2**, same box, same hour. |
| **F2** `pop%` answered a narrower question | **FIXED 2026-08-24** (`e73c5ef`) — `pres%` + `fill%`. |
| **F3** `distinct` censored at 13 | **FIXED 2026-08-24** — exact to a visible cap, hashing the full value. |
| **F4** readers is a bare leaf grep | **FIXED 2026-08-24** — qualified, `RDRS-AMBIGUOUS` where it cannot attribute. |
| **F5** `WRITER_PATHS` is incomplete; the regex misses how gates stamp | **NOT fixed — accepted.** The `writer` column is machine-**proposed** and human-**confirmed** in the status file, which is what F5 itself recommended. `primary_literature_cap_value` is the proof the mechanical scan cannot be trusted alone: it is assigned through a constant and no name-based scan finds it. |
| **F6** "declared nowhere" is wrong | **FIXED** — `scope` is derived from the contracts at render time (A / B / R / neither) and never hand-copied. ⚠️ **The undeclared set is 19, not 20, by exact-path counting**: Contract B declares the `scores` container, so `nexus_mind_attributes.*.scores.<dims>` reads as declared while the per-dimension NAMES — the genuinely undeclared part — are the per-filter vocabulary the census collapses into that leaf. |
| **F7** `_corroboration` invisible to check A | **FIXED — and what it found was correctly declared.** ⛔ Retracted same day: `_corroboration` is an INTERMEDIATE (built by story dedup, re-emitted under `source_quality`, popped at `main.py:2028`, read in-process by `display_ranking`), and its description said so all along. Contract B 1.18.1 marks it `x-intermediate: true` because **a description is not a machine-readable fact**; check A excludes marked fields and prints them once. Details below.<br><br>Original entry: **it fired on the first run.** Check A now reads Contract B at every level. New ghosts: `_corroboration` + `.cluster_id` + `.other_sources` + `.total_sources`, **declared in Contract B, present on 0 of 164,572 rows** (the dict is popped at `scripts/main.py:2028`), and `nexus_mind_attributes.*.source_quality.source_unreliable`, which may be a rare field rather than a dead one — it is written only when `source_tier == "override"` and credibility < 3.0. |
| **F8** nullable dicts mis-reported by construction | **FIXED** — `flatten` records `<obj:N>` for a populated parent. `image_analysis.extracted_image_dimensions` goes from `NEVER-POPULATED (0 of 1,410)` to `pres 7.43 / fill 89.99`. Constancy findings are suppressed on those rows: two objects of equal size are not equal objects. |
| **F9** the finding count is not a count of problems | **NOT fixed.** No de-duplication or by-design suppression list yet. The register carries the by-design cases as `note:` lines (`version` and `scores.<dims>` CONSTANT-IN-6 is one filter having one version), so a reader is warned even though the count is still inflated. |
| **F10** semantics are load-bearing | **FIXED by construction** — `_academic_gate` and its three children each carry a `note:` saying a refused MERGE is not a blocked article, and that no such row ever reaches the block ledger. |

## What the register is, as a control

It **exits 1** when a field is observed on production rows and classified
nowhere. The reverse is only reported: the census reads a WINDOW, and a field
written a few times per cycle is legitimately absent from a short one.

⭐ **The zero was checked, not assumed.** Three mutations seeded into the status
file and run against the real 12-cycle census — a deleted entry, an invalid
`status`, and a `record_path` the record schema does not declare — were all
three caught, exit 1. A clean run that has never been shown to fail is not
evidence of a clean record.

**Deployed** — sadalsuud at `651aa55`, and the committed register is the run from
that checkout: 177,466 rows, 72 files, `filtered_20260823_124537 ..
filtered_20260825_131739`.

⚠️ The pull was made while `nexusmind.service` read `activating`. The "deploy
when inactive" rule exists for code the pipeline imports, and that premise was
checked before pulling rather than skipped: nothing under `src`, `scripts`,
`deploy` or `filters` imports `stamp_census` or `article_record_register` (one
docstring mention in `title_affinity.py`), and `scripts/main.py` is unchanged.

⛔ **One of my own, and it nearly went in the session report.** The first full
suite run reported *78 failed, 123 errors* and I attributed it to "this
workstation's environment". It was the wrong interpreter: `python3` instead of
`venv/bin/python`. In the project venv the same tree is **1,457 passed** (1,431
+ 26 new). An environment explanation that is never tested is a way of not
looking — the correct reading was one command away.
