# Pre-registration — Thriving harm panel (2026-09-08)

⛔ **Written and committed BEFORE any judge call was made.** The point of this file is that a
prediction which turns out wrong stays on the record as wrong. `EXP-030`'s band-share prediction
failed (predicted 46–70%, observed 30.8%) and that failure is more useful than the successes.

## The question

Owner, verbatim: *"we optimised for precision. Reason being that very adverse articles were
presented as thriving in the past."* That is llm-distillery#91 — `uplifting v7` ranked a
child-trafficking investigation in its **top 6 of 3,530**.

Every precision number this project holds asks **"is this on-lens"**. None asks **"would a reader
be harmed seeing this in Thriving"**. Those are different questions, and the second is the one
the ruling turns on.

## Design

- **Population: display-eligible rows**, not rows above the op-point. ovr.news draws the tab with
  `getArticlesForBuild(filter, 4.5, …)` filtering on `afs.weighted_average >= 4.5`
  (`ovr.news/src/lib/db-articles.ts:290`, threshold `src/lib/config.ts:477`). Sets over the same
  four cycles / 15,372 articles: **v7-only 523 · both 131 · v8-only 37**.
- **Panel n=137**, seeded (`random.Random(20260908)`): 60 v7-only, 40 both, **all 37** v8-only.
- **Blind.** The judge sees title and body only — never the stratum, never either lens's score.
- **Rubric belongs to NEITHER lens.** Built from the reader-facing tab copy in
  `ovr.news/src/i18n/translations.ts`. Grading v7 on v8's rubric is the confound the NexusMind
  session hit and flagged (their v7 0.492 vs v8 0.825, adjusted 0.603).
- **Both oracle families judge, because each lens has one.** `uplifting v7`'s oracle is
  **Gemini Flash** (`filters/uplifting/v7/config.yaml:42`); `human_thriving v8`'s is **DeepSeek**
  (`filters/human_thriving/v8/config.yaml:63`). A judge from one family flatters its own lens, so
  **each lens's conservative number is the one from the OPPOSING family's judge.**
- **k=3, majority vote** on the primary arm (#135: a single pass is a coin toss near a boundary).

## Verdicts

`harmful` (dominant subject is a harm) · `misleading` (nothing improved yet) · `weak` (real but
thin) · `fits` (delivered improvement for identifiable people).

## Predictions, stated before looking

**Primary — the #91 rate.** `harmful` share by stratum:

| stratum | predicted `harmful` | reasoning |
|---|---|---|
| v8-only (n=37) | **0–5%** (0–2 rows) | `EXP-029` found 2 of 62 live v8 passers off-lens |
| both (n=40) | **0–8%** (0–3 rows) | shared by both lenses; v7's known defects are elsewhere |
| v7-only (n=60) | **5–20%** (3–12 rows) | #91 is this shape; #125 shows v7's oracle is permissive |

**The load-bearing comparison: I predict v7-only's `harmful` rate EXCEEDS v8-only's.** ⛔ If it
does not, the main safety argument for the cutover fails, and the ~74% supply cut buys nothing on
the dimension the owner actually named.

**Secondary — the #125 shape.** `misleading` should be much higher in v7-only than v8-only:
predicted **30–50%** v7-only vs **5–20%** v8-only, because #125 measured v7's oracle rating
research abstracts on-lens at 55.2% vs 30.6%, and a research finding delivers nothing to people yet.

**`fits` share:** v8-only **50–75%**, both **50–75%**, v7-only **20–40%**.

## What would make this uninformative

- **n=37 is the whole v8-only population, not a sample** — so its interval is the only one that
  is not a sampling question, and it is still small. A difference of 1–2 rows will not be
  distinguishable. Predicted in advance: a Fisher test on `harmful` v7-only vs v8-only is
  **unlikely to reach p < 0.05** unless the v7-only rate is at the top of my range.
- Both judges are LLMs of the two families that TRAINED these lenses. An
  authorship-independent judge is still blocked (`openai_api_key` → HTTP 401, 2026-09-08).
- Four cycles in an 11h38m window; c1 is the backlog cycle.
- The panel is drawn from what each lens surfaces. It measures **precision-shaped** quantities
  only. It cannot say what either lens MISSES.
