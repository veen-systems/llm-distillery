# Reader flags, 2026-08-09 — 12 pulled, 6 already filed, 5 staged, 1 must stay rejected

Pulled all 89 ovr.news reader flags via `GET /api/flag` (read-only). 35 carry
free-text notes; **15 are off-lens complaints** ("not constructive", "Why isnt
this a solution?"). 12 of those matched a production row.

**Only 5 are new.** Checking against the existing files first is the whole
reason this note is short.

## Already filed — do not restage (6 of 12)

| article | file |
|---|---|
| Momias incas… (smallpox, es) | `cultural_discovery.jsonl` |
| Pocken: Europäer brachten… (smallpox, de) | `cultural_discovery.jsonl` |
| Le dernier voyage sacrificiel de trois enfants incas | `cultural_discovery.jsonl` |
| Kixikila: uma forma de organização social… | `cultural_discovery.jsonl` |
| Madagascar: Invasive Rats Are Stopping Small Mammals… | `nature_recovery.jsonl` |
| Hong Kong mulls AI facial recognition-enabled drones… | `solutions.jsonl` |

The two smallpox rows are the same study in two languages, already noted as a
pair on 2026-08-05.

## Already REJECTED — must not be re-proposed (1 of 12)

`south_american_brasil_de_fato_42843d936b64` — *Unifesp identifica resíduo
compatível com sangue no antigo DOI-Codi/SP*, `cultural_discovery` raw 6.11,
reader note "Not constructieve i tbink?".

Adjudicated **not adverse** on 2026-08-05 with full reasoning: forensic work by
a living university on a dictatorship torture site is an ongoing process going
well, and labelling it adverse would suppress truth commissions, mass-grave
identification and transitional justice as a category. The reader flagged it
again; the decision stands. Its absence from `cultural_discovery.jsonl` is
deliberate, and it is recorded here so that absence does not read as an
oversight on the next pass.

## Staged as candidates (5 of 12)

In `candidates/2026-08-09-reader-flags.jsonl`, with draft verdicts. **None are
adverse rows yet.**

| article | lens | raw | bar | draft (revised after reading full text) |
|---|---|---|---|---|
| 'Rattled' Charleville community vows to unite after 'violent' crime | belonging | **7.04** | 1.6446 | ADVERSE — clear |
| NEW: Five men arrested… for raping a minor | uplifting | **6.85** | 3.85 | ADVERSE — clear |
| Rethink Business Centre Management | uplifting | 6.09 | 3.85 | ADVERSE — clear *(upgraded)* |
| The silent crisis on our plates | uplifting | 6.49 | 3.85 | **RECOMMEND REJECT** *(downgraded)* |
| The anatomy of erasure: Indigenous Assyrian women… | belonging | **7.67** | 1.6446 | **needs adjudication** |

**Two drafts moved once the full articles were read, in opposite directions —
which is the argument for reading them.** The Rappler piece has a recovery arc
("It meant learning how to simply enjoy eating again") and belongs in the lens;
the reader's objection is to its RANK, not its membership, and that is the
DOI-Codi situation — filing it adverse would fix the wrong layer. The Namibian
piece turned out to be a signed consultant's opinion column about facilities
*failing* their mandate, with nothing delivered, so it strengthened.

**The test that separates them, and it is the owner's own from 2026-08-05:**
does the article contain a process that is going well *now*? DOI-Codi did (a
living university doing forensic work). The Rappler piece does (a recovery). The
Namibian column does not (a complaint plus a proposal). The Assyrian essay does
not either — it closes on "justice that remains unresolved" — which is why the
DOI-Codi precedent does **not** shield it and why it needs a real decision.

Every one is **above its lens's p99**, so these are not marginal admits — they
are confident, top-of-feed placements. The Charleville row scores 7.04 on
belonging because "community vows to unite" — a phrase that exists *because* two
people were murdered. The Zimbabwe row normalizes to **9.86**, i.e. it would
lead the feed.

The Assyrian-genocide row is deliberately **not** proposed as adverse, but note
the reason changed once the full text was read: it is **not** shielded by the
DOI-Codi rejection, because that turned on a process going well now and this
essay has none. What holds it back is the consequence, not the precedent —
accepting it risks teaching the scorer to suppress memorialisation and
Indigenous-rights coverage as a category. It is staged so the decision is made,
not so it is assumed.

## Why these matter more per row than the oracle batch

The same day's oracle batch graded uplifting's ≥5.5 band **29/29 perfect**.
Three of the rows above sit in that band and readers called them not
constructive. An oracle that defines the editorial line the student was trained
on cannot see a blind spot it shares — **so oracle-driven active learning
cannot surface this class at all.** Reader flags are currently the only
independent label source, which is why 5 hand-checked rows are worth more here
than 34 oracle-selected ones.

## Two limits of the source

- ovr.news no longer records a reason category — flags are free text only, by
  design. The `wrong_lens` counter on `/ops/flags` reads 0 and is vestigial for
  new flags; do not read it as "no lens complaints".
- **The flag does not record which lens the reader was viewing.** Several of
  these surface in three lenses at once, so lens assignment above is inferred
  from where the article scored highest above its own p99, not from the reader.
