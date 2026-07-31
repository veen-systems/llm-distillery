---
status: Accepted
date: 2026-07-31
deciders: [Jeroen Veen]
superseded_by:
---

# ADR-022: Stamp Always, Decide Once — Gate-Module Contract

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
