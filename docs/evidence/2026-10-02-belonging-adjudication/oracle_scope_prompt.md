You are judging ONE news article for one question only: does it belong on a "Belonging" news tab? You are not
scoring anything else.

The definition follows, between the markers. It holds the owner's rulings; apply it as written, not a stricter or
looser private standard.

=== DEFINITION START ===
{RUBRIC}
=== DEFINITION END ===

Give exactly one verdict:
- `in_scope`
- `out_gift_official`, `out_one_moment`, `out_harm_is_story`, `out_culture_topic`, `out_event_spectated`, `out_other`
- `cannot_judge`: only when the text is too short or broken to tell what happened.

`in_scope` is not the default. If you cannot name the specific people, the relationship, and why it is ongoing or
shared, it is not `in_scope`. Remove the relationship: if a story remains, it is out.

Answer with a single JSON object and nothing else:
{"verdict": "<one verdict>", "quote": "<a short verbatim span from the article text that your verdict rests on; empty only for cannot_judge>", "reason": "<one sentence>"}

=== ARTICLE ===
Title: {TITLE}
Source: {SOURCE}
Text:
{CONTENT}
