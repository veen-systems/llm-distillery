# Reader flags, 2026-08-09 — 12 pulled, 6 already filed, 3 accepted, 2 rejected, 1 open

Pulled all 89 ovr.news reader flags via `GET /api/flag` (read-only). 35 carry
free-text notes; **15 are off-lens complaints** ("not constructive", "Why isnt
this a solution?"). 12 of those matched a production row.

**Only 5 were new** — checking the existing files first is what turned 12 rows
into 5. Of those, 3 were accepted as adverse, 1 rejected, and 1 is still open.

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

## ADJUDICATED 2026-08-09 (owner)

**Accepted as adverse — 3.** Promoted into the lens files with
`label: adverse`, `labelled_by` naming the decision.

| article | lens | raw | bar | file |
|---|---|---|---|---|
| 'Rattled' Charleville community vows to unite after 'violent' crime | belonging | **7.04** | 1.6446 | `belonging.jsonl` |
| NEW: Five men arrested… for raping a minor | uplifting | **6.85** | 3.85 | `uplifting.jsonl` |
| Rethink Business Centre Management | uplifting | **6.09** | 3.85 | `uplifting.jsonl` |

Counts after promotion: belonging 1 → **2**, uplifting 2 → **4**.

**Rejected — 1: "The silent crisis on our plates"** (Rappler, `uplifting` raw
6.49, normalized 9.57). Recorded here because a row that is simply absent looks
like an oversight.

Read in full (13,107 chars) it is a **recovery**: Haley *used to* struggle with
binge eating disorder, and it closes on "It meant learning how to simply enjoy
eating again" plus a help-seeking note. It belongs in the lens. The reader's
objection is to its **rank**, not its membership — a harm-heavy opening carried
it to the top of the feed. Same disposition as DOI-Codi: when the fault is
framing rather than lens-fit, an adverse label fixes the wrong layer and makes
the scorer worse.

*This one also stands as a caution about method: it was drafted "probable
adverse" off a 190-character excerpt and reversed on reading the article. Three
of the five drafts moved after full-text review. Excerpts are not sufficient for
adjudication.*

**Still open — 1.** See below.

## Still awaiting adjudication — 1

In `candidates/2026-08-09-reader-flags.jsonl`. **Not an adverse row.**

**"The anatomy of erasure: Indigenous Assyrian women and forgotten genocide"**
(Global Voices) — `belonging` raw **7.67** against a p99 of 5.41, normalizing to
**9.93**: the highest score in this batch and effectively top of the feed.

A first-person essay on the 1933 Simele massacre and Seyfo, and on memory
eroding as elders die. It closes on remembrance that is *"incomplete,
constrained by the stories that were never told ... and the justice that remains
unresolved."* So the model is asserting exemplary community thriving about an
essay whose subject is a community's erasure.

**It is not shielded by the DOI-Codi rejection**, and the reason matters: that
one turned on the article containing a process going well *now* — a living
university doing forensic work. This essay has none.

**What holds it back is the consequence, not the precedent.** Publishing the
essay is itself an act of community continuity; Global Voices is exactly the
Global South source ovr.news wants to carry; and an adverse label here teaches
the scorer to suppress memorialisation and Indigenous-rights coverage as a
category. That is the 2026-08-05 hazard in its sharpest form, which is why it is
staged for a decision rather than proposed.

## The test that decided the rest

The owner's own from 2026-08-05, and it settled four of five here — recorded so
the next pass does not re-derive it:

> **Does the article contain a process that is going well *now*?**

- DOI-Codi forensics — **yes** (a living university at work) → rejected as adverse
- Rappler eating-disorder recovery — **yes** (a recovery) → rejected as adverse
- Namibian workspace column — **no** (a complaint plus a proposal) → adverse
- Assyrian erasure essay — **no** ("justice that remains unresolved") → still open

Charleville and the Zimbabwe arrests needed no test: both are stories *about*
harm that merely contain a good-sounding phrase. The Charleville row scores 7.04
on belonging because "community vows to unite" — a phrase that exists *because*
two people were murdered. The Zimbabwe row normalizes to **9.86**.

## Why these matter more per row than the oracle batch

The same day's oracle batch graded uplifting's ≥5.5 band **29/29 perfect**.
Three of the flagged rows sit in that band and readers called them not
constructive — two are now accepted adverse rows (6.85 and 6.09), and one is the
still-open Assyrian essay at 7.67. An oracle that defines the editorial line the student was trained
on cannot see a blind spot it shares — **so oracle-driven active learning
cannot surface this class at all.** Reader flags are currently the only
independent label source, which is why 5 hand-checked rows yielded 3 accepted
adverse examples while 34 oracle-selected candidates yielded none.

## Two limits of the source

- ovr.news no longer records a reason category — flags are free text only, by
  design. The `wrong_lens` counter on `/ops/flags` reads 0 and is vestigial for
  new flags; do not read it as "no lens complaints".
- **The flag does not record which lens the reader was viewing.** Several of
  these surface in three lenses at once, so lens assignment above is inferred
  from where the article scored highest above its own p99, not from the reader.
