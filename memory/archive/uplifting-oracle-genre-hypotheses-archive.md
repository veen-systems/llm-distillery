# uplifting v7 / Thriving oracle genre bias — archive of closed sections

*Moved VERBATIM from `memory/uplifting-oracle-genre-hypotheses.md` on 2026-10-12 (`docs/TODO.md` item 2a, #163 the read
surface), under the 2026-09-27 ledger rule: sections whose verdict is REFUTED / CONFIRMED / RESOLVED. Order kept; a
subsection repeats its parent heading. The hypothesis TABLE stays whole in the live file as the index; OPEN sections and
the owner RULINGS (H-UP8, H-UP14, the accountability boundary) stay too.*

## H-UP7 — class A is BOTH a label defect and a student defect ⭐⭐

**Measured 2026-08-20.** `docs/evidence/2026-08-20-uplifting-v7-class-a-valence-bakeoff.md`.
Reproduce: `scripts/analysis/valence_bakeoff.py` (three arms; reproduce steps in its header).

Three oracles, same v7 prompt, same text, bar `max_acceptable_wa` = 3.85:

| article | student | Gemini | DeepSeek | qwen3:14b | reading |
|---|---|---|---|---|---|
| Five men arrested … raping a minor | 6.85 | **7.62** | **6.25** | **7.30** | all three fail — **label defect** |
| Greyhounds / NZ racing ban | 5.86 | 2.30 | 3.95 ⚠️ | 2.00 | oracles right, **student is the outlier** |
| Rethink Business Centre Management | 6.09 | 1.55 | 1.80 | 4.35 | oracles right, **student is the outlier** |

⚠️ 3.95 is 0.10 over the bar — inside ±0.16, indeterminate. ⚠️ n=3.

⛔ **Consequence: a prompt-only v8 fixes about a third of class A.** The residue needs
playbook §4b hard negatives, at $0 oracle cost. This is why `docs/HUMAN_THRIVING_V8_PLAN.md`
carries a Phase B2 at all.

⚠️ **A FOURTH noise floor, and it invalidates single-run gates.** Same oracle, same prompt,
same article, 10 days apart: **mean |Δ| 0.82, max 2.25** (n=7) — 5× the #95 batch floor.
**A single-run oracle score is not a measurement.** Every oracle-side acceptance gate must
be a k-run mean with a stated band. (`feedback-noise-floor-per-population`: a floor belongs
to a population and a mechanism, not to a project.)

⭐ **Vendor choice is second-order.** Gemini fires caps 3/10 vs DeepSeek 1/10 vs qwen3 0/10
over all ten rows — replicating the `cultural_discovery v5` result (Gemini 60% / DeepSeek
26%) on a different filter and prompt. But the worst row fails on **all three**, and the
smallest pairwise gap (0.18) sits inside the 0.82 noise. **Build strictness into the
mechanism, not the purchase order.**

## H-CV1 — did the keyword prefilter deplete the corpus? ⛔ REFUTED — it never ran

**Full write-up: `docs/evidence/2026-08-22-uplifting-v7-corpus-provenance.md`.** Raw logs:
`docs/evidence/2026-08-22-hcv1-runs/`. Reproduce:
`scripts/analysis/prefilter_removal_probe.py` (today's rules),
`scripts/analysis/prefilter_march_probe.py` (the rules that existed at corpus build time).

**The tempting story:** `uplifting v7`'s prefilter carries **37 `crime_violence` patterns**
(*not* 36 — the file has **77** patterns total, not 74), class A is harm-adjacent, so perhaps
the student never learned the shape.

### The answer, and it is upstream of the question

The corpus files are dated **2026-03-11**. `prefilter.py` was created **2026-03-09** and has
changed **four times since**. Running today's rules over a March corpus settles nothing, so
the March version (`991ffec`) was checked out of git and run:

| arm | population | instrument | blocked |
|---|---|---|---|
| A | 235,905 production rows | today's prefilter | 6.917% |
| B | 6,590 corpus rows | today's prefilter | 9.074% |
| **C** | the same 6,590 | **March-2026 prefilter** | **15.493% (1,021 rows)** |

**Those 1,021 rows — 350 of them `crime_violence` — are in the training splits.** A filter
that had run would have removed them. Corroborated twice over: `batch_scorer.py:1615` carries
a legacy `--prompt` mode marked **"NO PREFILTER SUPPORT"**, and the March prefilter enforced a
300-char floor while the corpus contains rows of **35 characters**.

Same instrument both sides, the corpus is **not depleted**: crime-violence matches **2.72%**
of the corpus vs **2.38%** of production.

⛔ **`HUMAN_THRIVING_V8_PLAN.md` Phase 0's "the 6,590 rows were selected with 74 Latin-script
patterns applied" is FALSE.** Corrected there 2026-08-22.

### Why the 2026-08-21 measurement could not have answered it

It inspected corpus rows that *matched* `crime_violence` — but those are **override survivors**
of the filter under test, so it measured the override leak, not removal. Checker and checked
were the same object. *(That objection also dissolves once the filter is shown never to have
run: 112 rows it blocks are present.)*

⚠️ **Ruling 3 (drop the prefilter) never depended on this** and is unaffected. It rests on
coverage, now quantified: the prefilter is a **four-language** instrument (EN/NL/DE/FR =
**74.9%** of production). Spanish — the 2nd-largest language, 16,390 rows — is filtered at
**0.89% against English's 8.89%**; Korean and Croatian match `crime_violence` at **0.00%**.

### ⚠️ What refuting H-CV1 does NOT buy

It closes **removal**. It says nothing about **composition** — see **H-UP10**, which is where
the corpus argument actually lives, and which survived measurement.

## H-UP1 / H-UP2 — the defect is in the labels

Held-out oracle test split, `datasets/training/uplifting_v7/test.jsonl`, n=660. The
weighted average is re-derived from the deployed `DIMENSION_WEIGHTS`, so the student is
not in the loop. On-lens is the ADR-021 gate's own cut, oracle weighted ≥ 4.0
(reproduces its 216/660 positive set exactly).

```
  academic-source rows   32/ 58 =  55.2% on-lens
  everything else       184/602 =  30.6% on-lens
  difference +0.246   permutation p = 0.0001 (one-sided, N=20000, seed=11)
```

**Mechanism — the weight arithmetic admits the genre by construction:**

| dimension | weight | acad | other | delta |
|---|---|---|---|---|
| human_wellbeing_impact | 0.30 | 4.55 | 2.84 | **+1.71** |
| social_cohesion_impact | 0.20 | 2.04 | 2.38 | −0.34 |
| justice_rights_impact | 0.15 | 2.11 | 2.64 | −0.53 |
| evidence_level | 0.10 | 4.76 | 2.92 | **+1.84** |
| benefit_distribution | 0.10 | 3.59 | 2.83 | +0.77 |
| change_durability | 0.15 | 3.93 | 2.87 | +1.06 |

The four dimensions a competent method paper maximises carry **65%** of the weight; the
two that encode *"for people"* carry **35%** and are the only two that fall.

Four sites in `filters/uplifting/v7/prompt-compressed.md`, worst first:
1. **Contrastive Example 5** anchors *"Open-source medical AI (global, verified)"* at
   overall **6.7**.
2. **`evidence_level`'s top bands describe what a paper IS** (7–8 *"peer-reviewed data"*,
   9–10 *"meta-analyses, independent verification, replicated results"*). It is also the
   **GATEKEEPER**, so the only dimension that could cap the total is the one the genre
   maximises — the restraint never engages.
3. **IN SCOPE** admits preprint servers: *"Knowledge freely shared (open access …)"*.
4. **OUT OF SCOPE cannot catch it**: *"Technical achievement alone … **without wellbeing
   impact**"* — a health/medical paper always asserts one. Pre-classification flags A–E
   have no research-artefact case.

## H-UP3 — refuted and blocked

Already swept to 5.00 on 2026-08-10 (`docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md`).
⛔ **Blocked above 4.5 regardless**: `MAX_NORMALIZATION_RAW_MIN = 4.5`
(`scripts/normalization/fit_normalization.py:61`); the production loader rejects a higher
fit and falls back to `score_scale_factor` with no symptom but a log line. 4.5 already
sits on the bound with zero margin. Ignoring the guard, 4.5 → 5.0 buys **1.57pp of FPR
for 13.4pp of recall** — a far worse trade than 4.0 → 4.5 was.

## 2026-08-23 — Gate A measured on TWO oracles ($0.4711)  *(context heading, repeated)*

### ✅ H-UP11 CONFIRMED — the gatekeeper rewrite (step 2b) fixes class B

Class B **1/3 → 3/3 on both oracles**. The two owner-flagged rows of 08-22 collapse:
Dawn 5.98 → **3.00** (DeepSeek) / 7.36 → **1.60** (Gemini); TSA appointment 4.63 → **2.53** /
5.53 → **0.00**. The `3.00` is `GATEKEEPER_CAP` firing, exactly as §1h predicted.
⚠️ **Directional only: 3 of 9 class-B rows** — the other 6 could not be hydrated (aged out).

### ⚠️ H-UP12 REFUTED AS WRITTEN — a prompt rule is not a rule both oracles follow

Class A improves (4/9 → **7/9** DeepSeek, 4/9 → **6/9** Gemini) and does not clear. The
finding is the **disagreement**: *"Five men arrested for raping a minor"* goes
**7.05 → 3.00 on DeepSeek** (capped) and **7.23 → 7.43 on Gemini** (*rises*) — a **4.4-point**
gap on the most reader-offensive row in the set. Step 1's text names "individual
arrest/sentencing" explicitly; DeepSeek applies it, Gemini ignores it.
⭐ **Consequence: this decides Phase B's open oracle question.** A prompt-only fix is only as
good as the oracle's willingness to follow it.

## 2026-08-23 evening — H-UP12 RESOLVED, H-UP14 RULED, and the diagnosis was wrong  *(context heading, repeated)*

### ✅ H-UP12 RESOLVED — and "Gemini ignores step 1" was the WRONG DIAGNOSIS

⭐⭐ **Step 1 was not ignored. It was OUTVOTED by five later instructions**, found by reading
**dimension-level** output instead of the weighted average: Gemini's v8 scores on the arrest row
were *identical to v7* (`evidence_level` **7.0 every run**, so the gatekeeper never got a
chance), and DeepSeek's "pass" came from step 2b alone — its non-evidence dims sat at 5–6.
**Step 1 fired on neither oracle.**

The six contradictions, five of them *after* step 1 in the prompt:

| where | what it said |
|---|---|
| `STEP 2` opening | *"Rate the six dimensions **COMPLETELY INDEPENDENTLY**"* — cancels "score ALL dimensions 0-2" |
| §4-D | the old `>50%` doom test → `max_score = 4.0` (step 1 §1 had deleted it) |
| §4-D exception | *"investigative journalism → score Justice normally"* |
| §4-E | individual crime → `max_score = 3.0`, laxer than 0-2 |
| §7 reminders 8–9 | restate both, in the **recency position** |
| output schema | recorded **no scope decision at all** |

⛔ **And every cap was inert.** `content_type` is emitted and consumed by nothing:
`filters/uplifting/v7/config.yaml:174` declares `content_type_caps`, **v7 ships no
`postfilter.py`**, and the only implementations (v1, v4) are imported by nothing. DeepSeek's
`3.00` looked like §4-E working; it was the **gatekeeper**. Two mechanisms sharing the constant 3.0.

**Fix:** all six, plus `dominant_subject` + `scope_verdict` as the **first two JSON keys** binding
every dimension, plus the **occasion test** (*the event that caused publication today; background
does not displace it; **length does not vote***).

**Result — class A 4/9 → 9/9 (DeepSeek), 4/9 → 8/9 (Gemini); class B 3/3 both.** The 4.4-point
disagreement is **closed**: arrest row **1.00 / 1.05**, both via `harm_is_subject` with
`gatekeeper_applied: False` — carried by the dimensions, the only channel any code reads.

⭐ **Unprompted side effect: run-to-run spread collapsed.** Gemini max **5.25 → 0.80**, DeepSeek
mean 0.543 → 0.237. Committing the verdict to an output field appears to *stabilise* the
judgement, not merely record it. One run each side — suggestive, not established.

