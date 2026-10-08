# belonging candidate 2: plan (2026-10-08). APPROVED by the owner 2026-10-08: the ~$1.40 labels + build, and a 2× (2,400-drawn) fresh held-out set

**Why:** v1_adj1 failed the held-out gate (Δspec +0.047, CI [−0.015, +0.105]; `../2026-10-08-belonging-adj1-leak-check/README.md`
§ Run 3). On ovr.news's 40 published stories (EXP-028) it kept state commemoration and harm-led stories. Its only hard negatives
were `out_one_moment`. **Owner ruling (2026-10-08):** add hard negatives ONLY from `out_gift_official` and `out_harm_is_story`;
no new `out_one_moment` negatives; the rubric text is unchanged.

## 1. Training data: v1_adj1's build + 135 new hard negatives (~$1.40 est.)

- **Source, already judged ($0):** harvest r1's Gemini-in rows where BOTH blind judges gave the same out-class
  (`datasets/belonging_harvest_r1/positives_r1.jsonl`): **46 `out_gift_official` + 89 `out_harm_is_story` = 135**.
  0 of them are in v1_adj1's training data (measured). All are in v1's hi band (raw ≥ 5.6), i.e. v1's own live false positives.
  For contrast, rows where only ONE judge said so: 68 and 112. Those are NOT used (same rule as r1: both judges).
- **Labels:** exactly as r1's hard negatives. Gemini Flash, v1's prompt, k=3 on full text, mean per dimension, every dimension
  capped at 2.0. ~$1.40 est. (r1: 121 rows × 3 ≈ $1.25 est.; `batch_scorer` records no tokens, so it is not measured).
- **Build:** `build_adj1.py` → a `build_cand2.py` that adds an origin `harvest_hard_negative_c2`, with the same
  FMEA checks, the twin loop and the gate's `refuse_overlap` at the end.
- **No harvest round 2.** Recall was not the failure (k = 40/44); the ~$9.70 positive harvest is not needed for this question.
- **Training:** same flags as run 3 (`--epochs 6 --select-metric last`, seed 42). ⚠️ Seed band: run 2 → run 3 (2 negative rows
  dropped) moved val recall_medium 0.862 → 0.759. A single seed cannot separate a small effect from that band.

## 2. Pre-gate checks (all $0)

- **Leak check:** re-run `leak_check.py` (same 5,000 rows, same rule).
- **ovr's 40 (EXP-028), as a CHECK, not a gate:** pre-register now, before any score: candidate 2 should pass FEWER of the 27 weak
  stories than v1_adj1's 13, specifically fewer of the commemoration/harm titles listed in the leak-check README. The
  40 must never become training rows.
- **Proxy recall:** the 23 test-split harvest positives (v1_adj1 found 22).

## 3. A FRESH held-out set: the owner's sizing decision

The old set is spent. The new one reuses `draw_heldout.py` + `heldout.py` (Gemini v2.2 + two blind judges + an owner spot-check),
drawn AFTER excluding every id in the spent set, both builds, harvest r1, the easy negatives and the leak-check draw.

**Power (estimate, not measured):** the failed gate's 95% CI half-width was ~0.06 on 163 deciding negatives. If a candidate's
true Δspec is ~0.05, the lower bound clears 0 only about half the time at that size. Halving the width needs ~4× the
deciding negatives. ~2× gives a half-width of ~0.042.

| size | deciding negatives | cost (est.) | odds a true +0.05 passes (est.) |
|---|---|---|---|
| same as before (1,200 drawn) | ~163 | ~$9 + owner review | ~coin flip |
| 2× (2,400 drawn) | ~325 | ~$18 + owner review | better, not sure |

The pass rule (pass rule v2, GATE.md) stays as is, and only the size changes. Changing the RULE after a failure is not proposed.

## 4. Order

owner approves → label the 135 (~$1.40) → build + validate → train → calibrate → leak check, ovr-40 check, proxy recall
→ draw + judge the fresh held-out (owner reviews the spot-check) → gate (one shot).
The held-out draw can run while training runs. It uses no GPU.

## 5. Two variants (owner 2026-10-08, after "so now these gems will end up in belonging, right?")

The plan as first written keeps v1_adj1's 121 `out_one_moment` hard negatives, so candidate 2 would most likely still drop
single-person stories (v1_adj1 dropped 6 of ovr's 13 good ones). Owner: train BOTH, at $0 extra:
- **c2a** = v1_adj1 build + the 135 new hard negatives (keeps the 121)
- **c2b** = the same, WITHOUT the 121 `out_one_moment` hard negatives (neutral on single-person stories)

Compare them on the free checks (leak check, ovr's 40, proxy recall). The OWNER picks which goes to the gate. Only one is gated.

## 6. No owner spot-check for the fresh held-out set (owner 2026-10-08: "so tired of spot checking")

The rubric (v2.2), the judge instructions and the judge model are unchanged since two owner checks agreed with "both judges in"
(harvest r1: 10/10 in; first held-out: 3 in / 1 unsure / 0 out of 4). That is 0 owner-outs in 14. **Replaced by a tripwire:**
the fresh set's judge A/B binary agreement must lie in [0.90, 0.97] (seen: 0.918 harvest, 0.956 held-out), and its hi-band
both-in rate among Gemini-ins must lie in the first held-out's Wilson interval [0.29, 0.48]. Outside either → STOP and
bring the owner rows. NOT delegated to ovr.news: its panel is another LLM on a different construct (reader gladness, on the
headline), kept apart by agreement. Cannot catch: a subtle owner/judge disagreement that leaves both statistics unchanged.

## 7. The c2a/c2b pick: delegated to a pre-set rule on ovr's panel (owner 2026-10-08: "can you have ovr do the comparison?")

Fixed BEFORE any candidate-2 score was seen; amended the same hour on ovr.news's review (its points a–c), also before any score.
- **Disagreement set:** rows of the 5,000-row leak-check draw that exactly ONE of c2a/c2b flags (stage2, weighted_average ≥ 4.0).
  ovr.news rates them blind with its EXP-028 panel (3 LLM raters, publisher og:title + og:description; the variant is hidden).
  Stories without a usable card drop out, and ovr reports how many.
- **Two questions per story:** Q1 is the EXP-028 quality rating (1–3; weak = at least 2 of 3 raters give 1). Q2 is new: "Is this
  story about a group, community or shared practice, not one person? yes/no" (majority of 3).
- **The decision rests on Q1, paired:** d = weak share(c2b-only) − weak share(c2a-only), with a bootstrap 95% CI (10,000 resamples
  within each side, seed 20261013). **c2b goes to the gate UNLESS the CI lies entirely above 0** (c2b's extra stories clearly
  weaker). A tie goes to c2b: the owner's "no new single-person negatives" default, and c2b is the neutral variant.
- **Q2 is reported, not deciding.** It shows how many c2b-only stories are single-person: the owner's open fit/reach question,
  which a quality panel cannot answer (ovr's point a). The owner can veto on it.
- 27/40 = 0.675 (ovr's PUBLISHED Belonging weak share) is a reference line only: a different population (ovr's point b).
- A variant failing the leak check is out regardless. The free checks are reported beside the panel. **Ratings never become
  training labels** (unpublished stories; ovr keeps them under data/held-out/).

## 8. Results (2026-10-08): both variants, free checks, ovr's panel. **c2b goes to the gate**

Trained at `49d52a9`, `--select-metric last` (epoch 6), calibrated on val; b650 GPU. Measured:

| | v1 (live) | v1_adj1 (FAILED) | c2a | c2b |
|---|---|---|---|---|
| leak check (`leak_c2{a,b}.json`) | | NOT LEAKED | NOT LEAKED | NOT LEAKED |
| proxy recall, test-split harvest positives | 23/23 | 22/23 | 22/23 | 23/23 |
| ovr's 40 (EXP-028): weak stories still passed | 27/27 | 13/27 | 6/27 | 9/27 |
| ovr's 40: good stories kept | 13/13 | 7/13 | 7/13 | 9/13 |
| flags on the 5,000-row production draw | 109 | 42 | **8** | **25** |

**ovr's panel (ovr.news EXP-029, ovr `f40c016`; input sha256 `1c4857e259d6f420`):** 21 disagreement rows; 2 c2b_only dropped (no
card); rated c2a_only 2, c2b_only 17. d = 4/17 − 2/2 = **−0.765**, CI95 [−0.941, −0.529] (re-derived here from the per-story rows).
Not entirely above 0 → **c2b**. As stated before the ratings, n=2 on the c2a side made this near-automatic. Informative:
c2b_only weak 4/17 (0.235); no story got a 3 from any rater; Q2: 13/17 about a group. The 4 single-person ones are two
wedding human-interest items (weak), a restaurant profile and a farming-tech piece.

⚠️ **Volume (not gated; the owner's call at switch):** 25 vs v1's 109 flags on the draw ≈ a quarter. My extrapolation, not
measured: ovr's ~81/day published Belonging would fall to roughly 20/day.

**OWNER VETO (2026-10-08, after the panel result): gate c2a, not c2b.** The rule's pick was c2b; the owner exercised the veto
the rule reserved. Recorded as the owner's decision; no reason was given. c2a: 6/27 weak and 7/13 good on ovr's 40, 8 flags of 5,000.
Known risk, stated beforehand: c2a's low flag rate may miss the recall bar (k ≥ 45 of 63).

## 9. GATE on held-out set 2: c2a FAILED (2026-10-08). Set 2 is SPENT; v1 stays live

Full output: `../2026-10-08-belonging-heldout2/result_v1_c2a.txt`. Both orders identical in verdict (1/539 order flip for the candidate).
- **Recall: k = 43/63 < K_MIN 45 → FAIL.** None of the 20 missed positives is within ±0.16 of 4.0 (scores 1.47–3.56, most
  2.3–2.9), so batch noise (#95) is not the explanation: c2a is genuinely too strict. This is the risk stated before the veto.
- **Specificity: PASSES on its own.** Weighted Δspec +0.019, 95% CI [+0.003, +0.031] (forward; reversed +0.019 [+0.002, +0.030]);
  unweighted 0.951 vs v1@t* 0.718.
- Disputed rows (not deciding), unweighted spec, candidate @4.0 vs live v1 @4.0: out_gift_official 0.750 vs 0.050,
  out_harm_is_story 0.971 vs 0.147, out_one_moment 0.923 vs 0.231. So candidate 2 learned the targeted classes.

## 10. GATE on held-out set 3: **c2b PASSED** (2026-10-08). Set 3 is spent

Full output: `../2026-10-08-belonging-heldout3/result_v1_c2b.txt`. Owner approved gating c2b on set 3 after c2a's FAIL.
- **Recall: k = 76/83 ≥ K_MIN 59.** v1 matched at t* = 4.0317.
- **Specificity: weighted Δspec +0.350, 95% CI [+0.322, +0.376]**, identical in both orders; 0/585 order flips.
- ⚠️ **Read the size with its mechanism, not as population specificity.** The bands ARE v1's production raw (hi ≥ 5.6, mid
  4.0–5.6), and c2b's recall puts v1's matched threshold at ~4.03, so v1 passes almost every hi/mid row by construction
  (hi+mid weighted spec v1@t* 0.024). The +0.35 says: of the stories v1 lets through, c2b rejects most (hi+mid weighted 0.863) while
  keeping 76/83 positives. On set 2, c2a's lower recall put t* at 5.74, which is why its Δ was +0.019. Same rule; different t*.
- Not deciding: disputed rows, candidate vs live v1 @4.0 (unweighted spec): out_gift_official 0.706 vs 0.176, out_harm_is_story
  0.800 vs 0.150, out_one_moment 0.500 vs 0.250, out_other 0.391 vs 0.159.
- 22 of the candidate's judged rows lie within ±0.16 of 4.0 (#95, batch-composition noise), with 0 flips between orders.

**A PASS is not a switch.** Not measured by the gate, and the owner's call: volume (c2b flags 25 vs v1's 109 on the 5,000-row
draw); the normalized-score shift until a refit (ovr's ≥ 4.5 display gate, NexusMind's enrichment min_score, NexusMind NM#319);
and the deploy itself (RUNBOOK; diff before sync; the decision-0 sync is still pending).
