# Belonging held-out screen measurement: pre-registration (2026-10-03)

*Written and committed BEFORE the draw, before any oracle call and before any judging. Approved by the owner
2026-10-03 (400 per band, ~$1.30 Gemini estimate at list price). START HERE item 0.3.*

## The question

On production rows nobody has read, **how well does Gemini Flash on the frozen rubric v2.2 find lived belonging, and
what does confirming its hits cost?** The 242-row calibration set cannot answer this: v2.1 and v2.2 were written from
its rows, so it is a DEV set.

## Frozen inputs

- **Rubric:** `../2026-10-02-belonging-adjudication/rubric_belonging_v2.md` = **v2.2**, sha256 prefix
  `d450b79510418cf7`. It is not edited until this measurement is reported; a change means a new held-out set.
- **Oracle prompt:** `oracle_scope_prompt.md` (unchanged), with the rubric filled in. `gemini-2.5-flash`,
  temperature 0, thinking budget 0, max 1,024 output tokens, JSON mime type, as in the calibration.
- **Judges:** `judge_instructions_v2.md` VERBATIM, Claude Opus 5.5 subagents, two blind passes on different
  shuffles with opaque ids. They see no oracle verdict, band, score or weight.

## Population and draw (`draw_heldout.py`, run on sadalsuud)

- **Population:** every distinct `stage2` belonging row in sadalsuud's retained `data/filtered/belonging/` files. The
  window is printed by the script and copied into the report.
- **Excluded:**
  - news.google.com rows and content under 300 characters
  - all 771 ids in `belonging_exclusions.py`
  - v1's train/val/test ids (7,370, fetched from b650)
  - exclusion runs before deduplication by id and `content_hash`
- **Bands,** on the student's raw score (the harvest plan's bands): `hi` ≥ 5.6, `mid` 4.0–5.6, `near` 2.5–4.0.
  Rows below 2.5 are outside the population, so **nothing here speaks for them**.
- **The draw:** 400 per band, seed 20261003. Every row carries its band's pool size and its design weight
  (pool / 400), as data.
- **Afterwards:** the 1,200 drawn ids are added to `belonging_exclusions.py`, so they can never enter training.

## Stage A: Gemini on all 1,200 rows

Each row's verdict, quote, reason, tokens, the served model and the prompt sha are recorded. Errors are retried,
never guessed.

## Stage B: the judges

- **Every row Gemini calls `in_scope`.**
- **Plus a random 50 of Gemini's non-in rows per band** (seed 20261004; `cannot_judge` rows count as non-in). These
  are the only window on what the screen misses.
- **Labels:**
  - `in` when both passes say in, `out` when both say out, `split` otherwise
  - `either_in` = at least one pass says in (the candidate confirm rule from the calibration, n=14)

## What gets reported, per band and weighted to the population

1. **The in-rate.** Positives are found among Gemini-ins plus the sampled outs; the sampled outs are weighted up by
   (band's Gemini-outs / 50). This sizes harvest round 1.
2. **Gemini's hit rate:** of its ins, the share that are `in` and the share that are `either_in`. This is the
   judging load per true positive.
3. **Gemini's recall:** weighted, as TP / (TP + estimated misses). With 0 misses observed in a band, the report gives
   the rule-of-three upper bound on that band's miss rate, never "recall 1.0".
4. **Specificity,** weighted. Precision and in-rate are base-rate dependent and are reported only beside their band's
   positive rate (ADR-023).
5. **Judge agreement:** A/B binary agreement and the number of splits.

## The owner check (closes the measurement)

**10 rows, drawn by seed 20261005:**
- 4 `in`
- 3 `split`
- 3 Gemini-in rows that are both-judges-out

The owner reads the title and opening. Claude adds a gloss only for non-English text, marked as one; the verdicts
stay hidden.

**Bar for using "either judge says in" as the confirm rule:**
- **no owner `out` among the 7 `in`/`split` rows,**
- **and no owner `in` among the 3 both-out rows.**

Unsure counts as neither. If the bar fails, the confirm rule goes back to the owner.

## Predictions (Claude's, before the draw)

| band | in-rate |
|---|---|
| `hi` | 3–8% |
| `mid` | 1–4% |
| `near` | 0–2% |

Gemini says in on roughly the in-rate plus 5–8 points in each band (calibration: 13 false ins of 212 outs on v2.1).
**Weighted recall:** 0.8–1.0, with an interval too wide to rank anything.

⚠️ **Claude predicts, draws, and runs the judges.** Every label is judge-relative except the owner's 10.
