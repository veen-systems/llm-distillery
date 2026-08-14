# `origin.*` — sequencing an editorial task, not an engineering one

**2026-08-14. Sequencing note, not approved, not started.**
Companion to `docs/proposals/contract-a-redesign.md` §C and the envelope decision
(`docs/decisions/2026-08-14-contract-a-envelope.md`). Split out on the owner's
instruction: *"origin.* is an editorial task, not an engineering one — sequence it
separately."*

---

## Why it is not in the implementation pass

Every other block in the redesign is **threading out** — the value exists at
collection time and is discarded at a return statement. `origin.*` is the one block
where **the value does not exist anywhere yet.** FluxusSource's answer to #112 was
explicit: no country and no timezone exists on a source anywhere in config.

The size, from their triage: **~1,872 per-source YAML entries**, not ~30 aggregators
— aggregators do not know a publisher's country. Of 107 config shelves, **64 are
geographic and cover 932 of the 1,872 feeds**; the remaining ~940 need judgement.

So the cost is a person deciding 1,872 times, and no amount of engineering
compresses it. Starting it before the block shape is stable spends that cost twice.

## ⚠️ The trap: a shelf is not a claim about the publisher

The obvious move is to bulk-seed the 932 from their geographic shelf. That produces
a field that **looks measured and is a restatement of the shelf layout**. The first
analysis that says "X% of our corpus is African publishers" would then be reporting
how the config files are organised, which is the question `origin.country` was added
to escape (`source_group` mixes 64 geography / 37 subject / 6 collection-method
shelves, and that conflation is why the question is unanswerable today).

This is the hand-built-population failure in a new place: a population someone chose
by hand, wearing the clothes of one the pipeline computed.

**So `origin.*` needs a provenance sibling before any seeding happens.** The same
shape as `published.had_timezone` and `language_source`, and for the same reason —
separating *stated* from *assumed* is unrecoverable if not recorded at the time:

```
origin.method   "config_declared"    a person decided this source, individually
                "shelf_inferred"     bulk-seeded from a geographic shelf
                "aggregator_supplied" the API told us  (GDELT metadata.source_country)
```

Without it, 932 inferred values and ~940 judged ones are byte-identical downstream,
permanently.

## ⚠️ Second trap: country does not determine timezone

`origin.timezone` is the field that pays — it is what makes an offset-less publisher
date recoverable *after the fact*, converting the redesign's worst case from
unrecoverable to merely awkward. It will be tempting to derive it from
`origin.country` with a lookup table.

That is correct for most countries and wrong for the ones with the most publishers:
the US, Russia, Brazil, Australia, Canada, Indonesia, Mexico and the DRC all span
several IANA zones. A country→timezone table is a silent wrong answer precisely where
the corpus is densest. Multi-zone countries need the timezone decided per source, or
left null — **null is honest and a wrong zone is not**, since the whole point of the
field is to disambiguate a naive timestamp.

## Sequencing — three tranches, and only the first is engineering

**T0 — engineering, small, do with the redesign.**
1. The block is already declared by the envelope commit (all properties optional), so
   nothing is blocked on schema work.
2. Add `origin.method` to the declaration. It must exist *before* the first value is
   written, not after.
3. Wire the one case that is already populated: GDELT rows carry
   `metadata.source_country`. Passing it through as
   `origin.country` + `origin.method: "aggregator_supplied"` proves the path end to
   end on real rows **before any editorial time is spent**, and it is the only tranche
   whose outcome can be checked by running a cycle.

**T1 — editorial, bulk, ~932 entries.** Seed from the 64 geographic shelves, every
one stamped `shelf_inferred`. Cheap, reversible, and honest about what it is. A
consumer can then choose to trust or exclude it, which it cannot do today.

**T2 — editorial, judgement, ~940 entries plus corrections to T1.** The long tail.
Whether this is ever worth completing is a separate call, and it can be taken with
T1's data in hand — which is a better position than taking it now.

## Do not start T1 before the engineering pass lands

The editorial cost is unrecoverable if the block shape moves. T0 is safe because it
is code. T1 and T2 should wait until `published.*`, `fetch.*`, `content_meta.*` and
`collected.*` are emitting and the schema has stopped changing.

## Where the work is filed

The config is FluxusSource's (`config/schemas/source_schema.yaml` and the per-source
YAML), so T0–T2 belong on their board, not this one. This note is the sequencing
argument, not the ticket.
