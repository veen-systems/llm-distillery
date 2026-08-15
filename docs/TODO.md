# LLM Distillery - TODO

## 🔵 NEXT SESSION — **two peer repos hold finished, uncommitted work awaiting the owner**

> **Housekeeping done 2026-08-15 night** (`memory/project_session_2026_08_15_night.md`) — nothing
> below changed. Framework adopted to **v1.26.0** (v1.25.1 + v1.26.0; 3 adopt, 1 decline, 4 N/A,
> 2 in force — `docs/decisions/framework-adoption-history.md`), then `/audit-context`:
> references **16 → 0**, `memory/MEMORY.md` **54.8k → 26.5k chars**, refcheck harness **20/20 →
> 24/24**. Two probes added — the framework stamps must agree, and the index must stay under 30k.
> ⚠️ **The reason the drift sat two releases unreviewed: the stamp had been bumped ahead of the
> adoption, and the stamp is the drift check's only input.** 13th occurrence of the
> unreachable-mechanism rule. Declined upstream's `isdelim()` guard tightening (agent-ready-projects#52,
> commented there with the adopter evidence).


✅ **Contract A realization was HANDED OUT and BUILT on 2026-08-15.** The owner authorized
NexusMind (W0) and FluxusSource (Track A) through this session; ovr.news and pipeline-atlas
took information-only briefs. **This repo wrote no code and deployed nothing.** Record:
`docs/CONTRACT_A_REALIZATION.md`, commit `1c02bf8`.

### ⭐ THE ONLY NUMBER THAT MATTERS: fields EMITTED on delivered rows — **3 of 23**

Measured 2026-08-15 evening on `collection_20260815_160753` (2,437 rows), not on report.
**The consumer schema reached 1.26.0 while the producer emitted none of it** — that gap,
not the schema's correctness, is what "implement Contract A" means.

| block | fields | emitted |
|---|---|---|
| `published` | raw · had_timezone · fabricated | ✅ **2,425 / 2,437 = 99.5%** |
| `published` | element · precision | ⛔ **omitted** (not null — and null means *fabricated* in this block, so the two states differ) |
| `content_meta` | kind · echoes_title · error | ⏳ built, `690c2dd`, **owner: merge + deploy in FluxusSource's session** |
| `collected` · `fetch` · `feed` · `origin` | 14 | ⛔ 0 rows |

⚠️ **`fabricated: False` on 2,425 rows is a REAL NEGATIVE, not a vacuous one** — corrected
by NexusMind, verified here in the producer: `extract_date_from_rss_entry` fabricates
`now − 2h` **by default** (`date_parser.py:125`, `fabricate_fallback=True`), so all **2,345**
RSS rows could have fabricated and none did. *(My "only 80 rows were fabricating-capable"
filtered by a remembered list of aggregator names instead of reading the path every row
takes — a hand-built population, again.)* **What IS untested is narrower than "the
true-branch"** — corrected by FluxusSource against my phrasing: the positive **has** been
observed on **prod bytes** (Track A's post-pull verification on sadalsuud, 224 rows,
`had_timezone {True: 204, None: 20}`, all 20 `french_le_parisien`), including the
`null`-means-fabricated shape. It is unobserved **in a delivered run** only.
⭐ **And the live positive needs no discriminator feed built — it is already scheduled.**
`french_le_parisien` is 24h cadence, `next_due_time 2026-08-16T11:54:56Z`, so it lands in
the **16:00 local run tomorrow**. ⚠️ Check the run, not the prediction: one feed on one day,
and if it has started serving dates the population is empty and the negative says nothing.

**NexusMind's side is DONE for this round** — `source_group` declared and deployed, W2.2
closed; `content_meta.truncated` removed (PR #373, `cfd1f18`); check ran **through the
systemd unit** on deployed code: `status ok · overall info · exit 0`, provenance block
populated, violation class gone. First *automatic* fire 02:23 (`LastTriggerUSec` still empty).

### ⏳ OWNER DECISION — delete 5 declarations rather than implement them

Measured in the producer's code; **the fastest route to a contract that describes reality is
deleting the fields that cannot carry information on the rows that exist.**

| off the row | why |
|---|---|
| `fetch.http_status` | **200 by construction** — all three body-returning sites in `robust_feed_parser.py` (`:484`, `:594`, `:763`) are guarded on 200; no 304/ETag path; non-200 branches return `None` |
| `fetch.url_requested` · `url_final` · `content_encoding` | real facts, but **per-FEED**, not per-row — they belong in the per-run feed-health report, which is rewritten each run and costs nothing in the archive |
| `feed.cadence_hours` | per-**source** constant repeated on every row → Category G's sidecar |

**Worth writing instead:** `fetch.at` (⚠️ through `time_utils.utc_now()` — stamped from
`datetime.now()` it inherits #176 and puts a host-local fetch time beside a UTC
`collected_date`, giving the skew a second witness that makes it look like a real interval),
`charset_used`, `charset_detected` (emit only when the strict-UTF-8 fast path fails, so
absence means "clean" and the field is near-free), `charset_declared`, `collected.clock_source`,
`feed.ttl_declared`, `published.precision`.

⚠️⚠️ **Two of my three charset calls were WRONG and the reason is reusable.** I argued they
duplicate a decision feedparser makes — but the producer **decodes before parsing**
(`_fix_encoding_issues` → `_parse_with_fallbacks(content: str)`), so feedparser never sees
wire bytes and `feed.encoding` is a tautology. **I inferred a mechanism from a general
pattern true of the library rather than following the call path.** On the corrected reading
`charset_declared` is the **most** interesting of the three — nothing reads the publisher's
declared charset today, so it is the only field that could compare a claim against reality.
⭐ **And the finding beside it is worth more than the field**: the ladder's docstring says
*"strict UTF-8 → declared/detected encoding → …"* and **the declared step does not exist in
the code** (filed by FluxusSource, `cee0044`).

⚠️ `origin.country`/`region` must NOT be derived from `domain_mappings.yaml` — measured
coverage on the live collection is **51.8%** (exact 214, by-suffix 478, TLD-fallback 571 of
2,437), and the **48.2% unmapped are systematically non-Western** (hindustantimes, lrt.lt,
vnexpress, nst.com.my, tovima.gr, seneweb). A geography field absent exactly where geography
is the question invites a consumer to read its coverage as a distribution. GDELT passthrough
+ `origin.method` only.

⚠️ **The four rows above read differently on 2026-08-15 evening than they did that afternoon,
and the correction is the point: this table said "awaiting owner commit" for work that was
already committed, merged, installed and in one case deployed.** Re-derived by reading the
schema off NexusMind `main`, both peers' git logs, and `systemctl` on sadalsuud — not from
either session's report. **A handoff table decays faster than anything else in this file**,
because it describes other repos' states and nothing here changes when they move.

⭐ **THE FINDING OF THE ROUND, and it is about how the round was run: three of this
session's own calls were wrong, and every one was caught because the receiving session
RE-DERIVED instead of adopting.** (1) `content_meta.error`'s type — the owner ruling
settled *whether to declare*; `(string, nullable)` was this repo's parenthetical
**inheriting authority by adjacency**. (2) *"measured at fetch needs a new read"* — it
needs a new **write**. (3) ⛔ **I recommended spending the only non-circular acceptance
control**, to drive a violation count to zero — *the very number whose trustworthiness it
establishes.* Promoted to `memory/working-rules.md`: **a failing check may be the control
working.**

⚠️ **Do NOT re-derive these, they are settled:** `published.had_timezone` is nullable as
of 1.22.0 (a **recommendation**, not a ruling — FluxusSource may still push back);
`content_meta.error` is **non-nullable** (`type(exc).__name__` has no null branch);
`published.element` is pinned as a **root conditional**, not a flat enum, because its
vocabulary is closed for RSS and **open overall**; `collected.clock_source` is **two
values, not three** — three call sites, two clocks.

⚠️ A mechanical "unpinned string" scan flags **16 of 23** fields and is useless —
`published.raw` is a publisher's literal string. The curated list is in the doc; do not
re-run the naive scan and treat its output as the backlog.

### ⭐ Contract A closeout — what is actually left, verified against the live schema 2026-08-15

**Two owner decisions, then four items. Nothing here is blocked on a machine.**

1. ✅ **DONE — NexusMind W0 is MERGED. Contract A 1.24.0 on `main`** (PR #368, `8e9c489`),
   46 contract tests, suite 1322, conformance on 165,107 producer-delivered rows:
   **3 → 3 violation classes, none new.** `null` ⟺ `fabricated` is now **enforced** rather
   than asserted. Verified here by reading the schema off `main`, not on report.
2. ✅ **DONE — FluxusSource Track A is committed AND deployed.** `08c4f56` emits the
   top-level `published` block; the deploy is recorded in their curate commit `0fb7a57`.
   The storage commitment (+95 bytes/row, ~1.5 MB/day, against archives kept indefinitely
   since #164) therefore **shipped without being decided separately** — it is now a fact to
   note, not a decision to take. ⚠️ *This item read "the only owner decision left in this
   round" for a day after it was closed.*
3. ✅ **RULED 2026-08-15 — `content_meta.truncated` comes OUT of Contract A**, and the
   distinction is **re-filed as a NexusMind enrichment stamp**, not dropped. It was declared
   against the wrong producer: detecting whether the *source* truncated a body needs the feed
   body compared against the full article, and full-text fetch left FluxusSource when
   `full_text_fetcher.py` was deleted. `pre_enrich` already computes both sides. **The
   distinction is real and bears on #114** — the description is the only place it is written
   down, so it must survive into the new issue verbatim rather than paraphrased. Relayed to
   NexusMind; theirs to execute (a property removal on a field 0 of 14,409 live rows carry,
   so no reader breaks). **W0 item 9 is closed.**
4. ⏳ **Track B — the blocker is gone; only the deploy call is left.** FluxusSource landed the
   `echoes_title` split on `feat/contract-a-content-meta-kind`, tip **`690c2dd`**, rebased onto
   `master`, **not merged, not deployed** — correctly still the owner's call.
   ⭐ **The naive split would have been a bug**: `body == title` is also true when **both are
   empty**, so it stamps `echoes_title: true` on a row that echoes nothing. Guarded with
   `bool(body)` first. Not visible in the one-line derivation.
   ⭐ **Measured, and the number to quote is 0.12% — not 6.3%.** Replayed through the real
   `from_dict`/`to_dict` over 12,516 prod rows (6 runs, 2026-08-14 20:08 → 08-15 12:05):
   11,892 RSS stamped, 624 non-RSS absent, **0 derivation errors**; `feed_summary` 93.68%,
   `headline_only ∧ ¬echoes` 6.21%, **`headline_only ∧ echoes_title` 14 rows = 0.12%**
   (china_cgtn 6, gestion_pe 3, tagesschau 2, seneweb / el_comercio_pe / irish_telegraph 1
   each — 6 sources, against 50 in the empty half). `kind` moved for **no row** — same
   predicate read twice, which is a test rather than a claim, so the 08-10→14 percentages
   survive. **Anything sized against this field is sized against 0.12%.**
   ⚠️ **A live SEMANTIC mismatch inside 1.24.0, silent class:** the schema says `echoes_title`
   is *"substantially a repeat of the title"*; the producer's predicate is **exact equality of
   the stripped strings** (title-plus-a-full-stop reads `false`). `type: boolean` accepts both,
   so it validates clean forever — the same shape `kind` had before its enum was pinned.
   **The producer's predicate is the authority** (principle 2), so the fix is a NexusMind
   description change; widening is refused because the same predicate decides `kind` and would
   move rows between kinds. Relayed.
5. 🔨 **The canary is MERGED, INSTALLED, ARMED — and HAS REPORTED THE CONTROL. W2.2 is held
   to the first AUTOMATIC fire, 02:22 tonight.** NM#361 merged (`1c2f20f`), units installed.
   Verified from this workstation over ssh, 2026-08-15:

   ```
   nexusmind-contract-check.timer    LoadState=loaded  ActiveState=active  LastTriggerUSec=  (EMPTY)
   next elapse                       Sun 2026-08-16 02:22:48 CEST
   artefact /home/jeroen/local_dev/NexusMind/data/contract_check.json  0644 jeroen:jeroen
   additionalProperties.<root>.source_group   asserted=true  rows=2722  errors=2722  error
   ```

   ⭐⭐ **The control fired against genuine producer bytes — the check DETECTS, it does not
   merely run.** That is the precondition the plan set for W2.2, and it is met.
   ⛔ **W2.2 still waits, and the reason is the whole thesis:** the artefact was produced by a
   **hand invocation**, and the timer has never fired. `LoadState=loaded` proves installation,
   not execution. NexusMind then proved the *unit definition* works (`systemctl start` →
   `ExecMainStatus=1` by design, `ProtectSystem=strict` + `ReadWritePaths` do not block the
   write — a real unretired risk, now retired) and **correctly refused to bank it**: a
   `systemctl start` satisfies "a run I did not invoke by hand" while being a hand invocation
   one level up. ⭐ **My acceptance criterion was itself the unreachable-mechanism shape it
   was written to catch.** Their in-repo test names two release conditions (automatic caller
   **and** a named replacement control); only the second is discharged. **Third session pushed
   to spend this control early and refused.**
   ⭐ **Replacement control named: `eval_query` on a pinned historical collection** — a
   producer-chosen field on producer-delivered bytes the check was never shown, and **frozen**,
   so unlike `source_group` the producer can never fix it away. Its limit, which must travel
   with it: it fires on **pinned bytes, not current input**. Spending `source_group` trades a
   **live-path control for a fixture-path one** — say that in the commit that spends it.
   ⚠️ **The artefact's own `scope.edges_not_covered` hardcodes the `source_group` hold**
   (`build_artefact`, `scripts/contract_check.py`). Declaring without moving it leaves the
   artefact asserting a held control that no longer exists.
   ⭐ **Artefact gains `invocation: {trigger, invocation_id, unit}`** (additive, schema stays 1)
   so "who ran this" is answerable at the surface where it is asked. ⚠️ **My proposed mechanism
   was defective**: systemd sets `INVOCATION_ID` for a service and **every child inherits it
   through the environment**, so a hand run from a terminal inside a scope unit stamps
   `systemd` — a false positive in the one direction that matters, and **a one-sided test
   passes against it**. NexusMind replaced it with the leaf of `/proc/self/cgroup` compared to
   the unit name (not inheritable across units), verified in both directions.
   ⚠️ `trigger: "systemd"` still does **not** mean the timer fired — a hand `systemctl start`
   is genuinely systemd. `LastTriggerUSec` + a fresh `generated_at_iso` is the pair that
   answers it. **Absent `invocation` means UNKNOWN, never "manual"** — it dates the artefact,
   it does not describe the run.
5b. ✅ **RULED 2026-08-15 — `eval_query` stays UNDECLARED, and NM#367 closes as a written
   decision**, not an omission. The field is **dead by decision**: FluxusSource retired the
   three #119 eval arms in `eda28eb` (#158, ADR-007 decisions 2 and 3), pulled onto sadalsuud
   **16:56:08 on 2026-08-11**, and the five identities that stopped are `newsdata_eval_{td,mg,bi}`,
   `gnews_eval_td`, `gdelt_constructive_madagascar`. Both switches were thrown (`enabled: false`
   **and** removal from `aggregator.enabled_sources`). So declaring it would declare something
   the producer stopped emitting, and it would spend the fixture-path control above.
   ⚠️⚠️ **TWO CORRECTIONS to figures this document held for a few hours, both FluxusSource's:**
   **(a) the stop boundary was four days too early.** The claimed edge was
   `…080541` → `…095038`. But `collection_20260811_095038` is an **off-grid partial run — 4
   sources / 933 items against a full cycle's ~1,950 / ~5,700 — that ran no eval aggregator at
   all.** Its zero means *did not run*, not *ran and yielded nothing*, and the field was still
   emitted at 12:08 (16 rows) and 16:06 (9 rows). ⭐ **The real edge is 16:06 → 17:02, six
   minutes after the deploy** — cause and effect, no gap. **Rule: bound a stop by last non-zero
   → first zero, and verify the run between is a FULL one.** Single-run zeros were normal
   throughout the emitting stretch (2–51 rows/run), so any single zero was never evidence.
   **(b) "511 is cumulative history" is wrong** — it is exactly the **7-day hot window** (26
   runs, `…0807_160813` → `…0811_160635`), so it **decays to 0 around 2026-08-18** as those runs
   age out. Recording it as a lifetime count would later read as the corpus losing rows. The
   lifetime figure lives in `data/archived/` (retained indefinitely since #164) and is uncounted.
   ⚠️ **Not a divergence, and the tidy-up it invites is destructive:** FluxusSource's own
   `config/schemas/output_schema.json` **must keep declaring `eval_query`** — their root is
   `additionalProperties: false` and `validate_output.py --archives` samples the indefinitely
   retained archive, whose rows carry the field. **Contract A undeclared + producer schema
   declared is correct: different windows, different jobs.**
   *(An earlier owner answer of "declare as expiring" was taken on my wrong premise and changed
   the moment the measurement reached them.)*
   ⚠️ **`source_group`'s 20.5% is a DATE, not a rate** — it landed 2026-08-13 16:57, 0%
   before and 100% after, so a presence-based check must key on **run date**. And point it
   at delivered bytes (`~/mirrors/sadalsuud/local_dev/FluxusSource/data/current/collection_*/`,
   52 collections / 165,107 rows), **not `data/raw`**, whose real problem is **vintage**:
   it predates `source_group` entirely.
6. ⏳ **`published.precision` is UNWRITTEN, not merely unpinned** — zero occurrences in
   `date_parser.py`. It is declared and nullable, so nothing is broken; it is simply the
   one field that is genuinely new producer code rather than threading-out. Sequence last.
   ✅ **Confirmed by FluxusSource 2026-08-15** against their own tree (`grep -c precision
   src/utils/date_parser.py` → 0; the 3 hits across `src/` are unrelated). **Not started, by
   agreement** — it is theirs and it stays last.

**Already settled — do not reopen:** `content_meta.error` non-nullable · `had_timezone` /
`precision` nullable · `element` pinned as a **root conditional**, not a flat enum ·
`clock_source` = `["host_local","utc"]` · `fetch.at` carries the canonical pattern ·
the **`null` ⟺ `fabricated`** `if`/`then` clause **landed on both sides**.

### New, unowned, and none of it blocks the above

- ~~**`eval_query` is a SECOND undeclared root field** (511 rows)~~ — **superseded, see 5b.**
  True as far as it went, and **the 511 was cumulative history, not a live population**: the
  field stopped on 2026-08-11 and is 0 in all 26 collections since. ⭐ **A row count with no
  time axis read as a standing condition** — the same denominator-must-travel shape as
  `source_group`'s "20.5%", and pointing the opposite way: one is a field that **started**,
  the other a field that **stopped**, and a bare count cannot tell them apart.
- **A fifth fabrication class at ~0h** — `devto`/`fda`/`clinicaltrials` do
  `if not published_date: published_date = datetime.now()`. **Not a wrong constant: the
  signal is at zero**, outside the 2h/4h taxonomy entirely. `fabricated` is **UNDEFINED**
  there, not false.
- **`CEST` maps to an LMT offset** in FluxusSource — `09:15:00 CEST` parses to **09:06**,
  so a wrong `published_date` can ride a correct `had_timezone: true`. Unfiled, theirs.
- **Track A costs +95 bytes/row (~1.5 MB/day) against archives kept indefinitely** — a
  storage commitment nobody has agreed to.
- **Ours: `merge_fluxus_data.py` / `merge_historical_data.py` sort undated articles
  FIRST** while commenting *"will be at the end"*. Measured **dead — 0 of 165,107** rows,
  because undated entries arrive fabricated rather than null. Comment wrong either way.
  Same two files still default to Windows Google Drive paths abandoned 2026-06-29.

### ✅ CLOSED: the ovr.news corpus backfill — answer is NO

Carried for weeks as *"authorised and not run"*. **Three successive refutations, two of
them ovr's of its own reasoning.** The population was never 79 rows (**21,520 = 98.2%**);
*"value increases with delay"* is **false** (the naive population is **closed**); there is
**no time trigger and no event trigger** (the write boundary canonicalises before storage,
so an offset never reaches `ORDER BY` as one — **0 inversions in 21,948 production rows**,
0 in a seeded post-FS#174 simulation); and the last benefit fails on **scope** — it
rewrites the DB only, while the append-only archive is the **durable** copy since
ADR-022/#262. ✅ **llm-distillery is a structural non-stakeholder**: reads no ovr archives,
and both `sort_articles_by_date` impls truncate at `'T'`, so the sort key is `YYYY-MM-DD`.

## 🔵 Also open (updated 2026-08-15)

**Nothing was deployed and no filter package was touched; `deploy` is not applicable.**
Seven commits, all documentation and findings, `041cc10` → `24d5ff2`, pushed.

### The three decisions waiting on the owner

1. **#114 — the 300-char floor's rationale has never been measured, and it now gates
   more than the floor.** Settling it needs a **paired** oracle measurement (same
   article at stub and full length) ⇒ **spend approval.** Three repos hold three
   different views of why the floor exists and none has evidence; FluxusSource has
   already shipped *"Length was never the property being measured"* into a
   machine-readable contract as a flat assertion about **our** rationale.
2. **`CLAUDE.md` is 37.4k against a 35k soft target**, and the savepoint's advice
   (check formatter table padding first) does not apply — **0 recoverable padding
   bytes** across all 51 table lines, 0 trailing whitespace. Cutting content is the
   only lever. `## Before You Start` is **10,415 chars = 28% of the file** and is a
   router that has drifted into summarizing its own targets. **Recommend
   `/audit-context` over a hand-trim**, for exactly the duplication reason the file's
   own footer gives.
3. **Category G** now needs an **implementer, not a decision** (grain decision taken
   below). Candidate FluxusSource, after their (b) sequence.

### What is NOT ours and should not be started here

`published.fabricated`/`had_timezone`/`raw`, the `content_meta.kind` deploy, and
`clock_source` are **FluxusSource's**, confirmed with that session. The canary is
**NexusMind's** — it is item 1 in their own brief. ⛔ **`content_meta.kind`'s consumer
was deliberately NOT written**: the field is emitted on **0 of 14,409** production rows,
so it would be dead code with green tests, and its premise is #114.

### One local branch left deliberately

`docs/event-identity-encoder-plan` — **unmerged, 1 commit ahead** of `main` (#100 work).
Five merged branches were pruned locally this session; all five still exist on `origin`,
so `git checkout <name>` restores any of them.

---

## 🔵 Contract A — the envelope is LANDED. The producer emits nothing yet.

**2026-08-14, late: the redesign was implemented as far as it can go without producer
code.** The decision record is
**`docs/decisions/2026-08-14-contract-a-envelope.md`**; the five-repo detail is
`docs/CONTRACTS_PLAN.md` § *Round 3*.

### What landed — verified against `origin/main`, not taken on report

```
NexusMind/contracts/fluxussource-output.schema.json   version 1.20.0
root additionalProperties  false            ← the decision, intact
blocks   published · collected · fetch · content_meta · feed · origin · payload
published                  element · fabricated · had_timezone · precision · raw
language                   type: string     ← the collision, avoided
source_group declared      False            ← the hold, UNSPENT
required                   the original 8 keys, unchanged
```

NM#360 merged (`7d1086f`), NM#364 merged (`0652414`), 1,305 tests green.
**Nothing deployed — sadalsuud remains on `b115fda`.**

⭐ **The envelope answer, in one line:** the blocker was never
`additionalProperties: false` — it was assuming that *declaring* a field and
*emitting* one are the same step. **Declare the whole shape first, all optional;
after that every field ships independently.** Verified runtime-inert: no production
path opens either schema file.

### ⭐ The redesign got SMALLER, and that is the result

| removed | why |
|---|---|
| the whole `language` block | `language` is already a live top-level **string** on 100% of rows and read as one at 8 production sites. Declaring it an object fails `type` on every row — optionality cannot help, the property is *present*, not absent. Once the rename ban applied it was one new fact and five relocations. |
| `source`, `item` | same class: re-nesting a live flat field is a *relocation*, which is the forbidden act |
| `published.instant` | **same moment as `published_date`** — adds no temporal information, only an offset that `origin.timezone`/`had_timezone` carry better. And the defect it was justified by is a **consumer bug** (ovr's JS reads naive as local) with a one-line fix. |
| `collected.at`, `content_meta.raw_length`, `feed.title`, `feed.declared_language` | declared duplicates of live flat keys |

### ✅ H-D2 CLOSED 2026-08-14 ~20:10 — the 6h spike was arXiv, not a date defect

Ran the discriminating measurement (condition the gap on `source`) that both sessions
had deliberately deferred. The **7,478-row population is exactly two NexusMind raw
deliveries** (3,835 + 3,643), and the recorded bins reproduce digit for digit. **974 of
the 1,046 rows in the 6.0 bin (93.1%) are arXiv**, 983 sharing one `published_date`
(`2026-08-14T04:00`, arXiv's daily announcement).

⭐ **The gap walks with the collection timer** — arXiv sits at 2.06h / 6.12h / 10.10h /
14.08h across four consecutive deliveries, +4h each, because `published` is fixed and
`collected` moves. FluxusSource's *"11h spike is 84% `science_arxiv_cs`"* is the same
batch at their cadence: **one phenomenon at two phases, not two phenomena.**

⚠️ **The trap, and it is the reusable part:** this artifact passes through **2.06h**
once per daily cycle — the fabrication signature's own bin. `collected − published` is
**not** a fabrication instrument without a `source` breakdown.

⭐ **Sharpened by the FluxusSource session the same evening, and it inverts my
framing.** I said H-D1 survives "by a margin" (arXiv 216s outside its 2h ± 5s window).
Their run put the same batch **452s** out — and *two different margins is the finding*.
arXiv announces **04:00 UTC**; the timer fires **06:00 UTC** (08:00 Amsterdam, FS#132),
exactly 2h later. **The coincidence is a scheduled tick, not a hypothetical**, and the
only thing holding a whole announcement batch out of the fabrication window is how long
a run takes to reach that aggregator — which no invariant fixes. **Correct conclusion:
`published.fabricated` must be stamped at the point of fabrication, because no
downstream rule can separate a fabricated date from a real one genuinely 2h old.**
Recorded in FS#173 (comment + body correction). Full record:
`memory/date-error-recency-boost-hypotheses.md`.

### Do first, in this order

1. **`fabricated` + `had_timezone` + `raw`, TOGETHER** — not `fabricated` alone.
   `display_ranking.py` applies a flat **1.3× boost under 24h** on `published_date`,
   and the producer invents `now − 2h` for date-less entries, so a fabricated date
   reads as maximally fresh and wins it. **But the population is wider than
   fabrication** — see the hypothesis file — and those three fields are exactly what
   separates the causes. **`fabricated` cannot be interpreted without the other two.**
   All three are declared on `main` and nothing populates them.
2. **`content_meta.kind` deploy** — built, reviewed, moved to top-level, verified over
   5,995 prod rows (emitted on exactly the 5,739 RSS rows, 0 schema violations).
   ⚠️ **The commit is `7bc20a0` on `feat/contract-a-content-meta-kind`, NOT `f3e8954`**
   — that hash was amended away, is an ancestor of no branch, survives only in
   FluxusSource's reflog and is GC-eligible. Corrected 2026-08-14; **build against
   `7bc20a0`.** Branch **not merged** (their `master` is `cb4f6ac`, sadalsuud
   `6455c06`, `grep -rn content_meta src/` on master returns nothing), and it is
   **correctly parked, not racing** — its own gate is *"not for deploy until
   NexusMind's envelope declaration merges"*, consumer-declares-first. ⭐ **That gate
   now appears SATISFIED** (Contract A 1.20.0 is on NexusMind `main`, `25dc482`) —
   FluxusSource's call to make, not ours.

   **The emitted vocabulary is TWO values, not three** — `feed_summary` and
   `headline_only`. There is no `summary`. `error` is a **sibling key** (an exception
   type name, present only if derivation faults) so a fault stays distinguishable from
   a non-RSS row; the sub-object is `additionalProperties: false`. `full_text` is
   deliberately absent for **two independent reasons** — enrichment moved to our side,
   *and* `rss_aggregator` never reads `entry.content`/`content:encoded` at all —
   so removing either one alone does not reopen it. Measured 2026-08-10→14 over 97,526
   RSS rows: **5.3% `headline_only` overall, 6.9% of native RSS, 0.0% of 25,607 GN rows.**

   ⚠️ **The consumer's fallback keys on `source_type`, NOT on the field's absence.**
   Absence means **not applicable, not unknown** — there is no feed document behind an
   api/social/data row, which is also why `kind` can never become `required`. So: RSS
   row with no `kind` ⇒ pre-deploy data, fall back to length. Non-RSS row ⇒ the length
   question is meaningless, don't apply a document-shaped prefilter at all.

   ⚠️ **This does NOT retire the floor on its own — see `H-L1` in
   `memory/prefilter-length-floor-hypotheses.md`.** `kind` never looks at length (the
   whole derivation is `'headline_only' if not body or body == title else
   'feed_summary'`), and the floor's stated rationale is *framework leakage*, which is
   a function of **how much text the oracle sees**. A `feed_summary` of 143 chars still
   hands the oracle 143 chars. **That rationale has never been measured.**
3. **`collected.clock_source`**, then `fetch.*`, then `element`, then `precision` last
   (the only one that is new code rather than threading-out).
   ⚠️ **My "move `clock_source` up" suggestion is WITHDRAWN AS ARGUED** — the reasoning
   (a latent *false-positive* collision at ~1.98h) was wrong twice over: the 1.98h was
   an artifact of comparing to the run median when NewsAPI **runs first**, and for a
   skewed producer `gap = true_age + 2h`, so a real article hits `2h ± 5s` only if it is
   under **5 seconds** old. Sequencing is FluxusSource's call.

   ⭐ **The real interaction is a FALSE NEGATIVE, and it is active — now `FS#176`.**
   `DateParser.ensure_valid_date:217` is a **second** fabrication site, called from the
   `news_api`/`github`/`academic`/`patent` aggregators, several of which are the
   clock-skewed ones. Fabricated-in-UTC + collected-on-local-clock ⇒ **`gap = 4h`, two
   hours outside FS#173's detection window.** Verified here on 155,513 rows: **46 rows
   at `4h ± 5s`, 32 `semantic_scholar`, 32/32 carrying microseconds** on `published_date`
   with published/collected agreeing to ~35µs — one instant, two clocks. **So FS#173
   undercounts fabrication.** A detector keyed on a fixed gap is keyed on the
   *producer's clock* and needs a new constant per aggregator **and after every DST
   transition** (4h in CEST, 3h in CET). Detail:
   `memory/date-error-recency-boost-hypotheses.md`.

   ⚠️⚠️ **STANDING DATA RULE until FS#176 lands — archives are NOT being backfilled.**
   `collected_date` is on the **host local clock (+2h CEST)** for **8 of 768 sources**:
   `newsapi_general`, `github`, `hackernews`, `stackoverflow`, `ourworldindata`, NASA
   APOD, and two Dev.to author-named sources. The other ~760 are UTC; `published_date`
   is unaffected. **Any llm-distillery analysis treating `collected_date` as uniformly
   UTC is wrong by 2h on that slice**, in `data/current/` and in the archive.

### ⭐ A DECLARED FIELD WITH NO PRODUCER — `content_meta.truncated` (found 2026-08-14)

Contract A **1.20.0 declares `content_meta.truncated`** (verified by reading the schema
on NexusMind `main`, `25dc482`: `content_meta -> ['echoes_title', 'kind', 'truncated']`).
**FluxusSource does not emit it, has no plan to, and nothing named `truncated` exists
anywhere in their tree** — the only `truncat*` hits are `collection_truncated` in
`content_aggregator.py`, which is source/category collection caps and unrelated.

⚠️ **Both sides were right and neither was wrong** — which is the whole session's theme
one more time. **Declaring a field and emitting one are separate acts**, and the
envelope decision made declaration cheap *on purpose*. The cost is that the schema now
documents a capability that has no owner, and a consumer reading the schema would plan
for truncation detection that is never coming.

⭐ **This is the exact inverse of `source_group`**, which is *emitted on every row and
declared nowhere*. Contract A currently has a gap in **both** directions, and only one
of them (`source_group`) is on anyone's list. **Neither is visible to a validator**:
undeclared-and-emitted needs the canary to be caught, declared-and-unemitted is
invisible to any check that validates rows that exist.

⚠️ **My "delete it" suggestion is WITHDRAWN — I had not read the field's description.**
It says: *"Whether the **source itself** truncated the body (e.g. a partial-feed
publisher), as opposed to the body simply being short."* That is a **real and useful
distinction**, and FluxusSource not truncating is exactly why they cannot answer it —
detecting it means comparing the feed body against the full article, and full-text
fetch lives on **our/NexusMind's** side since `full_text_fetcher.py` was deleted from
theirs. **So `truncated` is declared against the WRONG PRODUCER, not declared
uselessly.** Structurally unownable at FluxusSource. Assign it here or drop it
deliberately — but not as dead weight.

### ⛔ THREE SHAPE MISMATCHES IN `content_meta` — and only ONE fails closed

**Verified 2026-08-14 by reading `origin/main` (`25dc482`), not on report.** Found by
FluxusSource off the back of the `truncated` note. `content_meta` is
`additionalProperties: false` and declares exactly `echoes_title`, `kind`, `truncated`.

⚠️ **`7bc20a0`'s deploy gate was *"not until NexusMind's envelope declaration merges."*
It has merged — so the gate is satisfied IN LETTER, and the next person to read that
commit message sees a green light.** These three are why that would be wrong.

| # | mismatch | fails how |
|---|---|---|
| **1** | **`content_meta.error` is UNDECLARED** on a closed sub-object. The producer emits it (an exception type name) on derivation fault. | ⛔ **HARD VALIDATION FAILURE.** The one path added so a fault stays *visible* is the path that turns a fault into a contract violation. **This is the only one that fails closed** — and it is FluxusSource's to fix, not NexusMind's. |
| **2** | **`kind` has NO `enum`** — just a description naming **four** notions (*"full article, RSS summary, title-only, empty"*). The producer emits **two**: `feed_summary` \| `headline_only`. | 🔇 **SILENT.** `type: string` accepts both, so it validates clean today and diverges whenever either side ships. An unpinned enum on a closed object. |
| **3** | **`echoes_title` is a SPLIT the producer collapsed.** Their derivation is `headline_only if not body or body == title` — **empty OR echoes-title fused into one value.** The schema separates precisely those two. | 🔇 **SILENT, and lossy both ways.** A consumer reading `echoes_title` cannot obtain it from `kind`; a consumer reading `kind == 'headline_only'` cannot tell an empty body from a title echo. ⭐ **The schema's split is the better model** and both halves already exist in the producer's one line — cheap to adopt. |

⭐ **The shape of this is the session's thesis again**: a gate written as *"wait for X to
merge"* tracks **whether X happened**, never **whether the two shapes agree**. Merging
satisfied the gate and changed nothing about the mismatch. `kind`'s own description
even says *"NexusMind currently infers this from length, which is a guess the producer
does not have to make"* — the consumer had a view about the rationale all along, and
it is not the one in `batch_scorer.py:146`. See H-L1.

### ⚠️ Unassigned — the list is now ONE item, not three

- ~~**The canonical-serialization defect**~~ — ✅ **CLOSED the same evening, before this
  list was read.** Fixed in `94e7337` at the single predicted site
  (`ContentItem._canonical_timestamp` → `utils/time_utils.canonical_timestamp`),
  deployed to sadalsuud **19:20:42**, and **verified live by this session**:
  `collection_20260814_161408` carried 143/143 microsecond `collected_date`,
  `collection_20260814_193603` carries **2,891/2,891 canonical on both date fields**.
  Follow-up **FS#174** tightens `output_schema.json`'s pattern and is deliberately
  held to ~2026-08-21 so the 7-day hot window rolls first — otherwise the validator
  exits 1 every run for a week and gets switched off.
  ⚠️ **This moved H-D1's expiry boundary**: the fingerprint dies at a *run*
  (`…_193603`), not at "~17:00" — the 16:02 and 16:14 runs are still quotable.
  `memory/date-error-recency-boost-hypotheses.md` corrected.
- ~~**The canary**~~ — not unowned: it is item 1 in the **nexusmind** session's own
  brief. Leave it there; two sessions building one canary is worse than none.
- **Category G** (`collection.*`, the non-event sidecar) — **the only genuinely
  unassigned item, and it was NOT "spec-ready" as the savepoint claimed.** This plan's
  own status table said so (`⏸ spec needs the per-tier grain decision before anything
  else`); the savepoint line was stale. pipeline-atlas supplied the model facts and
  correctly declined the code, since that repo owns no pipeline code.

  ⭐ **GRAIN DECISION MADE 2026-08-14 (llm-distillery), and it was already written in
  § *Round 3* — nobody had taken it.** The grain problem is not intrinsic to G; it
  **arrived with four fields that don't belong to G at all.**

  | field | disposition |
  |---|---|
  | `health_state`, `raw_item_count`, `items_emitted` | **MOVE OUT to categories A–F.** All three describe *how a fetch went*, which is A–F by this plan's own framing. They drifted in from the neighbours and **brought the grain problem with them** — `concurrent_rss` is one source name holding the whole feed tier, while `health_state` runs per *feed*. |
  | `poll_interval_actual_h` | **KEEP in G, with per-tier semantics declared.** It is per-*source* for exactly the population that needs it: FS#121's collect-every-tick sources fall through `select_sources_to_collect` **precisely for having no per-feed scheduling metadata**, so for them there are no feeds to disagree about. It is per-feed only for `concurrent_rss`, which is not the overpoll case. Losing it loses the only field that can expose #121. |
  | `refusal_reason` | **KEEP, but NAME IT AN AGGREGATE** at Site B's `no_feeds_due` exit — it summarises per-feed decisions under a source-name grain. Unnamed, *"the tier was refused"* and *"no feed was due"* become indistinguishable. |
  | `outcome` | **Written at the refusal site, never derived.** Derived from `collection_stats` it inherits the defect it exists to expose: Site B's `_record_skip` output is already classified downstream as `empty_sources`, so `refused_in_aggregator` and `empty` are indistinguishable **by construction** — a field that can never emit two of its four values. |

  **With those four moved out, G is clean, per source name, and the least-blocked item
  in the redesign.** ⚠️ Two things it still needs before code: *"measured at fetch"*
  requires **adding a read that does not exist** (the collection path only ever writes
  to the health tracker — a new coupling, fine if intended, but an explicit spec line
  and not a free field); and the enum is refusal-shaped, so it has **no value for
  FS#121's "fetched, but on the wrong cadence"**.

  **Owner candidate: FluxusSource**, positioned *after* the (b) sequence
  (`fabricated`/`had_timezone`/`raw` → `content_meta.kind` → `clock_source` → `fetch.*`
  → `element` → `precision`). Not started, not promised — G is a sidecar and every item
  ahead of it is on a live contract.

  ⭐ **Why it is worth doing at all, in pipeline-atlas's strongest form:** a block of
  European feeds sat `enabled: true` **collecting nothing for most of a year** — no
  error, no warning, no zero-yield alert. The source loader walks one level, so a key
  that never became a source cannot report zero. **A contract check validates rows that
  exist; a source emitting no rows is invisible to it at any strictness.** That is
  Category G's argument one level up, and no row schema will ever reach it.

### The offset gate has THREE parts, not one

FS#171 is **OPEN** and aimed at `published_date` itself.
`clock fixed` **and** `ovr#321` are **independent** gates, not a chain — adding an
offset *serialises whatever the value already is*, so on the 3.87% of rows carrying a
+2h local clock it converts a silent error into a durable explicit one.
⚠️ **Nothing downstream protects ovr**: NexusMind **relays `published_date`
byte-for-byte** (proven by a 6,024-row byte-identical join), so FS#171's offsets reach
ovr's 20 lexicographic sort sites unchanged.

### Parked

| repo | state |
|---|---|
| **NexusMind** | #360 + #364 **merged**. NM#361 (the checker) still stood down. Nothing installed; sadalsuud `b115fda`. |
| **ovr.news** | Three items committed: the Contract B drop reader (`FilterStats.validation`, on `/ops/`), the write-boundary test, the archive comparator. ⚠️ **Corpus backfill still authorised and NOT RUN** — and it is the **only** fix that reaches the delete boundary, because rows there are ~20 days old and only ≤10-day rows are rewritten. |
| **FluxusSource** | `source_schema.yaml` priority-polarity fix — **the committed file is still wrong**. |
| **pipeline-atlas** | Blind-spot section shipped with a mutation-tested verify command. Units still correctly **NOT ARMED** — and arming should wait until the check reads clean, or it trains the override it exists to prevent. |

## 🔵 Then: **the Thriving predicate is RULED; two decisions left.**

**✅ RULED 2026-08-13 — the lens predicate, in ovr.news `docs/BRAND.md` `a70609b`** (commit
verified here, not taken from the relay): *Thriving qualifies when the article shows **a
process going well for people** — health, safety, capability or circumstances improving, or
a protection established that will improve them. Not when the event only establishes that a
harm occurred, or that one has been answered; nor when the beneficiary is an institution.*
**#107 is SCOPED, not reversed** — its three adjacent-lens rows stand, and the ruling says
plainly *"the scorer is not miscalibrated; it is faithfully serving a definition we do not
publish."* **This makes ADR-012's `uplifting` → `human_thriving` rename LOAD-BEARING**: the
oracle prompt is written against the scorer's name, and the name carries the wrong
predicate. ⚠️ Build any predicate against two rows, not the prose — **Vox/Vision Zero**
(strongest qualifier, entirely about traffic deaths: a harm-vocabulary exclusion fails here
first) and **Banco Azteca's banking awards** (admitting it means you kept `uplifting`'s
meaning). Boundary pair that must BOTH qualify: Nepal's ILO ratification and Israel's
cigarette warnings — they answer a harm *and leave a protection behind*. ⚠️ **A retrain
trap**: the Commonwealth Games medallist story qualifies but its headline leads with the
beating — **if labels come from headlines this class is mislabelled systematically.**

### Framework drift closed 2026-08-13 evening: v1.25.0 → v1.26.0 (+ one candidate fix ported)

Checked `/home/jeroen/repos/agent-ready-projects` (clone 0 behind origin). **Two of the
three intervening releases describe defects this session actually hit**, which is the
argument for checking drift rather than assuming currency.

| release | verdict | why |
|---|---|---|
| **v1.25.1** — `review-changes` Step 1.5 CRLF | **already in force** | our copy already carries `core.quotePath=false` (5 occurrences) |
| **v1.26.0** — `curate` verify runner must take the PROJECT FILE | **ADOPTED, and it found a real gap** | `CLAUDE.md` has **0** annotations so that half is latent here — but `docs/TODO.md` has **2 that had never been run**, because this session's curate invoked the runner over `memory/*.md` only. Both now run and **both PASS** (`commerce_prefilter/v1` present; NM#185 OPEN) |
| **v1.26.1** (candidate, unreleased) — `review-changes` reports "nothing to review" on a **pushed** branch | **PORTED AHEAD OF RELEASE** | ⚠️ **I hit this today.** `/review-changes` returned an empty change set on a clean pushed `main`, and I substituted scope by hand (`277e6c6~1..dc691ce`) *without recognising it as a defect* — exactly what the upstream entry says happened there twice. Now resolves a default-branch baseline (`origin/HEAD` → `origin/main` → … ) and says **"SCOPE NOT ESTABLISHED"** rather than reporting a clean diff |

**Ported, not swapped** — `review-changes` here is project-local and deliberately re-mapped
to this repo's paths (a verbatim install would tier every change LOW and quietly do
nothing). The 2026-08-12 lesson stands: a straight swap of a shared instrument can be a
regression.

⚠️ **Needs an owner call — `~/.claude/skills/curate/SKILL.md` DIFFERS from
`agent-ready-projects/templates/curate.md`.** It is a **global** skill shared by every
project, so v1.26.0's project-file change was **not** applied to it from here. Until it is,
`/curate` in any repo will keep scanning `memory/*.md` alone. Two options: re-install the
global skill from the framework, or accept the divergence deliberately and record why.

**Interim rule for this repo**: invoke the verify runner as
`bash verify-runner.sh <repo>/memory/*.md <repo>/CLAUDE.md <repo>/docs/TODO.md`.

## 🔵 Then: two owner decisions, then #104.

**Cross-repo sync is CLOSED as of 2026-08-13 midday, and it was the only real gap.**
Verified three ways rather than assumed: gpu-server ↔ sadalsuud was already exact
(42/42 files md5-identical across the six live filters; `filters/CODE_REVISION`
re-stamped every cycle, so that hop self-verifies every 4h), sadalsuud was 2 commits
behind origin on **docs only** and auto-pulls `--ff-only` (`deploy_filters.sh:130-138`),
and the actual drift was llm-distillery → NexusMind: 3 files, all inert at runtime,
now pushed as `7ae74ba` + `bb204be`. ⚠️ Those two went **straight to NexusMind `main`
with no PR**, against that repo's `chore/*` branch convention — owner authorised the
content, the process miss is ours; revert-and-redo-as-PR is still on the table.

**⚠️ NEW owner decision — #47 REOPENED (`NO_HUB` does not cross the repo boundary).**
NexusMind still carries `filters/uplifting/v7/inference_hub.py`, which we deleted here;
`cp -r` never deletes. It points at `jeergrvgreg/uplifting-filter-v7`, which **404s under
an authenticated token** (measured with positive *and* negative controls — an
unauthenticated probe returns 401 for repos that exist and is worthless here). Deleting
it turns **3 NM#312 tests red**, because they assert `get_scorer_class(use_hub=True)`
resolves for every discovered filter — i.e. they were green *because of* the stale file,
and assert importability rather than repo existence. **Recommendation: delete the file
AND teach `filter_loader` to honour `NO_HUB`**, re-scoping those tests to the true
invariant (every filter resolves a scorer by its *declared* path, hub or local). The easy
way out is closed: `training_metadata.json` / `training_history.json` are still absent for
v7 and `upload_to_huggingface.py` reads both, so uploading would fabricate the metrics
#47 closed against. Weigh against ADR-012 (uplifting → `human_thriving` at v8, where the
sentinel goes away anyway; the `filter_loader` half is version-independent).

**Shipped 2026-08-13: checklist item 5 is now a guard (`d969a23`).**
`preflight_deploy_guards.py` guard D probes gpu-server for
`{filter}/{version}/model/adapter_model.safetensors` and aborts if absent — fails **closed**
when it cannot ask, with `--weights-preplaced` as the documented offline override. Proven
against production, not a fixture: **cd v5 passes, cd v6 fails**, so the pending cutover
cannot be started by accident from either deploy path. ⚠️ **Consequence to weigh:** every
`deploy_to_nexusmind.sh` run now needs ssh reachability to `gpu-server`. Fine from this
workstation; from the Windows box (still the script's default paths) the host alias may
not resolve and deploys will abort. Owner asked to decide whether an *unknown host* should
degrade to a warning, distinct from *unreachable*.

**Framework verified CURRENT at session close 2026-08-13:** pinned v1.25.0, upstream v1.25.0
(`889b038`), clone **0 commits behind origin**. No drift, nothing to triage.
H-E1 and the #109 Arm B design gap are both closed.

**Owner decisions waiting (nothing is blocked on a machine):**

0. **NM#284 — DELETE the per-lens rule prefilters, or wire them up?** NexusMind
   recommends deleting and asks us to own it, because `filters/*/v*/prefilter.py`
   and `config.yaml` are ours. **Verified here: 5 of 6 deployed filters still declare
   `prefilter.enabled: true`** (`solutions v6`, `uplifting v7`, `cultural_discovery v5`,
   `belonging v1`, `nature_recovery v4`; only `investment_risk v6` declares no `enabled:` key — it still carries a `prefilter:` block) —
   config has promised something the runtime never delivered since 2026-02-10.
   **My recommendation: DELETE.** Three reasons, and the second is the strongest:
   the e5 probe already absorbed the cheap-triage role — **`stage1_low` is 65.83% of
   `solutions` and 56.00% of `cultural_discovery`**, re-derived 2026-08-12 over
   `nexus_mind_attributes.<lens>.stage_used` on sadalsuud, **denominator = STAMPED rows**
   (235,873 / 235,904 all-rows; the of-all-rows figure is 19.61% / 16.69% because
   pre-2026-08-08 rows carry no stamp — a **3.4× swing from denominator choice alone**,
   so always state which). ⚠️ The peer session's figures were 66.1% / **59.8%**; the
   `cultural_discovery` half **does not reproduce** — its daily range is 52.35–58.32%,
   so 59.8% is above every single day. Use the re-derived numbers.
   Verify: `ssh sadalsuud` + count `stage1_low` over `nexus_mind_attributes.<lens>.stage_used`
   (**not** `analysis.stage_used`, which is `None` on all 105,304 rows — the wrong-path trap); **enabling them would INTRODUCE a
   language gap that does not currently exist** — our own #99 found `DISCOVERY_PATTERNS`
   is an English-only back door (66/516 English passers vs **0/265** everything else),
   and **#99 was closed by removal in v6 ONLY — v5 is the LIVE version and `filters/cultural_discovery/v5/prefilter.py:269` still declares `DISCOVERY_PATTERNS`**, so switching the gate on ships that defect into production for the first time (the argument is stronger than first written); and the dead code is
   what let a stale number steer NM#292's gating row for two weeks, because
   `enabled: true` made it look live.
   ⚠️ **Sequencing is in our favour and must not be reversed:** NexusMind's NM#284
   shadow evaluator is currently the ONLY thing measuring these prefilters. **We decide
   and delete first; they strip the plumbing after.** Removing their half first would
   cost observability before the decision.

1. **#109 Arm B — go / no-go.** The design blocker is gone: judges are now named
   (**Qwen3:14b + Phi4:14b**, local, non-Gemini, **$0** on b650), with a
   both-must-agree rule and a per-judge planted-error gate that runs before any
   real sample. Scoping comment is on the issue. ⚠️ Read it with #108's retitle:
   the *motivation* Arm B drew from #108 is weaker than it was, because whether
   the 300-char floor is a language filter turns on a pipeline stage nobody has
   established. Arm B still answers "are the labels correct", which is worth
   having either way — but the priority argument changed.
2. **`cultural_discovery v6` cutover** (#98). The `tiers:` gap is closed and now
   guarded. Remaining: fit `normalization.json` on real 6.0 rows, and **update
   `ACTIVE_FILTERS` to v6 in the same commit that promotes it**.

**Then #104** (every accuracy number is CPU-measured; production serves on GPU —
worth 1 verdict flip at the deployed op-point). Unchanged, unstarted.

**New and cheap, from H-E1:** `nature_recovery`'s `protection_durability` is the
only dimension in the enrichment pilot with a materially negative delta (−0.173,
24 of 48 rows down). Untested hypothesis on **#71**: enrichment is *correcting* an
over-score, not damaging a good one. **Do not "fix" it before establishing the
direction is wrong.**

### ✅ 2026-08-12: the `tiers:` gap is CLOSED, and it is now guarded rather than remembered

**Done, not pending.** `filters/cultural_discovery/v5/config.yaml` **and
`v6/config.yaml`** both carry a `tiers:` block mirroring `base_scorer.py`
(7.0 / 4.0 / 0.0). They were the only two deployed/staged filters without one.

**It is not documentation-only, and the earlier claim here that it was is
withdrawn.** No PRODUCTION SCORING code reads the block — `production_scorer.py:142`
takes the op-point from `base.TIER_THRESHOLDS` — but **eight llm-distillery tools do**:
`fit_normalization`, `ground_truth_gate` (the ADR-021 threshold), `prepare_data`,
`fit_calibration`, `train_scope_probe`, `calibrate_hybrid_threshold`,
`evaluate_models`, and `uplifting v1`'s postfilter. Measured consequence for
`cultural_discovery`: `prepare_data.extract_filter_info` goes `tier_boundaries={}` →
`{'high':7.0,'medium':4.0,'low':0.0}`, flipping `use_score_bins` True→False, so **a
future retrain's train/val/test splits stratify by TIER instead of score bins.** The
normalization fit floor is unchanged (`resolve_op_point` returns 4.0 both ways).
Other consumers were unaffected only because cd's op-point is 4.0 and their fallbacks
are hardcoded 4.0 — a coincidence of value. **On `nature_recovery` (3.75),
`investment_risk` (4.25), `uplifting` (4.5) or `solutions` (2.25) the same edit would
move the ADR-021 gate threshold.**

**Now enforced, not remembered:** `scripts/deployment/preflight_deploy_guards.py`
runs as Step 0.5 of **both** `deploy_to_nexusmind.sh` and `.ps1`, and refuses a
package whose `scoring.tiers` is missing from, disagrees with, or declares a
different tier *set* than `base_scorer.py`. 34 tests, each proven to fire on the real
defect and stay quiet on the healthy case.

**Still open, and it is the hand-maintained list:** `ACTIVE_FILTERS` in
`tests/unit/test_filter_config_schema.py` names `cultural_discovery v5`. **Update it
to v6 in the same commit that promotes v6** — that list lagging is exactly how drift
in a deployed version went unseen for six weeks.

**On version selection — scoped, because the earlier wording here overclaimed.**
NexusMind's `filter_loader._find_latest_version()` (`src/filters/filter_loader.py:178-193`;
the selection is at `:192-193`) serves the **highest `vN` on disk**. So **there is no
version-selection step anywhere** — nothing names v6, no config flip activates it, and
there is nothing to forget. ⚠️ But *"the deploy and the cutover are the same
keystroke"* was **FALSE and is withdrawn**: the canonical chain
(`docs/FILTER_PLAYBOOK.md` § Deploy safety checklist) is **llm-distillery git →
NexusMind git → sadalsuud `deploy_filters.sh` → gpu-server**, and that last script
ships `git archive HEAD` (never the working tree), hard-exits on uncommitted or
untracked scorer-tree files, then rsyncs and restarts. Landing a directory in the
NexusMind checkout does **not** reach readers; that run is the last checkpoint.

**The two trees currently disagree** — the v5 fix landed here; NexusMind's own copy of
`cultural_discovery/v5/config.yaml` has no `tiers:` block. **This self-heals:** the
next `deploy_to_nexusmind.sh cultural_discovery v5` propagates it. Do **not**
hand-patch the NexusMind copy. ⚠️ Note that deploy also lands the **LD#86 multilingual
topic-gate extension** — our `prefilter.py` is 87 lines ahead of NexusMind's and has
been since 2026-08-06. Runtime impact there is nil (the per-lens rule prefilter runs
with `use_prefilter=False`), but NM#284's **shadow pass rates will move**. Direction is
safe: llm-distillery is newer, this is not NexusMind divergence.

⚠️ **Do NOT reach for `.nexusmind-owns` — it CANNOT protect per-filter files, and it
fails silently.** Verified 2026-08-12: Step 1 of `deploy_to_nexusmind.sh` is an
unconditional `cp -r "${SOURCE_DIR}/"* "$DEST_DIR/"` with **no manifest lookup**; the
manifest is consulted only in Step 2, for `filters/common/`. The script's own header
says so. **Adding a `filters/{name}/v{N}/` path to the manifest is accepted and does
nothing.** Same silent-success shape as the op-point reader above. Per-filter content
is **one-way**: upstream overwrites NexusMind unconditionally. This is now guard A and
will abort the deploy rather than accept the entry.

Also worth knowing if controlled divergence is ever genuinely needed there: `cp -r`
runs **without `--delete`**, so it overwrites and merges rather than pruning — a file
NexusMind *adds* under a version dir survives, a file it *edits* does not. Adding is
durable, editing is not.

**Evening 2026-08-12 (fourth context): #106 CLOSED, and the GN thread reached a
mechanism.** Nothing deployed, no filter package touched, no oracle spend. Seven
commits, all docs/memory/one analysis script.

**The single most useful number to come out of it, and it will not drift:**
enrichment attempted **35,229 Google News proxy rows over nine days and replaced
zero of them** — 100.0%, CI 100.0–100.0, against control arms failing 0.7–7.1%.
FluxusSource had independently predicted it pre-gate from the URL scheme alone (a
GN `url` is an opaque redirect, so `pre_enrich` fetches a Google interstitial, never
a body). **State it as mechanism + measurement, and ALWAYS NAME THE FETCHER —
"NexusMind's `pre_enrich` cannot resolve GN, here is the confirmation" — never as a
bare number.** ⚠️ **The stronger form of this claim is REFUTED (2026-08-12):** "a
property of the URL scheme, so no fetcher change moves it" generalized from one
fetcher to the scheme and is false — **ovr.news resolves these URLs and enriched 74
of 103**, via `batchexecute`. See `memory/google-news-corpus-hypotheses.md` for the
scoped version and what the over-generalization nearly cost. ⚠️ It also does **not**
support FS#145 (which recovers a publisher *domain*, not a fetchable URL).

⚠️ **The window 2026-07-31..08-08 cannot be extended and there is no remedy** —
from 08-09 all six filters exclude `eval_aggregator`, and the arms stopped upstream
2026-08-11T14:06Z. `data/raw` is pre-enrichment; `shadow_mode` stamps forward-only.
Both were considered and rejected with FluxusSource. **Do not re-propose either.**

**⚠️ FRAMEWORK: still pinned v1.23.0, upstream still v1.25.0 (`889b038`,
re-checked at close).** No new releases since the morning triage, so the decision
table below is current and this is now **the first task of the next session** by the
owner's instruction.

**Carry forward from arm A, independent of cd v5:** ν, the **within-oracle**
run-to-run floor on a cd-lens population, is **0.436 mean / 2.10 max** at
temperature 0.3, measured by scoring 40 articles twice. It is **not** #95's 0.16
— that is a *student* batch-composition band and a different quantity. Any future
cross-oracle claim needs a gap above ~0.44 to mean anything, and the floor is
**arm-asymmetric** (0.238 on off-lens rows vs 0.634 on on-lens rows, n=20 each),
because off-lens rows return zeros from both runs and agree trivially.

| # | What | State |
|---|---|---|
| ~~**#109 Arm A**~~ | **DONE 2026-08-12 — verdict WITHIN NOISE, and it is a BOUNDED null.** 150/150 matched pairs, 300/300 rows scored, 0 errors. `MAD_refused` 0.8325 vs `MAD_passed` 0.8370, `D` = −0.0045, CI **[−0.216, +0.195]**, against a **measured** within-oracle floor **ν = 0.436** — the CI's widest excursion sits *below* the noise floor, so no interpretable effect can hide in the residual. **Per #109's pre-registered table this closes #105's `cultural_discovery` half: a retrain there is a base-rate change, not a label-quality repair.** $1.37 actual vs ~$1.20 estimated. Evidence: `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md` (pre-registration committed in `6741da2` *before* any score existed; result in `e01f1f1`). **Scope, which is the easiest thing to lose:** the estimand is the **pair-matchable** refused population, 2,024 of 4,458 (45.4%); the other 54.6% comes from outlets the lens gate refuses wholesale (`eco.sapo.pt` 0.93, `www.theverge.com` 0.90, `www.ad.nl` 0.87) and has no passed rows to match against. | **Closed** |
| ~~**#109 Arm A follow-up — the op-point band**~~ | **DONE 2026-08-12, $0.26. The +1.044 did NOT replicate: 66 pairs give `D₄` = +0.3958, CI [+0.056, +0.750], ν₄ = 0.6869 → NOT MATERIAL / not interpretable.** Not a clean refutation either (sign holds, CI excludes 0) — the effect, if real, is below what the instrument sees. **The instrument IS the finding: ν₄ = 0.687 exceeds the 0.396 it was meant to adjudicate, so a single-shot cross-oracle comparison at this op-point is unfalsifiable at ANY `n`** — the floor is per-article and does not shrink with sample size. The fix is repeated draws: `k = 4` puts the floor near 0.34 for ~$1.05 (arithmetic, assumes normality 40 pairs cannot establish). Also measured, and easy to misread: every row is stored ≥ 4.0 by construction and Gemini puts **37/66 refused (56%)** and **27/66 passed (41%)** back below it — that is **cross-oracle disagreement, not error**. Evidence: `docs/evidence/2026-08-12-cd-v5-op-point-band-followup.md` (pre-reg `d79a4be`, result `c43ed66`). | **Closed** |
| ~~**Pre- vs post-enrichment score delta**~~ | **DONE 2026-08-12 — NM#310 is a compute story, not a quality story.** Pilot n=300 across all six filters, b650 `venv-prodparity` CPU. **Control PASSED: 231/231 `stage2` rows within 0.16, median \|Δ\| 0.0000**, so the result is production-anchored. Delta: mean +0.270, **median +0.112**, 26.4% negative, p95 +1.452. **Crossings: 10/280 (3.6%) raw and 7/280 (2.5%) normalized, ALL UPWARD, 0 downward** — under ADR-023 enrichment cannot let junk through here, only surface what was already present. **The finding that travels: the SHORTEST stubs gain the LEAST** (0–150 chars +0.216 vs 300–600 +0.426), and GN stubs are median 89 chars — so the extrapolation to the population this cannot reach predicts *less* gain (H-E2, contested). Three new facts: **GN is 0.0% of the paired population** (0 of 122,557, by construction); **empty pre-enrichment bodies are 7.71%** and are a different harm (`_validate_article` rejects empty, so production could not have scored them either — enrichment is existence, not improvement); and **`stage_used` must be conditioned on** before `raw_weighted_average` is treated as a model output (23% of rows were `stage1_low` probe estimates). Also measured: this population's batch-composition floor is **0.000000**, so #95's 0.16 does not apply. Evidence: `docs/evidence/2026-08-12-pre-post-enrichment-score-delta.md`; open hypotheses in `memory/enrichment-delta-hypotheses.md`. | **Closed** |
| **`nature_recovery v4` returned a delta of ZERO — run the per-dimension check before believing it** | **H-E1, open.** +0.023 mean / +0.033 median with 39.6% negatives, against `cultural_discovery` +0.409 and `uplifting` +0.428, and 0 gained / 0 lost at both thresholds. The 397-row normalization fit is **ruled out** for the delta (computed on raw scores, normalization applies after) but not for the crossing count. **Do not cite "+0.023" as evidence enrichment is useless for `nature_recovery`** until per-dimension deltas are compared against `cultural_discovery`'s — an aggregate zero can be a cancellation. Costs nothing: the paired scores already exist. Fold into **#71**. | **Runnable, cheap** |
| ~~**Pre- vs post-enrichment score delta (original assignment)**~~ | **OWNER-ASSIGNED to llm-distillery 2026-08-12** (relayed via the NexusMind session). Decides whether NM#310 is a compute story or a quality story, and lands on ovr#312's ordering argument. Same article, same model, score on pre-enrichment text vs post-enrichment text. **Asked for beyond the headline:** the delta *distribution* not a central estimate; the sign breakdown **at the normalized 4.0 gate specifically** ("how many articles cross a gate they would not have crossed"); and split by **whether the body actually changed** — enrichment can succeed and return substantively the same text, and those rows drag any average toward zero for a reason unrelated to the effect. **Two traps:** #95's \|0.16\| band means small deltas are not effects, and never compare scores computed on two different machines. **This is the measurement I do NOT have** — my #310-vs-#309 ranking was inference from adjacent numbers (op-point de-selection, CDF residue, published share), and I told the peer so. | **Next** |
| **#109 Arm B** | **HELD on gaps 1–4, and cost is explicitly not the reason** (≤$7 total; $0 on b650 with local judges). Blocking gap is #1: the judge model is never named, and the obvious default (Gemini Flash) is the model that *made* `investment_risk v6`'s labels — that turns Arm B into a self-consistency check. Needs non-Gemini judges; precedent is cd v5's Qwen3:14b / Phi4:14b via `scripts/score_ollama_oracle.py`. Gaps 2–4 have proposed answers on the issue needing confirmation, not invention. | Held |
| ~~**#106**~~ | **CLOSED 2026-08-12 evening by owner ruling — no longer load-bearing.** The residue is real, small and one-way: max normalized Δ from removing all GN mass is **0.128 on `belonging`**, 0.0% of articles move ≥0.5, every crossing of the normalized-4.0 enrichment gate is **downward** — GN presence causes *more* enrichment, the cheap direction under ADR-023. The supporting reframe — *that experiment deletes all GN, so it forecasts the phase-out* — was **over-scoped and corrected the same evening by the FluxusSource session (my error, second comment on the issue)**: **ADR-007 retires population A only** (B stays, C can never migrate — a permanent GN floor), on **no date and no rate by design**, and **FS#145 is an attribution instrument, not the migration lever**. The decided deletion is strictly smaller than the one measured, so the *safety* claim is conservative in the right direction and survives; nothing else does. **Three carry-outs:** `nature_recovery v4`'s 0.367 is a small-fit problem, already on **#71** (397 rows vs a floor of 200) — nothing further needed there; **do not build a headline-only publication ban or a framing gate as GN-motivated work**; and **"GN gone" is neither "stubs gone" nor a decided outcome** — deleting *all* GN still leaves 10.0% of the corpus sub-300, and the decided scope removes nearer ~40% than 65% of stubs (order-of-magnitude, **do not quote**). Refit trigger belongs on our own measured GN share, not on upstream retirement events. Evidence: `docs/evidence/2026-08-12-gn-share-of-normalization-cdf.md`. | **Closed** |
| ~~**#107**~~ | **RULED + CLOSED 2026-08-12: a positive outcome suffices, a pleasant subject is not required.** Also settles the three held adjacent-lens rows (coffee frog, Buenos Aires estancia, Antalya nomadic tents). **#91 is untouched** — there the dominant subject and the scored text *disagree*, which this ruling does not license. Owner intends a retrain anyway; the home for any subject-weighting work is **`human_thriving` v8** (ADR-012 amended, #90), scoped against #91's mechanism. Unmeasured and stated: how often positive-outcome/unpleasant-subject items reach the lens. | Closed |
| ~~**Should ovr.news enrich at all?**~~ | **DECIDED 2026-08-12 by the owner: enrichment moves UPSTREAM.** ovr deletes its own pass; NexusMind's `pre_enrich` becomes the single enrichment point (**NM#339**; recorded on ovr#312). **The GN resolver is explicitly NOT ported** — Google News is being retired, so that half dies with the source. **The argument that decided it was structural and neither side had stated it: ovr's pass is the only enrichment in the chain that cannot RESCORE**, because ovr has no scorer, while NexusMind's `enrich_articles` enriches *and* re-scores. So the ordering problem is not "enrichment happens downstream of scoring" — it is *one specific pass changes the text without redoing the decision*. ⚠️ **My "don't fix the GN resolver" call was RIGHT and I withdrew it wrongly** — it never rested on the refuted URL-scheme claim, it rested on the retirement. See the gotcha entry *Conceding a correct conclusion because a neighbouring sentence was refuted*. Also: the four "correctly refused" rows from our 68-id lookup (cookie wall, paywall, video block, under-floor) did more work in the decision than the 38-article headline — ovr counted all four as *successes* because it accepts any text longer than what it had. **Carry-out for us: ovr#313's pre-flight source-length floor must land WITH the migration, not after it** — with no local enrichment, anything NexusMind cannot enrich arrives at ~100–140 chars and would be summarized from a stub (measured cut 29 summaries / 23 published per 11 days, 0.7% of published). ⚠️ **PRECONDITION added 2026-08-13, and it was nearly missed: consolidation routes ALL enrichment through NexusMind's decoder — the one that had the NM#338 charset bug when this was decided.** It held by luck of timing (fixed hours earlier). Posted to NM#339 as an explicit precondition. **The durable half is ovr's: the redundancy being deleted was also, incidentally, ERROR-DETECTION** — NM#338 was found by pairing against a second copy, so after consolidation the same fault reaches everything with nothing positioned to notice. Wants a *standing* probe, not a one-time check; the cheap one is the U+FFFD count (it is 4, and 4 is what moves if the surviving decoder regresses). | **Closed** |

### ⚠️ Framework drift again: pinned v1.23.0, upstream is **v1.25.0** — triaged 2026-08-12, ADOPTION DEFERRED to next session by the owner

Checked at session close (`/home/jeroen/repos/agent-ready-projects` @ `889b038`).
Two releases behind, both shipped 2026-08-12 — the same day we adopted v1.23.0, so
this is upstream velocity, not neglect. **Owner's instruction: continue in the next
session.** Pre-triage so it starts from a decision list:

| release | change | first read |
|---|---|---|
| v1.24.0 | `curate` reads **metadata, not documents** — Step 0.3 reads headings, a body is opened only for an entry being acted on | **Adopt.** Direct win on this repo's 203-entry gotcha log |
| v1.24.0 | `curate` Step 1 header read was level-blind | Adopt with the above |
| v1.24.0 | lint rule 8 — ratchet adopter-facing template sizes | Probably n/a; we ship no templates upstream |
| v1.25.0 | adversarial lens: **one rule — a claim that needs a measurement gets one, gets hedged, or is not ready** (merges #35 + #39) | **Adopt.** It is this repo's central failure mode stated in one line |
| v1.25.0 | `hypothesis-log` gains a **trigger in the working path**: write the entry at the moment the claim is made, with the lens finding as the cue | **Adopt.** Exactly the gap hit today — H-E3 was noticed while writing results up, not when the claim was made |
| v1.25.0 | shape rule: **never end a bolded phrase with a `**`-suffixed glob** (prettier ≤3.8.1 corrupts it) | Adopt as a writing rule; check our own skill files for the construct |
| v1.25.0 | the gotcha-log "2–3 lines" rule is **withdrawn** — *"Adopter action: none. If you have been ignoring it, you were right to"* | **No action, and note it vindicates our log.** llm-distillery IS the evidence: 203 entries, median 1,200 chars, 35% >1500 — cited upstream |

**Framework: adopted to v1.23.0 on 2026-08-12** (was v1.21.0, 2 releases behind —
v1.22.0 and v1.23.0 both shipped 2026-08-11 evening, so last session's "unreleased
candidate, do not pin it" is superseded). Triage table:
`docs/decisions/framework-adoption-history.md`. **The memory verify runner now
reads 25 pass / 0 fail / 0 error / 0 malformed, exit 0**, all 38 annotations
accounted for — up from the framework's own measurement of this repo at
12 pass / 9 fail / 5 error / 3 malformed. **One annotation needs
`VERIFY_TIMEOUT=120`** (the LD#92 DiD bootstrap, ~50s vs a 30s default); it is
annotated in place, so do not read its timeout as a broken claim. One item
deferred: v1.23.0's `<!-- placeholder -->` markers, to the next `audit-context`
run — 0 paths are marked today and a marker is only meaningful against a live
findings list.

**Earlier, still current:** `solutions v6`'s `community_practice_strength` is
**not dead — it is rare**, and no change is worth making. Three measurements in
`docs/evidence/2026-08-11-solutions-v6-community-practice-dimension.md` (commit
`3ea78a5`). Afternoon record: `memory/project_session_2026_08_11_afternoon.md`.
| ~~**Withholding gate**~~ | **NO LONGER A READER-SAFETY ITEM.** ovr#311 (a guard rejecting any summary longer than its source) blocks the whole class structurally, one stage earlier than a Chief Editor rule would; ovr#310 closed as superseded and the rule was never built. Reopen trigger over there is **non-GN only** — for Google News, NM#310 means the redirect never resolves, so the body cannot grow and the ratio cannot invert. Any remaining NexusMind-side ask is **data hygiene** (stop scoring/storing stubs), not reader safety, and is weaker. | Owner, if still wanted |

### Three enrichment passes, and why that is not as mad as it looks

Answering the owner's *"I cannot imagine we need multiple enrichments?"* — **measured,
not inferred**:

1. **NexusMind `pre_enrich`** — before scoring, short articles, no score gate
2. **NexusMind `enrich_articles`** — after scoring, `min_score` 4.0
3. **ovr.news** (`summarize.ts:453`) — before summarising, `content < 500` **AND NOT**
   `wasEnrichedUpstream`

**(3) exists for exactly one reason: it is the only one that can resolve Google News
links** — NexusMind has no GN resolution at all (verified). ovr places it late
deliberately: resolving at collection would be ~13,000 requests/day against a private
Google endpoint; late it costs ~15/day.

⚠️ **"But that unique capability fails every time" — REFUTED 2026-08-12 by the
ovr.news session, and the "don't fix the resolver" conclusion that stood here is
WITHDRAWN.** It was my error: ovr#312's line 20 cites NM#310 for *"these URLs can
never resolve"*, and NM#310 measures **NexusMind's** fetcher, which has no resolver
(verified: `grep -rniE "batchexecute|data-n-a-sg|resolve.*google.?news"` over
NexusMind `src/`+`scripts/` returns nothing). **ovr's resolver works and is live** —
`src/lib/google-news.ts:106-107` scrapes the `data-n-a-sg`/`data-n-a-ts` signature,
posts to Google's private `batchexecute` (`:43`), then fetches the *publisher* URL.
Measured on ovr's live DB: **74 of 103 GN rows enriched**, median 95 → 3,074 chars,
most recent success 2026-08-12 06:58. Acting on "don't fix the resolver" would have
retired a capability carrying **22 of ovr's 38** GN-derived published articles.

**And the consolidation argument inverts:** moving enrichment upstream to NexusMind
would *lose* GN resolution entirely, because there is no resolver there to move it
to. That belongs in the deferred *should ovr.news enrich* decision.

The ADR-007 direction is unchanged and still real (6 feeds moved 2026-08-08, median
length **89 → 326**, sub-300 share **100% → 47%**) — but it retires **population A
only**, so it does not make the resolver redundant on any stated date. The
withholding gate remains independent of all of it.

### Peer-owned, do not duplicate

ovr.news **#310** (withholding rule), **#311** (summaries longer than source — 324
published, 40 at ~8.9× expansion, **current** at 24 in August; the mechanism behind
their reader-reported #286), **#312** (silent enrichment refusal).
NexusMind **#322** (sizes the unmeasured wrong-body region; **n=300 is the threshold,
n=150 settles nothing** — unstarted; the LD-side source distribution they asked for
was sent 2026-08-12 and is **stratum-design input, not a frame**: it is a
cd-lens corpus published 2025-10-08 → 2026-05-27 and identifies no wrong-body
candidates), **#323** (post-scoring enrichment does not fan out across lenses —
0.1%, structural). FluxusSource **#145** / **#157**.

⚠️ **The earlier "NM#314 / PR #317 has not run a cycle" line here was STALE and is
deleted.** Peer-reported 2026-08-12 (their measurement, not verified by me):
merged and deployed to sadalsuud ~14:12 CEST 2026-08-11, 2 cycles on deploy day,
9 batches, `lines == candidates` in every one, and running every cycle since —
outcome-proven, not merely code-proven. Also from that session: NM#326 fixed a
verifier that printed `PASS` while never running the completeness check, so
**read its exit code, not its last line** (0 pass / 1 problem found / 2 gate did
not run).

**Two standing traps re-confirmed today.** Never oracle-score sub-300 content —
and note the corollary found this session: **difference-of-differences does NOT
rescue it**, because the short-content effect is length-dependent and therefore
confounded with the treatment variable itself (#109 § arm B). And when sampling
anything by length, **stratify by source** — #108 is the precedent.

---

## 🟢 2026-08-11 (afternoon) — OP-POINT CYCLE VERIFIED. Both read zero. #102 CLOSED.

**Done. The 12:02 cycle of 2026-08-11 confirmed both moves.** Full record:
`docs/evidence/2026-08-10-uplifting-v7-op-point-4.5-VERIFIED.md` (renamed off
`-PREPARED`).

| filter | op-point | rows tiered `medium` in the old band | baseline | verdict |
|---|---|---|---|---|
| `uplifting v7` | 4.0 → **4.5** | **0** (50 band rows, all `low`) | 81 | **PASS** |
| `investment_risk v6` | 4.0 → **4.25** | **0** (49 band rows, all `low`) | 82 | **PASS** |

**The secondary expectation was not met and that is correct, not a miss.**
`medium` read 58 and 224 against a predicted ≈152 and ≈318 — but this cycle's
batches are far smaller than the baseline's (1,720 vs 4,676; 1,210 vs 1,928), so
the absolute counts are **not comparable quantities**. As shares: `uplifting`
3.37% observed vs 3.25% predicted (matches); `investment_risk` 18.51% vs 16.49%
(runs high, which is the pre-registered `proxy_aggregator` caveat). **Do not
re-derive this as a failure next session.**

Both batches were confirmed **fully written before reading** (size stable across
3s; per-row counts sum to line counts). Pre-cycle, `TIER_THRESHOLDS` was read from
**NexusMind's checkout on sadalsuud** — the runtime source — not from `config.yaml`.

**#102 is closed** (2026-08-11), with its step 1 recorded as NOT RUN rather than
silently dropped: no second oracle batch was collected, and that step's second
half ("reach the sub-300 rows the first batch could not grade") is now refused by
the do-not-oracle-score-short-content rule. The known non-random hole in its
precision figures — 26 of 170 ungraded, 11 in the marginal band — therefore
survives the closure.

**Only remaining on this thread:** if a cycle-wide rather than
first-batch-per-lens count is wanted, re-run the command in the evidence doc.

### 2. Then: measure the `proxy_aggregator` after-side

Baseline saved at
`docs/evidence/2026-08-11-investment-risk-v6-proxy-aggregator-baseline.json` —
**it is unrecreatable.** Expected: `investment_risk v6` keeps excluding Google
News (now via `proxy_aggregator` instead of accidentally via `academic`) and gains
~310 rows: Guardian 290, Ars Technica 19, Quanta 1, IEEE 2.

**Attribute only the `google.com` row to this work.** The same FluxusSource
regeneration applied ~15 unrelated pre-existing drift changes (`nytimes.com`
unknown→news_major, `brookings.edu` think_tank→academic, several art/disability
feeds). FluxusSource flagged it unprompted.

### 3. ✅ DONE 2026-08-11 afternoon — #105's open question is ANSWERED, and it split in two

**Two deployed filters were trained on corpora >50% refused by TODAY'S labelling
gate**: `investment_risk v6` **51.6%** (length floor) and `cultural_discovery v5`
**52.2%** (its own `no_cultural_topic_signal` gate). `nature_recovery v4` is the
clean reference at **0.0%**.

**Answered without any oracle spend** — refused rows already carry the label they
were trained on, so comparing refused-vs-passed label distributions settles it for
free and never runs the oracle outside its validated range.
`scripts/research/gate_refused_label_audit.py`.

- **`cultural_discovery v5` — the RULE tightened, the labels are fine.** Lens-refused
  rows: mean label **1.102**, **2.4%** at/above the 4.0 op-point. Passed rows:
  **2.214**, **16.1%**. The gate refuses what the oracle also scored low, stripping
  tech/commerce domains hardest — off-lens for a culture filter, working as designed.
  **But**: dropping 4,458 rows that are 97.6% negative roughly **doubles the positive
  rate, 9.0% → 16.2%**, so any across-retrain comparison is non-comparable per ADR-023.
- **`investment_risk v6` — neither. Split out as #108.** The corpus-level numbers look
  like #92 short-stub inflation (refused mean 2.633 / 19.6% at-or-above vs passed
  2.245 / 8.3%) and **that reading is REFUTED**: length is near-perfectly collinear
  with source (elpais 97.8% short, spiegel 99.5%, aljazeera 100.0%), the one domain
  with both sides runs the *opposite* way (`ad.nl` short 2.086/9.7% vs long
  2.502/19.4%), and the 300–600 bucket **passes** the gate while looking identical to
  100–300. The floor is a **de-facto source and language filter** — a retrain removes
  six mostly non-English outlets at 93–100% each. Lands on NM#292.

**Still not established** (both halves): whether the labels are *correct*. This
compared distributions, not truth. Correctness needs the judge-panel substitute
below, never a re-score.

⚠️ **INSTRUMENT TRAP** — do **not** oracle-re-score Google News rows. Median
content is **89 characters**, and the 300-char floor exists precisely because short
content makes the LLM analyse the evaluation framework instead of the article. The
valid substitute is a judge panel asking *does the headline support the score?*
Full detail: `memory/google-news-corpus-hypotheses.md`.

### Owner rulings waiting

*(Both #107 and #106 have since been ruled and closed — kept here only as the
record of what the midday session handed over. The live decision state is the top
block of this file, not this list.)*

1. ~~**#107**~~ — **RULED + CLOSED 2026-08-12**: a positive outcome suffices, a
   pleasant subject is not required; also settles the three adjacent-lens rows.
2. ~~**#106 — Kačanik.**~~ — **CLOSED 2026-08-12 evening as no longer
   load-bearing**, after the residue was measured rather than assumed. Note the
   options list in the issue is superseded: option 1 (do not publish headline-only
   items) should **not** be built as GN-motivated work — but not because the
   population goes away on its own. ADR-007 retires only population A, on no
   schedule, and populations B and C stay.
3. **#104** — every accuracy number is CPU-measured; production serves on GPU.
   **Still open.**

### What the midday session established (do not re-derive)

**`memory/google-news-corpus-hypotheses.md`** is the file. Summary:

- **100.0%** of all 14,357 Google News items are sub-300-char headline echoes —
  both populations, max 277/283. With NexusMind#310 they are content-free at
  collection *and* unfixable downstream.
- Training corpora are **0–4.9% GN** against **25.3–25.5%** in production; three
  filters have never seen a GN row in training.
- GN is **1.1% of what is PUBLISHED** but **8.2% of `nature_recovery`**.
  A surfacing share is not a reader-exposure number.
- Panel of **all 39** published GN articles: ~33 of 39 defensible. But **19
  `nature_recovery` articles are 9 stories — Nepal's tiger census published six
  times** (→ NexusMind#188, with a cheap discriminator proposed).
- **#93 step-4 re-measure: gate still CLOSED, do not set `short_content.cap`.**
  The decisive ground survived a doubled window — short `solutions` rows max raw
  **4.878**, zero ≥ 5.0 over 13,406 rows.
- **REFUTED this session** (all mine unless noted): "96% removed downstream"
  (denominator error), "GN scores like its training labels" (measured **20.2%**,
  not ~50%), "ADR-007 closes the 25%/5% gap" (**58%** — population B needs a
  second lever), "a Nepal story arrived via a Zambia proxy" (grouping artifact),
  and the feed-count→item-mass inference (FluxusSource's).

### Landmine closed

`deploy_to_nexusmind.sh` **Step 1 is a bare `cp -r` with no manifest lookup.**
`.nexusmind-owns` covers only Step 2 (`filters/common/`), so **nothing** under
`filters/{name}/v{N}/` is protected and adding a manifest entry would not help.
`proxy_aggregator` had been committed NexusMind-side only and would have been
deleted silently on the next filter deploy. Ported into llm-distillery; usage block
corrected; both entries in `memory/gotcha-log.md`.

### Framework drift — 2 releases behind, unreviewed

**Stamped `v1.18.0`; agent-ready-projects released `v1.19.0` and `v1.20.0` on
2026-08-10.** The earlier "Framework: no drift" note further down this file was
true when written and is now marked superseded.

**Run `/update-drift` to triage properly — do not bulk-adopt.** One thing already
checked: **v1.20.0's load-bearing change does not apply here.** It adds a
session-start row to the project-file template so something points at the memory
index at the moment it matters; `CLAUDE.md:168` already has that row. The rest of
v1.19/v1.20 is documentation correcting the claim that the in-repo memory index is
auto-loaded (it is not — it is pointer-reached), which this repo's own
`/audit-context` run has now measured directly.

---

## 🟢 2026-08-10 — #102 (uplifting v7 specificity) step 2 DONE + the 21 `solutions_story` candidates adjudicated. Read this block first.

**NOTHING WAS DEPLOYED.** No config edit, no refit, no filter sync. Everything
below is evidence and curated data.

### 1. #102 step 2 — the op-point sweep, through the ADR-021 ground-truth gate

**`docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md`**,
machine-readable at `docs/evidence/2026-08-10-uplifting-v7-threshold-sweep.json`.

**Moving 4.0 → 4.5 is a real specificity gain, not noise.** FPR **8.11% →
2.70%**; specificity bands **[0.901, 0.941] vs [0.957, 0.982] — DISJOINT**. The
recall cost is real too ([0.685, 0.773] vs [0.583, 0.644], also disjoint): **24
fewer FPs for 27 more FNs**. **F1 bands OVERLAP** — expected, and the reason not
to use F1 here: it is symmetric, this problem is not (ADR-023). Recall and
specificity are conditional on the true class, so both transfer to production
despite the split's 32.7% enrichment; precision/MAE/F1 do not.

Ran on **production's own predictions** (the committed parity dump) — no
re-scoring, so it cost seconds instead of ~30 min on the serving box.
**Control passed:** at 4.0 the pipeline reproduces the committed
`ground_truth_gate.json` exactly (tp=159 fn=57 fp=36 tn=408, indeterminate 37).

**A hard constraint found, and it removes 2 of 5 candidate thresholds:**
**`MAX_NORMALIZATION_RAW_MIN = 4.5`.** `test_normalization_invariant.py` requires
`normalization.json` `raw_min` == the tier threshold, and
`production_scorer.py:513` rejects `raw_min > 4.5` and falls back to
`score_scale_factor` **with only a log warning**. uplifting v7's fit is
`raw_min: 4.0`. So **4.5 is reachable but sits ON the bound with zero margin;
4.75 and 5.0 are not reachable** without raising the constant in both repos, and
**any op-point move must refit normalization in the same change.**

**PRODUCTION FEED IMPACT (step 3, done).** Estimated from the 2026-08-09 oracle
batch band table; the 4.5 cut lands on a band boundary so nothing is
interpolated. Surfacing **1,193 → 870 per 6 cycles** (≈199 → ≈145 per cycle,
**−27%**); **off-lens reaching readers 302 → 164, i.e. 25.3% → 18.8%, 46%
fewer**; on-lens retained **79%**.

⚠️ **Correction to this block's first version: 4.5 does NOT "remove roughly
two-thirds of surfacing volume."** Two-thirds is the **false-positive**
reduction (36 → 12). Volume falls ~26% on the split, ~27% on the feed. I
conflated the two.

**WHICH TPs ARE LOST (step 3, done).** The 27 have oracle median **5.00**, range
4.20–6.25, **none above 6.5** — the loss is entirely the weakest quarter of the
positive set. They are **enriched in academic/preprint sources: 22.2% (6/27) vs
12.2% of the 189 survivors and 7.9% of the split** — the same class the adverse
adjudication called the dominant off-lens failure, i.e. part of the "recall cost"
is the oracle and student sharing a blind spot. **n=6: directional, not
established.** Genuinely on-lens losses to weigh: Dutch housing for young single
women, Paralympic curling gender integration, a high-court VAT ruling, a
physician on women's health literacy.

**⚠️ I RETRACTED YESTERDAY'S b650 CLAIM AND THE RETRACTION WAS WRONG. It is
withdrawn; the 2026-08-09 conclusion stands.** I argued "b650 not cleared at 4.5"
failed because the #95 specificity bands overlap. **Wrong instrument.** The #95
band answers *"what if batch composition changed"*; parity runs hold batch
composition **fixed**, so batch noise is not the source of between-box variation
and a band built from it proves nothing. Settled by a third run — see below.

**Three gaps closed in `ground_truth_gate.py`** (all backward-compatible; 270
unit tests green): specificity now carries a #95 band and is overlap-checked
**first and separately from F1**; new `--truth-threshold` pins what "on-lens"
means while the student's bar sweeps (without it the positive set moved under the
sweep, 216 → 193, and recall stopped being comparable across thresholds); the
overlap check now prints **DISJOINT** explicitly instead of only warning.
New: `scripts/verification/parity_dump_to_gate_input.py`.

### 1b. b650's GPU WORKS — and pinning production's stack CLEARS THE BOX COMPLETELY

**`docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`.** Two new dumps:
`…_b650-GPU-prodstack_…` and `…_b650-CPU-prodstack_…` in `datasets/parity/`.

**Use `~/llm-distillery/venv-prodparity` on b650.** **No sudo was needed** — the
old venv is built on the system python (`home = /usr/bin`, no headers); `uv
python install 3.11` downloads a standalone CPython that ships them. The old
`venv/` is untouched (the 08-09 dumps cite it as provenance).

**THE HEADLINE, and it reverses what I wrote three hours earlier: on CPU with
production's pins, b650 is 660/660 rows BIT-IDENTICAL to production, with ZERO
verdict flips at every threshold 4.0–5.0.** Different machine, different site,
different python patch level — not one score differs. **b650-CPU-prodparity is a
production-exact measuring instrument**; quote its numbers without qualification.
That removes the "only free between pipeline cycles" constraint from every future
threshold question.

**Decomposed one variable at a time** (this is what the fourth run bought):

| change | bit-identical | flips @4.0 | flips @4.5 |
|---|---|---|---|
| **host** (gpu-server CPU → b650 CPU, pins held) | **660/660** | **0** | **0** |
| **library stack** (b650 CPU, old pins → prod pins) | 15/660 | 0 | 3 |
| **device** (b650, CPU → CUDA, pins held) | 4/660 | **1** | 3 |

**⚠️ I published the opposite of this at midday and it was confounded.** I wrote
*"matching the library stack made agreement WORSE"* and hardened it into a rule —
*"you cannot clear a box by pinning its library versions"* — across five surfaces.
The comparison changed the stack **and** the device at once. The review battery
caught it; a ~16-min run on the free box settled it. **Pinning works, completely.**

**New open question, and it is not small:** CPU-vs-CUDA on the student is worth
**1 verdict flip at the deployed 4.0 op-point** and 3 at 4.5 (max |Δ| 0.1956).
**Production SERVES on GPU, while `ground_truth_gate.json` and the entire #102
sweep were measured on CPU.** The deployed numbers carry that term and nobody has
quantified it end-to-end.

**`constraints/production-gpu-server.txt`'s documented install command is
UNSATISFIABLE** — found by running it. `requirements.txt` needs
`datasets>=2.14.0,<3.0.0`, every version of which caps `fsspec<=2024.6.1`, while
**the constraints file itself** pins `fsspec==2026.1.0` and a `-c` file is a pin.
Production's serving venv has **no `datasets` at all**. *(A first fix blamed
torch for the fsspec pin; torch declares `fsspec>=0.8.5` — wrong mechanism, right
conclusion.)* The header now carries a command that works.

**`sadaltager` is predicted to need the same `uv python install` fix. Untested.**

**NEXT — the sweep still does NOT decide the flip:**
- **owner call**: is a ~145-article/cycle uplifting feed acceptable for 46% less
  junk? That is a product judgement, not a metrics one;
- re-examine the oracle labels on the 6 academic "lost positives" — if they are
  mislabelled, 4.5's real recall cost is lower than 0.611 implies;
- if it goes ahead: **refit `normalization.json` at 4.5 in the same change**, and
  note it lands exactly on `MAX_NORMALIZATION_RAW_MIN` with zero margin.

### 2. The 21 `solutions_story` candidates — adjudicated: 7 accepted, 3 rejected, 11 held

**`datasets/adverse/2026-08-10-uplifting-oracle-batch-adjudication.md`.**
`uplifting.jsonl` goes 4 → 11 rows.

**The framing was wrong and this is the part that outlives the batch.**
`content_type: solutions_story` is **not a lens signal** — it is the oracle's
*residual bucket* (none of the five penalty caps applied) and the tag the prompt
puts on its **own 7.3/10 and 5.8/10 good examples**. So "uplifting is absorbing
solutions-lens material" was an artifact of reading it as routing, and the
ADR-015 overlap defence covers **2 rows, not 21**. The real dominant class in the
21 is **academic-abstract register (9 of 21; 6 of the 13 in the 4.0–4.5 band)** — abstract prose
supplying benefit vocabulary and a high `evidence_level` with no beneficiary in
the text.

Two rules now written down: **`raw ≥ 4.01` is the admission bar** (an assertion
closer to the bar than the #95 floor is a coin flip, not a gate — one candidate
rejected on exactly that, raw 4.004), and **`oracle_wa` in 3.5–4.0 is held, not
labelled**. New fields `assertion_margin` and `oracle` on promoted rows.

Two accepted rows document **oracle-prompt gaps**: the `corporate_finance` cap
does not cover prudential regulation (EBA dashboard), and check C (speculation)
did not fire on an aspiration with no programme behind it (Namibian minister).

**Owner call still open — one question, not eleven:** three held rows are good
articles in an adjacent lens (new frog species, Buenos Aires estancia, Antalya
nomadic tents). *"Delight/discovery is not uplifting"* is an editorial line, not
a fact, and one ruling covers the class. The other 8 split **6 + 2**: six are
mechanical (a second oracle pass — `oracle_wa` in 3.5–4.0), two are valid accepts
left out so one register would not take 5 of 11 rows — a curation choice, not a
measurement gap. **The other 13 candidates (`doom_framed` 7,
`community_building` 3, `speculation` 2, `politics` 1) are untouched.**

### 2b. The review battery found 3 blockers in my own same-day work

`/review-changes` at HIGH tier, 6 lenses. Worth recording because every finding
was in work committed hours earlier and none was caught by 273 green tests:

1. **A guard that did not guard.** `parity_dump_to_gate_input.py` refused
   "uncalibrated" output by checking `load_calibration` returned something truthy
   — but a calibration file with a partial `dimensions` block is truthy, and
   `apply_calibration` passes those dims through raw. Measured cost: recall 0.759
   / spec 0.914 against the true 0.736 / 0.919, printed under a success line.
   This repo's signature defect, in a guard whose own message cites #98. Fixed.
2. **An evidence file inside a deployed filter package.** `threshold_sweep.json`
   sat in `filters/uplifting/v7/`; `deploy_to_nexusmind.sh:137` is an unfiltered
   `cp -r`, and a `--dry-run` would leave it **untracked** under `filters/`,
   where `deploy_filters.sh`'s `scorer_untracked_blocking()` runs in the every-4h
   `ExecStartPre` — **the scorer would refuse to start.** Moved to
   `docs/evidence/`. **`ground_truth_gate.json` still carries the same hazard.**
3. **A confounded causal claim** (see 1b) and **a vacuous statistical argument**
   (see 1). Plus: a DISJOINT verdict I added that fires 23.7% of the time when a
   model is compared against a subsample of *itself* — reworded to state only
   what it excludes; a silent all-zeros gate report when `--recompute-model-wa`
   is omitted — now a hard error; and ~12 doc-level errors, all fixed.

### 2c. The three unmeasured filters now have numbers, and the fleet is complete

`docs/evidence/2026-08-10-fleet-deploy-gate-completion.md`. `belonging v1`,
`cultural_discovery v5` and `investment_risk v6` were **live with no accuracy
number of any kind**. First measurements, at each filter's own 4.0 op-point:

| filter | recall | spec | **FPR** | n |
|---|---|---|---|---|
| uplifting v7 | 0.736 | 0.919 | **8.1%** | 660 |
| **investment_risk v6** | **0.761** | 0.955 | **4.5%** | 1045 |
| solutions v6 | 0.671 | 0.972 | 2.8% | 1032 |
| nature_recovery v4 | 0.650 | 0.979 | 2.1% | 391 |
| **cultural_discovery v5** | 0.587 | 0.980 | 2.0% | 857 |
| **belonging v1** | 0.600 | 0.985 | 1.5% | 738 |

**#102's premise survives the completed set** — uplifting is 1.79× the next worst
and 5.4× the best. **New: `investment_risk v6` at 4.5% FPR is the second
concern**, invisible until today, and it carries the fleet's *best* recall.
`belonging` and `cultural_discovery` are conservative, not broken (lowest FPR and
lowest recall together). Only recall/specificity are quoted — split positive
rates run 8.8–32.7% (ADR-023).

`cultural_discovery v5`'s gatekeeper **binds 0 times in 857 rows** — the #94
shape, second instance found. Worth its own look.

### 2d. The op-point move is PREPARED ON A BRANCH, not deployed

**Branch `uplifting-v7-op-point-4.5`** (pushed).
`docs/evidence/2026-08-10-uplifting-v7-op-point-4.5-VERIFIED.md`.

Staged rather than shipped: a filter deploy restarts the scorer and this could
not be verified until **08:00 on 11 Aug**, because the 04:00 cycle dies with the
Odido uplink. **Nothing scheduled invokes `deploy_to_nexusmind.sh`**, so it
cannot reach production on its own — verified, not assumed.

**Read this before deploying it:** the op-point lives in **four** places, and
`config.yaml` is **not** the runtime one — `base_scorer.py TIER_THRESHOLDS` is.
Changing the config alone is a no-op in production. I nearly did exactly that;
`fit_normalization.py` caught it by refusing to agree with itself and fitting at
the old anchor. All four now agree at 4.5, 273 tests pass, and the tier
assignment was **executed** (raw 4.49 → `low`, 4.50 → `medium`) rather than
inferred.

Before the cheaper alternative is proposed again: **a register/source-type rule
was tested out-of-sample and REFUTED** — it removes 2 false positives and costs
21 true ones. Details in the #102 evidence doc.

### 3. Housekeeping

- **Spam comment on #95 handled** (owner request): `michaelmanly`'s comment
  minimized as spam, account **blocked org-wide from `veen-systems`**. Personal
  block needs `gh auth refresh -h github.com -s user` (token lacks the scope);
  reporting to GitHub Trust & Safety has no API and needs a browser click. The
  account's public events are 71 issue comments across ~25 unrelated repos in
  bursts (12 repos in 37 minutes on 08-07), 0 followers, and GitHub's search API
  refuses to return it while the profile still resolves — likely a hidden/flagged
  account.
- `datasets/adverse/README.md` contents table had drifted a **second** time
  (uplifting n=2 vs 4 on disk, belonging n=1 vs 2). Fixed, and the table now
  carries the one-liner that regenerates the counts.
- `OpenAlex` rows carry `publication_year: 2050` / `original_published_date:
  2050-01-01`. Not chased.

---

## 2026-08-09 (night) — previous session close.

Sent to start #102. **Did not start it** — a prerequisite turned out to be
unverified, so this session removed the confound instead. Nothing was deployed;
nothing needs to be.

### What was actually established

1. **#102's premise survives.** `uplifting v7` spec **0.9189** was measured
   yesterday on b650, not the serving box. Re-scored the same 660 rows on
   gpu-server's own serving venv with model weights, all filter + `common/` code
   and the split md5-identical: **0 verdict flips at the 4.0 op-point, identical
   confusion matrix** (tp=159 fn=57 fp=36 tn=408). The number is production's.
2. **But the student is not box-clean, and 4.5 is inside the skew.** Only
   **2.3%** of rows are bit-identical; calibrated |Δ| max **0.2008**, *above* the
   #95 0.16 floor; at **4.5** three rows flip and specificity splits **0.9730
   (production) vs 0.9662 (b650)**. **A box is cleared at a threshold, never in
   general** — the e5 probe's 4.2e-6 does not transfer to the student.
   `docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md`.
3. **#102's sweep, on production predictions** (on-lens fixed at oracle ≥4.0):
   4.0 → FPR **8.11%**; 4.25 → 5.41%; **4.5 → 2.70%**; 4.75 → 1.58%; 5.0 → 1.13%.
   4.5 lands between `solutions v6` (2.8%) and `nature_recovery v4` (2.1%),
   trading 24 fewer FPs for 27 more FNs — right direction under ADR-023.
   **Not a decision**: no #95 band applied, `ground_truth_gate.py` not used,
   split is 32.7% enriched.

### Two corrections to yesterday's block

- **b650's GPU failure was misdiagnosed.** It is **not** a CUDA/libcuda link
  error. Triton's helper compile dies on `Python.h: No such file or directory` —
  **`python3.12-dev` is not installed**. `libcuda.so.1` *and* the dev symlink are
  both present and `gcc` links them fine (exit 0). The old reading came from the
  tail of a `CalledProcessError`, which prints the command line ending in
  `-l:libcuda.so.1`. **Fix (untried, needs sudo): `sudo apt install
  python3.12-dev`**, then `ssh b650-gpu '~/llm-distillery/venv/bin/python /tmp/tk.py'`.
- **`requirements.txt` ranges are the root cause of the wrong-interpreter class
  of error**, not any one box. Five interpreters across four machines all satisfy
  it with five different resolutions (torch 2.5.1 / 2.11.0 / 2.12.1 / 2.13.0;
  transformers 4.57.6 / 5.0.0 / 5.12.1 / 5.14.1). Production is now frozen in
  **`constraints/production-gpu-server.txt`** (91 packages, diffed against a
  fresh freeze). Note `torch==2.11.0` there is really `2.11.0+cu130` — pip freeze
  strips the CUDA tag.

### New, from two emails the owner forwarded

- **DeepSeek is raising API prices** — "significant increase", no numbers, no
  date (2026-08-06 announcement; continued use = acceptance). **The threshold
  that decides it is +64%**: DeepSeek off-peak $0.0011/article vs Gemini Batch
  ~$0.0018. Above that, Gemini Batch is cheapest and the cd v5
  DeepSeek-as-default precedent is void. DeepSeek *peak* ($0.0022) is already
  dearer than Gemini Batch today. Whole decision ≈ $5–6 per 8K-article retrain.
  Not affected: #102 (Gemini Flash oracle). Banner on
  `memory/oracle-pricing-scheduling.md`.
- **Odido maintenance 11 Aug, 01:00–07:00** takes the home uplink down. situla,
  sadalsuud and sadaltager all route via 192.168.1.1 — one uplink, all three go,
  plus Tailscale reach to gpu-server/b650. **The 04:00 cycle will be lost**
  (`Persistent=true` will NOT catch it: the host stays up and the timer fires, it
  just fails). 08:00 recovers. Expect a failed cycle in Tuesday's logs; do not
  diagnose it as a regression.

### Fourth box found: `sadaltager`

RTX 5060 Ti 16 GB (Blackwell sm_120), driver 610.43.02, 12 cores / 14 GB RAM,
425 GB free, on the home LAN. Only venv is `~/torch-test`: **torch 2.11.0+cu128
and nothing else** — no numpy/transformers/peft. Because it is empty it is the
cheapest box to build *from the lockfile*, and its torch already matches
production's version. **Prediction, unverified: it has no `python3-dev` either,
so it will hit b650's exact triton failure the moment it JITs on GPU.**

---

## 2026-08-09 (evening) — previous session close.

Sent to fix a calibration defect. **There wasn't one.** What the day actually
produced: one irreversible risk closed, a new ADR, two of my own headline claims
retracted, and the first accuracy number `uplifting v7` has ever had.

**NOTHING WAS DEPLOYED, and nothing needs to be.** Every artifact committed
today is either md5-identical to what production already runs (the three
recovered probe pickles), or training/dev evidence that production never reads
(adverse data, ADR, `requirements.txt`, gate JSON). The one live divergence —
`cultural_discovery/v5/prefilter.py`, repo 87 lines ahead — is **inert in
production** (`skip_prefilter=True`, `scripts/main.py:1207`), so shipping it
changes nothing and is not urgent.

**Framework: no drift.** agent-ready-projects is at **v1.18.0**, adopted. The
only commit past the tag is a README badge fix, and it is **unpushed in the
framework repo** (`294d83c`) — owner's to push.

> **SUPERSEDED 2026-08-11** (`/audit-context`): true when written, false now.
> The framework released **v1.19.0 and v1.20.0** on 2026-08-10; this repo is
> still stamped v1.18.0. See the top block. Left in place because this is a
> dated session record, not current state.

### The three things a next session should not re-derive

1. **`nature_recovery` is not miscalibrated and neither is anything else.** The
   173× surfacing spread is mostly genuine base-rate difference. Oracle-checked
   at 87% precision with ~8 true positives per 2,190 articles. Details below.
2. **ADR-023 now governs every quality claim**: optimise specificity, recall is
   a floor, **never rank filters on MAE**. Promoted to CLAUDE.md Hard
   Constraints. Two of my own claims died to it the same day.
3. **The oracle cannot see errors it shares with the student.** It graded
   `uplifting`'s ≥5.5 band 29/29 perfect; readers flagged articles at 6.85,
   6.49 and 6.09 in that band. **Oracle-only active learning cannot fix that
   class** — reader flags are the only independent label source.

### Open, in priority order

- **#102** (new) — `uplifting v7` specificity: 8.1% FPR vs 2–3% elsewhere; run
  the ADR-021 gate on a 4.5 op-point. First concrete target of #90.
- **Adjudicate the 21 `solutions_story` candidates** in
  `datasets/adverse/candidates/` — under ADR-015 they may legitimately belong in
  both lenses, so this decides most of the batch. Owner call.
- **One reader flag still open** — the Global Voices Assyrian-erasure essay,
  `belonging` 7.67. `datasets/adverse/2026-08-09-reader-flags.md`.
- **#81 repointed** — the sklearn mismatch is resolved (both boxes 1.8.0). The
  live one is **sentence-transformers 5.6.0 (sadalsuud) vs 5.2.2 (gpu-server)**
  on the mpnet + sklearn-MLP detectors, where the |0.16| skew was measured.
  **Obituary enforces at 0.85 with a 0.0012 margin.** Unmeasured.
- Three filters still have no ground-truth gate: `belonging v1`,
  `cultural_discovery v5`, `investment_risk v6`.

### Traps this session walked into, so the next one doesn't

- **gpu-server's system `python3` is NOT production.** The scorer runs
  `/home/hcl/gpu-server/nexusmind-scorer/venv` with
  `PYTHONPATH=/home/hcl/NexusMind`. Read it off `systemctl cat`. I published
  numbers from the wrong interpreter and had to redo them.
- ~~**b650 cannot run the Gemma student on GPU**~~ — **SOLVED 2026-08-10, and it
  needed no sudo. Use `~/llm-distillery/venv-prodparity` (~2 min per 660 rows).**
  `uv python install 3.11` downloads a standalone CPython that ships the headers
  triton wants; the old venv was built on the system python, which does not. The
  diagnosis history, kept because both readings were wrong once: ~~triton fails
  to compile its CUDA helper (`gcc` linking `libcuda.so.1`)~~ → **corrected
  2026-08-09 night to a missing `python3.12-dev`** (right cause, wrong remedy —
  the apt install was never run). Timing correction stands: on CPU the 660-row
  split takes **~16 min** on b650 and **~30 min** on gpu-server, not ~7. The e5
  probe path was never affected.
- **Matching articles by source prefix silently grabs the wrong one** — there
  are two `australian_abc_au` and two `south_african_namibian` rows in play.
  Use exact ids with an assert.
- **Excerpts are not sufficient for adjudication** — three of five adverse
  drafts moved after reading the full articles, in both directions.

---

## 🔴 2026-08-09 (evening) — scorer architecture/state audit: one real risk, and the calibration lead was a dead end

### The calibration thread ends here — nature_recovery is NOT miscalibrated

Oracle-scored 160 production articles with DeepSeek (nature_recovery's own
oracle, $0.21, 160/160 parsed), stratified by the student's own score over
6 cycles / 13,142 unique articles:

| band (student) | population | n | oracle ≥3.75 | implied/cycle |
|---|---|---|---|---|
| A ≥3.75 (surfacing) | 30 | 30 | **26/30 = 87%** | 4.3 |
| B 2.00–3.75 | 50 | 40 | 12/40 = 30% | 2.5 |
| C 1.00–2.00 | 353 | 40 | 1/40 = 2% | 1.5 |
| D 0.50–1.00 | 2,300 | 25 | **0/25** | 0 |
| E <0.50 | 10,409 | 25 | **0/25** | 0 |

Bands D+E are 96.7% of the corpus and the oracle's **maximum** there is 1.05 —
nothing is crushed down there. Precision at the gate **0.87** (recorded: 0.848);
implied ~8 oracle-positives/cycle vs ~5 surfaced → recall **~0.6** (recorded:
0.65). **"3 of 2,152" is not a defect — there are only about 8 of 2,190.** The
corpus genuinely holds ~0.36% nature-recovery content.

**RETRACTED, mine, same day:** I found an isotonic plateau in
`calibration.json` (`recovery_evidence` jumps **+2.47 over a 0.06 student
step**; >52% of the student's range maps to calibrated ≤1.33) and called it the
cause of the 173× spread. The plateau is real and measured — its *cost* is
about **3 articles/cycle**. Refitting it is not worth doing. **Do not re-open
the "isotonic crushes the scale" lead without re-reading this band table.**

Consequence for the 173× spread: the outlier is **investment_risk at 24.2%**,
not nature_recovery at 0.14%. Owner has deprioritised investment_risk for now.
Blocked anyway: `google-genai` is not installed and `requirements.txt:6` pins
the old `google-generativeai`, while `ground_truth/batch_scorer.py:569` imports
`from google import genai` — the declared env cannot run the Gemini oracle.

Suggestive, NOT significant: among oracle-positives, English recall 11/14=0.79
vs non-English 15/25=0.60, **Fisher exact p=0.304**. NM#292 axis; needs ~4× the
sample. One false positive worth knowing: a Bosnian article on *prirodni
priraštaj* (natural population **increase** = birth rates) scored 3.77 by the
student, 0.00 by the oracle.

### ✅ Done — the one real risk is closed (`b790b1b`)

**All six lenses run an e5 probe in production; only three pickles were in this
repo.** `cultural_discovery v5`, `investment_risk v6` and `uplifting v7`
existed on gpu-server and nowhere else. `.nexusmind-owns` is empty and
`deploy_to_nexusmind.sh` overwrites — the next sync would have deleted them.
Recovered, md5-verified against the running copies, committed.

Also pulled (gitignored by `filters/**/model/`, same as nature_recovery v4 and
solutions v6): **`uplifting v7`'s adapter weights, which existed in ONE place.**
NO_HUB because `training_metadata.json`/`training_history.json` were never
produced, so git ignores it and the Hub never had it. Verified md5
`eb0bf8416206b841`; PEFT keys OLD format (183 `.lora_A.weight`, 0 `.default.`).
**A durable second copy still needs an owner decision** — Hub upload would need
an honest model card that declares the metrics unknown.

**Why the repo was behind, and it is not the release path.** 35 of 36 shared
code/config files are byte-identical repo ↔ gpu-server. The gap is confined to
binary artifacts git was told to ignore. Root `.gitignore` ignores `*.pkl`; the
negation re-admitting probes (`!filters/*/v*/probe/*.pkl`) carried a trailing
same-line comment, which gitignore treats as part of the pattern, so it was
inert. Fixed 2026-07-10 (`f910032`). The split falls exactly on that date —
everything deployed before it is missing, everything after it is present.

### Two items from the audit that dissolved on measurement — do not redo them

- **cd v5's deployed `prefilter.py` is 87 lines behind this repo** (the
  2026-08-06 multilingual extension). **Deploying it changes nothing**: the
  per-filter rule prefilter still does not run in production —
  `scripts/main.py:1207` passes `skip_prefilter=True` and every scorer is built
  `use_prefilter=False` (NM#284, unchanged). The repo holds the good copy.
- **The #94 GATEKEEPER_CAP violations (cd v5 = 4.0, solutions v6 = 3.0) are
  already known, exempted and dated** in `tests/unit/test_gatekeeper_invariant.py`,
  with stated closure paths (cd when NexusMind moves to v6; solutions at its
  next version bump). Measured over 13,142 articles: **0 caps applied in
  either**; only 1 cd article with `evidence_quality<3.0` exceeds raw 3.50, and
  0 solutions articles with `concreteness<3.0` exceed raw 2.50. **Changing
  either cap now would fail `test_every_exemption_matches_a_real_violation`.**

### 🟡 Remaining, and it is the real work: Stage 1 is uncalibrated on 5 of 6 lenses

Only `solutions v6`'s runtime threshold equals its probe's own computed value.

| lens | runtime `DEFAULT_THRESHOLD` | probe's `selected_threshold` | corpus decided by probe alone |
|---|---|---|---|
| investment_risk v6 | 1.50 | *none* | 8.8% |
| nature_recovery v4 | 0.75 | **3.225** (ignored, documented) | 11.5% |
| uplifting v7 | 1.00 | *none* | 12.4% |
| belonging v1 | 1.00 | *none* | 14.9% |
| cultural_discovery v5 | 1.25 | *none* | **53.7%** |
| solutions v6 | **1.225** | **1.225** ✓ | **67.2%** |

Two training regimes: nr + solutions carry `selected_threshold` / `target_fn
0.02` / `val_fn_rate` / `val_recall_medium ≈0.98` (`train_probe.py --objective
recall`). The other four carry **only `val_mae`** — no threshold, no recall
guarantee. Probe val_mae: belonging 0.54, investment_risk 0.56,
cultural_discovery 0.87, **uplifting 1.10**.

**MEASURED 2026-08-09 — and the finding downgrades from correctness to
efficiency. At every deployed threshold the val FN-rate is 0.000.** All four
eyeballed thresholds landed on the conservative side. There is no live recall
bug in Stage 1.

Refitted all four on b650 (`--objective recall --target-fn 0.02`), probes kept
out of the repo in the session scratchpad, **nothing deployed**:

| lens | deployed | **val FN @ deployed** | recall-calibrated | val stage2-rate: deployed → calibrated |
|---|---|---|---|---|
| belonging v1 | 1.00 | **0.000** | 2.95 | 0.827 → 0.373 |
| cultural_discovery v5 | 1.25 | **0.000** | 3.25 | 0.826 → 0.316 |
| investment_risk v6 | 1.50 | **0.000** | 3.15 | 0.767 → 0.322 |
| uplifting v7 | 1.00 | **0.000** | 2.85 | 1.000 → 0.747 |

**Do NOT deploy the calibrated thresholds as a default action.** They buy a
2–3× cut in Stage-2 calls at 1.3–1.9% val FN — i.e. they trade recall for
speed, which is the wrong direction while the open complaint is that too little
surfaces. Take them only if throughput becomes the binding constraint.

⚠️ **val stage2-rate is NOT the production screening rate** — the val sets are
enriched (belonging 78 positives/738 = 10.6% vs 3.8% production surfacing).
Different quantities, not noisy versions of one (`rate-needs-population`).
Notable: `uplifting v7` at its deployed 1.00 passes **100% of val** — its probe
does nothing there — yet screens 12.4% of production.

**Cross-box parity: b650 is CLEARED to train probes for gpu-server.** Measured,
not argued — same 160 articles, same probe, the real `embedding_stage.py`
class: b650 (ST 5.6.1 / torch 2.13.0+cu130) vs the serving venv (ST 5.2.2 /
torch 2.11.0+cu130) gives **max |Δ| 4.2e-6, zero screening flips** at
0.75/1.0/1.25/1.5/2.85/3.25, bit-identical embedding checksums. That is
*smaller* than the serving venv's own CPU-vs-CUDA difference (5.4e-6).
**Scope correction:** `memory/b650-gpu.md`'s |0.16| cross-box skew was measured
on the **obituary detector** (mpnet + sklearn MLP). It does **not** generalise
to the multilingual-e5-small + torch MLP probe path.

⚠️ **THREE distinct stacks are in play; the SYSTEM python on gpu-server is NOT
production.** The service pins its own venv plus `PYTHONPATH=/home/hcl/NexusMind`:

    serving venv (gpu-server)  py3.11.2  torch 2.11.0+cu130  ST 5.2.2  tf 5.0.0   peft 0.18.1
    gpu-server system python   py3.11.2  torch 2.5.1+cu124   ST 5.2.3  tf 5.2.0   peft MISSING
    b650 venv                  py3.12.3  torch 2.13.0+cu130  ST 5.6.1  tf 5.14.1  peft 0.19.1

An earlier pass of this audit quoted the system python as production and had to
be redone. Read the venv off `systemctl cat nexusmind-scorer`, not `which python3`.

**Dependencies (`996c0c7`): two declared defects fixed, blanket upgrade
declined.** `google-genai` was never declared though `batch_scorer.py:569,579`
imports it — a clean install could not run the Gemini oracle at all.
`transformers<5.0.0` *excluded the 5.0.0 production serves*. No blanket upgrade:
the cross-box identity above currently holds and no open defect traces to a
stale dependency, so a bump would forfeit a measured property for nothing. The
parity harness is the acceptance gate for any future bump — require zero
screening flips.

Two smaller state notes: `belonging v1` and `uplifting v7` probes were pickled
with **sklearn 1.7.1** against gpu-server's **1.8.0** and emit
`InconsistentVersionWarning` on every load (the other four are clean).
Fitting-set sizes vary widely — calibration val n 389 (nr) … 1,045 (ir);
normalization 272 … 26,375 articles, a 97× spread. Only nr v4 and solutions v6
have a `ground_truth_gate.json` at all.

**Clean, verified:** all six probes load; all six normalization anchors correct
(`x[0]` == medium threshold); all six weight sets sum to 1.0;
`surfacing AND stage1_low` = **0 across all six lenses / 13,142 articles**, so
the hybrid design's core safety claim still holds. `pytest tests/unit` 270
passed, 4 skipped.

## 🔴 2026-08-09 — the lenses are not mutually calibrated, and #75/#76's closure does not hold

Owner: *"the mutual calibration of the lenses seems not to work"* — articles not
landing in the right outlets. Measured, one cycle, the same 2,152 articles
scored by all six lenses.

| lens | medium gate | raw p90 (all) | **surfaced** |
|---|---|---|---|
| investment_risk | 4.0 | 5.35 | **24.2%** |
| uplifting | 4.0 | 3.81 | 9.4% |
| belonging | 4.0 | 1.79 | 3.1% |
| solutions | 2.25 | 1.04 | 2.7% |
| cultural_discovery | ~4.0 | 1.94 | 2.4% |
| **nature_recovery** | **3.75** | **0.68** | **0.14% — 3 of 2,152** |

**A 173× spread in surfacing rate on identical input.** Five lenses gate at ~4.0
against raw distributions differing **8× at p90**. The gate is a fixed constant;
the scale it is applied to is not.

**NORMALIZATION IS NOT THE DEFECT — I said it was and was wrong.** Among
*surfacing* articles the normalized medians are **4.84 / 5.01 / 5.42 / 5.12 /
4.81** across five lenses (p90 8.8–9.6). That is exactly the cross-lens
comparability ADR-014 promises. The all-article `norm p90 = 0.00` that I first
read as "flooring 90% of articles" is expected: only ~3% surface, and
normalization is fitted on surfacing rows by design. **The defect is which
articles get to be surfacing, not how they rank once they are.** So this is
ADR-008 (calibration) territory, not ADR-014.

**#74, #75, #76 are all CLOSED — and #75's stated reason does not survive
re-measurement.** It was closed as *"nature_recovery v4 healthy; #75 was a
measurement artifact (probe-capped rows + files predating normalization)"*.
Checked that specific explanation against current data, splitting by
`stage_used` (now 100% populated since NM#300):

    stage2      (full model, NOT probe-capped)  n=3,532  p50 0.24  p90 0.67  max 5.44  surfaced 5
    stage1_low  (probe-capped)                  n=  493  p50 0.46  p90 0.71  surfaced 0

**The artifact explanation runs the wrong way** — probe-capped rows score
*higher* (p50 0.46 vs 0.24), so excluding them makes the picture worse. 3,532
fully-scored articles, p90 at **18% of their own gate**, five surfaced. The
condition is present in the non-artifact population.

**Do not re-open blind.** #76's other three threads were genuinely resolved
(uplifting unit-mismatch refit, belonging drift refit, the `_assign_tier`
double-cut under NM#280). Only the nature_recovery disposition is contradicted.

**Next step is diagnosis, not a refit** — a refit that does not know why the raw
scale sits at 0.2–0.7 will re-fit the same scale. Two candidates named in
`memory/calibration-history.md`: boundary-crush (raw ordering sound, gate too
high) vs scale-collapse (model barely fires). nature_recovery looks like the
second; belonging/cd like the first. **They need different fixes**, and
`memory/calibration-history.md` Dead Ends must be read first — `% norm<0.5` is a
known metric artifact there.

### Also measured the same day, unrelated to calibration

- **Junk detectors**: all three stamp 100% of rows, `obituary v5` / `violence v1`
  / `commerce v1`. Obituary and commerce **enforcing** (0 flagged survivors).
  **Violence flags 386 of 12,531 rows (3.1%) and ships them anyway** — shadow
  since 2026-07-28, never enforced, recall 0.550 @0.95 precision. That is a
  standing decision nobody has come back to.
- **Scorer staleness**: `investment_risk v6` deployed **2026-02-21** (5½ months,
  and it is the 24.2% outlier); **`uplifting v7` has NO MAE recorded at all**,
  raw or calibrated — a deployed filter whose accuracy has never been measured;
  `belonging v1` MAE 0.534, the weakest recorded; `nature_recovery v4` trained on
  3.9K, half of everyone else.


## 2026-08-09 (later) — the deletion happens three layers up, and one fix had been sitting merged-ready for six days

Full record: `memory/project_session_2026_08_09_later.md`. The session was sent to
certify one instrument; the owner's own question — *"FluxusSource is supposed to do
dedup only, then NexusMind does corroboration — are we on the right level?"* — turned
out to be the more valuable thread.

### ✅ Done

- [x] **INST-10 CERTIFIED by a non-author** (NexusMind `b90ba9e`), registered in
      V&V registry §2 together with INST-11, closing an open BACKLOG item where
      "nothing ships on `CERTIFIED: no`" was unenforceable for want of a row.
      Reproduced exactly: unweighted AUC **0.798 / 0.767**, 6/6 strata monotone,
      Kish ESS 36.1, robust to the date-only confound (0.798 → 0.794).
- [x] **REFUSED the flip it was meant to unblock, with evidence.** Certification
      does not authorise `temporal.enabled: true` — PROP-1's pre-registered
      falsification is a **recall** test at fixed cluster size, and INST-10 is
      precision-side-only by construction. That test has never been run.
      **And `sigma_hours: 72.0` in `config/app.yaml` is the refuted value**: at
      σ=72 the term nudges 99.1% of true pairs *and 79.4% of false merges*
      upward — a merge-more lever on a population already 83% wrong. Two-sided
      window is **σ ∈ [6, 36]**.
- [x] **Two INST-10 defects fixed.** Its docstring's weighted figures never
      reproduced (0.902/0.748 claimed vs 0.915/0.756 actual). Stratum weights
      were computed before exclusions, flattering the `--exclude-date-only`
      robustness check specifically (candidate 0.756 → **0.719**, ESS 83 → 31).
- [x] **NexusMind PR #299 MERGED** (`8ed8139`, closes NM#296) — the load-time
      `duplicate_title` drop is now source-aware. Rebased from `CONFLICTING`;
      the conflict was **one documentation row**. Tests 1021 → **1038**, +17,
      zero failures, CI green.
- [x] **Three deletion points identified, in series** — the answer to the
      owner's layering question. See below.

### The finding: three source-blind deletion points, not one

| # | Where | Deletes | Volume | State |
|---|---|---|---|---|
| 1 | FluxusSource content hash | same title+opening, **any outlet** | ~20 cross-source/run flagged (**provisional** — post-FS#142 reset) | FS#133 open; reframed as a **policy** bug, which unparks it |
| 2 | NexusMind `_is_duplicate` title check, **at load** | same normalised title, **any outlet** | **5,405 dup-title/cycle**, ~46.7% cross-outlet when measured | **FIXED — PR #299 merged, NOT DEPLOYED** |
| 3 | NexusMind `story_dedup` | whole clusters, keeps one | ~1,500/cycle | The counting/deleting conflation — unaddressed |

**Point 2 mattered most and was invisible from here**: it runs *before a single
embedding is computed*, so no threshold or representation change can ever reach
it — and it has been censoring the corroboration programme's own measurement
population. Every number in the V&V registry, the 0.173 precision included, is
computed on a corpus whose easiest positives were deleted first.

**Point 3 is the design flaw the owner's question actually names.** One clustering
pass with one threshold does two jobs with opposite risk profiles: it deletes
~1,500 articles/cycle *and* emits the `corroborating_sources` count that drives
ovr.news ranking. A wrong merge silently bins a distinct article **and** inflates
a trust signal. Nobody has measured how many of those deletions are wrong —
INST-12's row says so explicitly.

### Measurements made this session

- **Cross-source drops are ~half junk.** Classified FluxusSource's logged
      cross-source drops: **46% Google News feeds colliding with each other,
      42% real distinct outlets, 11% mixed** (corrected by the FluxusSource
      session from my `gn_`-prefix classification, which named only one of three
      GN populations). So "just stop deleting cross-source copies" would preserve
      more junk than signal — it needs a **publisher-identity** rule. PR #299's
      full-host comparison is exactly that, and independently replicates its own
      53.3/46.7 split on a different mechanism.
- **Generic-headline false-corroboration risk is not in the data.** 21,570
      titles, **282 cross-host collisions**, median title length 69 chars,
      **1 of 282 under 30 chars**. All specific events, no boilerplate.
- **PR #299's O(n²) safety net is fine** — 60 ms at 8,000 articles at a 40%
      duplicate rate, vs production's 2–4k/cycle.

### ⚠️ Corrections owed — three claims this repo gave the owner were false

Two of them drove owner decisions. All now corrected in
`memory/corroboration-feature-hypotheses.md` (`43815bb`).

1. **FS#143** — *"removes 100% of the duplicate class; 0 titles appear in ≥2
      category feeds"*. Both false. Category feeds duplicate **each other 738×
      in 7 days** (`cs_lg`×`cs` 452, `cs`×`math` 64, `cs`×`physics` 41), and
      **123 titles were unique to the dropped feed** (cond-mat 34, astro-ph 15,
      quant-ph 8…). The drop was still right — 82.8% of its titles were already
      carried elsewhere. **Consequence: 738 pairs/7 days remain, larger than what
      was removed. FS#143 did not close arXiv's contribution.**
2. **Contract A** — *"`additionalProperties: false`, so collection-stamping needs
      a schema change"*. False. `metadata` is open in **both** contracts; #305
      assumed a top-level field. This was the main reason post-enrichment was
      recommended.
3. **The post-enrichment recommendation itself** — measured 65/65 recall on 2,178
      scored rows, but that sample held **zero arXiv rows**, and `arxiv_announce`
      is the largest evidence class by 4× *and* reads 0.000 after enrichment. The
      gap was named when the decision was put to the owner and recommended past
      anyway. **A named gap is not a discharged one.**

**The shape, twice in one session:** a prior session's measurement relayed as fact
without re-derivation, inside a question that drove an owner decision.

### ⚠️ READ FIRST — direction, and a correction the agent had to make to itself

The goal is **releasing ovr.news to the general public**. A proposed working-rule
promotion was **declined** — do not re-propose the "an instrument that has never
returned a positive has not been shown to be able to" rule for `CLAUDE.md`; it
stays in the gotcha log.

**Then the agent over-corrected and was told so.** It concluded the next session
should be an ovr.news *issue triage* rather than pipeline work. The owner's
answer, verbatim in substance: **"getting the pipeline right is the most
important thing, otherwise I will not launch."** Pipeline correctness is not a
competing priority to the launch — **it is the gate**. Do not read the ranking
below as "stop working on the pipeline"; read it as "research on a switched-off
feature is not pipeline correctness".

**→ THE NEXT SESSION IS NexusMind#306, ON ITS OWN.** See the block after the
table.

**Ranking of the corroboration track against the goal:**

| | bearing on a public launch |
|---|---|
| **PR #299 (deployed)** | **Real.** ~392 more articles/day, and survivor selection fixed — 216 measured cases where a `news.google.com` redirect survived and the actual publisher was deleted. The publisher URL is the better one for article text *and* hero images, so this is page quality |
| **NM#301, the "N related sources" line** | **Judgement call.** It is a truth claim on the page, and 87.7% of what it counts is one wire story republished. "Related" is defensible; it is also exactly what a reviewer pokes at |
| **NM#306** | **Reader-visible.** Corrupted bodies miss the panel but reach the FILTERS, so articles get scored on text that is not theirs and the wrong things surface. ~18% for one outlet, unmeasured elsewhere |
| **INST-10 / PROP-1** | **None.** Research on a feature that is off and stays off. It was most of the session |

### 🔴 NEXT SESSION: ducroq/NexusMind#306, on its own — enrichment corrupts scoring input

**Found by the FluxusSource session, not this one.** Enrichment replaces a
correct article body with unrelated wire/widget content. One detector applied at
three stages: **0/725** at FluxusSource output, **0/300** at NexusMind
pre-enrichment, **282/1550 (18.2%)** post-enrichment. Two flagged rows carry the
*identical* wire body under different headlines — the signature of a page-level
widget being extracted instead of per-article content.

**Why it is launch-blocking and not merely a bug:**

- **The filters score whatever `content` holds.** A corrupted body means the lens
  score is computed on a different article than the title says, so the wrong
  things surface and the right things don't. Reader-visible by definition.
- **It is invisible to every check that exists.** Faithfulness scoring compares
  summary-against-input and the summary *is* faithful to the wrong text. The
  contracts check shape. `stamp_census.py` checks population. **Nothing checks
  whether the body belongs to the title.**
- **Nobody knows the corpus rate.** 18.2% is *one outlet*. If it is one Italian
  paper it is a bug; if it is 5% of the corpus it stops the launch. **Measuring
  this is the first task, not the fix.**

**⚠️ Cross-repo dependency — THE ORDERING CONSTRAINT IS REAL. My "it dissolves"
conclusion is RETRACTED, and it was the worst error of the session.**

I measured on `data/raw` files that were **all from Sunday 2026-08-09**, and
**arXiv does not announce at weekends** — verified after the fact: **0 arXiv rows
in 6,222 comparable rows**, `science_arxiv_*` and `ai_arxiv_*` feeds logged
"parsed successfully but contains no entries". *The population the exclusion
protects was not in the sample.* On a weekday arXiv is ~10.8k rows/week and
**100% `detected`**.

**I had written this exact lesson into the gotcha log hours earlier** — "the field
is bimodal and the corpus average measures the weekday" — and then drew an
adjacent conclusion from the same Sunday sample. Knowing the failure mode did not
prevent it; only applying it to *this* number would have.

**THE SEQUENCE, which is the part that would have hurt:**

    WRONG  delete the label first -> arxiv.org becomes `unknown`, investment_risk
           still excludes the STRING `academic`, arXiv stops being excluded,
           Aegis fills with preprints.
    RIGHT  investment_risk moves onto `metadata.primary_literature.detected`
           FIRST — arXiv stays excluded via the stamp, being 100% detected —
           and only THEN does FS#144 delete the topic-category branch.

Checked against config, not inferred: `arxiv.org` reaches
`type_classification: academic` **only** through the topic-category branch FS#144
deletes, across 14 feeds; same for biorxiv, mdpi, frontiersin, plos.

**What survives unchanged:** the 386 "would re-enter" rows are Global South news
mislabelled through the `google.com` collision, and releasing them is the fix —
that remains the best evidence for doing #144 at all. And it is **still not a
config change we can make**: `excluded_source_types` compares only against
`metadata.quality.type_classification`, so gating on the stamp needs NexusMind
code. Ordering is ours to schedule; implementation is theirs.

*Original measurement, retained because the numbers are right for the window they
were taken in and wrong to generalise from:*

Measured on `data/raw`, restricted to the 3,026 rows that carry the new stamp:

| | rows | meaning |
|---|---|---|
| `academic` AND `detected` | **69** | covered by the new stamp |
| `academic` NOT `detected` | **386** | "would re-enter" |
| `detected` NOT `academic` | **0** | no gain — the stamp is strictly narrower here |

**The 386 are overwhelmingly NOT preprints.** Top sources: `gn_asia_gn_united_arab_emirates` 75, `gn_africa_gn_algeria` 73, `gn_europe_gn_serbia` 62, `gn_central_america_gn_guatemala` 28, `gn_africa_gn_benin` 25, `gn_oceania_gn_papua_new_guinea` 25. That is **FS#144 exactly** — Global South news mislabelled `academic` because 308 Google News feeds collide on domain `google.com`. **Letting them re-enter is the fix, not the regression.** The genuine remainder is small and is science-*journalism* (`bioengineer` 13, `neuroscience_news` 12), `academic` because it writes *about* science.

**And it is NOT a config change we can make.** `excluded_source_types` is compared against **`metadata.quality.type_classification`** only — `src/scoring/source_filter.py::_get_type_classification`, three levels deep. **There is no mechanism to gate on `metadata.primary_literature.detected`.** Supporting that is NexusMind code, not a filter package, so **this belongs with the NexusMind session, not here.**

Also flagged: `detected` fires on **2.3%** of these rows (69/3,026) against the **8.94%** the FluxusSource replay reported over 167,234 rows. Different window and a small sample — but reconcile before anyone sizes a gate on it.

**Trap that nearly cost the whole thing:** `metadata.primary_literature` is a **dict** (`{"detected": false, "evidence": [], "detector_version": "v2"}`), so a truthiness test reads **8,864 of 10,955 = 81%**. Gating on truthiness would have blocked ~80% of the corpus. Read `.detected`.

**✅ STEPS 1–3 ARE DONE (NexusMind session, 2026-08-09). Read this before redoing any of it.**

- **Detector rebuilt and validated both ends**, with a per-source **null control** — each title also scored against a different row's body from the same source, so the threshold is read off a known-mismatched distribution. Sources that don't separate report **UNMEASURED**, not 0%. `israeli_israel_hayom` is UNMEASURED by design: its bodies are editorial standfirsts that paraphrase the headline with zero shared vocabulary.
- **Corpus rate: ~1%.** 25,707 of 115,843 judged replacements broke the title link (22.19%), **but 95% of those are the NM#276 consent/paywall class, fixed 2026-07-26**, and that window predates the fix. The #306 residual is **1,284 rows ≈ 1.1%**, an upper bound. **510 of 660 sources at exactly 0.00%**; worst are `southeast_asian_nst` 81.9%, `german_golem` 73.0%, `french_mediapart` 58.2%, `italian_il_fatto` 25.0%.
- **Guard shipped**: `should_replace_content` refuses a replacement whose title-affinity **collapses** (≥0.75 → ≤0.25). Beats strict-zero on **both** axes — 98.0% vs 85.0% of known-bad, firing on 0.66% vs 1.47% of the rest — so it is not a trade-off point someone picked. Recall on il Fatto **47/47**. `resolved_url` persisted, contract 1.16.0, additive, never `required`.
- **#276 was never fixed for non-English sources.** Its keyword list is English-only: **25.9%** of the residual is foreign-language consent walls (German, French, Dutch, Swedish, Malay). That is the **NM#292 axis** and the reason a *relationship* check is right — it catches them without knowing any of those languages.

**Numbers that were revised, all against the flattering direction, all labelling/plumbing rather than detector logic:** instrument recall 97.0% → **90.2%**, guard recall 59% → **47/47**, known positives 33 → **51**, non-English share 45.3% → **25.9%**. Their export v1 was truncated at 2,000 chars by a spool cache — **do not use it; v2 is clean**.

**Still open on #306:** the guard is **uncommitted** in the NexusMind working tree, so it is neither merged nor deployed — the defect is live until it ships. Then verify by outcome on a cycle, not by the predicate.

*Original session shape, retained. Corrected 2026-08-09 after the FluxusSource
session pushed back: an earlier version put "corpus rate" first. That ordering is
incoherent — the rate cannot precede the instrument — and the bias runs the wrong
way. A guarded detector silently skips every CJK, Korean, Greek, Hebrew and
Ukrainian source, so the rate understates **specifically on the non-Latin half**,
which NM#292 already says is disadvantaged at four independent stages.*

1. **Build a detector that can be trusted, before believing any null.** The
   existing one fails in two opposite directions, both proven 2026-08-09: it
   over-flags outlets writing proper standfirsts (Repubblica reads 73–86%,
   legitimately), and a Latin-only tokenizer flags every non-Latin title as
   disjoint by construction (`korean_yonhap_kr` 99.0%, `israeli_israel_hayom`
   99.7%). Guarding it with a minimum-token skip then makes it report **0 flagged
   for sources it cannot inspect** — identical to a clean source. Report
   **examined / skipped / flagged**, and validate against known positives (the il
   Fatto rows) *and* known negatives before trusting it.
   Requirements before any rate is quoted: report **`examined / skipped /
   flagged` per source, never flagged alone** (200 examined / 200 skipped must
   not appear as 0%); script-appropriate tokenization or an explicit per-script
   strategy — **character-bigram overlap for CJK**, where whitespace tokenization
   does not work; and validate at **both ends** — it must flag the known il Fatto
   positives *and* stay silent on a hand-checked sample of clean rows from at
   least one non-Latin source.
2. **Measure the corpus rate** — all sources, all six filters, not one outlet.
   **Per-source framing beats a corpus average**, because outlets writing proper
   standfirsts over-flag on top of everything else.

   **The repair path exists and is written down nowhere else:** the only
   surviving copy of a displaced body is in **`FluxusSource/data/archived/`,
   keyed by the same `id`, inside a 730-day window**. That turns #306 from
   "detect and prevent" into "detect, prevent, **and repair what is already
   stored**". Asked the FluxusSource session to put the exact path, file-naming
   pattern and id field on NM#306 before they wrapped.
3. **Locate the mechanism**: `should_replace_content` / `article_fetcher`.
   **NM#276 is the same family** (RSS summaries swapped for Google consent
   pages), so the code path is known. #276's guard is *content-shaped* — it knows
   what a consent page looks like. This one needs a **relationship** check:
   refuse a replacement whose body shares no distinctive token with the title.
4. **Acceptance test is a persisted row, not the code** — NM#300 and NM#303
   precedent. A green predicate test proves only the predicate.

**Related and already corrected: NM#307's central claim is retracted.**
`pre_enriched` and `original_content_length` *are* persisted — 6,014 of 6,014
rows where pre-enrichment ran, inside `nexus_mind_attributes.<lens>`, not at top
level. What survives is narrow but real: the **length** is kept, the **text** is
not, so a same-length substitution leaves no evidence in the row. Length is a
weak signal — il Fatto new/original ratio median **8.41** when enrichment is
correct vs **17.31** when a wire body was swapped in, overlapping distributions.

---

**After #306**, and only then: a launch-readiness pass over ovr.news's ~89 open
issues. Noticed but not investigated: **ovr#304 — `displayScoreThreshold` gates
publication on the normalized score, not raw, contradicting ADR-022**, which
decides what reaches readers at all. Also open: ovr#138 (private beta with
students), ovr#150 (launch newsletter). **ovr#299 — headline-only summaries
mostly invented — is CLOSED** (2026-08-05).

The corroboration items below are not withdrawn, just behind #306.

### Then — three owner decisions are TAKEN, these are their implementations

*Items 1 (deploy #299) and 3 (CLAUDE.md) from the earlier version of this list are
DONE. Decisions recorded on ducroq/NexusMind#301 and in
`NexusMind/docs/investigation/2026-08-09-prop1-recall-prereg.md`.*

1. **Boost on distinct headlines only** (owner decision 1, ovr.news).
      `corroboration-boost.ts` — the flat 1.3× on `display_rank` applies only
      where a related source carries a genuinely distinct headline. Display
      keeps counting all carriage; the label is already hedged. Also fix line
      13's "independent sources", which is measurably wrong.
2. **Persist the resolved URL at enrichment** (owner decision 2, NexusMind).
      Enrichment already fetches these pages and throws the final URL away. One
      field, no extra requests. Fixes `_outlet_identity`, the Google News
      ambiguity, and part of FS#144. Declare it in the contract so
      `stamp_census.py` sees it; **never `required` initially** (NM#300).
3. **PROP-1 recall test** (owner decision 3) — follow the pre-registration
      exactly. Baseline **3×** on different traversal seeds to measure the
      harness's noise floor FIRST, then temporal at **σ=18h** (not the shipped
      72, which is refuted). Ship only on all three: gain > floor, largest
      cluster does not grow, intervals do not overlap. b650 is idle and staged.
4. **Separate counting from deleting in `story_dedup`** — the design flaw the
      owner's layering question named. One pass, one threshold, two jobs with
      opposite risk profiles.
5. **PROP-2 ratio-margin scoring** — still the top untouched per-pair lever.
6. Deepen panel-v3's giant stratum, then revisit 0.94/0.90.
7. **~2026-08-18: re-measure on the CAPPED system.** Every precision figure in
      this area was measured with the 25-member cap disabled; the oversized
      clusters drain via the 14-day TTL around then.

### Not ours, in flight on the FluxusSource session

- `metadata.primary_literature` stamped at collection (`33c7f41`, deployed):
      replayed over 167,234 rows, **8.94% detected, 0 faults**. Verification was
      the 12:01 CEST run. Once live this is the primary-document exclusion
      predicate — worth **0.344 → 0.459** — with no source list.
- FS#143 executed (`754a4fe`, config-gated) plus 7 substitute archive feeds
      (`50b9150`); all 14 arXiv feeds moved to 12h because a daily *replaced*
      batch at 24h ±25% jitter can skip an entire day.
- FS#144 classifier fix, which must land before `investment_risk`/v6 moves off
      `academic` or arXiv preprints re-enter Aegis.

## 2026-08-09 — corroboration: the shippable change was refuted, the gate is the lever

Full record: `memory/project_session_2026_08_09.md`. Feature detail:
`memory/corroboration-feature-hypotheses.md`.

### ✅ Done

- [x] **Step 2 (a): production embeds `title_raw`** — `_prepare_text` returns
      `f"query: {title}"`, no stripping. The hypotheses file had quoted the
      `title_stripped` row for the live config; corrected.
- [x] **Step 2 (b): the 0.92 threshold does NOT transfer, and that was already
      known.** The v2 panel was adjudicated 2026-08-06 (registry OBS-13/27/28/29,
      PROP-6 "DOES NOT SHIP AS SPECIFIED"). My starting brief said the panel was
      unadjudicated — it was, in a gitignored NexusMind dir never copied to b650.
- [x] **Turn-over point measured** — fresh 680-pair panel v3, pre-registered rule
      (`NexusMind/docs/investigation/2026-08-08-turnover-prereg.md`).
      **`title_body@0.94/0.90`** passes all three gates. `title_body@0.92/0.88`
      decisively dead (17.7M merged pairs, giant stratum 0/25).
- [x] **Filed**: ducroq/FluxusSource#143 (arXiv duplicates defeat collection
      dedup — 600/8 days), ducroq/FluxusSource#144 (+scope-correction comment),
      ducroq/NexusMind#305 (article-derived primary-literature detection).
- [x] **Regression check**: `content_length` / `stage_used` / `stage1_estimate`
      **100% on the latest cycle**, all six filters (15,422 rows). The 54.8% over
      4 cycles is pre-fix rows in the window, not a regression.

### ⛔ NOT done, deliberately — do not read the pass as a green light

- [ ] **Do NOT flip `cross_source_threshold` yet.** 0.94/0.90 passes *my*
      pre-registered rule but **ties live under the #95 standard** (overlapping
      CIs). The live baseline moved **0.283 → 0.173** between two draws at
      n_eff 36, because 83% of pair mass sits in giant clusters sampled 25 deep.
      **Deepen the giant stratum first** — cheap re-run, not new machinery.
- [ ] **Production untouched.** No config changed, nothing deployed, in any repo.

### ~~Next session, in order~~ — SUPERSEDED, see the 2026-08-09 (later) section above

*Items 1–3 were all resolved or refuted the same day. Kept verbatim because three
of the five carried claims that turned out to be false, and the corrections are
the useful part.*

1. ~~**Certify INST-10 and turn the temporal term on.** Blocked *only* on review
      by a non-author.~~ **HALF DONE, AND "ONLY" WAS WRONG.** Certified — but
      certification cannot authorise the flip: PROP-1's falsification is a
      **recall** test and INST-10 is precision-side-only by construction. Plus
      the shipped `sigma_hours: 72.0` is the refuted value.
2. ~~**NM#305** — decide the stage; **Contract A is `additionalProperties:
      false`**~~ **SHIPPED AT COLLECTION by the FluxusSource session, and the
      Contract A premise was FALSE** — `metadata` is open in both contracts.
3. ~~**FS#143** — removes 100% of the duplicate class; 0 titles in ≥2 category
      feeds.~~ **DONE, but both measurements were FALSE.** The category feeds
      duplicate *each other* **738 times/7 days**, and 123 titles were unique to
      the dropped feed. The drop was right on other evidence (82.8% overlap).
4. **PROP-2 ratio-margin scoring** — still untouched, still the top per-pair
      lever (ART-11: F1 77.0 → 94.8 on the *same* embeddings). No new labels.
5. Deepen panel-v3's giant stratum, then revisit 0.94/0.90. Still untouched.

### Refuted this session (do not re-propose without new evidence)

- **Shared numbers as a corroboration feature** — AUC 0.581, rare-number variant
      **0.503**. Good argument, no signal on this data.
- **`type_classification` as the exclusion mechanism** — 86% of `academic` is
      Global South news, and the root defect (topic read as source type) survives
      the Google News retirement.

## 2026-08-08 (afternoon) — proven by outcome, and a self-inflicted outage

Full record: `memory/project_session_2026_08_08.md` (same file, second half).

### ✅ NM#300 + LD#88 — VERIFIED on production rows, both CLOSED

- [x] **`content_length` 100% populated in all six filters** (17:10 cycle), from
      **0 of 50,605**. `stage_used` / `stage1_estimate` likewise 100%.
- [x] **It was FIVE allowlists in series, not two.** The morning's fix corrected
      hops 1 and 5; the 12:03 cycle still read **0 of 2,170** with both fixes
      provably loaded. The three unexamined hops were all on the
      response → result-object boundary (`gpu_client.py` dataclass, its
      construction, `main.py`'s dict conversion). The earlier "verified there is
      no third" checked the *article → disk* seam, which is true and is not where
      the loss was. **Patching the sender proves nothing unless the receiver's
      parser is checked too.**
- [x] **Bonus, unasked**: with `stage_used` on disk for the first time —
      **no surfacing article is ever probe-scored.** `stage1_low` rows peak at raw
      0.75–1.50 against op-points of 2.25/4.0, so `surfacing AND stage1_low` is
      **0** in every filter. The hybrid design's core safety claim, assumed since
      2026-02, measured at last.
- [x] Contract B `content_length` → `required`: **still NO.** Now populated, but
      promote only after it holds across several cycles; rows before
      `filtered_20260808_17*` are absent-or-null forever.

### 🔴 I took the pipeline down, and it was a decision, not a slip

`nexusmind.service` FAILED at 16:07 and would have failed every 4h. Not a crash —
the fail-closed deploy gate refused to ship because
`src/scoring/gpu_client.py.bak_nm300third_20260808` was untracked under a guarded
path. **I had decided ~20 minutes earlier to keep those `.bak` files as a
rollback for an unverified fix**, when the commits were already pushed and git
*was* the rollback. Recovered 16:23; the 16:07 collection was reprocessed, no
data lost, one cycle delayed. Gotcha logged (`0c14de4`) — patch in place and rely
on git, or write backups **outside** the repo.

### ✅ cd v6 — both cutover blockers cleared, NOT deployed

- [x] Hub repo `cultural-discovery-filter-v6` created (private, v5 adapter
      verbatim, md5-identical, OLD PEFT keys, no `resave_adapter.py`).
- [x] `normalization.json` fitted n=3,680, `raw_min` 4.0, from `filter_version=5.0`
      rows **deliberately** — the "needs a historical rescore" framing was
      circular (a rescore needs the Hub repo) and its stated reason applies to the
      firehose, not to the `raw >= 4.0` fit set where the probe blocks 1 of 2,653.
- [x] `--check-hub` **9/9**; loaded end-to-end from its own Hub repo and scored.
- [ ] **The cutover itself** — deferred by owner decision so it doesn't share a
      cycle with NM#300. Then refit normalization from real 6.0 rows, then #87.

### ✅ LD#93 step 4 — sized, then the sizing was withdrawn

- [x] **Verdict: do not set the cap.** A cap ≥ the op-point removes **zero** false
      positives (visibility keys on raw), and nothing short reaches `medium_high`
      (max 4.93), so its stated purpose is already met and any cap ≥ 5.0 is a
      no-op.
- [x] Two corrections, both caught by the FluxusSource session: the residual was
      understated 3× (post-ADR-007 is **8.0/cycle**, not 2.6 — ADR-007 retires 59
      `gn_*` proxies, not the 243 publisher-named GN feeds), and the "topic feeds
      emit solution vocabulary" mechanism was **refuted** — `google_news_uplifting`
      is 80 short rows and **0** surfacing. It is one feed × one lens:
      `energy_storage` on solutions, 56.8%, and 0% on the other five.
- [ ] Re-measure gated on **measured GN-URL share per cycle**, not on "migration
      complete" — FluxusSource says there is no near-term done.

### ✅ Shipped alongside

- [x] **NM#303** production contract validation (`11d5860`) — Contract B CLEAN
      over 27,831 rows; **Contract A had never met production either** → **NM#304**
      filed with 4 defects (priority max 8 vs a 1–10 scale, `word_count` required
      on body-less sources, `source_type` enum missing `social`, undeclared
      `eval_query`).
- [x] **Census check A hardened** (`3f1bf07`) — it false-positived on
      `enriched`/`enriched_at`, which are rare-but-working (0–3 per filter per
      cycle). My first patch referenced a variable that does not exist and
      `py_compile` was green; only executing it caught that.
- [x] **`commit-msg` hook fixed** (`8741fa1`) — it false-failed on private Hub
      repos with no `HF_TOKEN`, and its own advice on failure is `--no-verify`.
- [x] **Framework v1.15.1 → v1.17.0** (`c286bb3`), reconciled by content.
      **agent-ready-projects#33** filed: `install-global-skills.sh` installs from
      the working tree, so an adopter can receive unreleased, later-reverted
      content — which happened for ~42 minutes today.

### Board

**197** — LD 34 · NM 44 · ovr 89 · FS 14 · ps 12 · atlas 3.
Closed today: NM#300, LD#88. Filed: NM#304, agent-ready-projects#33.

## 2026-08-08 — the checks failed, the analysis didn't

Full record: `memory/project_session_2026_08_08.md`. New topic file:
`memory/stamp-contract-integrity.md`.

### ✅ LD#101 — CLOSED, confirmed by outcome

- [x] **Confirmed live on the 08:49–08:55 cycle.** `eval_aggregator` rows in each
      filter's output went **21 → 0**, all six. Control: that cycle's *input*
      carried **22** such articles, so they were collected, scored, and stopped.
- [x] **Committed out of drift** — it had been running as *uncommitted
      working-tree edits on sadalsuud*, with nothing in `ducroq/NexusMind`
      referencing `eval_aggregator` at all. Now `9fb441a`; box fast-forwarded,
      tree clean, the six `.bak` files verified byte-identical to `e63202b`
      before deletion.
- [x] **The 30 published rows: 4 suppressed, 26 left to expire.** Not a cleanup
      job — all sat inside the 10-day window and age out 08-09..08-14 on their
      own, and most are good global-south coverage (Iringa/Njombe pine
      smallholders, Tanzania science policy, tree-kangaroo conservation deed,
      Els Xiquets de Tarragona). Bulk deletion would have hit exactly the
      population Chain 14 protects. `ovr.news@75bde57`, via the
      `manual_suppression` config kill switch — **not** a DB edit, because the
      live site builds from the R2 copy.
- [x] **Re-checked after the build 2026-08-08 — PASS exactly as pre-registered.**
      `gdelt_constructive_madagascar_7ff89d70aaf8` **404**,
      `newsdata_eval_td_456de0a16300` **404**, control
      `newsdata_eval_bi_1c78d8e397b7` **200**. The control holding is the part
      that matters: the suppression list is not over-matching.
- [ ] **Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
      solutions. Unusually good stream, or scorers over-rewarding it? Check
      against LD#91 and NM#289 upper-tail inflation.

### 🔴 The pre-registered check would have called this fix broken

The check was *"`source_filter excluded N` must exceed the 121 baseline"*. It came
in at **86** — lower. That line aggregates all excluded types and swings with
corpus composition (**69 → 121 → 86** in one day; investment_risk 519 → 545 →
946). It was never sensitive to the one type added. **A metric that moves for
reasons unrelated to your change cannot confirm your change.** Two more of my
instruments broke the same day (a `len>3` language heuristic; a watcher whose
hour-glob matched the *date*), against zero broken conclusions.

### 🟢 NM#300 — fixed, deployed, NOT yet proven *(SUPERSEDED — see the afternoon section: it was FIVE drops, and it is now verified and closed)*

- [x] **Two drops in series**, so fixing either alone changes nothing:
      `FilterScoreResult` in `deploy/gpu-server/main.py` is a Pydantic allowlist
      (**kills it first**), then `scripts/main.py`'s `analysis` allowlist.
      Verified there is no third — `analysis` is attached whole and written with
      `json.dumps(article)`.
- [x] **Both halves deployed.** Free: the scorer was already down with ollama
      holding the GPU, so no restart and ollama untouched. gpu-server half
      **proven on the box** by `ast`-extracting the model classes verbatim from
      the deployed file and executing them in the scorer venv.
- [x] **OUTCOME CHECK RAN AND FAILED** — the 12:03 cycle read **0 of 2,170** with
      both fixes provably loaded. *"Suspect a third drop"* was the right
      instruction and there were **three** more. Closed out in the afternoon
      section above.
- [ ] Promote `content_length` to `required` in Contract B **only after** the
      census shows it populated **across several cycles**. One green cycle is not
      enough for a field that reached zero rows for months.

### 🟢 Stamp census + contracts — new, and they found things nobody asked about

- [x] `scripts/stamp_census.py` (`e64a45f`) — checks **population** and
      **consumers**, which no schema can express. It **failed its own acceptance
      test on first run** (missed NM#300, because absent ≠ null; missed LD#94,
      because six filters averaged hide a single-filter constant). Both gaps are
      why checks A and per-filter constancy exist.
- [x] **Contract B 1.15.0** (`3030e35`) — first-ever validation against
      production: **908 violations**. `image_analysis.image_confidence` declared
      `0..1` is a **raw logit** (−12.330..6.365, median −2.696, 68.4% outside).
      Producer right, contract wrong since it was written; fixtures could never
      have caught it. **908 → 1**, that one real and left failing.
- [x] Filed **NM#303** (contract tests validate fixtures, never production) and
      **FS#138** (a `null` inside `tags`).
- [x] **LD#88 item 1 gained evidence**: the census found `stage_used` and
      `stage1_estimate` assigned by a writer and present on **no** row. Fixed and
      verified the same day; **LD#88 closed** (all four items).
      ⚠️ Check A also **false-positived** on `enriched`/`enriched_at` in the same
      run — rare-but-working, 0–3 per filter per cycle. Hardened in `3f1bf07`.

### Board

**196** — LD 36 · NM 43 · ovr 89 · FS 13 · ps 12 · atlas 3. Sediment **74**
(cutoff 2026-07-09 — quote the cutoff, it moves on its own).

**Chain 8 (Google News) is CLOSED** — `ADR-007` accepted, FS#120 + FS#119 closed,
native-first, GN proxies and all three eval arms retired. **Done by a parallel
session 30 minutes before I commented on the issue asking for a decision already
taken.** So the board now has **no calendar-bound item at all**.

## 2026-08-07 (night) — the dedup question answered by mechanism, and a deadline in trouble

Full record: `memory/project_session_2026_08_07_night.md`.

### 🔴 LD#101 — evaluation arms are scored AND PUBLISHED (filed tonight, needs an owner decision)

- [x] **DECIDED 2026-08-08: exclude via `excluded_source_types`** — because that
      mechanism **already is** "score, don't publish".
      `NexusMind/src/scoring/source_filter.py::apply_source_filter` marks
      **already-scored** articles as `passed_prefilter = False`, so scores are
      kept and the rows never reach `filtered/` or ovr.news. *I first recommended
      building the same gate in ovr.news, on the wrong premise that
      `excluded_source_types` prevents scoring — it does not, and
      `memory/nexusmind-data-sources.md` had said so since 2026-08-02.*
      No new code, no third-repo change, no LD#95 batch perturbation (the corpus
      is unchanged), and it keys on `type_classification`, which is verified to
      survive into `ovr.db`.
      **Count corrected: 30 published rows, not 28** — `source LIKE '%_eval_%'`
      misses `gdelt_constructive_*` entirely. The two extra are Traditional
      Chinese Taiwanese local news at tier `high` under a Madagascar query.
      **Never key on the source string.**
- [x] **SHIPPED 2026-08-08.** `eval_aggregator` added to `excluded_source_types`
      in all 6 live filters + `cultural_discovery/v6` (the cutover candidate), and
      `eval_aggregator` added to `KNOWN_SOURCE_TYPES` in
      `tests/unit/test_filter_config_schema.py` — the schema gate rejected it
      otherwise, exactly as designed. Suite green (269 passed, 4 skipped).
      Copied surgically to `NexusMind/filters/*/config.yaml` (**not** via
      `deploy_to_nexusmind.sh`), backups at `config.yaml.bak_20260808_074336`.
      No restart needed: `nexusmind.service` is a per-cycle process, dead between
      runs, so configs load fresh; `scripts/main.py:1016-1018` is the caller.
      **Verified by EXECUTING the guard on the deployed config**, not by reading
      the key — positive and negative control:
      `eval_aggregator → passed_prefilter False`, `news_regional → True`,
      `excluded_count 1`. All 6 confirmed `eval_aggregator=True, shadow_mode=False`.
- [ ] **Confirm on the next cycle's log** (00:02 / 04:00 grid) — the `N scored,
      M prefiltered` line should show the eval arms among the prefiltered. That is
      the end-of-run outcome check; the guard test above proves the predicate and
      the load, not the production run.
- [x] **`memory/nexusmind-data-sources.md` updated** with the two traps this
      creates: corpus statistics over `data/filtered/*` will silently omit the
      eval arms, and FS#120's funnel must be read from the **GPU scorer log**,
      not from `filtered/`.
- [ ] **Remediate the 30 already-published rows** — reader-facing, ovr.news side,
      independent of the decision.
- [ ] **Check the Zimbabwe funeral row against the obituary gate** (enforcement is
      ON at v5@0.85). If it scored under threshold it is a live false negative and
      belongs in `memory/project-obituary-detector.md`.

- [ ] **FS#133's question is STILL OPEN — my "arbitrary" answer was retracted
      the same night.** The dedup survivor *within a run* is decided by
      `as_completed()` completion order — that part holds, though it is
      **untestable**: no fetch-duration field exists anywhere. But my premise
      ("both drops happened inside one source") is an **instrument artefact** —
      only **4,116 of 40,693 hashes (10.1%) carry a source**, so cross-run drops
      are structurally undetectable and every countable drop is same-run *by
      construction*. FS#133's own first comment said not to conclude from n=2; I
      did. **The cross-run mechanism is the bigger one and it is systematic**:
      `seen_hashes` persists 30 days, so the winner is whichever *run* polled
      first, set by `update_frequency` — GN feeds are **1 sub-12h vs 159 non-GN
      sub-12h**, i.e. **publisher-correlated**. And the loss is **sticky for up to
      30 days**, not reversible next run. Re-read after the next cycle: incumbents
      now carry sources, so cross-run drops become visible for the first time.
- [ ] **Measure near-duplicate SURVIVAL, not just deletion.** In the 20:06 run,
      **6 cross-source syndicated stories survived** dedup (different snippet →
      different hash) against **2 dropped** — one survivor being the same story as
      a drop, via a third outlet. Exact-hash dedup may not be where the
      corroboration evidence goes at all. Nobody has measured this.
- [x] **FS#134 DECIDED: delete.** Four independent grounds; the signal already
      exists downstream (E5 cosine at `cross_source_threshold=0.88`), it degrades
      cross-language, wiring it into dedup makes corroboration *worse*, and the
      emit-instead option is blocked by a live `numpy.uint64` JSON bug. Deleting
      drops `scipy` too — **114 MB of a 450 MB venv** — and removes the import
      that caused a 26-hour outage on 2026-06-30. Posted to FS#134.
- [x] **Board maintenance DONE** — NM#225 → Chain 15 (**re-dated 2026-05-28; the
      chain is 71 days old, not 2, and NM#225 is its root and the most actionable
      of the three derivations**), NM#226 → Chain 13, NM#254 → Chain 16 (it holds
      the SemEval-2023 taxonomy decision), **Chain 17 (NER) promoted** into the
      canonical chain list with five dependents.
- [x] **Cross-repo dependency audit: 13 live instances** of an OPEN issue citing a
      CLOSED dependency. FS#85 alone has **five** dependents (NM#223, ovr#222,
      ovr#223, ovr#231, ovr#232). Correcting comments filed on all uncorrected
      ones plus LD#38 (→NM#108), LD#56 (→NM#161), LD#23 (→NM#88).
      **Two were my own, filed the previous session** — FS#133 and FS#134 both
      cited NM#213 as the live consumer; NM#213 has been closed since 2026-05-23.
- [x] **Framework adoption verified by content, not by stamp** —
      `agent-ready-projects` v1.15.1 is genuinely installed (five marker strings
      present; installed mtime matches the commit to the second), `curate` body
      identical to template, no global `review-changes` shadowing the project one.
      `agent-ready-papers` is at v2.4.0 + 2 doc-only commits and is **not adopted
      here by design**.

### ⚠️ FS#120 (due ~2026-08-14, 7 days) — two measurement defects found

- [ ] **`newsdata_eval`: the local-publisher share is 40% / 12% / 8%, and that is
      probably H3's ANSWER, not a defect to fix.** ~~Same defect as GNews; add
      `country_queries`~~ — **WITHDRAWN, and it would have damaged the gate.**
      NewsData sends `country=` with **no `q=` at all**: it filters on *publisher
      location*, so it is the **geographic** arm, while `gnews_eval` uses `q=`
      only because its free tier can search topic alone. A comment at
      `newsdata_eval_aggregator.py:104-108` says exactly this and I read past it.
      Adding `country_queries` would convert the only geographic arm into a second
      topical one and destroy the like-for-like comparison against GDELT.
      My "77–97% off-topic" therefore measured the **wrong property** — an article
      from a Chadian publisher about cricket is *correctly* returned. Re-measured
      on publisher over the same 8 runs: **Chad 40.0%** genuinely local
      (`alwihdainfo`), **Madagascar 11.8%** (58.8% is `ign_za`, a South African
      video-game site), **Burundi 8.3%** (79.2% is `thecitizen_co_tz`, Tanzanian).
      **Score H3 on `metadata.publisher_name`, not article topic**, and re-derive
      at the API response — those denominators (65/34/24) survive a 49% dedup drop.
- [ ] **`items/day` is censored** — every eval identity is capped per run
      (`max_articles: 10` × 3 countries = 30; GDELT `max_records` 30–50 hardcoded).
      `gnews_eval` sat at exactly 30 in **13 of 44 runs (29.5%)** — and the more
      informative half is the floor: **21 of 44 runs returned only 10**, i.e. two of
      three countries yielded nothing. (30 is the ceiling *by arithmetic*, 3 countries
      × `max_articles: 10`, not an empirical discovery.) The readout must say it
      compares *tier ceilings* against the GN proxies' uncapped RSS supply.
- [ ] **H2 (GDELT starvation) — my "76% → 66%" was REFUTED; the sign is backwards.**
      Full record: pre-fix **66.4%** (122 runs) → post **76.9%** (13) / **80.0%**
      (10); Fisher **p = 0.546**; items/run 19.1 → 10.0. My "76% pre" was the
      issue's last-8-runs snapshot and my "66% post" was Aug 7 alone, dropping four
      post-fix Aug-6 runs that all yielded zero. I also split on the GitHub **close
      time** rather than the deploy time (`git reflog`: `0fa9ffa` 08-05 18:09,
      `61be1b1` 08-06 07:49 — two commits, the first still broken). **What holds:**
      FS#125's *coverage* half is real; the *yield* half cannot move — it is an
      external per-IP quota shared by two identities, and the plan doc already says
      "~50% zero is the designed behaviour". **H2's real question is whether the
      free tier is viable at all** — FS#125's Option 3, still undecided, and
      FS#132 still gates `gdelt_constructive`'s half.
- [ ] **Every rate in the readout needs a "measured over which window, across
      which config changes" line.** The eval period contains FS#125 (08-06),
      FS#128 (08-06) and the GNews `country_queries` change (08-05). I published a
      72.6% figure that straddled the FS#125 boundary and had to correct it.

## 2026-08-07 (late) — coverage pass, a refuted plan, one instrument shipped

Board was reported unchanged at **195 open** — *corrected 2026-08-07 night to **198**; this pass never re-counted after filing FS#133/#134*. The work was in what it does not cover, and in
one finding upstream. Full record: `memory/project_session_2026_08_07_late.md`.
Feature-level detail: `memory/corroboration-feature-hypotheses.md`.

- [x] **Cross-source dedup stamp SHIPPED + DEPLOYED** — `ducroq/FluxusSource@4994d61`,
      live on sadalsuud. Collection dedup drops on `md5(title + content[:500])`
      **with no source comparison**, so the same wire copy from two outlets is
      deleted before NexusMind ever embeds it. Drop behaviour unchanged; the
      collision is now counted and reported at INFO. **FS#133.**
- [x] **FS#134 filed** — MinHash + Jaccard implemented, `datasketch` pinned,
      **zero call sites**. Wire it up as a corroboration feature or delete it.
- [x] **NM#232 planned, then refuted by a six-lens review.** Findings filed on the
      issue. Do not build as specified: its consumer list omits the only consumer
      with code (the matching model — **NM#188/NM#301**; NM#213 is CLOSED), which wants a cross-lingual *offline
      re-run*, not a CPU pipeline stage.
- [x] **Dependency corrections filed** on NM#223 and ovr#222 — both cite
      `FluxusSource#85`, which is CLOSED and re-homed to NM#232.
- [x] **Read the cross-source count** — done 2026-08-07 night, and the count is
      **not yet readable**: only one run has carried the stamp (20:06), giving 2
      drops; the timer is 6 runs/day and the figure stays a floor until
      ~2026-09-06. **The question it was meant to answer was settled by reading
      the call path instead** (see the night block above). Step 3 of the
      corroboration track is still gated — but expect "the pairs were never
      there", not "the pairs are biased".
- [x] **Board maintenance** — done 2026-08-07 night, plus Chain 17 promoted and
      seven stale entries corrected (NM#213/#220/#91, LD#43/#49, FS#125/#126) and
      a count error fixed (**198 open, not 195** — the pass never re-counted after
      filing FS#133/#134).
- [ ] **Owner call**: does `ducroq/augmented-engineering` (34 open, **1 closed
      ever**) belong on the board? CLAUDE.md mandates filing evidence into it.

## Commerce Prefilter SLM - NEEDS REWORK

ML classifier for commerce/promotional content detection. Cross-cutting prefilter for all filters.

**Status:** v1 complete but needs redo - concerns about multilingual embeddings and context size.
**v1 is the version running in production** — force-pinned by LD#80 because **v2 underperformed v1** on production traffic. There is no v3.

- [x] **v1 Training data collection** - 2,847 examples (commerce + journalism)
- [x] **v1 Model training** - DistilBERT, MiniLM, XLM-RoBERTa compared
- [x] **v1 Backtesting** - 56,336 articles, threshold optimization
- [ ] **Re-measure the miss rate before retraining** ← **DO THIS FIRST (added 2026-08-07)**
- [ ] **NM#223 is a live input to this and is blocked** (found 2026-08-07 late) —
      NER entity-density as an *additive* commerce signal, explicitly "does not
      replace the v3 retrain planned in NM#185 Phase 2". It is blocked on
      **NM#232**, not on the closed `FluxusSource#85` its body still names.
      Nothing here should assume entity features will be available.
- [ ] **Redo with proper multilingual embeddings** - Current approach may not handle Dutch/multilingual well
- [ ] **Redo with proper context size** - May need longer context

### The v3 case is tracked in ducroq/NexusMind#185, and its evidence has decayed

Found 2026-08-07 while re-querying the cross-repo chains. NM#185 bundles the
obituary blocker (shipped, enforcing at 0.85 since 07-30) with a **commerce v3
retrain that was never started** — which is why Chain 1 read as complete when it
was half done.

**Before any v3 training run, re-measure.** NM#185's commerce evidence is the
2026-06-25 reader-flag audit, whose headline was that the recoverable miss set
was **100% scored by `sustainability_technology`** — a filter **deleted
2026-08-03** (#64, superseded by `solutions`). The product-launch-in-
sustainability-framing pattern presumably still arrives, but it is now scored by
`solutions v6`, which has a different prompt, a different op-point and an e5
probe in front of it.

**Open hypothesis:** the commerce miss rate under the current five-lens set is
materially lower than the 2026-06-25 audit implies, and v3 may not be warranted
at all. Unmeasured. Deciding it costs one count, not a training run.

See `filters/common/commerce_prefilter/docs/` for full documentation.
<!-- verify: ls filters/common/commerce_prefilter/ | grep -E '^v[0-9]+$' -->
<!-- verify: gh issue view 185 -R ducroq/NexusMind --json state --jq .state -->

---

---

## Filters

### Production Ready
- [x] **uplifting v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.673 (was 0.688 in v5), 12% faster inference
  - Gemma-3-1B base model (was Qwen2.5-1.5B)
  - 10,495 training articles with data sculpting: active learning (495 MEDIUM enrichment) + label correction (57 crime articles capped)
  - v5 crime news issue fixed via manual label correction in training data
- [x] **uplifting v5** - Superseded by v6
  - Val MAE: 0.68, 10,000 training articles
- [x] **sustainability_technology v1** - Deployed on HuggingFace Hub
  - Test MAE: 0.690
- [x] ~~**sustainability_technology v3**~~ — **REMOVED 2026-08-03**, replaced by solutions. Package deleted; recover from git history. Entry kept for the training record below, not as a statement of what is deployed.
  - Val MAE: 0.734 (calibrated test: 0.724), Gemma-3-1B
  - 10,608 training articles (v2 10,039 + 569 active learning enrichment)
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.91)
- [x] **sustainability_technology v2** - Superseded by v3
  - Val MAE: 0.71, 7,990 training samples
- [x] **investment-risk v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.497 (calibrated: 0.465), Gemma-3-1B
  - 10,448 training articles (v5 10,198 + 250 active learning enrichment)
  - Tier simplification: RED/YELLOW/GREEN/BLUE/NOISE -> high/medium_high/medium/low
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.557)
- [x] **investment-risk v5** - Superseded by v6
  - Test MAE: 0.484 (excellent)
  - 10,000 training articles
- [x] **cultural-discovery v5** - Deployed on HuggingFace Hub + gpu-server (private) — 2026-05-31
  - Val MAE: 0.697 (v4 was 0.74), Gemma-3-1B
  - 8,551 training articles, DeepSeek V4 Flash oracle (first non-Gemini lineage)
  - Resolves llm-distillery#62 discovery-lens leakage via F/G/H/I/K soft-penalty flags (historical_harm_reckoning, commemoration, perpetrator_biography, decline, launch)
  - Provisional reference example for ADR-020 methodology (multi-oracle calibration + agent judging)
  - Target: ovr.news Discovery tab
- [x] **cultural-discovery v4** - Superseded by v5; on disk locally + git + HF Hub for rollback if needed
  - Calibrated test MAE: 0.74 (v3 was 0.77), Gemma-3-1B
  - 8,029 training articles (v3 7,827 + 202 active learning enrichment)
  - All 3 inference paths verified (local, Hub, hybrid)
- [x] **cultural-discovery v3** - Superseded by v4

### In Active Development (priority: ovr.news tabs)
- [x] **belonging v1** - Deployed, val MAE 0.49 (calibrated), 7,370 articles. Next: ovr.news tab
- [x] **nature_recovery v2** - Deployed to Hub + gpu-server + sadalsuud (Hub upload actually completed 2026-04-19 after #44; prior commit claimed it without uploading)
  - Val MAE 0.53 (calibrated), probe MAE 0.49, 3,517 articles
  - v1 had zero discrimination (#41); v2 uses sample weighting (scale=2)
  - Recall@20: 0.70 (v1: 0.55), NDCG@10: 0.86 (v1: 0.71), false negatives: 17% (v1: 41%)
  - Hub: `jeergrvgreg/nature-recovery-filter-v2` (private)
  - Remaining: normalization (needs production CDF), ovr.news Recovery tab frontend
- [x] **uplifting v7** - ADR-010 prompt rewrite, deployed with hybrid inference (2026-04-06)
  - v7 prompt: scope check, anti-hallucination, reframed assessment dimensions
  - Hybrid inference: probe MAE 1.10, threshold 1.00, 0.5% FN, 1.07x speedup
  - Evolved into thriving v1: renamed, social_cohesion_impact removed, 3-run averaging planned
- [ ] ~~**thriving v1**~~ - PARKED indefinitely. Uplifting v7 (MAE 0.67) stays as Thriving tab.
  - Root cause: orthogonal lens design created bimodal distribution (ADR-015)
  - A fixed thriving v2 would converge back to uplifting v7. Not worth retraining.
  - Assets preserved in `memory/thriving-v1-scoring.md` if ever revisited
- [x] ~~**foresight v1**~~ — **REMOVED 2026-08-03**, merged into solutions (#43, closing out #64). Was signs_of_wisdom. Package deleted; recover from git history.
  - Val MAE 0.75, 3,480 training articles, 6 dimensions
  - Hybrid inference: probe trained, threshold 2.25 (default, calibrate on production data)
  - Remaining: ovr.news Foresight tab frontend integration

### Active Learning In Progress
- [x] **cultural-discovery v5** - **DEPLOYED** (HF Hub, DeepSeek oracle, MAE 0.70). Stale `[ ]` corrected 2026-08-03 — the entry below describes the training-data prep that has long since shipped. Live follow-ups are #86 (prefilter is dead in production — measured, DO NOT enforce) and #87 (v6 scope: lens-fidelity + op-point re-derivation).
  - Oracle-scored 473 production MEDIUM+ articles with Gemini Flash (active-learning lane, 2026-04-06)
  - Smooth distribution (bell curve centered at WA 4.8), no bimodality
  - 2026-05-29: #62 hard-negatives cohort added — 49 articles labeled with v5 oracle prompt (5 new pre-classification flags F,G,H,I,K)
  - v5 prompt deltas: TRAJECTORY OVER VOCABULARY principle, CAP ENFORCEMENT clamp rule, F carve-out covers wartime restitution (Modigliani fixed), J intentionally omitted (handled by `filters/common/obit_signal.py` per #51)
  - Cohort stats: production v4 mean 8.27 → v5 oracle mean 4.05; 44 hard-negatives + 5 calibration-confirmed positives (tagged `_v5_oracle_reclassified`)
  - Next: train on gpu-server, calibrate, retrain probe, deploy
- [x] **nature_recovery v2** - Trained, calibrated, deployed (2026-04-16)
  - Sample weighting (scale=2) + active learning enrichment (237 articles)
  - Remaining: normalization (needs production CDF), hybrid threshold recalibration

### Other Filters
- [ ] ~~**future-of-education**~~ - DROPPED: education stories land naturally in Breakthroughs (research)
- [ ] **ai-engineering-practice v2** - Ready for oracle scoring (not ovr.news, separate product)
  - FluxusSource hardware sources active (1,193 articles)
  - Prompt calibration complete (~60% tier accuracy)
- [ ] **seece** - Corporate excellence (not ovr.news)
- [ ] **sustainability_economic_viability** - Sustainability sub-dimension (not ovr.news)
- [ ] **sustainability_policy_effectiveness** - Sustainability sub-dimension (not ovr.news)

### Parked Ideas

- [ ] **Measuring "true AI adoption" in SMEs and larger companies** - PARKED 2026-08-11 by Jeroen ("interesting, park it as an idea"). Owner side question. **Answer: not as asked** — our corpus is articles, adoption happens at firms, so it measures adoption *discourse*, not adoption. SMEs are ~99% of firms and ~0% of coverage; 25.7% of the corpus is GN headline stubs; no firm-level ground truth to validate against. **What it WOULD answer well:** of AI-adoption claims in the press, what share are concrete deployments vs announcements — the `solutions v6` shape, whose tech/hybrid tiebreak already makes that discrimination. **The pivot that reaches the literal question: job postings** (firm-level, size-linkable, exists for SMEs; needs a FluxusSource vacancies feed). **Cheap first probe with a kill criterion: base-rate screen of the existing corpus, ~1h, no oracle spend — if AI-adoption content is a fraction of a percent, stop.** Precedent for that kill: `solutions v6`'s `community_practice_strength` is a sourcing problem, not a modelling one. Full note in **`docs/ideas/ai-adoption-measurement.md`**. Re-check #103 (DeepSeek price rise) before any oracle spend.

- [ ] **Re-enchantment outlets (wonder lens / standalone digests)** - PARKED 2026-07-16 by Jeroen ("some other time"). Byung-Chul Han-inspired exploration: wonder/mystery/myth as lens or standalone oracle-only outlet (no distillation needed at digest scale, ~$6.50/wk). Six ideas + four cheap probe plans (<$3 total: Residue query $0 → Wonder probe ~$0.50 → form-scoring feasibility ~$1-2 → Ledger design note $0) with kill criteria in **`docs/ideas/re-enchantment-outlets.md`**. Hard constraint if resumed: "unexplained" needs an `epistemic_honesty` gatekeeper (misinformation magnet otherwise). Below solutions v4 (#43) and the #62 check in priority.

## Training Pipeline

- [x] **Data preparation pipeline** - Stratified splits working
- [x] **Training script** - Gemma-3-1B + LoRA working (was Qwen2.5-1.5B)
- [x] **Context length experiments** - 1024/2048/head+tail tested
  - 1024tok: MAE 0.652, 2048tok: MAE 0.627
  - head+tail (256+256): MAE ~0.69 (deployed to production)
  - See `docs/IDEAS.md` for full results
- [x] **Stage 2 model comparison** - Gemma-3-1B adopted as default Stage 2. Wins on both uplifting (MAE 0.652 vs 0.660) and cultural-discovery (MAE 0.743 vs 0.755). 8% faster, fewer params. Qwen-0.5B rejected (MAE 0.760)
- [x] **Gemma-3-1B training support** - `training/train.py` updated with `load_base_model_for_seq_cls()` for both initial and resume paths
- [x] **Stage 2 model selection** - Gemma-3-1B adopted as default (was Qwen2.5-1.5B). Larger models deferred.
- [ ] **Training monitoring improvements** - Better logging, early stopping

## Score Calibration (ADR-008)

Post-hoc isotonic regression to correct MSE score compression at inference time.

- [x] **Shared calibration library** - `filters/common/score_calibration.py` (fit, apply, save, load)
- [x] **CLI fitting tool** - `scripts/calibration/fit_calibration.py` (works for any filter)
- [x] **Uplifting v6 calibration** - Fitted on 1,049 val articles, val MAE 0.673 -> 0.653 (+3.1%)
- [x] **Cultural-discovery v4 calibration** - Fitted on 803 val articles, test MAE 0.77 -> 0.74 (+4.4%)
- [x] **Base scorer integration** - `_load_calibration()` + `apply_calibration()` in `_process_raw_scores()`
- [x] **sustainability_technology v3 calibration** - Fitted on 1,061 val articles, test MAE 0.725 -> 0.724
- [x] **investment-risk v6 calibration** - Fitted on 1,045 val articles, val MAE 0.497 -> 0.465 (+6.5%)
- [x] **belonging v1 calibration** - Fitted on 738 val articles, val MAE 0.534 -> 0.489 (+8.3%)
- [x] **nature_recovery v1 calibration** - Fitted on 328 val articles, val MAE 0.540 -> 0.507 (+6.2%)
- [x] **nature_recovery v2 calibration** - Fitted on 352 val articles, val MAE 0.632 -> 0.533 (+15.7%)

## Hybrid Inference Pipeline (ADR-006)

Two-stage pipeline: fast embedding probe (Stage 1) + fine-tuned model (Stage 2).

- [x] **Shared infrastructure** - `filters/common/embedding_stage.py`, `hybrid_scorer.py`
- [x] **Uplifting v5 integration** - `inference_hybrid.py` + MLP probe
- [x] **Calibration script** - `evaluation/calibrate_hybrid_threshold.py`
- [x] **Threshold calibration** - Calibrated on 24K production articles. Probe retrained (v2): MAE 0.49, bias +0.007. Threshold 3.5 → 1.7% FN rate on MEDIUM+
- [x] **Speed benchmark** - RTX 4080: e5-small 1.3ms + Qwen 37.9ms. Threshold 4.5 → 2.09x on skewed data, ~2.5-3x in production
- [x] **Stage 2 model evaluation** - Gemma-3-1B adopted as default Stage 2 model. Confirmed on two filters: uplifting v5 (MAE 0.652 vs 0.660, tier 86.6% vs 85.4%) and cultural-discovery v3 (MAE 0.743 vs 0.755, tier 94.6% vs 94.5%). 8% faster inference, 38% faster training
- [x] **Generalize to other filters** - Phase A complete: inference_hybrid.py + probe dirs + calibration fix for sustainability_technology v2, investment-risk v5, cultural-discovery v3
- [x] **Train probes + calibrate thresholds** - Phase B complete: e5-small MLP probes trained and calibrated for all 3 filters
  - sustainability_technology v2: probe MAE 0.707, threshold 1.25, 1.2% FN, 1.25x speedup
  - investment-risk v5: probe MAE 0.497, threshold 1.50, 0.8% FN, 1.07x speedup
  - cultural-discovery v3: probe MAE 0.609, threshold 1.25, 0.0% FN, 1.52x speedup
- [x] **Cultural-discovery v4 probe** - Retrained for Gemma-3-1B, MAE 0.87, threshold 1.25, 3% FN, 1.51x speedup
- [x] **Sustainability_technology v3 probe** - Trained for Gemma-3-1B, MAE 0.91, threshold 1.25 (to be calibrated)
- [x] **Investment-risk v6 probe** - Trained for Gemma-3-1B, MAE 0.557, threshold 1.50
- [x] **Belonging v1 probe** - Trained for Gemma-3-1B, MAE 0.54
- [x] **Nature_recovery v1 probe** - Trained for Gemma-3-1B, MAE 0.50
- [x] **Nature_recovery v2 probe** - Retrained for v2 model, MAE 0.49 (early stop epoch 24)
- [x] **Foresight v1 probe** - Trained for Gemma-3-1B, threshold 2.25
- [x] **Foresight v1 calibration** - Fitted, calibration.json committed with filter package
- [x] **Uplifting v7 probe** - Trained for Gemma-3-1B, MAE 1.10, threshold 1.00 (#34)
- [x] **Harmonize all filters** (2026-04-06) - All 7 production filters now have hybrid inference with calibrated thresholds and `--compare` CLI. Fixed investment-risk import path bug (hyphen vs underscore). Deployed to sadalsuud + gpu-server.

## Code Quality (Feb 2026)

- [x] **FilterBaseScorer extraction** (#10) - Shared base class in `filters/common/filter_base_scorer.py`, all 4 production filters migrated
- [x] **load_lora extraction** (#11) - Shared `load_lora_model()` in `filters/common/model_loading.py`
- [x] **Code quality sweep** (#12-#19) - Resolved 8 issues: removed dead code, cleaned stale comments, fixed inconsistencies (-314 lines)

## Energy-Efficient Inference (#24)

- [x] **PyTorch dynamic quantization experiment** - 2026-03-07
  - Tested FP32/FP16/INT8 on uplifting v6, CPU-only
  - INT8: 2.6x faster, 3.3x smaller, but MAE +0.63 (unusable)
  - FP16: NaN on CPU (no native fp16 ALUs)
  - **Verdict:** Naive quantization rejected
  - See `docs/experiments/quantization-benchmark-2026-03-07.md`
- [ ] **ONNX Runtime INT8** - Calibrated quantization with representative data
- [ ] **Smaller base model retraining** - SmolLM-360M or similar sub-1B models
- [ ] **llama.cpp / GGUF** - Purpose-built CPU inference engine

## Deployment

- [ ] **Inference server** - Unified prefilter + model + postfilter pipeline
- [ ] **Batch processing** - High-volume article scoring
- [ ] **Production monitoring** - Latency, accuracy drift detection

## Infrastructure

- [x] **Prefilter evaluation framework** - Complete for sustainability_technology
- [ ] **Generalize prefilter evaluation** - Apply to all filters
- [ ] **Dataset QA pipeline** - Automated quality checks
- [ ] **Cost tracking** - Monitor API usage for oracle scoring
- [x] **Hub scorers: add torch_dtype parameter** - All 6 `inference_hub.py` files now accept optional `torch_dtype` param and pass it to `from_pretrained()`. Use `torch_dtype=torch.float16` on hardware without bfloat16 support.
- [x] **Deploy all filters to NexusMind** (#7) - All 6 filters deployed to gpu-server + sadalsuud + HuggingFace Hub
- [x] **Auto-compute score_scale_factor** (#22/#26) - Calibration script writes `score_scale_factor` to config.yaml; backfilled to all 6 filters
- [x] **Harmonize filters: llm-distillery as single source of truth** - Fixed drift between llm-distillery and NexusMind
  - base_prefilter.py: threading.Lock() for commerce detector (was bool flag)
  - investment-risk v5: merged source-based + content-pattern approaches, removed academic source blocking
  - Deployed all production prefilters to NexusMind (sadalsuud + gpu-server)
  - Verified 0 diff between all three locations
- [x] **Manifest-aware deploy script (#50)** - 2026-04-28. `.nexusmind-owns` at repo root + `--dry-run` + `--force-skip-owned-drift` in both `.sh` and `.ps1`. Lists `filter_base_scorer.py` and `hybrid_scorer.py` (NexusMind-owned). Deploy now exits non-zero on drift between distillery and NexusMind copies.
- [ ] **Harmonize prefilter structure across all 7 production filters (#52)** - Filed 2026-04-28. Survey shows 5 different override mechanisms, 3 with class/version drift between class name and dir, mixed flat-list vs dict containers. ~12-16h work; per-filter migration in priority order.
  - [x] **ADR-018** (2026-04-28) - Declarative shape decision documented; backwards-compatible BasePreFilter extension chosen
  - [x] **BasePreFilter extension** (2026-04-28) - EXCLUSION_PATTERNS / OVERRIDE_KEYWORDS / POSITIVE_PATTERNS / POSITIVE_THRESHOLD class attrs + default apply_filter() pipeline + _is_excluded / _has_override / _filter_specific_final_check helpers. All 7 production prefilters import + run unchanged (verified)
  - [x] **sustainability_technology v3 migrated** (2026-04-28) - 6/6 self-tests pass; behavior preserved
  - [x] **belonging v1 migrated** (2026-04-29) - 19/19 self-tests pass; behavior preserved. Data shape (EXCLUSION_PATTERNS dict, base-compiled patterns) harmonized; apply_filter stays custom because per-category positive-count thresholds + URL-based domain exclusions + obituary floor rule don't fit the base pipeline (ADR-018 explicitly permits this).
  - [x] **cultural-discovery v4 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Data shape harmonized: EXCLUSION_PATTERNS dict + parallel EXCEPTION_PATTERNS_PER_CATEGORY dict (per-category exceptions don't fit base's single OVERRIDE_KEYWORDS slot). CULTURAL_DISCOVERY_BOOST_PATTERNS renamed to POSITIVE_PATTERNS so base compiles them. classify_content_type() preserved. Surfaced regression vs v3: v4's apply_filter doesn't call check_content_length (preserved as-is in this commit; tracked separately under Prefilter Quality below).
  - [x] **uplifting v7 migrated** (2026-04-29) - 12/12 self-tests pass; behavior preserved. Same EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY pattern as CD v4 for the 3 pattern-with-exception categories (corporate_finance, military_security, crime_violence); 4th category (pure_speculation) is count-based (speculation_count >= 3 AND outcome_count == 0) and stays as separate class attrs with an inline check after the dict iteration. classify_content_type preserved. ThrivingPreFilterV1 (which subclasses UpliftingPreFilterV7) verified working. Surfaced bug: Dutch `munitie` and similar multilingual patterns lack `\b` boundaries — fire on English substrings like "co-MMUNITIE-s" (preserved as-is; tracked under Prefilter Quality).
  - [x] **investment-risk v6 migrated + class drift fix** (2026-04-29) - 11/11 self-tests pass; behavior preserved. v6 now has its own InvestmentRiskPreFilterV6 class (was a re-export of V5). Backward-compat aliases (InvestmentRiskPreFilterV5 = V6, InvestmentRiskPreFilter = V6) + legacy prefilter()/get_stats() functions kept so existing imports don't break. base_scorer.py updated to reference V6 directly. Data-shape harmonization only — apply_filter stays custom because the source-based flow + matched-pattern reason strings + title-only clickbait don't fit the base pipeline.
  - [x] **nature_recovery v2 migrated** (2026-04-29) - 6/6 self-tests pass; behavior preserved. Single text-pattern category (disaster_no_recovery) with one parallel exception list (recovery framing) lives in EXCLUSION_PATTERNS / EXCEPTION_PATTERNS_PER_CATEGORY. Custom apply_filter retained because: (1) nature-relatedness check runs FIRST in the original order — base's final-check hook runs LAST and would change reason precedence; (2) reason strings are bare category names (not "excluded_<category>"); (3) original v2 doesn't call `check_content_length` — same gap as CD v4 (tracked under Prefilter Quality). Class-name drift V1→V2 deferred to the cleanup batch as planned.
  - [x] **foresight v1 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Six block categories in EXCLUSION_PATTERNS dict; six positive-signal categories in custom POSITIVE_PATTERN_GROUPS dict (NOT base's POSITIVE_PATTERNS slot — semantics differ: foresight counts distinct *categories* with at least one match, while base's POSITIVE_THRESHOLD counts total matches). apply_filter stays custom for the distinct-categories-fired override + two pass reasons (`passed_positive_signals` for >=3 categories, `passed` for the no-block fall-through) + URL-based domain exclusions.
  - [x] **All 7 production filters now migrated** (2026-04-29) - sustech v3, belonging v1, cultural-discovery v4, uplifting v7, investment-risk v6 (+ class drift fix), nature_recovery v2, foresight v1. Only the deferred class-name drift cleanup batch remains as #52 work.
  - [ ] **Class-name drift cleanup batch** - sustech V2→V3, nature_recovery V1→V2 still pending. (investment-risk v6 own class — DONE 2026-04-29 as part of its #52 migration.) Deferred until remaining migrations done to avoid cross-repo coordination noise (NexusMind tests/unit/test_prefilter.py imports the V2 name).

## Post-#52 Review-Battery Followups

Items surfaced by the multi-agent code review of the migration commits (2026-04-29). Triaged in TODO.md as committed batches.

- [x] **RIP guard repair** (2026-04-29, commit `dd20749`). Code-reviewer caught that the `(?-i:\bRIP\b)` "fix" from `598fa72` was inert in production — `_get_combined_clean_text` lowercases input before pattern matching, so the inline case-sensitive flag had no uppercase chars left to enforce. Real fix: read the raw title directly and run a case-sensitive `\bRIP\b` against it. Title-only. 20/20 tests.
- [x] **POSITIVE_PATTERNS shadow rename** (2026-04-29, commit `7f22d01`). Refactoring agent flagged that belonging v1 + CD v4 shadowed `BasePreFilter.POSITIVE_PATTERNS` with incompatible semantics — a future maintainer setting `POSITIVE_THRESHOLD > 0` would silently activate wrong base behavior. Renamed to `POSITIVE_SIGNAL_PATTERNS` (belonging) / `DISCOVERY_PATTERNS` (CD) and compiled locally.
- [x] **CD v4 truncation** (2026-04-29, commit `e2595dc`). Security audit flagged CD v4 ran ~60 patterns against unbounded body. Added `[:MAX_PREFILTER_CONTENT]` slice in apply_filter + classify_content_type, matching uplifting v7's pattern.
- [x] **uplifting v7 multilingual `\b` boundary sweep** (2026-04-29, commit `d0916f4`). Far broader than the known `munitie`/communities bug — `viol`/`acquisition`/`fusion`/`auteur`/`association` were all unbounded multilingual alternations causing real false-positives on English content. All `\b` anchors added; locked-in test rewritten to expect correct `pure_speculation` outcome.
- [x] **Investment-risk v6 cleanups** (2026-04-29, commit `24af3f8`). `\bfed\b` keyword tightened (no longer fires on "fed up" / "force-fed"), `get_statistics` alias added for cross-filter naming consistency, reason-string raw-regex contract documented at construction sites.
- [x] **CD v4 colonial exception tightening** (2026-04-29, commit `ffffdf9`). Bare `\bcolonial\b` was too broad — bypassed celebrity_art on "colonial mansion auctioned by billionaire" et al. Dropped; surrounding repatriation/restitution/provenance patterns provide adequate coverage.
- [x] **`_check_domain_exclusions` hoist + `_pre_exclusion_check` hook** (2026-04-29, this commit). 4 identical implementations consolidated into `BasePreFilter._check_domain_exclusions` driven by a per-filter `DOMAIN_EXCLUSIONS` dict. Symmetric `_pre_exclusion_check` hook added to `BasePreFilter.apply_filter` (mirrors `_filter_specific_final_check` — useful for filters with a gate-in check that should short-circuit before exclusions). All 4 filter test suites pass; sustech v3 unaffected.
- [x] **ADR-019 first migration: belonging v1** (2026-05-22, commits `ba6b7cb` + `c1ebc98`). Per-category bypass logic (non-obit `has_exc OR pos >= threshold` rule, obit floor `pos >= 2 OR (has_exc AND pos >= 1)`) lifted out of `apply_filter` into `_compound_override_applies` hook. apply_filter shrank ~65 → ~30 LOC. Custom apply_filter retained for the three ADR-019-flagged reasons (URL-domain-first ordering, bare reason strings, case-sensitive `\bRIP\b` raw-title force-fire). 20/20 self-tests green; multi-agent review battery (code-reviewer + refactoring-guide + security-auditor in parallel) returned PASS with three inlinable findings (threshold>0 guard, assert on unhandled category, base docstring drift), all applied in `c1ebc98`.
- [ ] **Extend `_is_excluded` for per-category exceptions + migrate CD v4 / uplifting v7 to base pipeline** - Path narrowed by the belonging migration above: the architecturally-correct next move is the two-step path filed as **#66** (base `EXCLUSION_REASON_PREFIX` class attr + move domain checks into `_pre_exclusion_check`), which unblocks fully-declarative migration for belonging v1, CD v4, uplifting v7, foresight v1, and NR v2 simultaneously. ADR-019's hook signature widening (raw-article access) deferred until a second filter shows up needing case-sensitive raw fields. Original open questions still apply: (a) reason-string convention — covered by the prefix attr in #66; (b) CD v4 missing `validate_article` + `check_content_length` — base would add both, fixing the regression but changing observable behavior; (c) uplifting v7's count-based `pure_speculation` block doesn't fit the dict shape regardless.
- [ ] **Migrate nature_recovery v2 to fully-declarative shape via `_pre_exclusion_check`** - Bundle with #66 (the reason-prefix attr is the prerequisite). NR v2 has the same shape concerns as the post-#52 cluster: bare reason strings, missing `check_content_length`, and order-of-checks differences from the base pipeline.

## Prefilter Quality (Apr 2026)

- [x] **belonging v1 obituary leak (#45)** - 2026-04-28. 5 bypass classes patched (dies-with-verb, procession, vigil, RIP/rest in peace, killed-in-year), `dies at \d` → `\d+` bug fix, override floor on obit branch. Plus `(?-i:\bRIP\b)` follow-up after the case-insensitive false positive on "rip current".
- [x] **sustainability_technology v3 clickbait leak (#46)** - 2026-04-28. CLICKBAIT category added with 6 patterns (you-won't-believe, without-knowing, this-common, you're-probably, X-things-you-didn't, shocking-fact). Pattern 5 bounded `.{0,120}` after review caught cross-sentence FP risk.
- [x] **cultural-discovery v4/v5 missing content_length check** — CLOSED 2026-08-03 by #93, in the opposite direction from the one planned. No `apply_filter` calls `check_content_length` any more; the floor is enforced once, in the oracle path, for every filter. cd was the only filter whose *labelling* path had no floor, so #93 restores one there: measured on a short-skewed stress corpus (`data/raw`, 66% sub-300) that withholds ~40% of what cd would have sent to the oracle. The production-realistic share is lower and unmeasured — **re-measure before the next cd oracle run** (#87).
- [x] **nature_recovery v2 missing content_length check** — MOOT 2026-08-03 (#93). Not a gap any more: no prefilter checks length.
- [x] **uplifting v7 multilingual `\b` boundary leak** - FIXED 2026-04-29. Sweep of NL/DE/FR multilingual alternations added `\b` boundaries to every category in EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY. Big offenders cleaned up: `munitie` no longer fires inside "communities", `viol` no longer matches inside "violence"/"violation"/"viola"/"violin" (was a major crime_violence FP vector on English content), `fusion`/`acquisition` (false corporate_finance), `auteur` (false on "auteur theory"), `association` exception (over-broad bypass). Locked-in test case for "New Technology Could Transform Energy Production" rewritten — now correctly hits `pure_speculation` instead of bug-induced `military_security`. 12/12 tests pass; ThrivingPreFilterV1 subclass verified.
- [x] **Universal obituary detector (#51/#83)** — DONE through enforcement 2026-07-30 session 3: v5 trained (21 FN-delta hard positives), 3-reviewer battery corrected the eval (fair table excl-24; June-increment panel 0.71–0.83, threshold-insensitive), owner adjudicated 14 boundary rows (grief-vs-news rule, flips both sharpened-broad clauses), owner went recall-first ("I just hate obits coming through") → **ENFORCEMENT ON: v5 @ 0.85** (NexusMind `b904edc`, `obituary_blocked` in dedup gate, config-gated rollback via `pipeline.obituary_detector.enforce`). **Enforcement VERIFIED 2026-07-30 20:12 + overnight sanity check PASSED 2026-07-31** (1158→1208→1249 blocked, all-v5 stamps, zero post-enforcement obit leaks in 133 collected). ovr#204 handled ovr-side (editorial gate retired 2026-07-30; sentinel re-derivation ~5% after Aug 6; downstream death-rate 7.9%→2.9% past the boundary). Site carryover (47 flagged shadow-era articles + 2 v5 FNs) washes out by ~Aug 13 — owner accepted, no purge.
- [ ] **Obituary v6 (#85) — PARKED indefinitely (owner, 2026-07-30)**: v5@0.85 enforcement meets the recall-first requirement. Reactivate only if an obit reaches the site (owner flag) or over-blocking visibly hurts the feed. Plan preserved on the issue; b650 env + adjudicated golden set (14 rows) stay ready. **2026-07-31 FN evidence banked for reactivation** (memory/obituary-v4-hypotheses.md addendum 7 + #85 comment): community-mourning class regresses monotonically v3 0.68 → v4 0.44 → v5 0.12 (hard-negative interference); biography-rich obits are a stable all-version blind spot (~0.2–0.3, threshold can't reach).
- [x] **Violence promotion prefilter (#73)** — v1 shadow-deployed NM#274 (2026-07-28). Frozen mpnet-base-v2 + MLP(256,128), 1,957 training samples. OOF precision 0.936, recall 0.550 @0.95. Stamp-only per ADR-004. Next: shadow accumulation → panel validate → v2 retrain with more data (recall is low at 0.55).

## Cross-Filter Normalization (ADR-014)

- [x] **uplifting v6 normalization** - Fitted on production CDF
- [x] **belonging v1 normalization** - Fitted on production CDF
- [x] **cultural-discovery v4 normalization** - Fitted on production CDF
- [x] **sustainability_technology v3 normalization** - Fitted on production CDF
- [x] **uplifting v7 normalization** - Fitted on 73,986 production articles (2026-04-06)
- [x] **foresight v1 normalization** - Fitted on 623 articles (thin LUT, improves as data accumulates)
- [x] **nature_recovery v1 normalization** - Refitted on 76,500 articles (still clamped — extreme needle filter, #32)
- [x] **nature_recovery v2 normalization** - Fitted on 1,397 v2 production articles (filter_version=2.0, weighted_average >= 1.5), deployed to sadalsuud + gpu-server (2026-04-28). Patched `fit_normalization.py` with `--filter-version` to exclude v1 leftovers (19,948 articles correctly skipped). Curve: raw range 1.50–7.08, p95=4.49.
  - [x] **Follow-up VERIFIED 2026-05-04**: sustainability_technology JSONL on sadalsuud (1142 articles, 19:22 UTC pipeline run) shows `weighted_average=1.81`, `raw_weighted_average=4.42`, `normalization_method="percentile"` — both audit fields populated end-to-end for the first time since 2026-04-16. The verification revealed that the runtime application code itself had been silently deleted from NexusMind and gone unnoticed for 18 days; fix landed via Path B extraction into `NexusMind/src/scoring/production_scorer.py` wrapper class (NexusMind merge `0e80d92`). All 7 filters now populate the audit fields. See `memory/gotcha-log.md` "Manifest as Anti-Pattern" entry for full diagnosis.

## Documentation

- [ ] **Update filters/README.md** - Current status is outdated (Nov 2025)
- [ ] **Training guide** - Step-by-step for new filters
- [ ] **Deployment guide** - Production setup instructions
- [x] **HF Hub model card relicensing** (2026-05-22, commits `fb67d05` + `41d2108`, #65 closed). Source-side: `upload_to_huggingface.py:28` now declares `license: eupl-1.2` in the model-card YAML frontmatter. Hub-side: one-shot script `scripts/deployment/relicense_hub_repos.py` walked all 14 `jeergrvgreg/*` repos and rewrote the frontmatter `license:` line; verified post-upload on 3 repos (public uplifting-filter-v5, private belonging-filter-v1, private sustainability-technology-v3). Repo LICENSE + pyproject + upload template + 14 Hub model cards now all carry EUPL-1.2 consistently.
- [x] **deploy_to_nexusmind hardening: refuse-on-dirty + explicit staging** (2026-05-23, commits `4cf75dd` + `dd11727`). Fix for the origin-contamination hazard discovered during the 2026-05-22 belonging deploy: `git add -A` on NexusMind's working tree swept ~1,400 lines of unrelated story-dedup WIP into commit `7a595c4` and pushed it to origin without the author's review. Both `.sh` and `.ps1` now do (a) pre-flight `git status --porcelain` refuse-on-dirty check with `--force-dirty`/`-ForceDirty` escape hatch, and (b) explicit `git add $FILTER_PATH filters/common/` instead of blanket add. Printed server-pull instructions also corrected (sadalsuud at `~/local_dev/NexusMind`, gpu-server deploy via `bash scripts/deploy_filters.sh` from sadalsuud — not `git pull` on a stale `llm-distiller` hostname). Cross-referenced with NexusMind-side gotcha-log entry and `b12d554` documentation commit.

---

*Last updated: 2026-08-01*
## 2026-08-06 evening — four owner decisions taken, three backlogs closed

Session was decision-bound, not work-bound: three calls were blocking #87, #93 step 4
and #98, and a fourth (naming) had been re-scheduled through four version bumps.

- [x] **#95 step 2 — noise becomes a band.** See the corrected entry below; "pin a batch size" was not an option.
- [x] **#98 criterion 4 + package parity.** cd v6 can now score. Two prerequisites remain and neither is doable from a laptop — see "Next session".
- [x] **#94 — static invariant shipped.** `tests/unit/test_gatekeeper_invariant.py`: any filter declaring a gatekeeper must have `GATEKEEPER_CAP` **below** its medium tier threshold, or it cannot change visibility (the only outcome a filter has under ADR-016/ADR-022). Reads both values off the **scorer class**, never config. Catches cd v5 (cap 4.0 == 4.0) and solutions v6 (cap 3.0 > 2.25); both are EXEMPTIONS entries that must keep matching a real violation. cd v6 drops its gatekeeper entirely, so that exemption dies when cd v6 goes live.
- [x] **#97 assessed and remedied.** See the corrected CARVE-OUT 1 entry below.
- [x] **#88 items 2-4.** nature_recovery v4's `3.225` marked documentation-only (runtime `DEFAULT_THRESHOLD = 0.75`); its raw `high` tier 7.0 documented as structurally dead (calibrated ceiling 6.8) but KEPT, since ADR-022 reassigns tier on the normalized score where the band is reachable; investment_risk v6 tiers aligned to runtime (`medium` 3.0 → 4.0, declared `medium_high` 5.0 removed — the runtime has three tiers). **Item 1 (`stage_used` into row attributes) is NexusMind-side** and shares a root cause with ducroq/NexusMind#300.
- [x] **#84 v7 corrections written** next to the v6 prompt, not into it (`prompt_hash` is stamped into every scored result). The router points at a disposition that does not exist: "does NOT pass Step 1 → route to Flag A", but Step-3 flags apply only to articles that *passed* Step 1. Fix is a distinct **A2 `action_without_outcomes`** flag whose carve-out requires measured outcomes rather than committed resources.
- [x] **#99 closed by removal** — `DISCOVERY_PATTERNS` went with the keyword gate.
- [x] **ADR-012 rename backlog CLOSED.** Two cancelled, one confirmed, one named and scheduled. The ADR needed a third clause: its obvious reading is "rename to the lens name, or don't", a binary with no room for `{qualifier}_{lens}` — which is what left `uplifting` unresolved for five months.
- [ ] **NOT done, and deliberately: #87.** Unblocked now (it was waiting on #95) but not folded into #98 — that issue was scoped *probe first, dimensions later*, and merging them makes any change in the numbers unattributable.

**Self-review caught one of my own errors:** the ADR-012 amendment first said "five scheduled renames, one carried out". It is **four** — `belonging` "already matches" is not a rename and wisdom/education were never built. Corrected in the ADR before commit.


## 2026-08-06 — cd v6 probe (#98), the English escape hatch (#99), and an instrument for FS#120

- [x] **#98 probe trained and measured; all three acceptance criteria pass.** `filters/cultural_discovery/v6/`. Held-out oracle labels (test split, 75 MEDIUM+ positives): probe @ 2.50 FN **0/75**, keyword gate **10/75**. Production, 64 cycles / 156,226 rows / 2,653 surfacing, both arms in one pass over identical rows: surfacing blocked **337 (12.7%) → 1 (0.04%)**, high-tier **0 → 0**, every language except Portuguese at 0.0%. Full write-up in that directory's `STATUS.md`.
- [x] **Threshold is 2.50, not `train_probe.py`'s 3.025.** The trainer selects off the **val** recall curve, so val FN is optimistic by construction — it reported 1.3% where held-out gives 6.7%. Val and test independently both give FN 0.000 at ≤ 2.50 (0/152 positives).
- [x] **Two self-corrections, both recorded in the package rather than only in chat.** (a) Criterion 2 is a **regression** — on production the probe screens 63.7% against the gate's 70.2%; an earlier claim of parity came from the test split, which does not transfer (label set is 9% MEDIUM+ against a 1.7% production surfacing rate). (b) **Four of the five held-out positives** recovered by the lower threshold read as **off-lens** on inspection, so the FN gain is partly #87's lens dilution appearing inside the labels. 2.50 rests on recall being Stage 1's job, not on those five being losses.
- [x] **The probe is batch-invariant** — max |Δ| **3×10⁻⁶** across shuffled order, chunk 256→97, encode batch 64→1; zero threshold flips. Unlike student scores (#95, |Δ| ≤ 0.162), a probe decision is reproducible. `scripts/gate/probe_batch_invariance.py`.
- [x] **#98 criterion 4 EXECUTED 2026-08-06 evening** (owner call). Keyword gate, four exclusion categories and three domain blocklists deleted; `prefilter.py` 800 → ~90 lines, commerce-only pass-through on the ADR-018/019 declarative shape. `classify_content_type` deleted too — grepped first, only callers were each cd version's own self-test. **Package parity also reached**: three inference modules added, `calibration.json` copied from v5 (correct — the student is unchanged), `score_scale_factor` corrected **1.2829 → 1.0**, `normalization.json` still deliberately absent. `verify_filter_package.py` 7/7 offline.
- [x] **#99 filed** — `DISCOVERY_PATTERNS` is an English-only escape hatch: 66/516 English surfacing articles pass the cultural gate on lens-neutral science-journalism words, 0/265 non-English, all 66 read and none cultural. Also feeds `classify_content_type`, which a probe does **not** replace.
- [x] **FS#120 (~08-14) answered; the measurement is ours.** `pre_enrich` fires at **500**, not 300 (`config/app.yaml:171`). Their proposed denominator confounds enrichment success with native article length — supplied a third, conditional instrument. Blocking them back: `eval_query` is stamped on **28 of 547** eval rows, so their "drop Chad, keep Tchad" cut is unexecutable; and three of eight arms project to n≈13–35 by the 14th.
- [x] **ducroq/NexusMind#300 filed** — the #93 `content_length` stamp is computed by the scorer and lost before persistence: **0 of 50,605** rows carry it, though the deployed code is md5-identical to the repo. ADR-022's stamp half is not holding. Does **not** block FS#120.
- [x] **Four SSH-dependent verify assertions re-run** after slipping three curate passes; all PASS. Obituary blocked count 1208 → 2573 with no gap; rescore reproduces 07-31 to four decimals.
- [ ] **sadalsuud carries the pre-`80dd399` cd gate** (235 topic stems vs 453). Zero production effect — that prefilter does not run (NexusMind#284) — but flipping enforcement without syncing restores the exact skew #86 removed. Recorded on #86 as a trap; **do not close it by syncing**, since #98 deletes the file.

## 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open

- [x] **#28 decided — AI-crawler opt-out directives do not bar distillation training.** Record: `docs/decisions/2026-08-05-tdm-opt-out-training-data.md`. Grounds, strongest first: the directives name **other parties' crawlers** (of 333 flagged domains: GPTBot on 286, CCBot 270, Bytespider 235, ClaudeBot 231, Google-Extended 230 — we operate none; **corrected 2026-08-06, the first figures counted matching lines, not domains, and GPTBot's 401 exceeded the 333 total**); the student has a **regression head and cannot emit text at all**, so no output can substitute for a publisher's work; and the use is referral, not substitution. Sibling decision for the fetching layer is ovr.news ADR-043. **Recorded against itself:** *"modelling is not mining"* is not a distinction the DSM Directive draws — its TDM definition covers fitting a model to text. The position rests on the **Art. 4(3) reservation** question and on harm, not on being outside the definition; do not carry the shorter phrasing forward.
- [x] **#28's numbers were stale** — it cited 238/971 domains from March; the 2026-08-04 scan says **333/1,357**. Also **117 domains failed open** (unreachable, counted as clean) — a publisher behind a WAF that 403s non-browser agents scores clean, and that is exactly the publisher most likely to be reserving. Any future "we checked" is only as strong as those 117.
- [x] **CARVE-OUT 1 ASSESSED 2026-08-06 (#97).** Models clean: **zero of the 333 opted-out domains carry a `User-agent: *` reservation** — every signal names a third-party crawler we do not operate — so grounds 1-3 cover the already-trained filters with nothing left over. Overlap is real but irrelevant to that conclusion (solutions v6 29.5% of training rows, nature_recovery v4 14.6%). **Q2 did NOT come back clean**: the Hub is fine and splits are gitignored, but 812 committed JSONL rows carried full article bodies in a PUBLIC repo. That is republication, not mining — grounds 2-3 are silent on it. **Remedied the same day** (owner: truncate in place): 45 files, 834 rows, **1,889,627 chars removed**, capped at 300. Does NOT unpublish — the text remains in public git history; history was not rewritten.
- [x] **CARVE-OUT 2 — the oracle ships full article text to third parties.** Gemini Flash (Google) and DeepSeek receive complete article content under their own terms. None of the three grounds cover it, and ground 2 specifically fails because **the recipient is a generative model**. **Owner decision 2026-08-05: risk identified and knowingly accepted** — *"this is the only way I can do this, so if someone objects in future, let's see then."* Recorded with revisit triggers in `ovr.news/docs/compliance-register.md` §3 (it lives there because the summarisation path makes the same transfer; this repo is one of two callers).
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

## 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned

Both P0 issues carried into this session had the **mechanism right and the target wrong**. Neither correction needed new tooling — one came from widening a sample, the other from reconciling a denominator.

- [x] **NM#285 measured, resolved as Option B** (`89f2e5b`, NexusMind main). Same-row full-vs-truncated replay, 4 cycles, n=8,283. Truncation effect: nature_recovery **+0.0000**, solutions **+0.0000**, cultural_discovery +0.0005, belonging +0.0008, uplifting +0.0028, investment_risk +0.0097. **The 0.638–0.649 cluster is NOT a truncation artifact.** Option C declined — its cost saving came almost entirely from the length floor, the one rule we now have evidence against enforcing; Option A buys a rounding error. Shipped instead: every shadow line carries `contract=title+content`, `pre_source_filter=true`, and `INCOMPLETE(inert:url,source)` derived from declared rule containers (not a hardcoded list), verified to flag exactly the four filters with a non-zero measured effect.
- [x] **Real cause of the cluster found.** `nature_recovery v4` and `solutions v6` prefilters are **pure length floors** — both declare `EXCLUSION_PATTERNS = {}` by design (commerce upstream, ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides, a no-op with nothing to override. Zero lens blocks across 8,283 articles. `expected_pass_rate` **deleted** from both (`3ed47e1`), not corrected — 0.644 is "fraction of articles ≥300 chars", a corpus statistic, not a lens spec.
- [x] **Larger, opposite-signed defect found underneath**: the shadow denominator counts articles `source_filter` discards *after* scoring. investment_risk logs 0.642 while the rate on articles that can reach production is **0.770** — 13× the truncation effect, other direction.
- [x] **LD#92 — IDENTIFIED 2026-08-05, supersedes the n=60 caveat below.** The two discriminating tests the 08-02 review demanded were run, predictions pre-registered in the sampler before any oracle call. **D3 (matched percentile depth, where the selection artifact is largely removed) is the LARGEST effect, not the collapse toward zero the artifact predicted** — see the cap entry below for the numbers. Second oracle confirms. Two bookkeeping defects in the first write-up were caught by the newly-adopted `/review-changes` skill and corrected: the p-values were article-level permutation (anticonservative under source clustering) and the verify command's data was never committed. Both fixed; fixtures now in `tests/fixtures/ld92/`.
- [x] **NM#286 items 1+2 shipped together** (`23a9068`, NexusMind main): `pipeline.commerce_prefilter.enforce` (default **true** — unlike obituary's false, so a config predating the key cannot silently open a live gate), and `enrich_survivors.py` now reads the same key instead of re-deciding. 920 tests green.
- [x] **LD#86 answered — DO NOT FLIP.** cd's rate matches its declared 0.25, but enforcing it costs **15.5% of surfacing articles** (135/871 over 20 cycles), 0% of high tier. **A matching pass rate and safety-to-enforce are independent properties.** The "skewed non-English" framing is **corrected**: German 4.9% / French 5.3% are blocked *below* English's 13.0%, so pooling was wrong. The entire gap is one rule — `no_cultural_topic_signal`, 9.9% en vs 19.2% non-en, while the other three fire *more* on English. It is uneven `TOPIC_GATE_PATTERNS` keyword coverage, which is fixable and falsifiable.
- [x] **Chain 4 root — length floor split out of the per-filter prefilters (#93)** — LD side shipped 2026-08-03. `apply_filter()` no longer gates on length in any filter; the floor moved to `make_oracle_prefilter` (labelling-time, where the framework-leakage rationale lives); every scoring result carries a `content_length` stamp; one config-gated `short_content.cap` exists and is **off everywhere**. A/B over 2,917 production rows: the oracle verdict is **byte-identical** for five of six filters (cd is the intended exception, above). **Still open:** sync `filters/common/` + the six prefilters to NexusMind, then re-run the NM#284 shadow — its pass rates will jump, and for the first time they will describe lens behaviour rather than a length floor (what LD#90 item 2 needs).
- [ ] **Fit the solutions short-content cap** (#93 step 4) — **#92 no longer blocks it; #95 still does.** The second-op-point re-run ran 2026-08-05 and the defect is **identified**: D1 (both arms ≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster-bootstrap p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The selection artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and D3 is the *largest*. A gemini-2.5-flash cross-check on the same D3 sample gives **−1.351** [−1.73,−0.96] — two oracles with clearly different absolute bias, same gap, which rules out "the judge penalises short input". Harness + fixtures committed (`scripts/diagnostics/ld92_*.py`, `tests/fixtures/ld92/`). **Remaining blocker is Batch F.1 (#95)**: the cap value is a threshold fit and inherits the |Δ| ≤ 0.16 batch-composition noise floor. Also weigh the recall cost against NM#231/#292 before setting a value — `gn_africa_*` / `gn_asia_*` feeds lead solutions' short-and-clearing list.
- [ ] **Reader-reported defects 2026-08-03, filed upstream — all three land outside this repo.** A single reader complaint about ovr.news decomposed into three defects in three different repos, which is the clearest instance yet of "the repo where a symptom appears is not the repo that owns the fix":
  - **FluxusSource#124** — feed titles/content stored with UTF-8→MacRoman mojibake (`años` → `a√±os`). **5.0% of articles** (463/9,343 in one day), concentrated in `baltic_lrt` / `spanish_*` / `vietnamese_*` / `german_*`; English essentially unaffected, which is why English spot-checks never saw it. Present in FluxusSource's own collection file before NexusMind reads it. **Relevant here:** it degrades multilingual embeddings, so it touches any cross-language work this repo does.
  - **NexusMind#290** — hero extraction publishes third-party page chrome (a Google Play badge) as the article image; reproduces on current code *with* NM#287 in place. No cross-domain check exists. Compounded by `hero_validation_cap: 200` against ~968 heroes/run, so ~79% are never validated and visibility of the defect is a lottery.
  - **NexusMind#291** — cross-source dedup threshold 0.88 sits above where genuine same-story pairs land (**measured 0.8355** on a confirmed RU/ES pair, `multilingual-e5-large`, title-only). Method note: the mojibake was my first hypothesis for this and was **measured and refuted** — repairing the encoding buys +0.013, nowhere near the gap.
- [x] **#95 step 2 SETTLED 2026-08-06 — and "pin `batch_size`" was never an available option.** `DEFAULT_BATCH_SIZE = 16` (`filters/common/filter_base_scorer.py:50`) is already fixed and never varies in production; the variable is batch *composition*, which the seeded shuffle already addressed. Owner decision: **budget for the floor, do not try to remove it.** An article predicted within **0.16** of the surfacing threshold is *indeterminate*; every metric at that threshold carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE**. `scripts/gate/ground_truth_gate.py` computes and prints it (`--noise-floor`, default 0.16; `0` reproduces prior runs). Worked example — solutions v6 on its own held-out test set, 19/1,032 indeterminate: **F1 0.739 [0.712, 0.771]**, recall 0.671 [0.659, 0.707]. **This unblocks #87 and #93 step 4**, which only needed a stated rule for what counts as a difference. NOT attempted, still open: whether fixed-length padding would make scores batch-invariant.

- [ ] **Price the upstream fix before the downstream one (NEW 2026-08-05).** Google News is 14–17% of scored articles but **48–56% of all sub-300-char stubs** (~3× over-represented, measured within-period over 149,075 solutions v6 rows / 80 cycles). Pre-enrichment already rescues ~62% and fires below **500** chars — the net is not too small; GN survives because its `url` is a `news.google.com/rss/articles/…` redirect, so the fetcher retrieves Google's redirect page. **Retiring the GN proxies removes roughly half the population the solutions cap exists to handle, at no recall cost to genuine articles.** That decision is FluxusSource#120, due **~2026-08-14** — the only calendar-bound item on the board. Evidence and a suggested `enrichable rate` readout column posted there. Sequence: FS#120 → then size the cap against what remains.

- [ ] **Does the scorer share the summariser's fixed-budget failure? (NEW, ovr#299)** For English sources, summary content words absent from the article *and* title run 31.6% (1000+ chars) → 73.9% (120–299) → **83.4% (<120)**, monotone over 18,756 summaries. The mechanism there is a fixed output length target (medians 1159/968/875/1065 against a 40× input range) that the model fills — compressing an article, generating from a headline. **Open for this repo: whether the student has an analogous behaviour, or whether its short-content error is purely vocabulary-without-subject.** The fixes differ — one is a budget, the other a cap — so this is worth one experiment before building either.
- [x] **#93 synced to NexusMind** 2026-08-03 (`c932065` content, `c1df13c` record; 950 NM tests pass). Surfaced and fixed a second drift — `investment_risk v6` blocked `arxiv`/`mastodon_`/`bluesky` in NexusMind since 2026-05-18 and never upstream (`e51309d` ports them back). **Diff both copies before every sync**; `.nexusmind-owns` is empty so nothing else compares them.
- [ ] **`foresight v1` still floors on length** — the one prefilter left calling `check_content_length` inside `apply_filter` after #93. Deliberately out of scope (PARKED, merged into solutions #43, not in the production set), but fix it at the same time as any un-parking so it does not silently re-inherit the shape #93 removed.
- [ ] **Re-run the NM#284 shadow** now that the length floor is out of the prefilters *(deployed to gpu-server 2026-08-03 ~15:45 CEST, rev `2d5c54aa…`; first cycle carrying it is 16:10)* — its pass rates finally describe lens behaviour, which is what LD#90 item 2 needs. Rates measured before 2026-08-03 are not comparable to ones measured after.
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
- [ ] **Fix `no_cultural_topic_signal` multilingual coverage**, then re-run the identical LD#86 recall check — falsifies whether the language skew is the gate or the corpus.
- [x] **Retitle/relocate LD#92 to solutions** and correct the op-point in its body — done; the issue now reads "solutions v6 over-scores sub-300-char stubs (DiD −1.13) — NOT uplifting; original n=15 result did not replicate".

## 2026-08-01 — NM#281 gate contract + adversarial review of the day's own work

- [x] **NM#281 gate-contract harmonization** — shipped `0fd462b`, **corrected `b85a467`**, deployed. `_commerce_model` / `_violence_model` stamps; `pipeline.violence_promotion.enforce` (default false); `violence_blocked` accounting. Ships inert.
- [x] **Five-lens adversarial battery over the same day's changes** — found 2 blockers, both mine, both invisible to the tests shipped with them:
  1. **The violence gate could never fire.** Placed in `_is_duplicate`, which runs *before* violence stamping; `enforce: true` would have dropped 0 while logging `0 violence`. Commerce/obituary work there only because their preprocessors rewrite the input JSONL first. Fixed: drop moved to `_enforce_violence_promotion()` right after stamping; dead check removed; ordering asserted structurally (AST).
  2. **The shadow loader armed a dead branch.** Leaving `target.prefilter` populated makes `HybridScorer`'s third guard clause truthy — constructing the wrapper flipped a `use_prefilter=True` hybrid to blocking with null scores. Now restored to `None` after capture.
  Also fixed: the `MODEL_VERSION` getattr default was itself the v1-claiming bug the stamp prevents (→ `"unknown"`); shadow errors were dead code so a broken shadow logged nothing; digit-collapsing fragmented the histogram it existed to unify. **978 tests green** (was 969).
- [x] **NM#285 — RESOLVED 2026-08-02.** Measured: truncation is +0.0000 to +0.0097, so the cluster was never an artifact and the ~0.59 reading below was wrong. Option C **declined** on the measurement (see the 2026-08-02 section). Option B shipped `89f2e5b`.
- [x] **NM#286 — items 1+2 shipped 2026-08-02** (`23a9068`); item 3 still open and still blocks any violence enforce flip.

## 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected

- [x] **ovr#280 "upstream never sends cluster_id" — REFUTED 2026-08-01.** Measured on the live 12:4x cycle: **7,629 / 16,128 rows (~47%)** carry `nexus_mind_attributes.<lens>.source_quality.cluster_id`, with `corroborating_sources` + `other_sources` on exactly the same rows; present in the 2026-07-22 files too. The diagnosis had sampled `metadata.quality` (FluxusSource's block — its key list `bias_category, credibility_score, source_tier, type_classification` is quoted verbatim in the issue) instead of the per-lens NexusMind block one level deeper. **No NexusMind change needed**; ovr#280's Option A is already done, and the break is downstream between the JSONL and their DB. Posted to ovr#280.
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

## 2026-08-01 — Post-deploy verification + NM#284 (prefilters never ran in production)

Verification of the 2026-07-31 deploys: **refits and the NM#280 tier gate both green** (closed NM#279, NM#280, LD#74, LD#76). The third check — LD#86's cultural_discovery topic gate — was red, and the cause turned out to be architectural rather than cd-specific: **per-filter prefilters have never run in the production scoring path** since 2026-02-10. See the NM#284 items below and `memory/calibration-history.md` Dead Ends (two new entries).

## 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)

Full synthesis: LD#76 issuecomment-5140079896. Headline: **no shared root cause, no scale-collapse anywhere, no retrains needed**. `% norm < 0.5` retired as health metric (≈ 1−base-rate by construction; healthy investment_risk is itself 75% "invisible" by it). Healthy criteria going forward (from ir reference): raw p90 above op-point + populated spread-out MEDIUM+ band + separation intact + anchored fresh fit.

- [x] **uplifting v7 normalization refit** (NM#279) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: raw 5.00 → norm ≈5.18 (was ~3.0), `percentile` on 2647/2647 rows. NM#279 closed.
- [x] **belonging v1 normalization refit** (NM#279 / #74) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: MEDIUM+ p90 norm 8.71 (n=205 over 3 cycles), visible share 1.03% → 2.68%. NM#279 + #74 closed.
- [x] **NexusMind `_assign_tier` double-cut (NM#280)** — **DEPLOYED 2026-07-31, VERIFIED LIVE 2026-08-01**: `count(tier != low) == count(raw >= op-point)` holds exactly for all six live filters across six consecutive cycles (live from the 07-31 12:5x cycle). Restored visibility: uplifting +196%, ir +70%, belonging +82%, cd +67%, solutions +33%, nr +33%. Caps path untested in production (0 caps applied in these cycles). NM#280 closed.
- [ ] **cd v5 dead prefilter (#86)** — the gate is **correct and now production-validated, but still not enforced**. Verified 2026-08-01 by NM#284 **in-path** shadow measurement on the 12:46 cycle: **0.255 observed vs 0.25 declared (n=2099, full cycle)**, matching the fix's own offline validation (0.245 on 14,923 rows). *(An earlier claim here — "production stamps 2647/2647 pass, replay gives 28.8%" — was retracted: that baseline came from `filtered_*.jsonl`, which only receives `passed_prefilter: true` rows, so it is 100% passers by construction. See NM#284 issuecomment-5151154862.)* **Root cause is not cd-specific: the per-lens rule prefilter has never run in production** (NexusMind `deploy/gpu-server/main.py` L915 `use_prefilter=False` + L1318 `skip_prefilter=True`, since `66582e7`, 2026-02-10). e5 probe, commerce/obituary/violence, and the NM#189 source allowlist all verified running. Filed **NM#284**. #86 closes when NM#284 stage 3 flips cd to enforcement — the fix itself needs no further work.
- [x] **NM#284 stage 1 — shadow measurement** — **IMPLEMENTED + DEPLOYED + VERIFIED LIVE 2026-08-01** (`cd4fc6d` + `5d53774`, deployed ~11:59 CEST). `ProductionScorer` loads each filter's prefilter via the `_load_prefilter` hook (without flipping `use_prefilter`, keeping evaluation and enforcement separate levers) and logs observed vs declared pass rate. Enforces nothing; no schema change. Rollback `NM_FILTER_PREFILTER_SHADOW=0`. First cycle (12:46): **cd 0.255 vs declared 0.25 — LD#86 gate validated in production**; uplifting 0.525 vs 0.20; solutions 0.591 vs 0.20; ir 0.589 (no declared rate). Two defects the first live run exposed and fixed: drift judged at n=1 (smoke test scores one article/filter → six false "gate appears inert" alarms; now `MIN_SHADOW_SAMPLE=50`), and `expected_pass_rate: ~0.25` parsed as a YAML *string* and silently dropped.
- [ ] **NM#284 stage 1b — per-row shadow stamps into the JSONL**: needs `prefilter_shadow_pass` / `prefilter_shadow_reason` plumbed through gpu-server `main.py` (Pydantic `FilterScoreResult` drops unknown keys at the service boundary) → `src/scoring/gpu_client.py` → the `analysis` dict in `scripts/main.py`. Blocked on unrelated uncommitted WIP in `scripts/main.py` (image-classifier thresholds, NM#282) — staging it would sweep that in. Log-based measurement is sufficient for the enforcement decision, so this is a convenience, not a blocker.
- [x] **NM#284 stage 2 — global short-content gate before fan-out — REFUTED, DO NOT BUILD** (2026-08-02, superseded by #93 2026-08-03). The ~25%-of-inferences saving was real but it is bought by dropping content the oracle validates at the same rate as long content (uplifting: 67% short vs 65% long above the op-point), and the loss skews to the `gn_*` / `spanish_*` / `french_*` population NM#231 already flags as under-served. The floor is now a labelling-time precondition plus an off-by-default per-filter cap (#93), not a gate at any level. See `memory/calibration-history.md` Dead Ends before proposing this again.
- [ ] ⚠️ **SUPERSEDED PENDING DECISION 0 (2026-08-12) — do not act on this.** The top-block recommendation is to **DELETE** the per-lens prefilters rather than flip enforcement on, because enabling them would ship #99's English-only `DISCOVERY_PATTERNS` back door (still live in v5) into production for the first time. Resolve decision 0 before touching this line. ~~**NM#284 stage 3 — per-filter enforcement flip**, once a few cycles of shadow data exist.~~ cd is the only filter whose observed rate currently matches its declared one, and it is also the one LD#86 needs. Op-point / normalization re-derivation for affected filters is downstream of the flip (gates #87).
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [x] **#75 CLOSED as measurement artifact 2026-07-31** (owner confirmed) — nature_recovery v4 is healthy.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **`human_thriving` v8 — acceptance criteria (owner decision 2026-08-07).** Two open scorer-fidelity defects in `uplifting v7` are **not** separate work: they die in this retrain or they do not die. Both become held-out eval slices, judged under ADR-021 against oracle ground truth, and both carry #95's ±0.16 band — an article predicted within 0.16 of the op-point is indeterminate and cannot be counted as a pass.
  1. **#91 — dominant subject.** v7 scored a child-trafficking investigation raw **6.77**; it led the homepage with a trafficking price list as pull quote. The scorer rewards narrative fragments over what the article is *about*. Adverse examples are curated at `datasets/adverse/uplifting.jsonl` (`5be62dd`) — **2 records** today (6.7661 and 5.8601), so the slice must be grown before it can gate anything. **Criterion: every adverse record scores below `max_acceptable_wa`**, which the file itself declares as **3.85** (p90 of its reference population) — *not* the 4.0 op-point; the two are different bars and the file's own bar wins. Note both records are labelled `"editorial judgement … NOT oracle-scored"`, so this criterion is judged against an asserted upper bound, not against ADR-021 oracle ground truth — say so rather than implying otherwise.
    *Denominators, kept separate on purpose:* "median 1.36 / p90 3.85" is over **1,947** scored uplifting articles in `filtered_20260801`; the "6th of 3,530" ranking is a different, unstated population. Both derive from `data/filtered/uplifting/*.jsonl`, which is **100% passers by construction and drops source-type-excluded rows** — neither figure is currently re-derivable locally (the NexusMind mirror ends at `filtered_20260726`).
  2. **ducroq/NexusMind#231 — non-English under-scoring.** 19 panel-confirmed reader-facing documented-outcome articles score **3.52–4.42, median 3.74**, against a **4.0** op-point. **They are NOT mostly inside the noise band** — an earlier draft of this entry claimed that; ±0.16 around 4.0 is [3.84, 4.16], and every article listed in the issue is ≤3.74, missing by 1.6× the band at the median. The gap is real and larger than noise, which makes it a better criterion, not a worse one. **Blocker on using it at all:** the evidence file NM#231 describes as "(committed)", `data/held-out/golden-uplifting-2026-06-12.jsonl`, is neither on disk nor tracked in git — **the slice this criterion names cannot currently be enumerated.** Recover or rebuild it first. Note also NM#231's sample is drawn from a `weighted_average ∈ [3.5,4.5]` band with a ≥500-char floor (selection *into* a band around the op-point) and is measured against a "~5.0 hot-DB floor", not 4.0 — state which quantity the criterion means. **Criterion: the 19 clear the op-point, and the English/non-English mean-score gap is reported on one denominator** — not "improved", reported, so v9 has a baseline.
    This is Chain 14's *scoring* stage. It is **not** "the only stage not resolved" — an earlier draft said so and this repo's own board contradicts it: FS#124 (collection) and NM#291 (dedup) are both open and banded P1. Gating (#86) is the one that is measured and decided.
  Note the interaction: #91 wants the scorer to attend to the dominant subject, NM#231 wants it to stop discounting non-English framing. Neither is a threshold move, and a threshold move would trade them against each other — do not resolve either by shifting the op-point.
- [ ] **NM#231 re-measure after uplifting refit** — non-English under-scoring is real but secondary; size the residual model-side gap before considering v8 work. *(2026-08-07: superseded in scope by the v8 criteria above — the re-measure is now a v8 acceptance test, not a prerequisite study.)*
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question).

## 2026-07-27 Session — Small LD Issues Closed

- [x] **LD#49** — Remove 6 broken/superseded filter version dirs (`3e1ccec`). −61,314 lines.
- [x] **LD#68** — Add per-dim `description` field check to `verify_filter_package.py` (`c2ab571`).
- [x] **LD#63** — Branded/sponsored URL path blocking in uplifting v7 prefilter (`623ea51`).
- [x] **LD#57** — Schema gate for `source_filter:` block. Already implemented; closed.

## #52 belonging v1 migration notes (2026-04-29)

Belonging is the second prefilter migrated to ADR-018 declarative shape.
Diverged from sustech v3's "fully declarative" template in two ways:

1. **Data shape only.** Exclusion patterns moved into `EXCLUSION_PATTERNS`
   dict (compiled once by base `__init__`); per-category counts dropped from
   `get_statistics()` and rebuilt from the dict. Iteration order preserved.
2. **Custom apply_filter retained.** Belonging uses per-category
   positive-signal thresholds (3/3/3/2/3/2/special), not BasePreFilter's
   binary `OVERRIDE_KEYWORDS` bypass. Plus URL-based domain exclusions and
   the obit `pos>=1`-floor-when-exception-present rule. None of that fits
   the standard `apply_filter()` pipeline; ADR-018 explicitly allows
   "custom form" for this. The harmonization is at the *data* layer; the
   *control* layer stays specialized.

`POSITIVE_PATTERNS` class attr was kept (shadows `BasePreFilter.POSITIVE_PATTERNS`)
so base compiles it into `_compiled_positives`. `POSITIVE_THRESHOLD` stays at
0, so base's `_has_override` never reads it — belonging consumes the
compiled list directly via `count_pattern_matches`. Documented at the class
attr.

Pattern preservation verified by counts (9/7/9/9/7/6/11/6 exclusion
categories; 10 exceptions; 12 positives; 9 multilingual positives — all
identical to baseline) and 19/19 self-test pass.

No downstream consumers reference the renamed private attrs (verified via
grep across the repo); only the public class symbol + `apply_filter()`
contract are used by `base_scorer.py` and `verify_belonging_v1.py`.

## #52 cultural-discovery v4 migration notes (2026-04-29)

CD v4 is the third migrated prefilter. Same partial-declarative shape as
belonging — exclusion data harmonized, custom `apply_filter` retained.
But the divergence from base differs:

1. **Per-category exception lists.** Each exclusion category
   (appropriation_debate, political_conflict, tourism_fluff, celebrity_art)
   has its own escape-hatch list — celebrity_art has philanthropy /
   repatriation exceptions, political_conflict has reconciliation / peace
   exceptions, etc. BasePreFilter's single `OVERRIDE_KEYWORDS` slot is
   global; CD's exceptions are category-scoped. Modeled with a parallel
   `EXCEPTION_PATTERNS_PER_CATEGORY` dict keyed by exclusion-category name,
   compiled in `__init__` into `_compiled_exceptions_per_category`.

2. **classify_content_type method preserved.** Distinct from apply_filter
   — used (currently only by self-tests, but kept for API stability) to
   tag articles as `cultural_discovery` (>=2 positive boost matches) or
   one of the four exclusion categories or `general`. Rewritten on the
   new dict-based structure.

3. **CULTURAL_DISCOVERY_BOOST_PATTERNS → POSITIVE_PATTERNS.** Same trick
   as belonging: rename so base's `__init__` compiles them into
   `_compiled_positives`. POSITIVE_THRESHOLD stays at 0, so base's
   `_has_override` never reads them — only `classify_content_type` does.

4. **Surfaced bug: missing content-length check.** v3's `apply_filter`
   called `check_content_length` first; v4's does not. Looks like an
   unintentional regression when v4 was created. **Preserved as-is in
   this migration commit** (scope: zero behavior change). Tracked above
   under "Prefilter Quality" as a separate one-line fix at next CD bump.

Behavior preservation verified by 10/10 self-test pass plus identical
pattern counts (11/14, 17/12, 15/14, 15/14 across the four categories;
12 positives; 8/4/6 domain counts).

No downstream consumers (verified via grep): only `base_scorer.py`
references `CulturalDiscoveryPreFilterV4` as a class symbol +
`apply_filter()` call. Older CD versions (v1/v2/v3) keep their old
attr names internally — no cross-version import.

Next: uplifting v7 (flat-list-per-category, pattern-pair override — no count).

## #52 uplifting v7 migration notes (2026-04-29)

Uplifting v7 is the fourth migrated prefilter. Same shape as CD v4 for 3 of
4 categories, with one extra wrinkle: a count-based block.

1. **Three pattern-with-exception categories.** corporate_finance,
   military_security, crime_violence — all use the
   `EXCLUSION_PATTERNS` + `EXCEPTION_PATTERNS_PER_CATEGORY` pair, identical
   to CD v4's structure.

2. **One count-based block (pure_speculation).** Doesn't fit the
   pattern-with-exception shape. Outcome-evidence patterns are a parallel
   *count* check, not a per-pattern exception. Kept as separate
   `SPECULATION_PATTERNS` / `OUTCOME_EVIDENCE_PATTERNS` class attrs;
   inline check after the exclusion-dict iteration:
   `speculation_count >= 3 AND outcome_count == 0`.

3. **classify_content_type preserved.** Has a custom first-check ordering:
   "peace_process" wins when both military_security pattern AND its
   exception fire (e.g. military buildup article that's actually a peace
   accord). Standard category iteration follows. Speculation classification
   uses a looser threshold (>=2 / <=1) than apply_filter (>=3 / 0).

4. **Subclass ThrivingPreFilterV1 verified.** `filters/thriving/v1/prefilter.py`
   inherits from UpliftingPreFilterV7 with only a VERSION override. Public
   API preserved, so the subclass still works post-migration (verified with
   a smoke test exercising all 4 categories).

5. **Surfaced bug: multilingual `\b` boundary leak.** Dutch `munitie`
   (without `\b`) matches inside English "communities". Pre-existing v7
   FP — preserved here, tracked separately under Prefilter Quality.
   Same bug shape as the RIP/rip-current case (#45). Audit all 3
   multilingual exclusion lists at next uplifting version bump.

Behavior preservation verified by 12/12 self-test pass plus identical
pattern counts (21/11, 19/18, 37/25 across the three pattern-with-exception
categories; 7 speculation; 6 outcome-evidence; 8/4/6 domain counts).

No additional downstream consumers (verified via grep): only
`base_scorer.py` references `UpliftingPreFilterV7` directly, plus
`thriving/v1/prefilter.py` via inheritance — neither reaches into private
attrs.

Next: investment-risk v6 (re-exports v5; needs own class — class-name drift
fix is part of the migration).

## #52 investment-risk v6 migration notes (2026-04-29)

Investment-risk is the fifth migrated prefilter and the most structurally
divergent so far. Two things landed in this commit:

1. **Drift fix** — v6 was a thin re-export of v5 (importlib trick because
   the hyphen in `investment-risk` blocks normal imports). v6 now has its
   own `InvestmentRiskPreFilterV6` class. Backward-compat aliases
   (`InvestmentRiskPreFilterV5 = V6`, `InvestmentRiskPreFilter = V6`) plus
   legacy `prefilter()` / `get_stats()` functions preserved so existing
   imports keep working — including v6/base_scorer.py's import via
   importlib (now updated to call `InvestmentRiskPreFilterV6` directly).

2. **Migration to declarative shape** — but only data-shape harmonization;
   apply_filter stays custom for three reasons:
     - **Source-based filtering** runs against `source` / `source_type` /
       `id` fields, not URL or text. Has its own early-return flow:
       allowed-source -> pass, investment-keyword -> pass, blocked-source
       -> block, all before content patterns.
     - **Reasons include matched-pattern info** —
       `allowed_source:reuters`, `investment_keyword:recession`,
       `blocked_source:github`. The base pipeline's `excluded_<category>`
       shape would lose this signal.
     - **Clickbait operates on title only**, not combined text. Stays as
       a separate class attr with its own check below the EXCLUSION_PATTERNS
       iteration.

Three text-pattern categories did get the dict treatment:
fomo_speculation (8 patterns, no exceptions), stock_picking (6 patterns,
12 macro-context exceptions), affiliate_conflict (4 patterns, no
exceptions). The macro_context list is the only per-category exception
this filter has — modeled as `EXCEPTION_PATTERNS_PER_CATEGORY['stock_picking']`.

`(True, "default_allow")` and `(True, "passed")` are intentionally
distinct — investment-risk reports the *reason* an article passed, not
just the fact that it did. Default-allow means "no source/keyword/pattern
fired, falling through to the philosophy: when in doubt, score it."

Behavior preservation verified by 11/11 self-test pass plus identical
pattern counts (19 blocked sources, 25 allowed, 30 keywords; 8/0, 6/12,
4/0 across pattern-with-optional-exception categories; 5 clickbait).

Next: nature_recovery v2 (inline list in method form — simplest of the
remaining; class-name drift fix V1→V2 deferred to the cleanup batch).

## #52 nature_recovery v2 migration notes (2026-04-29)

Sixth migrated prefilter. Simplest of the lot — single text-pattern
category with a single recovery-pattern exception, plus a permissive
nature-relatedness gate.

The structure looked like a clean fit for *fully declarative* shape (sustech
v3 style — base apply_filter + `_filter_specific_final_check` for the
nature gate). But three behavior-preservation concerns ruled that out:

1. **Order**: nature-relatedness check runs FIRST today; base pipeline
   would run it LAST (via `_filter_specific_final_check`). Articles that
   are both off-topic and disaster-themed would change blocking reason
   from `not_nature_topic` to `excluded_disaster_no_recovery` — a
   user-observable change, no matter how rare.
2. **Reason strings**: current returns are bare (`"disaster_no_recovery"`,
   `"not_nature_topic"`); base prepends `excluded_<category>`.
3. **Content-length gap**: current v2 doesn't call `check_content_length`
   (same gap as CD v4 — see Prefilter Quality follow-ups). Base pipeline
   would add the call — also a behavior change.

Settled on data-shape harmonization with a custom apply_filter, same
strategy as belonging / CD v4 / uplifting v7 / investment-risk. The
disaster category fits the EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY
shape cleanly even though it's the only category in this filter.

Class-name drift (file v2 / class V1 / VERSION="1.0") preserved as planned
— part of the deferred cleanup batch alongside sustech V2→V3, gated on
NexusMind cross-repo coordination since their `tests/unit/test_prefilter.py`
imports the V1 name.

Behavior preservation: 6/6 self-test pass. Pattern counts: 33 nature
keywords (duplicate `deforestation` in the original list preserved
verbatim), 1 disaster regex, 1 recovery-exception regex.

Next: foresight v1 (count-based override — `POSITIVE_THRESHOLD = 3`).

## #52 foresight v1 migration notes (2026-04-29)

Seventh and final per-filter migration. Foresight's "count-based override"
turned out to NOT fit BasePreFilter's POSITIVE_THRESHOLD slot — the
semantics differ:

- Base `POSITIVE_THRESHOLD`: bypass when `sum(p.findall() for p in
  POSITIVE_PATTERNS) >= POSITIVE_THRESHOLD` — total match count.
- Foresight v1: bypass when `count(group_name for group in
  POSITIVE_PATTERN_GROUPS if any pattern in group matches) >= 3` —
  distinct categories with at least one hit.

A single repeated keyword in one foresight category counts as 1, not as N.
Migrating to base's semantics would have changed the bypass behavior —
some articles with 3+ matches all in one category would start bypassing
where they previously didn't, and vice versa.

Settled on: data-shape harmonization with a **custom slot**
(`POSITIVE_PATTERN_GROUPS`, not `POSITIVE_PATTERNS`) so the difference is
visible at the class definition. Six block categories DID move into
`EXCLUSION_PATTERNS` cleanly (no per-category exceptions). Custom
apply_filter retained for the distinct-categories-fired logic, the two
pass reasons (`passed_positive_signals` vs `passed`), and URL-based
domain exclusions.

Behavior preservation: 10/10 self-test pass; pattern counts
bit-for-bit identical to baseline (4/4/3/4/3/3 block; 8/4/4/6/3/15
positive; 8/5 domain).

## #52 retrospective (2026-04-29) — what we learned

**All 7 production filters now share a consistent EXCLUSION_PATTERNS data
shape**, even though only sustech v3 ended up using BasePreFilter's full
declarative pipeline. The other 6 retained custom apply_filter for one
or more of these reasons:

| Reason for custom apply_filter | Filters affected |
|---|---|
| URL-based domain exclusions | belonging v1, CD v4, uplifting v7, foresight v1 |
| Per-category exception lists | CD v4, uplifting v7, investment-risk v6 |
| Per-category positive-count thresholds | belonging v1 |
| Count-based block (not pattern-with-exception) | uplifting v7 (pure_speculation), foresight v1 (positive_categories) |
| Source-based filtering on non-URL field | investment-risk v6 |
| Matched-pattern reason strings (`allowed_source:reuters`) | investment-risk v6 |
| Title-only checks | investment-risk v6 (clickbait), belonging v1 (#45 obit) |
| Reason-precedence ordering depends on flow | nature_recovery v2 |
| Bare reason strings (no `excluded_` prefix) | belonging v1, CD v4, uplifting v7, NR v2, foresight v1 |
| Distinct pass reasons (`passed_positive_signals` etc.) | foresight v1 |
| Existing `check_content_length` gap to preserve | CD v4, NR v2 |

**The harmonization is in the *data*, not the *control flow*.** This is
the right call given the genuine variety of filter logic. ADR-018
explicitly permits "custom form" precisely for this case. Future filter
authors can:

1. Read EXCLUSION_PATTERNS to see what each filter blocks.
2. Read EXCEPTION_PATTERNS_PER_CATEGORY (or POSITIVE_PATTERN_GROUPS, or
   the filter-specific override slot) to see what pulls articles back through.
3. Read apply_filter for the specific control flow this filter needs.

That third step is no longer about hunting compiled-regex attributes and
helper methods scattered through the file.

**Surfaced bugs (preserved for zero-behavior-change scope; tracked under
Prefilter Quality):**
- CD v4 missing `check_content_length` call (regression vs v3).
- nature_recovery v2 missing `check_content_length` call.
- uplifting v7 multilingual `\b` boundary leak (Dutch `munitie` matches
  inside English "co-MMUNITIE-s"; same bug shape as RIP/rip-current #45).

**Remaining #52 work:**
- Class-name drift cleanup batch: sustech V2→V3, nature_recovery V1→V2.
  Deferred until cross-repo coordination with NexusMind (whose
  `tests/unit/test_prefilter.py` imports the V2 / V1 names).
- The three Prefilter Quality follow-ups above can be picked up with the
  next version bump on each filter.

