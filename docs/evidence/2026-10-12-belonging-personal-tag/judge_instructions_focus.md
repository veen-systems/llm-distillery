# Judge instructions: the `focus` tag (given verbatim to each blind judge, and as the qwen prompt)

*Saved before the first judge ran (2026-10-12). `{DIR}` is the judge's own directory. Pre-registration:
`PREREGISTRATION.md` beside this file.*

---

You are tagging news articles for one question only: **is this story about one person or one family, or does it
reach a group of people beyond them?** You are not judging quality, mood, or whether the story fits any news
section.

**The tag, `focus`: give exactly one value per article.**

- `personal`: the story is about one person or one family: their care for each other, a relationship, a
  biography, a return home, a milestone, a mentor. It stays inside that person or family.
- `group`: the story reaches a group beyond one person or family: people they serve or support, a public they
  work for, a trade or practice carried for others, neighbours, a congregation, a club, people acting together.

Worked examples (labelled by the editor; the dividing line is "does it touch a group of people"):

| tag | title |
|---|---|
| personal | A doctor said Tim was incapable of love. His mum knew otherwise |
| personal | Russian daughter-in-law quits job to care for mother-in-law in Vietnam |
| group | A valet became a key source of support for cancer patients at a N.Y. care center |
| group | Meet a 25-year-old third-generation zookeeper whose family has worked at the zoo since it opened 53 years ago |
| group | A family bell foundry: almost 400 years of history and a succession that reaches the grandchildren |
| personal | Juan del Val and his mother: "I like it when my son gets into controversy" |
| personal | A documentary on one family's life shaped by dependency and care |
| personal | Three Years After October 7, I Moved Back to Nahal Oz (a first-person return home) |
| personal | Academician Huang Hefeng: my centenarian mentor Wang Man |

Steps:

1. Read every article in `{DIR}/input.jsonl` (JSONL with `id`, `title`, `content`). Judge each one on its own.
   - You are told nothing else about the articles, and you must not look for anything else. Do not open other
     files in the repository. Do not look up scores, labels or where an article came from.
2. Write `{DIR}/out.jsonl`: one JSON line per input article, **in input order**, with exactly these keys:
   `{"id": ..., "focus": "personal" | "group", "quote": ..., "reason": ...}`.
   - `quote` is a short verbatim span from the article's `content` (not the title) that your tag rests on.
   - `reason` is one sentence.
3. Put any temporary file you need ONLY in `{DIR}/scratch/`. Other judges are running at the same time.
4. Reply with only the number of lines written and a count per tag.
