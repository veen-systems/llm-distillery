---
name: project_session_2026_08_06
description: Four-lens review of the previous evening's commits found 4 blockers and 13 warnings — every measurement held, the prose around them did not; plus a global skill symlink that had been shadowing this repo's own adapted skill
metadata:
  type: project
---

# Session 2026-08-06 — the review, and a skill that was never running

Short session, two subjects. No filter work, no training, no deploy.

## 1. `/review-changes` over the previous evening's two commits

Four lenses concurrently — guarantee-preservation, adversarial, code-correctness,
doc-accuracy — over llm-distillery `df64213` and ovr.news `2118a21`/`08d176b`.
**4 blockers, 13 warnings.** All fixed and pushed (`b37b88e` here, `8ce017c` there).

**The finding worth carrying: every measurement survived; the sentences around them
did not.** Verified intact — 333+117+907 = 1,357, every EU date against primary
sources, the 191 issue count reproducible to its measurement window, 44 ADRs, 1,103
tests, the EUR-Lex zero-hit result re-derived independently. What failed:

| # | Defect | Mechanism |
|---|---|---|
| 1 | Duplicate footer link, live on every page | A fact about the codebase asserted without a `grep` — the comment said "reachable only from in-page links until 2026-08-05"; it had been in the footer since `3a64f0f` |
| 2 | `GPTBot 401 domains` in a public ADR + two files | A derived count never checked against its own total (333, stated four lines above). They counted matching *lines*, not domains |
| 3 | ADR-003 contradicting itself and the shipped code, three ways | Stale text a few paragraphs from correct new text, in a file the same commit edited |
| 4 | `tests/ai-disclosure.test.ts` left stale while the table it enforces grew | A one-directional pointer: the "keep in sync" instruction lived in the test, the work happened in the ADR |

Blocker 4 was the serious one — the entire art. 50 marker could be deleted with a
green 1,103-test suite. Now extended and **proved to bite**: deletion fails 3 tests,
restoration passes 26/26.

**Two of my own predictions were refuted by measurement**, which is the useful part:
the surrogate-slice hazard has zero occurrences across 2,478 pages, and the PNG/SVG
dot positions are byte-identical (drift is font glyphs only). Convergence across
differently-worded lenses beat single-reviewer confidence — three lenses independently
found the ADR-003 contradiction, two independently found the missing guard.

**Substantive improvement that fell out of it:** the 160-char budget was Google's
snippet convention applied to social cards, which render ~300. Splitting it gave every
card back 26 characters — measured 160 → 186 over 567 pages, search meta still capped.

## 2. A global skill symlink had been shadowing this repo's own

`~/.claude/skills/review-changes` pointed at **`repos/personal`**, not
agent-ready-projects. So `/review-changes` here ran a checklist tiered on
`Nieuw huis/`, `modellen/*.py` and `principes.md`, asserting *"the container itself
has no git"*. The tier table had to be rewritten mid-run.

**A global skill wins over a project-local one of the same name, silently** — both
existed; the invocation reported `Base directory: ~/.claude/skills/…` for `curate`
*and* `review-changes`. The project copy is not consulted, not merged, not mentioned.

Fixed: removed the global symlink (project-local now confirmed serving), deleted two
genuinely stale local copies — `curate` and `audit-context`, older framework versions
with nothing repo-specific. Local `curate` was 43 lines behind and **missing the
warning that `git log -1` returns empty-with-exit-0 on a gitignored memory dir**, so
its staleness check reported nothing stale while examining nothing.

Then ported four items into the local skill, harvested from that divergent copy and
from a parallel harvest a concurrent ovr.news session did: **untracked-file scan**
(untracked files show in no diff and are usually new code, so they are the highest-risk
part of a change), two adversarial questions, **re-derive every number rather than
inherit it from adjacent prose**, and **re-read the whole section, not the diff**.
Each is a direct encoding of a blocker above.

## Concurrency note

A second Claude session was working in ovr.news throughout — it committed `bbdc8f4`,
`bb5c1b0`, `b905ce0` and the `datasets/adverse/` work that appeared in this repo as
`e22b4aa`. **Both repos were left to whoever was mid-flight**: nothing of theirs was
committed or pushed here. Worth knowing that two sessions can share a clone and that
`git status` is the only warning you get.

## Open

- **FS#120** — still the only calendar-bound item, ~2026-08-14, now eight days out.
- **#97** — the six deployed filters, unassessed against the #28 TDM position.
- ovr.news carries one open surface decision: share-by-email `mailto:` sends an AI
  headline with no marker (ADR-003 table, recorded as OPEN).

## Related

- [[project_session_2026_08_05_evening]] — the work this session reviewed
- [[gotcha-log]] — three entries added today, incl. the skill-shadowing one
- [[cross-repo-prioritization]] — unchanged today
