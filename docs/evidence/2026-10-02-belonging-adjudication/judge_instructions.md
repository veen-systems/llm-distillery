# Judge instructions: given verbatim to every blind subagent (pass A and pass B)

*Saved before the first batch ran. `{INPUT}` and `{OUTPUT}` are the batch's two file paths.*

---

You are judging news articles for one question only: **does this article belong on a "Belonging" news tab?** You
are not scoring anything else.

1. Read the definition in full before any article:
   `docs/evidence/2026-10-02-belonging-adjudication/rubric_belonging.md`. It holds the owner's rulings; apply them as
   written, including Q1–Q3.
2. Read every article in `{INPUT}` (JSONL with `id`, `title`, `url`, `source`, `content`). Judge each one on its own.
   - You are told nothing else about the articles, and you must not look for anything else.
   - Do not open other files in the repository. Do not look up scores, labels, exemplars, or which system selected
     an article.
3. Give each article exactly one verdict:
   - `in_scope`
   - `out_gift_official`, `out_event_crowd`, `out_one_person`, `out_harm_is_story`, `out_culture_topic`, `out_other`
   - `cannot_judge`: only when the text is too short or broken to tell what happened, e.g. a bare headline or a
     teaser that stops before saying who did what.

   `in_scope` is not the default. If you cannot name the group of ordinary people, what they did together, and its
   result, it is not `in_scope`. Pick the `out_*` class that fits best. Apply the definition as written, not a
   stricter or looser private standard.
4. Write `{OUTPUT}`: one JSON line per input article, **in input order**, with exactly these keys:
   `{"id": ..., "verdict": ..., "quote": ..., "reason": ...}`.
   - `quote` is a short verbatim span from the article's own text that your verdict rests on. It is empty only for
     `cannot_judge`.
   - `reason` is one sentence.
5. Reply with only the number of lines written and a count per verdict.
