# v8-5 prompt test — pre-registration (written before any call)

**2026-09-24, 18:2x UTC (off-peak).** Candidate: `filters/human_thriving/v8/prompt-v8-5.md`, which is
`prompt-v8-4.md` plus ONE edit: the §5 *"Nothing has taken effect yet"* category also lists a law
passed but not yet in force, a permit/permission/approval for something not yet built, works
"to be built"/"set to open"/"planned", and a petition/demand/appeal/campaign.

⚠️ **The bar below is the ASSISTANT'S PROPOSAL.** The owner asked for the test to run
("run the test on v8-5") without setting numbers. Owner may tighten it; it may not be loosened
after the results are seen.

## Arms (DeepSeek `deepseek-chat`, i.e. V4.1 Flash since 2026-09-10 — #157)

| arm | prompt | input | k |
|---|---|---|---|
| G4 | v8-4 | `docs/evidence/2026-09-03-v8-1-gate/gate_input.jsonl` (13 rows) | 12 |
| G5 | v8-5 | same | 12 |
| F4 | v8-4 | `flip_input.jsonl` (the 12 EXP-029 flips, text from `filtered_20260907_180414.jsonl`) | 6 |
| F5 | v8-5 | same | 6 |

v8-4 is RE-RUN, not reused: the 2026-09-03 k=12 runs and EXP-029's k=6 were scored by V4, and
the alias moved to V4.1 on 2026-09-10. Comparing v8-5-on-V4.1 with v8-4-on-V4 would confound
prompt with model.

## Bar (all three must hold)

1. **No regression:** `adverse_suite_gate.py` on G5 → **GATE PASSES** (exit 0). INDETERMINATE
   (exit 2) is NOT a pass.
2. **Targets:** of the four rows the edit is aimed at — Houston AC law
   (`climate_solutions_the_cool_down_8094f43914ed`), Kyrgyz water systems
   (`central_asian_24_kg_8351094c86fd`), Mentawai petition (`indonesian_mongabay_id_4a03fd01cc36`),
   Madras HC permission (`south_asian_indian_express_9f206d53ba0f`) — **at least 3 of 4** have an
   F5 mean below 4.5 with margin ≥ band (`2·sd/√6`).
3. **The edit caused it:** each target counted in (2) must be above 4.5 or within band of it
   under F4. A row already below 4.5 under F4 is not credited to v8-5.

## Predictions (stated before running)

- Houston, Mentawai, Madras: **flip** below 4.5 under v8-5.
- Kyrgyz water: **uncertain** — "a plan" was already in v8-4's list and the oracle passed it.
- The 8 non-target flips: **unchanged** (v8-5 does not address them).
- Hong Kong schools (502 chars): not targeted; no prediction.
- Gate: passes under both prompts; v8-4's recorded 12 PASS / 1 SKIP may shift under V4.1.

## What this does NOT establish

Four target rows. Passing shows the edit moves the rows it was written for without breaking the
13-row suite; it does not show v8-5 is right on production at large — that is the ~150-article
pre-labelling check (FILTER_PLAYBOOK §1b), a separate step.
