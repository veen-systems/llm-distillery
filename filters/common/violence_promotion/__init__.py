"""Violence Promotion Prefilter — stamp-only cross-cutting binary classifier.

Flags articles that promote, normalize, or present as desirable any form of
mass violence: active combat, weapons manufacturing, military force as a
solution, state violence against citizens, or instruments of violence as
progress.

ovr.news is a constructive-news feed. Violence and its instruments — whether
framed as combat reporting, industrial achievement, or policy necessity — are
not constructive. This detector answers the question "does this article center
violence or instruments of violence?" If yes, it doesn't belong on ovr.news.

Follows ADR-004: stamp-only (not a universal drop). Consumers opt in.
"""
