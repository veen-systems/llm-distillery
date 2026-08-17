---
name: project_session_2026_08_17
description: Short session — evaluated lyceum.technology (EU GPU cloud) for us; filed #124 (self-hosted oracle); no code, no measurement, two self-corrections
metadata:
  type: project
---

# Session 2026-08-17 — one question, one issue, no code

**Scope, stated up front so nothing is read into it: no code changed, no measurement made,
no spend, nothing deployed.** The session answered one owner question and turned it into a
backlog issue. Everything quantitative below is marked estimated or verified accordingly.

## The question

Owner: *"is lyceum.technoly something for us?"* — [lyceum.technology](https://lyceum.technology/),
a Berlin-based EU-sovereign GPU cloud (H100 SXM $2.79/hr, A100 SXM $1.59/hr, per-second
billing, GDPR/EU residency). Then, narrowing: *"but indeed for an oracle?"*

**Answer given: no for training, marginal-on-price for an oracle, and the price is not the
point.** Owner ruling: *"those are important experiments, but not right now. maybe an
issue?"* → filed as **#124**, P3-low.

## The finding that actually matters

⭐ **The option was marketed on the axis where it loses and the axis that matters was in
our own compliance doc.** Priced as GPU rental it is a wash at best: a v5-class 8K-article
retrain is prefill-dominated (~64M in : ~9.6M out, ~6.7:1), break-even vs Gemini Batch's
$14.40 is ~5.2 H100-hours, and the estimate is 70B fp8 ≈ 4.5–7 hrs ($12–20) — i.e.
**renting saves nothing at the size that would justify renting, and only wins at sizes we
nearly run for free on b650**. The real case is not a number at all:

1. **EU residency for full article text**, which closes the still-open carve-out in
   `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — the oracle ships full bodies
   to Gemini/DeepSeek.
2. **Independence from two dated vendor forcing functions** — AI Studio Postpay→Prepay by
   **2026-10-12** or the Gemini API is interrupted; the DeepSeek hike of **2026-08-16**.
3. **Model sizes past b650's 24 GB ceiling.**

⚠️ The cost table is **estimated**, wide bars (MFU assumption), operator time uncounted.
Per [[feedback-nothing-verifies-an-estimate]] it was presented as such and the
recommendation was deliberately built so it does **not** depend on the arithmetic being
right — the conclusion holds under either end of the range.

## Two code facts, verified by reading source (not inferred from config)

- `scripts/score_ollama_oracle.py` **already works** — byte-for-byte prompt parity with
  `ground_truth/batch_scorer.py` and `validate_deepseek_oracle.py`, scores the frozen
  522-article cd v5 set, `qwen3:14b` / `phi4:14b` already run through it. Host is one
  hardcoded constant, `OLLAMA_HOST = "http://gpu-server:11434"`.
- ⛔ **The canonical oracle cannot be retargeted today.** `batch_scorer.py` accepts only
  `claude/gemini/gemini-pro/gemini-flash/gpt4` and builds `openai.OpenAI(api_key=...)` with
  **no `base_url` anywhere in `ground_truth/*.py`**. Also: **DeepSeek has no backend there
  at all** — every DeepSeek call site is under
  `filters/common/obituary_detector/validation/`, not in the filter oracle path. Anyone
  reading "cd v5 was DeepSeek-oracled" and expecting a `--llm deepseek` flag will not find
  one.

## The free path that fell out of it

⭐ **#124 step 1 is the evidence #109 Arm B is blocked on, and it costs nothing.** Arm B's
gap #1 is that the judge model is never named, and the obvious default (Gemini Flash) is
the model that *made* `investment_risk v6`'s labels. But qwen3:14b and phi4:14b scores on
the frozen 522-article set **already exist on disk** alongside Gemini's and DeepSeek's.
Comparing them is $0, no new hardware, no new sample. Posted to #109; recorded in the TODO
Arm B row. ⚠️ It does **not** discharge Arm B's planted-error gate — a 14B judge being fine
on full-length cd v5 content says nothing about it at 163 chars.

## Two self-corrections

1. ⛔ **I raised cross-box parity as an argument against renting, then withdrew it.** Bit-level
   box determinism ([[b650-gpu]], `scripts/verification/box_parity.py`) governs **student
   scoring**, where a verdict flip at an op-point is a production defect. Oracle *labelling*
   carries a far larger intrinsic decoder noise floor (ν = 0.436 / 0.687), so an ephemeral
   rented box is an acceptable labelling instrument. The objection was real but pointed at
   the wrong path. **Recorded as a trap in `oracle-pricing-scheduling.md` and in #124 so it
   is not re-imported.** Note this is the *inverse* of the recorded gotcha *conceding a
   correct conclusion because a neighbouring sentence was refuted* — here the withdrawal
   was right, and the tell was that the objection's premise (a verdict flip matters) is not
   a property of the oracle path.
2. ⛔ **`memory/oracle-pricing-scheduling.md` claimed "#109 Arm B names Qwen3:14b +
   Phi4:14b". It does not** — #109's body names no judge model, which *is* its blocking
   gap. The names come from the cd v5 precedent. A memory line that read as a citation was
   a gloss. Fixed.

## What changed on disk

- `docs/TODO.md` — #124 recorded in the top block as **deliberately not next**; #109 Arm B
  row annotated with the free path.
- `memory/oracle-pricing-scheduling.md` — correction above, plus a new
  § *The third option: a self-hosted oracle (#124)*.
- GitHub: **#124 created**; comments on **#109** and **#103**.
- Committed separately: the previous session's uncommitted board-count removal in
  `memory/MEMORY.md` + `memory/cross-repo-prioritization.md`.

## Next session

**Unchanged: start at the 79.3%.** #124 is P3-low and must not displace it. See the
`docs/TODO.md` top block.
