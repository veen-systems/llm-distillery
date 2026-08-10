# Candidates — uplifting v7 oracle batch, 2026-08-09

> ### ⚠ Superseded in part, 2026-08-10 — read the adjudication first
>
> **This note's central reading is wrong.** It says the batch shows *"uplifting
> is absorbing solutions-lens material"* and that ADR-015 lens overlap *"decides
> most of the batch"*. It does not. `content_type: solutions_story` is the
> oracle's **residual bucket** — the value left when none of the prompt's five
> penalty checks applies — and it is the tag the prompt puts on its **own 7.3/10
> and 5.8/10 good examples**. The overlap defence covers **2 rows, not 21**; the
> dominant class is academic-abstract register (9 of 21).
> [`2026-08-10-uplifting-oracle-batch-adjudication.md`](2026-08-10-uplifting-oracle-batch-adjudication.md).
>
> **What still stands:** how the batch was built, the band/precision table, and
> all three caveats in "Three things to establish" — including caveat 3, which
> this session's work bore out.

**These are NOT adverse rows. They are unadjudicated candidates**, in
[`candidates/2026-08-09-uplifting-oracle-batch.jsonl`](candidates/2026-08-09-uplifting-oracle-batch.jsonl),
and they must not be fed to a training run in this state.

The precedent is `2026-08-05-ovr-flag-adjudication.md` in this directory, which
excluded one of five staged rows and recorded why: *"Labelling this adverse
teaches the scorer to suppress a category."* Thirty-four rows selected by an
oracle deserve the same per-row judgement, not a bulk import. `label` is set to
`CANDIDATE_UNADJUDICATED` so a careless glob cannot mistake them for evidence.

## How they were selected

First active-learning batch built under **ADR-023** (a false positive costs a
reader; a false negative costs nothing visible), so it samples **above** the
operating point — what reaches readers — not below it.

170 production rows over 6 cycles, stratified by margin above uplifting's 4.0
gate, oracle-graded with **gemini-flash** (uplifting's own oracle; DeepSeek
would not be comparable to a Gemini-fitted calibration). 144 came back. These
34 are the ones that **surfaced to readers and the oracle scored below 4.0**.

## What the batch measured

| band | population / 6 cycles | graded | oracle ≥4.0 | precision |
|---|---|---|---|---|
| ≥5.5 | 315 | 29 | 29/29 | **1.000** |
| 4.5–5.5 | 555 | 44 | 31/44 | 0.705 |
| **4.0–4.5** | 323 | 49 | 28/49 | **0.571** |
| 3.5–4.0 (below gate) | 449 | 22 | 7/22 | 0.318 |

**≈50 off-lens articles per cycle reach readers, of ≈199** — ~25%. Junk
concentrates exactly at the margin, which is the empirical case for ADR-023's
sampling rule.

By the oracle's own `content_type`, the 34 are: **`solutions_story` 21**,
`doom_framed` 7, `community_building` 3, `speculation` 2, `politics` 1. The
dominant failure is not randomness — **uplifting is absorbing solutions-lens
material**, which has its own filter. `doom_framed` is the uglier group (a
heatwave power cut, medicine waste, dog-walking fines).

## Three things to establish before adjudicating

1. **The sample has a known non-random hole.** 26 of 170 were never graded —
   the oracle prefilter's 300-char floor rejected them, median length 128 —
   and 11 of those 26 sit in the *marginal* band where the junk is. Every
   precision figure above is computed on the **long** articles in its band. The
   direction of the bias is unsigned; short bodies are where stubs and
   truncation live, so 25% is more likely an underestimate.
2. **`solutions_story` in an uplifting feed may not be adverse at all.**
   ADR-015 says lenses are overlapping perspectives and overlap is correct. A
   genuine solutions story that is also uplifting belongs in both. Labelling
   these 21 adverse could teach the scorer to suppress solutions content
   wholesale — precisely the failure the 2026-08-05 note refused. This is the
   adjudication that decides most of the batch.
3. **The oracle cannot see the errors it shares.** Reader flags pulled the same
   day found articles scoring **6.85, 6.49, 6.09** in uplifting that readers
   called "not constructive" — inside the band this batch graded 29/29 perfect.
   An oracle trained on the same editorial line as the student is blind to a
   shared blind spot. **Oracle-only active learning cannot fix that class**;
   reader flags are an independent label source and should be treated as one.

## Reproduce

    # sample (on sadalsuud) — bands are in scratchpad sample_upl.py
    # grade:
    PYTHONPATH=. .venv/bin/python -m ground_truth.batch_scorer \
      --filter filters/uplifting/v7 --source <sample>.jsonl \
      --output-dir <out> --llm gemini-flash --batch-size 50
