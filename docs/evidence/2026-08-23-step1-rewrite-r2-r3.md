# Step 1 rewritten against Gemini — the blocker was five contradictions, not the wording

**2026-08-23.** Two Gate A re-runs of the **v8 arm only** (the v7 control file is untouched;
its numbers below are yesterday's run). 90 calls each, **45/45 both oracles, 0 errors, no
partial-run warning**. Spend **≈$0.47 estimated**, not measured — derived by halving the
2026-08-23 four-arm invoice ($0.4711) at near-identical per-arm token volume. Nothing trained,
nothing deployed.

Predecessor: `docs/evidence/2026-08-23-gate-a-two-oracle-run.md`.
Raw results: `…/scratchpad/gateA/gateA_{deepseek,gemini}_v8r{2,3}/results.jsonl` (session-local;
every number that matters is reproduced below).

---

## 1. The diagnosis: step 1 was not ignored, it was outvoted

Yesterday's read was *"Gemini ignores step 1"*. That was wrong. Reading the **dimension-level**
output (not the weighted average) showed Gemini's v8 scores on the arrest row were **unchanged
from v7** — `evidence_level` 7.0 in all three runs, so the gatekeeper never got a chance.
DeepSeek's "pass" on that row was **step 2b alone**: its non-evidence dims sat at 5–6, meaning
**step 1 fired on neither oracle**.

The candidate prompt contained **six instructions that licensed a higher score than step 1
ordered**, five of them *later in the prompt* than step 1:

| # | where | what it said | vs step 1 |
|---|---|---|---|
| 1 | `## STEP 2` opening | *"Rate the six dimensions **COMPLETELY INDEPENDENTLY**"* | cancels "score ALL dimensions 0-2" |
| 2 | §4-D | the old *">50% doom-framed"* test → `max_score = 4.0` | step 1 §1 **deleted** this test; 4.0 is laxer than 0-2 |
| 3 | §4-D exception | *"investigative journalism → score Justice normally"* | licenses the exact upward move |
| 4 | §4-E | individual crime → `max_score = 3.0` | laxer than 0-2 |
| 5 | §7 reminders 8 & 9 | restate the caps and the >50% test | **recency position** — the last rules read before the article |
| 6 | output schema | records **no scope decision** | the verdict was never committed to |

⛔ **And the caps were inert anyway.** `content_type` is emitted and consumed by nothing:
`filters/uplifting/v7/config.yaml:174` declares `content_type_caps`, **v7 ships no
`postfilter.py`**, and the only implementations are v1/v4, which nothing imports. DeepSeek's
`3.00` on the arrest row looked like §4-E working; it was the **gatekeeper** — two mechanisms
sharing the constant 3.0. *(15th occurrence of "name the caller, then prove the outcome
changed".)*

## 2. Changes made

**r2** — fixed all six: scoped the independence instruction; deleted §4-D/§4-E's rules and
demoted §4 to a diagnostic label; rewrote reminders 8/9 to say the caps do not exist; added
`dominant_subject` + `scope_verdict` as the **first two JSON keys**, ahead of every dimension,
binding `scope_verdict != in_scope` → all six dimensions 0-2; tightened the three IMPACT
rubrics so an arrest, a joint agency operation, and a harm-stopped-without-documented-benefit
cannot reach the upper rungs; added a worked JSON example of the failing shape and put the new
fields in all four existing examples (few-shot beats schema).

**r3** — added the **occasion test**: the event that caused publication *today*, which is what
the headline and first two paragraphs report. **Background does not displace the occasion, and
length does not vote.** Guarded explicitly so an occasion that is *completed and delivered*
(remains identified, verdict handed down, compensation paid) stays `in_scope` however terrible
the setting.

⛔ **Also removed: leaked tool-call scaffolding** (`</content></invoke>`) at the very end of the
prompt. It is present in the **deployed** `filters/uplifting/v7/prompt-compressed.md` too, and
was therefore in **both** arms yesterday — so it did not confound that comparison, but it has
been appended to every uplifting v7 oracle label ever collected. **Left in v7 deliberately**
(it is the baseline that produced those labels); fixing it is a separate call.

## 3. Result — mean of k=3, bar 3.85

| row | cls | DS v7 | r1 | r2 | **r3** | GM v7 | r1 | r2 | **r3** |
|---|---|---|---|---|---|---|---|---|---|
| Five men arrested (Mashonaland) | A | 7.05 | 3.00 | 1.05 | **1.00** | 7.23 | 7.43 | 7.25 | **1.05** |
| Parents of baby girl killed | A | 7.07 | 4.03 | 1.05 | **1.05** | 7.15 | 6.90 | 1.87 | **1.77** |
| Celebrated at birth → sex work | A | 6.10 | 5.88 | 0.90 | **0.90** | 6.80 | 6.55 | 4.97 | **6.53** ⛔ |
| Assault/harassment victim line | A | 5.32 | 2.08 | 0.90 | **0.97** | 6.10 | 2.43 | 1.53 | **1.27** |
| Children's helpline calls up | A | 3.40 | 1.77 | 0.90 | **0.83** | 3.87 | 1.88 | 1.00 | **1.00** |
| Woman 'tortured' (Sahiwal) | A | 1.85 | 1.08 | 0.57 | **0.78** | 3.10 | 1.42 | 1.05 | **1.05** |
| Travelodge / DV victim | A | 1.32 | 0.75 | 0.75 | **0.67** | 2.62 | 1.10 | 0.95 | **1.15** |
| Greyhounds to Australia | A | 4.03 | 1.22 | 0.93 | **0.90** | 1.42 | 0.60 | 0.70 | **0.75** |
| Rethink Business Centre | A | 1.78 | 1.38 | 0.93 | **0.93** | 0.80 | 0.73 | 1.00 | **0.77** |
| Curing the cause (op-ed) | B | 5.98 | 3.00 | 0.93 | **0.83** | 7.36 | 1.60 | 0.80 | **0.80** |
| TSA clinician appointment | B | 4.63 | 2.53 | 1.00 | **0.65** | 5.53 | 0.00 | 1.00 | **0.90** |
| EBA ESG dashboard | B | 2.47 | 3.22 | 0.45 | **0.63** | 0.45 | 0.45 | 0.52 | **0.55** |

**Class A (blocking): DS 4/9 → 7/9 → 9/9 → 9/9. GM 4/9 → 6/9 → 7/9 → 8/9.**
**Class B (reported): DS 1/3 → 3/3 → 3/3 → 3/3. GM 1/3 → 3/3 → 3/3 → 3/3.**

✅ **The 4.4-point oracle disagreement is closed.** The arrest row was the row that made step 1
unshippable: DeepSeek **1.00**, Gemini **1.05** — 0.05 apart, and both by `harm_is_subject`
with `gatekeeper_applied: False`, i.e. **carried by the dimensions**, which is the only channel
any code reads.

⭐ **Run-to-run spread collapsed**, unprompted: DeepSeek mean 0.543 → **0.237** (max 1.600 →
0.750); Gemini mean 0.595 → **0.198** (max **5.250 → 0.800**). Committing the verdict to an
output field appears to stabilise the judgement, not just record it. *(One run each side —
suggestive, not established.)*

## 4. No-regression control — the honest part

| row | assertion | DS v7 → r3 | GM v7 → r3 |
|---|---|---|---|
| Rappler, "silent crisis" | raw > 4.5 (**only row with a production baseline**, 6.486) | 5.42 → **4.90** ✅ | 5.92 → **5.45** ✅ |
| Unifesp, transitional justice | **delta**: v8 ≥ v7 | 3.57 → **3.55** (−0.02, inside the 0.237 spread) | 4.88 → **4.25** (**−0.63**) ⛔ |
| Rwanda, development finance | raw > 4.5 — ⚠️ **an invented bar**; the row was rejected as adverse and never observed | 1.53 → **0.73** | 3.70 → **4.20** |

⚠️ **Unifesp fails its delta on Gemini (−0.63), and that is a real cost of these changes.** It
is not the occasion rule misfiring: all six r3 runs return `in_scope` with `dominant_subject` =
*"forensic identification of blood residue at a former torture centre"*, so **the guard worked
as written**. The drop comes from the tightened IMPACT rubrics. It still scores 4.25, above the
3.85 bar and above ovr's 4.0 enrichment gate — suppressed rank, not suppressed content.

⛔ **Rwanda still splits the oracles by 3.47** and remains the open **owner call** on
development finance. Unchanged by this work.

## 5. ⛔ What this does NOT settle

- **The one remaining class-A failure is a different defect.** *"Celebrated at birth, pushed
  into sex work"* — Gemini returns `in_scope` in all three runs with `dominant_subject` = *"the
  intergenerational practice of sex work in the Banchhada community"*; DeepSeek returns
  `harm_is_subject` / *"the exploitation of Banchhada women and girls"*. **Gemini adopts the
  article's own euphemism.** Neither the harm-event rule nor the occasion rule bites, because
  there is no *event* — it is an ongoing condition. A rule for **harm as an ongoing practice or
  custom** is the r4 candidate; it is not written.
- ⚠️ **Three iterations against the same 15 rows is how a prompt overfits.** Class A is the
  design target and has now been optimised against directly. The controls are the only defence
  and one of them moved the wrong way. **Treat 9/9 and 8/9 as measured-on-the-training-set.**
- ⛔ **A correction I nearly published:** I hypothesised the arrest row was *mislabelled* —
  adjudicated from its 300-char excerpt, which contains only the arrest, while two thirds of
  the full article is a community campaign (which is exactly what Gemini named). **The record
  refutes it:** `labelled_by: editorial judgement (ovr.news owner), 2026-08-09 — accepted from
  an ovr.news reader flag **after full-text review**`. The label stands; Gemini's reading was
  the error.
- ⛔ **Class B is still 3 of 9 rows** — 6 could not be hydrated. Directional.
- ⛔ **Nothing here touches the student.** §1f measured 2 of 3 class-A rows as the *student*
  disagreeing with all three oracles. **Phase B2 hard negatives remains the larger half of the
  class-A fix, and costs $0 of oracle.**
