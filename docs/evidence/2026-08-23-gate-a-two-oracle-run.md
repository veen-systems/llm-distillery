# Gate A, two oracles, v7 vs v8 — the prompt works on class B, not yet on class A

**2026-08-23. Spend: $0.4711** (DeepSeek $0.1771 off-peak, Gemini 2.5 Flash $0.2940).
Nothing deployed, no model trained.

## Design

15 rows × k=3 × 2 prompts × 2 oracles = 180 calls, 0 errors after the key fix below.

- **Prompt arms:** `filters/uplifting/v7/prompt-compressed.md` (control) vs
  `filters/human_thriving/v8/prompt-candidate.md` (Phase A steps 1 + 2b spliced into v7).
- **Rows:** 9 class A + 3 class B + 3 no-regression, **full text, hydrated from `ovr.db`**.
  ⛔ **All 18 adverse rows on disk are 300-char excerpts** (originals 620–28,905 chars);
  scoring those would have tested ledes, not articles, and class A turns on the *dominant
  subject*. **6 of 9 class-B rows could not be hydrated** — aged out of `ovr.db` and
  `filtered/` alike — so class B here is 3 of 9. **Class A is complete at 9 of 9.**
- Weighted average and gatekeeper computed with `uplifting v7`'s weights (v8 changes no
  weights; re-weighting is closed, plan §2).

## Result

| | DeepSeek v7 → v8 | Gemini v7 → v8 |
|---|---|---|
| **Class A** (blocking, bar < 3.85) | 4/9 → **7/9** | 4/9 → **6/9** |
| **Class B** (reported, bar < 3.85) | 1/3 → **3/3** | 1/3 → **3/3** |
| **No-regression** (blocking) | 1/3 → 1/3 | 2/3 → 2/3 |

### ✅ Class B is fixed, emphatically, on both oracles

The two owner-flagged rows of 2026-08-22 collapse:

| row | DeepSeek | Gemini |
|---|---|---|
| Dawn, "Curing the cause" (op-ed) | 5.98 → **3.00** | 7.36 → **1.60** |
| TSA, clinician appointment | 4.63 → **2.53** | 5.53 → **0.00** |

`3.00` is the gatekeeper cap firing exactly as §1h predicted. **Step 2b works.**

### ⚠️ Class A improves a lot and still does not clear

Both oracles fail the same two rows, and they are the two worst:

| row | DeepSeek v8 | Gemini v8 |
|---|---|---|
| Celebrated at birth, pushed into sex work | **5.88** (−0.22) | **6.55** (−0.25) |
| Parents of baby girl killed at nursery | **4.03** (−3.03) | **6.90** (−0.25) |

⛔ **And the oracles disagree by 4.4 points on the single most reader-offensive row.**
*"Five men arrested for raping a minor"*: DeepSeek **7.05 → 3.00** (capped), Gemini
**7.23 → 7.43** (*rises*). The step-1 text names "individual arrest/sentencing" explicitly;
DeepSeek applies it, Gemini does not. **A prompt rule that one frontier oracle ignores is not
a shipped rule** — this decides the Phase B oracle choice, which the plan left open.

### ⛔ Criterion 2's bars are wrong — and **v7 proves it**

v7 *also* fails the no-regression set (1/3 DeepSeek, 2/3 Gemini). **A criterion the incumbent
fails is a broken criterion, not a failing candidate.** Read against bars that actually have
evidence behind them:

| row | real assertion | DeepSeek | Gemini | verdict |
|---|---|---|---|---|
| Rappler (recovery) | raw > 4.5 — the **only** row with a production baseline (6.4864) | 5.42 → 4.65 | 5.92 → 5.62 | ✅ passes both, but ⚠️ DeepSeek's 4.65 is **0.15 above the op-point inside a 0.543 spread** — indeterminate |
| Unifesp (transitional justice) | **delta**: v8 ≥ v7 | 3.57 → 4.33 (**+0.77**) | 4.88 → 5.02 (**+0.13**) | ✅ passes both — transitional justice is **not** suppressed |
| Rwanda (lens overlap) | raw > 4.5 — ⚠️ **a bar I invented from the op-point**; the row was *rejected* as adverse and never had an observed score | 1.53 → **3.00** | 3.70 → **3.00** | ⛔ **capped by v8 on both** |

## ⛔ The one real regression, and it is a question for the owner

**v8 caps the Rwanda row to exactly 3.00 on both oracles** — the gatekeeper. And v8 is
behaving *exactly as written*: "Rwanda mobilises $46M from the EU for agricultural
resilience" is **funding announced**, which step 2b Shape 2 ("a funding round … announced, not
delivered") catches by design.

So one of two things is true, and **it is not mine to decide**:

1. **The rule is right and §5b mis-adjudicated the row** — development financing with no
   delivery is an announcement, and the 2026-08-10 adjudication called it "a genuine solutions
   story" on lens-overlap grounds without applying the announcement test; or
2. **The rule over-reaches on development finance**, where mobilised funding is the reportable
   event and delivery is years away — in which case Shape 2 needs a carve-out.

⚠️ This is the same boundary as the open delivered-accountability question, from the other
side. Both are about **what counts as delivery**.

## Instrument notes

- ⛔ **The first Gemini run was garbage and looked like a run.** `gemini_api_key` is
  free-tier: **429 RESOURCE_EXHAUSTED**, 14/45 and 8/45 succeeded, and k=3 silently became
  k=1 on 8 articles. Caught only because the harness prints "N articles have fewer than k
  successful runs". Fixed by preferring `gemini_billing_api_key`, now the script's default
  with the free-tier fallback labelled. **Re-run: 45/45, 0 errors, both arms.**
- **DeepSeek: 90/90, 0 errors, both arms.** Run-to-run spread mean **0.543**, max 1.600 —
  *inside* the recorded 0.82/2.25 oracle floor, and 3× tighter than `qwen3:14b`.
- ⚠️ **The v8 prompt is 33% longer** (31,577 vs 23,662 chars), which is 28% more input tokens
  and therefore 28% more cost per labelling run. Not a blocker at these sums; it is a
  standing cost on every future retrain.

## What this does and does not settle

- ✅ **Step 2b (the gatekeeper) is validated on two oracles.** Ship it.
- ⚠️ **Step 1 is validated on one oracle and ignored by the other.** Not shippable as written.
- ⛔ **Nothing here touches the student.** §1f measured 2 of 3 class-A rows as the *student*
  disagreeing with all three oracles; these are oracle labels. Even a perfect prompt leaves
  that untouched, and **Phase B2 hard negatives remains the larger half of the class-A fix.**
- ⛔ **Class B's verdict rests on 3 of 9 rows**, because 6 could not be hydrated. Treat 3/3 as
  directional.
