# Contracts plan — ARCHIVE of review rounds 1–4 (2026-08-13 → 08-15)

*Moved verbatim from `docs/CONTRACTS_PLAN.md` on 2026-09-27 (TODO item −1 step 3): "Review round 1", "Filed by NexusMind", and "Round 2" through the end of "Round 4". Order kept; nothing edited. The plan body, the owner decisions and the Baseline section stayed in the live file.*

## Review round 1 — outcome, 2026-08-13 evening

All four peers reviewed. **The plan's premise moved.** Beyond the corrections
already folded in above:

**New items, both prerequisites that draft 1's ordering missed:**

- **W2.7 (NexusMind) — normalize `parse_published_date` to UTC.** It returns `dt`
  as-is (8 call sites) while `story_dedup._parse_timestamp` normalizes. Diverges
  the moment offsets land: `filtered_archiver.py:146` buckets by
  `strftime("%Y-%m")`, so an article at `2026-08-01T00:30+13:00` is `2026-07-31`
  UTC and archives under `2026-08`. **Must land BEFORE W1.1.**
- **W3.4 (ovr.news) — normalize timestamp parsing.** **W1.1 CREATES a
  lexicographic hazard**: `'…T20:00:00+02:00' > '…T19:00:00'` as a string while
  being earlier in real time, across `idx_articles_published` and ~20
  `ORDER BY published_date` sites. In `story-dedup.ts:58-66` it pushes genuine
  duplicate pairs outside the window so **both publish** — a visible editorial
  failure. Pattern already exists in-repo at `source-funnel.ts:107`. **W1.1 depends
  on it.**

**Measured answers that closed open questions:**

- **The Cloudflare Pages build host is UTC.** ovr measured it without build-log
  access: RSS `pubDate` is build-host-computed, JSON-LD `datePublished` is the raw
  string, so their difference *is* the offset — **8/8 zero shift**. The 11
  build-time sites are correct today. **Nothing pins that TZ**, so ovr's
  correctness rests on a Cloudflare default. Make the two-URL diff the verify
  command.
- **sadalsuud is `CEST +0200` and more sites run there than draft 1 listed** —
  `calculateDisplayRank` too (`summarize.ts:414,:419,:1034,:1035`).
  `recencyBoost: 1.3` fires on `ageHours < 24`, a hard 30% step, so **~25
  articles/day rank ~30% below where they belong on sadalsuud while Cloudflare
  ranks the same articles correctly.**
- **Drop `collected_date` from W1.1's ovr-facing case** — ovr never passes the
  producer's value (`db-articles.ts:136` stamps its own; 100% of stored rows `Z`).
- **ovr reads exactly 2 metadata keys** — `og_image_url` (`summarize.ts:334`) and
  `quality` (`transform.ts:324`). Far better than draft 1's `word_count` example,
  which was a **name collision**: 49 occurrences at ovr, **zero** reading the
  upstream field. ⚠️ **The "2 of 52 / 96% undeclared" form is RETIRED — see round 2.**
  A single-run key count measures which aggregators were due in that tick: **27 to
  107 across 50 runs, median 63.5.** The 2 stands; the percentage never had a
  denominator.
- **`og_image_url` is read at `:334`, UPSTREAM of the `:887` projection, then
  discarded by it.** So a field can be load-bearing at ovr and leave **no trace in
  the stored row** — reading the projection literally understates ovr's dependency.

**Sequencing corrections beyond phase 0a:**

- **"Prove it sees the known defects" is circular** — those defects *are* the
  validator's own output, so reporting them shows it still runs, not that it
  detects. **The genuine control is `source_group`**: an independent commit,
  arriving against a closed top level, that the check was never shown. **It is
  time-limited — once W2.2 declares `source_group` the test is spent, so hold W2.2
  behind it.**
- **"exit 0 always" needs a shipped proof it can go red**, or the phase-3 flip is
  the first test of the wiring. pipeline-atlas has a register entry for exactly
  this: a CI guard that could never fail because `--self-test` always returned 0.
- **Phase 0/3 cannot see ovr's hop** — the `:887` gate is code, not a schema. A
  fully green check is compatible with ovr dropping all but 2 metadata keys, which is what
  it does. **Write that boundary in now**, because at phase 3 "the pipeline is
  contract-checked" is the natural misreading.

**W4 (pipeline-atlas) reshaped by its owner:**

- **Half of `reference/contracts.qmd` is GENERATED** from `model/chain.yml` via
  `ops/gen_views.py`. Editing the page or the `.html` is a named ops trap — the
  next run reverts it and `--check` fails CI. Edit the model, regenerate, commit
  both.
- **W4.3 accepted as reporting, REFUSED as running** — and rightly: *"a map that
  is the only instrument is not a map."* **W5.1's check writes a result artefact;
  the snapshot reads it.** With no file the panel reports **UNKNOWN, no result
  ever** — the visible form of "nothing runs the validator". **Blocking on
  llm-distillery: spec the artefact** (path, timestamp, per-defect-class counts,
  version stamp) so the reader can be written before the check exists.
- **Do NOT carry "Contract A is red on every cycle" onto the atlas** — it is a
  measurement *designed to become false*, and when W2.1 lands the sentence goes
  silently wrong. Counts become verify commands or nothing.

**Implementation trap for W5.1**, from pipeline-atlas: systemd units on sadalsuud
are **root-owned copies** installed by `deploy/install.sh`; `git pull` does not
update a changed unit. **A committed-but-uninstalled timer never runs — and a
check that never runs is indistinguishable from a check that passes**, which is
this plan's own thesis. The install step belongs in W5.1's definition of done, and
the snapshot should report the check **armed/not-armed**, not green/red.

**Two decisions with the right outcome and the wrong reason on record** — worth
naming as a pair, because it is the same shape twice in one plan:

1. **FluxusSource#164** keeps ~8 months of archives, justified as *"llm-distillery
   trains on this depth."* We do not read `data/archived/` at all. The retention is
   right for a different reason, recorded in *this* repo (`docs/TODO.md`): it is
   the only surviving copy of a displaced body, and therefore NM#306's only repair
   path. **Correct the reason, keep the retention.**
2. **ovr's `WebPage`-not-`NewsArticle`** was cited here as evidence that the
   schema.org question is closed. It is a choice of *type within* schema.org, made
   while **adopting** schema.org — as evidence about vocabulary adoption it points
   the other way. The scope call stands on its own grounds (four internal
   consumers, no external reader of the raw stream); its justification does not.

**Unmeasured hole spotted in passing, flagged not claimed:** `published_date` is
not in `validate.ts`'s required set, and `summarize.ts:866` falls back to
`rawArticle.published_date ?? new Date().toISOString()` — an article arriving
without a publication date is **silently dated "now" and ranks as maximally
recent**. Nobody has measured how often that fires.

---

## Filed by NexusMind, 2026-08-13 evening (their board, measured, no code committed)

- **NM#354** naive-on-arrival dates — needs producer-side sizing
- **NM#355** `_get_priority` non-strict tiering — the corrected version, explicitly
  **not** blocking the ceiling change
- **NM#356** `parse_published_date` returns aware datetimes unnormalized — the
  W2.7 prerequisite, and worth doing on its own for the `filtered_archiver`
  month-bucketing bug
- **NM#357** the validator grouping/labelling defect
- **NM#358** `format: date-time` declared and unchecked
- **NM#304** commented with the three additions, the `metadata:
  additionalProperties: true` scope correction, and the `_get_priority` retraction

---

## Round 2 — the sweep, 2026-08-14

**Method.** Swept all 20 directories under `veen-systems/` (16 git repos, 4 not)
for the *behaviour* — "reads structured data and checks it against a declared
shape" — across eight query classes rather than for any name: schema libraries
(`jsonschema`, pydantic), TS/JS schema libraries, other Python validation
libraries, required-field constants, missing-field accumulators, `validate_*`
definitions, validation error types, **DB-level DDL constraints**, and
**shell/`jq` field assertions inside CI and ops scripts**. Peer sessions
re-derived their own repos in parallel.

### The headline count is wrong again

Round 1 said **four**. The sweep finds **at least 21** under a consistent
definition. The four were not wrong, they were a subset selected by an instrument
that could only see one shape of thing.

**⭐ The single most telling result: a grep for TS/JS schema libraries
(`zod|ajv|yup|joi|superstruct|valibot|io-ts|typebox`) returns ZERO hits across all
20 repos — while `ovr.news/src/lib/data/validate.ts` demonstrably runs on every
cycle and drops rows.** Hand-rolled validators are structurally invisible to a
library grep. That is the miss shape, reproduced deliberately and confirmed.

### New on the news chain

| # | mechanism | runs? | why it was missed |
|---|---|---|---|
| **⭐ 6** | **`ovr.news/src/lib/db-schema.ts:179-199` — the `articles` table DDL** | **on every insert, unavoidably** | it is not a schema file and not code anyone calls a validator. **A SIXTH declaration of the row shape**, and the only *enforcing* one at ovr |
| 7 | `pipeline-atlas/ops/make_snapshot.py` | **every 20 min, 72×/day** | its name says "snapshot". **The estate's most-executed consumer-side shape check** — hand-rolled `isinstance` + key presence over two artefacts it does not own, plus a **cross-field consistency check** (re-derives newest run by `max(started_at)`, compares to the producer's declared `runs_order`) that no JSON Schema can express |
| 8 | `pipeline-atlas/_includes/ops-figures.qmd` | in every reader's **browser**, every page view | a validator written in JavaScript inside a Quarto include. Not a script, not a `.py`, no "validate" in its name or path |
| 9–14 | `gen_views.py --check`, `check_render.py`, `run_verifies.sh`, `check_framework_drift.py`, `smoke_architecture.py`, `publish.yml` | CI | six more; `gen_views.py --check` is *stronger* than schema validation — byte-identity against the projection of a declared source |
| 15 | `NexusMind/scripts/deploy_filters.sh`, `llm-distillery/scripts/deploy_to_nexusmind.sh` preflight guards | on deploy | shape checks on filter packages |

### ⭐⭐ The FIFTH Contract A mechanism — the only one that ENFORCES, and it validates against a hand-copied schema

*(Found by pipeline-atlas; **verified here against `main`**, not the feature branch.)*

`NexusMind/scripts/main.py:118`:

```python
# Contract A required fields (must match contracts/fluxussource-output.schema.json)
_CONTRACT_A_REQUIRED = frozenset({"id","title","content","source",
                                  "source_type","url","collected_date","content_hash"})
```

used inside the per-line load loop at `:1008`, which **drops the row**:

```python
if not self._CONTRACT_A_REQUIRED.issubset(article):
    stats.setdefault("schema_invalid", 0); stats["schema_invalid"] += 1
    if stats["schema_invalid"] <= 5: self.logger.warning(...)
    continue
```

**Verified 2026-08-14:** the frozenset and the schema's `required` currently match
exactly — both are the same 8 fields.

**Why this outranks the other four.** Of the mechanisms the plan names, this is
**the only Contract A check that runs on the production path and enforces.** The
others are the producer's own schema, ovr's TypeScript (Contract B), and two
unscheduled NexusMind validators. It is invisible to a validator sweep **twice
over**: it names no script, and **its only reference to the schema is a comment.**

⚠️ **The production gate and the schema are two artefacts with one name, and nothing
makes them agree.** The comment *is* the mechanism. **If W2.1 or W2.3 edit
`contracts/fluxussource-output.schema.json` and not `main.py`, the check validates
against the schema while production enforces against a copy that no longer matches
it — and both are green.** That is principle 3 with the roles reversed: the caller
exists, and the file it claims to follow is decorative.

⚠️ **And its output already goes nowhere.** `stats["schema_invalid"]` is counted per
cycle and logged five at a time. **Verified: `data/last_run.json` carries neither
`schema_invalid` nor `json_errors`.** So rows are dropped for Contract A violations,
counted, and **the count reaches no reader.**

⚠️ **Correction:** this document said the file's `stats` dict was *empty*. **It has
no `stats` key at all** — `'stats' in d` is `False`; the top level is seven flat
scalars. *Absent and empty are not the same, and reporting one as the other is this
repo's own dead-field trap.* Those seven **do** already flow to the atlas, because
`read_last_run` does `data.get("stats", data)` and surfaces every scalar it finds.
(`filter_stage_timings` is nested, so a scalar-scraping reader gets **seven, not
eight**.)

🚫 **ROUTED ASK 1 IS WITHDRAWN — it was cheap as an edit and WRONG AS A DESIGN.**
*(NexusMind, same day.)* This plan briefly recommended publishing `schema_invalid`
through `last_run.json` on the grounds that it was a one-key change costing the
reader nothing. **Verified: `_write_last_run_json` is defined at `scripts/main.py:3283`
and called at `:3577` — at the END of a pipeline run.** So for the key to be there,
something must compute it **inside the pipeline process**, which puts contract
checking back in the **cycle tail**, under the 4h `TimeoutStartSec`, in the same
systemd job as production scoring — **the one thing both consumers independently
ruled out**, and a constraint already recorded in this document.

> ⭐ **It was cheap precisely BECAUSE it rides a surface populated by the thing we
> agreed must not do the work.** "Zero work for the reader" is not a design
> argument; it is a description of who pays.

**The settled artefact has none of this**: a separate timer writes
`NexusMind/data/contract_check.json`, the snapshot reads that, `last_run.json` is
untouched. It costs the reader a second file read, not a publication path — **and it
buys the check its own liveness signal, which `last_run.json` cannot give it. A
stale `schema_invalid` inside `last_run.json` is indistinguishable from a fresh one,
because that file's timestamp belongs to the PIPELINE RUN, not to the check.**

**That is the second instance of this exact shape** — ovr's `validate.ts` drops rows
into a `warn` nobody reads. Two makes it a pattern, and it is the strongest argument
for W5.1's artefact: **the numbers already exist, they have nowhere to land.**

**Two routed asks (NexusMind's to accept or reject, not ours to make):**

1. Publish `schema_invalid` and `json_errors` in `last_run.json`. pipeline-atlas's
   snapshot surfaces every scalar in that file automatically, so they would appear
   on the atlas the same day with no work on the reader's side.
2. **Make "the frozenset equals the schema's `required`" a defect class in the
   artefact.** One line, and it is currently held together by a comment.

**⭐ Finding 6 in detail.** `articles` declares `title`, `url`, `source` and
`published_date` as `NOT NULL`, enforced by SQLite on every write. The
`published_date NOT NULL` constraint **can never fire**: `scripts/summarize.ts:866`
and `:1433` substitute `rawArticle.published_date ?? new Date().toISOString()`
*upstream of the insert*, and `validate.ts` does not mention `published_date` at
all — `grep -c` → **0**, with `grep -c 'title'` → **1** in the same file as a
control proving the instrument reads it (ovr.news session). So an article arriving
without a publication date is **silently dated "now" and ranks as maximally
recent**.

⚠️ **Causality corrected by ovr.news, and it reverses what draft 2 implied.** The
fallback is **not an oversight that happens to satisfy the constraint — it exists
BECAUSE of the constraint.** Without it, a dateless row throws on insert. So this
is a `NOT NULL` workaround, and the pair is the real finding: **a shape gate that
cannot fail, and a silent default written to keep it that way.** Neither half is
sloppy on its own; together they convert "we guarantee a publication date" into
"we guarantee a non-null string".

**Measured since: `published_date` is null or empty on 0 of 1,335,210 upstream rows
over 14 days**, so neither path fires today. **But the repair has an ORDER, and it
is not the obvious one** (ovr.news, 2026-08-14):

- **Require the field upstream FIRST.** The fallback then becomes dead code and can
  be deleted safely.
- **Delete the fallback first and a dateless row goes from a silent wrong date to a
  crashed pipeline run.**

So *"should `validate.ts` require `published_date`"* is a **sequenced decision, not a
tidy-up** — the fallback is not merely permitted by the `NOT NULL`, it is
**load-bearing for it**.

### ovr.news's own inventory — eight mechanisms, one of them a "validator" by name

*(Re-derived by the ovr.news session, 2026-08-14. Their library grep confirms the
miss shape from their side: zod/ajv/yup/joi/superstruct/valibot/io-ts return **0
files** under `src/`, `scripts/`, `functions/` and **0** in `package.json`.)*

Beyond `validate.ts` (drops rows at `:166`/`:191`; blind to everything outside
`['id','title','url','source']`) and the DDL above:

- **Two undeclared gates in series, not one.** The metadata projection
  (`summarize.ts:887`/`:1342`, since 2026-04-09) narrows to a single key, **and**
  an explicit field-by-field top-level mapping (`:825`/`:1028`/`:1335`) drops any
  top-level field nobody wrote a line for. **Neither announces itself, and a field
  must clear both.**
  ⭐ **Measured from the PRODUCER's side, which is stronger than inferring it from
  ovr's** (2026-08-14, NexusMind's filtered output on sadalsuud): `source_category`
  is present on **114,836 of 114,836 rows — 100% — and reaches ovr on none of them**,
  because the projection keeps only `quality`. Same for `word_count` at 113,667.
  Other named casualties: `stage_used`, `filter_version`.
- **`getArticlesForBuild`'s INNER JOIN on `summaries`** (`db-articles.ts:288`) — not
  a schema check, but structurally drops any article that failed summarization.
- **CODE LANDED AND LIVE ON THE HOST, CORPUS PENDING — ovr#321 / ADR-046,
  `60ada82` on master 2026-08-14.** ⚠️ **NOT `2583951`** — this document recorded
  that hash and it **no longer exists on any branch**: `origin` had moved under them
  (the pipeline's own auto-commit of `chain_metrics` / `qa-report` /
  `source-funnel`), so they rebased. Zero file overlap, tests and lint re-run green
  on the rebased state. *A commit hash recorded before a push is a claim about a
  history that has not happened yet.*
  ✅ **Verified ON THE HOST rather than inferred**: `git rev-parse HEAD` on sadalsuud
  returns `60ada829`, `src/lib/published-date.ts` is present, `db-articles.ts`
  carries the canonicalisation. **The write-boundary half is live**, which is the
  pull-before-backfill step. They checked on the box rather than trusting their own
  `git log` because of NexusMind's path-scoped-deploy warning. `parsePublishedDate` returns `null` rather than an Invalid Date,
  canonicalisation moved to the DB write boundary, and lint rule **[7/7] fails the
  build** on a bare `new Date(published_date)`. **The first declared-shape check on a
  field this plan is about.** Green on the committed state: 1,266 tests, lint clean,
  verify sweep 84/0, `tsc` byte-identical.
  ⚠️ **The BACKFILL IS AUTHORISED (owner, directly) AND NOT YET APPLIED.**
  **FS#171 stays blocked until ovr confirms it has RUN and been verified** — not when
  it was authorised, and the confirmation goes from ovr to FluxusSource directly.

  **Report-only against the real production DB, and the population was wrong all
  day:**

  | | quoted all day | actual |
  |---|---|---|
  | rows to rewrite | 6,000 | **21,700** |
  | sub-ms precision lost | 131 | **340** |
  | naive / offset | 98.87% / 1.13% | **99.64% / 0.36%** |

  **A trimmed 6,000-row hot copy stood in for the corpus, and survived a full day
  because the file is named `ovr.db` and looked like it.** Third instance of the same
  class. ⚠️ **The tell fired only because they went looking** — nothing caught it, and
  they had flagged the population caveat before running, so nothing downstream took
  the wrong figure.

  ⚠️⚠️ **IN FLIGHT, so it is not misread as the backfill's effect:** the pull is live,
  so the **~17:00 summarize run uses the new parser BEFORE the corpus is backfilled.**
  Every naive-dated row reads **2h younger** from that run onward, which moves the
  `recencyBoost` step and **changes which articles are selected.** That is the
  intended order — code first, corpus second — but **the selection change lands
  before the backfill does.** Anyone watching ovr's output in that gap is seeing the
  parser, not the backfill. Caveat from their own review: still host-dependent for non-ISO input (RFC 822
  etc.); exposure measured at **0 rows — latent, not live.**
- **`tests/contract-validation.test.ts`** — 22 cases, **on FIXTURES**. Worth naming
  separately: it is the only thing at ovr that *looks* like a contract check by
  name, and the only one that never sees production bytes.

**Line-number corrections to round 1**, from the same pass: `og_image_url` is read
at **`summarize.ts:336-337`**, not `:334`; `quality` is read back at **two** sites,
`transform.ts:292` (`sanitizeSourceQuality`) and `:324`.

### Off-chain, and this is where the plan should have looked first

**W5.1's problem is already solved twice inside the estate, on the energy chain.**

| mechanism | what it already does |
|---|---|
| `energydatahub/utils/data_quality.py` → `data/data_quality_report.json`, gated at `.github/workflows/collect-data.yml:83-95` | a result artefact + a scheduled caller + a gate that **fails when the file is MISSING**, and a severity ladder `critical > error > warning > info` (`data_quality.py:122`) with exactly one enforcing level — ADR-022's *stamp always, decide once*, already shipped |
| `energydatahub/scripts/detect_schema_drift.py` (`collect-data.yml:156`) | **a shape-drift tripwire with a scheduled caller**, comparing a shape signature against the previous commit's, with a deliberate exit-code taxonomy and a self-maintaining volatile/stable split. This is the contracts check, built, running, and unknown to the plan |
| `augur/scripts/wait_for_edh.sh` + `augur-daily.timer` | **a cross-repo reader of a result artefact on a systemd timer**, keyed on the artefact's own `timestamp`, with a written timeout policy |
| `art/sanderveen.art/scripts/validate_content.py` | real content vs a CMS schema, **two callers**: CI (`hugo.yml:55`) and a git hook |
| `RenkumSpot/.../content-validation.test.ts` | CI, over **real** JSON content, required-field + enum constants |

The artefact spec (`docs/CONTRACTS_CHECK_ARTEFACT.md`) is built on these rather
than invented.

### A category round 1 had no name for: FAKE validators

*(Raised by pipeline-atlas against their own repo; confirmed independently here.)*
Mechanisms whose **claim** is about behaviour and whose **evidence** is existence.
They inflate the estate's apparent coverage.

**Confirmed instance, and it is on the page W4.1 wants edited:**
`pipeline-atlas/_generated/contracts-table.qmd:10` (from `ops/gen_views.py:224`)
emits *"Declared in X, **validated against** Y"* for every contract edge — and the
only check behind the word *validated* is `<!-- verify: ls -1 X Y -->`. **Two
inodes exist, therefore validation happens.** The atlas asserts the signature
failure on the page where it commits it.

⚠️ **The category is NOT "existence-only", and getting this wrong sends someone off
to convert 42 healthy commands.** Estate-wide there are **44** existence-only verify
commands; pipeline-atlas audited their own — **102 verify commands, 4
existence-only, of which only 2 are the defect.** `ls -1 FluxusSource/config/sources/`
backing *"the registry is internal"* is **fine**: the claim is about location, so a
listing is direct evidence.

**The tell is: a check whose output does not change when the claim becomes false.**
Their second, worse instance: `reference/contracts.qmd` runs
`ls -1 FluxusSource/config/schemas/` under the claim *"still no schema for
logs_summary.json — the object's SHAPE remains undeclared."* **A negative claim
backed by a directory listing a human must read.** Add `logs_summary.schema.json`
and it prints five lines instead of four and still passes. Reading the *command*
cannot reveal this; you have to read the **claim** and ask what would falsify it.

That formulation also covers the `--self-test`-always-returns-0 register entry and
the `format: date-time` no-op. **Existence-only is a symptom; unfalsifiability is
the disease** — and it is mechanically testable by the mutation rule this repo
already has: simulate the defect, confirm the check goes red or empty.

### A live collision, and it is in THIS repo

*(Found by FluxusSource while inventorying their metadata namespace; verified here.)*
The plan's abstract point — *the blob crosses two contracts and is described by
neither* — has a concrete instance with a crash in it:

- FluxusSource emits **`metadata.sentiment` as a plain STRING** (32 rows in the
  current 7-day window, yfinance only: `"neutral"` / `"bearish"`).
- `llm-distillery/ground_truth/samplers.py:105` does
  `a.get('metadata', {}).get('sentiment', {}).get('compound', 0)` — i.e. it expects
  a **VADER dict**.

**On a string, `.get('compound', 0)` raises `AttributeError`; the `0` default never
applies.** The path presumably only ever sees NexusMind-enriched rows, so this is
**latent, not firing** — but it is the same key name meaning two things across a
contract boundary, which is precisely what an undeclared blob buys. FluxusSource has
marked their key RENAME. **Ours is a one-line fix and is not yet made.**

### 🔨 W2.4 is BUILT but NOT MERGED — and phase 0a's exit criterion was WRONG

⚠️ **Correction to an earlier reading in this session: `b8a191c` is NOT shipped.**
It sits on branch `fix/357-contract-validator-grouping` with two siblings —
`f55f708` (NM#356, W2.7's UTC normalization) and `99c74a4` (NM#304, "Contract A
meets production — 4 defects, source_group held"). **Main is at `010338d` and has
none of them; no PR has been opened.** The error came from reading `git log` in a
checkout that happened to be on that branch — *a branch is not a release, and `git
log` does not say which one you are on unless you ask.*

The fix itself reports **both units** — `"N error(s) on M row(s)"` — which is the
artefact spec's requirement E. It ships with 10 new tests that **do not share a code
path with the fix**, and reverting only the group key fails 5 of them. The test file
is covered by CI: `ci.yml:33` runs `pytest tests/` wholesale. *(Read `:29` alone and
you conclude it is not — the narrow line is listed first.)*

Their measurement, on 6 raw files / **10,677 rows**:

```
before: metadata [required] x751, message names only 'priority'
after:  metadata.priority   636 error(s) on 636 row(s)
        metadata.word_count 115 error(s) on 115 row(s)     (636+115 = 751)
```

⚠️⚠️ **PHASE 0a's EXIT CRITERION WAS WRONG AND IS REPLACED.** The plan said *"the
check reports per-row counts, verified against a hand count on one known class."*
**Insufficient — and it fails silently in the flattering direction.** Which field
disappears depends on **jsonschema's error order, not on the data**: the sadalsuud
run hid `priority`, this corpus hid `word_count`. So **a hand count on whichever
class happens to be printed reconciles perfectly while the other class is still
invisible**, and phase 0a signs off on a still-broken instrument.

> **New criterion, from NexusMind:** *the number of `required` groups equals the
> number of distinct missing properties.* That is what the merge actually destroys,
> and unlike a hand count it cannot be satisfied by the surviving half.

**Two further corrections to the plan's text.**

1. **"It hid the `priority` defect for five days" is a special case, not the
   defect.** The defect is that **an arbitrary one of the two is invisible**, chosen
   by error order.
2. **Do not reconcile 636/115 against the plan's 928/267/1,195.** Different corpora
   — 10,677 rows here, 21,636 over 6 cycles there. Adding them is the estate's most
   repeated error.

⚠️ **And instrument trap 1 was too narrow.** `memory/stamp-contract-integrity.md`
said the merge *"affects `required` only — `enum` and `maximum` key on leaf paths, so
78 and 2,774 are row counts."* **The counts survive; the breakdown does not.**
`(source_type, enum)` keys on the leaf, so every violating **value** merges into one
group carrying one example. On a corpus with both `social` and `data` violations the
report names **one of them**. Wherever you read violation counts *by value*, this
applies.

**Consequence for sequencing:** phase 0a is no longer a prerequisite to build — but
it is a harder prerequisite to *verify* than the plan claimed.

### ⚠️ "Zero callers" cannot be measured by grepping the script's name any more

Round 1's evidence was *`grep -rIl "validate_production_contract"` across five repos
returns zero files*. **It now returns 14 — and 13 of them are prose the five
sessions wrote while documenting the claim.** The grep measured its own
documentation.

The claim is about **callers**; a name-grep counts **mentions**. Restricted to
executable contexts the count is **1**, and it is the new unit test — a caller, not
a scheduler. So the durable statement is the one round 1 already insisted on:
**unscheduled**, never *never executed*.

`validate_contract_a` still holds at **3** mentions: its own definition plus this
plan and its memory file. **No caller.**

### Also established

- **llm-distillery has no `.github/workflows/` at all.** Our own
  `training/validate_training_data.py` is documented in seven places and invoked by
  hand. This confirms round 1's split — W5.1 is **specified** here and must be
  **implemented where it runs**, because there is no CI here to run it in.
### ⭐⭐ The thesis arriving as EVIDENCE: two hops, both internally consistent, disagreeing by two hours

*(Found by ovr.news 2026-08-14; **verified here on `main`**, independently.)*

The same naive timestamp is read as **two different instants** on either side of the
NexusMind → ovr.news boundary:

| hop | how a naive `published_date` is read | verified at |
|---|---|---|
| NexusMind | `pub_date.replace(tzinfo=timezone.utc)` — **UTC** | `src/scoring/display_ranking.py:180-181` |
| ovr.news | ECMAScript parses an offset-less ISO string as **LOCAL** | language spec; sadalsuud is CEST |

**Both then apply the same recency rule** — `recency_threshold_hours: 24`,
`recency_boost: 1.3` (`display_ranking.py:36-37`, applied at `:200`). So an article
NexusMind scores at 23h old is **25h old to ovr**: NexusMind grants the 30% boost,
ovr does not. And `getDisplayRank`'s fallback into NexusMind's `display_rank`
**silently mixes the two timebases**.

⭐ **Why this is the plan's central claim rather than another bug.** Neither hop's
contract could have surfaced it: **each is internally consistent, and neither
declares the field's SEMANTICS** — only its type. A schema saying
`"published_date": {"type": "string", "format": "date-time"}` is satisfied by both
readings. *A contract that describes shape and not meaning cannot catch a
disagreement about meaning*, and this one has existed for as long as both hops have.

**It also refutes "the timestamp work is cosmetic" for good.** W1.1's payoff is not
standards hygiene — it is that two systems currently disagree about which articles
are new.

### ⭐ The SECOND automatic production-bytes check — and it looks like validation without being it

*(NexusMind's inventory of 11 mechanisms; **verified here against `main`**.)*
`deploy/gpu-server/main.py:338` — pydantic v2 models on the scoring API, running on
**every scoring request**:

```python
class Article(BaseModel):
    title:   str = Field(default="", max_length=MAX_TITLE_LENGTH)
    content: str = Field(default="", max_length=MAX_CONTENT_LENGTH)
```

Three properties, all confirmed:

- **Both fields default to `""`.** A row arriving with no content is **accepted and
  scored as an empty string**. The boundary **cannot distinguish "the body failed to
  arrive" from "the body is empty"** — precisely the distinction NM#304 refused to
  destroy on `word_count`, destroyed here at a different boundary.
- **No `id` field.** Request and response are correlated **positionally**. A
  reordering or a dropped item is **undetectable at the schema layer.**
- **No `model_config`**, so pydantic v2's default `extra='ignore'` applies: **every
  other field of the row is silently discarded here.** Contract A and Contract B
  both stop at this boundary.

**Net: the estate's two automatic production-bytes checks assert, between them,
eight key names and two strings' maximum length.** That is the headline at the top
of this document.

### ⚠️ `jsonschema` is in NO dependency manifest — every schema mechanism runs on a coincidence

**Verified on `main`:** `requirements.txt` contains no `jsonschema` and no
`rfc3339-validator`, while `scripts/validate_production_contract.py` is the one
thing that imports `jsonschema`. CI works because `ci.yml:25` does
`pip install jsonschema pytest` **inline**; sadalsuud works because its venv happens
to have it. **A venv rebuilt from `requirements.txt` cannot run it.** The missing
`rfc3339-validator` is NM#358's whole point (instrument trap 2), so **NM#358 is a
two-part dependency change: `format_checker`, plus BOTH packages into the root
manifest.**

⚠️ **RETRACTED, same day: this section first said "three manifests, three absences"
and called NM#358 a three-part fix by counting `pydantic` too.** Verified since:
**zero files under `src/` or `scripts/` import pydantic** — it is used only by
`deploy/gpu-server/main.py`, a separate service whose **own manifest carries it**.
The two manifests are **properly separated, not jointly incomplete**, and the root
manifest is *correct* to omit it.

> **The shape matters more than the fact, because it is this review's own pattern:
> a defect claim was read off three correct greps without checking whether the
> absent thing was NEEDED.** Absence is only a defect relative to a consumer.
> ⚠️ **And note the direction: it escalated.** A three-part change sounds harder
> than a two-part one, **and nobody downstream re-derives a warning.** Errors that
> inflate an ask survive longer than errors that shrink one.

⭐ **Consequence for the artefact, and it is a hard requirement:**
`validate_production_contract.py` already exits **2** for "could not run" versus
**1** for "found violations" — a good distinction that is **worth nothing unless the
caller treats 2 as an alert.** Today *"no new violations"* and *"could not import
jsonschema"* both produce a non-1 exit. **The artefact must carry that distinction
explicitly** — see `status: "could_not_run"` in the spec. NexusMind's parallel:
`verify_decision_log.py` prints PARTIAL and exits 2 rather than passing, since
NM#326. ***Exit 2 = "I did not look" is a distinction worth stealing estate-wide.***

### ⭐ The un-reconstructed check already exists and has never been run

**`validate/validate_contract_a.py` reads FluxusSource's `data/current/`
DIRECTLY** — pre-mutation, no stamps to strip, no reconstruction.

That matters because `scripts/validate_production_contract.py` reads NexusMind's
**mutated** `data/raw/`, so it must strip `_commerce_*`, `_obituary_*`,
`_violence_*`, `nexus_mind_attributes` and `display_rank` to recover the producer's
shape. **It validates a RECONSTRUCTION of producer output, not producer output.**
(It prints the subtraction, which is right.) Its `--cycles` also **defaults to 2**,
so the default invocation sees a *window*, not the corpus.

> **If W5.1 wants producer bytes rather than our copy of them, revive
> `validate_contract_a.py` — do not write a new script.** The estate already
> contains the better observation point and has never run it.

⭐ **And the argument is stronger than "it reads the right directory"**
*(pipeline-atlas, verified on `main` for both scripts, so not branch-contaminated).*
`validate_production_contract.py`'s per-class counts are **conditional on its strip
list being complete.** If NexusMind adds a stamp and does not extend the strip, the
check begins reporting `additionalProperties` violations **against the producer, for
keys the producer never emitted** — a false red pointing at the **wrong repo**.

**That is the exact mirror of the frozenset drift class: two places that must agree,
held together by nothing.** It is therefore a defect class the artefact must carry
in its own right — `drift.strip_list_vs_observed_keys`.

**`validate_contract_a.py` has no such dependency**, because it reads the producer's
own directory. **It is the only Contract A check in the estate whose result does not
depend on a second list being maintained** — a much better reason to schedule it
than its `--latest` mode.

*(The script agrees with this framing in its own source: it carries the comment
"NexusMind MUTATES data/raw/*.jsonl in place … So data/raw is NOT FluxusSource's
output as emitted", plus a strip function documented as "Remove keys NexusMind adds
to data/raw after FluxusSource wrote it." The file named `raw` is **neither** the
producer's bytes **nor** the scorer's text — it is pre-enrichment too. pipeline-atlas
is proposing it for `reference/invariants.qmd` as an artefact **wrong in both
directions from its own name**, not for the contracts page, since the arrow's payload
has not changed.)*

**A second local pattern worth copying:** `tests/unit/test_aegis_export.py`
validates **the output of `export()`** rather than a stored fixture — *"the only
place in the estate where a schema automatically meets something a code path
produced."*

### ⭐ The `source_group` control is LIVE, DEMONSTRATED, and deliberately HELD

Independently re-derived by NexusMind, who **did not read this plan before
measuring**:

- Contract A: `additionalProperties: false` at the top level, 14 declared
  properties, **`source_group` not among them.**
- Producer emits it unconditionally — `content_item.py:838` in the to-dict path,
  field at `:408`, ADR-010.
- **Real bytes:** `data/raw/content_items_20260814_080752.jsonl`, **3,697/3,697 rows
  carry it.**
- **The one thing that could have made the control silently dead was checked:** the
  validator strips NexusMind's own stamps before validating, and `source_group`
  matches neither `NEXUSMIND_STAMP_KEYS` nor the `_commerce_`/`_obituary_`/
  `_violence_` prefixes. **It survives the subtraction.**
- **Run end-to-end it fires:** `<root> [additionalProperties] 3697 error(s) on 3697
  row(s)`, *"'source_group' was unexpected"*, **exit 1.** Not available in
  principle — demonstrated on production bytes.

**They fixed Contract A today and deliberately did NOT declare it**, having put the
tradeoff to their owner as *"declaring this spends llm-distillery's only
non-circular control"*. After their fix the same file goes from **5 defect classes
to exactly 1, and the 1 is `source_group`.**

⭐ **The decision is pinned in CODE, not a note:**
`tests/unit/test_contracts.py::test_source_group_is_deliberately_still_undeclared`
asserts a row carrying it is **rejected**, with a docstring saying to delete the test
in the same commit that declares the field. **Declare it and the test goes red and
names the consequence.** Also under *"Not changed, deliberately"* in
`contracts/CHANGELOG.md` 1.18.0. **W2.2 stays held.**

⚠️ **Caveat that cuts against the control's strength, and it is theirs:**
`source_group` is **INERT downstream, not merely harmless.** The ingestion gate is a
subset test (`_CONTRACT_A_REQUIRED.issubset(article)`, `scripts/main.py:1008`) and
`commerce.py` round-trips the whole dict through `json.loads`/`json.dumps`, so an
undeclared top-level key is **neither rejected nor dropped**. That is what makes
holding it free. **It also means the control measures the CHECK's sensitivity and
says nothing about the pipeline's** — never report it as evidence that anything
downstream would have caught the field.

### The `source_type` enum fix must not be scoped from the corpus

**Today's data: `{rss: 3535, api: 64, data: 98}` — `social` does not appear at
all**, and the 98 `data` rows are all ourworldindata. **So W2.1 scoped from the
older corpus ("add `social`") goes red on the next cycle.**

NexusMind instead declared the producer's **controlled vocabulary** —
`SOURCE_TYPES = {rss, api, social, data, video}` (`content_item.py`, ADR-008 item 5).
**Declaring only observed values writes a vocabulary the producer can already
violate.**

⚠️ **This plan's first relay of that got `video` BACKWARDS — corrected by
FluxusSource, and the correction is the point.** It was written up here as
"including `video`, which has never been observed", filed alongside Contract A's
declared-and-unemittable `email`/`web`/`patent`. **It is not that defect. It is the
opposite one.**

| | `email` / `web` / `patent` | `video` |
|---|---|---|
| in the controlled vocabulary | **no** | **yes** |
| has an emitter | **none** | **two** — `vimeo_aggregator.py:287`, `youtube_api_aggregator.py:391` |
| enabled today | — | **yes**, `vimeo` in `aggregator.enabled_sources` |
| rows in window | 0 | 0, because `vimeo` is in `aggregator-health-report.json` → `summary.enabled_without_record` |

**`video` is reachable, configured and silent — an estate health problem, not a
contract problem.** Narrowing the enum to the observed corpus would start rejecting
rows the moment `vimeo` recovers.

⭐ **And the stronger half: `social` is emitted — 466 rows in a 7-day window** carry
social-only keys (`all_domains`, `primary_domain`, from bluesky/mastodon/vimeo/
youtube). **So declaring from that single run's corpus would have rejected every
social row in the estate.** That is the *same single-run denominator error* the 96%
figure was retired over, arriving from the other end — one run measures which
aggregators were due in that tick, and here the consequence is a closed enum that
silently drops an entire `source_type`.

> **Write this down, because the principle does not say it on its own:**
> **"Declare from the REACHABLE set" reads as "declare from what you OBSERVED"
> unless someone states that they differ. Reachable means the code can produce it,
> not that it appeared in your window.**

⚠️ **Trap they hit and avoided:** grepping `source_type=` literals in FluxusSource
surfaces **`atom`** — which is `SourceConfig.source_type`, a feed's **wire format**,
a different vocabulary entirely (`content_item.py:340` says so). It was nearly
declared.

### Relayed to FluxusSource, not a plan item

`config/schemas/source_schema.yaml` describes `priority` as *"1=highest,
10=lowest"*. **Production is the opposite** — 10 is `disaster_alerts_gdacs_alerts`,
9 the major-outlet tier, 5–6 the long tail — and their own
`docs/CONFIGURATION.md` agrees with production. **The 1..10 range is sound and is
what the ceiling fix used; only the polarity string is inverted.** A consumer
copying that description would invert its own semantics.

### Still open after round 2

- **The artefact spec is written** (`docs/CONTRACTS_CHECK_ARTEFACT.md`) and revised
  once against pipeline-atlas's review, which rejected `"armed"` as a field, forced
  the path inside their systemd mount namespace, and added the "a defect class may
  be `null`-with-a-reason, never absent" requirement. **Not yet accepted.**
- **The document needs restructuring before it reaches a cold reader** — see
  pipeline-atlas's review: undefined terms on first use, four genres in one file,
  a third of the body superseded, and roughly a dozen figures that **this plan's
  own success will falsify** (`2,774`, `928`, "one commit ever", "34 undeclared",
  "no caller at all"). Their rule: *a figure is safe in prose only if the mechanism
  that produced it would have to change for the figure to change.* Not yet done.
- Invert every "returns zero" verify command — **and the obvious inversion does not
  work**: `grep -rIl X . | wc -l` prints `0` but still **exits 1** under
  `-uo pipefail`. Use `echo "n=$(grep -rIl X . | wc -l)"`, which isolates the exit
  status and labels the number. Also: **do not use the ` — expect …` suffix in this
  file** — that convention is `run_verifies.sh`'s and does not travel; the curate
  runner hands the em-dash to the shell as a filename.
- Owner decisions 1, 2, 4 remain open.

---

## Round 3 — implementing the redesign, 2026-08-14

**Trigger:** the owner put the llm-distillery session on implementing the Contract A
redesign (#112), starting with the (b) fields and then the envelope. Four peer
sessions were briefed and all four answered. **Nothing was committed in any repo;
no session edited another's checkout.** The envelope decision is
`docs/decisions/2026-08-14-contract-a-envelope.md`; only what that record does *not*
carry is below.

### What the peers changed in my brief — every one of the four found something

⭐ **Three of the four corrections landed on claims I had inferred from code shape
rather than measured, and each peer measured its own repo.** That is the division of
labour working; it is also the fourth occurrence of *don't infer runtime behaviour
from structure* in this thread.

#### FluxusSource — takes all four (b) blocks; four specifics wrong in my brief

Measured on sadalsuud `data/current/`, 7-day hot window, **152,422 rows / 47 runs**.

1. ⭐ **`had_timezone` cannot be captured where I pointed.** `normalize_timezone:175`
   does branch on `tzinfo` — but it is called from *inside* `parse_date_string`
   (:127, :145). By the time `extract_date_from_rss_entry:110` calls it again the
   value is **already naive**, so that second call can never see an offset. Capture
   belongs inside `parse_date_string`.
2. ⭐ **`precision` is new code, not a capture.** The dateutil path (:126) is tried
   *first* and succeeds for nearly everything; `common_formats` (:132) is only the
   fallback. So "which format matched" answers precision for the rare tail, not the
   common case — the date-only-stored-as-midnight problem is **the default path, not
   an edge case**. Producer will parse twice with different `default=` sentinels and
   diff which fields dateutil actually filled. Most expensive of the five.
3. **`fabricated` has two sites with two populations, and they don't compose.**
   `rss_aggregator:592-593` calls both back to back, and since
   `extract_date_from_rss_entry` defaults to `fabricate_fallback=True` it never
   returns None there — so `ensure_valid_date:214` is **dead on the RSS path** and
   live only for `fabricate_fallback=False` callers (feed-health staleness, FS#98).
   One stamp reading as one mechanism would be wrong.
4. **`element` needs a wider vocabulary than the 7 `date_fields`** — `entry.time.datetime`
   (:74) and the `tags` term fallback (:91) also answer.

**`collected.clock_source`: three clocks, not two.** Of 36 `collected_date=` stamp
sites: **28 naive `datetime.now()`** (local, wrong), 6 `utc_now()`, and **2
`DateParser.get_timezone_naive_now()` which are correct** — the third clock I missed.
My "~27 vs 6" also described the wrong population: across `src/aggregators/*.py` there
are 138 `datetime.now()` in 21 files, mostly **cutoff arithmetic, not stamps**. The
stamp population is 36 and it is the one that matters.

⭐ **Measured effect, and it reprices the field.** Local is UTC+2 on sadalsuud, so a
wrong-clock row is stamped ~2h ahead of an RSS row in the same run. Against the
per-run RSS median: **5,901 of 152,422 rows = 3.87%** sit at +1.98h, across 14
families (newsapi_general 2,804 · pubmed 943 · github 723 · ClinicalTrials 424 ·
hackernews 279 · CrossRef 253 · arxiv 167 · …). All 144,844 RSS rows and all social
sit at ±0.03h. **So `clock_source` is ~96% constant from birth** and the fix is
bounded and fully enumerated (28 sites, 19 files). Stamp-before-fix still holds — the
stamp is what makes the fix provable — but plan for a 4% field, not a coin flip.

**`fetch.*`: the trap is one layer below `resp.encoding`.** Every strategy in
`RobustFeedParser` returns `response.content` (bytes), and `_fix_encoding_issues()` —
where `charset_used` is decided — **never sees the headers**. Same shape as the date
five, one function lower. The vehicle already exists: `fetch_ctx`, a dict created at
`parse_feed:333` and threaded through all four strategies, already carrying
`saw_5xx`/`hard_http`. Open question they raised and I agree with: the ladder makes
several requests, so the triple must describe **the request that produced the returned
bytes** — last-success-wins, stamped only on the winning branch.

**`content_meta.kind`: `full_text` is unemittable for a second reason.**
`rss_aggregator` never reads `entry.content` at all (feedparser's `content:encoded`
mapping), only `summary`/`description` at :548 — so even a publisher serving full text
in-feed arrives as a summary. ⚠️ **And the discriminator cannot be attribute presence**:
`:548` is `getattr(entry, 'summary', getattr(entry, 'description', ''))` and feedparser
routinely supplies an **empty string** rather than omitting the attribute — the exact
shape that made `hasattr(tag, 'term')` wrong in FS#138. Test the cleaned body's
truthiness.

⭐⭐ **And the measurement that strengthens LD#93 beyond what the proposal claimed.**
Of 144,844 RSS rows: 7,529 empty body (5.2%) + 204 body == title (0.1%) = **5.3%
`headline_only`**. The other 94.7% are feed summaries — median body **143 chars**,
p10 70, p90 914; 60.0% under 200, **77.2% under 300**. So the 300-char floor discards
77.2% of RSS rows, and what it discards is overwhelmingly **complete feed summaries,
not truncated articles**. `kind` is what licenses saying so: length was never the
quality signal.

⚠️ **A presence rate for a recently-shipped stamp needs its window checked against
that stamp's ship date.** FluxusSource retracted a `feed_declared_language` figure
(108,038 rows / 70.9%) before it propagated — `language_source` shipped **mid-window**
(0% on 08-07/08-08, 26.2% on 08-09, 100% from 08-10), so any count over the 7-day hot
window measures the rollout rather than the field. **Same 2026-08-10 boundary FS#149's
confidence floor is already pinned to**, and nobody had connected that it equally
poisons presence counts. Clean-window figures, and the disjoint-populations trap that
kills the name `declared_by_feed`, are in the envelope decision record.

#### pipeline-atlas — Category G confirmed as model facts; six corrections

Confirmed the two refusal sites and the asymmetry (`model/chain.yml` `gate:` block,
`gate.qmd` Level 4; the model's own comment: *"Same word, 'skip'; opposite
consequences."*). **They are not taking the implementation** — that repo owns no
pipeline code. Corrections, sharpest first:

1. ⭐ **The grain is wrong for the RSS tier, and this is the one that makes the
   sidecar useless.** `concurrent_rss` is **one source name holding the entire feed
   tier** (the breaker registry keys on source name, so an open breaker refuses every
   feed at once). But `health_state` runs per *feed*, and `poll_interval_actual_h`
   comes from per-feed `update_frequency` for RSS vs `aggregator_frequencies` for
   everything else — **two registries**. A per-source row for that name either
   aggregates N feeds into one meaningless value or silently reports the first.
   **Decide the grain per tier, or the tier carrying most of the feeds is the one the
   sidecar cannot describe.**
2. ⭐ **`outcome` must be written at the refusal site, not derived.** Derived from
   `collection_stats` it inherits the defect it exists to expose: Site B's
   `_record_skip` output is *already* classified downstream as `empty_sources`
   (`'error' not in stats and items == 0`), so `refused_in_aggregator` and `empty`
   are indistinguishable there **by construction** — a field that can never emit two
   of its four values. The `uncomputed_at_callsite` variant arriving in the block's
   first field.
3. **`health_state` must name *which* health.** Three "healthy" counts across two
   files, no two meaning the same: `summary.healthy_feeds` (fetch reliability),
   `summary.states.HEALTHY` (freshness/cadence ladder), and
   `logs_summary.json → health.feed_summary.healthy` (an unmarked **copy** of the
   first, up to a day stale). Worse, `HEALTHY` on the ladder is the **fall-through** —
   it means *unclassified*, not *fine*.
4. **"Measured at fetch" requires adding a read that does not exist.** The collection
   path constructs the health tracker and only ever writes to it; there is no
   "should I fetch this?" query anywhere. A new coupling from collector into the
   health subsystem — fine if intended, but an explicit spec line, not a free field.
5. **The enum is refusal-shaped and misses a live non-refusal defect.** Site A has a
   third branch: a plugin in `enabled_sources` with no `aggregator_frequencies` entry
   and no self-scheduled declaration falls through to `else`, warns, and **collects it
   every tick** (FS#121) — a weekly source on the collection cadence. `outcome` has no
   value for *"fetched, but on the wrong cadence"*, and `poll_interval_actual_h` only
   exposes it if **measured from consecutive fetches**; read from config it confidently
   reports the interval the source is failing to be polled at.
6. **`poll_interval_actual_h` has two semantics with no flag distinguishing them** —
   the due-time advance is guarded on the name already holding a row in
   `data/source_states.json`, and rows exist only for aggregators carrying scheduling
   metadata.

#### ✅ The grain blocker RESOLVED — and it makes G smaller

*(pipeline-atlas, same day, unprompted: they had sent the problem without the
resolution and noticed the plan now blocked on it.)*

⭐ **The test is: which fields presuppose a fetch? The collision is entirely inside
those, and none of them is what G is for.**

Both refusal sites decide at **source-name** granularity. Site A selects source names;
Site B's breaker registry is keyed on source name — which is *why* an open breaker on
`concurrent_rss` refuses the whole tier **before per-feed dueness is consulted at
all**. So the non-event itself, the thing G exists to record, is **natively per source
name and has no grain problem**:

```
collection (per source name, per cycle)
  outcome         fetched | refused_pre_dispatch | refused_in_aggregator | empty
  refusal_site    "A" | "B" | null
  refusal_reason  disabled | not_due | circuit_open | no_feeds_due | ...
  first_seen_run  "collection_20260801_120500"
```

**The four colliding fields — `health_state`, `poll_interval_actual_h`,
`raw_item_count`, `items_emitted` — all describe *how a fetch went*.** By this plan's
own framing that puts them in categories A–F. They drifted in from the neighbours and
**brought the grain problem with them.** Move them out and G is clean, per source
name, and still the least-blocked item in the redesign.

Two refinements not to flatten:

- **`poll_interval_actual_h` may be worth keeping in G**, because it is per-*source*
  for exactly the population that needs it: the FS#121 collect-every-tick sources fall
  through `select_sources_to_collect` **precisely for having no per-feed scheduling
  metadata**, so for them there are no feeds to disagree about. It is per-feed only for
  `concurrent_rss`, which is not the overpoll case. Keeping it with per-tier semantics
  declared costs less than losing the only field that can expose #121.
- ⚠️ **`refusal_reason` at Site B's `no_feeds_due` exit is an AGGREGATE** over per-feed
  decisions — the one place a source-name-grained field summarises feed-level facts.
  **Name it as an aggregate in the spec**, or *"the tier was refused"* and *"no
  individual feed happened to be due"* arrive as the same value. That is the
  four-states-collapse-to-one shape G was written to stop, **reappearing inside G.**

**Ownership as they framed it:** they own the chain model, so the grain *fact* is
theirs to supply; the schema is FluxusSource's data model and the spec is this repo's.
Recommendation, not decision.

✅ **And their blind-spot section shipped** — `reference/contracts.qmd`, standing, so
silence there cannot be read as a pass. ⭐ **The never-walked detector's null result
travels with the claim as a verify command rather than prose, and it is
mutation-tested in BOTH directions**: a url-less key in an examined file moves it
0 → 1 and names it, **and a new else-branch file — the case the old check could not
see at all — now appears in a named not-examined list instead of vanishing silently.**

⚠️ **Quote that null as "0 among the files it examines, with 5 excluded and named",
never as "0, clean"**, and "shown capable of firing" carries "on the shape it
examines". ⭐ **The general form, volunteered by pipeline-atlas against their own
artefact one turn after correcting me for the same thing: an instrument's null result
is only as broad as its denominator, so THE DENOMINATOR HAS TO TRAVEL TOO.** The
scope error was committed hours after the rule it violates was written down — their
own logged finding that knowing a class does not reduce the first-attempt error rate,
it only ensures the error is caught.

**On readership, in their words:** if the sidecar's only consumer is the ops snapshot,
it has failed READER BEFORE STRICTER and `raw_item_count` has repeated itself one
level up. The atlas can *report* it; that is display, not readership.

⭐ **Two declared blind spots they named — classes no row-schema check can ever see:**

- **The non-event one level up.** The source loader walks one level: a key holding a
  `url` becomes a source, a key that does not is skipped *without descending*. **A
  block of European feeds sat `enabled: true` collecting nothing for most of a year** —
  no error, no warning, no zero-yield alert, because a source that was never walked
  cannot report zero. A contract check validates rows that exist; a source emitting no
  rows is invisible to it **at any strictness**. This is Category G's own argument one
  level up, and it is the strongest case for doing G.

  ⚠️ **The incident is evidence; the detector is not.** pipeline-atlas re-ran the
  config-shape check that would catch the class against the live config —
  **2,080 source keys, 0 with no `url` of their own, across the 107 of 112 files
  declaring a top-level `sources:` key.** ⚠️ **The other 5 were not examined and the
  output said so nowhere** — `bluesky_accounts`, `mastodon_accounts`,
  `vimeo_channels`, `youtube_channels` reach the same one-level walk via the loader's
  else-branch. *(Not a live defect: those tiers are collected by aggregators reading
  their own files directly rather than through `get_sources()`, so excluding them is
  correct and widening the check would cry wolf. The defect was that the exclusion was
  invisible. Fixed at `4b71a7b`.)* It has never returned a
  positive, *"and an instrument that has never fired has not been shown to be able
  to. It is written against the shape of the incident rather than validated by it."*
  ⭐ **That strengthens the case for G rather than weakening it** — the only existing
  instrument for this class is an unvalidated config-shape grep, not a check on the
  data. But the caveat has to travel with the claim, or this thread's own failure
  class arrives inside the argument for the fix.
- **Attribution through the reconstruction.** The strip list is a hardcoded
  enumeration, so a key added on the NexusMind side and not added to it is reported as
  a *producer* violation for a key the producer never emitted. The check detects
  correctly and **attributes wrongly**.

#### NexusMind and ovr.news

Both are carried in the envelope decision record: the `language` name collision and
the four measured violation classes (NexusMind), and the closed offset gate, the
offset-grammar hole, and the ingest confirmation (ovr.news). Two items from NexusMind
that belong here rather than there:

- ⚠️ **`validate_production_contract.py` printed `metadata [required] x222` for what
  is 203 rows** — errors merged across two fields, and the example it printed was
  `word_count` (the 19-row minority), so `priority` (203 rows) **never appeared in the
  output at all**. NM#357 reproduced live on today's bytes; cite it.
- ⚠️ **Unreconciled numbers.** This document records `priority`-absent at **928** and
  `word_count` at **267**; NexusMind measures **203** and **19**. Different corpora
  (mutated `data/raw` vs FluxusSource `data/current`) and possibly errors-vs-rows
  again. **Nobody has chased it. Do not quote either pair until someone does.**

### Status at end of round 3

| | |
|---|---|
| Envelope | ✅ **settled** — declare-before-emit, closed at every level, `language`/`source`/`item` excluded |
| Producer-side (b) work | ✅ **accepted by FluxusSource**, sequenced kind → clock → fetch → time |
| Consumer-side declaration commit | ✅ **LANDED** — owner lifted the stand-down directly; `012da1a` on `feat/contract-a-envelope-declaration`, unpushed. Outcome test on 7,478 live rows: **introduced no new class** (⚠️ NOT "4 → 1" — the branch base 1.18.0 already read 1; the 4 → 1 belongs to NM#304/#356/#357). Hold unspent, falsification controls green. Based on **#360, which is a prerequisite** — the criterion cannot pass on `main` |
| `published.instant` offset | ⛔ **gate closed** by ovr.news; reopens when their write-boundary integration test exists and is green |
| Acceptance control | ✅ **resolved by splitting** — repeatable canary for "detection fires", declared gap for "catches the unanticipated" |
| `origin.*` | ⏸ **sequenced separately**, `docs/proposals/contract-a-origin-sequencing.md`; T0 (GDELT passthrough + `origin.method`) is the only engineering tranche |
| Category G sidecar | ✅ **grain decision TAKEN 2026-08-14** — move `health_state`/`raw_item_count`/`items_emitted` out to A–F (they carried the grain problem in), keep `poll_interval_actual_h` with per-tier semantics declared, name `refusal_reason` an aggregate, write `outcome` at the refusal site. G is then clean and per source name. ⏸ **now awaiting an implementer, not a decision** — candidate FluxusSource, after the (b) sequence. Two spec lines still owed: the "measured at fetch" read does not exist, and the enum has no value for FS#121. Detail in `docs/TODO.md` |

⭐ **Both halves are now unblocked.** The producer's declaration commit is written and
parked behind the consumer's, which has landed. What remains open is scope, not
permission: whether the rename ban extends past the three language keys (if it does,
`feed` collapses to `ttl_declared` alone), and whether `content_meta.kind` stays
RSS-only.


---

## Round 3 addendum — two blockers found by checking, 2026-08-14 late

### ⛔ 1. `NM#360` does NOT merge cleanly, and "merges clean" was a stale observation

```
gh pr view 360 --json mergeable,mergeStateStatus
  {"mergeable":"CONFLICTING","mergeStateStatus":"DIRTY"}
  9 ahead / 6 behind main · 14 files · CI green (test + GitGuardian, 14:18-14:23Z)
```

⚠️ **CORRECTED AGAIN, by NexusMind, against their own favour — it was not stale, it
was WRONG.** `origin/main` is at `4758226`, **the identical commit it was at when they
checked**. Nothing moved. Their command used the **old 3-arg `git merge-tree`, whose
output format does not emit the markers they grepped for**, so it returned 0 matches
and was read as 0 conflicts.

⭐ **A check whose pattern cannot match the thing it looks for reports clean whatever
the truth is** — a control that cannot fail, which is the exact class this thread has
been naming in everyone else's work all day. *(So my "a merge state is a relationship
with a moving branch" was a tidy generalisation of something that had not happened.
Correct in general; not what occurred here.)*

Verified properly, `git merge-tree --write-tree` exits 1:

```
CONFLICT (content): memory/MEMORY.md
Auto-merging  memory/project_session_2026_08_14.md   (clean)
```

✅ **Exactly one conflicted file and one conflicted ROW inside it — a docs index row.
No code conflicts at all.** `main` says *"MORNING ONLY — not current state"*; #360 says
*"Current state — no code changed"*. Both were true when written and both are
combinable. **So #360 is a small unblock, not a large one.**

**NexusMind's recommendation, which I endorse: merge `main` in, do not rebase.** #360
is a pushed PR with a green CI run from 14:23Z; rebasing 9 commits over 6 force-pushes
the branch, discards that CI result, and can replay the conflict several times. A
merge resolves it once, in a table row.

### ✅ And that conflicted row CLOSES the 928/267 vs 203/19 discrepancy

Both of us had recorded it as unreconciled. **#360's own side of the conflict already
contained the answer and neither of us had read it:**

> `priority`-absent vs `word_count`-absent was recorded as **928 / 267** — **that pair
> is host- and window-dependent** (sadalsuud's last 6 at midday 2026-08-14: 901/252;
> this checkout's last 6: 636/115) and must never be quoted without its corpus; the
> stable finding is that `word_count`-absent is a strict SUBSET.

Confirmed independently on the 7,478-row sample: all **19** `word_count`-absent rows
are among the **203** `priority`-absent ones. ⭐ **So the reconciliation is: the RATIO
is corpus-dependent and unquotable; the SUBSET RELATION is the stable finding.** Both
measurements were right and neither was comparable — the fourth
denominator-must-travel instance in this thread, and the answer was sitting in a
branch nobody had merged.

### ⛔ 2. RETRACTED: nothing downstream protects ovr from FS#171

I told ovr.news that NexusMind's `astimezone(timezone.utc)` stood between
FluxusSource's FS#171 and ovr's 20 lexicographic sort sites. **False, and backwards.**

**NexusMind RELAYS `published_date` byte-for-byte; it does not produce it.**
`scripts/main.py:1505` emits `article.get("published_date")` verbatim;
`parse_published_date` serves only *their* freshness cutoffs, archive buckets and
dedup, and **its return value is never serialized to output.** Proven by joining raw
to filtered on `id`: **6,024 matched rows, byte-identical strings, zero reformatted.**

**Consequences, both inverted from what I recorded:**

1. **The two-spelling defect is FluxusSource's, not NexusMind's.** The
   `+00:00`-with-microseconds form is in the producer's own bytes
   (`2026-07-13T15:23:03.480000+00:00`): **0.21%** of 7,478 live raw rows, **1.03%** of
   195,233 local raw, **0.58%** of 1,133,205 filtered — one phenomenon measured at
   three points on a pass-through, and it matches ovr's independent 68/6,000.
2. ⛔ **FS#171 is an ovr-facing hazard TODAY**, gated only on FluxusSource not yet
   emitting offsets. When it does, `+02:00` lands in ovr's filtered JSONL **unchanged**.
   ovr's offset test is not a guard on a hypothetical path; it is the real thing.

⭐ **And the fix moves repo.** Making it `Z` in NexusMind would mean **rewriting
producer data on a relay path** — a materially larger decision than a serialization
tweak, and the wrong site: **fixing it in FluxusSource fixes it for every consumer at
once**, including any that never read NexusMind. NexusMind declined and put
relay-verbatim to the owner as a property to keep or lose deliberately, which is
right.

⚠️ **The fix is a single canonical serialization, not an offset choice.** The prefix
collision (`'…T13:32:48'` is a prefix of `'…T13:32:48.480000+00:00'`) comes from the
**microseconds** as much as the offset — two rows at the same second with different
sub-second precision collide identically. And it is separable from W1.1: it changes
no instant and no ordering semantics, so it is not gated on ovr#321 or the clock fix.

*(Sixth wrong-sentence-beside-a-correct-finding here, and the costliest: it would have
sent the fix to the wrong repo AND left ovr believing they were protected.)*


### Round 3 addendum, later — the tie defect is 9 not 17, and the corrections cancel

**ovr.news, correcting their own figure in this record's disfavour.** ADR-046's *"17
unordered pairs share a second across the two shapes"* **overstates it.** Sharing a
*second* is not being the same *instant*: `'…T13:32:48'` vs
`'…T13:32:48.496000+00:00'` differ by 496ms, and text order is **correct** for them.
Exhaustively, naive-vs-`+00:00` has **0 inversions**.

**The true equal-instant / unequal-text count is 9** — all whole-hour timestamps where
the aware spelling carries no fraction (`…T04:00:00` vs `…T04:00:00+00:00`). It
remains the only thing that bites **without** an offset.

⛔ **AND THE 9 IS ALSO WRONG — it is 31.** ovr's own follow-up: the unit fix above was
right, **the population was not.** `data/ovr.db` locally is the **hot copy** —
`create-hot-db` trims to 6,000 rows and keeps the filename. Production is **21,743**.
Re-measured there: **31 cross-spelling row pairs across 14 colliding instants,
involving 45 rows.** *"All whole-hour"* was also false — 7 of 14. ⭐ **So the
correction that fixed a unit error repeated the population error it was fixing, inside
the paragraph fixing it.** Quote **31**.

⚠️ **Same class again, same session:** the NexusMind census quoted here as *"34,744
naive + 184 aware of 34,928"* was a **two-files-per-lens sample presented as a
population.** The real figure over all 548 files is **1,133,205 rows, 99.42% naive,
0.58% `+00:00`** — which is the number NexusMind independently produced. The
pass-through conclusion survives and is *stronger*; the denominator was invented.

⭐ **So the two corrections move in OPPOSITE directions: the offset half is bigger
than recorded and the tie half is smaller.** Neither side should claim the net
position — this record had the mechanism backwards (NexusMind normalizes ⇒ ovr
protected) while ovr had the disproof sitting in their own numbers (**99.5% naive
output is impossible if NexusMind serialized its own aware parse — an aware datetime
cannot `isoformat()` to a naive string**). The original ranking survived by accident
on both sides.

### ⭐⭐ Predicate-vs-outcome, finally as a MEASURED result

The thread's running example was an argument: *"`published-date.test.ts:113` tests the
helper, not the path, and would stay green if canonicalisation were deleted."* ovr
built the outcome test and mutated the invariant to check:

| with `canonicalizePublishedDate` deleted from `db-articles.ts:141` | |
|---|---|
| ovr's new outcome test | **fails 7 of 9** |
| `published-date.test.ts` | **22 / 22 PASSING** |

**A green helper suite over a corpus that has silently reverted.** What makes it hold
is that `create-hot-db`'s prune was *extracted* so the test exercises the real `DELETE`
statement rather than a copy of it. **Cite this rather than the argument.**

*(Also shipped there: `FilterStats.validation` as the Contract B drop reader —
persisted, printed when non-zero, on the ops dashboard, and left **optional** so
absent ≠ zero for runs predating it. And `compareByPublishedInstant` with an
`article_id` tie-break so idempotent re-merges don't churn the month file.)*


### ⭐⭐ The spelling defect has FOUR classes, and the biggest one has no offset at all

**FluxusSource measured their own bytes** — hot window, 152,422 rows, 2026-08-07→14:

| spelling | rows | share |
|---|---|---|
| `…T09:12:03` — naive, no micro (canonical) | 148,147 | 97.195% |
| `…T01:41:14.720000` — **naive, MICROSECONDS** | **2,797** | **1.835%** |
| `…T06:51:12+00:00` — offset, no micro | 940 | 0.617% |
| `…T23:20:42.720000+00:00` — offset + micro | 538 | 0.353% |
| **non-canonical total** | **4,275** | **2.805%** |

Zero `Z`, zero non-zero offsets — those halves hold.

⛔ **The microsecond-only class is the LARGEST non-canonical population and is
invisible to any offset-based query.** 2,797 rows carry sub-second precision with **no
offset at all** — nearly **double** the entire offset-bearing population (1,478). This
record said microseconds matter *"as much as"* the offset; on the producer's data they
matter **roughly twice as much**, and ⭐ **a fix framed as choosing between `Z` and
`+00:00` would leave the biggest class untouched.**

**The collision is live at the producer too, and mostly not about offsets.** Grouping
every `published_date` to the same UTC instant at second precision: **459 seconds in
the 7-day window carry more than one spelling of that same instant**, and four of the
first five differ by microseconds only.

⚠️ **Do not read 459 against ovr's 9 as a discrepancy** — different populations (a
7-day producer window vs ovr's hot DB) and different units (*seconds carrying multiple
spellings* vs *unordered pairs*). Only the direction transfers.

⭐ **And this decides the fix SITE: it is not a rogue producer.** **207 distinct
sources** are affected across all three source types — `french_le_parisien` (700),
`newsdata_eval_td` (178), `mastodon_engineering` (172), `kathmandu_post`,
`nikkei_asia`, `sydsvenskan`, the `gdelt_*` arms. It is **publisher-supplied precision
flowing through untouched**, so a per-producer fix is 207 fixes and is wrong again for
producer 208. **It has to be canonicalized where the value is STORED** — one site in
`ContentItem`, the same rule that put `redact_secrets`, tag normalization and language
folding in one place each — and that fixes every consumer at once, including any that
never read NexusMind.

**Separable and ungated**, confirmed by the producer: `…T13:32:48+00:00` → `…T13:32:48`
changes no instant under naive-means-UTC, and dropping `.480000` discards precision no
publisher meaningfully asserted. Neither touches ordering *semantics* — it makes
existing values self-consistent, which is what the text sorts already assume. **Own
issue, not riding the three-part gate.**

⏸ **NOT STARTED.** New scope beyond the four items, rewriting bytes on a live field
with ~20 downstream sort sites. With the producer's owner, correctly not taken on a
peer's report.

✅ **`content_meta.kind` moved to top-level** (⚠️ **`7bc20a0`**, branch
`feat/contract-a-content-meta-kind`, **unmerged** — the hash first recorded here,
`f3e8954`, was **amended away**: it is an ancestor of no branch, lives only in
FluxusSource's reflog and is GC-eligible. Corrected 2026-08-14) — it also needed the producer
schema to declare it, since that root is `additionalProperties: false` and
`validate_output.py` exits 1. Replayed over 5,995 prod rows: emitted on exactly the
5,739 RSS rows, **0 schema violations**, kind split unchanged. 22 tests, suite 1,224
green.


### ✅ #360 green, #364 open — and a green tick that is not a test result

**NM#360** merge-forward done (`origin/main` merged in, **not** rebased — it was a
pushed PR with a CI result, and rebasing 9 over 6 would have force-pushed and replayed
the conflict). `5b86c5f..5fb92d9`. **Verified independently from this repo:**

```
gh pr view 360 --json state,mergeable,mergeStateStatus
  {"state":"OPEN","mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}
```

Ready to merge, **waiting only on the owner** — NexusMind correctly did not merge it.

The conflicted row **was** the 928/267 reconciliation, and resolving it meant combining
both sides rather than picking one, plus the third corpus (203/19) and the invariant
promoted to the headline: **`word_count`-absent is a strict subset of
`priority`-absent** — the part that survives every corpus.

**NM#364** open behind it — `feat/contract-a-envelope-declaration` →
`fix/357-contract-validator-grouping`, 1,305 tests green *locally*, acceptance still 1
class on 7,478 production rows.

⚠️⚠️ **#364 SHOWS "ALL CHECKS PASSED" AND HAS NOT RUN THE TESTS.** `.github/workflows/ci.yml`
triggers on `pull_request: branches: [main]` only, so a **stacked** PR gets GitGuardian
and nothing else. Confirmed from here:

```
gh pr view 364 --json statusCheckRollup
  checks: [ {"name":"GitGuardian Security Checks","conclusion":"SUCCESS"} ]
                        ← no `test` job, at all
```

⭐ **A green tick whose meaning is "the tests were not run" is the purest instance of
this whole thread's failure class** — the signal exists, is truthful about what it
measured, and is read as something it never claimed. It gets real CI the moment it
retargets `main`, i.e. after #360 merges. **The only test evidence for #364 today is
that someone ran them locally and said so.** *(Flagged by NexusMind unprompted, which
is the right instinct: the danger is exactly that nobody looks at which checks ran.)*


### ✅ #360 MERGED, #364 green on real CI — and a two-session collision

**NM#360 merged** `7d1086f`, 15:55:32Z. **NM#364 retargeted to `main` and its `test`
job ran for the first time.** Verified from this repo after the fact:

```
#364  base=main  mergeable=MERGEABLE  mergeState=CLEAN
      test=SUCCESS   test=SUCCESS   GitGuardian=SUCCESS
```

So the 1,305 local passes are now corroborated by real CI on the merged tree. **Not
red** — but it was worth forcing, because until then the only evidence was someone
saying they had run them.

⭐⭐ **Three mechanism findings, none of which is about this PR:**

1. **`--merge` without `--delete-branch` leaves a stack pointing at a merged branch,
   silently.** GitHub's auto-retarget fires only when the base branch is *deleted*.
2. ⭐ **Retargeting does not re-run checks under default `pull_request` types**
   (`opened`, `synchronize`, `reopened` — a base change fires `edited`). So a
   *corrected* PR can carry a stale empty green, **and this is the nastier one,
   because the correction increases the PR's apparent legitimacy while changing the
   evidence not at all.**
3. ⭐ **Two sessions given the same owner "go" will both act, and the duplicate-work
   fingerprint only appears afterwards.** Here: `gh pr merge 360` returned *"already
   merged"* to the NexusMind session — this repo's merge had landed seconds earlier —
   and both sessions then close/reopened #364, leaving **two `test` check runs** as
   the visible trace. **Cheap only because every action taken was idempotent** (merge,
   retarget, reopen). It would not have been if either side had pushed a commit, and
   the other session nearly pushed an empty one to fire CI before choosing reopen.
   **Convention worth adopting: under one owner instruction spanning repos, say which
   side is taking the action before taking it.**

⚠️ **And one more state-vs-mechanism instance, self-reported.** The NexusMind session
told the owner #364 *"auto-retargeted to main"*. It did not — this session retargeted
it with `gh pr edit`. They read the *state* (`base: main`) and inferred the
*mechanism*, without checking that the branch had been deleted. It had not.
**Reading a state and inferring what produced it** is the same move as their
`merge-tree` grep and as every wrong-sentence-beside-a-right-finding in this thread.

⏸ **`published.instant` remains DROPPED and CONTESTED** — the one thing in #364 that
is not settled, recorded there as a live decision with the foreclosure argument
attached.

---

## Round 4 — the check is live, and four records were stale, 2026-08-15 evening

**Run from llm-distillery (W5, oversight). Three peer sessions took the work; this repo
wrote no code in any other repo and deployed nothing.** Every state figure below was
re-derived here — from NexusMind `main`, both peers' git logs, and `systemctl` on
sadalsuud — **not taken from either session's report**, which is the only reason the
staleness below was visible at all.

### ⭐⭐ THE FINDING OF THE ROUND: a handoff table decays faster than any other record

Four entries in `docs/TODO.md` described work as *awaiting the owner* that was already
committed, merged, installed, or deployed:

| entry said | actually |
|---|---|
| FluxusSource Track A: *"owner: commit + deploy"*, *"the only owner decision left"* | **committed AND deployed** — `08c4f56`, deploy recorded `0fb7a57` |
| NexusMind: *"owner: commit"* at 1.21.0–1.23.0 | **1.24.0 merged** (`8e9c489`) |
| the canary: *"only the automatic caller is missing"* | **merged (#361, `1c2f20f`) AND installed**, units loaded and armed |
| W2.2: *"open, unstarted"* | the control has **fired and been reported** |

**None of it was anyone's error.** A handoff table describes *other repos' states*, and
**nothing in this repo changes when they move** — so it is the one record with no local
event that can falsify it. The general form, worth the catalogue:

> **A record whose subject lives in another repo has no local trigger for being wrong.**
> Freshness has to come from re-deriving it, because staleness here produces no symptom.

Cost, had it not been re-derived: three briefs would have asked for work that was done,
and an owner decision would have been put on a storage commitment that had already
shipped.

### ✅ The canary is live, and it DETECTS

```
nexusmind-contract-check.timer    LoadState=loaded  ActiveState=active  LastTriggerUSec=  (EMPTY)
next elapse                       Sun 2026-08-16 02:22:48 CEST
artefact  /home/jeroen/local_dev/NexusMind/data/contract_check.json   0644 jeroen:jeroen
          generated_at_iso 2026-08-15T13:06:08Z   rows_validated 2722
          validator.commit 1c2f20f   contract.commit c06cbd9
  drift.contract_a_frozenset_vs_required     asserted=true   errors=0    clean
  published_date.format.date_time            asserted=false  (NM#358)
  unreported.schema_invalid                  asserted=false
  additionalProperties.<root>.source_group   asserted=true   rows=2722   errors=2722   error
```

⭐ **The acceptance control fired against genuine producer bytes** — the check detects a
field it was never shown, not merely runs. That is the precondition W2.2 was waiting for.

### ⛔ And W2.2 is STILL held — because my acceptance criterion was the defect

I wrote the release test as *"a new `generated_at_iso` whose run you did not invoke by
hand"*. **NexusMind refused to bank it**, correctly: a `systemctl start` satisfies that
sentence **while being a hand invocation one level up**. The 15:06 artefact was hand-run;
`LastTriggerUSec` is empty; the timer has never fired.

> ⭐⭐ **A criterion written to catch the unreachable-mechanism shape was itself an
> instance of it.** `LoadState=loaded` proves installation. A hand `systemctl start`
> proves the unit *definition*. **Neither proves a caller.**

What the manual unit run **did** retire, and it was a real risk: `ProtectSystem=strict` +
`ProtectHome=read-only` + `ReadWritePaths` do not block the artefact write, and
`SuccessExitStatus=0 1 2` handles the by-design exit 1.

**Third session pushed to spend this control early, third refusal.** Cost of waiting: ~11
hours.

### ⭐ Replacement control found — and it is a WEAKER KIND, which must travel with it

NexusMind's in-repo test names two release conditions (an automatic caller **and** a named
replacement control). The second is now discharged: **`eval_query` on a pinned historical
collection** (`collection_20260811_080541`: rows 51, errors 51) is a producer-chosen field
on producer-delivered bytes that the check was never shown — non-circular in the way a
synthetic injected key is not — and **frozen**, so the producer can never fix it away.

⚠️ **Its limit is the sentence that must not get dropped: it fires on PINNED BYTES, NOT
CURRENT INPUT.** `source_group` fires on every live run. **Spending `source_group` trades a
live-path control for a fixture-path one**, and that belongs in the commit that spends it.

⚠️ **And the fixture itself moves on 2026-08-18** *(FluxusSource, verified in
`file_rolling_window.py:163`, not inferred)*. It is **not** deleted — #164 holds — but the
7-day window **relocates and gzips** the collection: `data/archived/collection_20260811_080541.tar.gz`,
member `collection_20260811_080541/content_items_20260811_080540.jsonl`. ⚠️ **The directory
is `…080541` and the JSONL inside is `…080540`** — one second apart, so a member path built
from the directory's timestamp does not exist; and it is a tarball, so opening the path
directly breaks even once the path is fixed. ⭐ **The right answer is neither path: copy the
file into NexusMind as a test fixture.** A control living in the producer's data directory
is a control the producer's retention policy can move — the same class of assumption that
started this thread. (51 rows across 5 sources, so it exercises more than one producer.)

### ⚠️ `eval_query` is DEAD BY DECISION — and both figures I first recorded were wrong

**Retired deliberately**: `eda28eb`, *"retire the three #119 eval arms (#158, ADR-007
decisions 2 and 3)"*, authored 16:53:11 +0200 on 2026-08-11 and pulled onto sadalsuud at
**16:56:08**. Five identities stopped — `newsdata_eval_{td,mg,bi}`, `gnews_eval_td`,
`gdelt_constructive_madagascar` — with both switches thrown (`enabled: false` **and**
removal from `aggregator.enabled_sources`).

⚠️⚠️ **CORRECTION (a) — I recorded the stop FOUR DAYS EARLY, and the zero I trusted was a
partial run.** This section first said the field was *"present through
`collection_20260811_080541`, then exactly 0 in all 26 collections since
`collection_20260811_095038`"*. **`…095038` is an off-grid run that processed 4 sources /
933 items** against a full cycle's ~1,950 / ~5,700, **and ran no eval aggregator at all**
(`items_by_source` carries no `*_eval_*` key). **Its zero means *did not run*, not *ran and
yielded nothing*.** The field was still emitted at 12:08 (16 rows) and 16:06 (9 rows).

⭐ **The true edge is 16:06 → 17:02 — six minutes after the deploy, cause and effect with no
gap.** And single-run zeros were normal throughout the emitting stretch (the arms yielded
2–51 rows per run), so **no single zero was ever evidence of anything.**

> **Rule: bound a stop by LAST NON-ZERO → FIRST ZERO, and verify the run between is a FULL
> one.** A partial run's zero is the same byte as a real zero. This is *establish what your
> source excludes* landing on **a run**, where the excluded thing is most of the corpus.

⚠️ **CORRECTION (b) — "511 is cumulative history" is also wrong.** It is exactly the
**7-day hot window**: 26 runs, `collection_20260807_160813` → `collection_20260811_160635`,
summing to 511. `data/current/` is a rolling window, so **that figure decays to 0 around
2026-08-18** as the 08-11 runs age out. Recorded as a lifetime count, it would later read as
the corpus having lost rows. The lifetime figure is in `data/archived/` (retained
indefinitely since #164) and is uncounted.

⚠️ **Not a divergence, and the tidy-up it invites is destructive.** FluxusSource's own
`config/schemas/output_schema.json` **must keep declaring `eval_query`**: their root is
`additionalProperties: false`, and `validate_output.py --archives` samples the indefinitely
retained archive, whose rows carry the field. **Contract A undeclared + producer schema
declared is correct — different windows, different jobs.**

⭐ **Two undeclared root fields, opposite in time, indistinguishable by count:**
`source_group`'s *"20.5%"* is a **field that started** (0% before 2026-08-13 16:57, 100%
after); `eval_query`'s *"511 rows"* is a **field that stopped**. **A count with no time axis
reads as a standing condition in both cases**, and the presence check keys on run date in
opposite directions. Fifth denominator-must-travel instance in this thread.

**Owner ruled on the corrected premise: `eval_query` stays UNDECLARED and NM#367 closes as
a written decision.** *(An earlier answer of "declare as expiring" was given on my wrong
premise and changed the moment the measurement reached them — the value of putting a
correction back rather than absorbing it.)* Open with FluxusSource: was the stop
deliberate? If not it is a silent emission stop and its own defect; the ruling stands
either way.

### ⚠️ My `INVOCATION_ID` proposal was defective in the one direction that matters

The artefact could not answer *"who ran this"*, so I proposed stamping systemd's
`INVOCATION_ID`. **systemd sets it for a service and every child inherits it through the
environment** — a person running the script by hand from a terminal inside a scope unit
would be stamped `trigger: "systemd"`. **A false positive rendering a hand run as
automatic, and a one-sided test passes against it.**

NexusMind replaced it with the leaf of `/proc/self/cgroup` compared to the unit name — not
inheritable across units, because the kernel moves a process into the cgroup of whatever
unit actually started it — verified against a real transient service, an ssh shell, and the
terminal that was the ex-false-positive. Shape (additive, schema stays 1):

```json
"invocation": {"trigger": "systemd"|"manual", "invocation_id": "…"|null, "unit": "…"|null}
```

`unit` is published rather than collapsed into the boolean so an unexpected unit is visible
instead of rendering identically to a shell run; `invocation_id` is populated only when the
unit is ours. ⚠️ **`trigger: "systemd"` still does not mean the TIMER fired** — a hand
`systemctl start` is genuinely systemd; `LastTriggerUSec` + a fresh `generated_at_iso` is
the pair that answers it. ⚠️ **Absent means UNKNOWN, never "manual"** — absence dates the
artefact, it does not describe the run.

*Found in passing by NexusMind:* both unit files still carried `# NOT INSTALLED` in their
header comments and `install.sh` copies them verbatim — **a stale claim parked in `/etc`, at
the exact surface someone checks to find out.**

### ✅ Track B unblocked — and the naive split would have shipped a bug

FluxusSource landed the `echoes_title` split (`feat/contract-a-content-meta-kind`, tip
**`690c2dd`**, rebased onto `master`, pre-rebase tagged so it cannot repeat `f3e8954`).
**Not merged, not deployed — the owner's call, correctly.**

⭐ **`body == title` is also true when BOTH are empty**, so a bare split stamps
`echoes_title: true` on a row that echoes nothing. Guarded with `bool(body)` first. Invisible
in the one-line derivation everyone (including this document) had been quoting as "both
halves are already there".

Replayed through the real `from_dict`/`to_dict` over 12,516 prod rows, 6 runs: 11,892 RSS
stamped, 624 non-RSS absent, **0 derivation errors**; `feed_summary` 93.68%,
`headline_only ∧ ¬echoes` 6.21%, **`headline_only ∧ echoes_title` 14 rows = 0.12%** (6
sources; 50 sources in the empty half). `kind` moved for **no row** — the same predicate read
twice, a test rather than a claim, so the 08-10→14 percentages survive. **Anything sized
against this field is sized against 0.12%, not `headline_only`'s 6.3%.**

⚠️ **A live SEMANTIC mismatch inside 1.24.0, and it is the silent class.** The schema says
`echoes_title` is *"substantially a repeat of the title"*; the producer's predicate is **exact
equality of the stripped strings** — title-plus-a-full-stop reads `false`. `type: boolean`
accepts both, so it validates clean forever. **Same shape `kind` had before its enum was
pinned in 1.21.0, one level down: the type is right and the meaning is not.** Principle 2
governs — the producer's predicate is the authority, so the fix is a NexusMind *description*
change. Widening is refused for a measured reason: the same predicate decides `kind`, so it
would move rows between kinds and invalidate every percentage the field is justified by.

### ✅ RULED — `content_meta.truncated` comes out of Contract A

W0 item 9, the one item nobody closed, is closed. **Undeclared from Contract A and re-filed
as a NexusMind enrichment stamp** — not dropped. Contract A describes what FluxusSource
emits; detecting whether the *source* truncated a body needs the feed body compared against
the full article, which only the enrichment side can do since `full_text_fetcher.py` left
FluxusSource. `pre_enrich` already computes both sides. **The distinction is real and bears
on #114**, and the schema description is the only place it is written down, so it must
survive verbatim into the new issue. A property removal on a field **0 of 14,409 live rows**
carry: no reader breaks.

*(§ "Standing after round 4" was moved back to the live `docs/CONTRACTS_PLAN.md` on 2026-09-27: it is the last status of unexecuted items.)*
