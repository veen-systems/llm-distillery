---
status: Accepted
date: 2026-07-31
deciders: [Jeroen Veen]
superseded_by:
amended: 2026-09-22
---

# ADR-022: Stamp Always, Decide Once — Gate-Module Contract

**Amended 2026-09-22** — the first SIGNAL is recorded as an explicit exception, the way
the *Revisit If* clause below requires. See *Amendment* immediately after this line.
⛔ **DRAFT: written by the assistant for the decider's review; not yet ruled.**

## Amendment (2026-09-22, DRAFT): harm is a SIGNAL, and signals are the recorded exception

### What happened

`harm_is_subject` (llm-distillery#156, NexusMind#463) shipped as a cross-lens detector that
stamps a continuous score, ships **no threshold**, has **no `_is_harm`**, and is intended to
be read per-lens from each filter's own `config.yaml`. Four documents cited *this ADR* as the
authority for that shape — NexusMind `73ad620`, its contracts changelog, llm-distillery#156's
body (*"That is ADR-022 verbatim"*), and `memory/hypothesis-ledger.md:280`.

⛔ **That citation was backwards, on all three clauses of the Decision below:**

| this ADR requires | harm does |
|---|---|
| the stamp triple, including `_is_<detector>` (bool at the deployed op-point) | ships **no** bool, deliberately |
| one enforcement point, the central load/dedup gate, `pipeline.<detector>.enforce` | N per-lens decision points, in `filters/*/config.yaml` |
| stamps are *"observability/audit fields, not routing fields"* (Risks) | the stamp exists **to be routed on** |

### Why the design is nonetheless right, and the citation is what was wrong

This ADR governs **gate modules that DROP on a GLOBAL VERDICT**. Harm has neither property,
and that is measured rather than asserted:

- **No global verdict is possible — the LENS-PROMISE argument, and this is the one that
  carries the claim.** The same article is a betrayal under one lens's promise and
  constitutive of another's: "Bihar copes with floods" breaks Thriving's *"lives getting
  better"* and is arguably exactly right under Solutions; Nature Recovery is *about*
  recovering from damage. There is no single answer to stamp, so there is no bool.
- **A SHARED detector rather than per-lens duplication — a SEPARATE argument on separate
  evidence, and it is what justifies emitting ONE field for every lens.** Of 9 articles two
  blind judges *both* called harmful, 6 were already surfaced by another lens, and ⚠️ with
  the control that makes it a finding: 53% of harm-flagged rows carry to ≥1 other lens
  against a **58% whole-panel baseline** — harm content is **as** cross-lens as anything
  else, *not enriched* for it (`H-V8-37`).
  ⛔ **These two must not be merged, and an earlier draft of this amendment merged them**,
  citing the carriage figure as proof that no global verdict is possible. It is not: it
  shows the concern is corpus-wide, which is an argument about WHERE THE DETECTOR LIVES.
  The lens-promise argument is what shows the verdict cannot be global. Both halves are
  needed and they support different clauses — the same collapse was made independently by
  a reviewer relaying this decision, which suggests the pairing invites it.
- **Nothing is dropped.** The per-lens mechanism is a **cap** on the weighted average
  (`filters/common/filter_base_scorer.py`, `short_content.cap`'s shape), not a removal. The
  article survives; its score falls below *that lens's* op-point. Clause 2 forbids a *drop*
  outside the central gate, and a cap is not a drop.
- **Clause 1 is inapplicable, not merely unmet.** `_is_<detector>` is specified as *"bool at
  the deployed op-point"*. Harm ships no op-point, so there is no bool to stamp; inventing one
  would assert a global answer this ADR's own evidence says does not exist.

### The decision

**A concern that cannot carry a global verdict is a SIGNAL, not a gate module, and the
Gate-Module Contract does not reach it.** Signals are recorded here as the exception the
*Revisit If* clause anticipated, and they carry their own contract:

1. **Stamp the score, the model version and the stack.** No verdict field, ever — a verdict
   on a signal asserts the global answer that made it a signal in the first place. Enforced
   in code, not prose: `tests/unit/test_harm_preprocessor.py::test_the_declared_harm_shape_carries_no_verdict`
   (NexusMind), which goes red when a `verdict` member or a boolean `_harm_*` appears.
2. **A signal is declared under `nexusmind.signals.*`, never `nexusmind.gates.*`**
   (`contracts/article-record.schema.json` 0.7.0). The filing location is the assertion.
3. **Consumption is per-lens, config-gated, and must CAP rather than DROP.** One cap per lens
   per concern, in that lens's own `config.yaml`.
   ⛔ **This is the carve-out to clause 2 of the Decision, stated here so the two do not
   contradict each other.** Clause 2 forbids *"a drop inside the detector"* and *"a
   consumer-side drop"*. A per-lens cap is neither: it runs inside NexusMind's own scoring
   path (`filters/common/filter_base_scorer.py`), not in a downstream repo, and it **removes
   nothing** — the article survives and its score falls below that lens's op-point. Option B
   stays closed: a *drop* outside the central gate remains forbidden, and a downstream repo
   filtering on a signal stamp is still the failure this ADR was written about.
4. ⛔ **The audit trail is owed per-lens, and harm does not yet have it.** This is the one
   guarantee clause 1 provided that is genuinely lost, and it must not be waived: this ADR's
   own evidence — the 2026-07-31 obituary diagnosis separating 47 shadow-era carryovers from
   2 true v5 FNs — was only possible because a stamp recorded what the deployed op-point had
   decided **at the time**, and a threshold reconstructed later from config is not the
   threshold as applied.
   **A lens that consumes a signal MUST record its EVALUATION, not merely its firing**, and
   MUST do so by `$ref`-ing the existing `$defs.gate_verdict` in
   `contracts/article-record.schema.json` rather than minting a fourth vocabulary. That
   definition already carries exactly the members this needs, with `score`, `verdict`,
   `model`, `enforced` and `stamped` required and `threshold` declared:
   - `stamped` — whether the lens evaluated this row at all;
   - `enforced` — whether a positive would have been capped, i.e. shadow vs live;
   - `threshold` — the value this row was judged at, not the one config holds today.
   ⚠️ **"Stamp that the cap fired" is not sufficient and an earlier draft of this clause said
   exactly that.** A row with no cap record would then mean either *no cap is configured for
   this lens* or *a cap is configured and did not fire* — the same absence-vs-judged collapse
   the signal's own score is careful to avoid (*"ABSENT, never 0.0"*), reintroduced one layer
   up. `stamped` and `enforced` being separate members is what prevents it.
   ⚠️ **The `verdict` member here is a LENS's verdict, not the signal's**, and that is the
   whole distinction this amendment turns on: the signal carries no global answer (clause 1),
   while each lens's own decision is exactly the kind of thing that has one and must be
   recorded.
   ⛔ **Blocked on a prerequisite, deliberately.** This clause multiplies stamped fields by
   lens count, and NexusMind#521 has established that the project has **no written rule for
   which stamps Contract B declares**. Landing clause 4 before that rule exists would add N
   undeclared stamps on the strength of an issue arguing that undeclared stamps are the
   problem. **NM#521 first, then this.**

⭐ **A third argument arrived after this draft was written, from ovr.news, and it closes the
remaining escape route.** Their ingest is a whitelist at **both** boundaries: a top-level
stamp never reaches the `metadata` projection because it stops earlier at a fixed column
list and a fixed `ArticleInsert` shape, and selection reads the DB at build time, so nothing
in memory is reachable. `content_quality` is their standing precedent. ⇒ *"stamp in NM,
exclude in ovr"* is **not** the "cheap field check" the cross-repo dependency rows assume —
it costs a schema change plus a write plus a read **per concern**. So consumer-side
enforcement of a signal is not merely forbidden by this ADR on evidence; for the one
consumer that would do it, it is expensive by construction. ⚠️ Reported via the review
session, not verified in this repo, and ovr.news's own suggestion — a namespaced object
passed through whole, one migration instead of N — is **undecided**.

### What this does NOT license

- ⛔ **Not a general escape hatch.** Commerce, obituary and violence promotion remain gate
  modules under the unamended contract. "Different lenses might want different policies" is
  not sufficient — the test is whether a global verdict is **impossible**, demonstrated on
  data, as `H-V8-37` did.
- ⛔ **Not consumer-side enforcement across repos.** A downstream repo excluding articles on
  a signal stamp at selection time is exactly Option B, and the measurement above is exactly
  why: a cross-lens exclusion removes two lenses' subject matter rather than gating harder.
  ⚠️ **An earlier draft named ovr.news's `docs/cross-repo-dependencies.md` Chain 7.5/7.6 as
  a live instance of this. That was WRONG and is withdrawn.** Chain 7 is
  *trajectory-framing / constructiveness* (LD#61 → LD#60/#87); that file contains **zero**
  occurrences of `harm_is_subject`, `#156` or `_harm_`, 7.5 is a conjunction whose other half
  is *"ship retrained scorers / prefilter"*, and both its blockers (LD#60, LD#87) are open.
  *"The field"* there is not this field. ⛔ **The error was confirming the QUOTE and not the
  REFERENT** — the rows were read and quoted accurately against the wrong premise. That file's
  own banner records the same failure twice before, in Chain 2 and in this same Chain 7.
- ⛔ **Not retroactive cover for the four citations.** They are wrong and are being corrected;
  this amendment is what they should have cited, and it did not exist when they were written.

### Open for the decider

**(a)** Adopt as above — signals as a recorded exception inside this ADR. **(b)** Split it
into its own ADR and leave this one to gate modules alone. This draft assumes (a) because the
*Revisit If* clause says an exception is recorded *"here"*, and one place to look beats two.

## Context

The NexusMind processing chain is a sequence of gate modules (commerce,
obituary, violence_promotion, dedup) followed by logically-parallel lens
scoring. The gate modules have drifted into three different
detection-vs-enforcement shapes:

- **Commerce**: stamps + drops at the load-skip gate (always enforced).
- **Obituary**: stamps (`_obituary_score` / `_is_obituary` /
  `_obituary_model`) in preprocessing; drop lives separately in the dedup
  gate, config-gated via `pipeline.obituary_detector.enforce` — stamps
  always written, even when enforcing.
- **Violence promotion**: stamp-only (shadow), **no enforcement path exists
  at all** — config has `enabled: true` + `threshold: 0.95` but no `enforce`
  key (verified 2026-07-31), and the config comment designates "ovr.news
  exclusion" as "a separate consumer-side step" — i.e. the current written
  plan for violence is Option B below, the pattern that already failed for
  obituary.

The question "should we drop earlier (in the preprocessor), or stamp all
and drop later (in consumers)?" came up while reviewing the chain
architecture (2026-07-31). The project history contains strong evidence on
both failure modes, so the answer deserves a settled record.

## Options Considered

### Option A: Drop early, inside each detector/preprocessor

| Pros | Cons |
|------|------|
| Single-module reasoning; blocked data never flows | Destroys the audit trail: a dropped article can never be panel-reviewed for FP rate afterward |
| Marginally smaller intermediate files | No shadow mode; every threshold change is a deploy, not a config flip |
| | Rollback requires re-collecting data, not flipping a flag |
| | Saves no meaningful compute: the central gate already sits before dedup/enrich/lens scoring |

### Option B: Stamp everything, enforce in consumers (downstream drops)

| Pros | Cons |
|------|------|
| Maximum flexibility per consumer | Every consumer must honor every stamp, forever — enforcement smears across repos |
| | Empirically failed twice: lens scoring is NOT an obit backstop (102 obit-flagged rows passed lens thresholds in one cycle, 2026-07-30); ovr.news built redundant defenses (hardcoded obit filter, editorial gate) because it couldn't trust upstream — the silent cross-repo divergence shape the 2026-05-04 manifest gotcha warns against |

### Option C: Stamp always + exactly one config-gated drop point per concern

| Pros | Cons |
|------|------|
| Full audit trail survives enforcement (stamps always written) | Blocked-but-stamped rows persist in raw files (minor storage) |
| Shadow → verify → enforce is a config flip (`enforce: true`), rollback likewise | Two places to read per gate (detector + gate), mitigated by a uniform contract |
| FP review of blocked content stays possible after enforcement | |
| Attribution stamps enable exact post-hoc reproduction (model-version parity) | |

## Decision

**We chose Option C — the pattern obituary enforcement already implements
(NexusMind `b904edc`), now promoted to the standard contract for every gate
module:**

> Every stage stamps what it saw; exactly one place per concern decides;
> every decision is a config flip away from reversal.

Concretely, each gate module MUST provide:

1. **The stamp triple**: `_<detector>_score` (float), `_is_<detector>`
   (bool at the deployed op-point), `_<detector>_model` (version string).
   Stamps are always written, enforced or not.
2. **One enforcement point**: the central load/dedup gate in
   `scripts/main.py`, gated by `pipeline.<detector>.enforce` — never a drop
   inside the detector, never a consumer-side drop.
3. **Uniform accounting**: one skip counter per detector in the Loaded log
   line (`… 5415 commerce, 1249 obituary, …`).

Evidence this earns its keep (all from this project's own history):

- The 2026-07-31 obit-sighting diagnosis separated 47 shadow-era carryovers
  from 2 true v5 FNs in minutes — only possible because stamps existed, and
  `_obituary_model` + stamped scores allowed exact production-parity
  rescoring (reproduced to 4 decimals).
- The v4→v5 corrective cycle (FN-delta panel, hard positives) ran entirely
  on stamped shadow data.
- LD#80 (commerce v2 rollback that was a production no-op for 2 days) went
  unnoticed partly because commerce lacks a `_commerce_model` attribution
  stamp.
- Obituary enforcement itself shipped as a low-risk config flip precisely
  because detection and enforcement were separated.

### Explicit non-goal

Do **not** harmonize commerce onto the frozen-mpnet+MLP recipe for
architectural uniformity. Commerce v2 was exactly that migration and
underperformed v1 in production (LD#80, rolled back). The mpnet+MLP recipe
is the template for *new* gate modules, not a migration target for working
ones. The contract above is about stamps/enforcement/config, not about the
classifier inside.

### Relationship to the lens end of the chain

NM#280 (tier double-cut) is the same principle at the other end: the
pass/block decision belongs to one place (raw score ≥ op-point, decided
upstream at calibration time), and the normalized score is
ranking/attribution metadata — not a second gate. Adopting both makes the
whole chain uniform.

## Consequences

### Positive
- New gate modules (violence promotion next) enforce via config flip with
  zero new mechanism.
- FP/recall review of blocked content remains possible indefinitely.
- Cross-repo consumers can trust the gate and delete redundant defenses
  (ovr#204 pattern).

### Negative
- Raw files carry stamped-but-blocked rows until age-out (accepted; this is
  the audit trail).

### Risks
- A consumer that filters on a stamp anyway reintroduces Option B silently.
  Mitigation: stamps are documented as observability/audit fields, not
  routing fields; enforcement changes go through the gate config only.

## Revisit If

- A gate module's detector becomes expensive enough that scoring everything
  (instead of dropping early) measurably matters (>5% of cycle time).
- Storage of stamped-but-blocked rows becomes a real cost (raw file growth
  >2× from stamps alone).
- A concern genuinely needs per-consumer policy (different ovr.news vs
  Aegis blocking rules) — that would justify consumer-side enforcement for
  that concern, as an explicit exception recorded here.

## Implementation

1. NexusMind: add missing stamp-triple fields — `_commerce_score` /
   `_is_commercial` naming kept as-is where already deployed, but add
   `_commerce_model`; violence promotion adds `_violence_model` (issue
   filed).
2. NexusMind: define `pipeline.violence_promotion.enforce` (default false)
   wired into the same gate as obituary, ready for the post-shadow-audit
   flip (issue filed).
3. llm-distillery: share the frozen-mpnet embed pass between obituary and
   violence detectors — one embed, two MLP heads (issue filed).
4. Config/log shape audit: every gate detector appears in the Loaded-line
   skip accounting with its own counter.

## Related Decisions

- [ADR-004](004-universal-noise-prefilter.md) — commerce as the only
  universal prefilter; stamp-only consumers opt in (this ADR supersedes the
  "consumers opt in to exclusion" phrasing for *enforcement*: consumers
  read stamps, the gate drops)
- [ADR-006](006-hybrid-inference-pipeline.md) — coarse→cheap-ML→big-ML
  staging inside lens modules (orthogonal: that ADR is about cost staging
  within a module; this one is about detection-vs-enforcement across
  modules)
- [ADR-016](016-drop-tier-assignments.md) — pass/block + continuous score;
  NM#280 completes it under this ADR's principle

## References

- LD#83 (obituary enforcement design, `b904edc`: "stamps always written")
- LD#80 (commerce v2 no-op rollback — missing attribution stamp)
- LD#76 audit synthesis (issuecomment-5140079896) + NM#280 (tier double-cut)
- memory/gotcha-log.md "Manifest as Anti-Pattern" (2026-05-04) — the
  cross-repo trust failure shape Option B reproduces
