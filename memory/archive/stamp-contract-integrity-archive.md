# Stamp & contract integrity — archive of closed entries

*Moved VERBATIM from `memory/stamp-contract-integrity.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read surface), under
the 2026-09-27 ledger rule: entries whose verdict is closed (CONFIRMED / REFUTED / SETTLED / RESOLVED) move; open
entries, rulings and standing traps stay. Order kept; a block from inside a section repeats that section's heading.
Owner's DATE rule (2026-10-09), by judgement: the NM#300 fix history, the four-validator finding (itself superseded),
the single-run 2026-08-13 measurements and the block already headed SUPERSEDED moved; rules, instrument traps, the
Contract A record and the register sections stay.*

## NM#300 is FIVE allowlists in series (2026-08-08, proven by outcome)

It was diagnosed as "two drops in series", both fixed and deployed — and the
next cycle still read **0 of 2,170**, with both fixes provably loaded. There are
five explicit allowlists between the scorer and the persisted row:

| # | location | |
|---|---|---|
| 1 | NexusMind `deploy/gpu-server/main.py` — `FilterScoreResult` (Pydantic) | server |
| 2 | `src/scoring/gpu_client.py:141` — `FilterScoreResult` **dataclass** | client |
| 3 | `src/scoring/gpu_client.py:815` — its construction from `response.json()` | client |
| 4 | `scripts/main.py:481` — dataclass → dict conversion | consumer |
| 5 | `scripts/main.py:1099` — the `analysis` dict | consumer |

The first diagnosis fixed 1 and 5 and checked the wrong seam for a third: it
verified that `analysis` is attached whole and written with
`json.dumps(article)` — true, and not where the loss is. **When a value crosses
a process boundary, patching the sender does nothing unless the receiver's
parser is also an allowlist — and here it was, twice.**

**`absent` vs `null` localises the fault for free.** After hops 1+5 were fixed,
`content_length` went from *absent* to *present-and-null*. Absent = nobody wrote
the key. Null = the last hop wrote it and something upstream had already emptied
it. That distinction pins the fault to the middle hops without reading code —
and a census that only counts `is not None` throws it away. Check `"k" not in d`
separately from `d[k] is None`.

## The finding

**The estate has FOUR contract validators and none watches the failure.** Draft 1
of the plan claimed nothing ran a validator at all; **that was false**, refuted by
ovr.news. The claim came from grepping for one script *name* rather than for the
*behaviour* — `a grep for a pattern is not a grep for a behaviour`, broken while
auditing contracts.

| validator | on real bytes | blind to |
|---|---|---|
| `FluxusSource/scripts/validate_output.py` | yes, with a track record | consumers' beliefs — its own schema only |
| `ovr.news/src/lib/data/validate.ts` (`summarize.ts:404`, since 2026-03-03) | yes — and **drops rows** into an unread log | `published_date` **and** `metadata`: `grep -c` → **0** |
| `NexusMind/scripts/validate_production_contract.py` | when invoked | — **unscheduled** |
| `NexusMind/validate/validate_contract_a.py` | has `--latest` | — **no caller** |

Say **unscheduled**, never *never executed*: no file naming a script is not proof
nobody ran it interactively.

## Measured, run `content_items_20260813_161006` (3,514 rows) unless stated

- Top level **12 fields on 100%**; `metadata` **52 distinct keys** — ⚠️ **a
  SINGLE-RUN count, and NOT a namespace measurement.** Reproduces exactly, and is
  still the wrong quantity for almost every question: per-run counts range **27 to
  107, median 63.5** across 50 runs. **Never derive a share or a percentage from it**
  — see the retirement note below before quoting this line.
- FluxusSource's schema declares **7** metadata keys, Contract A declares **12**,
  **overlap ZERO**. Provenance half vs operational half. 34 declared by neither —
  **legal**, Contract A's `metadata` is `additionalProperties: true`; only its top
  level is closed.
- Contract A defects over 6 cycles / 21,636 rows: `social` missing from the enum
  (78 rows); `priority` ∈ {9,10} over `maximum: 8` (**2,774**); `word_count`
  absent (**267**) and `priority` absent (**928**) though both `required`.
- **ovr reads exactly 2 metadata keys** — `og_image_url`, `quality`. `og_image_url`
  is read at `summarize.ts:334` **upstream** of the `:887` projection that discards
  it, so a field can be load-bearing at ovr and **leave no trace in the stored row**.
  ⚠️ **The "2 of 52 / 96% undeclared" form is RETIRED (2026-08-14), and the reason
  is stronger than "wrong denominator".** The **2 is solid.** But **a single-run key
  count is not a namespace measurement at all** — it measures which aggregators
  happened to be due in that tick. FluxusSource counted distinct metadata keys per
  run across all 50 runs in the hot window: **min 27** (`…_20260808_160714`, 494
  rows), **median 63.5**, **max 107** (`…_20260813_001014`, 3,814 rows) — a **4×
  spread**. The run this file used gives 52; the next morning's gives 55. Sampling
  six hours either side would have produced a visibly different percentage over the
  same estate. **52 reproduces exactly** (`collection_20260813_161007`, 3,514 rows,
  independently confirmed by the producer), so it is a correct number answering a
  question nobody wanted asked.
  - The producer's inventory counts **168** keys, **154 of the 168 confined to a
    single `source_type`**. That is the **hot-window union** — `data/current/`, 50
    runs, 2026-08-06→08-14. **Do not call it "the full namespace":** `data/archived/`
    is kept indefinitely since FS#164, so keys retired before 08-06 sit outside it.
  - **3** keys are read by name in consumer pipeline code: `quality`,
    `og_image_url`, `priority`. ⚠️ **Carry this caveat with the 3 every time** — it
    means *read by name*, **not** *the only keys that can break a consumer*.
    NexusMind passes the whole `metadata` blob through untouched into
    `data/filtered/*.jsonl`, so a key nobody names still travels and can still be
    depended on downstream. Without that sentence the 3 reads as a safety margin it
    is not.
  - **Quote the 2, the 3 and the 154/168 with its window; do not reconstruct the
    percentage.** It also moves the wrong way: declaring more keys (principle 1)
    makes it look worse.
- Byte budget: 1,700 B/row · `metadata` **37.5%** (larger than `content` at 23.8%)
  · repeated JSON keys **30.3%** · gzip 4.5×.
- Standards: `language` 3,509/3,514 two-letter, `zh-cn` ×5; `published_date` /
  `collected_date` **99.4–99.7% carry no UTC offset**; `url` 100% absolute.

## ⛔ Two counts that are SUPERSEDED — kept only to date the correction

*Moved here from `memory/MEMORY.md` on 2026-08-17 (`/audit-context`); the index was
their only home, and an index entry is a hook, not a record.*

- **"FOUR validators" was an undercount**, by an instrument that could only see one
  shape. A behaviour sweep over all 20 repos found **21+** — and counting them was the
  wrong question anyway. The finding in its final form: **exactly TWO shape checks are
  both automatically invoked AND looking at real production bytes, and between them they
  assert eight key names and two strings' max length.**
- **"ovr reads 2 of 52" is retired.** The **2 stands**; the 52 was a single-run count
  ranging **27–107** across runs, so the derived 96% never had a denominator.
- **The two schemas over one stream overlap on ZERO metadata keys.** (2026-08-13,
  § *The contracts layer*.)

## Moved 2026-10-16 (#163 round 6)

*Moved VERBATIM; each block repeats its source section heading. Reason: (1) a dated 2026-08-08 episode whose lesson (a rate needs its population) lives in `feedback-rate-needs-population`; (2) the redesign-era plan, SUPERSEDED by Contract A shipping 2026-08-16, with `clock_source` and `_get_tzinfos` now tracked in `memory/date-error-recency-boost-hypotheses.md`.*

## VERIFIED FIXED — 17:10 cycle, 2026-08-08

**My pass criterion was the wrong shape and I published it anyway.** I
pre-registered "`stage1_low` should be a nonzero *minority*, the 08:00 journal
showed 17–32%". Observed: solutions **64.6%**, cultural_discovery **51.5%** —
both "fail" that wording. The 17–32% came from journal lines whose filter I never
identified, so the baseline was not the same quantity; and a screening rate has
no reason to be a minority. The right criterion is *populated, discriminating
(≥2 values), and no `stage1_low` row above the op-point*. **A per-filter quantity
compared against an unattributed aggregate is not a check** — third instance
today, after `source_filter excluded N` and the GN population split.

# ⭐ REDIRECTED 2026-08-14 — the contract is being REDESIGNED, not patched

**Seven categories of exclusive+perishable fact**, A–F from defects tripped over and
**G supplied by pipeline-atlas from the chain model**: time · language (incl. `script`)
· origin (country/region/IANA tz) · fetch (charset triple, redirects) · content fidelity
· feed · **the non-event**.

⭐ **G is the one nobody would find from symptoms.** A–F all presuppose a fetch
happened. Two sites refuse work *before the network* — one leaves **no trace at all**,
the other records `items: 0` with no error key, so it reads as a successful empty visit.
**"This publisher went quiet" and "we stopped asking" are indistinguishable downstream,
and they have opposite editorial meanings.**

✅ **BOTH ANSWERED by FluxusSource at close.** `content_meta.kind` is **(b), one line —
and it COLLAPSES**: FluxusSource never fetches bodies (~~`full_text_fetcher.py`~~ deleted,
enrichment moved to NexusMind), so `full_text` is not emittable and `kind` reduces to
`feed_summary` vs `headline_only`, both decidable at parse time. **This retires the
300-char floor.** `origin.*` is **(c)** and no country/timezone exists anywhere — but
**the unit is ~1,872 per-source YAML entries, not ~30 aggregators**, ~932 bulk-seedable
from geographic shelves: **an editorial cost, not an engineering one.** Most of TIME is
(b) and threading-out rather than computing; **most of LANGUAGE already exists** as
`language_source`/`language_confidence`/`language_input_len` — ⚠️ **do not rename them**,
two are inputs and #149's floor is fitted on the others.

⭐ **And the field this proposal MISSED: `collected.clock_source`. 19 of 26 aggregators
build `collected_date` from local `datetime.now()`** — byte-identical downstream to a
UTC value and wrong by the host offset, unrecoverable. The same defect as
`published_date`'s, on *our own* clock, and nobody had noticed.

**Superseded, kept to date the correction:**

1. ~~**FluxusSource feasibility triage**~~ — which proposed fields are already in hand at
   collection, which are one line, which need new plumbing. Two decide the sequencing:
   does `origin.country`/`timezone` exist in source config in *any* form, and is
   `content_meta.kind` (full body vs feed summary vs headline) knowable at collection?
   **If the second is yes it retires the 300-char floor outright.**
2. **`_get_tzinfos` third population** — still UNMEASURED, and it fails in the direction
   of looking correct (an unrecognised tz abbreviation is silently relabelled UTC and
   arrives *aware but wrong*). Do not let "unmeasured" decay into "small".

⚠️ **Blocker the redesign inherits:** both schemas set `additionalProperties: false`, so
**a redesign cannot ship incrementally under the current shape** — the shared-envelope
question arrives as a hard blocker rather than a design choice. Full invalidation list
(6 items, ranked by how quietly each breaks) is in the proposal.
