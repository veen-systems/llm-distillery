# Judge instructions v2: given verbatim to every blind subagent (pilot v2, pass A and pass B)

*Saved before the first batch ran. `{DIR}` is the judge's own directory.* ⚠️ When pilots v2 and v3 ran, `rubric_belonging_v2.md` held **v2.0**, now kept verbatim as `rubric_belonging_v2_0.md`. To reproduce them, point the instructions there.

---

You are judging news articles for one question only: **does this article belong on a "Belonging" news tab?** You are
not scoring anything else.

1. Read the definition in full before any article:
   `docs/evidence/2026-10-02-belonging-adjudication/rubric_belonging_v2.md`. It holds the owner's rulings; apply them
   as written.
2. Read every article in `{DIR}/input.jsonl` (JSONL with `id`, `title`, `url`, `source`, `content`). Judge each one on
   its own.
   - You are told nothing else about the articles, and you must not look for anything else.
   - Do not open other files in the repository. Do not look up scores, labels, exemplars, or which system selected
     an article.
3. Give each article exactly one verdict:
   - `in_scope`
   - `out_gift_official`, `out_one_moment`, `out_harm_is_story`, `out_culture_topic`, `out_event_spectated`,
     `out_other`
   - `cannot_judge`: only when the text is too short or broken to tell what happened.

   `in_scope` is not the default. If you cannot name the specific people, the relationship, and why it is ongoing or
   shared, it is not `in_scope`. Remove the relationship: if a story remains, it is out.
4. Write `{DIR}/out.jsonl`: one JSON line per input article, **in input order**, with exactly these keys:
   `{"id": ..., "verdict": ..., "quote": ..., "reason": ...}`.
   - `quote` is a short verbatim span from the article's `content` (not the title) that your verdict rests on. It is
     empty only for `cannot_judge`.
   - `reason` is one sentence.
5. Put any temporary file you need ONLY in `{DIR}/scratch/`. Other judges are running at the same time, and shared
   locations get overwritten.
6. Reply with only the number of lines written and a count per verdict.
