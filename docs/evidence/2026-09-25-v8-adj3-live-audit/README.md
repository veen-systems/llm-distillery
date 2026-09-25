# adj3 vs v8 on a week of production — RESULT (2026-09-25)

**adj3 WINS the pre-registered bar.** Of what each model would publish, **33.8% is junk for v8
and 14.9% for adj3** (difference +0.189, 95% CI [+0.136, +0.244]). Per cycle that is ~10.7 junk
articles for v8 vs ~2.9 for adj3, at the cost of ~21.0 → ~16.7 in-scope ones. Nothing deployed.

Bar: `PREREGISTRATION.md` (`0ca203a`, amended `6c59615`), applied by `analyse.py` (`e9730ac`),
all committed before any adj3 production score or verdict existed.

## Stop conditions — all passed
| check | result |
|---|---|
| b650-v8 vs production v8, passers disagreeing outside the 0.16 band | **2 of 1,351 (0.15%)**, stop above 10% |
| known-answer controls in pass A | **4/4** |
| drift, pass A vs pass B | **0.944** on 72 rows, stop below 0.90 |
| owner blind check | **16/20 — BELOW the ≥ 18 bar**; resolved, see `owner_check_resolution.md` |

⚠️ **The owner check did not meet its bar blind.** The result was withheld, the owner ruled on
the 4 disagreements (3 were the owner being generous; 1 was the judge being generous), and against
those rulings the judges are 19/20. Substituting the owner's 20 rulings changes 1 row's
in/out and moves the difference to +0.187 [+0.134, +0.242]: still a WIN.

## The week (`groups.json`)
42 cycles, `filtered_20260918_145649` → `filtered_20260925_093350`; 123,994 `stage2` ids, **620
excluded** as training overlap (adj3 was trained on production passers from this same week).

| group | N | judged | junk | junk rate |
|---|---|---|---|---|
| **A** — adj3 adds | 250 | 149 (+1 cannot_judge) | 39 | 26.2% |
| **R** — adj3 removes | 754 | 150 | 78 | **52.0%** |
| **B** — both publish | 576 | 60 | 6 | 10.0% |

Over the week, adj3 removes ~392 junk and ~362 in-scope articles, and adds ~65 junk and ~185 in-scope.

## Read these before quoting it
1. **adj3's ADDITIONS are junkier than what both keep** (26% vs 10%). Most of the gain comes from
   what it removes: half of the articles v8 publishes and adj3 drops are junk.
2. **Volume: adj3 publishes ~38% fewer articles** (19.7 vs 31.7 per cycle) and **~20% fewer in-scope
   ones** (ADR-023: a missed positive costs nothing visible). Above the pre-registered 50% flag.
3. **The judge is Claude under the same rubric that produced adj3's training labels.** The owner's
   20 and the four rulings are the independent part.
4. **v8 is not what Thriving serves today.** `uplifting v7` is (#151). This compares candidate
   with candidate; the cutover question is the next one.
5. One week, one seed. Rates are over the audit population (exclusions removed), re-weighted by
   group size, and do not describe the whole feed.
6. **Incident:** the A02 judge re-ran the A01 judge's helper script, which rewrote `out_A01.jsonl`.
   A01 still matches its own judge's reported counts, keeps its input order, and every one of its
   quotes appears verbatim in its article (`b6e3f1b`). The judges shared a scratch directory, and
   the next run should give each judge its own.

## Files
`groups.json`, `key.jsonl` (copied here after judging; kept out of the judges' reach until then),
`input_*`/`out_*` (blind batches and verdicts), `owner_check*.{md,jsonl}`, `judge_instructions.md`,
`build_panel.py`, `analyse.py`. Scores: `datasets/audit/ht_2026-09-25/` (gitignored, local).
