# Judge instructions — Nature recovery RELABEL PILOT under ruling NR-1 (given verbatim to every blind subagent)

*Copied from the miss-audit re-judge; only the file paths differ. Saved before the first batch ran. `{BATCH}` is A1, A2, B1 or B2.*

---

You are judging news articles for one question only: **does this article belong on a "Nature recovery" news tab?** You are not scoring anything else.

1. Read the definition, in full, before any article: `docs/evidence/2026-09-25-nature-recovery-miss-audit/rubric_scope_nr-v4.md` (the nature_recovery v4 oracle prompt's STEP 1 scope check and §4 pre-classification, verbatim). Use only its SCOPE rules; ignore the dimension scoring. THEN read `docs/decisions/2026-09-25-nature-recovery-scope-ruling.md` (the owner's ruling NR-1); it overrides the rubric where they differ.
2. Read every article in `docs/evidence/2026-09-25-nature-recovery-relabel/pilot_input_{BATCH}.jsonl` (JSONL; `id`, `title`, `url`, `source`, `content`). Judge each one on its own. You are told nothing else about the articles, and you must not look for anything else: do not open other files in the repository, do not look up scores, labels, or which system selected an article.
3. Give each article exactly one verdict: `in_scope` (it documents ecosystem recovery: observed ecological recovery, DELIVERED in-force protection / pressure removal, or — under ruling NR-1 — a COMPLETED restoration or protection step even before recovery is measured), `out_of_scope` (anything else, including the rubric's out-of-scope categories and flags: climate doom, climate tech, greenwashing, conservation appeals without outcomes, policy announcements, pledges and plans, short-lived gains, research without recovery outcomes, symbolic gestures, single-animal events), or `cannot_judge` (only when the text is too short or broken to judge, e.g. a bare headline). `in_scope` is not the default. Apply the definition as written, not a stricter or looser private standard.
4. Write `docs/evidence/2026-09-25-nature-recovery-relabel/pilot_out_{BATCH}.jsonl`: one JSON line per input article, **in input order**, with exactly these keys: `{"id": ..., "verdict": ..., "quote": ..., "reason": ...}`. `quote` is a short verbatim span from the article's own text that your verdict rests on (empty only for `cannot_judge`). `reason` is one sentence.
5. Reply with only the number of lines written and a count per verdict.
6. If you write any helper script or scratch file, put it ONLY under `/tmp/judge_nrpilot{BATCH}/`. Never run, edit or read a script you did not write yourself.
