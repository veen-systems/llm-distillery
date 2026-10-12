# belonging v3: the `focus` tag and the first count of personal stories (pre-registration, 2026-10-12)

*Written and committed BEFORE the draw. When this was written, the live page had been fetched once to check its
structure (HTTP 200, cards link `/en/artikel/<id>`); no title, score or story on it had been read. Template:
`experiments/PREREGISTRATION.template.md`.*

## 0. What is under test, and the decision it feeds

- **Under test:** two things. First, a new judge tag, `focus` (below), which the owner ruled on 2026-10-12 is how
  "personal" is measured (`docs/decisions/2026-10-10-belonging-personal-story-bar.md` § *How "personal" is
  measured*). Second, **belonging v3** (live since NexusMind run `bd00dad6`, 2026-10-09) against the owner's bar.
- **The bar (owner, 2026-10-10):** *"At most 6 of the top 30 Belonging stories may be single-person or
  single-family stories."*
- **Decisions fed:** (a) whether v3 meets the bar now, which is the case for or against the next belonging
  candidate. It is NOT an automatic rollback (v3's rollback rule predates the bar; the owner decides). (b) Whether
  blind judges can stand in for the owner on future counts (candidate gates, post-switch checks).

## The tag (the definition every judge gets)

`focus`, one value per article, independent of whether the article is in scope for Belonging:

- **`personal`:** the story is about one person or one family: their care for each other, a relationship, a
  biography, a return home, a milestone, a mentor. It stays inside that person or family.
- **`group`:** the story reaches a group beyond one person or family: people they serve or support, a public they
  work for, a trade or practice carried for others, neighbours, a congregation, a club, people acting together.

The owner's dividing line, quoted: 3, 4 and 5 below are not personal *"cause these touch groups of people"*.
Worked examples (owner labels, 2026-10-12; held-out set-2 rows, so they are NOT part of this test's population):

| owner | title |
|---|---|
| personal | A doctor said Tim was incapable of love. His mum knew otherwise |
| personal | Russian daughter-in-law quits job to care for mother-in-law in Vietnam |
| group | A valet became a key source of support for cancer patients at a N.Y. care center |
| group | Meet a 25-year-old third-generation zookeeper whose family has worked at the zoo since it opened 53 years ago |
| group | Campanas Quintana: almost 400 years of history and a succession that reaches the grandchildren (a family bell foundry) |
| personal | Juan del Val and his mother: "I like it when my son gets into controversy" |
| personal | 'Tuentifourseven', a documentary on one family's life shaped by dependency |
| personal | Three Years After October 7, I Moved Back to Nahal Oz (first person) |
| personal | Academician Huang Hefeng: my centenarian mentor Wang Man |

The rubric's in/out verdicts (rubric v2.2) are not asked for. This test is about `focus` only.

## 2. Top-of-page composition (this test)

- **Population, computed by the pipeline, not by me:** the Belonging page as ovr.news renders it,
  `https://ovr.news/en/belonging/`, fetched once. Cards are taken in page order (first appearance of each
  `/en/artikel/<id>`). This is the ranking the reader sees: display rank, Chief Editor and canonical lens all
  applied. No re-ranking by me.
- **Version filter:** each id is joined to NexusMind's stamp (`nexus_mind_attributes.belonging.version` in the
  belonging `filtered_*.jsonl` files on sadalsuud). Keep `"3.0"` rows only. Rows v1 scored, still draining, are
  skipped and counted. The first **30** v3 rows in page order are the population. If the page holds fewer than 30
  v3 rows, N is what it holds, reported as such. A page id found in no NexusMind file is reported, not guessed.
- **Owner labels (the reference):** the owner labels each of the N rows `personal` / `group` from the title and
  the English summary as the page shows them, **before** seeing any judge tag. That count, against the bar, is
  the step-2 answer.
- **Judges:** two blind Claude subagents, separate directories, given the tag definition above and each article's
  `title` + `content` (the NexusMind row's text). They see no scores, no owner labels, no page position. A row is
  judge-`personal` when both say `personal`.

## Binding rules, fixed now

1. **v3 against the bar:** owner count of `personal` ≤ 6 of 30 → v3 MEETS the bar; > 6 → it does not. (If N < 30,
   the bar scales to ≤ 6/30 × N, rounded down, and the result is reported as provisional.)
2. **Judges usable as the owner's stand-in:** BOTH of
   - per-row agreement of the both-say rule with the owner ≥ 26 of 30 (≥ 87%), and
   - the judges' count within ±2 of the owner's count.
   Otherwise the judges are not yet usable, and future counts need the owner or a revised tag (re-tested on fresh
   rows, never on these 30).
3. Nothing here is re-run to get a different answer. A disagreement is read and reported, not re-judged.

## 3. Live check after a switch

Not applicable: no switch is being made. This IS a live check of the current version.

## 4. Data

- The fetched page HTML and the joined rows go in this directory if small and free of article text; article
  text stays out of git (judge inputs in the session scratchpad). No GPU host is involved; nothing to pull
  through `lab.py`.

## 5. Predictions (before looking)

- **Owner count:** 10–18 personal of 30. Source: Claude's title read of the page on 2026-10-10 ("about half").
  ⚠️ That read and this prediction share a source, so a hit inside the range is not independent confirmation.
- **v3 meets the bar:** predicted NO.
- **Judge agreement with the owner:** 22–28 of 30. The tag is new and tested only on its own 9 examples.
- **v1-scored rows skipped before reaching 30 v3 rows:** 0–5 (v3 has been live three days; v1 rows drain for
  about 10).
