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

