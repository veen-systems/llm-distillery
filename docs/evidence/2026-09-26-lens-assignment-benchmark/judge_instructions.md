# Judge instructions — lens-assignment benchmark (given verbatim to every blind subagent)

*Saved before the first batch ran. `{BATCH}` is A1, A2, B1 or B2.*

---

ovr.news is a news site with five tabs. Each article below passed the filters of two or more tabs, listed in its
`passed_lenses` field. Your one question per article: **on which tab does it belong?**

The tabs (filter name → tab):
- `uplifting` → **Thriving**: a process going well for PEOPLE, now (documented outcomes delivered to people; not
  emotional tone, funding, plans or speculation).
- `belonging` → **Belonging**: genuine community bonds, rootedness, intergenerational ties; social fabric that
  cannot be bought or optimised.
- `cultural_discovery` → **Discovery**: discoveries about art, culture and history, and connections between
  peoples and civilisations.
- `nature_recovery` → **Recovery**: nature bouncing back (documented ecological recovery, or protection or
  restoration of nature that has actually happened); not technology, pledges or doom.
- `solutions` → **Solutions**: concrete actions toward problems, across technology, governance and community.

1. Read every article in `docs/evidence/2026-09-26-lens-assignment-benchmark/input_{BATCH}.jsonl`. Judge each one
   on its own; do not open any other file in the repository and do not look up scores.
2. Give each article exactly ONE answer:
   - one filter name from its own `passed_lenses`: the tab the article is MOST about;
   - `both:<a>+<b>`: only when it is genuinely equally about two of its passed lenses (use sparingly);
   - `none`: it belongs on none of its passed tabs (junk that got through).
3. Write `docs/evidence/2026-09-26-lens-assignment-benchmark/out_{BATCH}.jsonl`: one line per input article, in input
   order, keys exactly `{"id": ..., "answer": ..., "reason": ...}` (reason: one sentence).
4. Reply with only the number of lines written and a count per answer.
5. Keep any helper script or scratch file ONLY under `/tmp/judge_lens{BATCH}/`. Never run, edit or read a script
   you did not write yourself.
