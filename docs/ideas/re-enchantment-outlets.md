# Re-enchantment outlets — divergent ideas + probe plans

**Status:** IDEAS — no build commitment. Probes only, deliberately below the priority queue
(solutions v4 #43 and the overdue #62 leakage check come first).
**Origin:** 2026-07-16 session — Byung-Chul Han's information-vs-narrative critique
(*The Crisis of Narration*, *The Disappearance of Rituals*) as a design prompt.
**Prior reflection:** wonder-lens discussion (three-construct unbundling: wonder/awe,
genuine mystery, myth/folklore; plus a fourth reading — form-not-topic).

## Reframe

The asset is the pipeline's ability to encode an editorial sensibility in a prompt and
apply it to a firehose cheaply — not ovr.news, not the trained students. Corollary:
**at newsletter/digest scale, distillation is unnecessary.** A weekly outlet consuming
~5K articles ≈ $6.50/week on DeepSeek oracle-only. Training/calibration/normalization
only trigger if an idea earns real-time scale. Precedent for non-ovr products:
ai-engineering-practice.

## Ideas

1. **The Cabinet** — weekly wonder digest (deep-sea, deep time, cosmology, archaeology,
   honest open questions). Weekly cadence is itself the Han move: ritual rhythm, not feed.
   Oracle-only; cheapest shippable standalone outlet.
2. **The Ledger of Open Questions** — publication unit = *question*, not article.
   Each tracked mystery is a page with a slowly growing timeline; filters + e5 embedding
   similarity *route* new articles onto question pages. Time-binding = narrative, literally.
   Most original idea; most Han-aligned.
3. **The Residue** — the anti-lens. Query articles scoring below every production lens's
   op-point but past prefilters: the unclassifiable remainder. Zero cost (query existing
   sadalsuud output). Doubles as an instrument for discovering the next lens + lens-set
   health check.
4. **The Slow Feed** — form-not-topic filter: score *how* a piece is told (long-form,
   time-binding, arc), regardless of subject. Research-grade: no filter has ever scored
   form; oracle consistency on it is unproven.
5. **The Folklore Observatory** — observe myth-*making* (internet legends, ritual
   revivals) as cultural signal, never truth claims. Defuses the misinformation trap of
   "unexplained" by reframing. Overlaps cultural-discovery (fine per ADR-015).
6. **Sensibility-as-a-service** — meta: the half-page-sensibility → oracle → weekly-digest
   method as a repeatable template. Business thought; parked.

## Probe plans (independent; any can die alone)

Order: **B → A → C**; D anytime. Total ≈ <$3, ~3 sessions.

### Track B — Residue query ($0) — RUN FIRST
Pull recent NexusMind filtered output (sadalsuud `data/filtered/`), select articles below
every lens op-point but past prefilters, sample 50, read. Deliverable: one-page taxonomy
of the negative space. Also answers the wonder base-rate question — if the corpus carries
no wonder-material, the fix is upstream (FluxusSource sources), not a filter.

### Track A — Wonder probe (~$0.50)
Half-page sensibility definition. Dims: `awe_scale_shift`, `genuine_unknown`,
`narrative_depth`, gatekeeper `epistemic_honesty` (wonder = "we don't know yet";
woo = "they don't want you to know"). Score ~300 master-dataset articles, DeepSeek
off-peak (avoid 08:00–12:00 CEST). Read top-20 + distribution.
**Kill:** top-20 is pseudoscience (gatekeeper failed) OR museum press releases
(foresight-style construct drift) OR thriving-style bimodal distribution.
**Pass:** hand-assemble Cabinet "issue #0" from top scorers; judge as a reader.
A digest you wouldn't send is a filter that shouldn't exist.

### Track C — Form-scoring feasibility (~$1–2)
100 articles of varying length/style; oracle scores `narrative_depth` alone; k=3 runs ×
2 oracles. Apply ADR-017 logic: poor inter-run/inter-oracle agreement → Slow Feed parked
*with evidence* (calibration-history Dead Ends entry). Confound check: if
`narrative_depth` ≈ word count (r~0.9), it measures length, not narration → dead.

### Track D — Ledger design note ($0)
One-pager: question-page product shape + routing mechanism (curated question list,
e5 similarity match, append-to-timeline). No prototype.

## Standing constraints (from prior reflection)

- "Mythical/unexplained/fantastic" is ≥3 constructs — never one prompt (ADR-010).
- Define positively, never by negation (thriving v1 bimodal collapse, ADR-015).
- Any "unexplained" reward REQUIRES an epistemic-honesty gatekeeper (misinformation
  magnet otherwise) — same pattern as nature_recovery's `recovery_evidence` gate.
- Needle filter expectations: ADR-003 screen+merge, ADR-011 embedding screening.
- English names (ADR-013).
