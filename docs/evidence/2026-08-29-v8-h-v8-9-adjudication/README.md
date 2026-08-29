# H-V8-9 — the rows the reorder moves across the op-point, adjudicated one by one

**2026-08-29. Spend $0.0208** (27 DeepSeek calls in step 2, 0 errors). **No model, no
threshold, no probe, nothing in `filters/` changed, nothing deployed.**
**Step 1** re-reads labels the Phase A k=3 run already bought
(`docs/evidence/2026-08-29-v8-phase-a-k3/`, $0.867) — no calls.
**Step 2** scores the three §5b no-regression articles under both v8 arms and the v7 prompt.

## Headline

⚠️ **One line: only FOUR of the twelve crossings are stable in both arms, and on those the
reorder is right three times — it drops a 2060 projection study, an ODA funding plan and a
mentorship guidebook, and its one stable ADDITION (the WestJet settlement) I judge a false
positive, arguably.** Two more crossings are
produced by a *single* within-arm gate flip inside the k=3 mean (#135, not a property of the
arm), and the remaining six are magnitude drift between arms that agree on `in_scope`.

✅ **Step 2 (below, $0.02) closes the hole step 1 could not reach: neither §5b hazard is
suppressed by the reorder** — the recovery narrative clears the op-point under both arms, and on
the transitional-justice row the reordered prompt scores **highest of the three prompts tested**.
⛔ **The third no-regression row fails its assertion under v7 as well**, which is a defect in
acceptance criterion 2, not in v8.

⛔ **This is an adjudication by the assistant against the v8 prompt's own STEP 1 and §5, not a
ground-truth panel and not an owner ruling.** H-V8-9 is *"the owner's decision dressed as a
hypothesis"*; this document is evidence for that decision, not the decision.

## Population — and it is the pipeline's, not a hand-built one

k=3 mean per arm, op-point **4.5 imported** from `filters/uplifting/v7/base_scorer.py`
(never copied — the rule that NM#161 and NM#205 exist for). A row "crosses" when the two arms
land on opposite sides of the op-point at k=3.

| | A (reordered) | B (as-is) |
|---|---|---|
| rows above the op-point, k=3 | **15** | **23** |

⭐ **This reconciles exactly with §3 of the published `results.txt`** — arm A: 8 (R) + 7 (B) = 15;
arm B: 11 (R) + 12 (B) = 23 — so the crossing set is derived from the same numbers already
reviewed, not re-derived by hand. **10 dropped, 2 added, net −8 (23 → 15, −34.8%).**

⛔ **12/200 is NOT a production crossing rate.** The cohort is design-weighted (150 R
production-mix + 50 B boundary, the boundary stratum ~4.4× oversampled); the published per-pair
rates in §4 are the quantity with an interval. Do not carry 12/200 anywhere.

## The three kinds of crossing, and only one of them is stable

| id | str | A k=3 | B k=3 | A verdicts (3 runs) | B verdicts (3 runs) |
|---|---|---|---|---|---|
| `italian_qualenergia_9776a593411a` | R | 0.517 | 4.883 | out/out/out | in/in/in |
| `korean_yonhap_kr_4bdf936317d3` | R | 0.750 | 4.683 | out/out/out | in/in/in |
| `gifted_davidson_gifted_8f9df075bd7b` | B | 0.800 | 4.517 | out/out/out | in/in/in |
| `positive_news_frontiers_..._4274585d688e` | B | 3.067 | 4.667 | out/in/in | in/in/in |
| `southeast_asian_cna_sg_cc65ac33d31b` | R | 4.050 | 5.083 | in/out/in | in/in/in |
| `arabic_ammonnews_en_ae36010efd70` | B | 4.217 | 4.950 | in/in/in | in/in/in |
| `korean_hankyung_4512142f32e3` | R | 4.450 | 5.100 | in/in/in | in/in/in |
| `dutch_news_nos_algemeen_da99e440d0af` | B | 4.267 | 4.533 | in/in/in | in/in/in |
| `southeast_asian_khaosod_en_1f663b3e79f6` | B | 4.433 | 4.650 | in/in/in | in/in/in |
| `global_news_spiegel_1822ab53217e` | B | 4.333 | 4.517 | in/in/in | in/in/in |
| `japanese_mainichi_jp_e8744b88eb34` (**added**) | B | 4.633 | 4.400 | in/in/in | in/in/in |
| `canadian_globe_mail_a5fec9b7be28` (**added**) | R | 4.733 | 0.850 | in/in/in | resp/resp/resp |

Three classes, and they do not carry equal weight:

- **Class 1 — stable gate change (4 rows):** every run in each arm agrees with its own arm, and
  the arms disagree. `italian_qualenergia`, `korean_yonhap_kr`, `gifted_davidson_gifted`
  (A out ×3 vs B in ×3) and `canadian_globe_mail` (A in ×3 vs B `response_to_harm` ×3).
  **These are the only crossings that are a property of the prompt rather than of a run.**
- **Class 2 — one coin toss inside the k=3 mean (2 rows):** `positive_news_frontiers` (A
  0.45/4.70/4.05) and `southeast_asian_cna_sg` (A 5.55/1.00/5.60). The arms' *majority* verdicts
  agree; a single `out_of_scope` run drags the mean across the line. ⛔ This is #135's step
  function, not the reorder — with a different draw these rows do not cross.
- **Class 3 — magnitude drift (6 rows):** all six runs `in_scope` in both arms; the reorder
  simply scores lower (once higher). Five drops of **0.18–0.73** and one add of **+0.23**.

## Adjudication — the three stable drops, and the two coin-toss drops

Read against the v8 prompt's STEP 1 (`prompt-candidate.md`), not against an intuition of
"uplifting". Every one of these was scored `in_scope` by the as-is arm on all three runs.

1. **`italian_qualenergia` — "Towards an equitable future of global photovoltaic waste
   recycling" (456 chars).** A *Nature* study projecting that by **2060** the world *could*
   accumulate 297–402 Mt of end-of-life modules and this *could* generate $529–936bn.
   ⛔ §5 first bullet, **speculation without outcomes**. The as-is arm scored
   `human_wellbeing_impact` **6.0** and its own evidence quote is the conditional —
   *"potrebbe generare benefici"*. **Reorder correct, as-is wrong.**
2. **`korean_yonhap_kr` — Japan's foreign ministry will fund joint AI research with ASEAN
   universities (¥4M per study, FY2026 ODA).** Funding allocated, research planned, nothing
   delivered. ⛔ **"Money committed is not a protection established"** (owner ruling 2026-08-23),
   which the prompt says to apply *before any other test*. As-is scored it 4.68 with
   `social_cohesion_impact` **6.0** for the funding decision itself.
   **Reorder correct, as-is wrong.**
3. **`gifted_davidson_gifted` — "Mentorships: Questions & Answers" (6,243 chars).** An extract
   from a guidebook: what a mentorship is, how to find one, what to do when it fails. Citations
   from 1981–1994. ⛔ §5, **professional knowledge sharing**, and it is the #125 / class-B
   academic-register defect in its purest form. No person, no event, no outcome.
   **Reorder correct, as-is wrong.** *(Note: the as-is arm's three scores — 4.55/4.35/4.65 —
   straddle 4.5 on their own, so this row also surfaces or not by coin toss under as-is.)*
4. **(class 2) `positive_news_frontiers_sustainable_food_systems` — a Frontiers abstract
   applying MMQR to 2000–2023 panel data for four South Asian economies.** ⛔ Class B again;
   the "findings" are regression coefficients and the recommendations are *"allocating capital"*
   and *"catalyzing innovation"*. The drop is **editorially right and mechanically fragile**:
   arm A returned `out_of_scope` on one run of three, and that single run is what carries the
   k=3 mean below 4.5. ⚠️ **Do not count this as evidence about the reorder** — count it as
   evidence about #135.
5. **(class 2) `southeast_asian_cna_sg` — the NDR childcare-leave reimbursement, with employer
   reaction.** Same shape: one `out_of_scope` run out of three (5.55 / **1.00** / 5.60). The
   article is an announcement plus *"manpower concerns remain"*, so a low score is defensible —
   but nothing here is a stable property of the reordered prompt.

## Adjudication — the one stable addition, and it goes the other way

**`canadian_globe_mail` — "WestJet flight attendants' harassment suit settled for $4.5-million".**
The reordered arm calls this `in_scope` on all three runs (4.73); the as-is arm calls it
`response_to_harm` on all three (0.85).

⚠️ **This one is genuinely arguable, and the honest reading is that both arms have a case.**
FOR the reorder: the prompt's §1 guard names *"compensation was paid"* and *"a conviction was
handed down"* as in-scope occasions, and a **court-approved** settlement covering **3,400**
named women is a completed legal outcome — which is what the reordered arm scored
(`justice_rights_impact` **7.0**, `benefit_distribution` **7.0**, `change_durability` 6.0).
AGAINST: the compensation has **not** been paid — *"An online claims portal is being prepared
and those who submit valid claims could receive roughly $470"* — there is no admission of
liability, the lead plaintiff calls the outcome *"a gross feeling"*, and the assault allegation
is recounted at length in the body a reader would meet.

**My call is AGAINST the reorder here, and it is a judgement under ADR-023, not a rule
violation**: a harm-dominated text landing in a *human thriving* feed is the error that costs a
reader. ⚠️ **A reader of this document should know it could go the other way** — which is why
the stable record below is written as *3 of 4 on my reading*, and why this row is the first
thing to put in front of the owner.

⭐ **So the reorder is not uniformly stricter at the gate** — it is *differently* strict: three
stable category exclusions gained (four if the coin-toss Frontiers row is counted), one
harm-dominant story admitted.

## Adjudication — the six magnitude drifts

Both arms `in_scope` on every run; the reorder just scores lower (or, once, higher).

| row | drop | reading |
|---|---|---|
| `arabic_ammonnews` professional-licensing law passed | −0.73 | a law **enacted** that lets experienced workers license without exams — a real if bureaucratic benefit. **Marginal loss.** |
| `korean_hankyung` Seoul identifies 540 independence activists, honours **applied for** | −0.65 | ⚠️ the §5b-adjacent shape: recognition/memory work. But the honour is *applied for, decision pending* — the announcement-vs-outcome boundary, not the transitional-justice guard. **Defensible drop, flag it.** |
| `global_news_spiegel` collectively-agreed wages *forecast* to beat inflation | −0.18 | a WSI **projection** ("dürften", "prognostiziert"). §5 speculation. **Defensible drop** — though both arms call it in_scope, so neither applies the rule. |
| `southeast_asian_khaosod` Thai children learning Khon at a temple, free classes | −0.22 | a real, ongoing, delivered community practice. **True positive lost.** (419-char stub.) |
| `dutch_news_nos_algemeen` 200 years of Feijenoord, residents' stories, volunteers | −0.27 | a genuine community/belonging story. **True positive lost** (arguably a `belonging` row). |
| `japanese_mainichi` national coach visits Kumamoto quake area, ~500 children | **+0.23** | delivered, human, specific. **True positive gained.** |

## Verdict

**Under ADR-023 the trade in this cohort is the one the ADR says to take, and it is smaller
than the raw −8 suggests.** Stably, the reorder removes **three** unambiguous false positives —
a 2060 projection, an ODA funding plan, a how-to guidebook — and admits **one** (WestJet):
**net −2 reader-facing false positives.** Two further drops (the Frontiers abstract, the NDR
announcement) are editorially right but are carried by a single coin-toss run each, so they
belong to #135, not to the reorder. Against that it costs **two, at most three, true
positives** (Khon classes, Feijenoord, and arguably the Seoul recognition row), all three of
which landed within **0.24** of the op-point under the reorder — rows that #95's 0.16 band and
#135's step function already move across the line between identical runs.

⚠️ **The direction is right and the margin is thin.** Three stable removals against one stable
admission, on n=12 crossings from a 200-row design-weighted cohort, is not a mandate; it is one
of the two things a decision needs. ✅ **The other — the no-regression check — is step 2 below,
and it also comes out in the reorder's favour.**

⛔ **What this does NOT establish, and none of it is repairable by re-reading the same labels:**

- **No ground truth was consulted.** The adjudicator is the assistant, applying the v8 prompt's
  own rules. `feedback-oracle-not-ground-truth` applies to *both* arms; this compares each arm
  against the prompt, which is a consistency check, not an accuracy measurement.
- **Neither §5b hazard was triggered by either arm in this cohort** — and that was a **negative
  from an instrument that contained no such row to begin with**: the three no-regression
  articles are not in this 200-row draw, so this cohort *could not* have produced that positive.
  ✅ **Closed by step 2 below**, which scored them directly — but the caveat stands as written
  for anyone reading step 1 alone.
- **n=12, of which 4 are stable in both arms.** A 3-of-4 record has a binomial interval so wide
  it excludes nothing, and two of the twelve are #135 coin tosses that would not recur.
- **Three rows are truncated stubs** (329 / 419 / 456 chars). The *label* question is about the
  stub, which is what the oracle saw; the *editorial* question is about the article, and §5b's
  method rule says excerpts are not sufficient for that one.
- **The cohort carries the Phase A design weighting.** Boundary rows are ~4.4× oversampled;
  nothing here is a production rate.

## Step 2 — the no-regression set, actually scored (2026-08-29, **$0.0208**, 27 calls, 0 errors)

The hole above is now filled. All three §5b rows scored under **both v8 arms and the v7 prompt**,
k=3 each, **one judge** (`deepseek-chat`) — the v7 arm exists because two of the three assertions
are relative, and the Unifesp row's says *"the same prompt family and the same judge"*. Full
article text in every case (13,107 / 4,761 / 1,896 chars), so §5b's *"excerpts are not
sufficient"* rule is satisfied. Raw runs in [`no_regression_runs/`](no_regression_runs/),
output in [`no_regression_results.txt`](no_regression_results.txt).

| row | guard | v8 reordered | v8 as-is | v7 prompt | assertion | verdict |
|---|---|---|---|---|---|---|
| Rappler, *"The silent crisis on our plates"* | recovery narratives | **4.900** | **5.350** | 4.983 | `raw > 4.5` | ✅ **PASS both arms** (every individual run above 4.5 too) |
| Unifesp, DOI-Codi forensic work | transitional justice | **4.367** | 3.983 | 2.950 | delta: v8 must not score it **lower** than v7, same judge | ✅ **PASS both arms** — reordered **+1.417**, as-is **+1.033** |
| Rwanda–EU $46M agricultural financing | lens overlap (ADR-015) | 0.817 | 0.817 | **1.600** | `raw > 4.5` | ⛔ **FAILS under all three, v7 included** |

⭐⭐ **Neither §5b hazard is suppressed by the reorder — and on the transitional-justice row the
reordered prompt is the BEST of the three.** That is the check step 1 could not make, and it
comes out in the reorder's favour: `in_scope` on 3/3 runs in both v8 arms, scoring **+1.42**
above the v7 prompt under the same judge.

⛔⛔ **But the third row exposes a defect in acceptance criterion 2 itself, and it is not v8's.**
The Rwanda row's `assertion_basis` says in the file: *"Observed raw NOT recorded — it was
REJECTED as adverse, so no observed block was written. Score it under v7 to establish the
baseline before asserting."* **That baseline is now established: 1.600 under v7's own prompt,
same judge — 2.9 points below the op-point it is asserted to clear.** The row cannot detect a
regression, because there is no baseline above the line to regress from. Criterion 2 is
**BLOCKING**, so as written it would fail v8 for a defect that predates v8.

⚠️ **And the reason is a collision between two owner rulings, which is the owner's to resolve:**
- **§5b (2026-08-23)** keeps the row as *"a genuine solutions story that may legitimately also be
  uplifting"* — lens overlap working as designed (ADR-015).
- **The money-committed ruling (2026-08-23, same day)** says *"funding secured, mobilised,
  pledged or allocated improves nobody's circumstances yet"* — and the headline is literally
  *"46 millions de dollars **mobilisés** auprès de l'UE"*.

Under the second ruling, **0.817 is the v8 prompt working exactly as instructed.** One of the
two has to give: either the row leaves the no-regression set, or its assertion becomes a delta
(as the Unifesp row's did on 2026-08-23 — that correction was made for one row and not for this
one). ⛔ **Do not "fix" this by softening the money-committed rule** — three of the four
class-1 crossings in step 1 depend on it.

### Two side-findings worth keeping

- **The judge matters more than the prompt on the Unifesp row.** The stored v7-prompt baselines
  are **1.883** (`qwen2.5:14b`) and **0.767** (`qwen3:14b`); the same prompt under
  `deepseek-chat` gives **2.950**. The spread between judges (2.2) is larger than the v8-vs-v7
  delta being tested (1.4) — which is why that assertion names the judge, and why it must keep
  naming it.
- **The v7 prompt has no scope binary at all** — `scope_verdict` comes back `__absent__` on all
  nine v7 rows (the scorer's sentinel, not a missing field). #135's step function is a
  **v8-only** property, introduced with the gate. Whatever is decided about the reorder, k≥3 is
  a v8 requirement and was not one for v7.

⚠️ **The Rappler row's stored `observed` is 6.4864** — that is the **deployed student model** in
production, not an oracle score. The 4.90/5.35/4.98 here are oracle scores under three prompts.
Do not read the difference as drift; they are different scorers
(`feedback-oracle-not-ground-truth`).

## Reproducing

```bash
python3 docs/evidence/2026-08-29-v8-h-v8-9-adjudication/enumerate_crossings.py <scratch-dir>
python3 docs/evidence/2026-08-29-v8-h-v8-9-adjudication/crossing_table.py     # scratch path is hardcoded
python3 docs/evidence/2026-08-29-v8-h-v8-9-adjudication/dump_rows.py <id> ... # scratch path is hardcoded
```

Committed output: [`crossings.txt`](crossings.txt) — produced by the **committed** copies and
verified byte-identical to the scratch run that this document was written from
(`feedback-verified-artifact-is-the-shipped-one`).

⛔⛔ **PROVENANCE HAZARD: this repo keeps no `phaseA_cohort200.jsonl` and no run files.** The
cohort and the six `phaseA_{A,B}{1,2,3}.jsonl` (6.6 MB, 1,200 oracle labels, $0.867) exist
**ONLY in a previous session's `/tmp` scratchpad**
(`…/96c7f831-6b9e-443a-a955-658f6c98dec6/scratchpad/`). H-V8-3, H-V8-4, H-V8-5, H-V8-6 and this
document all rest on them, and `/tmp` does not survive a reboot. **Deciding where they live is
an owner call** (they are full article text, so the TDM register in
`docs/decisions/2026-08-05-tdm-opt-out-training-data.md` is in scope) — but they should not stay
where they are.
