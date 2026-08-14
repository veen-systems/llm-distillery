# The contracts check result artefact — v1 spec

**DRAFT, NOT APPROVED, NOT IMPLEMENTED.** Written 2026-08-14 by the llm-distillery
session (W5.1). **Revision 3**, against two review rounds from pipeline-atlas, who
own the reader and who rejected four of draft 1's choices with better mechanisms.
The reader is written against this file, so this file is the contract between the
check and the map — specified **before** the check exists, deliberately.

Parent: `docs/CONTRACTS_PLAN.md` (W5.1). Measurements and instrument traps:
`memory/stamp-contract-integrity.md` § *The contracts layer*.

---

## 🔒 FROZEN for phase 0, as of 2026-08-14 end of day

**This spec changed four times in one day**, which is why pipeline-atlas deferred
building the reader against it — a correct call, and the churn was the problem rather
than any single revision.

**It is now frozen at `schema: 1`.** Build against this text. Any further change is a
**numbered revision with a dated changelog line at the bottom**, announced to both
implementers — not a silent edit. If a change would alter what a reader must parse,
it bumps `schema` to `2` rather than editing `1`, and both sides already have
machinery for that: the reader refuses unrecognised versions, the writer bumps the
int.

**What a reader may rely on:** every field in § *Shape* and § *Requirements*, the
three-valued `status`, `classes_not_asserted`, and the `defects[]` record shape.

---

## What this is, and what it is not

The artefact is the **only** channel between the check and any reader. Not its
stdout, not its exit code, not a log line. If a fact is not in the file, no reader
has it.

It answers **one** question: *what did the check find?* Three questions, three
sources, and **no field may pretend to answer another's**:

| question | answered by |
|---|---|
| is the check **scheduled** | systemd (`LoadState`) — never this file |
| is the result **fresh** | `generated_at_iso` + `period_seconds` |
| what did it **find** | this file |

## Prior art — this problem is already solved twice inside the estate

Round 2's behaviour sweep found two working instances on the **energy** chain that
the contracts plan did not know existed. All three below were verified in place by
both sessions.

| precedent | what to copy |
|---|---|
| `energydatahub/utils/data_quality.py` → `data/data_quality_report.json`, gated at `.github/workflows/collect-data.yml:83-95` | the artefact + a gate that **fails when the file is MISSING** (`:84`), and the severity ladder (`:122`, fall-through `:129`) — **with the fix in § *The ladder*** |
| `augur/scripts/wait_for_edh.sh` + `augur-daily.timer` | **the mechanism only** — a cross-repo reader on a timer keyed on the artefact's own `timestamp`. ⚠️ **Do not import its policy**: on timeout it exits 0 and proceeds on possibly-stale data, deferring the signal to a next-day pre-flight ALARM in a commit message. Defensible there (failing would freeze the dashboard with no signal at all); the opposite of what this artefact's readers must do |
| `pipeline-atlas/ops/make_snapshot.py:570-608` | the reader shape — and a scar, § *The scar, both halves* |

## The ladder — with the rung the precedent is missing

`critical > error > warning > info`, from `energydatahub/utils/data_quality.py:122`.

⚠️ **But `:129` returns `info` as the FALL-THROUGH: nothing wrong ⇒ `info`.** So
`info` is not the lowest severity, it is the *absence* of severity, and the ladder
**cannot represent "clean" at all.** Two consequences:

- `overall_status: "info"` would be ambiguous — clean, or info-severity findings
  exist. A panel cannot render those the same.
- It breaks the phase-3 proof, below.

**So this spec adds a rung: `clean` (or `ok`) below `info`.** One estate, one
ladder — and the fix should travel back to energydatahub, which has the same
ambiguity.

## Path, ownership, mode — a hard constraint, not a preference

⚠️ **The reader runs inside a systemd mount namespace**
(`ops/pipeline-atlas-refresh.service`): `ProtectSystem=strict`,
`ProtectHome=tmpfs`, `PrivateTmp=yes`, and `BindReadOnlyPaths=` exactly three
sibling roots — NexusMind, FluxusSource, ovr.news. Inside it, `/var/lib`, `/run`,
`/srv`, `/tmp` and `$HOME` **do not exist**.

**An artefact written outside those roots is ENOENT to the reader forever**, while
the check runs perfectly every night — this plan's own thesis executed against this
plan, and invisible from the writing side.

- **Path: `<nexusmind_root>/data/contract_check.json`** — confirmed accepted by the
  reader. NexusMind owns Contract A and B; matches the reader's root convention;
  needs no unit change.
- Moving it requires a new `BindReadOnlyPaths` line in a **root-owned installed
  unit**, plus its reinstall. **The move is not free — say so before making it.**
- **Mode 0644, traversable parent.** The reader runs `User=jeroen`; if the check's
  timer runs as root, a 0600 artefact is EACCES forever — and that failure **has no
  visible cause from either side**: the writer sees a file, the reader sees nothing.
  This belongs in W5.1's definition of done next to the install step.

Rejected: an energydatahub-style version sidecar. A second file is a second thing
that can go missing independently.

## Arming is not in this file — and the spec owes two unit names

Draft 1 called `gate_level` "the armed/not-armed state". **Wrong, and it was the
project's signature failure in miniature, inside a spec written to catch it.** Two
different questions were sharing a word:

- **enforcement** — at what severity does the check fail? A config flip.
  **Renamed `enforce_at`.**
- **scheduling** — is the unit loaded and firing? Only systemd knows.

A file cannot attest to its own scheduling: an uninstalled check cannot write a
file saying it is uninstalled.

⚠️ `systemctl show` on a **nonexistent** unit exits 0 and reports
`ActiveState=inactive, Result=success` — **byte-identical to a real stopped unit**
(proven by the reader's session, diffing a bogus name against a real one).
`LoadState=not-found` is the only discriminator, and committed-but-uninstalled is
precisely that.

✅ **PUBLISHED AND SHIPPED — the names are `nexusmind-contract-check.timer` and
`nexusmind-contract-check.service`.** Both are in pipeline-atlas's `UNITS` as of
`ff9dcc6` and both are committed by NexusMind. **These names are authoritative; the
JSON skeleton above is illustrative and was WRONG until rev 5** (it said
`contract-check.*`, unprefixed). *That contradiction is exactly the placeholder
failure the reader refused to accept — a wrong hardcoded name renders
`LoadState=not-found` forever, a confident false NOT-ARMED for a check running fine
under its real name.*

**W5.1 must publish BOTH unit names** — `<name>.timer` and
`<name>.service`. They are different units and the reader takes `LastTriggerUSec`
from one and `ExecMainExitTimestamp` from the other. With the names, *never
installed* is distinguishable from *installed and has not written yet* — strictly
better than inferring either from a missing file.

## The five states of the file

All five render as some kind of unknown; they are **five different things to go
fix**, and a panel that says only "unknown" sends the reader to the wrong one.

| # | state | meaning |
|---|---|---|
| 1 | absent | no result has ever been written |
| 2 | present, unparseable / truncated | something wrote badly — most likely mid-write. **Must not collapse into 1** |
| 3 | present, **EACCES** | the mode/owner failure above — no visible cause from either side |
| 4 | present, parseable, unrecognised `schema` | refuse to render, state the version |
| 5 | present, parseable, older than `period_seconds` × margin | stale |

Plus: present, fresh, complete.

## Shape

Matches the reader's existing `to_json()` record — `{label, value, unit, source,
error}` plus a verbatim `problems[]` — so it routes through the existing renderer
with almost no new code, and **the caveats travel with the figures**.

```json
{
  "schema": 1,
  "generated_at_iso": "2026-08-14T02:20:11+00:00",
  "period_seconds": 86400,
  "status": "ok",
  "overall_status": "clean",
  "enforce_at": "none",
  "exit_code": 0,
  "classes_not_asserted": 1,
  "units": {"timer": "nexusmind-contract-check.timer",
            "service": "nexusmind-contract-check.service"},
  "validator": {"name": "check_contracts", "commit": "abc1234"},
  "contract":  {"path": "NexusMind/contracts/fluxussource-output.schema.json",
                "commit": "1d6133c", "sha256": "..."},
  "input":     {"path": ".../content_items_20260814_080753.jsonl",
                "mtime_iso": "...", "rows_validated": 3697},
  "scope": {
    "edges_covered":     ["contract-a"],
    "edges_not_covered": [
      {"edge_id": "contract-b",
       "reason": "Contract B declares metadata with zero properties — nothing to assert"},
      {"edge_id": "publish",
       "reason": "ovr's ingest projection at summarize.ts:887 is code, not a schema"}
    ]
  },
  "defects": [
    {"class_id": "required_absent.priority", "asserted": true,
     "rows": 928, "errors": 928, "severity": "error", "not_asserted_reason": null},
    {"class_id": "published_date.format.date_time", "asserted": false,
     "rows": null, "errors": null, "severity": null,
     "not_asserted_reason": "format assertion inactive: rfc3339-validator not installed"}
  ],
  "problems": ["..."]
}
```

### Requirements, each with the failure it prevents

**A. Atomic write.** The reader fires every 20 minutes, unconditionally — 72
reads/day *will* catch a partial write. Write `contract_check.json.tmp` in the same
directory, then `os.replace()`.

**B. `input.rows_validated` is mandatory, and zero rows must be unrenderable as a
pass.** If the check finds no input and validates 0 rows, an empty `defects` is
literally true and reads green. Ship `rows_validated` plus the input path and mtime
so the reader can say *"checked 0 rows — that is not a pass"*.

**C. ⭐ Enumerate every defect class ALWAYS, and let a class say it was not
asserted.** The most important requirement here, and the one draft 1 specified
past. A class not evaluated — input missing, rule disabled, checker silently
no-opping — carries `asserted: false` **with a reason**, never omitted, never `0`.

The concrete case is in this plan's own through-line: `format_checker=FormatChecker()`
**no-ops for `date-time` without `rfc3339-validator`**. Under draft 1 that class
reported `rows: 0`, rolled up clean, and the artefact went green over a check that
was switched off — *inside the very tool phase 0 is built on*.

**`classes_not_asserted` is a top-level count, rendered next to any green, and
`overall_status` MUST NOT read `clean` while it is non-zero.**

> This is `scope` one level down. `scope` names hops the check structurally cannot
> see; an unasserted class is a constraint it cannot see **inside a hop it claims
> to cover**. Both are needed — `scope` alone stops the over-read *across* hops and
> does nothing about the over-read *within* one.

**C⁺. Two defect classes the check must carry that are not schema violations at
all.** Both were found in round 2 and both are invisible to any validator that only
compares bytes against a schema:

```json
{"class_id": "drift.contract_a_frozenset_vs_required", "asserted": true,
 "rows": null, "errors": 0, "unit": "fields", "severity": "clean",
 "source": "NexusMind/scripts/main.py:118 vs contracts/fluxussource-output.schema.json"}
```

- **`drift.contract_a_frozenset_vs_required`.** `main.py:118` holds a **hand-copied
  duplicate** of the schema's `required` set, used at `:1008` to **drop rows on the
  production path** — the only Contract A mechanism that enforces. Its only link to
  the schema is a **comment**. Edit the schema and not `main.py` and the check
  validates one artefact while production enforces another, **both green**. They
  match today (8 fields each, verified 2026-08-14). This is a one-line set
  comparison and it belongs in the check because nothing else will ever notice.
- **`unreported.schema_invalid`.** The production gate already counts its own drops
  in `stats["schema_invalid"]`, and `data/last_run.json` publishes neither it nor
  `json_errors` (verified: that file has **no `stats` key at all**). **The numbers
  exist and have nowhere to land** — the same shape as ovr's `validate.ts` dropping
  rows into an unread `warn`. **n = 2** — every validate-and-drop mechanism found so
  far has unread output, with a third hop (FluxusSource) that **does not self-validate
  at all**, so it has no such mechanism to check. A pattern on a small denominator,
  stated as such. It is still the plainest justification this artefact has.
- **`uncomputed_at_callsite.*` — a distinct and worse class.** ovr's
  `validateArticles` returns `{ valid, summary }` and `summarize.ts:404` destroys
  `summary` in the same expression that consumes `valid`. **No downstream plumbing
  helps**: the artefact can only read what a producer hands it. Likely the commoner
  of the two, *because it leaves no trace at all to notice* — not even a log line to
  grep. **A hop of this class needs two steps in phase 0b: surface the count, then
  land it.**
  🚫 **Do NOT publish it through `last_run.json`.** That file is written at the end of
  a pipeline run (`main.py:3283`, called `:3577`), so putting the count there requires
  computing it **inside the pipeline process** — restoring the cycle-tail run both
  consumers ruled out. It is cheap *because* it rides a surface populated by the thing
  that must not do the work.
- **`drift.strip_list_vs_observed_keys`.** If the check is wired to
  `validate_production_contract.py`, its counts are **conditional on that script's
  strip list being complete** — it reads NexusMind's *mutated* `data/raw` and
  subtracts NexusMind's own stamps to reconstruct producer output. Add a stamp
  without extending the strip and the check reports `additionalProperties` violations
  **against the producer, for keys the producer never emitted: a false red pointing at
  the wrong repo.** The mirror of the frozenset class. *(`validate/validate_contract_a.py`
  reads the producer's directory directly and carries no such dependency — which is
  the strongest argument for scheduling that one instead.)*

**D. Always write the file, including on failure** — plus `problems[]`. A check that
crashes and writes nothing is indistinguishable from one never installed.

⭐ **`status` has THREE values, not two: `"ok" | "found_violations" |
"could_not_run"`.** The third is a hard requirement, not a nicety:

- **`jsonschema` is in no dependency manifest in NexusMind** (verified on `main`:
  absent from `requirements.txt`; `deploy/gpu-server/requirements.txt` carries only
  `pydantic`). CI works because `ci.yml:25` pip-installs it **inline**; sadalsuud
  works because its venv happens to have it. **A venv rebuilt from the manifest
  cannot run any schema mechanism in the repo.** `rfc3339-validator` is missing the
  same way, which is instrument trap 2's third part.
- `validate_production_contract.py` already exits **2** for "could not run" vs **1**
  for "found violations" — **a distinction worth nothing unless the caller honours
  it.** Today *"no new violations"* and *"could not import jsonschema"* both produce
  a non-1 exit.

> ***Exit 2 = "I did not look" — and a reader must never render it as green.***
> Local precedent: `verify_decision_log.py` prints PARTIAL and exits 2 rather than
> passing (NM#326).

**D⁺. Name the tree, always.** `input_path` and `rows_total` are already required
because *a result without its population is not a measurement*. The same applies to
code: **every git-derived figure must name its ref.** These checkouts are shared with
parallel sessions, and a bare `git log --` answers about whichever branch someone
else last left checked out — measured, mid-session: one baseline figure read **1** on
`main` and **2** in a working tree, and *changed value while being written down*
because a peer committed to that branch. If the check reports anything derived from a
repo, it reports the ref and short SHA it read.

**E. Declare `unit` per class.** Phase 0a's entire correction is rows-vs-errors.
`rows` and `errors` are both required **even when equal** — merging them is how the
current instrument got 1,195 for 928 rows.

**F. Freshness self-describing — and `period_seconds` must be DERIVED from the
unit, not typed.** Typed, it is a third copy of a number that lives in
`OnUnitActiveSec`, and a spec written to end undeclared interfaces must not create
one in its own second paragraph. `generated_at_iso` carries a **UTC offset** — a
contracts checker does not get to ship a naive timestamp.

**The margin belongs to the reader**, not the file: the panel and the phase-3 gate
should not be forced onto one tolerance. The reader will use 2× cadence.

**G. Two version stamps.** `schema` (int, this artefact's shape — the reader refuses
unrecognised values) and *what was validated*: the contract's path plus commit/sha,
and the validator's own commit. Contract A has one commit ever, so when it changes
the panel must say the counts are against a **different contract** rather than
report a step change as an improvement. If a commit is expensive, send `null` **and**
an mtime — a field declared and never populated is a schema that asks less.

**H⁺. The canonical wording of the boundary**, drafted by the ovr.news session, who
own the hop it describes. Use this text wherever a green result is presented:

> The contract check validates Contracts A and B — the bytes FluxusSource emits and
> the bytes NexusMind emits. **It does NOT validate the ovr.news hop.** ovr's gate is
> code, not a schema: an ingest-time projection keeps **one** metadata key, and a
> field-by-field row mapping drops any top-level field nobody wrote a line for.
> Neither is expressible as a schema and **neither reports what it dropped**. A fully
> green check is therefore compatible with ovr discarding **every metadata key but
> one — which is what it does today.** Read a green result as *"the producers emitted
> what they declared"*, never as *"the pipeline is contract-checked"*.

⭐ **The load-bearing move is stating the compatible-with claim as a concrete
quantity in the same breath as the green.** *"Does not cover the ovr hop"* alone
reads as a gap someone will close later; *"green is compatible with all but one
metadata key being dropped, and they are"* cannot be read that way.

**The supporting measurement is denominator-independent, which is what makes the
wording safe:** ovr's own `current-state` records **3,000 of the 3,000 most recent
stored blobs carrying exactly ONE top-level key.** That counts what ovr *stores*, so
it does not move with how many keys arrived in a given tick.

*(Their draft said "50 of 52". Rewritten to "every key but one" — the 52 is a
single-run count with a 4× spread across runs, see the plan's round 2. The force was
always in the ratio being near-total. ovr adopted the change in their own docs rather
than let the two estates disagree, and **kept a retirement note in place**, on the
reasoning that a number quoted in three places and then silently changed is how the
next session re-derives the old one.)*

**H. `scope` is keyed to the atlas's canonical edge ids**, not ad-hoc hop strings —
`contract-a`, `contract-b`, `run-timing`, `filter-packages`, `aegis-gist`,
`publish`, from `pipeline-atlas/model/chain.yml`. Ad-hoc strings leave the reader
string-matching prose against a generated view. **Reasons are per-edge**, because
two uncovered edges have different reasons: Contract B has nothing to assert
(`metadata` declared with zero properties), while ovr's gate is code, not schema.

**I. The check validates its own artefact against this spec before writing it.**
A contracts checker that emits an unvalidated artefact is the joke writing itself.

### What the reader will not do

- **It will not compute pass/fail.** Whether 928 is acceptable is a judgement, and
  the atlas does not make judgements (W4.3 accepted as reporting, refused as running).
- **It will not put a count in page prose.** The numbers reach a reader through the
  snapshot panel or a verify command, nowhere else.

## The scar, both halves

The reader's `read_last_run` carries a comment about an earlier version that hunted
four **nested** blocks that did not exist, matched 0 of 4, emitted no problem line,
and rendered an empty section.

- **Half A — taken:** nothing a reader keys on sits behind a nested path. A wrong
  path and an absent value are indistinguishable.
- **Half B — the half that actually ended the bug, and draft 1 missed it:** the
  reader must **count what it matched and report when the count is zero.**
  Flat-and-required is necessary, not sufficient; *required-in-a-spec is a
  declaration, and a declaration with no caller decays to a lie* — principle 3.

⚠️ Sharper version in the same file: at `read_fluxus_run` the equivalent counter's
**first version was unreachable** — it counted the selector key it had just selected
on, so `found >= 1` always. The check was dead, and its message still quoted
`runs[-1]`, wording from before selection moved to `max()`, *precisely because
nobody ever saw it print*. **A dead check keeps whatever it was born with.**

## Acceptance — the first thing this artefact must prove

**`source_group`.** Reporting the four known defect classes is circular: those
classes *are* the current validator's output, so reproducing them shows the check
still runs, not that it detects. The genuine control is an independent, dated,
never-shown defect arriving against Contract A's closed top level.

Measured 2026-08-14:

- FluxusSource emits it on **100% of rows from `collection_20260813_200749` onward**
  (0% through `…_161007`) — their `docs/OUTPUT_CONTRACT.md`, verified across all 51
  retained runs.
- NexusMind's Contract A **still does not declare it** — grepped `contracts/`,
  `validate/` and `scripts/validate_production_contract.py`, all three paths
  confirmed to exist first, so it is not a wrong-path zero.

**The control is intact and time-limited: hold W2.2 behind the check reporting it.**

## How phase 3 gets proved before phase 3 — and it takes TWO observations

Round 1's objection: *"exit 0 always"* needs a shipped proof it can go red, or the
phase-3 flip is the first test of the wiring.

⚠️ **Draft 1's proof was itself defective**, and in the mirror-image of the register
entry it cited. Setting `enforce_at: "info"` makes `exit_code` non-zero on *every*
run, clean ones included, because the precedent ladder's fall-through is `info`.
That shows the wiring is connected; it does **not** show the gate discriminates.
Instead of a self-test that could never fail, a gate that could never pass — which
would surface at phase 3 as a permanently-red gate getting switched off, the exact
failure the sequencing decision exists to avoid.

**The proof is two observations:** with `enforce_at: "warning"`, a run with a known
warning exits non-zero **and** a run without one exits zero. *A gate proven in one
direction is not proven.* (This is why the ladder needs a `clean` rung.)

⚠️ **rev 4 — the proof must read CLASS-LEVEL results, NOT `overall_status`.**
*(NexusMind, on implementing it.)* **`overall_status` cannot read `clean` today, by
construction**: two classes are permanently unassertable — `published_date.format.date_time`
(no `rfc3339-validator`, NM#358) and `unreported.schema_invalid` (the counters exist
and have no surface to publish on, and must not ride `last_run.json`). Since
`overall_status` may not read `clean` while `classes_not_asserted > 0`, the best this
check can currently report is `info`. **That is the rung doing its job, not a bug** —
but it means a both-directions proof keyed on `overall_status` can never observe the
zero-exit half. Prove it at the **exit-code and per-class** level: a conforming row
exits 0, a violating row exits 1, **plus a control on the refusal guard so it cannot
pass by always tripping.**

**And the reader owes the same proof.** W4.3's definition of done is that the panel
reads *"contract check: NO RESULT EVER · unit not installed"* **on the served site
before the check exists** — otherwise a reader that renders nothing until the
artefact appears is the dead mechanism built one layer up. That state is free today.

---

## Revision log

Required by the freeze protocol. A revision is a numbered entry here plus an
announcement to both implementers — never a silent edit.

- **rev 3 — 2026-08-14, frozen.** `schema: 1`. sha256
  `46fea1a2fb016780c9196e96583ce49f92b8b76ac8906933359dbae44a411881`.
- **rev 4 — 2026-08-14.** `schema: 1` **unchanged — no reader change required.**
  Clarifies § *How phase 3 gets proved* only: the both-directions proof must read
  **class-level results and the exit code**, not `overall_status`, because
  `overall_status` cannot read `clean` while two classes are permanently
  unassertable. Raised by NexusMind while implementing; no field added, removed or
  retyped.
- **rev 5 — 2026-08-14.** `schema: 1` **unchanged — no reader change required.**
  **Corrects a live contradiction**: the JSON skeleton's `units` said
  `contract-check.timer` / `.service` while the authoritative names, already shipped
  in pipeline-atlas's `UNITS` (`ff9dcc6`) and committed by NexusMind, are
  **`nexusmind-contract-check.*`**. An implementer copying the skeleton would have
  hardcoded a name that renders `LoadState=not-found` forever — a confident false
  NOT-ARMED. Found by pipeline-atlas, who declined to change their committed names off
  an example block. No field added, removed or retyped.
