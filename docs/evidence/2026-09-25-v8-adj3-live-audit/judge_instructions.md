# Judge instructions — given verbatim to every blind subagent (pass A and pass B)

*Saved before the first batch ran. `{INPUT}` and `{OUTPUT}` are the batch's two file paths.*

---

You are judging news articles for one question only: **does this article belong on a "Thriving"
news tab?** You are not scoring anything else.

1. Read the definition, in full, before any article:
   - `docs/evidence/2026-09-24-thriving-adjudication-pilot/rubric_scope_v8-4.md` (STEP 1 of the
     v8-4 oracle prompt, verbatim)
   - `docs/decisions/2026-09-24-thriving-scope-rulings.md` (the owner's rulings; they override
     the rubric where they differ)
2. Read every article in `{INPUT}` (JSONL; `id`, `title`, `url`, `source`, `content`). Judge each
   one on its own. You are told nothing else about the articles, and you must not look for
   anything else: do not open other files in the repository, do not look up scores, labels, or
   which system selected an article.
3. Give each article exactly one verdict:
   `in_scope`, `out_of_scope`, `harm_is_subject`, `response_to_harm`, `no_person_benefits`, or
   `cannot_judge` (only when the text is too short or broken to judge, e.g. a bare headline).
   `in_scope` is not the default: if you cannot name a process going well for people, now, it is
   not `in_scope`. Apply the definition as written, not a stricter or looser private standard.
4. Write `{OUTPUT}`: one JSON line per input article, **in input order**, with exactly these keys:
   `{"id": ..., "verdict": ..., "quote": ..., "reason": ...}`. `quote` is a short verbatim span
   from the article's own text that your verdict rests on (empty only for `cannot_judge`).
   `reason` is one sentence.
5. Reply with only the number of lines written and a count per verdict.
