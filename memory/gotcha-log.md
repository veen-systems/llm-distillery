# Gotcha Log

Problems encountered and resolved. Format: Problem → Root cause → Fix.

<!-- Template for new entries:

## [Short description] (YYYY-MM-DD)
**Problem**: What went wrong or was confusing.
**Root cause**: Why it happened.
**Fix**: What solved it.

     Write the lesson, not the narrative of the session that found it.

     ⚠️ The old "keep it to 2-3 lines" rule is WITHDRAWN (agent-ready-projects
     v1.25.0), and this log is the evidence that retired it upstream: 203
     entries, median ~1,200 chars, 35% over 1,500. The rule was unenforceable
     (a markdown source line has no length limit, so it could be met and
     violated at once) and enforcing it in characters would have flagged
     88-92% of entries across three independent logs. Upstream's verbatim
     adopter note: "If you have been ignoring it, you were right to."
     The real signal is ABOVE ~3,000 characters — 2-7% of entries across the
     logs measured (this one is the high end, 5.8%) — and at that size it belongs in a topic file or an ADR.

     STATUS AND RECURRENCE GO IN THE HEADING, NOT THE BODY (v1.24.0). Curation
     reads headings and opens a body only for an entry it is acting on, so a
     status buried in prose is invisible to it. Forms in use here:
         ## [RESOLVED] Title (date)
         ## [RESOLVED <date>] Title (date)
         ## [RESOLVED <date> by <ref>] Title (date)
         ## [<N>x <pattern-name>] Title (date)   <- recurrence
         ## [<N>x] Title (date)
     `[CORRECTED <date>]` is a second accepted status form (one entry uses it).
     Grep `^#{2,3} \[` to catch every status marker, not `[RESOLVED` alone.

     (agent-ready-projects v1.25.0. Note the heading level differs from the
     framework template: entries here are `##`, not `###` — and BOTH levels
     are in use, so any reader must match `^#{2,3} `. A `^### `-only grep
     misses 106 of the 203 entries here (re-derived 2026-08-12: 106 under `##`,
     97 under `###`); that exact bug shipped upstream in a
     v1.24.0 draft and was caught on this file.)

     NEW ENTRIES ONLY. Do not retrofit the existing log — a bulk rewrite of
     history is a separate, engineer-approved decision, and this file is
     1,995 lines precisely because it predates the rule.
-->

---

## PINNING AN ALIAS TO ITS "REAL" NAME IS NOT A RENAME — `deepseek-chat` and `deepseek-v4-flash` are different runtimes (2026-08-14)

**Problem**: Every DeepSeek call site in this repo hardcodes the **alias** `deepseek-chat`
(`scripts/score_deepseek_production.py:197`, `filters/common/violence_promotion/v1/oracle.py:66`,
`scripts/validate_deepseek_oracle.py:270`, `filters/common/obituary_detector/validation/relabel_deepseek.py:44`),
never a model ID. Ahead of the 2026-08-16 repricing the obvious hygiene move is to pin the
literal model so the cost line is unambiguous. **That change would have broken the oracle**,
and it would have looked like a no-op rename in review.

**Root cause**: The alias does not merely *name* a model — it selects a **mode**. Measured
against the live API, same prompt, `max_tokens=60`:

| model sent | resolved | prompt tok | completion tok | content |
|---|---|---|---|---|
| `deepseek-chat` | `deepseek-v4-flash` | 22 | **1** | `'10'` |
| `deepseek-v4-flash` | `deepseek-v4-flash` | 101 | **60**, all `reasoning_tokens` | `''` |

The explicit ID injects a fixed ~79-token preamble (reproduced exactly on a second, unrelated
probe: 5→84) and runs in **reasoning mode**: output lands in `reasoning_content`, `content` is
empty, and the whole token budget is spent thinking. Our score parser reads `content`, so it
would receive an empty string on every article. Reasoning tokens bill at the **output** rate —
the rate rising most in the 2026-08-16 change.

**Fix**: Leave the `deepseek-chat` strings exactly as they are. The alias is load-bearing, not
sloppiness. `--model` help text in `validate_deepseek_oracle.py` now says so; the stale
"default: deepseek-chat for V3.x" it replaced was actively misleading, since the alias has
resolved to V4-flash since the V4 GA.

**Generalisation**: *A name that the vendor resolves server-side is an API surface, not a
label.* Replacing it with "what it really is" is a behaviour change disguised as a cleanup —
the same family as this repo's rename traps, but sourced outside the codebase, so no amount of
local grepping reveals it. **The only instrument that answers it is a live call whose response
you inspect** (`d['model']`, `usage.completion_tokens_details`, and whether `content` is empty)
— reading vendor docs would have confirmed the alias mapping and said nothing about the mode.

**Related, same session**: only two model IDs exist for our key (`GET /models` →
`deepseek-v4-flash`, `deepseek-v4-pro`), so there is **no lighter tier** to retreat to under the
price rise. See `memory/oracle-pricing-scheduling.md`.

---

## NEVER MASK A UNIT THAT SITS IN AN `OnSuccess=` CHAIN — the loss has no failure surface (2026-08-14)

**Problem**: The obvious way to open a maintenance window on sadalsuud is to mask the
unit you need to hold still — e.g. `ovrnews-summarize.service` while rewriting
`ovr.db`. **Do not.**

`OnSuccess=` is **fire-and-forget**. By the time the downstream unit would start,
`nexusmind.service` has **already exited 0**. So masking the downstream unit means
that cycle's work simply never happens, **the upstream run is still recorded as a
success, and nothing anywhere reports a failure.** The cycle is lost silently.

**Fix**: don't mask — **use the quiet window instead.** The chain is
`fluxus-collection.timer` → `nexusmind.service` → `ovrnews-summarize.service`, and it
occupies roughly **90 of every 240 minutes**, leaving a **~2.5h quiet window from
about :35 past the hour after a tick** until the next.

⚠️ **And the grid is FluxusSource's, not NexusMind's** — verified:
`systemctl show nexusmind.service -p TriggeredBy` is **EMPTY**. ovr's writer is
**three hops from the clock**. Anyone reasoning about "NexusMind's schedule" is
reasoning about a timer NexusMind does not have. See
`reference-sadalsuud-pipeline-chain` in the auto-memory, which already says NexusMind
is `inactive` between cycles **by design**.

*(Found by the ovr.news session while planning a corpus backfill; the masking
instinct is the natural move and it is the wrong one.)*

---

## ⭐ THE UNIFYING FORM: a check that answers a NARROWER question than the one asked of it — where the narrow answer is TRUE (2026-08-14)

*(NexusMind's formulation, after four instances landed in one day. This is the
general case of most entries below it.)*

> **A check answers a narrower question than the one being asked of it, and the
> narrower answer is true.** Nothing is broken, nothing is lying, and the result is
> read as covering the wider question.

Four instances, same day, four different sessions:

| the check | what it actually answers | what it was read as |
|---|---|---|
| sha256 of a spec | *are these the announced bytes?* | *have these bytes been reviewed?* |
| a key-diff against a spec's JSON block | *are the keys present?* | *does this artefact conform?* |
| `grep -rIl <script-name>` | *is this name mentioned?* | *does anything CALL it?* |
| `systemctl show` (`ActiveState`) | *is it running right now?* | *does the unit exist?* |

**Why it is worse than a wrong check:** a wrong check eventually produces a visibly
wrong answer. **This one is correct forever**, so nothing ever contradicts it, and
the gap lives entirely in the reader's head. *That is why four sessions hit it in one
day and none noticed from the output.*

⭐ **USE THIS ONE PROSPECTIVELY — it supersedes the symptom-level form.**
*(pipeline-atlas, comparing it to their own register's wording and preferring this
one.)* An earlier statement of the same defect was *"a check whose verdict does not
change when the claim becomes false"*. **That names the symptom; this names the
cause** — and the symptom form is **only applicable in hindsight**, because to use it
you must first imagine the event that would falsify the claim, and anyone who could
reliably do that would not have written the bad check.

> **The cause form reduces to one question you can ask of any check BEFORE trusting
> it: *what question does this actually answer, and is it the one I am asking?***

`ls` answers *"do these paths exist"*, not *"does validation happen"*. A hash answers
*"do I hold the announced bytes"*, not *"have I read them"*. Both fall out
immediately, with no hindsight required.

**Fix**: state the property the check establishes, in the sentence that reports it.
*"Hash-verified"*, not *"verified"*. *"Keys present"*, not *"conforms"*.
*"N mentions"*, not *"no callers"*. **If the report names the narrow property, the
gap cannot open.**

⭐ **THE TELL — how to catch it in yourself.** *(NexusMind, having nearly committed
the fifth instance inside the message about the pattern.)* **The narrow answer is
not merely true, it is SATISFYING. It arrives feeling like closure** — which is
exactly why nobody asks the wider question afterwards. If a check's result lands as
relief, that is the moment to ask what it did *not* establish.

**The fifth instance, and it is a good one because the arithmetic is airtight.**
A file's growth was accounted for exactly: three additions summing to 1,226 bytes
against a delta of 1,226. That is a **stronger** constraint than it looks — the net
of every other edit must be zero — and a **much weaker** one than it feels:

> ⚠️ **Byte accounting is blind to any SAME-LENGTH SUBSTITUTION.** A changed digit, a
> flipped `true`/`false`, a swapped identifier of equal length — all invisible, all
> net-zero, all perfectly consistent with the arithmetic.

**And that is precisely the class the defect it was meant to reassure about belonged
to**: the unit-name bug was a **value** change, not an addition. It happened to cost
23 bytes only because `nexusmind-` has length. **Had the wrong name been the same
length as the right one, the reconciliation would have been perfect and the defect
still there.** So the accounting was not merely *"still trust"* — it was
**structurally incapable of detecting the specific defect it was offered as assurance
about.**

> ⭐ **Byte counts answer *"how much changed"*, never *"what changed"* — and the two
> look identical when the answer is reassuring.**

✅ **THE POSITIVE CASE, so this does not overcorrect into "hashes are useless".** The
same reviewer later used a hash correctly: *"is the committed blob the text I already
read?"* — and a hash answers **exactly** that, no narrower, because they had read the
text first. At rev 3 they asked *"have I verified the spec?"* and answered it with a
hash, which is a strictly narrower question wearing the same clothes. **Same
instrument, different question, different verdict.** The defect is never the tool; it
is the gap between the question asked and the question answered.

*(Related, same day: pin the **full** object name, not a short SHA or a branch —
branches move, short SHAs collide, and only the full name means one specific text
forever.)*

⚠️ **And test it against the wider question, not the narrow one.** NexusMind's unit
test for this had been `assert (d / "nexusmind-contract-check.timer").exists()` —
**two spellings of one literal compared to each other**, never reading the artefact
at all, in the test written specifically to protect the reader contract. It passed
however wrong the published names were. Now derived from the artefact's own `units`
block, with a control: publishing the unprefixed name fails three tests, and would
have failed none of the old ones.

---

## A HASH IS NOT A REVIEW — identity and content are different guarantees (2026-08-14)

**Problem**: A spec file was declared "frozen" and pinned by sha256 so a downstream
implementer could detect a silent edit. They computed the hash, matched it, and
recorded the spec as **"verified"**. Both sides then believed the content had been
checked. **It had not been read at all.**

It surfaced when they spot-checked a later revision's claim that no fields had
changed: they grepped for `artefact_version`, `expected_cadence_seconds`,
`checker_version`, `schema_sha256`, `hops_not_covered`, `rows_invalid` — **all six
returned zero**, which briefly looked like the announcement was a lie. It was not.
Those were names from **two revisions earlier**; the intervening revision had
restructured the whole shape. **They had been carrying a two-revision-stale model
while believing it was verified.**

**Fix**: say **"hash-verified"**, never "verified". A hash proves **identity** — that
you hold the bytes the author announced. It proves **nothing about their content**.
The word "verified" is read later as "reviewed the fields", which is the thing nobody
did.

⚠️ **The sharper half — hash-pinning has a second boundary that only version control
closes.** The pinned file was untracked and each revision **overwrote the last in
place**, so the earlier revision no longer existed anywhere and *nobody could diff
them*. "No field added, removed or retyped" was therefore taken **on trust**.
**Announcement + hash proves identity; only version control proves what CHANGED.**
Had the file been committed, the check would have been a two-line diff instead of six
greps and a false alarm.

**General form**: when a check substitutes for a review, name the property it
actually establishes. *Verifying the wrong property and reading the result as
coverage* is this estate's most repeated failure, and this is the version of it that
hides inside a correct-looking cryptographic guarantee.

---

## "This path doesn't have failure mode X" is a claim about the PATH — it silently becomes a claim about the TOOL (2026-08-14)

**Problem**: The contracts check was deliberately built on `validate_contract_a.py`
because it reads FluxusSource's directory **directly**, which structurally eliminates
`drift.strip_list_vs_observed_keys` — a dependency on a hand-maintained strip list
that the *other* validator has, because it reads NexusMind's mutated copy. The
reasoning was correct and was recorded in the design.

**It was true of the path and not of the script.** Nothing stopped
`--input data/raw/…`. Pointed at a mutated file, the check reported a single class,
`additionalProperties.<root>`, over 3,697 rows — **and that class could not
distinguish the deliberately-held control (`source_group`) from seven NexusMind
stamps**, i.e. from the check having been aimed at the wrong directory entirely.

⭐ **A held control and a misconfiguration rendering identically — inside the
artefact whose entire job is to stop a reader over-reading a result.**

**Fix** (NexusMind, on implementing it): `additionalProperties` now fans out **one
class per unexpected key** (`additionalProperties.<root>.source_group`), and the
check **detects its own stamps in the input and refuses with `could_not_run`** rather
than blaming the producer.

**The generalisable form**: ⚠️ **eliminating a failure mode STRUCTURALLY and
eliminating it BY CONVENTION look identical in a design note.** The dependency
removed by choosing the right input directory came straight back as an *unenforced
precondition on the input argument*. If a design claims a failure mode is impossible,
ask what enforces it — and if the answer is "we pass the right argument", it is
convention wearing structure's clothes.

*(Found only by running it against the wrong directory on purpose. Reading the design
would not have surfaced it.)*

---

## A HANDOFF IS INVISIBLE FROM THE SENDING SIDE, BY CONSTRUCTION (2026-08-14)

**Problem**: Across one day of five parallel sessions, the same defect appeared in
this session's work **three times**, and a peer caught all three: the unit names a
reader needed, the post-install flag flip only the installer could trigger, and a
"frozen" declaration on a file with no version control. Each was one line of
information whose absence broke a distinction nothing else could make. Each was
dropped for being **too small to look like work**.

**The framing that explains it** *(pipeline-atlas, and it is better than "a blind
spot in my attention")*: **all three were HANDOFFS, and a handoff is invisible from
the sending side by construction.** The sender knows the fact, so *the system
containing the sender and the fact looks complete*. It is only visibly incomplete
from the receiving end — the half that does not have it.

**The mirror held, which is what makes it a property rather than a personal failing.**
The same peer reported a peer's branch commit as "shipped" from a relay they had not
verified — the identical error from the other side, caught within the hour.

**Fix**: ⭐ **Take the mechanism out of a person's memory.** Prefer the durable form
every time it is available: commit the file rather than quote its hash; write the
handoff into a definition of done as its own numbered item rather than mention it;
tell the party who will act, not only the party who will read. **A fact recorded in
version control is a handoff that survives both parties closing their session.**

**Corollary for review**: this is *why* parallel independent sessions find things at
all. Neither side is more careful; they are differently positioned. A defect that is
structurally invisible from where you sit is not found by looking harder.

---

## Detection is path-scoped, the action is repo-wide — so deploy time is unrelated to merge time (2026-08-14)

**Problem**: NexusMind's standing note said a merge to `main` becomes a production
change on the next 4h tick, because `nexusmind.service` runs `deploy_filters.sh` as
`ExecStartPre` every cycle. The mechanism is real — verified running, exit 0. **But
the auto-pull is gated on `git diff --quiet HEAD origin/main -- "${SCORER_PATHS[@]}"`**,
and `SCORER_PATHS` is only `filters/`, `src/filters/`, `src/scoring/` and three
deploy files. A branch touching `contracts/`, `scripts/`, `src/utils/` or `tests/`
matches none of them, **so merging it deploys nothing.**

**Live confirmation, not inference**: sadalsuud's checkout sat at `b115fda` while
`main` was `010338d` — already one merge behind, because that merge was docs-only.

**The hazard is the asymmetry, not the gap.** The gate asks *"does the scorer tree
differ?"*; the remedy is `git pull --ff-only origin main`, which fast-forwards **the
entire repository**. So every non-scorer change accumulated since the last pull —
pipeline code, enrichment, contracts — **ships silently, bundled, at whatever moment
an unrelated filter change happens to land.** Its deploy time is unrelated to its
merge time and nobody is watching.

**Corollary, and the part to carry**: ⚠️ **"sadalsuud is on commit X" tells you when
a SCORER change last landed, not what pipeline code is running.** Never reason from
*"it is merged, therefore it is running."*

**General form**: a mechanism that appears to cover a class of change, is trusted to,
and is **structurally scoped to a subset** — while its remedy is not. Sibling of the
`origin/main` entry below: both answer confidently about a different question from
the one asked. *(Found by the NexusMind session while checking whether its own branch
would deploy; recorded here because five sessions were reading each other's repos.)*

---

## `origin/main` is a CACHED answer with no staleness indicator (2026-08-14)

**Problem**: Checking whether a sibling repo (`energydatahub`) was still publishing
its daily result artefact, two sessions independently read
`git show origin/main:data/data_quality_report.json` and found a timestamp **five
days old**. The obvious reading — the upstream has stopped publishing, and `augur`'s
consumer has been silently proceeding on stale data every day since — was about to be
written up as a live cross-repo incident.

**It was false.** `.git/FETCH_HEAD` was *also* five days old: the clone had not been
fetched. `git ls-remote origin refs/heads/main` returned `b5188df` against a local
`origin/main` of `7a27eae`. **The remote had moved the whole time.** A stale clone,
not stale data.

**Fix**: `git ls-remote` is the thing that actually asks the remote. `origin/main`
answers from cache.

**Why it fools you**: it is *named after the remote* and reads exactly like a remote
query, but it silently reports the last fetch — so it answers **confidently about a
window that ended days ago**. Same class as two rules already here: `pgrep -f` (3rd
occurrence) matching the shell carrying the pattern, and `systemctl show` on a
**nonexistent** unit exiting 0 with `ActiveState=inactive, Result=success`,
byte-identical to a real stopped unit.

**The general form**: ⚠️ **a source that cannot say "I don't know" will say something
else.** When a read decides whether you raise an alarm — especially about another
team's repo — establish the source's own freshness before believing its content. A
cached answer and a current one are byte-identical by construction.

*(Found while sweeping for contract validators; the artefact being checked was a
precedent this repo was about to copy. Peer-confirmed by the pipeline-atlas session,
who had hedged the claim and was right to.)*

---

## The failures were never where the author was looking — and every one was a hand-built population (2026-08-12)

**Problem**: A four-repo investigation into NexusMind#292 ran across ~10 exchanges
between four sessions. **Every quantitative claim any side made failed under
checking** — and not one failed where its author was looking. Catalogue, mine and
the peer's alike: a stage-mix figure retracted because `stage_used` is per-filter
not per-article (found by auditing an own assumption, not by the adversarial lens
aimed at it); a Google News mechanism claim over-generalized from one fetcher to a
URL scheme (refuted by a repo nobody thought to ask, after it had already
propagated into that repo's issue as a premise); an op-point resolver that returned
`None` and printed `visible% = 0.0` for every cohort, caught only because all-zero
was implausible; an "ADR-022 does not exist" correction produced by running
`ls docs/adr/` in the wrong repo, where a populated directory made the wrong answer
look right; a survival rate whose numerator and denominator had different exclusion
lists; and a counterfactual replay over stored rows presented as an observed
attrition rate.

**Root cause**: In every case **the object checked and the object that was wrong
were different objects**, so no amount of care applied to the first could reach the
second. The common structure underneath: **each error was a hand-built population.**
Someone chose a file, a window, a join key or a directory, and the choice — not the
arithmetic — carried the defect. Care concentrates on the arithmetic because that is
what looks like the work.

**Fix**: Prefer a population the pipeline already computes to one you construct.
The worked example: NexusMind's scorer logs
`Loaded 4577 articles (skipped: 114464 processed, 17845 commerce, 3232 obituary,
22472 dup-url, 3442 dup-title, 140870 old, …)` **every cycle** — it already
decomposes the aggregate by mechanism and throws it away. Stamping those skip
reasons with the article's language answers #292 continuously and retires the whole
probe genre. **The one thing nobody got wrong was the log line, because nobody built
it.** Corollary when you must build one: a documentation surface that is right 83% of
the time (config.yaml matched runtime on 5 of 6 filters until 2026-08-12; 6 of 6
since) is the same hazard as a
field that is article-level 99.9% of the time — **make the missing case raise, never
return `None`**. The original defect was not reading the wrong file; it was that the
wrong file failed silently. Related: [[feedback-rate-needs-population]],
[[feedback-enumeration-is-not-inventory]].

**Verified op-points, extracted from every deployed filter's `base_scorer.py` —
the SOLE runtime source, per `production_scorer.py:142` reading
`base.TIER_THRESHOLDS`** (2026-08-12, cross-checked by two sessions):
`solutions 2.25 · uplifting 4.5 · cultural_discovery 4.0 · investment_risk 4.25 ·
belonging 4.0 · nature_recovery 3.75`. `config.yaml` agreed on 5 of 6 at the time of measurement, 6 of 6 after the same day's fix;
`cultural_discovery` v5 had no `tiers:` block at all (added 2026-08-12; **v6 still
lacks one — add before cutover**).

## An instrument chosen to avoid a known bias is not thereby unbiased (2026-08-12)

**Problem**: FluxusSource's mojibake detector reported 7 live positives, which looked
like exactly the residual collection-stage corruption their own docs predict. **All 7
were false.** The firing rule is: any character whose MacRoman byte lands in
`0xC2–0xF4` (a UTF-8 *lead* byte) immediately followed by one in `0x80–0xBF` (a
*continuation* byte) forms a structurally valid 2-byte sequence, and the detector's
"repair" rewrites it into a foreign script. Their `upstream_mojibake` health list
consequently **cannot be quoted in either direction**, and had been naming seven
innocent publishers.

⚠️ **The first characterisation of this class — including mine here, and the issue
author's — was TOO NARROW, and that is the second lesson.** It was recorded as
"apostrophe-elision before an accented vowel in French and Italian", from the worked
example `l’éclipse` → `lՎclipse`. The real class is **48 lead characters × 64
continuations = 2,030 firing pairs**: `«` `»` `—` `“` `…` `€` `√` and NBSP are all
leads; every accented lowercase vowel plus `°` `µ` `©` `™` `≤` are continuations. The
second worked example is a non-breaking space before a degree sign — `121\xa0°C` →
`121ʡC`, found on a `pubmed` row — which is scientific units, not orthography, and no
amount of thinking about French would have reached it.

**Why the narrow reading looked complete:** it came from a 51,640-row window that
happened to contain *only* apostrophe cases. The wider class surfaced only when a
second repo ran the same detector over 21,174 **stored** rows, and a third scan
covered 208,153 rows of history. Same instrument, same defect, three sample shapes —
the first could not have shown the second trigger. **A characterisation of a defect
inherits the shape of the sample it was found in, and reads as complete regardless.**
That is the same failure as [[feedback-rate-needs-population]], applied to a *defect
class* rather than to a rate.

⚠️ **There is NO validated fix.** The obvious guard — reject any repair that
introduces a foreign script — scores 6 of 8 and fails in *both* directions: it
rejects genuine emoji repairs on the variation selector, and it accepts `121ʡC`
because U+02A1 is a Latin lowercase letter by name and category. FS#167 is open, not
pending.

**Root cause**: The instrument was chosen *specifically* to avoid a bias its authors
had correctly reasoned about — the module docstring rejects a marker list because `Ã`
is ordinary Portuguese and `√` ordinary maths, noting that "a marker heuristic fires
hardest exactly where the false positives are." The round-trip replacement adopted
instead has its **own** version of that failure, relocated from Portuguese to French
and Italian. **Having reasoned carefully about bias A is what makes bias B invisible**:
the design conversation is over, the instrument feels earned, and nobody re-opens it.

**Fix**: When an instrument is justified by *what it avoids*, that justification is not
evidence about what it does. Ask separately "where does THIS one fire hardest?" and run
it against the population where its own mechanism is most likely to misfire — here, any
language whose orthography puts a high byte next to an accented vowel. Corollary for
consumers: a detector's output is not evidence until someone has stated its false-positive
mode, and "0 found" and "7 found" need that statement equally. Related:
[[feedback-claim-requires-verify]] and the standing rule that a negative needs a positive
control — this is its mirror, a *positive* needing a negative control.

## The audit never scanned the file that is auto-loaded every session (2026-08-13)

**Problem**: `/audit-context` step 4 checks `CLAUDE.md`, `memory/MEMORY.md` and
`memory/gotcha-log.md`. It does **not** check the **user-level auto-memory index**
(`~/.claude/projects/<slug>/memory/MEMORY.md`) — which is **auto-loaded into every
session**, is larger than the in-repo index it shares a name with, and whose pointers
all name repo files. A curate pass found **three dead pointers in it**:
`project_session_2026_08_01.md`, `_02.md` and `_03.md` were never committed, and two of
them had obvious renamed targets sitting beside them (`_01_afternoon.md`,
`_03_evening.md`). One (`_02`) has no repo file at all, so its summary in the index is
the **only surviving record** of that session.

Two audits the same day reported the reference check clean.

**Root cause**: the two files share the name `MEMORY.md`, and the skill's own Step 1
warns they are different artifacts — but Step 4's document list was written against the
*repo* one and nobody re-read Step 1 while editing Step 4. The check was not wrong
about what it examined; **it was examining the wrong set**, and a clean result over the
wrong set is indistinguishable from a clean result. Same shape as `filtered_*.jsonl`
being 100% passers: the instrument worked, the population was wrong.

**Fix**: `refcheck.py`'s `DOCS` now includes the auto-memory index by absolute path,
guarded by `exists()` so it degrades on a machine without one. It immediately paid for
itself — the widened scope caught two further dead names in the *correction text I had
just written*. **Generalisation: when a check names its own inputs, the input list is a
hand-built population too** — audit it on the same schedule as the thing it checks, and
ask "what is loaded that this does not read?" rather than "does this pass?".
Related: [[feedback-hand-built-population]].

## Repair needs a detector; re-derivation needs nothing — prefer the clean upstream copy (2026-08-13)

**Problem**: Four sessions spent most of an evening making a *repairer* safe. ovr.news
had ~474 stored rows with mojibake and planned to fix them in place. That requires a
**detector**, because a repairer must decide which strings were corrupted — and the
detector is where the entire false-positive class lives (2,030 `mac_roman` pairs, of
which `l'éclipse → lՎclipse` destroys correct French, Greek and Portuguese prose
irreversibly). We built candidate classes, arm independence, a pair requirement, a
signature conjunction and a hand-review residue, all to make a **guess** safe enough
to run.

**Root cause**: nobody asked whether the guess was necessary. **A clean copy of every
corrupted row existed one hop upstream** — NexusMind stores `original_content` per
article (`src/enrichment/article_fetcher.py:840`), FluxusSource's text, measured
0.000% corrupt and confirmed through a three-round challenge. The owner's framing:
*repairment should not be necessary; if it is, there are bugs upstream.*

**Fix**: **When a clean upstream copy exists, RE-DERIVE — never repair.** Re-derivation
has **no false-positive class at all**, because nothing is inferred: there is no path
from copying a clean string to `lՎclipse`. Two conditions make it the practical answer
as well as the correct one, and both must be checked:

- **The upstream fault must be fixed first, or re-derivation is a treadmill.** NM#338
  landed (raw bytes to trafilatura instead of `.decode(resp.encoding or "utf-8")`),
  which is what bounds the set and makes the job terminate.
- **Check for irreversibly lossy damage, which re-derivation is the ONLY cure for.**
  Mojibake is a reversible byte-level mis-decode; **U+FFFD has thrown the bytes away**
  and no repairer could ever recover it. Measured here: 4 of 21,316 rows, and 0 of 160
  cache rows — near-empty, but it was the one finding that could have made
  re-derivation insufficient rather than merely better.

The detector work is not wasted: it becomes the **verification** step ("did the
re-derived text come back clean?"), where a false positive costs a second look instead
of a destroyed row. Same instrument, consequence of being wrong drops by a category.

## Consolidating onto one path deletes redundancy that was silently ERROR-DETECTION (2026-08-13)

**Problem**: NM#339 decided to consolidate enrichment into NexusMind's `pre_enrich` and
delete ovr.news's independent pass. **That routes every article through the decoder
that had the NM#338 charset bug** — and nobody in the four-session thread, including
me, checked that path's correctness before agreeing to consolidate onto it. It had been
fixed hours earlier, so the decision held **by luck of timing**.

**Root cause**: the duplication was being argued about as *waste*. It was also, without
anyone designing it that way, a **cross-check**: while two independent fetchers decoded
the same articles, a fault in one was partly masked *and partly revealed* by
disagreement with the other. NM#338 was found precisely by pairing NexusMind's enriched
text against a second copy. Remove the second path and the same fault reaches every
article with nothing downstream positioned to notice.

**Fix**: **"Consolidate onto path X" is a bet on X's correctness — state it as a
precondition, not an assumption.** And when removing a redundant path, ask what it was
incidentally detecting, then replace that with a *standing* probe rather than a
one-time verification. Here the cheap one already exists: the U+FFFD count is **4**,
and 4 is exactly the number that moves if the surviving decoder regresses. Generalises
past encodings — any "we do this twice, let's stop" should name what the second copy
was catching before it goes.

## A verified quantity carries an unverified PASSENGER — and the sixth kind is a SCOPE (2026-08-12)

**Problem**: Six times in one session, across four repos, a correctly-measured number
shipped with an unmeasured claim attached, and the measurement's credibility carried
the passenger. The passenger is what turned out to be wrong every time.

| the verified quantity | the passenger it carried | passenger type |
|---|---|---|
| `pre_enrich` attempted 35,229 GN rows, replaced 0 | "a property of the URL scheme, so no fetcher change moves it" | **mechanism** |
| cd's `tiers:` block is absent | "so adding it is documentation only" | **consequence** |
| `_find_latest_version()` serves the highest `vN` | "so the deploy and the cutover are the same keystroke" | **step count** |
| ovr enriched 38 published articles | "so ovr rescues what NexusMind missed" | **valence** |
| the round-trip inverts a mis-decode | "so it would not have the French false positives" | **discrimination** |
| deriving the class fixes the cp1252 blind spot | "so deriving is the structural fix" | **SCOPE** |

**Root cause**: The measurement is the part that got attention, so it is the part that
is right — and its correctness is then read as covering the sentence next to it, which
nobody measured at all. **The sixth is the one worth naming separately: a result true
of one ARM, one CODEC, one FILTER, one FETCHER, stated for all of them.** Deriving the
character class fixed coverage on the arm the author was blind to (`cp1252`) *and
simultaneously manufactured false positives on the arm they thought they had already
fixed* (`mac_roman`, where the derived leads contain `’` at 0xD5 and the derived
continuations contain `é` at 0x8E). Their narrow hand-written v1 was roughly right **by
accident** — a narrow class costs coverage *and* buys precision, and nobody had noticed
it was doing both.

**Fix**: When a number and a claim ship in the same sentence, **say which one was
measured** — and for a scope passenger, name the population the measurement covered:
*"verified on the cp1252 arm; untested on mac_roman"* is one clause and it is the whole
fix. Note that "name the population" is **already a rule here and did not fire on any
of the six**, because it reads as being about denominators; it needs to be understood
as covering arms, codecs, fetchers and filters too. Two of us took two hops to notice
the sixth. Related: [[feedback-hand-built-population]],
[[feedback-claim-requires-verify]], and the four adjacent entries below.

## A 6-row denominator gap was the visible end of three defects, none visible in the number (2026-08-12)

**Problem**: A peer's cross-repo measurement (NM#338) reported English 130/10,312 and
non-English 993/13,332 against a stated total of 1,123/23,638. Every percentage was
internally correct and the numerators summed exactly — but **10,312 + 13,332 = 23,644**,
six rows more than the total. I had quoted the pair as consistent in a session record
and a pushed commit message. Queried it during `/review-changes` as a small
reconciliation nit. It was the visible end of three defects:

1. **A sliding `[-N:]` glob is not a fixed population.** The total and the split were
   separate invocations minutes apart; new cycle files landed between them, so the two
   commands measured two different file sets. That was the six rows.
2. **`sorted(glob("data/filtered/*/filtered_*.jsonl"))[-40:]` sorts by PATH**, which
   groups by directory — so it selected **40 files from one filter and nothing else**,
   not "the last 40 cycles" as documented. Sort by basename for a cross-lens window.
3. **The detector was blind to 83% of its population.** Its continuation class was
   hand-written `U+0080–U+00BF` — correct for latin-1, which renders bytes `80–9F` as
   C1 controls — but **cp1252 renders those same bytes as printable punctuation**
   (`U+2019`, `U+20AC`, `U+201C`), so every smart-quote corruption was invisible.
   Corrected, the blind arm was the larger one: cp1252 1,210 vs mac_roman 256.

Corrected figures moved *every* direction the wrong way: introduced 4.751% → **5.639%**,
non-English/English ratio 5.91× → **6.86×**. And a figure I had routed onward as "the
cleanest confirmation anyone produced" — a clean 0.000% for the upstream repo — became
**0.081%**.

**Root cause**: All three are the same mistake in different clothes: **a population or
a class assembled by hand, then trusted as if derived.** A glob evaluated twice is two
populations; a sort key chosen by convenience is a stratum, not a window; a character
class typed out is a *guess at* a codec rather than the codec. None of the three is
visible in the output — the numbers looked fine, and two of them were even
self-consistent.

**Fix**: **Re-derive the number; do not inspect it.** The gap was found by recomputing
the arithmetic, not by reading it — and the arithmetic was the *only* one of the three
defects that surfaced that way, with the other two found by pulling the thread.
Concretely: pin a window before measuring (never a sliding `[-N:]`), state the sort key
when a glob is a sample, and **derive character classes instead of writing them** —
`bytes(range(0x80,0xC0)).decode(codec)` *is* the continuation set by construction and
cannot drift from what it models. ⚠️ **Scope that correctly: derivation fixes COVERAGE,
not discrimination, and it is codec-specific.** Verified 2026-08-12 — for `cp1252` the
derived classes exclude the `’`+accented-vowel pair (so deriving fixes that arm, which
was the blind and larger one); for `mac_roman` they CONTAIN it (`’`=0xD5 is a derived
lead, `é`=0x8E a derived continuation), so a derived candidate stage plus a round-trip
**reproduces FS#167 exactly**. Deriving is how those 2,030 pairs were enumerated. The peer's generalisation is the keeper: **hand-built
populations and hand-built character classes are the same failure with different
nouns.** Related: [[feedback-hand-built-population]], and the entry below on reasoning
about an encoding instead of running it.

## Asserted a mechanism made a DESTRUCTIVE operation safe, without running the one line that tests it (2026-08-12)

**Problem**: FS#167 records that a mojibake detector's positives are false — a "repair"
turns correct French into Armenian (`l’éclipse` → `lՎclipse`) — which is why ovr#291,
a repair pass over ~474 stored rows, is blocked. On hearing that NexusMind's detector
"confirms each candidate by reversing the mis-decode", I wrote to FluxusSource that
**"a round-trip confirmation would not have the French/Italian false positives at all,
because `l’é` does not survive `encode('mac_roman').decode('utf-8')` as a different
valid string"**, and concluded *"if it holds, ovr#291 becomes safe to run."*

**It survives. 5 of 5, measured in one line after the peer pushed back:**
`'l’éclipse solaire'.encode('mac_roman').decode('utf-8')` → `'lՎclipse solaire'` —
different, valid, wrong. Also `cos’è`→`cosՏ`, `l’âme`→`lՉme`, `121\xa0°C`→`121ʡC`.
**The round-trip IS the operation that produces the false positives**, so it cannot
possibly detect them.

**Root cause**: I reasoned about an encoding mechanism from a plausible story instead
of executing it, on a claim whose consequence was authorising an **irreversible write
to production data**. The story was appealing because it explained a real distinction
(round-trip beats marker lists) — it was just the wrong half. **NexusMind's detector is
safe because of its CANDIDATE-GENERATION stage** (`’` is not in the marker set
`Ã â √ ‚ ¬`, so it never becomes a candidate), **not because of its round-trip stage**,
which is what I credited. I inverted which half does the work.

**Fix**: **A claim that unblocks a destructive operation is the last place to reason
from a story.** Run it — this one cost four lines and thirty seconds, and I sent it to
another repo instead. Two durable rules: **safety here is a CONJUNCTION** — an
unambiguous signature *and* a clean inversion, then hand-review the residue; a single
test in either position is not a detector. And when relaying a mechanism between repos,
**state which stage carries the safety**, because "their detector is round-trip based"
is true and, taken alone, licenses exactly the destructive run it appears to authorise.
The routing chain caught this — FluxusSource re-measured rather than acting — which is
the argument for sending mechanisms with their evidence rather than as conclusions.
Related: [[feedback-claim-requires-verify]], [[feedback-hand-built-population]].

## Conceding a correct conclusion because a neighbouring sentence was refuted (2026-08-12)

**Problem**: I recommended *"don't fix the Google News resolver — it is a workaround
for a source under retirement"*, and attached a mechanism claim to it: *"a property of
the URL scheme, so no fetcher change moves it."* A peer refuted the mechanism claim
with a measurement (ovr.news resolves those URLs and enriched 74 of 103). I then
**withdrew the whole recommendation**, called it "the dangerous kind of wrong", and
corrected it in six files. Hours later the owner decided exactly what I had originally
recommended — Google News is being retired, so the resolver is explicitly **not**
being ported upstream (NM#339).

**Root cause**: The two sentences arrived together and were refuted as a unit, but the
conclusion never *rested* on the refuted premise — it rested on the retirement, which
was untouched. Two things made the over-retraction feel correct at the time: the
refutation was well-evidenced, so deferring to it felt like good practice; and I had
just been caught over-generalising, which primed me to concede rather than separate.
**Being wrong about X raises the felt probability of being wrong about adjacent Y**,
and that feeling is not evidence.

**Fix**: When a supporting claim is refuted, **name what the conclusion actually rests
on before withdrawing it.** One line: "does this conclusion survive if the refuted
claim is simply deleted?" Here it plainly did. Retract the false sentence, keep the
true one, and say explicitly which is which — a peer correcting your mechanism has not
thereby corrected your recommendation, and treating it as though they have hands them
a decision they did not make and cannot see the grounds for.

**The symmetric failure, named by the peer who committed it in the same exchange:**
*when you REFUTE a supporting claim, check whether you have actually touched the
conclusion.* They took down the mechanism sentence and then argued as though the
recommendation had fallen with it — and spent hours measuring a capability into
significance on the strength of a point that was never load-bearing. **Same joint,
opposite directions: one side over-retracted, the other over-claimed**, and the actual
load-bearing premise (the source is being retired) went untouched and unexamined by
both until the owner stated it plainly.

**A third shape fell out of the same thread and generalises further: a count that is
invariant under a relabelling of what it counts.** ovr's 38 enriched-and-published
articles were read as "rescues NexusMind missed"; the same rows are equally "boilerplate
NexusMind deliberately refused" — consent walls and paywalls that ovr accepted because
its only test is *longer than what I had*. **No aggregate distinguishes the two, because
the relabelling does not change the number** — only inspecting individual rows does. When
a count is doing argumentative work, ask what else those same rows could be called.

Related: [[feedback-claim-requires-verify]], [[feedback-hand-built-population]]; the
mirror of the endorsement entry below — there I under-checked agreement, here I
over-accepted refutation.

## A loosened check must be tested on what it newly PERMITS, not on what it preserves (2026-08-12)

**Problem**: `/audit-context` step 4's reference checker gained v1.23.0's
`<!-- placeholder -->` skip — a deliberate loosening, so that paths never meant to
resolve stop being re-triaged every audit. The existing sensitivity harness passed
**12/12 immediately after the port**, which read as "the change is safe". It was not.
Seeding the failures the loosening *newly permits* found **two defects in the port**
within one run: `PATH_RE` did not admit `<` or `>`, so angle-bracket placeholders
(`filters/<name>/<version>/config.yaml`) were **never extracted at all**; and the
stale-marker check tested the *bracketed* string, so a real path merely wrapped in
`<>` resolved as an intentional placeholder instead of being caught as a mislabel.

**Root cause**: A harness written before a change tests the behaviour that change was
designed to **preserve**. It is structurally incapable of testing what the change
**permits** — that surface did not exist when the cases were written. So a green run
measures *specificity* and says nothing about *sensitivity*, while looking exactly
like a safety proof. The first defect is the more dangerous shape: a path the
extractor never captures is **not reported**, and "not reported" is indistinguishable
from "checked and fine". A skip that silently does nothing is the precise failure the
whole step exists to prevent, reintroduced by the mechanism meant to prevent it.

**Fix**: When loosening any check, **write the new cases before trusting the old ones**
— one per way the loosening can now hide a real defect. Here: a marker on a path that
*does* resolve (both marker forms), a marker covering no path at all, and an unmarked
break sharing a line with a marked one. Harness went 12/12 → **18/18**. Two related
rules earned the same day: **a straight swap of a shared instrument can be a
regression** — replacing our adapted `refcheck.py` with upstream's lost a local
class and re-reported 33 `config.yaml` matches as collisions, so the feature was
*ported* rather than swapped; and **zero findings is not the target** — a change that
drives a check to zero has probably disabled it. Related:
[[feedback-hand-built-population]].

## Endorsing a peer's number suppresses the re-check that would have caught it (2026-08-12)

**Problem**: A peer session sent a cross-repo measurement — "41.5% of English rows
reached `stage2` vs 31.2% of non-English" — and I replied that it was *"a better
catch than the warning I sent you"* and built a recommendation on it. They retracted
it themselves an hour later: `stage_used` is **per-filter, not per-article**, and
differs across the six filters on 2,679 of 3,271 rows (82%). The figure was a
`solutions`-only number wearing an article-level label; corrected per filter the gap
holds for `solutions` alone and **reverses** in `cultural_discovery`, `belonging` and
`nature_recovery`.

**Root cause**: Two mechanisms, and the social one is the one without a guard. The
technical error is the familiar shape — a field that exists, is populated, and means
something different per row, exactly like `content_length` and
`raw_weighted_average` before it. The new part is that **praise is a suppressor**:
the peer named it themselves — *"'better catch than the warning I sent you' is exactly
the kind of endorsement that stops a number being re-checked."* A number I have
publicly agreed with is one I am now motivated not to re-examine, and my agreement
travels to everyone downstream as independent corroboration when it is nothing of the
kind. Nothing in the review battery covers a claim arriving from outside the diff.

**Fix**: **An endorsement carries the check that would falsify it, or it is not an
endorsement.** When agreeing with a peer's measurement, state in the same message what
would have to be true for it to be wrong and whether that was tested — "this is right
*if* `stage_used` is article-level; was that checked?" costs one clause and is the
entire fix here. Corollary for the receiving side: treat an incoming agreement as
zero new evidence, because a peer agreeing with your number has usually not
re-derived it. Related: [[feedback-claim-requires-verify]], and the standing rule
that a field's existence says nothing about what it means per row.

## A comparison harness whose treatment arms went to zero still prints a table (2026-08-12)

**Problem**: `scripts/gate/measure_enrichable_rate.py` (the FS#120 enrichable-rate
harness, gate due ~2026-08-14) compares three eval aggregator arms against a
`gn_proxy` baseline. `arm_of()` prefix-matches `FAMILIES = ("gnews_eval",
"newsdata_eval", "gdelt_constructive")` against `source`; anything unmatched
returns `None` and is skipped, and `fams` is built from *what was found*. So if the
arms stop producing rows, the harness drops them, prints the baseline alone, and
**exits 0**. Nothing distinguishes "the treatment is gone" from "the treatment
measured nothing".

**Measured, and it is not hypothetical**: on sadalsuud, `data/filtered/solutions/`
(85 files, 2026-07-29..08-12) has all three families producing rows every day from
07-31 to **08-08** — then **zero from 08-09 onward, all three at once**. The
silent emptying had already happened four days before anyone looked, with the gate
two days out.

**Cause, resolved the same evening across two sessions — and it was OURS, not
upstream.** My three candidates (ADR-007 retirement, free-tier expiry, a
FluxusSource#163-shaped silent skip) were **all excluded by FluxusSource from their
own health snapshot and logs**: collection ran continuously, `total_failures: 0`,
`consecutive_skips: 0`, and the two API arms had `total_zero_yields: 0 across 38
runs`, last yield **2026-08-11T14:06Z** — two days *after* my boundary. They
emitted 92 rows on 08-09 and 122 on 08-10 while my table read zero. So the break
was downstream of them, and this side found it in one query: the arms **do** reach
`data/raw` on 08-09..08-11 (`source_type: api`), and since **2026-08-08 07:43** all
six live filters exclude `eval_aggregator` (NexusMind `9fb441a`) — exactly these
arms' `type_classification`. They are collected, ingested and **scored**, then
dropped by the NM#189 source filter, so they never enter *any* lens store.
Changing `--lens` recovers nothing.

**The exclusion is correct and deliberate** — the arms are an A/B measurement rig,
not a content source, and before it they were published: 30 rows in ovr.db
including a funeral/murder story at tier `high` (llm-distillery#101). Nothing is
broken. **What broke is the instrument, by a deliberate fix to the thing it
measures.** ADR-007's retirement (`eda28eb`, in production 2026-08-11 16:56 CEST)
is real but arrives *after* the boundary, so it is the second cause, not the first.

**The stale comment that would have sent the next reader the wrong way**: this
script's `--lens` help said solutions is the default *because* "its
`excluded_source_types` match nothing that exists, so its store drops no rows
(measured 2026-08-06)". True when written, falsified by our own change 48 hours
later, and it is precisely the "a comment explaining why code is safe is a claim
like any other" trap. Both that rationale and a second stale claim in the same
docstring (`content_length` is never persisted — fixed 2026-08-08 17:10) are now
corrected in place with their expiry dated.

**Fix**: the harness now names every empty arm before printing anything, and
**refuses with exit 2** when all arms are empty rather than presenting a
baseline-only table. A partial emptying warns and continues, because a partial
comparison is still meaningful.

**Proven, not asserted** — three fixtures, run end to end, outcome printed each
time: all arms present → silent, exit 0 (**presence control**: the pooled table
still prints, so the guard is not just always-quiet); one arm missing → names
`gdelt_constructive`, warns PARTIAL, exit 0; all arms missing → refuses, exit 2.

**How it was found**: a peer session checked my clean grep result instead of
recording it, ran a **positive control** on the same tree, and noticed my pattern
only matched string literals inside `startswith(` — a tuple-driven prefix match was
structurally invisible to it. Their own first attempt had pointed at a path that
did not exist and returned a clean-looking negative. Two lessons in one exchange:
**a grep for a pattern is not a grep for a behaviour**, and **verify a negative
with a positive control on the same instrument**, because a mis-aimed search and a
true absence are the same output.

**Belongs to the unreachable-mechanism catalogue below** as its inverse: not a
mechanism that never runs, but a mechanism that keeps running after its *input
population* disappears. Same tell — the output still looks like a result.

---

## Two defects cancelling presented as correct behaviour, and this repo's data depended on it (2026-08-12)

**Problem**: FluxusSource#164 — archive retention is configured 730 days, the code
reads a different path so 90 is what runs, and the purge that would enforce 90 is
itself broken, so **nothing has ever been deleted**. 1,469 archives intact, 253 days
/ 1.2 GB against 395 GB free. Two llm-distillery dependencies were living on that:
the obituary detector *must* train on raw ingest (its README — obituaries are what
the filters remove), and `docs/RUNBOOK.md:187` names the historical harvest as the
route a needle filter reaches the 200-row normalization floor. `nature_recovery v4`
sits at 397 rows today.
**Root cause**: The archives *are* the raw harvest (`content_items_*.jsonl` inside
each tarball). Fixing **either** defect alone would have silently destroyed
everything past 90 days — and the `.suffix` half looks exactly like a one-character
typo fix.
**Fix**: Owner chose deletion of the purge loop over repairing the config (my
suggestion, withdrawn — "documented as broken" is the state that invites the next
person to repair it and fire it). FluxusSource's `tests/test_no_archive_purge_164.py` at
91/365/731/5000 days; ADR-003 amended naming both consumers.
**Durable lesson**: my register said *verify a mechanism actually runs*. It did not
say **verify that a mechanism NOT running is what is protecting you.** Two bugs can
cancel into apparently-correct behaviour, and the more innocuous the repair looks,
the more dangerous it is. Nobody would have caught this from here: the failure mode
was a retrain coming up short months later with no visible cause. Found by a peer
session reading its own config, not by anyone auditing my dependencies.

## A nested-path mistake and a dead stamp have the identical symptom (2026-08-12)

**Problem**: Told the enrichment strata were flagged at `analysis.pre_enriched`, I
read that over 1,070,665 production rows, got **0**, and nearly reported a second
NM#300 — a stamp claimed to label strata reaching zero rows.
**Root cause**: The flags live at `nexus_mind_attributes/<lens>/pre_enriched`;
`filtered_*.jsonl` rows have no top-level `analysis` key at all. `analysis` is a
*local variable* in NexusMind's `main.py`, persisted under a different key — the peer
had quoted the variable name as if it were the schema.
**Fix**: Verified the path before reporting. The flags are populated and fine.
**Durable lesson**: **a wrong path and a dead field both read as zero, and the wrong
one is the more exciting finding** — which is exactly the pressure that gets it
published. Before reporting an absence, dump the keys that *are* there. This repo
already carried `metadata.quality` is not
`nexus_mind_attributes.<lens>.source_quality`; same trap, other direction.

## A ported vocabulary value left `main` red, and the file that needed updating says so in a comment (2026-08-11)

**Problem**: `main` failed `tests/unit/test_filter_config_schema.py` from the midday
session until the afternoon's `/curate` ran the suite. `proxy_aggregator` was ported
into `investment_risk v6`'s `source_filter` but never added to `KNOWN_SOURCE_TYPES`.
**Root cause**: The port and its validating gate live in two files, and only one was
edited — even though `KNOWN_SOURCE_TYPES` carries the instruction *"When FluxusSource
adds a new value, add it here in the same PR to keep the gate in lockstep."*
**Fix**: Added `proxy_aggregator` with its provenance. **Run the suite at session
close, not only before a commit that touches code** — this was found by `/curate`
running tests on a docs-only working tree, and nothing else that day would have.
**Durable lesson**: a comment prescribing a cross-file lockstep is not a mechanism;
it is a hope. The same session that logged *"a comment explaining why code is safe is
a claim like any other"* was two commits from this.

## An early return before the logging boundary makes a refusal indistinguishable from no-attempt (2026-08-11)

**Problem**: Two articles that ovr.news should have enriched had no row in
`enrichment_errors` and no upstream-enriched flag, so nothing could say whether
enrichment ran and refused, or never ran. Chased across both repos before the answer
came from reading the branch (ovr.news#312).
**Root cause**: `enrichment.ts:154-167` returns on an unresolvable Google News URL
*before* the fetch, the skip-domain check, and the `try/catch` that calls `logError`.
The only output is an unpersisted debug line. Three other early returns in the same
function share the shape.
**Fix**: ours is to look for it — an early return that precedes the error-logging
boundary is a silent path by construction, and the refusal is invisible **at exactly
the inputs that trigger it**, which are the ones any investigation selects.
**Durable lesson**: when a guard *declines* to act, ask where the decline is recorded,
not whether the decline is correct. Sibling of NM#314's argument that unrecorded
refusals make a whole failure direction unobservable rather than merely unmeasured.
Check the table is live before reading absence as signal — `enrichment_errors` had 453
rows written that morning, while `enrichment_history` has **0 rows ever** and a pruner
but no writer.

## Confident recall of a document you actually opened is worse than not having looked (2026-08-11)

**Problem**: The NexusMind session asserted that the singleton wrong-body case was
"most of the population by count", and I committed it into
`memory/cross-repo-prioritization.md` on their word. The measurement said the
opposite — ~7.5%, a tail. **They had read the refuting caveat section in that same
session, while checking something else**, and did not re-read it before making a
population claim.
**Root cause**: Having opened a document produces the *feeling* of knowing its
contents, which suppresses the impulse to re-check that not having read it would
have triggered. This is a strictly worse position than ignorance: ignorance is
loud, recall is quiet and confident.
**Fix**: Re-open the source before any claim about **population, composition or
rate** — the classes where memory reconstructs a plausible number rather than
failing. When such a claim is passed between sessions, verify against the cited
source, not the report; I did that for their retraction and it surfaced two further
exclusions their message had not carried. Their remedy on the other side: NM#322
states the bound arithmetic explicitly rather than pointing at the doc, because a
caveat living only in a section nobody reaches is not a caveat.
**Durable lesson**: this is the sibling of the promoted rule *"before using any
source as evidence, establish what it excludes"* — here the source was correct and
available, and the failure was between the file and the sentence. **Both of my own
retractions this session (the `investment_risk` inflation reading, and this one)
were plausible-and-unchecked rather than wrong-and-obvious.**

## A check that reconciles a partition breaks when someone adds a member — and the failure lands on the honest path (2026-08-11)

**Problem**: Reported by the NexusMind session. `verify_decision_log.py` asserts the
`refused_*` verdicts sum to `quality_rejected`. Adding a new verdict to the writer
alone leaves that sum short by exactly the new guard's firing count — so **every
batch in which the guard worked would have failed reconciliation**, while batches
where it never fired passed.
**Root cause**: A partition-reconciliation check names its members implicitly. Adding
a member is a silent contract change; the check keeps enforcing the old partition.
**Fix**: Test every member positively and count the remainder in an explicit
`unattributed` bucket, rather than attributing by `else`. Our variant is worse than
theirs and was live for an hour: `gate_refused_label_audit.py` attributed anything
not blocked by the length floor to "lens rules" via `else`, so a third refusal reason
would have been **silently misattributed** rather than loudly failing — under numbers
already published to #105 and #108. Now tests `apply_filter` positively and reports
`refused_unattributed`; re-run confirms 0 and every figure unchanged. Same shape lives
in `tests/unit/test_ground_truth_gate.py:101` and `test_prepare_data.py:179`.
**Durable lesson**: when a control asserts parts-sum-to-whole, ask what happens the day
a part is added — and prefer a loud remainder over a silent `else`.

## `deploy_to_nexusmind.sh` Step 1 ignores `.nexusmind-owns` entirely (2026-08-11)
**Problem**: `proxy_aggregator` was added to `investment_risk v6`'s config
NexusMind-side. The next filter deploy would have deleted it silently — no
conflict, no warning.
**Root cause**: Step 1 is a bare `cp -r "${SOURCE_DIR}/"* "$DEST_DIR/"` with **no
manifest lookup**. Only Step 2 (`filters/common/`) consults `.nexusmind-owns`, so
nothing under `filters/{name}/v{N}/` is protected and *adding a path to the
manifest would not help*. The usage block said "honors .nexusmind-owns" and was
silent about Step 1 not doing so.
**Fix**: Ported the change into llm-distillery (source of truth) and documented
Step 1's behaviour in the usage block. Precedent: normalization plumbing deleted
from NexusMind 2026-04-16, unnoticed 18 days. Edit the llm-distillery copy and
deploy; never the NexusMind copy.

## A peer session's commit convention saved a production cycle by accident (2026-08-11)
**Problem**: NexusMind's `deploy_filters.sh` runs as its `nexusmind.service` `ExecStartPre` and is
fail-closed: it `exit 1`s when committed state differs from origin **and** the
scorer tree has uncommitted changes. A working-tree edit to `filters/` on sadalsuud
can therefore stop the cycle running at all.
**Root cause**: The gate treats uncommitted scorer changes as unsafe-to-deploy,
which is right, but the failure mode is a silently skipped pipeline run rather than
a visible error.
**Fix**: None needed — the edit was committed and pushed, so HEAD matched origin and
the gate block was skipped. Recorded because LD#101 was the same shape and did *not*
get lucky: it ran for days as uncommitted edits on sadalsuud, invisible to the repo.
**Check before trusting a filter change on the box**: `git status --porcelain -- filters/`
and `git rev-list --count origin/main..HEAD` on sadalsuud.

## A `.bak` file left beside a patched source blocked the whole pipeline (2026-08-08)

**Problem**: `nexusmind.service` FAILED at 16:07 and would have failed every 4h. Not a crash — the fail-closed deploy gate refused to ship, because `src/scoring/gpu_client.py.bak_nm300third_20260808` was untracked under a guarded path.
**Root cause**: I made `.bak` copies while patching, then *deliberately kept them* as a rollback for an unverified fix. The commits were already pushed, so git was the rollback and the `.bak`s were redundant — the reasoning was wrong at the moment it felt most prudent.
**Fix**: Delete them; the gate is right. Patch in place and rely on git, or write backups **outside the repo** (`/tmp/…/scratchpad`). Verify with `git status --porcelain` before leaving a repo that a service deploys from — clean means clean, not "only my scratch files".

---

## [5x verify-the-call-path] Copied a gate to a new concern without copying the mechanism that feeds it — the gate could never fire (2026-08-01)

**Problem**: NM#281 added a violence-promotion drop point next to the existing
commerce and obituary checks in `_is_duplicate`. It was a no-op: `enforce: true`
would have dropped **zero** articles while logging `0 violence` — a false
all-clear. Caught by adversarial review the same day, before anyone flipped it.

**Root cause**: `_is_duplicate` runs inside `load_articles`, called from
`_run_shared_dedup`, which happens *before* `_run_violence_promotion_prefilter`
stamps `_is_violence_promotion`. Commerce and obituary work there only because
their preprocessors **rewrite the input JSONL** earlier in the run, so their
flags are physically in the file `load_articles` reads. Violence stamps only
in-memory, and deliberately later — it runs on the *enriched* superset. The
neighbouring code looked like a template; the load-bearing part was somewhere
else entirely.

**Fix**: `b85a467` — move the drop to the stamps (`_enforce_violence_promotion`,
called immediately after stamping), not the stamps to the drop. Mirroring
obituary would have scored un-enriched text and cost recall on a gate already at
0.55. The dead check was **removed** rather than left in place.

**Lesson 1 — the tests were the problem, not just the code.** All three unit
tests fabricated `_is_violence_promotion: True` on a load-time article and
called the gate in isolation. That state never occurs in production. 24/24
green against a gate that could not fire. **When a test constructs the input
itself, ask whether the real pipeline ever produces that input at that point.**
The replacement asserts the ordering structurally (AST: drop-call must follow
stamp-call) and exercises stamps in `_article_cache`, which is the real state.

**Lesson 2 — "next to the similar code" is not a safe default.** Three gates
sharing a function looked like consistency; two of them depended on a
write-back step the third does not have. Before copying a control into a new
concern, verify *when* its input comes into existence, not just where similar
controls live.

**Pattern (5th occurrence of verify-the-call-path)**: previous four are #161
climate_doom, the 2026-07-22 partial-grep issue, LD#80's no-op rollback, and
NM#284's dead prefilters. Every one: correct-looking code at a point in the
flow where it cannot act.

## Two similarly-named structures, sampled the wrong one, got a clean zero — twice in one day, in two repos (2026-08-01)

**Problem**: Two independent investigations reached confident wrong conclusions
by measuring a *different* object than the one under discussion, and both times
the wrong object returned a clean, unambiguous zero that read as proof.

1. **Mine (NM#284)**: counted `passed_prefilter` in
   `data/filtered/*/filtered_*.jsonl` to prove prefilters weren't blocking. That
   file only receives `passed_prefilter: true` rows NexusMind `NexusMind/scripts/main.py`’s `if result["passed_prefilter"]:` write guard —
   0 blocks by construction.
2. **ovr#280**: concluded "NexusMind never sends `cluster_id`" from
   `metadata.quality` (FluxusSource's block: `bias_category, credibility_score,
   source_tier, type_classification` — quoted verbatim in the issue). The field
   is in `nexus_mind_attributes.<lens>.source_quality`, one level deeper, on
   7,629 / 16,128 rows (~47%). Two shipped features were declared no-ops and an
   upstream change was proposed, for a field already on the wire.

**Root cause (shared)**: an article row carries several `quality`/`source_quality`
-shaped blocks from different producers. Nothing in the name distinguishes them,
and each is individually plausible as "the" block.

**Fix / lesson**: **a zero is a claim about the thing you measured, not about the
thing you asked.** Before believing a 0% or 100%, name the exact path you read
and confirm a *positive* control on it — find at least one row where the field IS
populated. Both errors die instantly under that check. Note also the asymmetry:
these read as clean results (0 of 3202, 2647 of 2647), and clean numbers get
quoted onward without re-derivation — mine reached four docs and a commit message.

## `git stash push` + a long test run in ONE chained command lost work to the Bash timeout (2026-08-01)

**Problem**: Comparing a test failure-set before/after a change, written as one
command: `pytest > after.txt; git stash push <files>; pytest > before.txt; git
stash pop`. The harness killed it at the 2-minute limit **between the stash and
the pop** (the suite takes ~60s and ran twice). The working-tree changes were
gone — silently, since the command reported only a timeout.

**Root cause**: Chaining a state-mutating step and its matching restore step
inside a single timeout-bounded command makes the restore conditional on the
whole chain finishing. Any timeout lands the repo in the intermediate state.

**Fix**: `git stash list` → `git stash pop` recovered it (nothing was lost).
**Lesson**: never put `stash push` and `stash pop` in the same timeout-bounded
command. Run the baseline as its own step, or use `git worktree` / a second
checkout so no stash is involved. Generally: **any push/pop, mv/mv-back,
disable/re-enable pair belongs in separate commands** — the second half must not
depend on the first half's command surviving.

## Unit-tested observability shipped two defects that its first six lines of real output exposed (2026-08-01)

**Problem**: NM#284's shadow prefilter logging shipped with 6 passing unit tests.
Its first production run immediately showed two bugs: (1) drift was judged at
n=1, because the post-deploy smoke test scores exactly ONE curated article per
filter — so all six filters logged `observed_pass=1.000` and got flagged
`DRIFT(gate appears inert)`; (2) `expected_pass_rate: ~0.25` (the "approximately"
form, used by 3 filters) loads in YAML as the **string** `"~0.25"`, so a strict
`isinstance(rate, (int, float))` check silently dropped it — exactly the filters
the work cared about logged no declared rate at all.

**Root cause**: Both defects depend on properties of the real environment (what
the smoke test actually does; how the config files are actually authored). Unit
tests encoded the author's model of the environment, so they could not see either.

**Fix**: `5d53774` — `MIN_SHADOW_SAMPLE = 50` before judging drift, and parse the
`~N` form. **Lesson**: for *observability* changes specifically, deploy-then-read
beats test-then-trust; the first real output is the cheapest and highest-yield
review it will get. Corollary: a false alarm on every deploy (6 of the first 6
lines) is worse than no alarm — it trains everyone to ignore the signal.

## [4x verify-the-call-path] Every filter's prefilter was dead in production for ~6 months — config said enabled, runtime hard-coded it off (2026-08-01)

**Problem**: Verifying the LD#86 cultural_discovery topic gate showed the deployed
gate having no effect. Scope precisely: the dead layer is the **per-lens rule
prefilter** (`filters/{name}/v{N}/prefilter.py`, ADR-018/019 `BasePreFilter`
subclasses). The e5 probe, commerce/obituary/violence gates, and the NM#189
source-type allowlist all run normally — each verified, not assumed.

⚠️ **The first evidence for this was invalid and had to be retracted** (same day,
after the owner asked what the prefilter actually was). The claim "all eight
filters stamp 0 prefilter blocks per cycle" came from counting `passed_prefilter`
in `data/filtered/*/filtered_*.jsonl` — but NexusMind `NexusMind/scripts/main.py`’s `if result["passed_prefilter"]:` write guard only writes a
row `if result["passed_prefilter"]`, so that file is 100% passers **by
construction** and can never contain a block. Reading "no blocked rows in a file
that excludes blocked rows" as evidence of no blocking is circular. The pipeline
log in fact reports ~350–360 prefiltered per lens per cycle (source-type
allowlist + validation failures, not lens rules).

**Root cause**: NexusMind `deploy/gpu-server/main.py` builds every scorer with
`use_prefilter=False` (L915) and calls `score_batch(..., skip_prefilter=True)`
(L1318) — present since `66582e7` (2026-02-10), i.e. since the GPU scorer
service was first written. Meanwhile every filter's `config.yaml` declares
`prefilter: enabled: true` with a documented `expected_pass_rate`. The runtime
silently overrode the config, and nothing compared declared against observed.

**Fix**: NM#284 — stamp the prefilter verdict always, enforce via config with an
env lever (ADR-022), shadow first, flip per filter, plus a declared-vs-observed
pass-rate assertion.

**Lesson — the diagnostic that actually settles it**: measure the component
**in-path, on the pre-drop stream**. The NM#284 shadow log reports cd
`observed_pass` 0.255 pooled over 2,099 articles at the scorer; if the gate were
enforcing upstream the scorer would only see the ~24% that passed and the same
measurement would read ≈1.000. That is the load-bearing proof.

**Second lesson — check what your evidence source can physically contain.** The
replay-over-production-rows trick (28.8% vs a stamped 100%) *looked* decisive and
was the first thing I reached for, but its baseline came from an output file that
excludes the very rows in question, so the "100%" was an artifact. A reproduction
is only as good as the population you reproduce it on. Before using a data source
as a denominator, ask what it is filtered on — here, one `if` statement at
NexusMind `NexusMind/scripts/main.py`’s `if result["passed_prefilter"]:` write guard. Related: the wrong-shaped-verify entries below.

**Pattern (4th occurrence of verify-the-call-path, cf. LD#80 below)**: a config
key named `enabled` is not evidence that anything is enabled. When a component
declares an expected rate, assert the observed rate against it in production —
otherwise a component can declare 0.15, stamp 1.00, and stay green for months.

## [3x restated-set drift] Pre-push battery ran tests/unit only — CI runs tests/ incl. root-level files (2026-07-30)

**Problem**: NexusMind 6728a77 passed the local battery (890 tests) but broke CI:
`NexusMind/tests/test_gpu_client.py` (root-level, not under tests/unit/) mocked 5 subprocess
results for a function that now makes 6 calls -> StopIteration.

**Root cause**: local run was `pytest tests/unit`; CI runs `pytest tests/` (minus
integration). Root-level test files were invisible to the battery.

**Fix**: 85aac22 (test now derives its mocks from _SCORER_PATHS and asserts the
exact call list). **Lesson**: before pushing NexusMind, run the full
non-integration suite: `pytest tests/ --ignore=tests/integration` (952 tests).

**Pattern promoted (3rd occurrence of restated-set drift, same file!)**: when two
artifacts must agree on a set (deploy_filters.sh SCORER_PATHS vs gpu_client
_SCORER_PATHS vs its test), derive one side from the other or add a test that
asserts equality — comment-enforced sync ("keep in sync with X") WILL drift.
Occurrences: 2-of-5 components (pre-07-16), hash-object-vs-HEAD (07-16),
missing smoke_test component (07-30).

## LD#80 rollback was a production no-op — the diff looked right, the call path was wrong (2026-07-30)

**Problem**: Two days after the commerce v2→v1 "rollback" (a7771c9), gpu-server logged
66 `POST /commerce/predict` calls in one pipeline run — v2 was still scoring everything.

**Root cause**: `if False:` disabled only the *self-resolution* branch of
`process_files`. Production passes the shared `gpu_client` (main.py:508), which takes
the `elif gpu_client is not None` path straight to `predict_commerce()`. The companion
"repair syntax error" commit (d50967a) proved the module was never imported before
push — a syntax error can't be version-dependent.

**Fix**: NexusMind 96d9acc discards any provided GPU client in commerce
`process_files`. Review lesson: to verify a disable/rollback, trace every call path
to the disabled thing (grep the *callers*), then confirm in production logs — the
absence of `/commerce/predict` calls is the proof, not the diff.

## gitignore negation with trailing comment is silently inert (2026-07-30)

**Problem**: `!filters/*/v*/probe/*.pkl  # comment` never un-ignored anything — new
probe pickles were silently skipped by `git add` for months; only per-directory
.gitignore fixes masked it for solutions v5/v6.

**Root cause**: gitignore treats everything after the pattern start as pattern —
` # comment` becomes part of the glob. No warning, no error.

**Fix**: comment moved to its own line (root .gitignore). Test:
`touch filters/<f>/v<N>/probe/x.pkl && git status --porcelain` must show `??`.

## commit-msg deploy-verification hook can't check Hub on this machine (2026-07-30)

**Problem**: the LD#44 commit-msg hook aborts any commit whose message contains
deploy-class words if `verify_filter_package.py --check-hub`-adjacent checks fail —
and its `python3` lacks `huggingface_hub`, so the hub check fails environmentally
even when the Hub state is correct and verified.

**Root cause**: hook runs system python3; huggingface_hub only exists in venvs.

**Fix (workaround)**: verify the Hub state manually (venv python + safetensors key
inspection), then use the hook's own option 2 — reword to avoid trigger words
(deploy/ship/upload/released). Proper fix: make the hook use a venv python or skip
the hub check with a WARN when the package is missing.

## Commerce v2 deployed without Phase 5 shadow comparison — production regression (2026-07-28)

**Problem**: Commerce prefilter v2 was blocking only 2.1% of articles vs v1's 5.2%,
and generating false positives on multilingual (Greek/Hungarian) news. The v2 design
explicitly required a 1-week shadow comparison (Phase 5) before cutover.

**Root cause**: v2 was deployed based on 190-sample test-set parity (97.8% F1) alone.
Phase 5 was never run. The 190-sample test set from Jan 2026 was not representative of
production's short (median 125 chars), multilingual, Greek-heavy July 2026 traffic.

**Fix**: Rolled back to v1. v1 weights (541MB DistilBERT) uploaded to HF Hub
(`jeergrvgreg/commerce-prefilter-v1`) and copied to NexusMind. commerce.py switched
from GPU v2 path to local v1 CPU path.

## Solutions v6 score compression broke display threshold — tab went empty (2026-07-28)

**Problem**: Solutions v6 compresses model output to ~0-5 range (by design), but the
shared `displayScoreThreshold` (4.5) and summarization pipeline assume 0-10. Only
top ~1% of articles cleared the threshold. Solutions tab collapsed from ~100 to 1-3
articles/day across Jul 26-28.

**Root cause**: Normalization.json was pending for v6 ("needs ≥200 articles at ≥2.25")
but never fitted. Score range mismatch between v6 (0-5) and v5 (0-10) with no bridge.

**Fix**: Added `SCORE_SCALE_FACTORS` map in `ovr.news/summarize.ts` with `solutions: 2.0` +
guard (`raw > 5.0 → skip scaling` to prevent double-scaling old v5 articles).
Bridge until normalization.json is fitted.

## Hot DB creation silently produced 0-byte file — site deployed with empty DB (2026-07-28)

**Problem**: `ovr.news/scripts/create-hot-db.ts` ran without error but produced a 0-byte
`ovr-hot.db`. This was uploaded to R2 and Cloudflare Pages built the site with it.
Solutions page showed only 2 articles (hero + one standard) despite 497 in DB.

**Root cause**: Not yet diagnosed. The script succeeded when re-run manually with
identical parameters. Possible race condition or transient resource issue.

**Fix**: Manual hot DB recreate + R2 upload + Cloudflare deploy hook re-trigger.
Root cause diagnosis deferred — monitor for recurrence.

## Score scale factor double-scaled pre-v6 articles to 16-20 (2026-07-28)

**Problem**: Applying `score_scale_factor=2.0` to ALL solutions articles multiplied
old v5 scores (8-10) to 16-20 in the DB. QA alert fired: avg 13.8, deviating 6.8
from baseline.

**Root cause**: The summarize script reads ALL recent NexusMind JSONL files (10-day
window), including v5-era articles. The initial scale factor had no version awareness.

**Fix**: Added guard `if scale > 1.0 && raw > 5.0: return raw`. v6 max raw is ~4.6,
v5 min display is ~6.8 — clean gap for the heuristic. Ran DB fix to halve 90
inflated scores (49 in `article_filter_scores`, 41 in `articles`).

## Gate file cross-contamination: solutions v6 gate overwrote nature_recovery v4 gate (2026-07-27)

**Problem**: `filters/nature_recovery/v4/ground_truth_gate.json` contained solutions v6 gate
data (threshold 2.25, model "v6" with solutions metrics) instead of nature_recovery v4 data
(threshold 3.75, models "v4" and "v2"). The nr gate results were lost.

**Root cause**: The gate script's `--report` argument was pointed at the wrong filter's
directory during a previous session (Jul 26, before this session). The script writes to
whatever path `--report` specifies — there's no guard that the report path matches the
config or labels being evaluated.

**Fix**: Restored from git (`git checkout HEAD -- filters/nature_recovery/v4/ground_truth_gate.json`).
The original gate data was committed and recoverable.

**Prevention**: Documented in FILTER_PLAYBOOK.md §7: verify after every gate run that the
threshold, model names, and n_labeled match the filter. The gate file is filter-specific,
not a shared template. A `--report` path that points to the wrong filter silently replaces
that filter's gate results.

---

## solutions v4 Deployed Without e5 Probe — Model Can't Screen AND Score (2026-07-26)

**Problem**: Solutions v4 quality gate found 27% policy/regulation bleed in medium+
articles (135/500, 63 in high_solution tier) and severe score discretization (only
10 unique concreteness values across 500 medium+ articles). The 1B-param model was
trying to do BOTH screening ("is this a solution?") AND scoring ("how good?") in a
single forward pass — it can't do both reliably.

**Root cause**: The e5 embedding probe stage (ADR-006, FILTER_PLAYBOOK.md §4) was
marked "optional but recommended" in the dev-guide and was deferred during the 6-day
solutions v4 build sprint (July 17-22, 2026). The config.yaml had a placeholder
`hybrid_inference` section with `threshold: 1.50` marked "recalibrate after
training," but no `inference_hybrid.py` was created, no probe was trained, and no
`probe/` directory exists. The architecture was deployed as single-stage: commerce
prefilter → model — missing the e5 probe screening stage that nature_recovery v4
and other needle filters use.

The prompt's Step-1 "DEFAULT TO PASS" bias amplified the problem: it routes
government regulation announcements, policy proposals, and enforcement actions past
the scope check, and the content-type caps (4.0-5.0) sit above the 2.25 op-point,
so capped articles still surface in medium+ tiers.

**Fix** (solutions v5, in progress):
1. Generalized `scripts/train_probe.py` to read filter-specific constants
   (dimensions, weights, gatekeeper) from the filter's `base_scorer.py` instead
   of hardcoding nature_recovery values.
2. Created `filters/solutions/v5/` with `inference_hybrid.py` (following
   nature_recovery v4's pattern) and `probe/` directory.
3. Probe training pending: `PYTHONPATH=. python scripts/train_probe.py --filter
   filters/solutions/v5 --data-dir datasets/training/solutions_v4 --objective
   recall --target-fn 0.02`
4. **Process fix**: FILTER_PLAYBOOK.md §4 updated — probe is now **REQUIRED for
   needle-in-haystack filters**, not "optional but recommended."

**Promoted to**: FILTER_PLAYBOOK.md §4 (probe requirement gate check). Candidate
for a deploy-gate automation: `test_filter_integrity` should verify
`probe/embedding_probe_e5small.pkl` exists for needle filters.

---

## Retiring a filter but leaving its smoke fixture fail-closes the whole deploy (2026-07-22)
**Problem**: The first cron after the solutions v4 cutover (retired sustech + foresight from
`enabled_filters`) aborted every 4h with `ERROR: smoke fixture references filters not in app.yaml
enabled_filters: ['foresight', 'sustainability_technology']`. Looked like the new lens broke the pipeline.
**Root cause**: `NexusMind/scripts/deploy_filters.sh` has a fail-closed name-alignment gate: every filter
in `NexusMind/deploy/smoke_test_articles.jsonl` must be in `enabled_filters`. The cutover updated `enabled_filters`
but left the two retired filters' smoke fixtures behind → orphan fixtures → gate abort (correct behavior,
just an incomplete cutover).
**Fix**: repoint the iron-air-battery fixture (a clean solutions positive) to `solutions`, drop the
foresight fixture (`e2a102e`). **Lesson**: retiring a filter is a *3-place* edit — `enabled_filters` AND
the smoke fixture AND (for llm-distillery) the package. Add "update `NexusMind/smoke_test_articles.jsonl`" to any
filter-retirement checklist.

## Filed a wrong issue from a partial code grep — the runtime disproved it (2026-07-22)
**Problem**: Filed NexusMind #277 claiming hero image extraction has "no overall budget" (uncapped),
based on a grep that found only the per-page `hero_extraction_timeout=5.0` and no budget. Hours later the
journal printed `Hero extraction: budget exhausted at 3600s — completed 15890/21251` — it DOES self-cap,
exactly like og:image backfill. Closed #277 as not-planned.
**Root cause**: concluded "no budget exists" from "grep didn't find one" (absence-of-evidence) + the phase
running >40 min (which was just heading toward its own 1h cap). A partial read of one file, asserted as fact.
**Fix**: for "does X have a guard?" questions, prefer runtime evidence (run it / read the logs) over a
keyword grep, or read the whole function — grep proves presence, never absence. Reproduce-don't-assume
caught it, but only after the wrong issue was already filed.

## First pipeline run after adding a NEW filter is ~5–8× slower (one-time backlog catch-up), NOT a regression (2026-07-22)

**Problem**: The first NexusMind cycle after the solutions v4 cutover ran for **>1h20m** (still going) vs the normal ~16 min, with the journal stuck for ~1h on `og:image backfill: fetching 20303 article pages`. Looked like a hang / a problem introduced by the new lens — worrying enough to ask "is this broken?"

**Root cause**: A **brand-new filter has no processing history**, so its entire surfaced-article backlog gets dedup-clustered and image-backfilled in one go. Evidence from same-day cron runs (all healthy) vs this run, with *near-identical article input* (~2.6–3.6k in each):
| Run | Dedup clusters / time | og:image backfill |
|---|---|---|
| 04:08 / 08:08 / 12:10 (cron) | ~2,000 / **150–200s** | **1,570–1,952 pages** |
| 17:58 (first run w/ solutions) | **29,132 / 1,327s** | **20,303 pages** |
~10× dedup + backfill despite normal input → not backlog-from-the-failed-16:09-deploy (a 5h gap can't do 10×), but solutions' never-before-seen surfaced articles. The og:image backfill is network-bound (dead-domain timeout tail, ~5 concurrent conns crawling the last few thousand) — but it is **already guarded by a 3600s budget**: this run hit it (`budget exhausted at 3600s — completed 18775/20303, dropped 1528 at budget`) and moved on gracefully, so it self-bounds at ~1h and never hangs forever.

**Fix**: None needed — it's a one-time onboarding cost; the **next** cron cycle returns to the ~16 min / ~180s dedup / ~1.6k backfill norm. Expect exactly one slow catch-up run **per new-filter launch** — recognize it, don't panic, and DON'T kill it (aborting discards the scored output, which is only written at pipeline end). The 3600s backfill budget caps the pain at ~1h and drops the tail (1528 images just miss hero-image enrichment for one cycle — cosmetic, self-heals next run). Latent improvement if new-filter launches get frequent: lower the backfill budget for the first catch-up cycle so it drops the tail sooner.

## deploy_to_nexusmind.sh: Windows-only paths + `filters/common` sync pulls unrelated artifacts (2026-07-22)

**Problem**: Running the solutions v4 cutover from situla (Linux), `deploy_to_nexusmind.sh` (1) failed immediately with `ERROR: Filter not found: C:/local_dev/llm-distillery/...` — the script hardcoded the Windows workstation paths; and (2) after fixing that, its "sync all of `filters/common/`" step pulled **unrelated `obituary_detector` training/validation dirs + a `calibration_report.json` into NexusMind** (mtime = the copy), plus surfaced a real 44-line `score_normalization.py` divergence — none of which belonged in a solutions deploy. `git add filters/common/` would have bundled the obituary artifacts (origin-contamination shape).

**Root cause**: (1) `DISTILLERY_ROOT`/`NEXUSMIND_ROOT` were hard assignments (`C:/local_dev/...`), never run on Linux. (2) The `.nexusmind-owns`-empty policy means the script copies ALL of `filters/common/` including sub-model data dirs; NexusMind doesn't gitignore those, so they land as untracked-and-stageable. Also: the script's `verify_filter_package --check-hub` call passes no `--token`, so it "not found"s a private Hub repo unless `HF_TOKEN` is exported (or an `hf` login is cached, as on the Windows box).

**Fix**: Made the paths env-overridable (`${DISTILLERY_ROOT:-C:/...}`), committed. Ran with `--dry-run` first, then staged **explicitly** (`git add filters/solutions/v4 config/app.yaml scripts/main.py src/filters/filter_loader.py` — NOT `filters/common/`), verified no weights/obituary staged, and reverted the `filters/common` contamination (`git checkout -- filters/common` + `git clean -fd filters/common`) before committing. Exported `HF_TOKEN` for the verify. **Durable lessons**: (a) run this script `--dry-run` first and stage explicitly — never `git add filters/common/` blind; (b) `filters/common` sync is broader than "shared math" and can bundle sub-model data — check the diff; (c) private-Hub verify needs a token in env on any box without a cached `hf` login; (d) situla's github SSH key (`situla@veen`) is passphrase-locked in the empty `openssh_agent`, so `git push` to the SSH remotes (NexusMind/ovr = `git@github.com:ducroq/...`) fails headless — the owner must `ssh-add` (same class as the gpu-server locked-key note).

## A runtime fail-closed `raise` halted the whole pipeline; the existing CI test was already the right guard (2026-07-22)

**Problem**: A round-1 review wanted to prevent the "app.yaml enables a filter whose package isn't copied → silent dark tab" hazard. The fix added a `raise RuntimeError` in NexusMind `scripts/main.py _resolve_filters` on any enabled-but-undiscovered filter. Round 2 caught it as a **critical defect-in-fix**: the raise fires before `valid` is returned, so ONE not-yet-copied filter aborts scoring for **all** filters (uplifting/investment_risk/cultural_discovery/belonging/nature_recovery too), turning a routine config-lag into a full pipeline outage — and it broke 2 pre-existing tests (`test_pipeline_stages.py::TestResolveFilters`) plus made `NexusMind/test_filter_integrity.py` 8/8 red.

**Root cause**: Added a runtime fail-closed control without (a) checking whether an existing guard already covered the case, and (b) bounding its blast radius. `NexusMind/tests/unit/test_filter_integrity.py` ALREADY reads `NexusMind/config/app.yaml` and asserts every enabled filter is discoverable — the hazard was already caught fail-closed at CI/deploy time. The runtime raise duplicated it in the wrong layer (production scoring) and over-broadly (halt-everything).

**Fix**: Reverted to warn-and-skip (resilient runtime: run the filters that ARE present). The silent-dark-tab hazard is handled by `NexusMind/test_filter_integrity.py` at CI + atomic package-with-config deploy. **Durable lesson** (promoted to MEMORY.md): before adding a runtime fail-closed control, check for an existing CI/deploy-time guard and bound the blast radius — fail-closed belongs at the CI/deploy layer, not inside runtime scoring; a runtime control that halts everything on one missing item is over-broad. Meta: this is exactly why the "run 2+ review rounds" rule exists — R2 found 15 defects-in-fixes, this being the worst; a R1 fix became a R2 critical.

## Enrichment silently poisoned 17.3% of the pool with consent-wall text (2026-07-19)

**Problem**: Solutions v4 e5 screening returned **99% junk candidates** — the top-k for all three types was dominated by Google "Before you continue… We use cookies and data…" consent-page text instead of articles. 17.3% of the survivor pool (29,585/171,050) had this as its "content."

**Root cause**: Our enrich-first step reused NexusMind's `ArticleFetcher.pre_enrich`, which follows Google-News redirect URLs; trafilatura extracts the GDPR **consent interstitial**, and `should_replace_content` swaps it in because it's longer than the RSS stub. The junk is >500 chars, so it **evades both guards** — `is_scrape_junk` only pattern-checks bodies ≤120 words, and re-enrichment only triggers <500 chars — and its generic service-language embeds near every solution centroid, so it out-ranks real content. Confirmed all 29,585 were enrichment-introduced (0 in the original scrape). **This is also a live NexusMind production bug**: `should_replace_content` has no consent/paywall guard, so production feeds the same consent pages to the scorer (tolerated only because it scores low).

**Fix**: Added a length-independent consent/paywall signature detector; reverted the 29,585 rows to their original raw RSS stubs (median 84 chars, real) by id-join with the raw pool; re-screened → 0% consent junk. Corpus-side only; the real remedy is a consent guard in NexusMind `should_replace_content` (filed as a cross-repo follow-up). **Durable lesson**: when you reuse a production fetch/enrich path on a *screening* corpus, its tolerated-in-production failure modes become *ranking* poison — an item scored-and-discarded in prod becomes a top-ranked candidate here. Audit enriched content for boilerplate BEFORE embedding, not after scoring.

## `pkill -f <pattern>` self-kills when the pattern is in its own command line (2026-07-19)

**Problem**: `pkill -f solutions_screen.py` inside an ssh'd shell silently aborted the *rest of the script* (a 669 MB transfer never ran); output truncated with no error.

**Root cause**: The remote shell's own command line contained "solutions_screen.py" (it was running a script that referenced it), so `pkill -f` matched and killed its own parent shell. This is the destructive twin of the already-logged `pgrep -f matches your own ssh command line` gotcha — `pgrep` gives a false positive; `pkill` executes it.

**Fix**: Don't `pkill -f` a pattern that appears in the wrapping command; match by pid, or use a bracket trick (`solutions[_]screen`) so the pattern-string doesn't match itself. Verify a kill by footprint (process gone / GPU mem freed), not by the pkill's own exit.

## A check-script bug reported a false "0", and reuse-caching can silently misalign (2026-07-19)

**Problem**: Two "wrong-but-green" issues found by the corpus-build review battery. (1) I told the engineer "0 Swahili articles in candidates"; the reproduction reviewer found **10** — my check had a nested-quote mangling (`.get(chr(39)…)` → looked up key `"'"`), so it returned 0 for *every* language. (2) The screener's `--reuse-embeddings` loaded cached vectors while rebuilding records from a file, with no fingerprint — and `survivors_enriched` (consent) vs `survivors_clean` (reverted) are **same-ids/same-order, different content**, so a reuse re-cut would pair the wrong embeddings with 17% of records and nothing would crash.

**Root cause**: Both are the project's own "a control never observed failing is decoration" lesson, extended to *measurement* scripts and *caches*: a check that can't detect the thing it counts, and a cache keyed on identity that ignores content. Nested double-quoting through two ssh hops is a bug factory that manufactured the false-0.

**Fix**: (a) For anything counting/gating, **watch it fail** — the fixed Part-A seed gate was proven to FAIL on a boilerplate seed, and the reproduction reviewer re-derived every number from disk (caught the false-0). (b) Content-sensitive embedding fingerprint (`id|len|head80`) that refuses reuse on mismatch (proven content-sensitive). (c) Through a double-ssh hop, **scp a script and run it** — never inline nested-quoted python.

---

## Two review rounds found 18 defects; 4 were in the FIXES from round 1 (2026-07-14)

**Problem**: A day of careful fixes, each individually verified, still shipped defects that only an adversarial second model found — and round 2's worst findings were *inside* round 1's fixes.

**Root cause**: Two distinct failure modes, and they need different countermeasures.
1. **Premises asserted in comments, never executed.** `a95c3d6` moved the deploy revision hash to HEAD, justified by: *"the uncommitted-changes check covers exactly SCORER_PATHS, so HEAD and the working tree are guaranteed identical."* False. `git diff --quiet <paths>` compares worktree-vs-**INDEX**, so `git add` defeats it — verified: a staged edit passed the guard while the hash named a blob without it and rsync shipped the worktree. The sentence was the bug; nobody runs a sentence.
2. **Tests that re-implement their subject.** `test_normalization_invariant.py` carried a private copy of `_op_point_from_base_scorer`, and the copy had already drifted **within the same commit** — it omitted the ambiguity check added right beside it. A test that reimplements what it tests, tests the reimplementation.
Plus: the invariant itself was **too strict** (`raw_min` is the smallest score *observed*, not the fit threshold; it only passed because the files are dense — invR is 4.0003, cd v5 is 4.0006, and the tolerance absorbed that by luck), guards keyed on the wrong quantity (`args.min_score` instead of the written `stats.raw_min`), and `--allow-thin-fit` — documented "never deploy it" — wrote straight into the deployed package.

**Fix**: All 18 closed, each verified against pre-fix behaviour rather than assumed (pre-fix resolved `3.0` from stale config; pre-fix resolved `1.5` on two definitions; pre-fix crashed on dict-shaped thresholds; pre-fix passed a staged edit). The durable lessons: (a) a claim written in a comment is not a control — if the comment asserts a property, *test the property*; (b) never re-implement the subject in its own test — import it; (c) run two rounds, because round 1 reviews the code and round 2 reviews the fixes, and the second one is where your own blind spots live.

---

## Reviewers misread design as defect too — and confidently (2026-07-14)

**Problem**: Round 1's top finding claimed the normalization guard "mixes scales" because `TIER_THRESHOLDS` is a normalized-scale cut used as a raw floor, predicting recall collapse. I amplified it into a plan, quantified "2,776 hidden articles across 5 lenses", and framed linear `score_scale_factor` as the healthy baseline. All of it wrong.

**Root cause**: Neither I nor the reviewer opened ADR-014, which **specifies** the pipeline as "…normalize → **reassign tier on normalized** → display_rank". `NexusMind/production_scorer.py`'s module docstring says the same thing 250 lines above the line I read. So `raw >= threshold` + `tier: low` is correct by design — the article sits at the bottom of its own MEDIUM+ population. And linear scaling isn't healthy, it's *superseded*: foresight only uses it because its fit was REJECTED by `MAX_NORMALIZATION_RAW_MIN` (#205). The engineer caught it by asking "are you not understanding the normalization procedure? … I think not the linear scaling?" — not by any check either of us ran.

**Fix**: Retraction recorded; round 2 was explicitly told the retraction *and invited to overturn it with evidence* (it didn't). The guard turned out **correct**, filling the missing LOW-side bound symmetric to the existing HIGH-side one. Evidence that settles it: 7 of 9 fitted `normalization.json` files sit at `raw_min == exactly the tier threshold`; the 3 that don't are the only 2 normalization incidents ever. Now enforced by `tests/unit/test_normalization_invariant.py`. **Generalisable**: a review finding is a hypothesis, not a verdict — verify it against the design docs before acting, especially when it is dramatic. Both a model and an agent reading the same code reached the same wrong conclusion, which means "two models agree" is not evidence.

---

## The #161 climate_doom cap was a band-aid over a normalization-fitting error (2026-07-14)

**Problem**: nature_recovery v4 capped two Spanish conservation stories to 2.0 (`cap_applied: ['climate_doom']`) — seed-banking Chile's last wild *Dendroseris neriifolia* (raw 3.79) and buying habitat for the Ecuadorian vizcacha (raw 4.28). Both are genuine recovery/protection content; neither is doom.

**Root cause**: Two independent defects, and the deeper one reframes #161 entirely.
1. **Window asymmetry**: `detect_caps` scanned title+500 chars for triggers *and* overrides. Both articles tripped on the single word `extinción` in the lede — used as *prevention* ("para evitar su extinción") and as the IUCN status label ("en peligro crítico de extinción"), never as a doom claim. Their recovery signals (`restauración`, `reintroducciones`) sat at char 2551+, outside the window. The asymmetry is structural: a conservation story states its threat context up front and reports the outcome later, so a lede-only override can never win on the articles it exists to rescue.
2. **#161 was never a model failure**: v2's model scored the five motivating doom articles **2.2–3.3** — correctly low. `normalization.json`, fitted at `raw >= 1.5` (fit-set median 2.19), mapped them to **5.2–8.3** and put them on the lens at up to 8.34/10 "high". Replaying all five raw scores through v2's `normalization.json` reproduces production **exactly** (5/5 match). The cap was a keyword band-aid over a threshold error.

**Fix**: **[SUPERSEDED the same day — the cap was RETIRED, NexusMind `1dd5e49`.]** The override-window fix rescued two of the three false positives and could not touch the third: *"Ecuador's Amazon coffee farmers get ahead of Europe's deforestation rules"* (raw 4.66) trips on `deforestation` inside **`deforestation-free`** — `\b` matches across the hyphen — and holds no recovery vocabulary in 12,627 chars, so no override can reach it. All three bites are the trigger word in a *non-doom construction*; a polarity-blind regex cannot see the difference and patching each is whack-a-mole across five languages. **Final scoreboard: 3 bites, 3 false positives, 0 saves.** The `recovery_evidence` gatekeeper (`<3 → cap 3.5`, below the 3.75 op-point) already does the job semantically — doom scores recovery_evidence 0.07–1.08, the coffee FP scored 4.58 — so the cap was a regex overriding the model's *correct* judgement, costing exactly the recall #71 chases. Registry now empty; mechanism retained for future filters. Superseded fix, for the record: (a) Overrides now scan the full body; triggers stay bound to the lede (NexusMind `8681efa`). A/B over 10,625 production articles: 33 change state, only 2 above the 2.0 ceiling — exactly the two false positives; nothing else moves. (b) The durable fix is upstream: `fit_normalization.py` now derives `--min-score` from the operating point and refuses below it (`33fba44`). Rescoring the five #161 articles under v4 gives raw **0.36–1.89** — all below the 3.75 op-point *and* below the cap's own 2.0 ceiling, so the cap cannot act on them at all. Under v4 it is a dormant safety net, not the thing keeping doom off the lens; its only measured effect in 24h was the two false positives (165 triggers, 163 no-ops, 2 bites, both wrong). Simulation confirms the conditionality: fit at 3.75 → all five clip to ~0.56 (cap moot); fit at v2's 1.5 → `burns` re-inflates to 5.32 and the cap becomes load-bearing again.

---

## Controls that were never executed against the thing they claim to control (2026-07-14)

**Problem**: Five separate "protections" found dead in one session — each added in good faith, none ever observed firing.

**Root cause**: Not a shortage of checks. Every one *was* a check; none had ever been watched fail.
- `.githooks/commit-msg` (the #44 deploy-claim gate): committed mode **100644**. Git silently ignores non-executable hooks, so every clone that followed CLAUDE.md's `git config core.hooksPath .githooks` step got a no-op. It also invoked bare `python` (only `python3` exists), so even once executable it could never *pass* — which trains `--no-verify` and hands back the hole it was written to close.
- `NexusMind/deploy_filters.sh` freshness gate: the deploy **hash** covers `src/scoring/`, but the origin/auto-pull gate only diffed `filters/` + `src/filters/`. A `src/scoring`-only commit merged to origin therefore skipped the pull, hashed the stale checkout, matched gpu-server's equally-stale revision, printed *"Filters already in sync — skipping deploy"* and exited 0. Reproduced live against the #161 fix, which touches only `src/scoring/`.
- `config.yaml` `content_type_caps.*.exceptions:` — documented ("Doom framing followed by documented recovery outcome"), never compiled into `NexusMind/cap_triggers.py`. Only `triggers:` were.
- `config.yaml` `scoring.tiers` — read by nothing; `TIER_THRESHOLDS` is the sole runtime source (found 2026-07-10, op-point 3.75 inert). Still live in **sustainability_technology v3**: config says `medium: 3.0`, code runs `4.0`.
- Three `MEMORY.md` `<!-- verify: -->` assertions reported FAIL on claims that were all **true** — `cmd && echo PASS || echo FAIL` collapses three states into two and cannot distinguish "claim is false" from "check could not run", making curate's own documented ERROR branch unreachable.

**Fix**: Hook made executable + interpreter resolved (`9b6126d`); freshness gate hoisted to a `SCORER_PATHS` array covering exactly what the hash covers (NexusMind `4e25934`); assertions rewritten so the *claim* decides PASS/FAIL and *transport/deps* surface ERROR (`7be2368`), each state verified to fire. Standing rule: **a control is not real until you have watched it fail.** New tests were run against the *old* code to confirm they fail; that is the only reason they are known to test anything.

---

## A wrong diagnosis that its own workaround kept alive (2026-07-14)

**Problem**: `ssh gpu-server` from situla returned `ssh_askpass ... Permission denied (publickey,password)`. I concluded "no gpu-server key from this workstation; it needs the sadalsuud hop", routed the #161 rescore through `ssh sadalsuud "ssh gpu-server ..."`, and stated the conclusion twice as fact. The engineer checked and corrected it: the link works fine.

**Root cause**: `~/.ssh/id_ed25519` is passphrase-protected, and situla runs **two** agents — `gcr/ssh` (gnome-keyring, `$SSH_AUTH_SOCK`, the unattended fleet keys) and `openssh_agent`, which holds only `situla@veen` and is pinned via `IdentityAgent` by gpu-server **and** github.com. On a cold `openssh_agent` the key isn't there; one interactive unlock caches it (`AddKeysToAgent yes`) and everything works for the rest of the session. What made the error durable is that **the workaround succeeded**: the hop works because sadalsuud's key is unattended, so a passing result kept confirming a wrong model. An error that produces green results never falsifies itself.

**Fix**: Recorded in `memory/gpu-server.md` (`fe07211`, corrected `4254487`). The first version of the note documented the *wrong agent* — it told the reader to run `ssh-add -l`, which reads gcr and lists `situla@veen` even when `openssh_agent` is empty and gpu-server is failing, i.e. a false-positive diagnostic. Corrected to name `SSH_AUTH_SOCK=/run/user/1000/openssh_agent` explicitly and to treat the `BatchMode` probe as authoritative. Note also records that nothing in production depends on this link (the pipeline reaches gpu-server from sadalsuud via `nexusmind-scorer@sadalsuud`), so the passphrase costs nothing operationally and must not be "fixed" by stripping it.

---

## Fresh-version normalization cold-start starves the ovr feed (2026-07-11)

**Problem**: After nature_recovery v4 deployed (2026-07-10), ovr.news showed "no new nature articles." Scorer was healthy and producing v4.0 MEDIUM+ output the whole time.

**Root cause**: A fresh version ships with **no `normalization.json`** (correct — ADR-014 forbids reusing the old CDF), so `NexusMind/production_scorer.py` emits RAW `weighted_average`. Every *other* lens emits *normalized* scores. Two ovr mechanisms then mis-handle the raw filter: (1) cross-lens assignment (`ovr.news/canonical-lens.ts`) picks the highest `weighted_average` across scorers, and (2) the uniform display gate (`ranking.displayScoreThreshold: 4.5`) is calibrated for normalized scores. Compounding it: for the ~10-day v2→v4 window overlap, still-in-window v2 rows carried *inflated* normalized scores (percentile CDF mapped raw≈2.0 / tier=low up to normalized 5–7) and **out-ranked** fresh v4 rows — so new v4 articles were buried, not absent. v2's "fuller" feed was ~90% inflation; v4's raw≥4.5 count (3–4/batch) actually *exceeded* v2's (0–2/batch).

**Fix**: (a) No ovr action needed — the inflated v2 rows age out of the 10-day `published_date` window by ~2026-07-19, leaving the honest v4 steady state (~3–4 genuine MEDIUM+/batch; nature is ~0.3% of feed — volume is a v5/#71 recall decision, not a normalization bug). (b) **Process fix**: fit normalization *at deploy time* from a production-representative historical rescore instead of waiting weeks for live accumulation — the missing runbook step. Documented in `docs/FILTER_PLAYBOOK.md` §6 + `docs/RUNBOOK.md` "Fit normalization". A thin fit doesn't help: `MIN_NORMALIZATION_ARTICLES=200` silently rejects it (a 33-article fit attempted here was inert), and the sample must be at production base rate (~145K rescored articles for 200 MEDIUM+), NOT the enriched val set. Normalization buys cross-lens *fairness*, not volume.

---

## PEFT Adapter Resave Breaks Hub Loading (Feb 2026)

**Problem**: After running `resave_adapter.py`, `PeftModel.from_pretrained()` fails to load the adapter from HuggingFace Hub.

**Root cause**: `resave_adapter.py` converts keys from OLD format (`.lora_A.weight`, `score.weight`) to NEW format (`.lora_A.default.weight`, `score.modules_to_save.default.weight`). Hub loading via `PeftModel.from_pretrained()` expects OLD format and doesn't remap.

**Fix**: Never run `resave_adapter.py` before Hub upload. Keep adapters in OLD format. Local `inference.py` remaps at load time. Documented in ADR-007.

---

## Gemma-3 Auto Mapping Not Supporting gemma3_text (Feb 2026)

**Problem**: `AutoModelForSequenceClassification.from_pretrained("google/gemma-3-1b-pt")` fails because `gemma3_text` model type isn't in the Auto mapping (only `gemma3` for multimodal is mapped).

**Root cause**: `google/gemma-3-1b-pt` uses `Gemma3TextConfig` with `model_type: gemma3_text`, but transformers 4.55.3 doesn't register it in `AutoModelForSequenceClassification`.

**Fix**: Created `load_base_model_for_seq_cls()` in `filters/common/model_loading.py`. Falls back to building a custom `Gemma3TextForSequenceClassification` using `Gemma3TextModel` + `nn.Linear` head when Auto fails.

---

## Windows Safetensors Memory-Mapped Write Conflict (Feb 2026)

**Problem**: Saving a safetensors file on Windows fails if the same file is currently loaded (e.g., modifying adapter weights in place).

**Root cause**: Safetensors uses memory-mapped I/O. Windows locks memory-mapped files, preventing overwrite.

**Fix**: Save to a temp file first, then `os.replace()` to atomically swap.

---

## rsync dup() Errors on gpu-server (Feb 2026)

**Problem**: `rsync` fails with `dup()` errors when transferring files to gpu-server.

**Root cause**: Unknown — likely related to LXC container filesystem or Tailscale network layer.

**Fix**: Use `scp` instead of `rsync` for all file transfers to gpu-server.

---

## Training Data Dir Naming Mismatch (Feb 2026)

**Problem**: Training data directories don't follow a single naming convention, causing confusion when scripting.

**Root cause**: Organic growth. Some dirs use filter version from when data was scored (e.g., `sustainability_technology_v3`) vs the filter version being trained. Hyphenated filter names (investment-risk, cultural-discovery) keep hyphens in dir names.

**Fix**: Convention: `datasets/training/{filter_name}_{version}/` where `{filter_name}` preserves the filter's canonical name (including hyphens). Check actual dir names before scripting.

---

## Hyphenated Filter Names Break Python Imports (Feb 2026)

**Problem**: `import filters.investment-risk.v6.inference` fails — Python interprets hyphen as minus.

**Root cause**: Python identifiers can't contain hyphens.

**Fix**: Use `importlib.import_module("filters.investment-risk.v6.inference")` for hyphenated filter names.

---

## Pipeline is I/O-Bound, Not Compute-Bound (Mar 2026)

**Problem**: Instinct says "optimize model inference" (#24), but production logs show GPU scoring is only 12% of pipeline time.

**Root cause**: The NexusMind pipeline spends most time on pre-enrichment (HTTP-fetching full article text from source URLs) — 55% of wall time on big runs. GPU scoring does ~2K articles × 5 filters in under 4 minutes (~22ms/article). Story dedup (GPU embeddings) adds another 8%.

**Data** (2026-03-08, 1,949 articles × 5 filters):
- Pre-enrichment: ~16 min (55%)
- GPU scoring: ~3.6 min (12%)
- Story dedup: ~2.3 min (8%)
- Aegis export: ~3.3 min (11%)
- Cleanup/sync: ~4 min (14%)

**Implication**: On GPU, scoring is fast and not the bottleneck — pre-enrichment is. But GPU access is borrowed. Without it, scoring becomes the bottleneck: ~900ms/article on CPU × 1,949 articles × 5 filters ≈ 2.4 hours per run (vs 3.6 min on GPU). That's why #24 matters — it's not about optimizing today's pipeline, it's about surviving without the GPU.

---

## score_scale_factor Is Linear, Cross-Filter Normalization Is Not (Mar 2026)

**Problem**: Filters produce structurally different score distributions. Uplifting passes 62.8% of articles as MEDIUM+, nature_recovery passes 0.3%. The HOME tab uses `max(weighted_average)` across filters, so uplifting dominates. Articles open in the wrong tab (uplifting instead of recovery).

**Root cause**: `score_scale_factor` (e.g., 1.53 for nature_recovery) applies a linear stretch to compensate for calibration range compression. But the distributions are non-linear — most nature_recovery articles cluster near 0, and linear stretching doesn't help them. Meanwhile, calibration itself is fitted on enriched val sets (ADR-003/005), not production data, so the calibration ceiling reflects what the oracle saw in enriched data, not what's possible.

**Fix**: Replace `score_scale_factor` with percentile normalization (ADR-014). Non-linear monotonic mapping fitted from production MEDIUM+ data. Same pattern as isotonic calibration (ADR-008) but applied on the weighted average across filters, not per-dimension within a filter. Set `score_scale_factor` to 1.0 for all filters after deploying normalization.

---

## SCP Creates Nested Directories When Target Exists (Mar 2026, recurred Apr 2026)

**Problem**: `scp -r source/dir/ dest/dir/` creates `dir/dir/` nesting. Hit three times: filter directory, model directory, and nature_recovery v2 model copy from gpu-server.

**Root cause**: When the target directory already exists, `scp -r source/ target/` copies `source` INTO `target` rather than merging contents.

**Fix**: Always scp to the PARENT directory: `scp -r source/dir/ dest/` (not `dest/dir/`). RUNBOOK.md updated 2026-04-15 with correct patterns. Promoted to feedback memory.

---

## Git Bash Mangles Unix Paths in Arguments (Mar 2026, recurred Apr 2026)

**Problem**: `--remote-dir /home/jeroen/...` becomes `C:/Program Files/Git/home/jeroen/...` when passed through Python on Windows Git Bash.

**Root cause**: Git Bash's POSIX-to-Windows path conversion applies to command arguments that look like Unix paths.

**Fix**: Set `MSYS_NO_PATHCONV=1` before the command: `MSYS_NO_PATHCONV=1 PYTHONPATH=. python ...`

---

## Systemd Service Context Differs From Interactive SSH (Apr 2026)

**Problem**: Filter works when tested interactively on gpu-server (`ssh gpu-server "python3 ..."`) but fails when the NexusMind scorer systemd service restarts.

**Root cause**: The systemd service runs with a different environment than an interactive SSH session. Key differences: working directory, PYTHONPATH, HF_HUB_OFFLINE, PATH, and available GPU memory (other services may claim VRAM). Interactive testing bypasses these constraints, so "it works when I run it" doesn't guarantee it works in production.

**Fix**: Always test through the actual execution context after deploying changes: `sudo systemctl restart nexusmind-scorer && journalctl -u nexusmind-scorer -f`. Check the service's EnvironmentFile and WorkingDirectory in the unit file, not just interactive shell behavior.

---

## MAE Is Misleading for Needle-in-Haystack Filters (Apr 2026)

**Problem**: nature_recovery v1 had val MAE 0.54 — looks great. But in production, 98.6% of articles scored below 1.0. The model had zero discrimination. v2 has "worse" MAE (0.63) but dramatically better ranking (Recall@20: 0.70 vs 0.55).

**Root cause**: MAE treats all errors equally. When 95% of articles are noise with oracle WA ~0, predicting zero for everything gives low MAE. The model is "accurate" on noise but useless on the articles that matter.

**Fix**: For needle filters, use ranking metrics: Recall@k, NDCG@k, false negative rate on MEDIUM+. Documented in filter development guide (Issue 4). Overall MAE is still fine for balanced filters (uplifting, belonging, etc.).

---

## Memory Claimed "Shipped" But Feature Only Existed in Running Process (Apr 2026)

**Problem**: Agent memory can state a feature is "shipped and working" based on a point-in-time test during a session. If the feature lives only in a running process (not persisted to the deployed codebase), it disappears on restart. Future sessions that trust the memory never re-verify.

**Root cause**: Memory records a session observation as deployed state. There's no mechanism to distinguish "I tested this once" from "this is persistently deployed."

**Fix** (v1.9.0 self-verifying memory): Never write "shipped"/"deployed"/"live" in memory based on a session observation alone. Qualify: *"responded correctly during session — verify persistence after restart."* Include a verification command in an HTML comment so future sessions can check before trusting: `<!-- verify: curl https://endpoint | grep expected -->`. The `/curate` skill now scans for unverified state claims and runs verify commands automatically.

---

## Commit Claimed "Deploy to Hub" But Upload Never Ran (#44, 2026-04-19)

**Problem**: Commit `399d739` "Deploy nature_recovery v2 with sample weighting (#41)" states in its body *"Deployed to HuggingFace Hub, gpu-server, sadalsuud."* The Hub upload was never actually executed. For three days production ran v2 config + v2 calibration × v1 weights (pulled from `jeergrvgreg/nature-recovery-filter-v1` by an `inference_hub.py` that had been scaffolded as a copy of v1). Caused NexusMind#155 / #161 scoring anomalies.

**Root cause**: Two failures compounded.
  1. *Scaffold-by-copy without translation*: all three v2 inference files (`inference.py`, `inference_hub.py`, `inference_hybrid.py`) were copies of their v1 equivalents with `v1` imports and `v1` repo_id left intact.
  2. *No gate between commit-message intent and actual upload*: the agent wrote "Deployed to Hub" based on intent, not verification. The upload script's post-upload `PeftModel.from_pretrained()` verification never ran because the script wasn't invoked.

**Fix** (2026-04-19):
  - `scripts/deployment/verify_filter_package.py` — 8 checks (imports match dir version, `repo_id` matches dir version, config/FILTER_VERSION consistency, Hub repo exists, Hub `last_modified` ≥ local `adapter_model.safetensors` mtime).
  - `scripts/deploy_to_nexusmind.{sh,ps1}` Step 0 runs `verify_filter_package.py --check-hub`; deploy aborts on failure.
  - `.githooks/commit-msg` refuses any commit whose message contains *deploy/shipped/uploaded* if the staged diff touches filters and verification fails.
  - See follow-up issues #47, #48, #49.

[PROMOTED to feedback memory: `feedback-claim-requires-verify.md`]

---

## [RESOLVED] deploy_to_nexusmind.sh Regressed BFloat16 Fix Owned by NexusMind (2026-04-19)

**Problem**: `deploy_to_nexusmind.sh` copies `filters/common/` from llm-distillery to the NexusMind checkout. llm-distillery's `filter_base_scorer.py` lacked a BFloat16 → float32 cast (`outputs.logits.float().cpu().numpy()`) that NexusMind had added in `68e3d5d` (2026-04-16). Running the deploy script for nature_recovery v2 today silently overwrote the fixed NexusMind copy with the broken llm-distillery copy. Production `/filter/nature_recovery/score` started returning 500s with `TypeError: Got unsupported ScalarType BFloat16`.

**Root cause**: `filters/common/filter_base_scorer.py` exists in both repos, but NexusMind had been evolved without back-porting fixes to llm-distillery. The deploy script blindly copies the entire `filters/common/` tree with no "NexusMind-owns" carve-out. NexusMind's own gotcha-log actually notes this pattern ("filter_base_scorer.py can't be synced from distillery"), but the rule was docs-only — no script enforcement.

**Fix** (immediate): Today I ported the `.float()` cast to llm-distillery (`b98fc6f`) so `filters/common/` is consistent both sides, and restored it on NexusMind (`2d9a11f`). Production verified via smoke test (nature_recovery wa=4.31, belonging wa=6.48).

**Fix** (durable — shipped 2026-04-28, issue #50): Added `.nexusmind-owns` manifest at repo root and patched both `deploy_to_nexusmind.sh` and `.ps1` to skip listed files (currently `filter_base_scorer.py` + `hybrid_scorer.py`) and warn on drift. Initial run after the patch caught real comment-level drift on `filter_base_scorer.py` that would have been silently overwritten. CLAUDE.md Hard Constraints now references the manifest.

---

## rsync dup() Errors from Windows Git Bash (Recurred 2026-04-19, NexusMind)

**Problem**: `NexusMind/scripts/deploy_filters.sh` fails with `rsync: dup() in/out/err failed` / `connection unexpectedly closed (0 bytes received so far)` when run from Windows Git Bash targeting gpu-server — even though gpu-server is reachable via plain SSH.

**Root cause**: Windows Git Bash / MSYS runtime doesn't cleanly hand rsync's fd management to the Tailscale SSH subprocess. Specific to the workstation runtime, not gpu-server. This is an old gotcha (Feb 2026, originally fixed by switching to scp) that recurred when NexusMind switched the deploy script back to rsync (Apr 2026, to preserve model/ directories via `--exclude`).

**Fix**: Run `NexusMind/deploy_filters.sh` from a Linux host (sadalsuud) instead of Windows. `llm-distillery/scripts/remote_deploy.sh` wraps the SSH hop — single command from the workstation, Linux→Linux rsync inside. Structurally unreachable on Windows now.

---

## [RESOLVED] \bRIP\b False-Positive on "rip current" (2026-04-28)

**Problem**: belonging v1 prefilter shipped a `\bRIP\b` pattern in `OBITUARY_PATTERNS` (commit `44b5e21`, #45). The standalone token was meant to catch obituary uses ("Tributes Pour In: RIP Hero"), and the comment said "MUST be uppercase to avoid matching 'rip' as a verb." But every pattern in `OBITUARY_PATTERNS` is compiled with `re.IGNORECASE` at the call site (`prefilter.py` line 262). So `\bRIP\b` matched lowercase "rip" too — including **"rip current"** in beach-safety articles, which would block from belonging.

**Root cause**: A list-of-patterns design plus a global compile flag at the call site means a single "case-sensitive only" token in the list silently becomes case-insensitive. The pattern author can't opt out of the global flag without explicit syntax.

**Fix #1 (incomplete)**: Inline `(?-i:...)` flag scope disables IGNORECASE for that one pattern: `r'(?-i:\bRIP\b)'`. Confirmed with a unit test against "Lifeguards Warn of Rip Currents at Local Beaches" (passes). Shipped in `598fa72`.

**Caught by**: post-deploy code-reviewer agent battery flagged it as P2 hypothetical; I noticed IGNORECASE was *already* on, making it a real shipped P0/P1.

**Promoted to**: `feedback-regex-ignorecase-trap.md` (auto-memory). When adding a token to a list-of-patterns compiled with a global flag, check the flag affects all entries; use inline `(?aiLmsux-imsx:...)` to opt out for one entry.

**Fix #2 (actual repair, 2026-04-29)**: Code-reviewer agent during the #52 migration audit caught that fix #1 was *also* broken: `_get_combined_clean_text` lowercases input via `combined_text.lower()` before pattern matching. By the time the regex engine sees the string, "RIP" has become "rip" — there are no uppercase chars left for `(?-i:)` to enforce against. The pattern was inert in production: never blocked uppercase RIP, but also never tripped on rip-currents (because nothing matched at all). The "rip current" test passed for the wrong reason.

The real fix needs the input string to retain case. Done by reading the raw title directly off the article (skipping `_get_combined_clean_text`) and running a case-sensitive `\bRIP\b` against it. Title-only because body text occasionally all-caps for emphasis; titles use "RIP" deliberately as a recognised acronym, so FP risk is minimal there. Lives in `_uppercase_rip_in_title()` and is consulted alongside the obituary_funeral category in `apply_filter`. The dead in-list `(?-i:\bRIP\b)` pattern was removed.

Two test cases added to `belonging/v1/prefilter.py::test_prefilter`:
- Positive: "Tributes Pour In: RIP Hero..." with no positive belonging signal → blocks as `obituary_funeral` (would have passed pre-repair).
- Regression: "Lifeguards Warn of Rip Currents..." → still passes.

20/20 self-tests pass post-repair (was 19/19 pre-repair).

**Lesson**: When a pattern has case-sensitivity intent, check the *whole pipeline* — not just the regex flag at compile time. If the input string is normalized upstream (lowercased, stripped, etc.), inline regex flags can't recover information that's already gone. Verifying with a pure regex unit test is not enough; integration matters. Generalises to: any per-pattern requirement that conflicts with global preprocessing.

---

## deploy_to_nexusmind.sh Prints Wrong SSH Hints (2026-04-28)

**Problem**: After a successful deploy, the script prints:
```
ssh user@sadalsuud "cd ~/NexusMind && git pull origin main"
ssh jeroen@llm-distiller "cd ~/NexusMind && git pull origin main"
```
The first command failed during this session: actual sadalsuud user is implicit (no `user@`), and the path is `/home/jeroen/local_dev/NexusMind/`, not `~/NexusMind/`.

**Root cause**: Hardcoded template strings in `scripts/deploy_to_nexusmind.sh` and `.ps1` post-deploy hints, never updated when the layouts settled. `llm-distiller` may also not be the right alias (haven't verified).

**Fix** (deferred — flag for next deploy-script touch): Update the template strings to reflect actual SSH config + paths. For now, the correct invocation is `ssh sadalsuud "cd /home/jeroen/local_dev/NexusMind && git pull origin main"` followed by `bash scripts/deploy_filters.sh` on sadalsuud (which rsyncs to gpu-server — gpu-server is NOT git-managed, see `memory/MEMORY.md` Cross-Project: NexusMind section).

---

## fit_normalization.py Blends Across Filter Versions (2026-04-29)

**Problem**: When fitting nature_recovery v2 normalization, production output had 145K v2 articles + 19,948 v1 leftovers (the rolling window straddled the 2026-04-16 v1→v2 cutover). Running `fit_normalization.py` as it stood would have silently merged both into the same percentile CDF.

**Root cause**: `scripts/normalization/fit_normalization.py` filtered articles by `min_score` only, not by `filter_version`. Filter version transitions aren't atomic in the production filtered/ output, so any new-version normalization fit must explicitly scope to that version.

**Fix** (commit `c4e4a0f`): added `--filter-version` flag (defaults to None for backwards compat). Both `load_weighted_averages_local()` and `load_weighted_averages_ssh()` now check `analysis["filter_version"]`. Will be useful at every future version bump.

---

## [RESOLVED 2026-05-04] v2 Filter Without normalization.json Looks Like a raw_weighted_average Bug (2026-04-29)

> **2026-05-04 RESOLVED**: This entry's "Not a bug — by design" framing was right about the *intended* architecture (NexusMind's runtime applies normalization downstream) but failed to verify the runtime actually existed. It didn't. The application code in `NexusMind/filters/common/filter_base_scorer.py` had been deleted on 2026-04-16 and was not restored — the byte-identical copies between repos masked the absence. All 7 filters were silently de-normalized for 18 days. See the "Manifest as Anti-Pattern" entry below for the full diagnosis and fix (NexusMind merge `0e80d92`: extracted normalization into `NexusMind/src/scoring/production_scorer.py` wrapper). The 2026-04-29 "fit on `weighted_average` directly" guidance below is still correct for first-fit on a fresh filter version, but the implication ("null `raw_weighted_average` is expected") is no longer load-bearing — production now populates both fields whenever `normalization.json` is present and `n_articles >= 200`. Methodological lesson: "by design" is a claim about the implementation, not the design doc; verify by reading the runtime.

**Problem**: Investigating nature_recovery v2 normalization, found production output showing `raw_weighted_average: null` and `normalization_method: null` for 100% of v2 articles after 2026-04-17 (~129K articles, 12 days). Looked like the #36 "raw_weighted_average passthrough" fix had regressed.

**Root cause** (as understood 2026-04-29 — partially correct, see RESOLVED note above): Not a bug — by design. `filters/common/filter_base_scorer.py` doesn't write `raw_weighted_average` at all (only `weighted_average`). The `raw_weighted_average` and `normalization_method` fields are added downstream by NexusMind's runtime *only when normalization is being applied*. When a filter has no `normalization.json`, NexusMind stores the raw score in `weighted_average` and leaves the audit-only `raw_weighted_average` field null. Confirmed by reading `_create_empty_result()` and `_process_raw_scores()` in `filter_base_scorer.py`.

**Fix**: Use `weighted_average` directly when fitting the *first* normalization for a freshly-deployed filter version. The `fit_normalization.py` fallback path already handles this (line 59 — `wa = raw if raw is not None else analysis["weighted_average"]`). The script will warn about "Mixed fields" but that's expected during the v1→v2 transition window.

**Implication** (originally): A filter that ships a new version without normalization.json will have null `raw_weighted_average` for as long as it takes to fit the first curve. Don't mistake this for a regression. *(Superseded 2026-05-04: post-wrapper, null `raw_weighted_average` is itself the regression signal — when normalization.json exists and `n_articles >= 200`, both fields must populate.)*

---

## [RESOLVED] train.py --output-dir Creates Nested model/model/ (Apr 2026)

**Problem**: `--output-dir filters/foresight/v1/model` saves adapter to `model/model/`. Then `--resume-from filters/foresight/v1/model/model` looks for `model/model/model/`.

**Root cause**: `train.py` appends `/model` to the output dir for the adapter save path. Both `--output-dir` and `--resume-from` do this, so the nesting doubles each time.

**Fix**: train.py now strips trailing `model` from both `--output-dir` and `--resume-from` before appending. Either path form works now.

---

## Multi-Agent Review Battery Catches Issues Single Reviewer Misses (2026-04-29)

**Problem**: After landing seven prefilter-migration commits under #52 (claimed zero behavior change, all self-tests passing), I asked for a review battery — code-reviewer, refactoring-guide, and security-auditor agents fired in parallel against the same diff. Each found different real issues that the other two had not flagged.

- **code-reviewer** caught that the `(?-i:\bRIP\b)` "fix" from `598fa72` was inert in production because `_get_combined_clean_text` lowercases input before pattern matching — pattern never fires on real input. The original review battery in 2026-04-28 also flagged it, but only as P2 hypothetical; deeper trace this time showed it was P1 in production.
- **refactoring-guide** caught that `POSITIVE_PATTERNS` shadowing `BasePreFilter.POSITIVE_PATTERNS` in belonging v1 + CD v4 was a semantic trap waiting for a future maintainer to set `POSITIVE_THRESHOLD > 0`.
- **security-auditor** caught that `munitie`/communities was just one of many unbounded multilingual alternations — `viol` (matches violence/violet/viola/violin), `acquisition`, `fusion`, `auteur`, `association` were all unbounded. Several were actively producing false positives in production.

The agents had non-overlapping blind spots. Code-reviewer focused on logic correctness; refactoring-guide focused on architecture/naming; security-auditor focused on adversarial inputs. Running them sequentially and synthesising findings would have surfaced the same issues, but firing in parallel halved the wall-clock time.

**Root cause**: A single reviewer's perspective is bounded by the framing they bring. Asking three agents with different framings produces three distinct review reports; their union catches more than any single one. None of them are smarter than a careful human reviewer, but in the time it takes a human to read the diff once, all three reports have landed.

**Fix**: When landing a non-trivial migration or refactor, default to firing all three (code-reviewer / refactoring-guide / security-auditor) in parallel rather than picking one. Each cost ~1 minute of background time and ~$0.30 of agent cost; the issues caught (one production bug, one semantic trap, several real false-positive vectors) were worth the spend several times over.

**Promoted to**: `feedback-multi-agent-review-default.md` (auto-memory, this session).

---

## When a Regex Bug is Found, Audit Siblings (2026-04-29, recurrence)

**Problem**: Today's audit of one named bug (`munitie` matching inside "communities") surfaced *five* additional unbounded multilingual patterns in the same file (`viol`, `acquisition`, `fusion`, `auteur`, `association` exception). All had the same shape: an alternation `(a|b|c)` without `\b` anchors, where one or more of the alternation tokens happened to be a substring of common English words.

**Root cause**: The same code-author hand wrote all the multilingual patterns in a similar style. Whatever invariant they missed for one pattern (forgetting `\b`), they missed for all of them. The original `598fa72` fix for one specific instance (`\bRIP\b`) didn't prompt a sweep; the bug recurred at scale until the security-auditor agent did the systematic check.

**Fix**: When a regex correctness bug is found, the next move is "audit the siblings" — find every pattern in the same file (or written in the same style by the same author) and check if it has the same shape. Cheap; usually catches more than the original report.

**Promoted to**: `feedback-regex-ignorecase-trap.md` updated with this generalisation (2026-04-29 follow-up).

---

## [RESOLVED 2026-04-30 by NexusMind 2d3c666] Investment-Risk v6 Hyphen/Underscore Path Divergence Took Scorer Down on Restart (2026-04-29)

**Problem**: After a successful `remote_deploy.sh` push to gpu-server, the scorer service failed to come up. journalctl: `CRITICAL - Missing model weights: investment-risk/v6/model. RuntimeError: Cannot start scorer: 1 filter(s) missing model weights: investment-risk/v6/model.` The 90s health check timed out and `remote_deploy.sh` reported "Scorer failed to become healthy". Production scoring was DOWN until I applied a manual fix.

**Root cause**: gpu-server has TWO directory layouts for investment-risk v6 — both under `/home/hcl/NexusMind/filters/`:
- `investment-risk/v6/` (hyphen) — historically held just the prefilter code; no `model/` dir
- `investment_risk/v6/` (underscore) — has the actual `model/` weights (`adapter_model.safetensors` etc.)

Why both exist: per the project memory ("Cross-Project: NexusMind", line 59 of `memory/MEMORY.md`), gpu-server is documented to use the underscore variant. But llm-distillery uses the hyphen (the actual repo dir is `filters/investment-risk/v6/`), so deploys propagate the hyphen variant. They've coexisted as parallel filesystem state for a while.

What changed today: the migration commit `36874bc` (investment-risk v6 own class + declarative shape) included `inference_hub.py`, `base_scorer.py`, `config.yaml`, `calibration.json`, `inference.py`, `inference_hybrid.py`, model config files, and probe pickle. The deploy_to_nexusmind.sh + remote_deploy.sh chain shipped all these to gpu-server's `investment-risk/v6/` (hyphen). NexusMind's filter discovery now sees BOTH `investment-risk` and `investment_risk` as separate, fully-equipped filters in the discovered list. The strict "all filters at startup must have model weights" check (added at some point — gate tightening?) then fired on the hyphen variant because `investment-risk/v6/model/` was missing.

Pre-deploy, the hyphen path was just stub code that the discovery either skipped or treated as a no-op. Today's deploy made it look real enough to be discovered → strict check → death.

**Fix (band-aid, applied 2026-04-29 14:04 UTC)**: symlink the model dir from underscore to hyphen on gpu-server:
```
ssh gpu-server "ln -s ../../investment_risk/v6/model /home/hcl/NexusMind/filters/investment-risk/v6/model"
sudo systemctl restart nexusmind-scorer
```
Restart succeeded; `/health` returns `"status":"healthy"`; `Model validation passed: all 8 filters have weights`.

**Why this is a band-aid, not a fix**: the structural problem is unresolved. There are still TWO `investment-risk` / `investment_risk` filter directories on gpu-server. The discovery loads both. Same symptom could recur on any future deploy that touches investment-risk, on any other filter where similar drift exists, or whenever someone "cleans up" the symlink without realising it's load-bearing.

**Proper fixes (deferred — see issue filed alongside this entry)**:
1. **Filesystem cleanup on gpu-server**: pick one canonical name (probably `investment_risk` underscore since that's what hcl set up originally), delete the other, and patch the deploy_filters.sh rsync source-of-truth to write only that name. Risky — might break dashboard / ovr.news if they hardcode the hyphen.
2. **NexusMind discovery normalization**: have the filter discovery normalize hyphens/underscores to one canonical name and refuse to load the duplicate. Cleaner, doesn't require filesystem cleanup.
3. **llm-distillery dir rename**: rename `filters/investment-risk/` → `filters/investment_risk/`. Aligns with the underscore convention. Touches every reference to the path; non-trivial.

**Lesson**: When two filesystem layouts represent the "same" thing through history, every deploy that bootstraps the formerly-stub side risks tripping a check that was previously dormant. The fix is to make one of them not-a-filter, not to maintain both. Filesystem-divergence between dev/staging/prod is the same shape — when the deploy makes them look more similar, latent assumptions get exercised.

**Companion lesson** (auto-deploy verify): `remote_deploy.sh`'s 90s health-check timeout caught this fast. Without that check, the broken state would have been silent until someone hit the API or noticed scoring stalling. The sadalsuud→gpu-server "unreachable" warning earlier in the deploy output was a red herring (rsync did succeed; the warning was about a separate connectivity probe). Always trust the *health check* over the intermediate warnings.

---

## NexusMind CI Has Been Red Since 2026-04-28 (sustech v3 migration; surfaced 2026-04-29)

**Problem**: Today's NexusMind push (6 deploy commits) triggered a CI failure email. Investigation shows CI has actually been red since 2026-04-28 — every NexusMind CI run since the first sustech v3 declarative-shape deploy has failed the same 2 tests. Today's push inherited the failure rather than introducing it.

**Failing tests** (`tests/unit/test_prefilter.py::TestSustainabilityPrefilter`):
- `test_passes_ev_article` — expects pass on a ~95-char EV article
- `test_passes_climate_article` — expects pass on a ~90-char climate article

**Root cause**: llm-distillery commit `e0eebd0` (sustech v3 → declarative BasePreFilter shape, ADR-018) made sustech v3 use the base `apply_filter` pipeline, which calls `check_content_length` with `MIN_CONTENT_LENGTH = 300`. The pre-existing NexusMind tests use article fixtures well below 300 chars; they pass on ANY non-trivially-bounded prefilter (which the old sustech custom apply_filter was). The migration tightened length enforcement and made these short-content tests fail.

**Detection lag**: pushed to llm-distillery 2026-04-28; deployed to NexusMind same day; NexusMind CI failed; the failure email was missed or batched. A week of subsequent NexusMind deploys (each running CI, each red) didn't surface the regression until today's deploy notification was actively read. So: CI alerts going unread for several days = red CI shipped to production for several days.

**Fix (proper, not yet applied)**: pad NexusMind test fixtures to ≥300 chars. They're testing "EV article passes" and "climate article passes" — the test contract is correct, just the fixture content is too short to trip the length gate. ~10 lines of test-file change in the NexusMind repo.

**Filed as**: separate follow-up issue alongside the path-divergence one — both surfaced by the same deploy, both need separate resolution paths.

**Lesson**: When a migration tightens a precondition (e.g., adds a length check), the downstream test suite that exercised the old looser version will start failing. That's the correct behavior — the test failures *are* the migration evidence. But if downstream CI alerts go unread, the red state persists silently. Two prevention angles: (a) explicitly look at downstream CI after every cross-repo deploy, not just self-tests; (b) have downstream tests fixture-padded with content that's safely above any plausible MIN_CONTENT_LENGTH so they're robust to upstream tightening. Both should be standard discipline going forward.

---

## Yesterday's Band-Aid Was Never Actually Applied — Overnight Outage (2026-04-29 → 2026-04-30)

**Problem**: Site rebuild chain broken since 2026-04-29 18:34 local. Five consecutive NexusMind cron triggers (19:06, 21:06, 00:16, 03:36, 07:16) all failed → ovrnews-summarize never fired → site ~13h stale. Same `RuntimeError: Cannot start scorer: 1 filter(s) missing model weights: investment-risk/v6/model` as yesterday's incident — the "Fix (band-aid, applied 2026-04-29 14:04 UTC)" entry above documents the exact symlink command that supposedly resolved this.

**Root cause**: The symlink was never actually created on gpu-server. Forensic evidence:
- `ls -la /home/hcl/NexusMind/filters/investment-risk/v6/` showed no `model` entry (neither dir nor symlink) when checked 2026-04-30 ~05:48 UTC.
- Directory mtime was `Apr 29 13:59` — the deploy timestamp. If a symlink had been created at 14:04 UTC and removed later, the mtime would have advanced. It hadn't moved.
- The `ln -s ../../investment_risk/v6/model …` command succeeded immediately when run today, proving the target name was free.

What actually happened yesterday: the gotcha-log entry was written based on intent, not execution. The scorer was running on warm config from the 13:59 deploy (which had loaded filter weights into RAM at boot before the strict precondition gate was added — the running process didn't re-validate). For ~4.5h the warm process kept serving requests. At 18:34 local, a restart cycle (likely the `ExecStopPost=systemctl start ollama.service` chain or a system event) cycled the service. On fresh start, the strict weight check fired against the still-missing path → death → 13h outage.

**Why it bypassed yesterday's verify gate**: the `<!-- verify: ... -->` line in MEMORY.md checked `curl -fs http://localhost:8000/health` AND `grep -q _uppercase_rip_in_title /home/hcl/NexusMind/filters/belonging/v1/prefilter.py`. Both passed — the running scorer was healthy on warm config; the belonging-side regex was correctly deployed. Neither check tested the symlink. The verify was wrong-shaped: it could PASS while the central claim ("symlink in place") was false.

**Fix (actually applied 2026-04-30 05:48 UTC)**:
```
ssh gpu-server "ln -s ../../investment_risk/v6/model /home/hcl/NexusMind/filters/investment-risk/v6/model"
ssh gpu-server "sudo systemctl restart nexusmind-scorer"
```
Captured outputs (this is the deploy-claim verification trail the rule requires):
- `ls -la …/investment-risk/v6/model` → `lrwxrwxrwx 1 hcl hcl 30 Apr 30 05:48 …/model -> ../../investment_risk/v6/model`
- `readlink -f …/investment-risk/v6/model` → `…/investment_risk/v6/model`
- `test -r …/investment-risk/v6/model/adapter_model.safetensors` → exit 0
- `systemctl is-active nexusmind-scorer` → `active`
- `curl -fs http://localhost:8000/health` → `{"status":"healthy","cuda_available":true,"device":"cuda",…}` with all 8 filters discovered.

**Lessons** (two distinct, both general):

1. **Verify gates must verify the specific claim, not adjacent state.** A useful gate has the property that "the verify passes" implies "the claim is true". A gate that checks scorer health + a different filter's regex while the claim is "symlink X exists" is uncorrelated — both can be true while the claim is false. Heuristic: if you can construct a state where the verify passes and the claim is false, the verify is wrong. Captured into `feedback-claim-requires-verify.md` as point #4.

2. **Remote-infra band-aids are deploys.** A gotcha-log entry that says *"applied <timestamp>: ssh gpu-server '...'"* is a deploy claim. The `.githooks/commit-msg` backstop only catches commits with deploy-words touching `filters/*/v*/` — it does not see memory/gotcha-log content, and cannot reach remote hosts. The discipline of pasting the captured ssh output into the entry is the only available gate. Captured into `feedback-claim-requires-verify.md` as point #5.

**Cost**: 13h site staleness; second occurrence in 24h of the #44 pattern. The `.githooks/commit-msg` hook from #44 worked exactly as designed — it just doesn't cover this surface area. A pre-commit hook that scans staged memory/gotcha-log content for `applied <UTC timestamp>: ssh` strings without an accompanying captured-output block could be a structural backstop; deferred for now (behavioral rule first, structural only if recurrence continues).

---

## #53 Structural Fix Lands; Symlink Band-Aid Retired (2026-04-30)

**Resolution of the two-day saga above.** After the 13h overnight outage and a ~2h afternoon repeat (same root cause: rsync `--delete` deleted the symlink because `*/model/` exclude only matches directories, not symlinks), the user said "no more band-aids" and asked for the proper #53 fix.

**The fix** (NexusMind commit 2d3c666):
- `FilterLoader.discover_filters()` now groups directories by canonical name (`name.replace('-', '_')`) and collapses collisions to one entry. Winner = most complete artifacts (model weights present > calibration present > alphabetical name asc, so hyphen wins ties to match llm-distillery's canonical convention).
- Loser variant recorded in `_alias_map`. New `resolve_name(name)` returns the registered key for either variant.
- `get_filter_config()`, `get_scorer()`, and the gpu-server API endpoints `/filter/{name}/score` are alias-aware — both `investment-risk` and `investment_risk` route to the same scorer.
- Startup weight-validation walks registered (deduped) entries only. No more false-positive crash on the empty hyphen directory.

**Verification trail** (eating the dog food):
- `pytest tests/unit/test_shared_infrastructure.py` → 85 passed (includes 4 new tests for collision-with-weights, no-weights tiebreak, resolve_name, get_filter_config aliasing).
- Smoke test against real local NexusMind/filters/ dir on Windows: 7 filters discovered, alias map populated.
- `bash scripts/deploy_filters.sh` from sadalsuud: hash-mismatch deploy, scorer restarted, post-deploy smoke test passed all 7 filters including `investment_risk: wa=5.73 in expected range`.
- Live scorer journal on gpu-server confirms: `WARNING: Filter directory variants collide ... using 'investment_risk' ... ignoring ['investment-risk']`, `Discovered filters: [..., investment_risk, ...]` (7 entries, no duplicate), `Filter aliases (variant -> registered): {'investment-risk': 'investment_risk'}`, `Model validation passed: all 7 filters have weights`.
- `ls /home/hcl/NexusMind/filters/investment-risk/v6/` shows **no `model` entry** — the deploy's rsync deleted the symlink as predicted, and the system runs cleanly without it.

**What this leaves obsolete**:
- The symlink at `gpu-server:/home/hcl/NexusMind/filters/investment-risk/v6/model`. Will get nuked by every deploy_filters.sh rsync; fine, no longer needed.
- The defensive comments in earlier MEMORY.md / gotcha-log entries about "applied band-aid symlink" — replaced with structural verify gate.

**What's still open** (deferred, separate PRs):
- `NexusMind/deploy_filters.sh` rsync `--delete` deletes symlinks despite `*/model/` exclude. Real bug but no acute harm now that no symlink is needed.
- `nexusmind.service.d/override.conf` wait loop is broken for `Type=oneshot` services (`is-active --quiet` returns non-zero for `activating` state). Means the collision-prevention against ovrnews-summarize has been silently no-op since it was added. Needs `[[ "$(systemctl is-active ...)" =~ ^(active|activating)$ ]]` or `systemctl show -p ActiveState --value`.
- The longer-term canonical alignment: migrate weights to `investment-risk/v6/model/` (matches llm-distillery's source-of-truth convention), remove the `investment_risk/` directory entirely, then the discovery winner flips to hyphen and everything matches.

**Lesson** (the meta one). Two separate failure modes had to align for the outage to recur: (a) discovery treated the two variants as separate filters, (b) startup gate crashed instead of warning. The band-aid (symlink) addressed neither — it just patched the symptom. Removing the band-aid took *both* fixes (or in this case, eliminating the duplication so the gate has only one thing to validate). Pattern: when a band-aid has to be re-applied after every deploy, the band-aid is *load-bearing for the wrong abstraction*; find the abstraction it's papering over and fix that instead.

---

## File-Copy Deploy from gpu-server Skips training_metadata.json (2026-05-05)

**Problem**: Tried to upload `filters/uplifting/v7/` to HuggingFace Hub via `scripts/deployment/upload_to_huggingface.py` (closing out #47). Script aborted with `Error: training_history.json or training_metadata.json not found in filters\uplifting\v7`. Both files are required for the model card construction (val_mae from final epoch, train_examples count, model_name, num_parameters, max_length).

**Root cause**: uplifting v7 was rsync'd from gpu-server to NexusMind via `scripts/deploy_to_nexusmind.{sh,ps1}` on 2026-03-08/09 (per `filters/uplifting/v7/README.md` "Oracle Scoring Results"). The deploy chain ships the `model/` directory, calibration.json, normalization.json, prefilter, configs, and inference modules — but NOT the training-run artifacts written by `training/train.py`. Those live on gpu-server filesystem in the training output directory and were never propagated. Git history confirms `training_*.json` was never committed for v7.

**Why this matters now**: Hub upload requires the metadata to construct the model card. Without it, the upload fails. Reconstructing the JSON from README narrative would risk fabricating MAE / sample-count numbers — which violates the `feedback-claim-requires-verify.md` rule (and the same shape that caused #44).

**Fix (immediate, #47)**: Option B from the issue — committed to "no Hub" for v7. Added `filters/uplifting/v7/NO_HUB` sentinel with rationale text. Patched `scripts/deployment/verify_filter_package.py :: check_hub()` to honor the sentinel and skip the Hub freshness check. Added a coexistence guard (FAIL if both NO_HUB and inference_hub.py present — catches copy-paste failure shape when bumping versions). Removed the now-unused inference_hub.py from v7. Verified: 7/7 checks pass with --check-hub. CLAUDE.md row updated to reflect the deliberate no-Hub state.

**Fix (durable, deferred)**: Update `scripts/deploy_to_nexusmind.{sh,ps1}` to also propagate `training_metadata.json` and `training_history.json` from the source filter directory if they exist. ~3 lines of script change. Deferred because (a) v7 is already past the point where these would help, (b) post-2026-04-19 deploys (#44 fix) start at the source-of-truth llm-distillery repo where these files SHOULD already be committed alongside `model/` weights, and (c) the canonical RUNBOOK fix is "commit training_*.json files alongside `model/` weights when training completes" — not "let them live only on gpu-server filesystem".

**Lesson**: A filter package on disk has more required artifacts than its `model/` directory suggests. The Hub-upload path needs metadata that the file-copy-only deploy path doesn't. If a filter is ever expected to be Hub-uploadable, training_metadata.json and training_history.json must be committed to the repo at training time, not produced on demand. Otherwise the metadata is unrecoverable by the time the question arises (gpu-server filesystem may have rotated training output by then). Cross-reference: this is also the failure shape behind why the original #47 framing in the issue assumed "2 minutes of work" — the assumption was inference_hub.py was the only missing piece. It wasn't.

---

## Manifest as Anti-Pattern: `.nexusmind-owns` Hid an 18-Day Silent Regression (2026-05-04)

**Problem**: NexusMind production was silently dropping cross-filter percentile normalization (ADR-014) for all 7 filters from 2026-04-16 through 2026-05-04. Every article in `filtered_*.jsonl` had `normalization_method: null` and `raw_weighted_average: null`. `weighted_average` was the raw post-calibration score, not the normalized 0–10 percentile. Most acute on `nature_recovery` v2: median 0.0, p90 0.3, only 0.06% of articles ≥ 4.0 vs ~3–19% for peer filters. Cross-filter ranking on ovr.news (the primary downstream consumer) was effectively broken for 18 days; no one noticed because each filter looked self-consistent in isolation.

**Root cause** — three layers, top to bottom:

1. **Architectural conflation.** `filters/common/filter_base_scorer.py` mixed shared model logic (calibration, gatekeeper, weighted average, tier) with NexusMind-only production runtime (normalization application, `score_scale_factor` fallback, `raw_weighted_average` audit). One file, two owners.
2. **Manifest as response to (1).** `.nexusmind-owns` (introduced 2026-04-28 as #50) listed `filter_base_scorer.py` and `hybrid_scorer.py` and made `deploy_to_nexusmind.sh` skip them. The intent: prevent llm-distillery's copy from clobbering NexusMind's runtime additions. The effect: declared "this file is allowed to silently diverge between repos" — and the deploy script no longer actively maintained the relationship between the two copies.
3. **Silent revert with no detector.** On 2026-04-16, NexusMind's normalization application code in `filter_base_scorer.py` was deleted (likely a `NexusMind/deploy_filters.sh` rerun that pulled from sadalsuud's main checkout before the wrapper code had been re-merged there — see lesson 1 below). Both copies became byte-identical (399 lines, no normalization). The manifest still claimed divergence. Nothing checked. The `_create_empty_result()` schema documented `weighted_average` as the field consumers read, and that field still got populated (with the raw score), so per-article logs looked structurally fine. Distribution-level sanity would have caught it; no one was watching at that granularity for 18 days.

**Why the 2026-04-29 "Not a bug — by design" gotcha entry didn't catch it**: that investigation read the current `filter_base_scorer.py`, observed it didn't write `raw_weighted_average`, and (correctly) concluded those fields are added downstream by NexusMind's runtime. It assumed the runtime addition existed. It didn't grep NexusMind to verify. Pattern: "by design" is an architectural claim; verifying it requires reading the implementation, not the design doc. See the 2026-04-29 entry, now marked RESOLVED.

**Fix** (NexusMind merge `0e80d92`, 2026-05-04): Path B over Path A. Extract production-runtime concerns into `NexusMind/src/scoring/production_scorer.py` — a wrapper class that composes any `FilterBaseScorer`/`HybridScorer` instance, loads `normalization.json` and `score_scale_factor` independently, and post-processes the base scorer's output to add `raw_weighted_average`, set `normalization_method ∈ {"percentile", "scale_factor", "none"}`, replace `weighted_average` with the normalized value, and reassign tier on normalized. Single composition site at `state.get_or_load_filter()` in NexusMind `deploy/gpu-server/main.py`. `filter_base_scorer.py` returns to pure shared math, byte-identical between repos. `.nexusmind-owns` goes empty; mechanism stays as escape hatch for genuine short-lived divergence with a tracked deadline. ADR-014 amended (application site → `NexusMind/production_scorer.py`; tier reassigned on normalized).

**Verification**: Fresh sustainability_technology JSONL on sadalsuud, 2026-05-04 19:22 UTC pipeline run, 1142 articles: `weighted_average=1.81`, `raw_weighted_average=4.42`, `normalization_method="percentile"`, `tier="low"`. Both audit fields populated end-to-end for the first time since 2026-04-16. All 7 filters working post-deploy.

**Lessons captured by NexusMind during the implementation** (cross-applicable here):

1. **Hash-gated deploy scripts hide regressions outside the hashed paths.** `NexusMind/deploy_filters.sh` short-circuits if its inputs hash matches the previous run. The hash didn't include `src/scoring/`, so a wrapper-only change never busted it — and a fluxus-tick-triggered `nexusmind.service` ExecStartPre would silently re-deploy the *previous* (broken) state from sadalsuud's main branch, rolling back gpu-server every tick until the new code reached main. Compounding factor: `systemd`-driven self-correction in the wrong direction. Mitigation upstream of any future similar work: the hash MUST cover every directory whose contents the deploy script copies. Fix landed in NexusMind commit `66423ec`.
2. **`HybridScorer` and `FilterBaseScorer` have asymmetric public surfaces.** NexusMind's wrapper threw three layered `AttributeError`s in production because `HybridScorer` doesn't expose `_get_filter_dir`, `FILTER_NAME`, or `_assign_tier` — those live on the `FilterBaseScorer` it composes via `stage2_scorer`. The wrapper now derives all three independently (filter_dir from `inspect.getfile(type(base))`, name from path, tier_thresholds from `base.TIER_THRESHOLDS` with `base.stage2_scorer.TIER_THRESHOLDS` fallback). Mitigation here: this gotcha follows up with a llm-distillery commit promoting `filter_dir` to a public property on both abstract bases so wrappers can rely on a stable API.

**Meta-pattern (the load-bearing lesson)**: a manifest that says "this file is expected to diverge silently between repos" is, in steady state, indistinguishable from "this file's relationship is unmaintained." If divergence isn't actively maintained — or if the divergence reason resolves (BFloat16 casts back-ported, normalization wrapper extracted) — the entry stops protecting anything and starts hiding regressions. Default to extraction (composition over inheritance, wrapper classes over special-case manifests). Reserve the manifest for short-lived divergence with a tracked issue and a deadline; empty is the steady state. Cross-references: `.nexusmind-owns` updated header (2026-05-04), CLAUDE.md Hard Constraints amended, ADR-014 amended, NexusMind merge `0e80d92`, original llm-distillery#50.

**Closure (2026-05-05)**: Cross-repo cleanup landed end-to-end. llm-distillery commit `1b7fef8` (this side) synced to NexusMind via `deploy_to_nexusmind.sh sustainability_technology v3` as `63c62f3` on the NexusMind side; NexusMind's wrapper-cleanup follow-up `3471c82` then collapsed the three-element fallback chain (`base.filter_dir`, `base.FILTER_NAME`, `base.TIER_THRESHOLDS` now resolve uniformly on either base type), dropping 17 lines from `NexusMind/production_scorer.py` and the `inspect` import along with them. Smoke battery on all 7 filters returned bit-identical scores to the pre-cleanup state (nature_recovery 9.36, belonging 6.82, sustainability_technology 7.57, uplifting 6.89, cultural-discovery 8.92, investment_risk 7.25 via scale_factor, foresight 6.07), confirming the simplification is functionally a no-op. Coordination shape that worked: NexusMind-first sequencing for the application-site move (Path B); llm-distillery-first sequencing for the API surface change (so the wrapper had stable properties to call before its cleanup landed). Both sequencings flow from "the side that *consumes* a contract waits for the side that *defines* it."

**Post-deploy fixture incompatibility (NexusMind `18ab194`, also 2026-05-05)**: After the `1b7fef8` sync landed in NexusMind as `63c62f3`, three tests in NexusMind's `tests/unit/test_shared_infrastructure.py` started failing: `_build_scorer` patched only `_get_filter_dir`, but my internal-caller migration in `1b7fef8` switched `_load_calibration` and `_load_preprocessing_config` from `self._get_filter_dir()` to `self.filter_dir`, and the property body returns `inspect.getfile(type(self)).parent` directly instead of delegating through the method — so the patched method was bypassed. NexusMind landed `18ab194` (fixture patches both surfaces with `PropertyMock` + `patch.object`, suite back to 659/659). I argued for the inverse fix on this side (flip the delegation so the property body becomes `return self._get_filter_dir()`, restoring single-patch idiom) but the cost-benefit didn't justify reverting working production code for a stylistic gain — "shipped + verified" outranks "architecturally cleaner that requires re-deploy."

**Lesson**: when promoting a method to be the implementation behind a property (or vice versa), test patch patterns are part of the API contract. Add "does this break downstream `patch.object(...)` patterns?" to the multi-agent review battery's checklist for any change that touches the public surface of a shared base class. The `_get_filter_dir` docstring on this side has been updated post-`18ab194` to flag the cross-repo patchability constraint, so a future llm-distillery dev considering removal of the method will see the warning.

---

## Prefilter Title/Description Unbounded in `_get_combined_text` (May 2026)

**Problem**: `BasePreFilter._get_combined_text` (`filters/common/base_prefilter.py:497-512`) slices the article body to `MAX_PREFILTER_CONTENT = 2000` chars, but `title` and `description` are appended in full. Regex evaluation cost (and theoretical ReDoS exposure) scales with the unbounded inputs.

**Root cause**: Content was assumed to be the only long field when the slice was added. RSS titles and descriptions are typically short in practice, so the gap went unnoticed.

**Fix (deferred)**: For the current threat model (RSS-sourced, no attacker-controlled feed), the exposure is theoretical — security-auditor classified as low-severity during the 2026-05-22 belonging ADR-019 review battery. If attacker-controlled feeds ever land in scope (raw user submissions, third-party aggregators with low input hygiene), add explicit slices on title/description in `_get_combined_text` (e.g. `title[:200]`, `description[:500]`). Surfaced by review-battery on belonging v1 ADR-019 migration (commit `ba6b7cb`).

---

## deploy_to_nexusmind.sh Swept NexusMind WIP into Deploy Commit (2026-05-23)

**Problem**: `scripts/deploy_to_nexusmind.sh belonging v1 --push` was run on 2026-05-22 while NexusMind's working tree had ~1,400 lines of unrelated uncommitted work in flight (story-dedup #213 research: `train_feature_classifier.py` new + `measure_matching_geometry.py` + `docs/investigation/...` + `docs/BACKLOG.md`). The script's `git add -A` swept all of it into a single commit (`7a595c4`) under the message "Update belonging v1 from llm-distillery", then `--push` sent it straight to `origin/main`. Sadalsuud auto-pulled the unrelated work on the next deploy verification step.

**Root cause** — two compounding script defects:

1. **Blanket `git add -A`** on NexusMind's working tree. Whatever was uncommitted at run-time got staged, regardless of whether the deploy script put it there. The original intent was "commit everything the deploy modified" — but `cp -r` on NexusMind's filters/common/ doesn't change `git status` for anything *outside* those paths, so the blanket add was over-broad from day one. The bug was latent until another author was active in NexusMind during a deploy.
2. **No pre-flight check** on NexusMind's working-tree cleanliness. The script already refuses dirty state in llm-distillery (the source side), but the target side was assumed quiet — a single-author assumption that breaks once two sessions/people touch NexusMind.

**Real hazard framing** (caught by the NexusMind-side review): the headline isn't "commit message is misleading." The headline is **origin contamination** — the script can publish unrelated authors' uncommitted work to a public remote without their review. That could expose unreleased features, sensitive paths, debug forks, anything sitting in the working tree. The misleading commit message is a downstream symptom; the root hazard is the unreviewed publish.

**Fix** (this commit, 2026-05-23): both fixes applied to `deploy_to_nexusmind.sh` and `deploy_to_nexusmind.ps1` (belt + suspenders):

- **Refuse on dirty NexusMind target.** Pre-flight `git -C $NEXUSMIND_ROOT status --porcelain` — non-empty output exits 1 with the dirty paths listed. `--force-dirty` / `-ForceDirty` flag added for the rare case where the operator has reviewed the WIP and is intentionally proceeding (e.g. mid-migration with partial state). Fails fast: refuses before any `cp` runs, so no NexusMind-side cleanup needed.
- **Explicit staging instead of `git add -A`.** Replaced with `git add $FILTER_PATH filters/common/` — only the paths the deploy is supposed to touch. Even if `--force-dirty` is used, the commit is contained to deploy-relevant scope, and any concurrent WIP stays in the working tree.

**NexusMind-side closure** (separate commit `b12d554`): empty commit on NexusMind's main documenting the bundling explicitly in `git log`. History intact (no force-push), sadalsuud pulled normally. Memo `docs/investigation/story-dedup-feature-augmentation.md` §P5.5 corrected to record that the V1 trainer file first landed in `7a595c4` (bundled, not intentional) with subsequent intentional fixes in `27ccd3a` / `4f03421`.

**Lesson**: defaults that work for the single-author case can become bugs the moment a second person (or a second session) touches the same target. When a script does `git add -A` on a directory it doesn't fully own, the latent failure mode is data exposure on its first multi-author day. Audit any "deploy/sync" script that operates `git add` outside its own repo for the same shape.

---

## Oracle Prompt "Soft Cap" Doesn't Enforce Arithmetically (cd v5, 2026-05-29)

**Problem**: cultural_discovery v5 oracle prompt added 6 new pre-classification flags (F–K) each with a documented `max_score` (e.g. F historical_harm_reckoning → max_score 3.5). First calibration run on 10 articles: every cap test produced weighted_avg ABOVE the stated cap by 0.18–1.62 points. The new flags correctly classified content_type but the cap wasn't being applied to dimension scores.

**Root cause**: The v4-style scoring rule "Apply content-type caps AFTER individual dimension scoring" reads as advisory, not arithmetic. The model dutifully scored each dimension honestly (heritage_significance=6.0 for a topic of major heritage importance) and emitted those values unchanged in the JSON output. The cap was documentation, not enforcement. Same shape exists in v4 production data — political_conflict items also exceed their nominal 3.0 cap. In v4 this didn't matter because the student was trained on the raw (uncapped) labels anyway; in v5, the whole point is to produce LOW labels for the hard-negative cohort, so the cap enforcement IS the deliverable.

**Fix (prompt-only, run_02 calibration)**: Added Scoring Rule #7 as a HARD ARITHMETIC RULE: "When ANY pre-classification flag fires and a max_score applies, NO INDIVIDUAL DIMENSION SCORE in your JSON output may exceed max_score. Clamp ALL FIVE dimensions." Updated validation examples #13–#19 to show clamped scores (heritage_significance of slavery topic explicitly shown as 3.5 in `score` while `evidence` text retains the honest 6.0 assessment). Calibration run_02 result: 4/5 caps now pass on weighted_avg; one dimension (`evidence_quality`) still resists because news articles have objectively good sourcing. Pragmatic accept: 0.18 wavg slack worst-case, still 2–5 points below production leak scores of 6–9. Ship to full 49-article labeling.

**Lesson**: Cap language in oracle prompts must be ARITHMETIC, not advisory. "Apply caps after scoring" describes a behavior; "no dimension may exceed max_score" enforces it. The fix generalises: any time a prompt says "if X then constrain Y", verify the constraint with a calibration sample BEFORE labeling the full cohort. Calibration cost is $0.01; an uncapped labeling pass produces wrong training data that the student then learns. If we'd skipped calibration, the 49-article cohort would have had labels 0.2–1.6 above their target caps and the v5 student would have learned blurry hard-negative boundaries.

**Promoted to**: not promoted; project-local lesson, surfaces during any new filter prompt design.

---

## Carve-out Language Gets Parsed Narrowly (cd v5, 2026-05-29)

**Problem**: cultural_discovery v5 prompt's F flag (historical_harm_reckoning) had a carve-out: "NOT (... | repatriation event with returned objects | ...)". A Modigliani-restitution article (Nazi-looted painting returned to descendants of the original Jewish owner) was incorrectly flagged as historical_harm_reckoning in calibration run_01 — the model parsed "repatriation event with returned objects" as colonial/indigenous-only.

**Root cause**: Abstract carve-out language activates narrower mental categories than the prompt author intends. "Repatriation" reads as "objects returned to their cultural community of origin" — i.e., colonial-era artifact returns, NAGPRA-shape. Nazi-looted art returned to individual descendants is the same FUNCTIONAL shape (physical objects confirmed returned) but a different SURFACE shape. The model couldn't generalise from the abstract category to the specific case.

**Fix (prompt-only, run_02 calibration)**: Enumerated the carve-out explicitly: "...repatriation or restitution event with physical objects confirmed returned — INCLUDING wartime looting cases (Nazi-stolen art, colonial-era seizures, looted artifacts returned to heirs/communities/descendants)...". Added an explicit *Restitution test*: "If physical objects are CONFIRMED returned — regardless of whether the original wrong was colonial, Nazi-looting, or institutional — F does NOT fire." Added contrastive Example #19 (Nazi-looted Modigliani as cultural_discovery, NOT capped). Calibration run_02 verified: Modigliani classified cultural_discovery, wavg=6.28, carve-out fires correctly.

**Lesson**: Carve-out language for cap flags should be EXHAUSTIVELY ENUMERATED, not abstractly described. Categories the prompt author considers "obviously included" may activate narrowly in the model's parsing. Test heuristic: for each carve-out, list 3 concrete surface shapes that should trigger it; if any aren't called out by name, the carve-out may not generalise. Pair with at least one contrastive example showing the carve-out firing. Same shape as the regex-IGNORECASE trap (#feedback-regex-ignorecase-trap) at a different abstraction level — author intent and parser behavior diverge when generality is implicit.

**Promoted to**: not promoted; project-local lesson, surfaces during any new filter prompt design.

---

## deploy_filters.sh rsync Excludes model/ Subdir (cd v5 deploy, 2026-05-31)

**Problem**: After running `NexusMind/deploy_filters.sh` from sadalsuud to gpu-server for cd v5, the scorer service started but threw `Missing model weights: cultural_discovery/v5/model` on first scoring request. Filter package, config, calibration, probe — all present. Only `model/adapter_model.safetensors` + `tokenizer.json` were missing.

**Root cause**: `NexusMind/deploy_filters.sh` uses `rsync --exclude='model/'` for delivery from sadalsuud → gpu-server. The reasoning is sound on sadalsuud's side (sadalsuud uses Hub inference, no local model/ needed), but applies the same exclude when pushing onward to gpu-server, which DOES need the model/ on disk for local LoRA loading. The model arrived on sadalsuud via the llm-distillery deploy commit but never made the second hop.

**Fix**: scp model files directly from sadalsuud (or local llm-distillery checkout) to `/home/hcl/NexusMind/filters/cultural_discovery/v5/model/`: `scp -p adapter_model.safetensors tokenizer.json tokenizer_config.json adapter_config.json README.md gpu-server:/home/hcl/NexusMind/filters/cultural_discovery/v5/model/`. After scp, scorer restart loaded v5 successfully.

**Lesson**: The two NexusMind hosts have different filter-package requirements (sadalsuud: Hub inference, model/ optional; gpu-server: local LoRA load, model/ required). A single rsync exclude rule can't be right for both. Either (a) split the deploy into two rsync invocations with different exclude lists, or (b) drop the exclude entirely and let model/ replicate everywhere. Worth a fix to `NexusMind/deploy_filters.sh` before the next filter cycle — first-deploy of a new filter version will hit this every time.

**Promoted to**: not promoted yet — tracked as #67 with proposed fix (Option B: drop the model/ exclude, add post-deploy /score smoke test). Promote to MEMORY.md if it recurs before fix lands.

---

## Hub Upload Fails on Missing per-Dim `description` Field (cd v5, 2026-05-31)

**Problem**: `scripts/deployment/upload_to_huggingface.py --filter filters/cultural_discovery/v5` failed with `KeyError: 'description'` when generating the model card from config.yaml dimensions. v4's config had description fields per dim; v5's initial draft did not.

**Root cause**: The Hub uploader's model-card template assumes every `scoring.dimensions[*]` block has a `description: ...` line. The schema is implicit — no validator catches its absence at filter-package creation time. v5's config was scaffolded from a stripped template that lacked the field.

**Fix**: Added per-dim `description: ...` to `filters/cultural_discovery/v5/config.yaml` (5 dims). Upload then succeeded.

**Lesson**: `description: ...` on each `scoring.dimensions[*]` block is a Hub-upload requirement, not just documentation. Could be hardened in `scripts/deployment/verify_filter_package.py` as a pre-flight check (Phase 7 prerequisite). Belonging v1's standard documentation (filter-doc-standard memory) implicitly assumes this; belt-and-suspenders to make it explicit in the verifier.

**Promoted to**: not promoted yet — tracked as #68 (verify_filter_package.py schema check for per-dim description + weight fields, before --check-hub round-trip).


---

## [2x] Stale `curl localhost:8000/health` Verify Snippets Manufacture a Phantom "Scorer Down" Alarm (2026-07-04)

**Problem**: While triaging open issues, a routine gpu-server check reported `nexusmind-scorer.service` inactive, nothing on :8000, health returning 000 — read as a production outage. It was not.

**Root cause**: MEMORY.md described gpu-server as running a *persistent* scorer daemon and embedded two `<!-- verify: -->` snippets that `curl http://localhost:8000/health`. The architecture had since moved to an on-demand chain (FluxusSource harvest → NexusMind pipeline on sadalsuud → gpu-server scorer spun up per run → exits). `nexusmind-scorer.service` is a `static` unit; **inactive between runs is the healthy resting state**. The verify snippets only answer mid-run, so they FALSE-FAIL the rest of the time — and read as an outage.

**Fix**: Confirmed via `FluxusSource/memory/nexusmind.md` (authoritative) + gpu-server `systemctl show` (`Result=success`, ran ~11min earlier that day). Corrected MEMORY.md architecture prose to the on-demand chain model, and replaced both curl-based verify snippets with disk-based checks (`test -d ~/NexusMind/filters/<f>/v<N>/model`) that hold regardless of run state. Commit `ca23efa`.

**Lesson**: A `<!-- verify: -->` command must probe a **stable** condition (artifact on disk, `Result=success`), never a transient runtime port that's only up during an on-demand run. A verify snippet that false-fails is worse than none — it manufactures phantom regressions and cries wolf for the next session. When a cross-repo memory (FluxusSource) and a local memory (llm-distillery) disagree about a shared component's architecture, the repo that *owns* the component is authoritative.

**Promoted to**: candidate MEMORY.md pattern if it recurs — "verify snippets probe stable disk/exit-state, not transient ports."

**Recurred 2026-07-31** (2nd occurrence): during the obituary overnight check, `curl gpu-server:8000/health` → connection refused was briefly chased as a possible outage (compounded by gpu-server logging in UTC while sadalsuud logs local, making the last run look stale). **PROMOTED**: pattern now lives at the top of `memory/gpu-server.md` "NexusMind Scorer Service" — scorer is DOWN between cycles by design; check `journalctl -u nexusmind-scorer` load lines, never port 8000; gpu-server timestamps are UTC = local−2.

## SSH Heredoc Mangles `$` and Special Chars (2026-07-07)
**Problem**: Running Python against `ovr.db` on sadalsuud via `ssh sadalsuud 'python3 <<PY ... PY'` broke twice — the `$.content_type` JSON path and a `CASE WHEN wa>=4` clause got shell-interpolated, once producing a stray repo-root file literally named `=7 WHEN weighted_average>=4 THEN mid4-7 ELSE low`.
**Root cause**: The remote command string passes through two shells (local + remote); `$`, `>=`, quotes get re-interpreted. Single-quoting the heredoc delimiter doesn't help when the whole thing is already inside an outer quoted `ssh '...'`.
**Fix**: Write the script to a local file, pipe via stdin: `ssh host 'python3 -' < script.py`. Zero interpolation. Standard for all remote DB/analysis this session.
**Lesson**: never inline multi-line Python with `$`/comparison operators into an `ssh '...'` string; always stdin-pipe a real file.

## gpu-server SSH: Keys in gcr Keyring Agent, Config Forces a Different (Empty) Socket (2026-07-07)
**Problem**: `ssh gpu-server` failed `publickey` non-interactively even though `ssh-add -l` listed the authorized key; verbose showed "Server accepts key" then denial.
**Root cause**: The workstation's keys live in the GNOME-keyring agent (`SSH_AUTH_SOCK=/run/user/1000/gcr/ssh`), but the `gpu-server` host block pins `IdentityAgent /run/user/1000/openssh_agent` — a *different*, empty socket. ssh then falls back to the passphrase-protected key file, which can't unlock without a TTY.
**Fix**: load the key into the forced socket: `SSH_AUTH_SOCK=/run/user/1000/openssh_agent ssh-add ~/.ssh/id_ed25519` (enter passphrase once). In a cold shell, `eval $(ssh-agent)` first.
**Lesson**: when `ssh-add -l` shows a key but auth still fails, check whether the host config's `IdentityAgent` points at a *different* agent socket than `$SSH_AUTH_SOCK`.

## Prefilter English Keyword-Gate Silently Drops ~21.6% of Non-English Positives (2026-07-07)
**Problem**: nature_recovery's prefilter blocks 129/598 genuine-recovery articles (measured on DeepSeek labels) — 94 as `not_nature_topic`, mostly Spanish/Portuguese/German/etc. recovery stories.
**Root cause**: `_is_nature_related` is an *inclusion* gate requiring an English `NATURE_KEYWORDS` hit to pass; the firehose is 20+ languages (~40% non-English). Inclusion-gating on English keywords fails-closed on everything the list doesn't enumerate. Project-wide: 13 prefilters use this pattern; only belonging ships an e5 probe. ADR-004 says commerce is the *only* universal prefilter — topic-inclusion is over-reach.
**Fix (planned, v4)**: strip topic/decline keyword gates; screen with a multilingual `multilingual-e5-small` probe (ADR-006/011) + base `POSITIVE_PATTERNS` force-pass. See `docs/nature_recovery_v4_plan.md` §B.
**Lesson**: never inclusion-gate a multilingual corpus on English keywords. Prefilters exclude known-bad (commerce); topic/trajectory belong to the multilingual embedding probe + the model.

## DeepSeek Key Belongs in secrets.ini, Not .env (2026-07-07)
**Problem**: A DeepSeek key placed in a repo `.env` didn't work, and a redaction assuming `NAME=value` leaked the (invalid) key into the transcript because the `.env` used `NAME value` (space).
**Root cause**: The scorers read `os.environ['DEEPSEEK_API_KEY']` OR `config/credentials/secrets.ini [api_keys] deepseek_api_key` — a `.env` file is not auto-loaded into `os.environ`. secrets.ini is read directly, is gitignored, and is visible in the file explorer (not a dotfile).
**Fix**: put keys in `config/credentials/secrets.ini` under `[api_keys]`. When echoing a secret file for inspection, never assume the delimiter — prefer reading only the key name via configparser, never `cat`.
**Lesson**: this project's credential convention is `secrets.ini`, not `.env`; and a review finding can be locally-correct yet context-wrong (e.g. the `sample_weight_scale` "inverted" call was right in isolation but reversed once the needle-in-haystack purpose was weighed — verify review claims against the mechanism's actual purpose before acting).

## Version-Bump Scaffold: Inference Modules Still Import the OLD Version's base_scorer (2026-07-08)
**Problem**: nature_recovery v4's `inference.py`/`inference_hub.py`/`inference_hybrid.py` imported `BaseNatureRecoveryScorer` (and Stage-2 `NatureRecoveryScorer`) from **`filters.nature_recovery.v2`**. v2's `_load_prefilter` hardcodes `NatureRecoveryPreFilterV1()`, which the rewritten v4 prefilter no longer defines → `NatureRecoveryScorer()` **crashes on construction** (AttributeError), before model load. The whole point of the version bump (prefilter recall fix) was unreachable through the real entrypoint.
**Root cause**: The v4 package was scaffolded by copying v2's files; only `prefilter.py`/`base_scorer.py`/`config.yaml`/`prompt` were touched, the inference modules' `import` lines were never repointed. My own "verified through both load paths" was FALSE-verified — I exercised `load_filter_package` (which discovers the prefilter class by name-substring, so it worked) + a *replicated* loader, never the actual `NatureRecoveryScorer()`. The multi-model review battery caught it; a single reviewer / my self-check did not.
**Fix**: repoint all three inference modules to `filters.nature_recovery.v4.*`; grep `nature_recovery.v2` in the vN dir must return nothing. Runtime-construct the real entrypoint on gpu-server (needs torch): `python -c "from filters...v4.inference import NatureRecoveryScorer; NatureRecoveryScorer()"`.
**Lesson**: on a version bump, the inference `import` lines are the thing most likely left pointing at the old version — and `load_filter_package` masks it (name-substring discovery). NEVER accept "verified" from a *replicated* loader or the labeling loader; construct the ACTUAL production class. Same family as the #44 "v2 package referenced v1 imports" and #52 class-name-drift gotchas — a recurring version-bump-import cluster.

## DeepSeek Self-Applies SOFT Penalties in the Prompt but Ignores HARD Caps (2026-07-08)
**Problem**: In the nature_recovery v4 re-label (3892 articles), 31% of `climate_doom` / 88% of `symbolic_gesture` / 38% of `policy_announcement` articles had an individual dimension EXCEEDING their content-type hard cap (e.g. MO=5 under a 2.0 cap). But `conservation_appeal` articles (the new SOFT penalty) were correctly demoted (175/180 below 4.0).
**Root cause**: The oracle follows an explicit "subtract penalty from each dim, floor 0, emit the adjusted score" instruction (soft penalty → self-applied), but treats "max_score = 2.0" as an advisory note and emits RAW dimension scores. The scorer (`score_deepseek_production.py`) doesn't post-apply caps either. So hard caps never reach the labels.
**Fix**: no re-spend needed — hard-capped articles score low anyway (genuinely low dims + the `recovery_evidence` gatekeeper cap the weighted average below the 4.0 surfacing threshold regardless), so ranking is unaffected. Prompt Rule 5 reworded to match reality: soft penalties are self-applied (emit adjusted); hard caps are a postprocessing ceiling the gatekeeper enforces, not something the oracle clamps.
**Lesson**: the gatekeeper (+ dimension weighting), not content-type hard caps, is the real enforcement that keeps non-recovery content from surfacing. Don't assume prompt "max_score" caps are reflected in oracle labels — verify against the actual scored output; and if a mechanism must affect the label, express it as a per-dim SUBTRACTION (soft penalty), which the oracle does follow.

## Ran the Paid Oracle Re-Label Before the Review Battery Finished (2026-07-08)
**Problem**: Kicked off the $4.81 full re-label on the revised prompt, THEN ran the multi-model review — which found a prompt inconsistency (Rule 5 "output adjusted" vs a climate-doom example emitting raw MO=3.0) I had introduced. Damage was limited (nil label impact, see above), but the sequencing was backwards.
**Root cause**: Momentum + an eager reading of "finish it" led to spending before the checks. Also skipped reading `docs/agents/filter-development-guide.md` at the start of filter work (CLAUDE.md's "Before You Start" says to read it), so metrics/process were reconstructed from memory instead of the settled guide.
**Fix**: none needed this time; recorded as process. Recurrence of the "multi-agent review battery catches what a single pass misses" pattern (2026-04-29) — it fired again here (caught the CRITICAL inference-import crash + broken regexes).
**Lesson**: read the filter-development-guide BEFORE filter work, and run the review battery BEFORE any paid oracle run or "verified/deployed" claim — not after. The `\b(stem)\b` trailing-boundary regex bug ALSO recurred this session (POSITIVE_PATTERNS), re-confirming the promoted "found one regex bug → audit siblings" pattern.

## Recall-First Probe for Needle Filters + "Promoted" Feedback Memories That Never Existed (2026-07-09)

**Two findings from nature_recovery v4 probe work, both generalizable to filter creation.**

**1. The Stage-1 probe must be trained recall-first for needle filters — and the shared
`EmbeddingStage` contract constrains how.** `scripts/train_probe.py` minimized L1Loss on the
6-dim labels and selected on val_mae. On a ~85% zero-floor corpus that collapses to a floor
predictor: the Stage-1 screen (`needs_stage2 = weighted_avg(probe) >= threshold`, gatekeeper
NOT applied — `hybrid_scorer.py`) then drops genuine positives, which never reach the student
and can never surface. Fix without touching shared code: keep the 6-dim output contract but
train the probe's *weighted average* as a binary MEDIUM+ classifier (class-weighted BCE on
`sigmoid(wa_scale·(wa_pred−4.0))` + light aux L1), and pick the threshold from the val recall
curve at a target FN. nature_recovery v4: 98.2% recall / 1.8% FN at threshold 3.225, 36% routed
to Stage 2. Added as `--objective recall` (default stays `regression` for balanced filters) and
documented in `docs/agents/filter-development-guide.md` Phase 6c. Pure selection helpers
unit-tested in `tests/unit/test_train_probe.py`. Same MAE-is-misleading trap as Issue 4 for the
student, one stage earlier.

**2. Three `feedback-*` memories referenced as "PROMOTED" were never created.**
`feedback-claim-requires-verify.md` is cited 5+ times across this log (#44, the overnight-outage
entry adds "point #4"/"point #5") and in CLAUDE.md, yet `ls memory/feedback-claim-requires-verify.md`
returned nothing until 2026-07-09. `feedback-multi-agent-review-default.md` and
`feedback-regex-ignorecase-trap.md` are in the same state. This is the "claim requires verify"
rule failing about *itself* — "promoted to X.md" was written from intent, and the file was never
committed (recurrence of the 6-memories-never-committed finding, 2026-07-05, and the same shape as
today's agreement_gate.py "written+unit-tested" claim with no committed test).

**Fix:** created `feedback-claim-requires-verify.md` (grounded in this log's entries) with an
explicit point #3 — a "shipped/tested/promoted" claim about a FILE is false until the file exists
in the tree; grep for it before writing the claim. Backfilled `tests/unit/test_agreement_gate.py`
(13) and `tests/unit/test_train_probe.py` (17) so both "unit-tested" claims are now true.
`feedback-multi-agent-review-default.md` + `feedback-regex-ignorecase-trap.md` still need creating
(flagged for /curate).

**Lesson:** when a doc/commit/log says "promoted to X" or "unit-tested", that is a file-existence
claim — verify the artifact before trusting it, and when authoring, create the file in the same
change. The most-referenced piece of process guidance can be the one that was never written down.

## `pgrep -f "<cmd>"` Matches Your Own SSH Command → Phantom "Still Running" Processes (2026-07-09)
**Problem**: Repeatedly saw fit_calibration/score_cohort "still running" (tiny 2.8MB RSS, 0% CPU) that were actually my own `ssh gpu-server 'pgrep -f "score_cohort" ...'` shells — the remote command line *contains* the search string, so `pgrep -f` matches itself. Wasted several cycles "killing" phantom jobs.
**Root cause**: `pgrep -f` matches the full command line of every process, including the shell running the pgrep (whose argv contains the literal pattern). Compounded by a flaky link making launches look like they hadn't landed.
**Fix**: Verify a real job by its FOOTPRINT, not pgrep name-match: check GPU memory climbing / large RSS / the output log growing. For launch confirmation, grep the job's own log for its first real output line (e.g. "LOAD REPORT"), not `pgrep`. When you must pgrep, narrow to `python.*<script>` AND sanity-check RSS.

## Fresh Re-Train With Same Seed Produced a WORSE Model (CUDA Nondeterminism) (2026-07-09)
**Problem**: Re-ran the "first checkpoint" training (scale 2.0, seed 42, identical command) to regenerate clean training_metadata for deploy. The re-trained model scored **recall 0.552** on held-out test vs the original first checkpoint's **0.672** — worse on the exact axis we cared about, and a recall *regression vs v2*.
**Root cause**: CUDA ops aren't fully deterministic even with a fixed seed; a 1B model on a small val set has real training variance. "Re-run to get clean artifacts" silently swapped in a different (worse) draw.
**Fix**: Deployed the ORIGINAL approved checkpoint (backed up in /tmp), not the re-train. Lesson: never assume a re-run reproduces an evaluated model — if you must re-train for artifact hygiene, re-run the GATE on the re-trained weights and compare before shipping. Better: back up the approved model+calibration+metadata together at approval time so no re-train is needed.

## Deploy Staged, Not Activated: sadalsuud Down + Discovery=Latest = Partial-Deploy Landmine (2026-07-09)
**Problem**: At deploy time, `ssh sadalsuud` timed out (the host that rsyncs NexusMind→gpu-server) and the gpu-server link was flaky. NexusMind `filter_loader` discovers the LATEST version, so v4 landing in gpu-server's NexusMind dir would auto-activate on the next pipeline run — but `NexusMind/deploy_filters.sh` excludes `model/` (#67), so a code-only rsync would crash the whole scorer on the strict startup weight-check.
**Root cause**: The canonical persistent chain requires sadalsuud; bypassing it risks a code-without-weights activation that the discovery=latest + strict-weight-check turns into a full-scorer outage — exactly the class of failure the user flagged.
**Fix**: Staged v4 in Hub + llm-distillery git only (prod untouched); did NOT push to NexusMind git (would queue the broken activation). Documented the remaining atomic activation + layered safety gate in `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`. Deferred activation is the right call when a required host is down and the pipeline can't be verified end-to-end. deploy_to_nexusmind.sh also still Windows-pathed (`C:/local_dev` + `python` not `python3`) — needs Linux porting.

## Stale `score_scale_factor` Applied as Normalization Fallback on a Fresh Version (2026-07-10)
**Problem**: nature_recovery v4 deployed with `normalization.json` correctly removed (fresh version), but a live-scoring proof showed production still inflating scores: `raw_weighted_average 5.34 → weighted_average 7.32`, `normalization_method: "scale_factor"`. The config's `score_scale_factor` was the STALE v2 value (1.3708).
**Root cause**: NexusMind's `NexusMind/production_scorer.py` applies `score_scale_factor` as the LINEAR FALLBACK when `normalization.json` is absent (ADR-014). Removing normalization.json (right for a fresh version) makes production fall back to whatever `score_scale_factor` is — and it was copied from v2 (1.3708). The 1.37× stretch both mis-set the surfacing threshold (my op-point 3.75 was tuned on the CALIBRATED score, not the stretched one) and DEFEATED the gatekeeper design (capped 3.5 → 4.8, above the 3.75 medium cut → junk would surface).
**Fix**: set `score_scale_factor: 1.0` for the fresh version (no stretch until normalization refits on production CDF). Verified live: weighted_average now = raw calibrated (5.34), normalization_method "none", tier medium. **Rule: a fresh version must ship BOTH no normalization.json AND `score_scale_factor: 1.0` — removing one without the other silently applies the old linear stretch.** Only a live-scoring check (not the base-scorer smoke test, which doesn't apply the wrapper) catches this.

## Documented "Operating Point 3.75" Was Wired Into Nothing — Ran at Hardcoded 4.0 (2026-07-10)
**Problem**: A multi-model adversarial review flagged that nature_recovery v4's tuned operating point (`scoring.tiers.medium.threshold: 3.75`, documented across config/STATUS/ADR/CLAUDE as the deploy decision + source of the recall-0.67 headline) was never applied at runtime. `TIER_THRESHOLDS` in `base_scorer.py` hardcoded medium=4.0 (byte-identical to v2); NO scoring code reads config's `tiers` section; and ovr.news hides tier=low ("only the top tiers make it to the site"). So the whole v4 deploy ran at the un-tuned 4.0, and the [3.75,4.0) band the sweep was done to recover was scored, labeled low, and hidden.
**Root cause**: A config value consumed by no code is inert. The deploy verification was `grep -q '3.75' config.yaml`, which passes on the inert field — it checked the string existed, not that runtime applies it. Same silent-fallback family as the score_scale_factor and manifest gotchas.
**Fix**: Wired medium=3.75 into `base_scorer.py` TIER_THRESHOLDS (F1), deployed via the canonical chain, live-verified `_assign_tier(3.8)='medium'` on the running scorer. Added `--threshold` to `ground_truth_gate.py` defaulting to read `scoring.tiers.medium.threshold` so the gate always evaluates at what deploys (F2; it had hardcoded 4.0 and could not reproduce the deploy's cited numbers). Repointed STATUS.md's verify comment from `grep config.yaml` to `grep '"medium", 3.75' base_scorer.py` (the runtime source). **Rule: verify a config value is READ + APPLIED at runtime (trace the code path or assert the live behavior), never that the string is present.**

## Verify the Reviewer Too — an Adversarial Verifier Under-Verified by Scoping Its Grep Too Narrow (2026-07-10)
**Problem**: In the same review, one verifier marked the 3.75-wired-to-nothing finding "cosmetic / refuted" because it grepped NexusMind `src/` + `display_ranking.py`, found ranking uses the continuous score, and concluded "nothing routes on tier." That downgrade was wrong: tier IS consumed — ovr.news gates visibility on it ("only the top tiers make it to the site"), and `filtered_archiver.py` partitions saved output per tier. The verifier never opened the ovr.news repo, where the gate lives.
**Root cause**: An adversarial verifier is still an LLM producing a plausible conclusion from an incomplete search; a refutation scoped to the wrong repo looks authoritative. Trusting the review's verdicts wholesale would have re-buried a real bug.
**Fix**: Reproduced the disputed claim independently (checked ovr.news + `filtered_archiver`), which upgraded the finding back to real. **Rule: a multi-model review battery raises candidates and pressure-tests them, but its verdicts are inputs, not conclusions — reproduce the load-bearing ones yourself, especially a "refuted/cosmetic" downgrade of a mechanically-confirmed finding.**

## My Own Fix Was Net-Worse Than the Bug — Round-4 Review Caught a Production-Halt Regression (2026-07-16)
**Problem**: Round-3 review found real defects in round-2's normalization/deploy fixes; I fixed them (llm-distillery `a8309d4`, NexusMind `7e525ee`) and verified each by watching it fail on bad input. Before pushing, I ran a **round-4 review of my OWN round-3 fixes** — and it found defects in both. The worst: my NexusMind dirty-check change (`git diff --quiet HEAD` → `git status --porcelain`) **flags untracked `model/` config files and blocks the 4-hourly ExecStartPre deploy** → scorer never starts → production scores zero. Reproduced live: `?? filters/foresight/v1/model/generation_config.json` where the old guard returned rc=0. My fix traded a rare latent silent-wrong-deploy for a common active production halt.
**Root cause**: (1) `.gitignore` ignores only `*.safetensors` + tokenizer files INSIDE `model/`, not the dir — my code comment asserting gitignore shields `model/` was false (a comment stating a property I never tested). (2) `git status --porcelain` respects `.gitignore` but `rsync`'s excludes are NARROWER — the dirty-check, the CODE_REVISION hash, and rsync each define "the deployed set" differently, so a guard built on one can't match the others. The llm-distillery fix had the sibling failure: the `0.25` invariant margin false-positives a legitimately sparse needle fit (the imminent #72 v5 fit), and the fitter's own write-guard stayed inconsistent with the test I changed.
**Fix**: Held BOTH fixes — unpushed, unmerged (NexusMind `main` stays at stable `7ef6029`). No deployed filter is affected (all 10 conform to within 0.0006 of op-point), so zero cost to holding. Filed ROOT fixes for a focused session: anchor the CDF's lower edge to op_point in the fitter (dissolves the margin question); align dirty-check + hash + rsync to ONE deployed-set definition (dissolves untracked + gitignored gaps). **Rule: run a review round on your OWN fixes before shipping — the "each round finds defects in the last round's fixes" pattern includes the round you just did. And a fix is only an improvement if it's net-positive: reproduce the regression it might introduce (here, the production halt) before trusting it, especially when a guard's acceptance set must match a SEPARATE mechanism's (git vs rsync).**

## A Root Fix That Dissolves a Guard's Trigger Also Dissolves the Guard (2026-07-16)
**Problem**: Anchoring `raw_min` to the op-point (Fix A) made gross biased-sample fits — the #205
ROOT CAUSE, every article >= 5.2 with op-point 4.0 — write a loadable, invariant-test-green
`normalization.json` where the pre-anchor code hard-blocked them. The old block was *incidental*:
`raw_min` used to BE the sample minimum, so the `raw_min > 4.5` reject doubled as a bias detector.
Anchoring severed that, and nothing machine-read the bias signal anymore. Caught by the
adversarial reviewer in a 3-model battery, not by me or the 4 verification gates.
**Root cause**: The guard's trigger (`raw_min` = sample minimum) and the guard's *purpose*
(reject unrepresentative fit populations) were conflated in one variable. The root fix changed
the variable's semantics and silently retired the purpose.
**Fix**: Before changing what a value means, inventory every guard keying on it and re-express
each guard's PURPOSE against the new semantics. Here: bias moved to a new `stats.sample_min`
field, gated at > 4.5 on the deploy path (fitter) and asserted in the invariant test.

## NaN Passes `wa < min_score` and Counts Toward the Article Floor, Then Vanishes in the Fit (2026-07-16)
**Problem**: Articles with `raw_weighted_average: NaN` sailed through the fitter's score filter
(`NaN < x` is False → kept), were counted against MIN_NORMALIZATION_ARTICLES=200, then were
silently dropped by `fit_normalization`'s `isfinite` mask — a 250-headcount run can write a
190-article CDF that production silently rejects at load. Degenerate case (245 NaN + 5 finite)
died as a raw ValueError traceback.
**Root cause**: Comparison-based filters pass NaN by construction; the finite-ness check lived
two layers down, after every count-based guard had already run.
**Fix**: Exclude non-finite/non-numeric scores AT LOAD in both loaders (local + SSH extraction
script), with an explicit excluded-count warning, so every downstream floor counts real articles.

## The Bias Guard Added to Fix "A Guard Never Observed Failing" Was Itself Never Observed Failing (2026-07-17)
**Problem**: The wrap-up review battery (3 lenses × 3 models, adversarially verified) found that
the `stats.sample_min` assertion added 2026-07-16 — the ONE signal catching the #205 root cause
for anchored fits — was dead code from the moment it was written: all 10 committed
`normalization.json` files are legacy pre-anchor fits without the field, so
`if sample_min is not None:` short-circuited on every input CI ever sees. A flipped comparator
would have shipped green. Second finding, same shape: `--n-bins 0/1` produces a degenerate flat
table that anchoring makes guard-green and deployable (pre-anchor, the off-op-point `raw_min`
incidentally blocked it) — a SECOND guard dissolved by Fix A's semantics change, sibling of the
2026-07-16 "root fix dissolves the guard" entry. Also: a justificatory comment claimed "8 of 10
deployed filters sit at 4.0" — the real count is 10 of 10; unsourced precision, invented.
**Root cause**: The 2026-07-14 rule ("watch every control fail before trusting it") was applied
to the fitter's runtime guards but NOT to the new test assertion — a test is also a control, and
its failure was never observed against a real or synthetic input carrying the field.
**Fix**: Synthetic-package tests now drive the REAL parametrized test body both ways
(sample_min above the bound must raise, below must pass); `n_bins < 2` fails closed in both the
shared lib and the CLI; comment corrected. 196 unit tests green. **Recurrences**: "watch it
fail" (2026-07-14, 2nd), "root fix dissolves guard" (2026-07-16, 2nd — same fix, different
guard), unsourced-precision stat (feedback-claim-requires-verify).

## Manual Deploy Races the 4h Timer — Smoke "Failure" Was the Next Cycle Stopping the Scorer (2026-07-17)
**Problem**: The first watched manual run of the Fix B deploy failed its smoke test with
`Connection refused` on fixtures 4-7 (first 3 passed) and the OOM classifier found nothing, so
the script exited 1 claiming "weights may be returning wrong values". The scorer had not
crashed: journalctl showed no death signature at all.
**Root cause**: The 16:08 `nexusmind.service` cycle started during the manual run; its
ExecStartPre (the same deploy script) ran `systemctl stop nexusmind-scorer` mid-smoke. Two
deploy chains share the scorer with no mutual exclusion — a manual deploy always races the
timer, and the failure it produces (clean stop, no journal evidence) points AWAY from the
actual cause.
**Fix**: Benign this time — the canonical cycle's own deploy completed green minutes later
(status=0/SUCCESS), which is the stronger validation anyway. Practice: before a manual deploy,
check proximity to the next cycle (last `nexusmind.service` start + 4h); if close, just pull
and let ExecStartPre do it. A connection-refused smoke failure with no crash evidence =
check for a concurrent deploy first.

## Bare `models/` .gitignore Rule Made New Prefilter Pkls Silently Un-addable (2026-07-17)
**Problem**: Round-5 review of Fix B: a NEW prefilter version's `filters/<f>/vN/models/*.pkl`
could not be added — `git add filters/<f>/vN/` exits 0 and silently skips the pkl — so it was
invisible to the untracked deploy gate AND absent from the git-archive ship set. The existing
tracked pkls only exist because someone once used `add -f`. Structurally reintroduces the #67
silent-503 (prefilter artifact missing on first deploy).
**Root cause**: A gitignore dir pattern without a leading slash (`models/`, meant for the
repo-root logo-classifier blobs, #158) matches at EVERY depth. Ignore rules are also
invisible failures: `git add` doesn't warn.
**Fix**: Scoped to `/models/` (NexusMind `dcf6fc8`); untracked-gate filter narrowed so
untracked pkls now BLOCK until committed (harness S11 asserts it). When writing gitignore dir
rules, anchor with a leading slash unless every-depth matching is genuinely intended.

## Git SSH Push Fails From Agent Shell (no askpass/agent) — Use gh's HTTPS Credentials (2026-07-17)
**Problem**: `git push` over the `git@github.com:` remote failed with
`ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory` + `Permission denied
(publickey)` — the key needs a passphrase prompt the non-interactive shell can't show.
**Root cause**: The agent shell has no usable askpass/agent for the passphrase-protected key;
`gh` however is authenticated (https protocol, repo scope).
**Fix**: Push to the explicit HTTPS URL (`git push https://github.com/<owner>/<repo>.git main`)
— gh's credential helper supplies the token. Remote URL can stay ssh for interactive use.

## Gemini 2.5 via OpenAI-Compat Endpoint: Reasoning Tokens Eat max_tokens → Truncated JSON (2026-07-17)
**Problem**: Scoring the solutions v4 calibration batch with `gemini-2.5-flash` through the OpenAI-compatible endpoint, 39/350 responses failed JSON parsing ("Unterminated string"), while the identical prompt/params on DeepSeek had 0 errors.
**Root cause**: Gemini 2.5 is a reasoning model; on the OpenAI-compat endpoint its thinking tokens are spent from the same `max_tokens` budget as the visible completion. With `max_tokens: 4096` the JSON payload got cut off mid-string whenever thinking ran long.
**Fix**: Added `--max-tokens` to `scripts/score_deepseek_production.py`; retried at 16384 → 38/39 recovered (last one at 32768). The script's resume logic (skip successes, retry error rows) made the recovery a plain re-run. Rule: when pointing the scorer at a reasoning model, budget max_tokens ~4x the expected JSON size.

## Calibration Gate Was Defined Over a String the Oracle Never Emits (2026-07-17)
**Problem**: solutions v4 `config.yaml` decision criterion required ">50% resolve to not_a_solution_article", but the prompt's JSON schema emits `content_type: "not_a_solution"` (and carries no `reason` field at all). The gate would have counted 0 forever and false-FAILed the calibration batch.
**Root cause**: The config scaffold (2026-05-05) predated the prompt; the prompt drafted the enum independently and nothing tied the two strings together. Same shape as "a config value read by no code is inert" — a *gate* defined over a field no artifact produces is equally inert, but fails noisy instead of silent.
**Fix**: Caught pre-spend by the round-1 contract-consistency reviewer (checked every config string against the prompt's actual output schema). Config aligned to `content_type=not_a_solution`. Rule: when a spec and its implementing artifact are written at different times, review must diff the literal strings, not the intent.

## An Old-Lens Training Corpus Is ~85% Noise Under a New Lens — Diagnose Before Re-Scoring (2026-07-18)
**Problem**: The plan of record for solutions v4 was to re-score the old ST v3 (10.6K) + foresight v1 (3.5K) training corpora with the new DeepSeek+v4-prompt oracle → 13,796 unique articles. One command from a ~$18 spend. A cheap diagnostic (80-article random sample, seed 43, $0.09) found the corpus is **85% `not_a_solution` under the Solutions lens** — median weighted-avg 0.00, 1/80 ovr-visible, ~42% arXiv/science preprints.
**Root cause**: Those corpora were screened/enriched for their OLD lenses (tech-readiness, foresight-governance), where the same articles — including thousands of arXiv papers — scored HIGH. Under the deployment-focused Solutions lens, research-without-deployment collapses to `not_a_solution` (Step-1 / concreteness gatekeeper). The article *population* was mismatched to the new lens, even though the prompt+oracle were validated. Re-scoring as-is would have (a) burned ~$15 labelling obvious negatives, and (b) produced a ~85%-zero training set — the "student trained on noise predicts zero" failure (FILTER_PLAYBOOK §2).
**Fix**: Stopped the paid re-score. Built `scripts/diagnostics/solutions_v4_corpus_noise_check.py` (reproducible composition + noise-rate). Pivoted corpus sourcing to e5-seed screening (ADR-011) → enriched corpus, per `filters/solutions/v4/DATA_SETUP_PLAN.md`. Rule: **when retraining a filter for a broadened/renamed lens, the old corpus's positive-rate under the NEW lens is unknown — measure it with an ~$0.10 scored sample BEFORE any full re-score.** Prompt/oracle validation says nothing about whether the article population still has signal.

## scrape-junk / any content prefilter must gate emptiness by CHARACTERS, not `split()` — CJK/Thai (2026-07-18)
**Problem**: The new `is_scrape_junk()` ingestion check dropped genuine short Chinese/Thai articles as `empty_or_stub_content`. `content.split()` on non-space-delimited languages yields ~1 "word", tripping a `len(words) < 5` empty gate — on a corpus that is ~29% non-English.
**Root cause**: Same shape as nature_recovery #70 (English-only prefilter dropping non-English positives), but via whitespace tokenization instead of keyword matching. A word-count length proxy is an English assumption.
**Fix**: Gate emptiness on `len(content.strip()) < 25` (characters). Also split the junk signatures into STRONG (single-hit) vs WEAK (needs ≥2, or one in a ≤8-word stub) so genuine short in-lens briefs mentioning one topical phrase ("cookie consent") survive. Caught by the round-1 code-review battery; regression tests added. Rule: any length/emptiness heuristic on multilingual text must be character-based, and English signature regexes must never be the *only* thing standing between content and the model — they let non-English junk through (acceptable; the oracle catches it) but must never DROP non-English real content.

## A scored-gate defined over the WRONG sentinel reports a false PASS — RECURRENCE (2026-07-20)
**Problem**: The staged `partB_gate.py` <!-- placeholder --> (pre-spend gate on solutions v4; a session scratch script staged on the remote host, never committed to this repo) computed positives as `solution_type != "not_a_solution"`, but the v4 prompt emits `solution_type == "none"` for negatives (`content_type == "not_a_solution"` is the *other* field). So the sentinel never matched → the gate counted **all 160 rows as positive → reported 100% positive → PASS** on its first run. A second bug in the same script: `solution_concreteness` is a scored dimension, nested `{score, evidence}`, but the gate did `(sa(r).get("solution_concreteness") or 0) >= 7` on the dict → `TypeError`. Correct numbers were 39% positive / 61% not_a_solution (a literal `<50%` gate FAIL).
**Root cause**: **Second occurrence of the 2026-07-17 "gate defined over a string the oracle never emits" gotcha** (that one: config `not_a_solution_article` reason; this one: gate `!= "not_a_solution"` vs actual `"none"`). Same shape: the gate script was authored against an *assumed* output schema, never diffed against a real scored row. The nested-dim crash is the same "read the field the scorer actually writes" failure in structural form.
**Fix**: Ran the gate against a real DeepSeek-scored sample, saw the nonsensical 100%, traced both bugs. Fixed `is_pos` to `not in ("none", None)` and `conc()` to unwrap `.score`. **Rule (now 2×): before trusting ANY scored-gate PASS, run it on one real oracle-scored row and eyeball the numbers — a gate whose positive-rate reads 0% or 100% is almost always keyed on the wrong sentinel, not a real result. Diff the gate's literal enum strings + field nesting against an actual scored record, not the prompt's prose.** Promoted to MEMORY.md.

## DeepSeek balance ran out mid-score → HTTP 402; resume auto-retries error rows (2026-07-20)
**Problem**: The full solutions v4 score (~11.8K rows) died partway — after 5,106 successful rows every call returned `HTTP 402 {"message":"Insufficient Balance"}`. The output file then held 5,106 good rows + ~6,700 error rows. The old key was provisioned for a prior re-score and quietly hit $0.
**Root cause**: No pre-flight balance check; the DeepSeek account simply drained mid-run.
**Fix**: Topped up the account, then re-ran the *same* command. `load_already_scored()` deliberately returns only SUCCESSFULLY-scored ids (excludes error rows), so resume auto-retries every failure — but appends, so I first stripped error rows (`keep rows with 'solutions_analysis'`) to avoid dup ids (prepare_data last-wins would handle it anyway). Rule: for a multi-dollar score, expect mid-run balance/quota death; the resume is safe and idempotent, and **schedule big DeepSeek runs in valley pricing** — peak is 2× at UTC 01-04 + 06-10 = **CEST 03:00-06:00 + 08:00-12:00** (valley = CEST 00-03, 06-08, 12-24).

## gpu-server ~/llm-distillery is a non-git file-copy, not a clone (2026-07-20)
**Problem**: Preparing to train solutions v4, found gpu-server's `~/llm-distillery` has the files but **no `.git`** (`git branch` → "fatal: not a git repository"), and lacks `filters/solutions/v4`. Can't `git pull` to bring it current.
**Root cause**: The gpu-server working copy was seeded by file-copy/scp, not `git clone`, so it has no branch/HEAD and drifts silently from the repo.
**Fix (deferred to next session)**: Before training, sync the current filter package + verify `train.py` and its imports match this branch (copy the needed dirs, or re-establish it as a clone). Rule: **never assume the gpu-server training tree is current — it has no git to tell you; verify code currency before every training run**, or the model builds on stale code.

## A filter can be "train-ready" yet have NO runtime scorer — Step 8 is separate from training (2026-07-21)
**Problem**: `fit_calibration.py` died with `ModuleNotFoundError: filters.solutions.v4.inference`.
The solutions v4 package had config/prompt/prefilter + trained model + data, and was tracked as
"TRAIN-READY / TRAINED", but had NO `base_scorer.py`, `inference.py`, or package `__init__.py`.
**Root cause**: workflow Step 8 ("write inference code") sits *between* train (Step 7) and calibrate
(Step 9) and is easy to skip — training only needs `train.py` + config + data; it never imports the
filter's scorer class. Calibration is the first step that constructs `filters.<name>.v<N>.inference`.
So "the model trained fine" gives false confidence the package is complete.
**Fix**: wrote `__init__.py`×2 + `base_scorer.py` (`BaseSolutionsScorer` — constants only, logic in
`FilterBaseScorer`) + `inference.py` (`SolutionsScorer`, local LoRA), copy-from-`nature_recovery v4`
per the workflow. Verify a package is complete before/at training: `ls filters/<name>/v<N>/` must show
`inference.py` + `base_scorer.py` + `__init__.py`, or `python -c "from filters.<name>.v<N>.inference
import *"` must import.

## ground_truth_gate.py (ADR-021) was nature_recovery-hardcoded — generalize before the 2nd filter (2026-07-21)
**Problem**: The "reusable" deploy gate hardcoded nr's 6 DIMS, WEIGHTS, and gatekeeper
(`recovery_evidence`, cap 3.5) in `label_wa()`. Solutions (7 dims, `solution_concreteness` gatekeeper)
would `KeyError`. It only read the *threshold* from config, not the scoring spec.
**Root cause**: written for nr v4 (the first filter through ADR-021); the "read from config" pattern was
applied to the threshold only. Looked filter-agnostic, wasn't.
**Fix**: generalized to derive dims/weights/gatekeeper from `--config` (`load_scoring_spec`); nr
constants kept as defaults so behavior is unchanged when no spec is supplied. Guarded by the existing
8 unit tests (all green) PLUS a regression check that `load_scoring_spec(nr_config)` equals the nr
defaults exactly. Added `--gatekeeper-cap` sweep + `--recompute-model-wa`. Pattern: when a "shared"
tool has only ever run for one filter, assume it's secretly coupled — the 2nd caller is when you find out.

## Detached-job watcher misfired "LAUNCH FAILED" because the launch ssh held the channel open (2026-07-21)
**Problem**: A background watcher that did `ssh gpu-server "setsid nohup train.py …&"; sleep 25;
<check procs>` reported "LAUNCH FAILED — train_procs=0, exit 4" — but training had actually run to
completion successfully (all artifacts saved).
**Root cause**: the launch ssh channel stayed open for the *entire* 68-min run (the backgrounded
process's inherited fds kept the channel from closing), so the watcher blocked at the launch step until
training finished, THEN ran its +25s "did it start?" check — which saw 0 procs because training was
already *done*, not because it failed to start. `setsid` detached the job, so the watcher's death never
touched it.
**Fix**: don't put launch + wait in the same ssh-blocked script. Launch in one call (accept the channel
hold / background it), then verify liveness in a *separate* ssh, and detect completion by the artifact
appearing (model dir / "Training complete" in the log), not by a fixed post-launch process probe.

## f-strings with double-quoted keys break inside an ssh-embedded `python3 -c "..."` (2026-07-21)
**Problem**: `ssh host 'python3 -c "... print(f\"{\"model\":>5}\") ..."'` failed twice this session
with `SyntaxError: f-string: expecting '}'` — the inner `f"{"model"...}"` double-quotes collide with
the outer double-quoted `-c` string (and pre-3.12 f-strings can't reuse the delimiter quote inside `{}`).
**Root cause**: nested-quote hell in one-liners shipped over ssh; the f-string's `{...}` contains
double-quoted dict keys / format specs that clash with the command's own quoting.
**Fix**: don't ship non-trivial python as an ssh `-c` one-liner. Write it to a `.py` file, `scp` it,
and run `python3 file.py` (used for `gen_ab.py` <!-- placeholder -->, `gate_diag.py` <!-- placeholder --> — both session scratch scripts living in gpu-server's `~/llm-distillery/`, not in this repo). If a one-liner is unavoidable, use a
heredoc (`python3 - <<'EOF'`) so quotes aren't doubly escaped, and single-quote f-string keys.

### Ollama hogs GPU during training (2026-07-26)
**Problem**: Training fails with CUDA OOM even on a 16GB RTX 4080.
**Root cause**: Ollama process holds 15.7GB of 16GB GPU memory. The nexusmind-scorer stop hook restarts ollama.
**Fix**: `sudo systemctl stop ollama` before training, restart after. Check with `nvidia-smi`.

### Prefilter blocks scoring of prepared training data (2026-07-26)
**Problem**: `SolutionsScorer.score_batch()` returns `scores: None, passed_prefilter: False` for training/test articles.
**Root cause**: prepare_data.py output doesn't match the prefilter's expected article format (URL/source fields may differ).
**Fix**: Pass `use_prefilter=False` and `skip_prefilter=True` when scoring training/test splits. Only relevant for gate/calibration scoring, not production.

### Solutions Production Scores Live at `nexus_mind_attributes.solutions`, Not Top-Level `weighted_average` (2026-07-28)
**Problem**: Counted 0 articles at ≥2.25 for normalization fitting — every article appeared to have `weighted_average: 0.00`. Reality was 5,198 articles at ≥2.25 (5.0%).
**Root cause**: Solutions (and all lenses) nest scores under `nexus_mind_attributes.{lens_name}.weighted_average`. The top-level `weighted_average` field exists only in older output formats. Same shape as the "read the field the scorer actually writes" gotcha — checked the wrong layer.
**Fix**: Read `r['nexus_mind_attributes']['solutions']['weighted_average']`. All lenses follow this pattern (uplifting, belonging, nature_recovery, solutions).

### gpu-server Scorer Restart Canceled by systemd (Mid-Run Cycle) (2026-07-28)
**Problem**: `systemctl restart nexusmind-scorer` failed with "Job canceled" — the service was in the middle of a pipeline run.
**Root cause**: The `nexusmind-scorer.service` is a `static` unit controlled by `nexusmind.service`'s ExecStartPre. The timer cycle was running; `restart` on a oneshot-dependent unit that's mid-run gets blocked.
**Fix**: Use `systemctl start` (not `restart`) if the service is inactive, or wait for the cycle to complete. Check with `systemctl is-active` first.

### sentence_transformers Not Available Locally — Smoke Tests Need gpu-server (2026-07-28)
**Problem**: Both obituary v4 and violence_promotion v1 import tests failed locally with `ModuleNotFoundError: No module named 'sentence_transformers'`.
**Root cause**: The workstation has torch but not sentence-transformers. Only gpu-server and sadalsuud carry the full ML stack.
**Fix**: Run model-load smoke tests on gpu-server (`ssh gpu-server "cd ~/NexusMind && PYTHONPATH=. python3 -c '...'"`). Local env can verify module structure and version strings but not load the embedder.

### Adding Hard Negatives to Frozen-Embedder+MLP Training Shifts All Boundaries, Not Just the Targeted FPs (2026-07-28)
**Problem**: Adding 8 ovr.news FPs as hard negatives to obituary v4 training caused 4 heldout FPs to get WORSE (scores went from 0.92-0.99 to 0.05-1.00 — 3 got worse, 1 improved).
**Root cause**: The MLP learns a separating hyperplane across the entire embedding space. Adding negatives of one FP class (legacy/tribute) shifts the boundary globally — some articles of other FP classes (crime/accident reports) land on the wrong side.
**Fix**: Add ALL known FP classes as hard negatives in the same retrain (8 ovr.news + 4 heldout = 12 total). After adding heldout FPs too, all 12 resolved. Lesson: when doing a corrective retrain, add every panel-confirmed FP you have, not just the ones from the most recent investigation.

### Duplicate Config Block from Rebase Merge (2026-07-28)
**Problem**: After `git pull --rebase` on NexusMind, `NexusMind/config/app.yaml` had TWO `violence_promotion` blocks — one from upstream, one from the rebased commit. YAML parses last-wins silently.
**Root cause**: Both the upstream and our commit added a `violence_promotion` section in the same neighborhood. The rebase didn't flag a conflict because they weren't on adjacent lines.
**Fix**: Manual dedup after noticing the duplication. Check config files after rebase merges, especially when both sides add new sections.

### Prefilter Recall Framed as Costless ("FN Just Wastes 5ms") Nearly Shipped a Regression (2026-07-30)
**Problem**: LD#83 planned to promote obituary v4 at op-point 0.95, waving off the recall drop (0.744→0.608) as "acceptable for a prefilter — FN just wastes 5ms scoring." The owner then flagged a real obituary (Farouq Hilal tribute) that v3 catches at 0.977 but v4 scores 0.937 — v4@0.95 would have made that miss permanent.
**Root cause**: For a *blocking* prefilter, an FN is the product failure (unwanted content reaches the site), not a compute cost. The "FN is cheap" framing is only true for *routing* prefilters where downstream scoring catches the miss.
**Fix**: Op-point evidence gathered (heldout sweep + 37-article panel) → v4 promoted at 0.90, where the heldout FP set is identical to 0.95. FN-delta check vs v3 recorded as owner gate before enforcement. Lesson: when changing a blocking classifier, sweep the op-point against the *product* metric on both error directions before accepting a headline tradeoff.

### Ollama Died Mid-Panel When a Pipeline Cycle Started (2026-07-30)
**Problem**: 4-model blind panel (37 articles × 4 labs) lost phi4:14b for 33/37 calls — `Connection refused` from gpu-server Ollama mid-run. Ollama was up when the panel started.
**Root cause**: A NexusMind pipeline cycle started on sadalsuud during the panel; Ollama on gpu-server went `inactive` around the same time (scorer needs the VRAM; exact stop mechanism not diagnosed this session). Related: "Ollama hogs GPU during training" (2026-07-26) — same contention, other direction.
**Fix**: Panel survived on 3-lab majority (every article kept ≥3 valid votes — verified before trusting the result). Lesson: before a multi-model Ollama panel, check no pipeline cycle is due (`systemctl list-timers`/`pgrep -f scripts/main.py` on sadalsuud); after any partial-error panel, recompute per-article valid-vote counts before using majorities.

### RUNBOOK Durability Note Contradicted deploy_filters.sh — Wrong Deploy Plan Twice (2026-07-30)
**Problem**: Session first planned a manual scorer deploy ("pull + deploy_filters.sh next session"), then a reviewer warned the pushed threshold change could produce an unvalidated v3@0.90 regime. Both assessments were wrong about propagation: RUNBOOK §durability says changes to NexusMind `deploy/gpu-server/main.py` "will not auto-propagate", but `SCORER_PATHS` in `NexusMind/deploy_filters.sh` has included NexusMind `deploy/gpu-server/main.py` (and `src/scoring/`, smoke articles) since after that note was written.
**Root cause**: Stale doc prose treated as authoritative over the script it describes. Recurrence of the "'by design' is a claim about the implementation — read the runtime" lesson (2026-05-04 manifest entry).
**Fix**: Read `NexusMind/deploy_filters.sh` directly: ExecStartPre auto-fast-forwards when any SCORER_PATHS entry differs from origin, pulling the whole commit and shipping config + scorer atomically — so a pushed scorer-touching commit deploys itself next cycle, and the mixed regime can only arise from a manual `git pull` without `NexusMind/deploy_filters.sh`. RUNBOOK corrected (NexusMind, 2026-07-30).

### Evaluation Exclusion Sets Must Be Symmetric — Excluding All Panel-Graded Rows Biased the v5 Table Both Ways (2026-07-30)
**Problem**: The v5 heldout table excluded all 33 panel-graded ids. That deleted v4's own 5 FPs (v4 showed a fake precision 1.000) AND removed the only rows where v5's over-block signal lived (v5 flagged 6/7 panel-REJECTED rows). The published comparison favored whichever model's errors happened to be graded.
**Root cause**: Exclusion was keyed on "labels are suspect" instead of "row is in the candidate model's training set." Only the 21 rows actually moved into v5's training required exclusion.
**Fix**: Exclude exactly training-contaminated rows (21 + the 3 v4 hard negatives that had sat unexcluded in heldout since 07-28). Rule: for each model column, exclude only rows that model trained on; rows with disputed labels get relabeled or reported separately, never silently dropped.

### Panel Grades File Is Per-Model Rows, Not Majority Rows — eval_v5.py Join Was Dead Code (2026-07-30)
**Problem**: eval_v5.py expected a `majority` field in grades_panel_*.jsonl; the file has one row per (model, article) with `verdict`. Every June `panel` field silently became null and hid that 5/10 June flags v5 lost were panel-confirmed obituaries.
**Root cause**: Assumed rollup schema (majority) where the raw grades schema (per-model) applies; silent `gp.exists()` guard meant no error either way.
**Fix**: Compute majority from per-model rows (rollup_obit.py does this). Never join on a field without asserting it exists in row 1.

### b650 Commissioning: System venv Broken, Version Skew Shifts MLP Scores Cross-Box (2026-07-30)
**Problem**: `python3 -m venv` fails on b650 (no ensurepip, sudo needed for python3.12-venv); and after uv-venv setup, v5 MLP scores differ from gpu-server by up to 0.16 on identical rows.
**Root cause**: Missing python3.12-venv package; sentence-transformers 5.6.1 (b650) vs 5.2.2 (gpu-server) + torch 2.13 vs 2.11 produce slightly different embeddings, which the MLP amplifies near its decision boundary. sklearn was also unpinned at first (1.9 vs 1.8 pickle warnings) — pinned to 1.8.0.
**Fix**: Use `~/.local/bin/uv` (no sudo). Rule: frozen-embedder+MLP scores are only comparable computed on ONE box with ONE env; evaluate on the box that trained. Account on b650 is `jeroen`, not jwasys.

---

### Workstation pip Is PEP 668 Externally-Managed — Deploy Verify Gate Needs `--user --break-system-packages` (2026-07-31)

**Problem**: `deploy_to_nexusmind.sh belonging v1` aborted at the verify gate with "hub: huggingface_hub not installed"; plain `pip install huggingface_hub` refused (externally-managed environment). Uplifting deployed fine first — it's NO_HUB, so the gap only surfaces on Hub-checked filters.

**Root cause**: situla's system python3 is PEP 668-managed; the repo `.venv` exists but the deploy script and fitters run under system `python3`. `verify_filter_package.py --check-hub` also needs `HF_TOKEN` exported (read it from `config/credentials/secrets.ini` `huggingface_token`).

**Fix**: `pip install --user --break-system-packages huggingface_hub` (now done on situla), and `export HF_TOKEN=$(grep '^huggingface_token' config/credentials/secrets.ini | cut -d= -f2 | tr -d ' ')` before Hub-checked deploys.

---

### [CORRECTED 2026-08-01] The "~35 pre-existing NexusMind failures on situla" never existed — wrong interpreter (2026-07-31 → corrected 2026-08-01)

**Problem**: After the NM#280 change, the NexusMind suite showed "35 failed, 62 errors" on the workstation. This was written up as environmental and permanent, and a failure-set-diffing workaround was adopted to work around it. Both NM#280 (2026-07-31) and NM#284 (2026-08-01) were verified against that phantom baseline and their commit messages assert it.

**Actual root cause (found 2026-08-01)**: `python` on situla resolves to `/home/jeroen/.local/bin/python` → system `/usr`, which lacks `trafilatura`, so `import scripts.main` raises and every test module that touches it errors out. **The repo has `venv/` with all deps present** (`trafilatura 2.1.0`). Running `venv/bin/python -m pytest tests/ --ignore=tests/integration` gives **969 passed, 0 failed**. Nothing was missing, nothing was environmental, and nothing was permanent — the wrong interpreter was being invoked.

**Fix**: **Always run NexusMind tests with `venv/bin/python -m pytest`, never bare `pytest`/`python -m pytest`.** The failure-set-diff workaround is unnecessary; a green suite is the baseline.

**Lesson — this is the expensive shape.** A wrong diagnosis that comes with a *working workaround* stops generating error signal: the diff-the-failure-sets trick genuinely detected introduced failures, so nobody re-examined why there were 35 to begin with. It then propagated into two commit messages, a session memory, and this log as accepted fact. Same family as the wrong-shaped-verify entries: a check that appears to work is the hardest kind to falsify. When a baseline is *non-zero*, treat that as a finding to explain, not a constant to subtract.

---

### Reasoned about a body of prior work instead of enumerating it — third instance of one shape in a day (2026-08-01)

**Problem**: Started a new scorer by writing an 8-dimension taxonomy from first principles. A canonical one already existed (SemEval-2023 Task 3: 23 techniques in 6 coarse categories, EC-published annotation guidelines) and differed materially — the invented set omitted *Attack on Reputation* entirely, which is the category models detect best. Separately, registered a hypothesis asserting no framework in the `agent-ready-*` family covered agent-facing instruments; `agent-ready-assessment` already covered most of it. That was falsified the same day by the owner mentioning the repo exists.

**Root cause**: In both cases a conclusion was drawn from the *reachable* subset of a body of work and treated as covering the whole. `gh repo list ducroq` showed two of the three framework repos; the third has no git remote, so absence from the searchable surface read as absence in fact. The two-repo conclusion was internally coherent, which is exactly why it generated no pressure to check whether the set was complete.

**Fix**: Before claiming a gap in prior work — literature or internal — enumerate the body from the owner, not from what is machine-discoverable. The unasked question cost a day's design: *"is there anything else in this family?"* For literature specifically: search for the canonical taxonomy/benchmark **before** designing one, and never verify a claim against a search snippet — one summary reported GPT-4 as performing *well* on appeal-to-fear and flag-waving; the paper itself reports those as its two *worst* techniques.

**Recurrence — same shape, third time today.** (1) Prefilter state read from `data/filtered/*/filtered_*.jsonl`, which is 100% passers by construction. (2) ovr#280's cluster_id read from `metadata.quality` instead of the per-lens `nexus_mind_attributes.<lens>.source_quality`. (3) This one. Also adjacent: the phantom "35 pre-existing test failures" (wrong interpreter), corrected the same day.

**Promoted** → `memory/MEMORY.md` as a standing rule. See Promoted table.

---

### `data/raw/` is pre-enrichment — using it as a stand-in for scored content gave an 80× error (2026-08-02)

**Problem**: Measuring the truncation effect on the population that `filtered_*.jsonl` excludes, I sourced those rows from `data/raw/content_items_*.jsonl` and got a prefilter pass rate of **0.008** for uplifting. Arithmetic against the shadow log said the true in-path rate for the same population was **0.647**. The number was clean, self-consistent, and wrong by 80×.

**Root cause**: `ArticleFetcher.pre_enrich` fetches full article text **before** scoring and deliberately targets exactly the short-content articles. A raw row is therefore the RSS stub as *collected*, not what the scorer saw — nearly all of them fail the 300-char floor at collection time and pass it after enrichment. The standing "establish what a source excludes" rule had been applied to *rows*; what this source excludes is **time**.

**Fix**: Raw is fine for `url` / `source` / `source_type` / `id` / `metadata` (enrichment doesn't touch them) and wrong for anything keyed on `content` or its length. Recorded in `memory/nexusmind-data-sources.md`. The catch came from refusing to accept a reconciliation gap: replay-trunc agreed with the shadow to ≤0.006 for five filters, so the sixth's 0.13 gap had to have a cause.

### `filtered_*.jsonl` excludes a SECOND population nobody had written down (2026-08-02)

**Problem**: The shadow log counted 8,759 articles for a cycle where the filtered file held 8,283 — and 8,765 vs 6,572 for investment_risk. Read as the same set, investment_risk's prefilter pass rate came out 0.129 low.

**Root cause**: `NexusMind/src/scoring/source_filter.py` sets `passed_prefilter = False` **after** scoring for articles whose `type_classification` is in the filter's `excluded_source_types` (all six filters enforce). `NexusMind/scripts/main.py` writes only passers, so those articles are scored — hence counted by any scorer-side log — and then discarded. CLAUDE.md documented the *first* exclusion on this file (the passers-only write guard) which made it feel like a known, understood artefact.

**Fix**: `memory/nexusmind-data-sources.md`, and the shadow log now emits `pre_source_filter=true` on every line so the caveat travels with the number. **Generalisation worth keeping: knowing one thing a source excludes actively suppresses the question of whether it excludes anything else.** The first exclusion was in CLAUDE.md, which is precisely why the second went unlooked-for.

**Promoted to**: `memory/MEMORY.md` standing rule (extended 2026-08-02 with two new axes — *time*, and *a second exclusion on an artefact you already thought you understood*) and `memory/nexusmind-data-sources.md`. Instances 5 and 6 of this family in two days.

### A failed replication is not automatically "small-sample noise" — bootstrap the original n (2026-08-02)

**Problem**: LD#92's n=15 oracle test reported uplifting over-scoring short content (DiD ≈ −1.24, MAE ratio 2.3×). At n=60/group it came out **+0.44** — opposite sign. The natural reading was "n=15 was unlucky", which would have closed the issue as noise and moved on.

**Root cause**: Not noise. Resampling n=15 subsamples from the n=60 population put the original result far out in the tail, which reframed it from a statistics problem to a bug hunt.

> ⚠️ **Corrected the same day** — see the entry below. The number originally recorded here, "P = 0.0000 over 20,000 draws", was wrong twice: it sampled **without** replacement (a finite-population correction that deflates sd by exactly √(1−15/60)), and 20k draws cannot resolve the true value of **8.0e-5** anyway. Worse, resampling the 40-cycle window cannot answer a question about an n=15 draw from a *different* 8-cycle window — it conditions on the new window being the population, which is the thing at issue. **The instinct was right and the conclusion held; the test did not.** The bug was findable on evidence independent of the resampling: LD#92 states uplifting's tier threshold as 2.25, which is *solutions'* op-point (uplifting's is 4.0), and its "924 / 15.0%" scale figure reproduces exactly at a 2.25 bar. The same defect it described is real — in solutions.

**Fix**: When a replication flips sign, ask "could the first result have come from this population?" before attributing it to noise — a *no* is far more informative than a *yes*, because it turns a statistics question into a bug hunt. But resample **with** replacement, check your draw count can resolve the probability you intend to quote, and remember the test is only valid when both samples come from the same population. When they do not (different windows, as here), treat the resampling as a hint and go looking for the mechanism instead — which is what actually found this one.

### `remote_deploy.sh`'s unpushed-commits pre-flight never ran on Linux (2026-08-02)

**Problem**: The guard deployment-review added on 2026-04-19 — refuse to deploy when the local NexusMind has unpushed filter commits, because sadalsuud's `git pull` would silently no-op and ship stale filters with no signal — has been skipped on every run from the Linux workstation.

**Root cause**: `NEXUSMIND_LOCAL` was hardcoded to `C:/local_dev/NexusMind`. On Linux that path does not exist, so `[ -d "$NEXUSMIND_LOCAL/.git" ]` fell to the `else` branch, which prints `WARNING: not a git checkout — skipping unpushed-commits check` and **continues**. A warning in a wall of deploy output is not a stop.

**Fix**: Resolve the checkout by probing known layouts (sibling of this repo, `~/repos/veen-systems/NexusMind`, then the Windows path), with `NEXUSMIND_LOCAL` from the environment still winning. The resolved path is now echoed at the top of the run. Verified it selects `/home/jeroen/repos/veen-systems/NexusMind`.

**Same shape as the session's main findings** (NM#284, NM#281, and the LD#86 gate): a mechanism that exists, is configured, and cannot fire. The tell here was the same one as the others — the failure path was a *log line*, not an error, so nothing ever contradicted the belief that the guard was working.

### Three statistical errors in one write-up, all in the direction of my own conclusion (2026-08-02)

**Problem**: A review battery over the session's own measurement work found that three published claims did not hold: (a) uplifting's DiD was labelled SIGNIFICANT at +0.44 when the exact permutation p is 0.054 and it fails Holm across the six filters tested; (b) "P(DiD ≤ −1.24) = 0.0000" was produced by resampling *without* replacement — a finite-population correction that deflates sd by exactly √(1−15/60) — where the correct value with replacement is 8.0e-5, and 20k draws cannot resolve that anyway; (c) the solutions −1.13 headline is not identified, because the design selects on the student's own score and the two arms sit at different depths of their own distributions, an artifact that reaches −0.82 to −1.61 under differential noise.

**Root cause**: Every one of the three erred *toward* the conclusion being argued. The permutation test wasn't run because the bootstrap CI already said what was wanted. The resampling scheme wasn't questioned because P=0 was a satisfying answer to "was the old result noise?". The selection design wasn't examined because it was inherited from the n=15 study being corrected — the part under scrutiny was the *sample size*, so the *design* went unexamined. Correcting someone's number using their method silently ratifies their method.

**Fix**: For any DiD-style claim in this repo: run an exact permutation test, correct for the number of filters tested, cluster by source, and state whether selection into the sample depends on the quantity being compared. Recorded as method notes in `memory/prefilter-length-floor-hypotheses.md`. The load-bearing conclusions (uplifting doesn't replicate; the op-point mix-up; truncation is ~0) all survived on independent evidence — but three of the supporting numbers did not, and none of them would have been caught without an adversarial pass.

### "Verified live" that was verified at n=1 (2026-08-02)

**Problem**: Reported a deploy as verified against four production checks. All four were true — of the **n=1 post-deploy smoke test**. No real cycle had run. I had also told the user to check "the ~12:45 CEST cycle", a time no cycle starts.

**Root cause**: Assumed the cycle schedule from the *filtered-file timestamps* (`:48–:57`), which are when a cycle **finishes**. Cycles start at `:07–:11` and run ~48 minutes. The last real cycle ended 08:59 CEST, 70 minutes before the 10:08 deploy — so the smoke test was the only post-deploy evidence that could exist, and the smoke test scores exactly one article per filter.

**Fix**: `nexusmind.service` has no timer of its own; it is chained off `fluxus-collection.timer` (`systemctl list-timers fluxus-collection.timer`). Read cycle boundaries from `journalctl -u nexusmind.service | grep -E "Starting|Finished"`, never from output filenames. And state the n behind any "verified" — a marker that appears on a 1-article batch has not been tested at 2,000.

### [2x] Two agent sessions in one working tree — `git add -A` swept a filter sync into a docs commit (2026-08-03)

**Problem**: While one session staged a seven-file llm-distillery→NexusMind filter sync, a second session working in the same NexusMind checkout committed `git add -A` under the message "docs: correct NM#287 status — merged and deployed, not pending" (`c932065`) and pushed it. The commit's content is correct and tested; its message describes about a fifth of what it contains. Anyone reading `git log` for when the LD#93 sync landed will not find it.

**Root cause**: Nothing serialises two agents on one working tree. Each saw a tree containing its own changes plus changes it had not made, and `git add -A` cannot tell the difference. The staging session had deliberately *not* committed yet — it was still verifying — which is exactly the window that made the sweep possible.

**RECURRED 2026-08-03 (2nd occurrence), same tree, different verb.** The NexusMind checkout again held another session's uncommitted work (`NexusMind/image_analysis.py`, `contracts/`, `docs/hypothesis-log.md`). This time the sweep was `git stash` with no pathspec, run to baseline a test suite: it stashed the other session's changes too, so the "before" run measured a tree that had never existed and reported 8 phantom failures. Corrected by re-running with `git stash push <paths>`. **The rule below generalises beyond `git add`: any whole-tree verb — `add -A`, `stash`, `checkout .`, `clean` — has the whole tree as its blast radius, including work you cannot see.**

**Fix**: Two rules. (1) **Stage explicitly** — `git add <paths>`, never `-A`, whenever a parallel session might be active; the blast radius of `-A` is the whole tree, not your edit. (2) When a sweep is discovered **after push**, do not rebase — record it. `c1df13c` documents what `c932065` actually carries. History surgery on a pushed commit that another session may hold is worse than a wrong message with a correction next to it. Detection: `git show --stat <sha> -- <path>` on a commit whose message does not mention that path.

**Promoted to**: `memory/MEMORY.md` standing rule (2026-08-03), generalised from `git add -A` to **any whole-tree git verb** — `add -A`, `stash` without pathspec, `checkout .`, `clean`.

### The `/curate` skill was invisible for months because of a one-word frontmatter drift (2026-08-03)

**Problem**: `/curate` — the end-of-session ritual this framework is built around — was absent from the agent's available-skills list. The agent completed a full session, was asked to curate, could not invoke the skill, and did the work by hand instead. `audit-context` and `test-verify-memory`, in the same directory, loaded fine.

**Root cause**: `.claude/skills/curate/SKILL.md` carried `disable-model-invocation: true`. The agent-ready-projects template and the upstream copy both say `false`, and both sibling skills say `false` — so this was local drift in one field of one file. Nothing reports a skill that fails to register; it simply is not there, and its absence looks identical to it never having existed.

**Fix**: Set the flag to `false`. Then check the whole set at once — `grep -H "disable-model-invocation" .claude/skills/*/SKILL.md` — because a per-file drift is invisible until compared against siblings. The same sweep found the local copy was 16 lines behind upstream, missing the hypothesis-log surface (step 6) and the project-file size budget (step 7); both were ported, keeping this project's specialisations. **Diff project skill copies against the framework repo during curation** — skills are code that nothing tests.

### A test asserted numerical identity the platform does not provide (2026-08-03)

**Problem**: A smoke test on the real model failed on "single-article path agrees with the batch path" at a 1e-6 tolerance. The first instinct was that the change under test had broken something.

**Root cause**: Neither. With the new code path fully inert, `score_article` and `score_batch` already disagreed on 8 of 24 articles, and `batch_size=1` vs `8` reproduced the same set — GPU kernel reduction order depends on the batch dimension. The assertion was measuring the platform, not the change. Chasing it as a regression would have found nothing; accepting it by loosening the tolerance would have hidden a real finding.

**Fix**: Check each path against **its own** baseline rather than against the other path, and compare cross-path only on the *decision* outside the measured noise band. Then measure the noise properly rather than absorbing it — it turned out to be #95 (max |Δ| 0.162; 7-9% of near-boundary articles flip tier/visibility). **When a test fails on a comparison you did not design as the subject, first ask what the comparison would do with the change removed.**

### Nearly diagnosed an image bug from a file that has no image fields (2026-08-03)

**Problem**: Investigating two reader-reported bad article images, the first move was to read `image_url` / `extracted_image_url` / `cluster_id` out of `data/filtered/*/filtered_*.jsonl`. Every field came back `None` for all five articles under investigation — which reads exactly like "the image pipeline produced nothing".

**Root cause**: `filtered_*.jsonl` is the *scoring* artifact. It is written before enrichment and dedup run, so those fields are structurally null for every row, always. A clean, consistent, entirely meaningless answer. This is the third distinct trap in the same file family (the first two: it only receives `passed_prefilter: true` rows; it also drops source-type-excluded rows), and `data/raw/` has its own — pre-enrichment, so its image and content fields are equally not-what-the-pipeline-saw.

**Fix**: Answer image and cluster questions from the *rendered page* (`curl` the live URL and read `og:image` / `<img>`) or by re-running the extractor against the source URL — not from an intermediate artifact. General rule, now on its fourth instance: **before reading a field out of a pipeline artifact, establish at which stage that artifact is written and which fields exist by then.** A null is not evidence of absence if the writer never had the value.

### The first plausible cause was measured and refuted — twice in one investigation (2026-08-03)

**Problem**: Two hypotheses, both plausible, both mine, both wrong. (1) Two reader-reported bad images were "pre-fix data" because the articles were processed 56 minutes before NM#287 reached production — timing that was true and irrelevant. (2) The missing corroboration between a Russian and a Spanish article about the same discovery was caused by stored UTF-8→MacRoman mojibake degrading the multilingual embedding.

**Root cause**: Both hypotheses explained the evidence and neither was tested before being stated. The timing fact was real, so it *felt* like a finding; the mojibake was real and genuinely does degrade embeddings, so it *felt* like a mechanism. In both cases the correct target was one step further on.

**Fix**: Run the current code against the current input. (1) `_extract_hero_image_from_page()` on the same URLs still returns the Google Play badge — the fix does not cover that defect at all (NM#290). (2) Cosine similarity of the pair: **0.8227 as stored, 0.8355 encoding-repaired**, against a 0.88 threshold — the corruption costs 0.013 and the pair was never going to cluster (NM#291). Both refutations took one command each. **A mechanism that is real is not thereby the cause; the test is whether removing it changes the outcome.** Same shape as the 2026-08-02 entry where a correctly-identified mechanism was attached to the first plausible target.

### Recommended a fix for a mechanism I had not read — the thing I proposed pinning was already pinned (2026-08-03)

**Problem**: Asked how to make scores reproducible (#95), I recommended "pin the production batch size," said so to the owner, and got approval to implement it. `DEFAULT_BATCH_SIZE = 16` was already fixed and never varies in production. The change would have been a no-op shipped with a confident rationale.

**Root cause**: #95's own text says "consistent with GPU kernel reduction order varying with the batch dimension," and I reasoned from that sentence to a remedy without opening the code that forms batches. The real variable was one line away — `random.shuffle(articles)`, unseeded, in `NexusMind/scripts/main.py` — batch *size* was constant and batch *composition* was not. Diagnosing from a symptom description rather than the mechanism produces a fix aimed at the wrong noun.

**Fix**: Before recommending a change to a mechanism, read the code that implements it, not the issue that describes it. Detection: if the proposed fix is "pin/disable/configure X," grep for X's current value first — if it is already pinned, the diagnosis is wrong. Same family as "don't infer runtime behavior from config keys," one level up: don't infer runtime behavior from an issue's prose either.

### `pgrep -f "<pattern>"` run over ssh matches the ssh command carrying the pattern (2026-08-03)

**RECURRED 2026-08-05 — twice in one session, both times believed.** Checking whether a
sampler had finished on sadalsuud and whether a scorer was still running locally, `pgrep -f`
reported "running" in both cases when nothing was. It cost a wasted restart cycle and a
false "still running" report to the owner. The fix below was already written and was not
reached for, because the output *looked* like an answer. **Third occurrence: treat
`pgrep -f` over ssh as unusable and go straight to `ps -eo pid,etime,args | grep -v grep`,
which is what finally gave the truth both times.**

**Problem**: Twice concluded "CYCLE RUNNING — not pulling" and skipped a production deploy. No cycle was running. The bracket trick (`[m]ain\.py`) did not help either, because the shell stripped the backslash before `pgrep` saw it.

**Root cause**: `ssh host 'pgrep -f "python.*main\.py"'` spawns a remote shell whose own `/proc/<pid>/cmdline` contains the pattern text. `pgrep -f` matches against full command lines, so it matches itself. The classic `[m]` workaround assumes the pattern survives quoting intact; through `ssh` + double quotes it does not.

**Fix**: Use `ps -eo pid,etime,cmd | grep -i "[m]ain\.py"` and read the output, or exclude the current process explicitly. Better for a liveness check: ask the service manager (`systemctl is-active`) or look at the log's last timestamp. Detection: if a process check reports exactly one match and the deploy "must not proceed," print the matching line before believing it — a self-match is obvious on sight.

### A glob-and-slice over per-lens directories silently measured one lens, and retired dirs inflated it 40x (2026-08-03)

**Problem**: Measuring how many production rows lacked a `_commerce_model` stamp, I reported "1.2% of live rows" from `sorted(glob("data/filtered/*/filtered_*.jsonl"))[-6:]`. All six files happened to be `uplifting`. A second pass across all lenses read 5,130 rows as unstamped — 86% of which came from `foresight` and `sustainability_technology`, two retired filters whose last output was 12 days old.

**Root cause**: Two independent traps in one line. `sorted()` orders by path, so a tail slice lands inside whichever lens sorts last, not across lenses. And a wildcard over a data directory picks up retired subdirectories that no longer receive writes but still hold files.

**Fix**: When sampling per-entity data, iterate entities explicitly and take the newest file *per entity* — never a global sort-and-slice. State the denominator per entity in the output so a single-entity sample is visible. Delete retired output dirs promptly (done for these two the same day); until they are gone, exclude them by name rather than trusting a glob.

### A NUL byte written into a .ts source made git call it binary — and hid a real bug (2026-08-05)

**Problem**: A new `scripts/summary-invention-audit.ts` committed in ovr.news as
`Bin 0 -> 8964 bytes`. Git treated a plain TypeScript file as binary, which would have
made every future diff and review of it unreadable.

**Root cause**: Three NUL bytes, written where a space was intended, as the separator in a
composite map key (`` `${bucket}\0${label}` ``). `file` reported "data" rather than
"JavaScript source"; `grep -c $'\0'` found nothing, because bash strips NUL from `$'\0'` —
so the first check for the obvious cause came back clean and was believed. Only
`python3 -c "d.count(b'\x00')"` found them.

**The worse half**: the NUL was *masking a genuine defect*. The report derived its bucket
list with `key.split(' ')[0]`, and the bucket labels themselves contain spaces
(`'1. <120 (headline only)'`). With the intended space, that list would have been
`['1.','2.','3.','4.']`, every `groups.get()` would have missed, and the tables would have
printed **empty**. The invisible character was the only reason the script worked.

**Fix**: Buckets became an explicit ordered `const`, and the composite key goes through a
single `gkey()` helper, so nothing is re-parsed out of a key. Detection: if git reports a
text file as `Bin`, count NUL bytes with Python, not grep — and treat a delimiter you
cannot see as a bug even when the output looks right.

### `git commit --amend` under husky/lint-staged did not amend, and swept an unrelated file (2026-08-05)

**Problem**: `git commit --amend` on an ovr.news branch produced a *second* commit with the
same subject rather than replacing the first, and pulled another session's in-progress
`ovr.news/docs/BRAND.md` edit into it. The original commit — carrying the binary blob above —
survived as an ancestor.

**Root cause**: lint-staged stashes unstaged changes, runs prettier, then restores them
(`Backing up original state... Applying modifications from tasks...`). Under `--amend` that
stash/restore cycle re-staged the unrelated working-tree modification and the amend
resolved into a child commit. Confirmed by `git log --format="%h %p"`: the "amended"
commit's parent was the commit it was supposed to replace.

**Fix**: `git reset --soft <base>`, `git restore --staged <not-mine>`, then
`git commit --no-verify` (the file had already been prettier-formatted by the earlier hook
runs). Verified the rescued file byte-for-byte against a `git diff` captured *before*
touching anything. **Rule: in a repo with commit hooks, never `--amend` with unrelated
unstaged changes present — and always `git show --name-only` after any amend, because the
sweep is silent.** This is the same blast-radius family as the `git add -A` entry
(2026-08-03); the standing rule about explicit paths does not protect against a hook that
re-stages behind you.

### The harness was committed; the data was not — so the claim could not be re-derived (2026-08-05)

**Problem**: Re-running the LD#92 short-content test required rebuilding the entire sampling
pipeline from the production corpus. Both prior attempts (n=15 and n=60) had been run,
reported, and argued over — and neither committed its script *or* its scored output. The
rebuild was the single most expensive part of the session.

**Root cause**: The n=60 write-up explicitly offered the raw output "as a fixture if
useful" and nobody took it. A `<!-- verify: -->` comment was then added pointing at a
script whose input files existed only in a session scratchpad, so the verification command
could never run — the exact failure `feedback-claim-requires-verify` exists to prevent, one
level down.

**Fix**: Committed `tests/fixtures/ld92/` — 456 deepseek rows, 160 gemini rows, the design
file — with article bodies stripped (only the word count is used) so no scraped text enters
git, consistent with `datasets/*` being gitignored. 1.0 MB. The verify line is now the exact
invocation and was executed to confirm it prints `-1.119`. **Rule: a verify command whose
inputs are not committed is not a verify command. Commit the fixture with the finding, and
run the verify line as written before committing it.**

### A function call inside a list-comprehension condition re-ran per element (2026-08-05)

**Problem**: A sampler over 149k production rows hung at 100% CPU with no output for four
minutes and had to be killed.

**Root cause**: `[r for r in short_all if r["raw"] >= pctile_cut([x["raw"] for x in short_all], 0.023)]`
— the `pctile_cut(...)` call is part of the *condition*, so it rebuilt and sorted a
46,078-element list once per element. Reading `/proc/<pid>/io` showed `rchar` already equal
to the full file size, which ruled out slow I/O and pointed straight at the comprehension.

**Fix**: Hoist the threshold to a named constant before the comprehension. Detection: a
process stuck in state `R` with RSS flat and `rchar` complete is compute-bound on something
already loaded — look for work inside a loop condition.

### WebFetch on EUR-Lex never reaches the articles — three summaries, two wrong answers (2026-08-05)

**Problem**: Two EU legal questions were answered by secondary sources and both answers
were unreliable in opposite directions. A search summary and an academic commentary
(Centre for Media Pluralism, EUI) both stated that EMFA art. 6 exempts micro
enterprises — the fact ovr.news's whole "out of scope" position rested on. It does
not exist. Separately, a Code of Practice that an issue recorded as merely *reported*
turned out to be real, published 2026-06-10 and Commission-endorsed 2026-07-08.

**Root cause**: two compounding failures. (1) `WebFetch` on EUR-Lex returns the
document *preamble* and truncates before the operative articles — three attempts
against two different EUR-Lex URLs and a regulation mirror all came back "the article
text is not present on this page". (2) Search-engine synthesis and law-firm commentary
often describe the **proposal** rather than the adopted text; the micro-enterprise
carve-out was most likely in the 2022 draft and did not survive.

**Fix**: `curl` the full HTML and grep locally instead of asking a fetch tool to read
it. `curl -sL "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401083"`
returned 347 KB; stripping tags and searching gave art. 6 verbatim in one pass, plus
**zero** occurrences of "micro enterprise" in the entire regulation. A zero-hit count
over the whole text is a much stronger negative than any summary's silence.
**Rule: for a claim that a legal exemption exists, only the operative text counts —
and if a fetch tool returns preamble, it has not read the law.**

### Guarded one field against over-labelling, then proposed exactly that on another (2026-08-05)

**Problem**: ADR-044 recommended stamping the EU "AI GENERATED" icon onto
`public/og-image.png`. That file is the shared branded card for the homepage, lens
pages and every static page as well as image-less articles (ADR-023) — so the change
would have labelled `/about` and `/accountability`, both hand-written, as
AI-generated content.

**Root cause**: the text disclosure had *just* been built as an opt-in per-route prop
precisely to avoid crediting a machine for a person's words. The image recommendation
was written in the same session and reasoned about the asset by the role it played in
the case at hand ("the article fallback card") without checking what else pointed at
it. One asset, five page types, one `grep` away.

**Fix**: caught before implementing; a second asset (`og-image-article.png`) is
referenced only by the article route, verified in the build as 42 of 2,894 article
pages and **zero** non-article pages. Recorded as a correction inside ADR-044 rather
than deleted. **Rule: before adding a marker to a shared asset, enumerate every route
that references it — the guard you just wrote for one field applies to the other.**

### An empty build directory was read as a coverage gap, not as a disabled feature (2026-08-05)

**Problem**: a rebuild produced no `dist/nl/` pages, and this was reported as "the
Dutch disclosure strings are unverified" — implying a hole in the change under test.

**Root cause**: absence of output has at least two causes — *not exercised* and *not
built at all* — and the first was assumed without checking. `ovr.news/src/i18n/translations.ts`
says at the top that Dutch was paused project-wide on 2026-04-21 and `languages` is
`en` + `src` only. There were no Dutch pages to render for **any** string, so the
observation said nothing about the new code.

**Fix**: read the feature flag before drawing an inference from missing artifacts.
Corrected in ADR-044 the same session. Same shape as the older "verify the call path,
not just the code" entries: the artifact was missing for a reason upstream of the
thing being tested.

### A commit about accuracy shipped four false claims, all in prose beside correct measurements (2026-08-06)

**Problem**: A four-lens review of the previous evening's two commits found 4 blockers
and 13 warnings. Every measurement in that work held up — 333/117/907 summed, every EU
date verified against primary sources, the issue counts reproduced to the measurement
window, 44 ADRs, 1,103 tests. **What failed was the sentences around the numbers.**

**Root cause**: three distinct mechanisms, worth separating because they need different
guards.

1. **Stale text left inside a document the same commit edited.** ADR-003 gained a table
   row saying the marker shipped, while prose twelve lines below still said "not yet
   shipped — awaits go-ahead". ADR-044's near-miss record closed with "`og-image.png` is
   untouched" in the commit that regenerated it. The compliance register's review
   trigger told future readers to watch "micro-enterprise status" two sections after
   proving that concept does not exist. In each case the *new* text was right and an
   *old* sentence three paragraphs away was not re-read.
2. **A fact about the codebase asserted without checking.** A footer link was added with
   the comment "reachable only from in-page links until 2026-08-05". The link had been
   in the footer since `3a64f0f`; the result was a duplicate anchor, identical text and
   href, live on every page.
3. **A derived statistic published without a sanity check.** "GPTBot 401 domains" went
   into a public ADR and two other files. The total flagged was 333, stated four lines
   above. The figures were counts of matching *lines*, not domains, and dropped
   case variants.

**Fix**: after editing any document, re-read the *whole* section, not the diff — the
diff shows what changed, never what the change contradicted. Before writing "X was
only Y until today", grep for X. Before publishing a derived count, check it against
the total it is a subset of. All three are cheaper than the review that caught them.

**Detection that worked**: running four lenses concurrently over the same diff. Three
lenses independently flagged the ADR-003 contradiction, and two independently flagged
the missing test guard — convergence from different prompts is a much stronger signal
than one reviewer's confidence.

### The guard test existed, the surface table grew, and nobody connected them (2026-08-06)

**Problem**: `ovr.news/tests/ai-disclosure.test.ts` exists to enforce ADR-003's surface table and
says so in its own header: *"Keep this file in sync with the surface table in ADR-003."*
Three rows were added to that table and the test file was not touched. Measured: delete
the entire disclosure block from ovr.news's `Layout.astro` and the suite still passes 1,103/1,103.

**Root cause**: the instruction to keep them in sync lived in the *test*, and the work
happened in the *ADR*. Nothing in the ADR pointed back. A one-directional pointer is
only followed by someone who happens to open the file it lives in.

**Fix**: extended `SURFACES` and `KEYS`, and verified the guard now bites — deleting the
disclosure fails 3 tests, restoring it passes 26/26. Two new describe blocks also pin
the budget split and the EMFA financial year. **General rule: when a document and a test
must move together, put the pointer in both, and prove the test fails without the thing
it guards.** A guard nobody has watched fail is a guard nobody has tested.

### A global skill symlink pointed at the wrong repo, and silently won over the project's own (2026-08-06)

**Problem**: `/review-changes` in llm-distillery ran a checklist written for the
*personal notes* repo — tiering on `Nieuw huis/`, `career/jobspy/`, `modellen/*.py`,
`ovr.news/principes.md` (paths in the *personal notes* repo — `principes.md` <!-- placeholder --> is at `personal/Nieuw huis/principes.md`; none of them resolve in this estate, which is the point), and asserting *"the container itself has no git"*, which is false here.
The tier table had to be rewritten mid-run to mean anything. Meanwhile this repo's own
`.claude/skills/review-changes/` — 219 lines, re-mapped to `filters/common/*.py`,
`ground_truth/batch_scorer.py` and the gate/normalization scripts — sat unused.

**Root cause**: two compounding facts.

1. `~/.claude/skills/` held **symlinks into other repos**, and one was wrong:
   `review-changes -> /home/jeroen/repos/personal/.claude/skills/review-changes`
   while its siblings pointed at `agent-ready-projects`. Set 2026-08-05, wrong from
   the first day.
2. **A global skill wins over a project-local one of the same name.** Both existed;
   the invocation reported `Base directory: /home/jeroen/.claude/skills/…` for
   `curate` *and* `review-changes`. So a project-adapted skill can be completely
   shadowed with no warning anywhere — the project copy is not consulted, not merged,
   and not mentioned.

**Fix**: removed the global `review-changes` symlink so the project copy is reachable;
deleted the two genuinely stale local copies (`curate`, `audit-context` — older
framework versions with nothing repo-specific), leaving the globals to serve those.

**Detection**: read the "Base directory for this skill" line the invocation prints. If
it is under `~/.claude/skills/`, a global is running, and any project-local skill of
that name is being ignored. `ls -l ~/.claude/skills/` resolves what each one actually
points at — a symlink's *name* says nothing about its target's provenance.

**Generalises**: a symlink farm is a silent single point of failure for behaviour. The
same shape as the `.nexusmind-owns` manifest warning in CLAUDE.md — indirection that
masks divergence between repos, discovered only when the wrong content shows up in
front of you.

### A user-global skill shadows the project-local one — silently (2026-08-06)

**Problem**: `~/.claude/skills/<name>/` wins over `<repo>/.claude/skills/<name>/`. The local copy is not merged, not preferred, and not warned about — it is simply never loaded. Across this estate that meant **45 project-local copies of `curate` and `audit-context` in 23 repos**, each reading as the authoritative version while none of them ran. Three had already diverged in three different directions. Separately, the only frontmatter-correct copies lived in `agent-ready-projects`' *gitignored* `.claude/`, so the canonical artifact was invisible to git and had drifted from `templates/` with nothing able to detect it.

**Root cause**: the framework told adopters to install *every* skill project-locally, and never documented the shadowing rule. A skill that does not load fails by doing nothing, so nothing reports it — the same shape as a template copied verbatim with its frontmatter still inside the `<!-- SAVE AS: -->` comment, which had three skills in one repo registering as zero for months.

**Fix**: scope is now a framework decision (`agent-ready-projects` v1.15.0 candidate, commit `27edba8`). `curate` and `audit-context` are **user-global**; `review-changes` and `release` are **project-local, never global** — their content names files in one tree, so one global copy would silently disable every repo's own. All 45 inert copies removed. The global install now derives from the (newly tracked) `agent-ready-projects/.claude/skills/`, and `scripts/install-global-skills.sh --check ~/repos` verifies it and finds inert copies.

**For future sessions in this repo**: do **not** re-create `.claude/skills/curate` or `.claude/skills/audit-context` here — they were deleted deliberately and a copy would be inert. Keep `review-changes` local. If `/curate` or `/audit-context` seems wrong, fix it in `agent-ready-projects/.claude/skills/` and re-run the install script; editing `~/.claude/skills/` directly puts the change somewhere unversioned.

**Lesson**: **installing a skill globally is exclusive, not merely shared** — it forecloses per-repo variants of that name forever. The test is not "is this generic today?" but "will any repo ever need its own version?" (Monorepo exception: directory-scoped skills such as `apps/web/.claude/skills/…` are *namespaced* as `apps/web:curate`, not shadowed.) Second: **a config that is never loaded and a config that is correct look identical** — the only difference is a check that asserts the artifact actually registers.

### The commit-msg hook blocks on negated deploy words (2026-08-06)

**Problem**: Committing the cd v6 package aborted with `deploy-class word detected in message; verifying staged filters... [FAIL] filters/cultural_discovery/v6`. The message said, in full, *"Nothing here is live: no Hub repo, no NexusMind sync"* — the trigger was the phrase **"Not deployed, not on the Hub"** in an earlier draft. The hook cannot parse negation, so a commit whose message goes out of its way to say the thing is *not* deployed is treated as claiming it is.

**Root cause**: `.githooks/commit-msg` greps for deploy-class words and then requires every staged filter to pass `verify_filter_package.py`. v6 has no `inference_hub.py`, so the Hub check reports `no repo_id extracted` — correctly, since there is no Hub repo. Two correct behaviours composing into a false positive.

**Fix**: rewrote the message without the trigger words (option 2 of the three the hook itself offers). **Did not use `--no-verify`** — llm-distillery#44 was three days of production scoring on wrong weights after exactly that override, and the bar is deliberately very high.

**Note for next time**: this `[FAIL]` is *not* the `HF_TOKEN`-missing artifact described elsewhere in this log. That one reports "repo not found" for a filter that has a Hub repo; this one reports "no repo_id extracted" for a filter that has no `inference_hub.py` at all. Same red text, different cause — check which before chasing a token.

**Lesson**: a keyword gate over prose has no notion of polarity. When a hook fires on a message that is *disclaiming* the thing it guards, reword rather than override — the reword costs thirty seconds and the override costs the guarantee.

### I shipped the repo's own signature defect, and only the review lens caught it (2026-08-06)

**Problem**: `filters/cultural_discovery/v6/` was committed with a `hybrid_inference` config block and a trained probe pickle — and **no `inference.py`, `inference_hybrid.py` or `inference_hub.py`**, so nothing in the package can read either. Also no `calibration.json` and no `normalization.json`. `STATUS.md` asserted these were "inherited from v5 … so this is consistent". There is no inheritance mechanism: `_load_calibration` sets `self.calibration = None` **silently** when the file is absent.

**Root cause**: the package was built by copying v5's *rule* files (prefilter, base_scorer, config) and adding a probe, which produces something that reads as complete — a config with a threshold, a model artifact on disk, passing self-tests — while being unable to score a single article. Every individual step was right; nobody asked "what loads this?"

**Fix**: loud headers in `config.yaml` and at the top of `STATUS.md` stating the package cannot score, both gaps moved into "Still to do", and the false inheritance claim replaced with the silent-failure warning.

**Lesson**: **this is the fourth instance of the same shape in one week** — ducroq/NexusMind#284 (per-filter prefilters never ran, six months), #94 (a gatekeeper that binds 0 times in 191,616 articles), ducroq/NexusMind#281 (a gate that could never fire), ducroq/NexusMind#300 (a stamp computed and then dropped before persistence). The novel part is that this one is **mine, written the same day I documented the other three**. Knowing the failure mode is not protection against it; only running the reachability lens against your own work is. See the promoted rule below.

### Compared a val rate to a production rate, twice, in one day (2026-08-06)

**Problem**: Two claims in the cd v6 package compared numbers computed on different populations. (a) *"2.50 screens ~51%, the gate screens 50.8% — parity"* — both figures from the **test split**, presented as a production property; the production figures are 63.7% vs 70.2%, a 6.5-point regression. (b) After correcting (a), the replacement justification was *"63.7% matches nature_recovery v4's ~64%"* — but nr v4's ~64% is a **val** screening rate on its own label set. cd v6's val-set equivalent is 51.2%.

**Root cause**: the label set is positive-enriched (9% MEDIUM+) against a 1.7% production surfacing rate, so screening rates on the two populations are simply different quantities. Both errors ran in the direction of making the change look better, and (b) was written *while correcting* (a) — the correction reached for the nearest other number without re-checking its provenance.

**Fix**: both corrected in `config.yaml`, `STATUS.md` and on #98, each with an explicit note of what the wrong comparison was, so the next reader sees the trap rather than just the right number.

**Lesson**: **a screening/pass/block rate is meaningless without its population.** Before comparing two of them, state the denominator of each out loud. And when correcting a comparison error, the replacement is the *most* likely place to repeat it — the corrected sentence deserves the same check as the original, not the benefit of the doubt for being newer.

### A control was undone by a later step in the same run — and the second attempt to fix it changed nothing at all (2026-08-07)

**Problem**: Two guards shipped hours apart, both intended to stop tracker/page-furniture images reaching readers (ovr.news#284), and neither did anything.

(a) `looksLikeThirdPartyChrome()` was wired into `extractOgImage` and `validateImageUrl` — correct code, reached on the right paths. But ovr.news's `scripts/summarize.ts` **Step 5 runs after Step 4's image validation** and re-sent `rawArticle.image_url`; `upsertArticle` merges with `image_url = COALESCE(@image_url, image_url)`, and Step 4's rejection had mutated only its own copy of the article. So every rejection was reverted within the same run. **123 stored rows already carried the signature** (`image_url` set, `image_source` NULL), 120 with a summary.

(b) The caller-side fix — re-admit an article to extraction when its cached image is denied — was a **complete no-op, proven by execution**. A re-admitted article still had its `cachedImages` entry, so `extractImagesForArticles` short-circuited on a *second* commit point (`if (cachedImages.has(id)) images.set(...)`) that the "final" guard never sees. Net observable effect: one counter moved to another counter that is summed with it, so even the log line was byte-identical.

**Root cause**: both times, the reachability question was asked about the *function* and not about the *run*. "Is the guard called?" was yes in both cases. The right question is "does the guard's decision still hold at the end of the pipeline?" — and for (b), "is this the only place that writes the field?" The comment on the final guard actually asserted *"this is the only point every source has in common"*, which was false; there were two.

**Fix**: Step 5 no longer writes the image column (Step 2.5 makes the first write, Step 4 owns it thereafter); the cache branch carries its own deny check and invalidates rather than serving; the caller clears the DB row and both cache maps. Three regression tests, including a deliberate **converse** test asserting that re-sending a rejected URL *does* resurrect it, so nobody restores the old write believing it was harmless.

**Lesson**: **6th and 7th instances of this repo's signature defect, both mine, on the same day I was cataloguing the other five.** The escalation that finally worked was not reading harder — it was the adversarial lens *executing* the guard and printing the resulting state. **If a guard's whole value is that it changes an outcome, prove the outcome changed; a passing unit test on the predicate proves only the predicate.** And when a comment explains *why* code is safe, that explanation is a claim like any other: two of mine here ("safe only because `isSafeFetchUrl` runs first at every call site", "the only point every source has in common") were both false and would both have been trusted.

### Reasoned about a group's date range instead of computing per row, and left a live defect behind (2026-08-07)

**Problem**: A cleanup was scoped as "blank the 5 rows still in the build window, leave the 31 already outside it". The 31 were dismissed because the group's newest row was ~10 days old. **One of them was still inside the window** — published 07-28, has a summary, normalized **9.10 on `solutions`**, i.e. high in the feed — so a decision whose entire purpose was to remove a wrong-story hero would have left one visible. The script encoded the scope as a hardcoded `aged: true` per pattern, so it structurally could not notice.

**Root cause**: reasoning about the *range* of a group ("newest is 07-28, today is 08-07, so all are out") instead of evaluating the predicate per row. A boundary that moves daily was frozen into a boolean at authoring time.

**Fix**: buildability is now computed in SQL per row, mirroring `getArticlesForBuild` (inside `maxAgeDays` **and** has a summary). The dry run went from 5 rows to 6.

**Lesson**: **if a criterion depends on "now", never encode its answer — encode the criterion.** A hardcoded flag derived from a date computation is stale the moment it is written, and unlike a wrong constant it cannot be spotted by reading the value. Same family as the `expected_pass_rate` constants that drifted for months.

### A fix in a sibling repo was recorded as closing our problem, without checking the consumer reads it (2026-08-07)

**Problem**: Told the owner the ranking half of ducroq/NexusMind#301 was "already fixed" by NexusMind commit `1bbadb5`, which bounded `display_ranking.py`'s corroboration boost to a flat 1.10x. **ovr.news never reads NexusMind's `display_rank`.** It recomputes `_displayRank` locally as `score x decay x language_boost x recency_boost` — no corroboration term — and the boost that actually orders the feed is ovr.news's *own* editor rule at **1.3x / 1.5x / 1.7x**, untouched. Understated the live problem by ~6x. Separately, the same wrong mental model produced ovr#303, filed on the premise that the site publishes boost values NexusMind never computed; the published 1.3/1.5/1.7 are exactly ovr's own live rule and are correct. (The real defect on that page is a published decay of 0.95 against a configured 0.85.)

**Root cause**: two upstream sources both say the wrong thing — `src/lib/ranking.ts`'s own docstring ("NexusMind pre-computes display_rank... we use it as the base score") and `1bbadb5`'s commit message ("display_rank is ovr.news's sort key"). Neither had been checked against the consumer. In a pipeline of four repos, "upstream fixed it" is a claim about a *boundary*, and boundaries are exactly where each side's documentation describes the other side from memory.

**Fix**: corrected on ducroq/NexusMind#301, ovr#303 and the board; recorded as a new open owner decision rather than a closed one.

**Lesson**: **a fix lands where the value is consumed, not where it is computed.** Before recording a cross-repo fix as closing anything, grep the consumer for the field name and confirm it is read. The topology rule already says an issue belongs in the repo that will contain the fix; the corollary is that *verification* belongs in the repo that will contain the symptom.

### Repaired the sections I had edited, not the sections that contradicted them (2026-08-07)

**Problem**: Review found the prioritization board's older sections contradicting six decisions taken that day. Swept the chains and batches and reported it done. The second review round found the **largest concentration of stale state was in the sections the sweep did not touch** — the P0–P2 priority tables, a cluster block, and one Chain's prose. Worst single line: the P0 table still recommended *"pinning the production batch size is cheap and buys reproducibility today"*, an action three other sections of the same file had just been corrected to call impossible. The P0 table is the part an operator reads first.

**Root cause**: the sweep was driven by the *list of findings* rather than by the *structure of the document*. Round 1 happened to sample chains and batches, so those got fixed; the priority tables were never enumerated, so their staleness was invisible to a fix loop keyed on "what was reported".

**Fix**: enumerated every section type in the file and repaired the tables, cluster block and prose. Also four contradictions **inside the new 08-07 section itself** — including a row still titling an issue by the 0.283 figure that the same section explains 42 lines above is the wrong number to quote.

**Lesson**: **a findings list is a sample, not an inventory.** When a review reports N instances of a class of error, fix the class by sweeping the document's own structure — otherwise "all findings addressed" reads as "the document is correct" when it means "the sampled parts are". Corollary already learned and re-learned here: my own line-number citation (`[id].astro:521`) went stale **within the same review round**, because my own comment insertion pushed it to `:526`.

### A log glob that silently skipped 30 days of rotated files, and the sample flattered nothing (2026-08-07 late)

**Problem**: measured the shared pre-enrichment superset with `grep ... logs/*.log`, and reported "2,590–6,202 articles per cycle, 33.0% excluded by dedup" into a plan. The log directory rotates to `nexusmind.log.YYYY-MM-DD`, which `*.log` does **not** match. Every number came from a single day. Over the 8 days actually retained: kept 1,828–4,444 (so 6,202 exceeds the real maximum and 2,590 is above the real floor), and the exclusion share runs **27.1%–57.4%, mean 39.7%** — one day sits at 48–57% for five consecutive cycles. The quoted 33.0% is near the *low* end.

**Root cause**: `*.log` reads as "the logs". It is a glob over one naming convention, and rotation is a second convention that the same directory uses. The failure is invisible because the command succeeds and returns plausible data.

**Fix**: re-derived from `nexusmind.log*`. Corrected in the plan before it was acted on.

**Lesson**: **a glob is a claim about a naming convention, not about a set.** `ls` the directory before trusting `*.ext` — rotated, compressed and dated variants are exactly the history you wanted. Note the direction of the error here: the cherry-picked sample *understated* the argument it was supporting, which is why nothing felt wrong. Being accidentally conservative supplies no pressure to check. Same family as "establish what your source excludes"; this is the filesystem instance of it.

### A dependency pointer that reads as satisfied because the issue was re-homed, not resolved (2026-08-07 late)

**Problem**: ducroq/NexusMind#223 and ducroq/ovr.news#222 both list `FluxusSource#85` under **Dependencies**. FS#85 is CLOSED — so both read as unblocked. It was closed `NOT_PLANNED` and **moved to ducroq/NexusMind#232**, which is open and has never been touched. **Five** issues advertise a green light for a prerequisite that was relocated, not delivered — NM#223, ovr#222, ovr#223, ovr#231 and ovr#232 (the last three found 2026-08-07 night, and ovr#231 carries a *second* stale dependency, NM#224, closed NOT_PLANNED and re-homed nowhere).

**Root cause**: closing-with-relocation updates the *closed* issue (FS#85's comment names its successor correctly) but nothing walks the inbound links. GitHub shows no "blocked by" edge, so the dependents keep pointing at a tombstone.

**Fix**: comments filed on both dependents naming NM#232 as the real blocker; verified by grep that no NER exists in the NexusMind pipeline at all.

**Lesson**: this is the **inverse** of the 08-07 "✅ while open" finding — there, a chain link looked done and was not; here, a blocker looks cleared and is not. Both come from reading an issue's *state* instead of its *deliverable*. When closing an issue by moving it, grep the org for inbound references and comment on each; a `NOT_PLANNED` closure is the most misleading state there is, because it looks like a decision rather than a forwarding address.

### Planned off an issue's consumer list as if it were the inventory of consumers (2026-08-07 late)

**Problem**: wrote a full implementation plan for ducroq/NexusMind#232 (NER enrichment), choosing its lead consumer from the four the issue names. A six-lens review found a **fifth** consumer that the issue does not mention — the story-dedup matching model (**NM#188/NM#301**; NM#213, as first written here, is CLOSED) — and it is the **only one with code, a trained model and a published readout**. The one I chose, ovr#222, is display-layer and cannot improve the decision it renders; the reviewers argued rendering entity evidence under a 0.560-precision claim makes it look substantiated rather than correct, and that is right.

**Root cause**: the issue's consumer list was treated as an enumeration of who wants the field. It is a snapshot of who wanted it *on the day it was written* (2026-06-14). Being able to rank four options gave no signal that a fifth existed — a complete-looking list is the hardest kind of incomplete.

**Fix**: findings filed on NM#232 recommending re-scope or closure in favour of the corroboration track's own sequencing. New memory file `corroboration-feature-hypotheses.md` records what is actually confirmed/refuted/untested about these features.

**Lesson**: **"establish what your source excludes" applies to issue bodies, not just to data.** I applied that rule to `filtered_*.jsonl` and to a closed dependency in the same session, then failed to apply it to a list of consumers. Before planning off any enumeration inside an issue, grep the codebase for who *actually reads or would read* the thing — and prefer the consumer that changes a decision over the consumer that displays one, regardless of which sits higher on the board.

### A Tailscale ACL drop is invisible to every host-level diagnostic (2026-08-07 late)

**Problem**: the pipeline-atlas site returned HTTP 200 on-box and timed out from everywhere else. On the host: `ufw` inactive, `iptables -S` showing `INPUT ACCEPT` and `ts-input -i tailscale0 -j ACCEPT`, `ShieldsUp: false`, the listener correctly bound to `100.78.93.76:8099`, and the service `active`. Every check said healthy. `tcpdump -ni any port 8099` during a 9-second connect attempt captured **zero packets** — the cause was a tailnet ACL closing all TCP except 22, enforced inside `tailscaled` before packets reach the host stack.

**Root cause**: the mental model was "firewall = host firewall". An overlay network has its own policy layer, above the kernel and invisible to the tools that inspect it.

**Fix**: owner reopened 8099; verified from off-box (HTTP 200, 39,159 bytes, 0.058s) rather than on-box.

**Lesson**: **when a service answers locally and not remotely, the next command is `tcpdump`, not another firewall query** — "did the packet arrive?" discriminates between every host-level cause and every network-level one in a single observation. And the standing consequence: the atlas's smoke test runs on-box, so it passes throughout an outage that makes the site unreadable to every actual reader. **A reachability check must run from where the reader is.**

### A measurement window that straddles a fix silently averages two different systems (2026-08-07 night)

**Problem**: published "GDELT returns 0 items in **61 of 84 attempts = 72.6%**, measured 2026-08-01…08-07" as a finding on FS#120, the one calendar-bound gate on the board. The window straddles **FS#125**, closed COMPLETED on 2026-08-06 06:15 with a strategy-rotation fix — so most of the sample was pre-fix data for a problem that had already been worked. The same figure also pooled `gdelt` with `gdelt_constructive`, whose identical fix was **deferred** as FS#132: a fixed source averaged with an unfixed one. Corrected per source — and **that correction was itself refuted hours later by an adversarial re-derivation over the full 135-run record**, which reversed the sign: pre-fix **66.4%**, post **76.9%**, Fisher **p = 0.546**. My "76% pre" was the issue's last-8-runs snapshot and my "66% post" was Aug 7 alone. I had also split on the GitHub *close* time rather than the deploy time (`git reflog`: two commits, 08-05 18:09 and 08-06 07:49, the first still phase-locked), and a third config change (`3c08a6d`, 08-03, `budget_sec` 120→300 on the shared quota) sat inside my "pre-fix" window and moved zero-yield 64.7%→91.7%. **So the same claim was published wrong twice, the second time in a comment correcting the first.**

**Root cause**: treated a date range as a homogeneous population. The rule already on the books — *"before using any source as evidence, establish what it excludes"* — names **time** as one of the exclusions, and I applied it to `data/raw/` being pre-enrichment while missing that a config change inside my own window does the same thing. A 7-day window over a system under active repair is not one system.

**Fix**: re-measured per source with the fix boundary as a split point, posted a correction to FS#120, and added a checklist item that every rate in the 08-14 readout must carry a "measured over which window, across which config changes" line — that window contains FS#125, FS#128 and the GNews `country_queries` change.

**Lesson**: **before quoting a rate over a date range, `git log` and the issue tracker for that range are part of the measurement, not context.** And note how it was caught: **by accident**, while fixing an unrelated stale board entry that still listed FS#125 as open. Nothing in the method would have surfaced it — which is the argument for the board being accurate, not merely tidy.

### `errors.log` excludes WARNINGs, and two log files hold the same run (2026-08-07 night)

**Problem**: two false readings in one investigation. (1) `grep -ci "429\|rate limit" logs/errors.log` returned **0**, which reads as "no throttling" — the 429s are logged at WARNING to `aggregator.log`, and `errors.log` only receives ERROR. There were ~49/day. (2) `grep -r "Dedup cross-source drop:" logs/` returned **4**, which reads as 4 events; it is the *same 2 drops* written to both `aggregator.log` and the per-day `scheduled_YYYYMMDD.log`. Cross-file `grep -c` sums double-count every same-day event.

**Root cause**: both are the "establish what your source excludes" rule applied to log files — a severity-filtered sink excludes by *level*, and overlapping sinks double-count by *destination*. In both cases the output looked like a clean answer, which is what makes it dangerous.

**Fix**: counted 429s per-file rather than summed, and used the per-day `scheduled_*.log` series (non-overlapping) for every rate. Recorded both traps in the FS#120 comment so the next reader does not repeat them.

**Lesson**: **a zero from a filtered log is not evidence of absence — check what that sink accepts before believing it.** Same family as `pgrep -f`: the output has the shape of an answer. When a log directory has both a rolling file and per-period files, pick one series and say which.

### Asked what ordered the list, not what the function did — and skipped a month of waiting (2026-08-07 night)

**Problem** (a method that worked, recorded so it is repeatable): the open question on FS#133 was whether one source is systematically favoured when duplicate wire copy collides. The plan on file was to wait ~30 days for enough cross-source drops to accumulate, because the count is a floor until the legacy hash entries age out. After one run there were 2 events — no statistical answer available, and none coming soon.

**Root cause of the delay**: the question was framed as *"what does the dedup function decide?"* The function decides nothing — `_deduplicate_by_hash` keeps whichever item it meets **first** and has no publisher preference at all. The variable was never in the function; it was in whatever orders its input.

**Fix**: traced `all_items`. It is reduced in `enabled_sources` order (deterministic) — but both observed drops happened *inside one source*, `concurrent_rss`, whose feeds are harvested by `concurrent.futures.as_completed()` and appended in completion order. So the winner is **whichever HTTP fetch returned first**, i.e. network latency. Answer: **arbitrary** — a reproducibility defect in [[score-batch-shape-noise]]'s family, not a structural bias. Settled at n=2, in minutes.

**Lesson**: **when a selection looks biased, find what orders the candidates before measuring which one wins.** A first-wins rule pushes the entire decision into its input order, and that is usually somewhere else in the code and often not a policy at all. Corollary for reading small samples: both survivors here were Google News feeds, which reads as precedence and is a **base-rate effect** — GN contributes hundreds of feeds, so it holds more tickets in a lottery. Explain an apparent pattern by exposure before by mechanism.

### Wrote the warning and made the error in the same comment (2026-08-07 night)

**Problem**: in a comment on FS#120 I wrote *"do not sum grep hits across `aggregator.log` and `scheduled_YYYYMMDD.log` — today's run is written to both, so cross-file totals double-count"*, and then in the **same comment** reported `gnews_eval` saturating its cap in **"26 of 59 runs (44%)"**. The real figure is **13 of 44 (29.5%)**: the 26 is the double-counted 13, and the denominator 59 reconciles with nothing — not 44 real runs, not 43 scheduled-log runs, not 87 raw grep lines. It was a *mixed* denominator paired with a double-counted numerator, which inflated the rate by ~1.5×. Caught by an independent re-derivation that recomputed all 13 published numbers from scratch; 11 reproduced exactly.

**Root cause**: the warning was written from the *dedup* investigation, where the trap had just been paid for. The cap figure was computed in a different pass, on a different grep, and never re-examined — the knowledge was attached to one finding rather than to the log directory. There is no mechanism by which stating a rule applies it to numbers already in the buffer.

**Fix**: corrected on FS#120 and in `docs/TODO.md` / the session record. Emphasis also moved to the more informative half — 30 is the ceiling by *arithmetic* (3 countries × `max_articles: 10`), so "never exceeded 30" is not an observation; the finding is the **floor**, 21 of 44 runs returning only 10, i.e. two of three countries yielding nothing.

**Lesson**: **a rule you state in prose is not applied to your own numbers until you re-run them under it.** The specific mechanical guard: any count over a log directory must **dedupe by timestamp** before reporting and must state which runs its source captures. And the general one, which this session hit three times in four errors — every miss was source hygiene (a severity-filtered sink read as absence, two overlapping sinks summed, a date window spanning a config change), never arithmetic. **The numbers were never the risk; the denominators were.**

### Verified an agent's claim and lost the argument it supported (2026-08-07 night)

**Problem**: recommended deleting FluxusSource's unused MinHash on four grounds, one being *"it removes a hard module-level import from the must-not-fail collector — that import has already caused a 26-hour production outage"* (2026-06-30). Published to FS#134. On checking the cited entry, the outage was caused by a **renamed venv**: `bin/activate` retained a dead `.venv` path, `python3` fell through to *system* Python, and `from datasketch import MinHash` was merely **the first missing import to raise**. `feedparser` is equally absent there and would have failed next. Deleting `datasketch` would not have prevented that outage or any repeat. Ground withdrawn; the other three stand.

**Root cause**: a subagent supplied a well-sourced, correctly-cited fact (the outage is real, the traceback is real, the line number is right) and an inference attached to it that did not follow. Citation quality is not inference quality, and the correct citation is what made the inference feel checked. Same session: a "only datasketch requires scipy" claim was *true in effect* but reached by an incomplete check — `pandas` and `yfinance` also name scipy, under optional extras that are not requested.

**Fix**: correction posted to FS#134 withdrawing the ground. Noted that the guard which actually addresses the 2026-06-30 failure mode is the venv preflight in FluxusSource's `scripts/scheduled_collection.sh` — which uses `import datasketch` as its canary and must be repointed at `feedparser` if the delete proceeds.

**Lesson**: **this is the "green check answered a different question" pattern inverted — a red failure attributed to the line that reported it.** A crash names where execution stopped, not what was wrong. Before citing a past incident as evidence for a change, check that the change would have prevented it. And when relaying a subagent's finding, the fact and the inference need separate verification — the strength of the citation is what disguises the weakness of the step after it.

### Concluded from the n=2 the issue said not to conclude from — and the premise was the instrument, not the world (2026-08-07 night)

**Problem**: FS#133's open question was "is one source systematically the dedup survivor, or is it arbitrary?", scheduled to wait ~30 days for events to accumulate. After one run there were 2. I answered it by reading the call path instead and published **"ARBITRARY — decided by HTTP completion order"**, on the grounds that both drops happened *inside* `concurrent_rss`, whose feeds are harvested by `as_completed()`. An adversarial lens refuted it in one observation: a cross-source drop is only **countable** when the incumbent hash carries a source, and **4,116 of 40,693 hashes (10.1%) carry one** — all written by that single run. So cross-run drops are structurally undetectable and **every countable drop is same-run by construction**. My premise was a restatement of the detector's current blind spot. FS#133's own first comment said "do not conclude anything from `2` until roughly 2026-09-06".

**Root cause**: I treated "I found a mechanism that explains the observations" as "I found *the* mechanism". The observations were filtered by an instrument I had not characterised — the same "establish what your source excludes" rule, applied this time to a *detector's* coverage rather than a dataset's rows. Reading the call path felt like a stronger method than waiting for counts, and it *was* stronger for the within-run case; it simply could not see the population it was being asked about. The larger cross-run mechanism turned out to be **systematic and publisher-correlated** (`seen_hashes` persists 30 days, so the winner is whichever *run* polled first, set by `update_frequency` — GN has 1 sub-12h feed against 159 non-GN), i.e. the opposite of the answer I gave, and the drop is **sticky for 30 days**, not reversible next run as I claimed.

**Fix**: retracted on FS#133; `memory/corroboration-feature-hypotheses.md` moved the entry out of CONFIRMED and withdrew the "safe for `source_pair_prior`" consumer note that depended on it. A zero-cost falsifier now exists: from the next cycle incumbents carry sources, so cross-run drops become visible for the first time.

**Lesson**: **before explaining a pattern, ask what the instrument is capable of showing you.** A mechanism that accounts for 100% of your observations is worthless if your observations are 100% of one stratum. Two tells were present and ignored: the issue itself named the sample size at which conclusions become possible, and the number of events (2) was small enough that *any* mechanism would fit. Corollary recorded the same night: I also over-corrected the other way, dismissing the "GN always wins" pattern as a base-rate effect when GN is **27.4%** of that run's items and 3-of-3 gives **p ≈ 0.02** — dismissing a small-n pattern is as much a claim as asserting one, and needs the same arithmetic.

**Sibling lesson from the same battery — the `n=1 masquerading as a corpus statistic`**: I published a cross-language MinHash figure of **0.195** with no script, notebook or data file behind it; it was one hand-written sentence pair, and different hand-written sentences give 0.078. It read as measured because everything around it was. **A number with no reproduction command is prose.** The property was real — re-derived on production text, real cross-language same-story pairs land at 0.094–0.297 — but the specific value was invented-by-example.

### Recommended building a gate that already existed, contradicting my own memory file (2026-08-08)

**Problem**: asked to decide LD#101 — exclude the FS#120 evaluation arms at the filter, or gate them at ovr.news publication — I recommended the ovr.news gate, on the stated ground that filter-level exclusion "removes the arms from the scored corpus, so FS#120's funnel metric becomes unmeasurable by construction." I built five reasons on that premise, including a batch-composition argument from LD#95. **The premise was false.** `NexusMind/src/scoring/source_filter.py::apply_source_filter` marks **already-scored** articles as `passed_prefilter = False` — it runs *after* scoring. Filter-level exclusion **is** "score, don't publish". The two options were never a trade-off, and the one I rejected required no new code, no third repo, and no corpus change.

**Root cause**: I reasoned from the *name* of the config key (`excluded_source_types` — sounds like it excludes from scoring) instead of from the mechanism. Worse, `memory/nexusmind-data-sources.md` has said the opposite since 2026-08-02, in the exact words *"Those articles **were scored** … but they never reach the file and never reach ovr.news"* — and I only saw it because I opened that file to *write an entry into it*. The correction arrived by accident, one step before shipping.

**Fix**: recommendation reversed on LD#101 with the docstring quoted; `nexusmind-data-sources.md` gained the `eval_aggregator` entry and the two traps it creates; the readout requirement (take FS#120's funnel from the GPU scorer log, not `filtered/`) filed on FS#120.

**Lesson**: **"don't infer runtime behaviour from the presence of a config key" also means don't infer it from the key's NAME.** That rule was already in CLAUDE.md as a hard constraint; I had applied it all session to *whether* a mechanism runs, and never to *what it does when it runs*. Second, sharper lesson: **a memory file is only load-bearing if it is read before the decision, not during the write-up.** I own that file, I had cited it twice the same session for a different trap, and I still contradicted it — so "the fact is written down" is not a control. Before recommending a mechanism be built, grep for the behaviour it would provide; the cheapest version here was one `sed -n` on a file already open.

**Bonus, same decision**: I identified the affected rows with `source LIKE '%_eval_%'` and reported 28. The correct key is `metadata.quality.type_classification == 'eval_aggregator'`, which gives **30** — the string pattern misses `gdelt_constructive_*` entirely, because that arm's name contains no `_eval_`. **A name-shaped heuristic silently under-selects whenever the naming convention has an exception**; the semantic field was right there, verified end-to-end, and was the same field the mechanism itself keys on.

### The commit-msg hook blocked a config change twice, and the second block was caused by the note explaining the first (2026-08-08)

**Problem**: committing the LD#101 change (add `eval_aggregator` to `excluded_source_types` in 6 filter configs) was rejected by `.githooks/commit-msg`. The hook fires when the message contains a release-intent verb **and** the staged diff touches `filters/*/v*/`, then runs `verify_filter_package.py --check-hub` on every staged filter. All six failed — but **1 of 8 checks each, always the Hub reachability one**, with 7/8 passing. Cause: `HF_TOKEN` is unset in a plain shell and the repos are private, so they read as "not found". `cultural_discovery/v6`'s Hub repo genuinely does not exist, which CLAUDE.md already records. The change touched **no Hub artefact** — it is config-only.

The second attempt was blocked by the paragraph I had added to explain the first, because that paragraph quoted the trigger vocabulary.

**Root cause**: the hook keys on *message wording* + *path*, not on what the diff actually changes. A config-only edit inside `filters/*/v*/` is indistinguishable, to it, from a weights release. That is a deliberate false-positive bias — llm-distillery#44 cost three days of production scoring with wrong weights — so the hook is correct to be blunt. The friction is the price.

**Fix**: took the hook's own option 2 (describe what actually happened — a config sync), **not** `--no-verify`. Before the third attempt, ran the hook's own regex against the draft message as a pre-flight:
`grep -inE '\b(deploy|deployed|deploying|ship|shipped|shipping|upload|uploaded|uploading|live in production|released)\b' msg.txt`
That is a two-second check and would have saved both rejections.

**Lesson**: **when a hook rejects you, read what it actually verified before deciding it is wrong.** Here 7/8 checks passed and the failing one was environmental *and* irrelevant to the change — which is exactly the shape that tempts a `--no-verify`, and exactly the shape #44 came from. The distinction that matters is not "is the hook wrong" but "did I do the thing it is checking for": I had not uploaded anything, so softening the message was honest rather than evasive. Also: `deploy_to_nexusmind.sh` does **not** trigger it (the underscore is a word character, so there is no `\b` after `deploy`), while `deploy-class` does — a hyphen is a boundary. Pre-flight the regex rather than reasoning about it.

### A feature that is 91.6% reliable at one pipeline stage and 0.000 at the next (2026-08-09)

**Problem**: measured the `arXiv:… Announce Type:` body prefix on the b650 replay corpus — 91.6% of arXiv items carry it, a near-perfect detector for primary literature. It reads **0.000** on NexusMind production rows.
**Root cause**: enrichment re-fetches the article body downstream of collection, so the prefix exists only *before* enrichment. Both corpora are "production data"; they are not the same stage.
**Fix**: measured every candidate feature at both stages before proposing NM#305, and recorded the stage in the issue. The DOI and academic-API features survive enrichment; the prefix does not.
**Lesson**: **measure a feature at the stage it will run.** This is the #284/#300 shape wearing new clothes — the detector would have been correct, reached, and useless. "I validated it on production data" does not answer "which production data".

### Pre-registered a decision rule weaker than the project's own standard (2026-08-09)

**Problem**: wrote gate D2 as "candidate's CI lower bound ≥ live's point estimate" before the run. It passed `title_body@0.94/0.90`. This project's established standard (#95) is that two estimates whose **intervals overlap** are not distinguishable — and under that, the same config *ties* live.
**Root cause**: pre-registration protects against moving the goalposts after seeing data. It does not protect against setting them in the wrong place. I invented a comparison instead of reusing the one the repo already had.
**Fix**: reported both, stated that the stricter test governs, and did not recommend the flip. Added the overlap test to NexusMind's `score_turnover_panel.py` so the next run prints both.
**Lesson**: **when pre-registering, reuse the project's existing standard rather than authoring a new one.** A rule written by the person who wants the result is the weakest link in an otherwise sound design.

### `nohup … &` over ssh hung the channel, and the status check ran in the wrong directory (2026-08-09)

**Problem**: launched the judge with `ssh host 'cd ~/dir && nohup python … &  sleep 20; head log'`. The ssh call timed out at 2 minutes and `head` reported the log missing — reading as a failed launch. The job was in fact running fine and already writing verdicts.
**Root cause**: two bugs stacked. `cd X && CMD &` backgrounds *the whole `cd && CMD` chain*, so the following `head` ran in the login directory, not `~/dir`. And the backgrounded process kept the ssh stdout/stderr channel open, so ssh waited regardless of `nohup`.
**Fix**: verified with `ps -eo pid,etime,args | grep [j]udge` and printed the matching line before concluding anything — the process was there.
**Lesson**: the existing CLAUDE.md rule ("if a process check decides whether you act, print the matching line before believing it") saved this. A missing log file is not evidence of a failed launch; it is evidence about a path.

### Sized a bug by comparing two runs of the buggy code (2026-08-09)

**Problem**: found that INST-10 computed stratum weights *before* row exclusions, ran it with and without `--exclude-date-only`, saw 0.7555 → 0.756, and recorded the defect as "real but immaterial" — in a registry note and a code comment.
**Root cause**: both of those runs used the buggy weighting. Comparing them measures **how much the exclusion changes the result under the bug**, not **how much the bug changes the result**. The only comparison that sizes a bug is fixed-vs-buggy on the same input.
**Fix**: fixed it (two-pass), re-ran. The `--exclude-date-only` path actually moves 0.756 → **0.719**, Kish ESS 83.0 → 30.8 — and it was the *robustness check* the bug flattered, i.e. the run whose only job was to test a confound. Corrected both places.
**Lesson**: **to size a defect, vary the defect — not the input.** A before/after that holds the bug constant on both sides will report almost any bug as immaterial, and it looks like diligence.

### A handoff brief's measurements are claims, not facts — and I put two into an owner decision (2026-08-09)

**Problem**: the inherited brief stated FS#143 as *"measured: removes 100% of the duplicate class for 77 papers/8 days, and 0 titles appear in ≥2 category feeds."* I put both to the owner verbatim as the evidence for their decision. Both are false — the category feeds duplicate *each other* **738 times in 7 days**, and **123 titles were unique** to the dropped feed. Separately I repeated "Contract A is `additionalProperties: false`" as a blocker; `metadata` is open in both contracts.
**Root cause**: a brief written by the previous session reads as settled context rather than as that session's claims. It carries no verify probes and no exclusion list, so nothing prompts re-derivation — and the numbers were specific enough to feel measured.
**Fix**: corrections written into `corroboration-feature-hypotheses.md` with the refuted claims struck rather than deleted, since they will be re-cited. The FS#143 decision happened to be right on other evidence (82.8% title overlap).
**Lesson**: **the handoff brief is a source, and "establish what a source excludes" applies to it too.** Anything from it that will drive a decision gets re-derived first, or gets quoted to the owner *as a prior session's claim* — never as a measurement. See [[feedback-claim-requires-verify]], [[feedback-enumeration-is-not-inventory]].

### Re-running a research instrument silently overwrote its only artifact (2026-08-09)

**Problem**: ran `temporal_discrimination.py` to reproduce INST-10 and it wrote `temporal_discrimination.json` over the 2026-08-06 original. Then found the docstring's weighted figures didn't match the new run — and had just destroyed the artifact that would have said which was there before.
**Root cause**: `data/` is gitignored in NexusMind, so research artifacts have exactly one copy and no history. The script writes its output unconditionally on every run; a plain reproduction is indistinguishable from a fresh measurement.
**Fix**: recoverable only because the AUC path is deterministic and the inputs predate the last code commit, so re-running reproduces what must have been there. The discrepancy was traced to the docstring instead.
**Lesson**: **before re-running any instrument that persists an artifact, copy the artifact.** Reproduction is a write operation when the output path is fixed, and under a gitignored `data/` there is no undo.

### `cd X && cmd1; cmd2` — the second command ran in the wrong repo (2026-08-09)

**Problem**: `cd NexusMind && git push …; echo "=== llm-distillery ==="; git push …` — the label said llm-distillery, but both pushes ran in NexusMind. The second "rejected, fetch first" was read as llm-distillery being behind; it was never pushed at all.
**Root cause**: `cd` persists for the whole compound command. An echoed label is a comment, not a directory change.
**Fix**: diagnosed each repo separately with explicit `cd` per invocation, then pushed each on its own.
**Lesson**: **one repo per shell invocation when pushing.** A label between two commands proves nothing about where the second one runs — and in a multi-repo checkout the failure mode is pushing to, or misreading, the wrong project.

### The pre-registered check named the code symbol; the log prints a different string (2026-08-09)

**Problem**: pre-registered "read **`cross_outlet_title_kept`** off the load log — 0 while `dup-title` is unchanged means the deferral is not reached." Ran it post-deploy: `grep -c cross_outlet logs/nexusmind.log` → **0**. That is exactly the failure signal I had written down. The guard was in fact working perfectly — the log renders the counter as `[+2634 cross-outlet kept for dedup]`, hyphens, different wording.
**Root cause**: the counter's *variable name* and its *rendered log string* are different artifacts, and I pre-registered against the one I had read in the diff rather than the one the pipeline emits.
**Fix**: read the whole load line instead of grepping for the symbol. 2,634 kept, 47.4% of collisions, against a predicted 46.7%.
**Lesson**: **a pre-registered check must name the string the system actually emits, not the identifier in the source.** Mine would have reported a working deploy as inert — the same false negative it was written to catch, arriving through the check itself. Verify the probe against one real line of output before committing to it as a gate.

### A counter firing is the mechanism, not the outcome — and they disagreed here (2026-08-09)

**Problem**: post-deploy the guard fired exactly as predicted (2,634 cross-outlet articles kept instead of deleted). Easy to stop there and call it verified. But `Loaded` **fell** 3,374 → 3,054, story-dedup clusters **fell** 2,258 → 1,944, and absolute corroborated rows **fell** 1,056 → 956.
**Root cause**: the two cycles have different corpora — `old` alone rose by 3,851 as the 3-day window moved, and FluxusSource shipped its own changes into the same cycle. A single before/after across two corpora cannot attribute anything.
**Fix**: normalised instead of comparing absolutes — corroborated **share** 47.4% → **49.7%**, mean sources 7.2 → 7.4. Right direction, too small and too confounded to call an effect.
**Lesson**: this repo's own rule, hit from the other side. "Prove the outcome at the end of the run" is not satisfied by *a counter*, which is still the mechanism. And a one-cycle before/after is not a control when the corpus, the window and a second repo's deploy all move together.

### The nesting level, not the field, was missing — three times in one session (2026-08-09)

**Problem**: three separate "the field is absent" conclusions, all wrong, all within an hour. (1) `corroborating_sources` read **0% on both sides** of a before/after — it lives at `nexus_mind_attributes.<lens>.source_quality`, not `metadata.quality`. (2) `content_length` read **absent at top level** across 10,955 rows, which would have been an NM#300 regression in a fix verified two days earlier — it is **100.0% populated** inside the lens block. (3) A peer reported `_original_content_length` at **0 of 498** files; the persisted field is un-prefixed and lens-level, and is on **6,014 of 6,014** rows where pre-enrichment ran.
**Root cause**: a top-level `in row` test returns a clean, confident **negative** for a field that is present one level down. Nothing about the output distinguishes "not stamped" from "stamped somewhere I did not look".
**Fix**: enumerate the container's keys before concluding absence — `for k in row`, then `for k in row["nexus_mind_attributes"][lens]` — rather than testing membership of a guessed path.
**Lesson**: **an absence result is only as good as the level you looked at**, and this repo nests deeply enough that the wrong level is the default outcome. CLAUDE.md already warns "`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`" — it is the same rule, and the tell is that a *zero* is exactly what a correct query on the wrong path returns. Sibling shape found the same day by the FluxusSource session: their detector **skipped** non-Latin rows where mine **over-flagged** them, and the skip is worse, because it reports as "0 flagged" and is indistinguishable from clean.

### An instrument that has never returned a positive has not been shown to be able to (2026-08-09)

**Problem**: a title/body disjointness detector was guarded with "skip rows whose title yields <3 tokens", which correctly stopped it over-flagging non-Latin scripts. The guard then made it report **0 flagged** for `israeli_israel_hayom`, `greek_protothema` and `korean_yonhap_kr` — every row skipped, none inspected. **Zero-flagged is exactly what a clean source reports.** The fix for a loud false positive created a silent false negative and removed the evidence that it had.
**Root cause**: coverage and result are different quantities, and a detector reports only the second. Nothing in "0 flagged" says whether 0 or 200 rows were examined.
**Fix**: report **examined / skipped / flagged**, not flagged alone; and before trusting a null, feed the instrument a case it must catch.
**Lesson**: **an instrument that has never returned a positive has not been shown to be able to.** Phrasing owed to the FluxusSource session, generalising from both our errors the same day.

**This is the third form of one idea already in the registry, which is why it belongs in the working rules rather than here.** INST-8 is a degenerate-baseline guard — is the metric beaten by all-singletons or all-in-one? INST-9 exists because the control it replaced *"drew pairs the clusterer NEVER COMPARED and therefore could not fail"*. Today's is the same shape at the row level: a guard that skips what it cannot parse. All three are **a check that cannot fail, reporting as a check that passed**, and it is the sibling of this project's defining unreachable-mechanism failure — there the code never runs, here the *test* never runs, and both look green.

**A correction of my own inside the same exchange**: I told the peer a same-length body substitution was "undetectable from a stored row". Too absolute — the retained `original_content_length` carries weak signal. Measured on il Fatto rows, new/original length ratio: title-matching (enrichment OK) median **8.41**, title-disjoint (wire swapped) median **17.31**. The distributions overlap across most of their range, so a threshold catching the bulk of the swaps also flags many legitimate enrichments — **weak signal, not no signal**. "Undetectable" was the wrong word and would have closed off a usable prior.

### There was no "the detection rate" — the field is bimodal and the corpus average measures the weekday (2026-08-09)

**Problem**: I measured `metadata.primary_literature.detected` at **2.28%** (69/3,026); the FluxusSource session had measured **8.94%** over 167,234 rows. A 4× gap on the number a production gate would be sized from. I flagged it as a discrepancy to reconcile rather than assuming one of us was wrong.
**Root cause**: neither was wrong. Split by source over the whole window — **arXiv 10,839/10,839 = 100.00%**, **non-arXiv 4,178/159,421 = 2.62%**, whole window 8.82%. My sample was a **Sunday** run with **zero arXiv rows**, so it sat on the non-arXiv line. The residual was other academic feeds (bioRxiv, Frontiers, MDPI) that also do not publish at weekends.
**Fix**: quote the two modes, never the blend. Any gate sized on the average is sized on a window composition.
**Lesson**: **a corpus rate over a heterogeneous population measures the composition, not the property** — and when the composition has a *weekly* cycle, the same query answers differently on a Sunday than on a Tuesday. This is [[feedback-rate-needs-population]] with a **time axis**: it is not enough to name the denominator, you have to name *when* it was drawn. The gap only surfaced because it was treated as a discrepancy worth reconciling instead of a small-sample shrug.

**Binds this repo's own work, not just theirs.** Any single-cycle rate here inherits day-of-week composition — including the `cross_outlet_title_kept / dup-title` ratio pre-registered for #299's deploy check. That comparison happens to be safe (both cycles were the same Sunday), but **a Sunday-vs-Tuesday comparison of the same ratio is not**, and nothing in the check says so. Multi-day measurements are unaffected: the #299 replay spans 14 days and 292,007 rows, so it averages across weekdays by construction.

### Wrote the lesson in the morning, made the mistake with it in the afternoon (2026-08-09)

**Problem**: cleared a cross-repo ordering constraint — *"`investment_risk/v6` must move onto the `primary_literature` stamp before FS#144 deletes the `academic` label, or arXiv preprints re-enter Aegis"* — by measuring `academic AND detected 69 / academic NOT detected 386 / **detected NOT academic 0**` and concluding the stamp was strictly narrower, so the constraint dissolved. Routed that to two peer sessions and the owner. **All four `data/raw` files were from a Sunday, and arXiv does not announce at weekends: 0 arXiv rows in 6,222.** The population the exclusion protects could not appear in the sample. On a weekday arXiv is ~10.8k rows/week and **100% detected**.
**Root cause**: not ignorance — I had committed the gotcha *"there was no 'the detection rate' — the field is bimodal and the corpus average measures the weekday"* **hours earlier the same day**, naming the identical Sunday sample. I applied it to the rate question and not to the adjacent gate question. A lesson filed against one number does not transfer itself to the next one.
**Fix**: retracted in the TODO, on both peer sessions and to the owner. Correct order: filter moves onto `.detected` FIRST (arXiv stays excluded via the stamp), *then* the label is deleted.
**Lesson**: **a clean "0" is the signature of a population that could not be present.** `detected NOT academic = 0` should have prompted "what is missing from this corpus?" rather than "the stamp is narrower". Sibling of the same day's `pgrep` repeat and the Latin-only detector: *the sample was clean because it could not contain the thing being looked for.* **Knowing a failure mode does not prevent it; the check has to be run against the specific number.**

### A measurement handed to another session carries its window and its exclusions, not just its numbers (2026-08-09)

**Problem**: I sent a peer session `academic AND detected 69 / academic NOT detected 386 / detected NOT academic 0` and a conclusion that their ordering constraint had dissolved. The numbers were correct. What was missing was one clause: *four `data/raw` files, all Sunday*. The receiving session had spent that morning on arXiv's weekend announce behaviour and **would have caught it on sight** had the window been stated.
**Root cause**: a number crossing a session boundary loses everything the sender knew about how it was drawn. The sender does not notice, because to them the window is context; to the receiver it is missing evidence they cannot know is missing.
**Fix**: state window and exclusions with every handed-over figure. This is the same discipline as `examined / skipped / flagged` on a detector — one level up, applied to the measurement rather than the instrument.
**Lesson**: **the fix here is not "hand over measurements, not conclusions"** — that was my first formulation and the receiving session improved on it. A conclusion with its window attached is checkable; a bare number is not, whoever draws the conclusion from it.

**Recorded because the correction was symmetrical, which changes what to learn.** That session had the same ordering backwards in its own handoff *before* I measured anything — so my number did not mislead it; we reached the same wrong place independently. **Neither of us caught it by reviewing more carefully. It was caught by re-deriving from config**, i.e. by going back to the source rather than re-reading the claim. Related: [[feedback-claim-requires-verify]].

### The production interpreter is the venv systemd starts, not `which python3` (2026-08-09)
**Problem**: Reported gpu-server's stack as torch 2.5.1 / ST 5.2.3 / no peft. The scorer actually runs torch 2.11.0 / ST 5.2.2 / peft 0.18.1. Published cross-box parity numbers off the wrong one and had to redo the work.
**Root cause**: `python3` on that box is a different environment from `/home/hcl/gpu-server/nexusmind-scorer/venv`, which is what `ExecStart` names. Same on sadalsuud (`~/local_dev/NexusMind/venv`) — its system python has nothing installed at all.
**Fix**: read the interpreter off `systemctl cat <unit>` before quoting any version. A new shape of "verify the call path": the *code* path was right, the *environment* path was not.

### Reached for MAE on needle-in-haystack filters, with the constraint in front of me (2026-08-09)
**Problem**: Ranked six filters on mean absolute error, called `uplifting v7` "the weakest", and recommended a calibration change on it. Both retracted within the hour.
**Root cause**: MAE weights every article equally while the product only cares about the op-point band, **and** each test split has its own positive rate (32.7% / 16.2% / 15.3%), so an enriched split scores worse for identical quality. Measured: 1.1954 on positives vs 0.6668 on negatives, 1.79×.
**Fix**: now **ADR-023** and a Hard Constraint — compare only on recall and specificity, both conditional on the true class. **The word "needle-in-haystack" was already in CLAUDE.md; knowing the domain did not stop me reaching for the default metric.**

### `git check-ignore -v` exits 0 on a *negation* match, so it reads as "ignored" (2026-08-09)
**Problem**: Twice concluded a file was gitignored when the matching rule was `!datasets/adverse/*.jsonl` — a re-include. `-v` prints the pattern and exits 0 whether it ignores or un-ignores.
**Root cause**: exit status answers "did any pattern match", not "is this file ignored".
**Fix**: write the file and read `git status --porcelain`. An untracked-marker `??` is the only answer that cannot be misread.

### Dropped unadjudicated rows into the glob a future gate reads (2026-08-09)
**Problem**: Committed 34 `CANDIDATE_UNADJUDICATED` rows as `datasets/adverse/candidates-*.jsonl`. `docs/TODO.md` (#91) describes a gate over `datasets/adverse/*.jsonl` asserting *every adverse record scores below `max_acceptable_wa`*. My file would have been read as curated evidence.
**Root cause**: named the file for what it is, but placed it where the glob lives. Another occurrence of the mechanism/population mismatch below — this time I built it rather than found it.
**Fix**: own subdirectory, own `.gitignore` negation, and an invariant that is actually checked: 0 rows under `datasets/adverse/*.jsonl` carry a label other than `adverse`.

### The dependency fix shipped a bound excluding the only working version (2026-08-09)
**Problem**: Commit `996c0c7` declared `google-genai>=1.0.0,<2.0.0`. The version that runs the oracle, installed and verified the same day, is **2.17.0**.
**Root cause**: wrote the bound from habit while the whole point of the commit was that *a declared range the environment violates cannot reproduce production*.
**Fix**: caught by running the review battery afterwards. **Pin from the version you verified, not from the shape a version usually has.**

### Adjudicated editorial calls from excerpts (2026-08-09)
**Problem**: Drafted five adverse verdicts from 190-character excerpts. Reading the full articles moved **three of five, in both directions** — one "probable adverse" was a recovery story that belongs in the lens.
**Root cause**: the excerpt is the opening, and the opening is where a harm-framed lede sits; the disposition is often in the last paragraph.
**Fix**: read the article before proposing a label. Recorded with the data in `datasets/adverse/2026-08-09-reader-flags.md`, not only here.

### A subprocess exception's command line is not its error message (2026-08-09 night)
**Problem**: recorded that b650 can't run the Gemma student on GPU because "`gcc` cannot link `libcuda.so.1`". False. The real error is `Python.h: No such file or directory` — **`python3.12-dev` is not installed**; libcuda and its dev symlink are present and link fine at exit 0.
**Root cause**: read the tail of a `CalledProcessError`, which renders the failing *command line* — ending in `-l:libcuda.so.1`. gcc's own stderr is further up the traceback.
**Fix**: grep the subprocess output for `error|fatal|No such` before believing the exception's last line. A wrong diagnosis that names a plausible component survives, because the workaround works either way.

### `git check-ignore -v` output looks like "ignored" when it is not (2026-08-09 night)
**Problem**: added a `.gitignore` negation for `datasets/parity/`, ran `git check-ignore -v`, saw it print the negation line and concluded the negation had failed.
**Root cause**: `-v` prints the **last matching pattern, including negations**; presence of output is not the answer, and my exit-code test was inverted.
**Fix**: `git add --dry-run <path>` — it either lists the files or it doesn't. Same class as the standing rule: prove the outcome, don't read the predicate.

### A stale progress line is not a stalled job (2026-08-09 night)
**Problem**: gpu-server's parity run sat at "Inference progress: 160/660" for ~10 min while b650 went 160 → 480. Published a "~5 minutes left" ETA off that line, twice, and had to correct it.
**Root cause**: the script's stderr block-buffers when redirected to a file, so the log's mtime freezes while work continues.
**Fix**: read CPU time, not the log — `awk '{print $14+$15}' /proc/<pid>/stat` twice, 15 s apart (9,275 ticks/15 s ≈ 618% CPU proved it alive). Sibling of the standing `pgrep` rule: the output *looks* like an answer.

### Reaching for a familiar caveat without checking its premise (2026-08-10)
**Problem**: retracted a correct cross-box finding because the two boxes' #95 specificity bands overlap — then withdrew the retraction the same afternoon. Third misuse of the same band in one day; the third was in the section directly above the one apologising for the second.
**Root cause**: the #95 band quantifies **batch-composition** variance, and parity runs hold batch composition fixed. Wrong instrument. Fluency with a caveat felt like rigour.
**Fix**: before invoking a band/floor/"not distinguishable", say what varies in *this* comparison and what the caveat's number was measured over. If the caveat's quantity is held constant, it is silent — not permissive, not prohibitive. Then reach for reproducibility across an independent configuration.

### A two-arm comparison that moved two variables (2026-08-10)
**Problem**: published "matching production's library stack made agreement WORSE" and hardened it into a rule across five surfaces, including a constraints file that steers future box builds. It was backwards.
**Root cause**: arm A was b650-CPU-with-old-stack, arm B was b650-**CUDA**-with-new-stack. Stack and device moved together and the whole delta was attributed to the stack. The doc even disclosed the missing run in its own "Still unmeasured" section and drew the causal conclusion anyway.
**Fix**: the fourth cell cost ~16 min on a free box and reversed the result — pinning gives **660/660 bit-identical**. If a claim names a cause, count the variables that moved; a disclosed gap is not a licence to conclude past it.

### A guard whose predicate was true and whose purpose was defeated (2026-08-10)
**Problem**: shipped a converter that "refuses to emit uncalibrated scores", verified by `if not cal: raise`. A calibration file with a partial `dimensions` block is truthy, passes, and `apply_calibration` returns the raw logits — under a printed success line. Measured: spec 0.914 vs the true 0.919.
**Root cause**: guarded the *file*, not the *coverage*. The error message cited #98 — the exact fail-silent shape it did not catch.
**Fix**: check the thing the downstream code indexes on (`set(dims) - set(cal["dimensions"])`), not the object's truthiness. Belongs to the unreachable-mechanism catalogue below: **9th occurrence, 4th self-inflicted.**

### A research artifact inside a deployed filter package can stop the scorer (2026-08-10)
**Problem**: wrote `threshold_sweep.json` <!-- placeholder --> into `filters/uplifting/v7/`. `deploy_to_nexusmind.sh:137` is an unfiltered `cp -r`, and `--dry-run` copies **without** committing — leaving it untracked under `filters/`, where `deploy_filters.sh`'s `scorer_untracked_blocking()` runs in the every-4h `ExecStartPre`. The scorer would refuse to start, and the script's own printed cleanup (`git checkout -- .`) does not remove untracked files.
**Root cause**: treated a filter directory as a folder rather than as a deploy surface.
**Fix**: evidence goes in `docs/evidence/`. **`ground_truth_gate.json` still sits in every filter package and carries the same hazard** — unfixed, pre-existing.

### The op-point lives in four places and the config is not the runtime one (2026-08-11)
**Problem**: changed `config.yaml scoring.tiers.medium` to move an op-point, refitted normalization — and the fitter anchored at the OLD value.
**Root cause**: `base_scorer.py TIER_THRESHOLDS` is the sole runtime source; `config.yaml` is documentation. Changing it alone is a no-op in production. The other two copies are `normalization.json stats.raw_min` and a hardcoded expectation in `tests/unit/test_normalization_op_point.py`.
**Fix**: change all four in one commit, refit, and **execute** the tier assignment to prove it (raw 4.49 → low, 4.50 → medium). Caught by `fit_normalization.py` warning that the two sources disagreed — a tool that argues with you is worth more than one that obeys. Promoted to CLAUDE.md Hard Constraints.

### A verification criterion that could never have failed (2026-08-11)
**Problem**: wrote "the next batch must contain no rows with raw in [4.0, 4.5)" into two deploy commit messages and an evidence doc. Rows in that band will still be there.
**Root cause**: assumed `filtered_*.jsonl` holds only surfacing rows. It holds every scored row — the batch I checked has a minimum raw of 0.8412. The op-point changes the **tier**, not the presence.
**Fix**: criterion is now "no row whose raw sits in the band is still tiered `medium`", with a pre-change baseline captured before the switch (81 and 82 rows). **Capture the baseline before the change, or the check has nothing to compare against.**

### A guard that 404s on the thing it is guarding (2026-08-11)
**Problem**: `deploy_to_nexusmind.sh` aborted with `hub: repo 'jeergrvgreg/investment-risk-filter-v6' not found`. The repo exists and is healthy — 9/9 checks pass with a token.
**Root cause**: the script ran `verify_filter_package.py --check-hub` with **no token**, and the Hub returns **404, not 401**, for a private repo accessed anonymously. `.githooks/commit-msg` already resolved the token from `secrets.ini`; the deploy script did not.
**Fix**: same resolution in both. Would have blocked deploying any private-Hub filter — which is all of them except uplifting v7 (NO_HUB).

### "85% failed" was 48% correct behaviour and 26% arxiv logos (2026-08-11)
**Problem**: og:image backfill reported 4,096/4,799 failed, chronic for 5+ days. The obvious fix — `urljoin` the relative og:image values — promised 22% → 48% success.
**Root cause**: one counter conflates "no og:image tag" with real failures. And **all 51 relative-URL cases in a 200-sample were arxiv.org**, whose og:image is its own logo — "fixing" it would push ~1,200 logos per cycle downstream.
**Fix**: NexusMind#316 — split the counter, skip arxiv from backfill. Checking *which hosts* before proposing the fix is what stopped it. Concurrency was tested and refuted as a cause (18.3% at 1 and 10 workers alike).

### A +19.5pp effect that a downstream percentile CDF erases (2026-08-11 evening)
**Problem**: re-weighting `solutions v6`'s dimensions moved articles at/above an absolute 4.0 from 31.1% to 50.6% (tech-shaped 15.6% → 56.8%), which read as a fix for NM#319's enrichment starvation. Clean, reproducible, pointed at a real open issue.
**Root cause**: NexusMind's enrichment gate reads `result["weighted_average"]`, and `production_scorer.py:16-17` overwrites that field with the **normalized** score. Normalization is a percentile CDF, so a monotone rescale maps back to the same percentiles and the gain vanishes at the next refit.
**Fix**: caught before recommending, by reading the gate's caller instead of trusting the measurement. Same shape as the 2026-08-07 `COALESCE` entry below — correct at its own layer, undone downstream — so it is a **recurrence of the catalogue, and the first one the check caught pre-ship.** `solutions_v6_reweight_ablation.py` now prints the interception in section 3 so it cannot be re-derived as a win.

### A decomposition that was true by definition (2026-08-11 evening)
**Problem**: explained an 83.1% zero rate as "40.0% tech-shaped + 43.1% governance-shaped" — the two summed to 83.1% exactly, which read as a complete account.
**Root cause**: both categories were defined *using* `comm == 0`, so they partition the zero rate by construction. The exactness that made it convincing was the tell that it was circular. `content_type` is not stored in the splits, so the real question was unanswerable from that data.
**Fix**: retracted the same session, and flagged in the evidence doc with a warning marker rather than deleted. **If a decomposition lands exactly on the number it explains, check whether the categories were derived from it.**

### A smoke test's sample is not a sample of the question (2026-08-11 evening)
**Problem**: a 5-row smoke run showed `community_practice_strength` at exactly 0.000 on every row; reported it as "a striking signal" the dimension was pinned.
**Root cause**: all five rows had oracle `comm = 0`, so 0.000 was the *correct* output. The smoke test was sized to check the interface, not the distribution.
**Fix**: the calibration stats (max 6.625) contradicted it within minutes. Smoke tests answer "does it run" — reading a substantive signal off one costs a retraction.

### Two `<!-- verify: -->` annotations that could never be extracted (2026-08-12)
**Problem**: `memory/stamp-contract-integrity.md`'s claim that NexusMind#300 is fixed carried a verify command twelve lines long — embedded Python inside an HTML comment. It had **never run**, and neither had a second multi-line annotation in the same file.
**Root cause**: an HTML comment's `-->` must sit on the annotation's own line, or the extractor reports MALFORMED and skips it. Nothing read the skip: the file looked annotated, and a claim that had already regressed once after being called fixed was unchecked for four days.
**Fix**: replaced by `scripts/verification/check_content_length_populated.sh` (one line to call, evidence not a verdict word, non-zero exit, explicit `CANNOT VERIFY`). Found by adopting the framework's v1.22.0 runner, not by review — **10th occurrence of the catalogue below**. An annotation is a mechanism like any other, and "the file has a verify comment" is a config key, not an outcome.

### A mean of daily shares is not the share (2026-08-12)
**Problem**: reported GN's trend as "first half 25.0%, second half 24.3%" and posted it to a peer repo. Those are unweighted means of *daily* shares, not the pooled share, and I did not say which.
**Root cause**: daily row counts vary 8,403–21,618, so the two aggregations weight the days differently. Pooled reads 24.83% → 23.69% — a −1.14pp gap against the −0.69pp I published. The conclusion survived; the quantity was still mislabelled.
**Fix**: corrected in the peer comment the same session, caught by this repo's own review battery rather than before posting. **Sibling of `feedback-rate-needs-population`: a rate needs its denominator AND its aggregation named.** When halves differ in size, quote the pooled figure.

### A JSON argument does not survive `ssh` (2026-08-12)
**Problem**: `gn_normalization_cdf_share.py` failed on its first end-to-end run — the remote script got `Expecting value: line 1 column 3` parsing a JSON argv element that had worked locally.
**Root cause**: `ssh host cmd arg1 arg2` does not pass an argv array; it joins the arguments and hands the string to a **remote shell**, which re-splits it. Quoting that Python's `json.dumps` produced is consumed by that shell, not by the remote program.
**Fix**: interpolate the payload into the piped script source instead (`REMOTE_DUMP.replace("__TARGETS__", repr(...))`). General rule: over ssh, pass data **in the script**, never in argv, unless it is `shlex.quote`d for the far side.

### A 401 cannot tell "private" from "absent" (2026-08-13) [x2]
**Problem**: asked whether `jeergrvgreg/uplifting-filter-v7` exists on the Hub, to settle a cross-repo test conflict (#47). An unauthenticated API probe returned **401**, which reads as "not found or private" — and I had been about to report it as absence.
**Root cause**: every one of this project's Hub repos is **private**, so 401 is the *normal* answer for a repo that exists. The control proves it: `cultural-discovery-filter-v5` also returned 401, twenty minutes after `verify_filter_package.py --check-hub` had confirmed it exists. The probe could not have produced a different answer for the two cases, so it carried **zero information** while looking like a measurement.
**Occurrences**: 2 — first recorded in `memory/cd-v6-probe-hypotheses.md` on 2026-08-06 as *"`--check-hub` returns `repo not found` for a private repo when `HF_TOKEN` is unset ... its first run here was a false FAIL on a repo that existed"*. **The lesson was written down and I re-derived it anyway**, in a different status code (401 from the REST API rather than 404 from the CLI) and a different tool, which is exactly why the mechanism and not the symptom is what needed recording. Promoted out of the cd-v6-specific file for that reason.
**Fix**: re-ran authenticated with **both** controls — positive (`cd-filter-v5`, `-v6`: exist, private, adapter present) and negative (a fabricated repo name: 404). `uplifting-filter-v7` then returns a real **404**. The original claim survived, but it had been inherited from a narrative file rather than measured. **A probe that cannot distinguish the two hypotheses is not evidence for either**, and the way to find out is to run it against something whose answer you already know.

### A local convention recorded as if it were a cross-repo contract (2026-08-13)
**Problem**: `filters/uplifting/v7/NO_HUB` states that `inference_hub.py` "is intentionally NOT present" and that `verify_filter_package.py` fails fast on the combination. NexusMind's copy has carried **both** files for months — the exact combination our verifier calls a defect.
**Root cause**: two layers. (1) `cp -r` never deletes, so a file removed here survives there indefinitely — the deletion side of a sync has no mechanism at all. (2) `NO_HUB` has **zero** references in NexusMind's `src/`, `tests/`, `scripts/` or `docs/`; `filter_loader.py:146` sets `hub_class` purely from whether `inference_hub.py` exists. So the sentinel means nothing on the side that serves, and our verifier only ever runs against **our** tree — never the deployed one.
**Fix**: #47 reopened; recommendation is to delete the file *and* teach `filter_loader` to honour the sentinel. The sharp part, found by the NexusMind session: three NM#312 tests were green **because of the stale file** — they assert *importability*, not repo existence, so they would stay green pointing at a repo that 404s. **Deleting it does not break the guard; it reveals the guard was already hollow.** General rule: a convention enforced by a checker that runs on only one side of a boundary is a convention on that side only.

### A checklist item is not a check, even after the outage that produced it (2026-08-13)
**Problem**: `deploy_filters.sh` excludes `model/` from both rsync passes, so a code deploy never carries LoRA weights. Landing a new highest version without pre-placing them makes the scorer refuse to **start** — the cycle then scores nothing for all six filters, unattended, because that deploy is `ExecStartPre` on the 4-hourly `nexusmind.service`.
**Root cause**: this was already known and already written down — `docs/FILTER_PLAYBOOK.md` checklist item 5, pointing at **#67, closed**, which was itself filed *after* the omission took `cultural_discovery v5` down on 2026-05-31. Between then and now the consequence quietly grew: the weights check moved from first scoring request to **startup**, iterating every discovered filter. So the documented remedy stayed the same size while the failure got six times larger.
**Fix**: guard D in `preflight_deploy_guards.py`, proven against production state rather than a fixture — cd v5 passes, **cd v6 (the real pending cutover) fails**. ⚠️ I first reported this as undocumented and had to correct it publicly. **The finding was never "nobody knew"; it was "knowing did not help."** A documented step that has already been missed once is the definition of what belongs in a guard.

### A true report becomes a false one while it is being read (2026-08-13)
**Problem**: told a peer session "held, your checkout is clean again at `80b0608`" after reverting a dry-run copy. It was true when sent. The owner then authorised the sync **in my session**, I committed and pushed, and the peer — checking rather than accepting — found two commits on `main` and reasonably concluded my report was false and my account of `--dry-run` unreliable.
**Root cause**: I reported a **state** without its ordering. A state claim has an implicit "as of now" that survives transmission, and a peer acting on it later cannot see the event that invalidated it. Nothing was wrong with either party's evidence.
**Fix**: reconciled by laying out the ordered timeline; the peer withdrew the `--dry-run` caution once I read the staging path (line 291 stages explicitly, no `git add -A`). **When reporting a state across sessions, stamp it and say what would change it** — "clean as of 11:31, and I have an owner decision pending that would change it" costs one clause and prevents the whole exchange. The peer's underlying rule is right and worth keeping: a reported state is not a state.

### Arguing about the behaviour of a branch that cannot be reached (2026-08-13)
**Problem**: recommended leaving a `NO_HUB` filter's CPU-fallback path raising rather than auto-selecting local, on the grounds that *"a CPU fallback is already a degraded run"*. Sound-sounding, and posted to #47 as a considered read.
**Root cause**: **the branch cannot execute at all**, three independently sufficient ways — `config/app.yaml:81` `require_gpu: true` aborts before scoring; `cpu_fallback.enabled: false` since NM#203 removes the automatic fallback; and CPU scoring measured ~2–3h against ~2min on GPU (`docs/reports/2026-02-10-pipeline-fixes.md:33`) and each filter blowing the **900s per-filter watchdog** long before completion. ⚠️ I also wrote that `TimeoutStartSec=3600` SIGKILLs the run halfway — **wrong, and I repeated it from a peer without checking**: `nexusmind.service.d/override.conf` raises it and `systemctl show` reports **`TimeoutStartUSec=4h`**. The conclusion rests on the per-filter watchdog alone, which is sufficient. I reasoned about what the path *would do* without checking whether anything reaches it.
**Fix**: corrected on #47 within the hour by the NexusMind session; the recommendation strengthened rather than survived (raising is the only outcome that *terminates*). **This is the unreachable-mechanism defect arrived at from the ARGUMENT side rather than the code side, and that direction is harder to notice**: nothing shipped, so there was no outcome to prove and no green test to be falsely reassured by — the usual tripwires all sit downstream of an action. The tell was available and ignored: I described a runtime behaviour without naming the config that enables it. **Sibling consequence**: `CLAUDE.md`'s "GPU unavailable → CPU" and `docs/ARCHITECTURE.md:77`'s "slower but functional" now contradict the config, and the honest scope of `--no-gpu` is local testing on small `--max-items`.

### A truncated grep certified a guarantee it could not see (2026-08-13)
**Problem**: a `/review-changes` run reported "#93 intact — no scoring path checks content length" from `grep -rn check_content_length filters/*/v*/prefilter.py | head -5`.
**Root cause**: `head -5` was in the command. The five lines shown were four comments and one real violation; **four more violations existed past the cut**. An AST walk over `apply_filter` bodies found `ai-engineering-practice v1` (live-ish, a separate product) plus archived `cultural_discovery` v1/v2 and `uplifting` v6. The grep also could not distinguish a call from a mention, which is why several correct packages appeared as hits.
**Fix**: replaced by an AST test over live filters (`test_no_live_prefilter_checks_length_inside_apply_filter`) — it cannot be truncated and cannot be fooled by prose. **A `head` in a verification command converts "I checked" into "I sampled", and the report says the former.** Where a guarantee is worth stating, parse it; where it is worth stating twice, test it.

### A sensitivity check that passed, having tested nothing (2026-08-13)
**Problem**: seeded a deliberate violation into `nature_recovery/v4/prefilter.py` to prove a new guarantee test would catch it. The test **passed**, which read as "the test is broken".
**Root cause**: the test was fine. `nature_recovery v4` **does not define `apply_filter` at all** — it inherits the base — so the `str.replace` anchor never matched, returned the string unchanged **silently**, and the "seeded" file was byte-identical to the original. The test correctly saw no violation.
**Fix**: re-seeded into `uplifting/v7`, which does define the method, after asserting *both* that the anchor matched *and* that the file content changed. The test then failed as designed. **A passing sensitivity check is the alarm, not the all-clear** — it means either the guard is broken or the seed is, and the second is likelier. `str.replace` and `sed` both no-op silently on a missed anchor; assert the mutation landed before drawing any conclusion from the result.

### The log that was not the log, and then a permissions message read as absence (2026-08-13)
**Problem**: needed the NM#284 shadow evaluator's observed-vs-declared pass rates. Grepped `~/gpu-server/nexusmind-scorer/scorer.log` → **0 shadow lines**. Nearly reported the shadow stage as dead.
**Root cause**: two independent traps in series. (1) That file is a **stale 2026-02-20 artifact, 55 lines, ending in `ModuleNotFoundError`** — not the live log at all; a positive control on size and date range caught it. (2) The live output goes to the journal (`StandardOutput=journal`), and `journalctl -u nexusmind-scorer` returns **"No entries"** because the account is not in `adm`/`systemd-journal` — a **permissions message**, textually indistinguishable from an empty log.
**Fix**: stopped trying to read it and **recomputed the measurement instead** (`scripts/research/shadow_recompute.py`), which needs no log: the per-lens prefilter never runs, so every row in `data/filtered/` is a valid population for "what would it have blocked". **Sibling of the 401-vs-404 trap on the same day — a probe that cannot see the answer reports "nothing", and "no entries" is a sentence the tool prints for at least two different worlds.**

### A config declared its rate as a STRING, so the check built to read it never could (2026-08-13)
**Problem**: `cultural_discovery v5`'s `config.yaml` declares `expected_pass_rate: ~0.25` — YAML parses that as the **string** `"~0.25"`, not a float.
**Root cause**: the NM#284 shadow stage exists to compare observed against declared. `_load_expected_pass_rate` returns the value verbatim, so any arithmetic against it raises `TypeError` or is skipped. **For the one filter of seven whose prefilter actually does anything (71.3% blocked), the detector's own comparison could never have run.** Found by my recomputation script crashing on `float - str`, i.e. by hitting it, not by reading for it.
**Fix**: recorded in NM#284 alongside the captured table. The generalisable form: **a detector built to catch a config that lies about the runtime can be defeated by the config lying in a TYPE the detector cannot consume.** Validate the type of any declared value a guard compares against, or the guard is conditional on the config being well-formed — which is the thing it exists to doubt.

### Pre-placing model weights can itself take the scorer down (2026-08-13)
**Problem**: `FILTER_PLAYBOOK` checklist item 5 says pre-place `model/` on gpu-server *before* `deploy_filters.sh`, because the rsync excludes it. Doing exactly that opens a window in which the scorer will refuse to start.
**Root cause**: `filter_loader._find_latest_version()` selects on the directory **name** and never inspects contents. A `v6/` holding only `model/` therefore becomes "latest", `_build_filter_config` finds no `config.yaml` and returns `None`, the filter drops out of the discovered set, and the `EXPECTED_FILTERS` guard raises `RuntimeError: Cannot start scorer` — **for all six filters, not just the one being deployed.** The mirror image (code without weights) fails the same way, so no ordering avoids a window.
**Fix**: there is only a window you *choose and close*. Do both steps between cycles — `deploy_filters.sh` is `ExecStartPre` on the 4-hourly `nexusmind.service`, so the deadline is the next cycle, not a human's attention. Rollback is `rm -rf ~/NexusMind/filters/<name>/<vN>` on gpu-server, which restores the previous version as latest.

### The pre-deploy check ran in an environment the target does not have (2026-08-13) [PRODUCTION OUTAGE]
**Problem**: `cultural_discovery v6` was promoted to production, its scoring endpoint returned HTTP 500, the post-deploy smoke test caught it and `nexusmind.service` failed closed. One scoring cycle lost. #98's pre-cutover verification had said *"loaded and scored end-to-end"*.
**Root cause**: v6's `_create_stage2_scorer` branches on `self._model_path`; the scorer constructs the hybrid without one, so it took the **Hub** branch. The gpu-server scorer sets **`HF_HUB_OFFLINE`** via its EnvironmentFile, so any Hub fetch raises `OfflineModeIsEnabled` — regardless of token, repo existence or privacy. cd v6 was the **only** hybrid filter with a Hub branch at all; `uplifting v7`, `solutions v6` and `nature_recovery v4` return their local scorer unconditionally, and v6's own `inference.py` already defaulted to `Path(__file__).parent / "model"`. Nothing compared them.
**Fix**: default `model_path` to the package's own `model/`, Hub as fallback (`dcf2860`). ⚠️ **The verification is the lesson, not the fix.** The original check passed on a machine **with a token and a network**; it could not have caught this, and its green result is why the defect shipped. The retry check runs on gpu-server, in the scorer's venv, with `HF_HUB_OFFLINE=1` and no token — where it now loads locally and scores 4.9896. **`HF_HUB_OFFLINE` is documented in `memory/gpu-server.md`, which sits in this repo's own pointer table; I read past it.** A gate that tests the code and not the environment tests half the deploy.

### A backup mirror broke a deploy guard's stated premise (2026-08-13)
**Problem**: the commit-msg hook blocked a legitimate commit — `verify_filter_package.py` reported *"last_modified 2026-08-08 is OLDER than local adapter 2026-08-13 — weights likely not uploaded since last training"* for a filter whose weights were published and byte-identical.
**Root cause**: the check compares adapter **mtime** against Hub `last_modified`, on the explicit premise that the adapter is *"written by training, never by git checkout or data-prep scripts"*. Mirroring adapters **down** from the Hub for off-site backup (#110), done earlier the same day, stamps a fresh mtime on already-published bytes. Four filters were mirrored, so the guard would false-FAIL every one on every deploy-worded commit — **and a guard that cries wolf on four of six live filters is one people learn to bypass, which is exactly how #44 happened**.
**Fix**: compare **content** before failing — identical `sha256` passes with a note that the mtime reflects a mirror, differing bytes keep the original FAIL, an unavailable hash fails closed. `repo_info` now passes `files_metadata=True`, without which siblings carry no `lfs` block and the fallback could never compare anything (it would have failed closed and *looked* like it worked). Proven both ways on the real repo: identical → 9/9 pass; one byte appended → 1/9 FAIL; adapter restored to `bd4e79f2…`. **General form: when you add a new writer of a file, find every check that infers meaning from that file's metadata.**

### A wrong-path negative shipped into another repo's tracker (2026-08-13) [x2]
**Problem**: filed NexusMind#351 asserting `stage_used` is *"computed on every row and dropped at the ovr handoff"*. **Wrong repo.** NexusMind emits it on **3377/3377** rows; ovr.news discards it at ingest — `scripts/summarize.ts:887`/`:1342` project the metadata blob to a single `quality` key, and have since 2026-04-09.
**Root cause**: my evidence was `grep -rn "stage_used" scripts/summarize*.py src/output/ src/publish*` returning nothing. **All three paths are ABSENT from that repo.** The grep was empty for the trivial reason and I read it as absence. Naming a producer and grepping for a consumer is not tracing the path.
**Fix**: retracted and closed #351, pointing at ovr's lane. **Second occurrence the same day** — the first was `analysis.raw_weighted_average` reading 0 for every filter (right field, wrong nesting), which I caught myself because zero-across-the-board was too clean. This one had no such tell and shipped. ⚠️ **I wrote the gotcha for this exact trap earlier the same session** and committed the error afterwards, which is the real lesson: knowing the failure mode does not prevent it — only running a positive control does. **Before asserting a path drops a field, prove the path EXISTS** (`test -e`, or list what you searched), and prefer measuring the producer's output over grepping the consumer's source.

### A field name from the wrong LAYER reads as "no score" (2026-08-13)
**Problem**: the offline verification of the cd v6 fix reported `weighted_average=None → FAILED: no score`, suggesting a second defect on top of the one being fixed.
**Root cause**: I asserted **`raw_weighted_average`** — that is **NexusMind's STAMPED field name**, not the scorer's. A direct scorer call returns `weighted_average`. The filter was scoring perfectly (4.9896, all five dimensions, tier medium); my assertion was reading a key from one layer against an object from another.
**Fix**: assert the scorer's own key. ⚠️ **The dangerous property is that this failure is indistinguishable from "never scored"** — it produces a null that looks like absence. Flagged to ovr.news while they were investigating 3,802 NULL `raw_weighted_average` rows; it was the right hypothesis to exclude first and the dates ruled it out (pre-instrumentation, their commit `b151f7a`, 2026-08-01). **Before concluding a field was never populated, check whether the reader is asking for the producer's name for it.**

### I inferred runtime behaviour from a config key — the constraint I was quoting all day (2026-08-13)
**Problem**: told the owner, a peer repo, a PR body and `CLAUDE.md`'s filter table that `cultural_discovery v5` is **single-stage** and that v6 would **add** Stage-1 probe screening. Measured on the deployed v5 during a recovery cycle: `stage_used = {stage2: 1371, stage1_low: 1668}` — **54.9% already screened**, n=3,039.
**Root cause**: I read `filters/cultural_discovery/v5/config.yaml`, saw **no `hybrid_inference` block**, and concluded no screening. The config does not select the path — `filter_loader.py:148` sets `hybrid_class` from the **existence of `inference_hybrid.py`**, and `main.py:264` uses it if present. v5 ships that file and a probe pkl (recovered in `b790b1b`, *"3 production probe pkls that existed ONLY on gpu-server"*), so it screens while declaring nothing.
**Fix**: corrected in `CLAUDE.md`, #98 and to the ovr.news session. v6 is a **probe/threshold change worth ~+9pp of screening** (54.9% → ~63.7%), not the introduction of screening — which materially weakens the case for the cutover I had already tried to ship. ⚠️ **This is `CLAUDE.md`'s own hard constraint — *"Don't infer runtime behavior from config keys"* — and I violated it on the same day I filed two other findings whose root cause was that exact shape.** The rule does not fire on its own; the check is to ask what the LOADER reads, then measure the running system. `stage_used` on real rows answered in one query what four documents had wrong.

### A grep whose pattern cannot match the thing it looks for (2026-08-14)
**Problem**: A peer reported NM#360 "merges clean, verified locally rather than trusting GitHub's `UNKNOWN`". GitHub then computed `CONFLICTING`. I first generalised this as "a merge state is a relationship with a moving branch" — tidy, and not what happened: `origin/main` was at the identical commit throughout.
**Root cause**: The check used the **old 3-arg `git merge-tree`**, whose output format does not emit the conflict markers the command grepped for. Zero matches was read as zero conflicts.
**Fix**: `git merge-tree --write-tree`, which exits non-zero. General form: **a check whose pattern cannot match its target reports clean whatever the truth is** — a control that cannot fail. Distrusting a stale signal and verifying locally was the right instinct; the local verification was the thing that lied.

### A stacked PR showed "all checks passed" without running the tests (2026-08-14)
**Problem**: NM#364 displayed a green tick with no `test` job. Its only test evidence was someone saying they had run 1,305 tests locally.
**Root cause**: `ci.yml` triggers on `pull_request: branches: [main]`, so a PR **stacked on another branch** gets GitGuardian and nothing else. Two follow-ons, each of which hides the first: `gh pr merge` **without `--delete-branch`** leaves the stack pointing at a merged branch (auto-retarget fires only on branch *deletion*), and **retargeting does not re-run checks**, because a base change fires `edited`, which is not in the default `pull_request` type set.
**Fix**: close/reopen to fire `reopened`. ⭐ The nastiest step is the middle one: **the correction increases the PR's apparent legitimacy while changing the evidence not at all.** Before merging any stacked PR, read *which* checks ran, not whether they are green.

### Two sessions given the same owner "go" both acted (2026-08-14)
**Problem**: The owner said "go" to two sessions working the same cross-repo task. Both merged NM#360 (the second got "already merged") and both close/reopened NM#364, leaving two `test` runs as the visible fingerprint.
**Root cause**: No convention for who takes an action when one instruction reaches several sessions. The collision is only detectable *afterwards*.
**Fix**: **Under one owner instruction spanning repos, say which side is taking the action before taking it.** Cheap here only because every action was idempotent (merge, retarget, reopen) — the other session nearly pushed an empty commit first, which would not have been.

### A relay cannot carry recency (2026-08-14) [PREVENTED]
**Problem**: Two owner answers on `published.instant` existed simultaneously, pointing opposite ways — one in each session. Neither session could order them from inside its own context.
**Root cause**: A relay is accurate about *what was said* and carries nothing about *when*. The relay was faithful and would still have produced a change against a decision the owner had already made elsewhere — and it would have looked entirely legitimate in the log.
**Fix**: **When two sessions hold conflicting owner instructions, the one that can ASK wins — not the one that heard it last.** ⭐ The only instance all day where a hold *prevented* the damage rather than catching it afterwards; what made it recoverable was flagging the provenance and inviting the hold rather than asserting the instruction. The lesson is not "peers are unreliable".

### An instrument's null result is only as broad as its denominator (2026-08-14) [x2]
**Problem**: A peer's never-walked-source detector reported "2,080 keys, 0 defects" and was cited here as an instrument demonstrated capable of firing. It read **107 of 112** source files; the other four reach the same one-level walk via a different loader branch and were never examined. The output said so nowhere.
**Root cause**: The exclusion was invisible. Not a live defect — those tiers are collected by aggregators reading their own files — but "0" and "0 among the files it examines" are different claims.
**Fix**: The command now prints its denominator **and** the files it did not examine, by name, mutation-tested in both directions. Same session, same class: a tie count quoted from a *hot copy* (6,000 rows) instead of production (21,743) — 9 vs 31 — inside the paragraph correcting a different unit error. **The denominator travels with the number, or the number does not travel.**

### A correct change silently destroyed another finding's evidence (2026-08-14)
**Problem**: Fabricated dates were attributable because `now - 2h` **retains microseconds** while publisher-supplied dates almost never do — 98.7% of ~2h-gap rows carried them. A timestamp-canonicalization deploy twenty minutes later stripped sub-second precision from every emitted timestamp and **erased the fingerprint from all future rows**.
**Root cause**: The signal was **accidental** — undocumented, unowned, and depended on a serialization detail nobody had written down as load-bearing. Both changes were correct and unrelated.
**Fix**: The archive (`data/archived/`, retained indefinitely) keeps every pre-deploy row, so the attribution stays reproducible. ⭐ **The lesson is an argument FOR the explicit field, not against the change**: an accidental signal vanishes the moment someone touches its substrate for an unrelated reason. If a diagnosis depends on an undeclared property, write it down as a field or expect to lose it.

## The unreachable-mechanism catalogue

Moved out of `CLAUDE.md` on 2026-08-09 (context audit): the **rule** belongs in the
project file, the **evidence** belongs here. The rule is unchanged — name the caller,
then prove the outcome changed at the end of the run.

A mechanism that is present, configured and unreachable is this repo's defining failure:

| occurrence | shape |
|---|---|
| ducroq/NexusMind#284 | per-filter prefilters never ran in production — **six months** |
| llm-distillery#94 | a gatekeeper binding **0 times in 191,616 articles** |
| ducroq/NexusMind#281 | a gate that could never fire |
| ducroq/NexusMind#300 | the #93 `content_length` stamp computed then dropped — **0 of 50,605 rows**, and it was **five allowlists in series**, not the two first diagnosed |
| `filters/cultural_discovery/v6` | a `hybrid_inference` block and probe shipped into a package with **no inference module** — written the same day the other four were documented |
| 2026-08-07, two guards | **correct callers on the right paths**, both inert: one reverted by a later step re-sending the old value through a `COALESCE` merge (123 stored rows already carried the signature), one a complete no-op because a different commit point short-circuited before it — while its own comment asserted it was "the only point every source has in common" |
| 2026-08-09, the stage trap | the arXiv `Announce Type:` prefix is a **91.6%** detector on the collection corpus and **0.000** on NexusMind rows, because enrichment re-fetches the body between the two. Both are "production data" |
| 2026-08-09 evening, self-inflicted | 34 rows labelled `CANDIDATE_UNADJUDICATED` committed **inside** `datasets/adverse/`, the glob a planned #91 gate reads as curated evidence. Not a mechanism that couldn't fire — **a population that would have been read by one that does.** Found by re-reading my own commit, not by a test |
| 2026-08-10, self-inflicted | a guard that "refuses to emit uncalibrated scores" and checks only that the calibration file is truthy — a partial `dimensions` block passes it and the raw logits go through under a success line. Its own error message cited #98, the shape it missed. Found by a review lens, not by 270 green tests |

| 2026-08-12, **10th occurrence** | a `<!-- verify: -->` annotation twelve lines long, backing the NexusMind#300 "100% populated" claim. An HTML comment ends at its first `-->` on its own line, so the extractor never saw it and the claim went unchecked. **The file looked annotated** — which is the config-key smell one layer up: presence of the mechanism read as operation of it. Found by adopting the framework's own runner, not by review |

| 2026-08-11 evening, **caught pre-ship** | a `solutions v6` re-weighting that moved +19.5pp across an absolute 4.0 — correct at its own layer, erased downstream by a percentile CDF, because the gate reads the *normalized* score. **Not counted in the occurrence total: it never shipped.** Listed because it is the first time reading the caller stopped the recommendation instead of explaining it afterwards |

The cultural_discovery v6 entry is the point of the whole list: **knowing this failure
mode does not prevent it.** Only running the check against your own work does.

The 2026-08-11 evening row is the first counter-example: the same check, run on my own
work *before* proposing it, converted a would-be occurrence into a negative result. One
data point, not a trend — but it is the only known way the list stops growing.
