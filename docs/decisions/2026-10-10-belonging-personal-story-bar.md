# belonging: the single-person story bar (2026-10-10)

## The ruling (owner, in session, choosing between options the assistant wrote)

> **At most 6 of the top 30** Belonging stories may be single-person or single-family stories.

The question as asked: *"of the top 30 Belonging stories (ranked as ovr.news shows them), how many may be
single-person or single-family stories? 'Single-person' = the rubric's existing class: one person's or one
family's one-off act, milestone, biography or portrait (e.g. 'couple celebrates 75 years', 'husband's secret
deal to care for wife', 'shepherd saves rare breed'). Community stories = a group, neighbourhood or
institution doing something together. This number becomes the pass bar for the next belonging candidate AND
the rollback bar after any switch. Blind judges count, not me."* Options offered: ≤ 6 (recommended), ≤ 10,
≤ 3 of 30.

Background: the owner's earlier words were *"i do not mind a few personal ones, but the majority should be
about community"*, after seeing the live page show "at least half personal stories"
(`docs/evidence/2026-10-10-belonging-v3-top-of-page/README.md`, ledger H-BB6).

## How it is applied (the assistant's gloss, not part of the ruling)

- **Class:** rubric v2.2's `out_one_moment` (`docs/evidence/2026-10-02-belonging-adjudication/rubric_belonging_v2.md`),
  assigned by two blind judges; a row counts when both say so (the harvest and gate rule).
- **Population:** the top 30 by the score the site ranks on, from a fresh production draw scored by the
  candidate (pre-switch), and from what ovr.news shows, joined to NexusMind's version stamp (48 h after a switch).
- **It is a second bar, not a replacement:** the held-out gate (`experiments/README.md` § *Protocol*, item 1)
  still has to pass.
- **Live v3:** today's top reads as about half single-person by Claude's reading of titles, which is not a
  judged count. So the first application is a judged count of v3's live top 30. If it is above 6, that
  is the case for the next candidate, not an automatic rollback: the v3 rollback rule
  (`filters/belonging/v3/STATUS.md`) was fixed before this bar existed, and changing it is the owner's call.

## Owner labels on nine judged rows (2026-10-12)

Shown nine held-out set-2 positives that both blind judges (rubric v2.2) called `in_scope`, and that Claude's
title-only read flagged as single-person / single-family (`docs/evidence/2026-10-10-belonging-v3-top-of-page/c2a_missed_positives.txt`).
Owner, verbatim: *"most of them, accept 3,4,5 . cause these touch groups of people"*.

| # | title (gloss for non-English) | owner |
|---|---|---|
| 1 | A doctor said Tim was incapable of love. His mum knew otherwise | personal |
| 2 | Nàng dâu Nga bỏ việc sang Việt Nam chăm mẹ chồng (Russian daughter-in-law quits job to care for mother-in-law) | personal |
| 3 | A valet became a key source of support for cancer patients at a N.Y. care center | **not** personal (touches a group) |
| 4 | Meet a 25-year-old third-generation zookeeper whose family has worked at the zoo since it opened 53 years ago | **not** personal (touches a group) |
| 5 | Campanas Quintana: casi 400 años de historia y una sucesión que llega a los nietos | **not** personal (touches a group) |
| 6 | Juan del Val y la madre que lo parió | personal |
| 7 | 'Tuentifourseven', el documental que narra la vida de una familia marcada por la dependencia | personal |
| 8 | Three Years After October 7, I Moved Back to Nahal Oz | personal |
| 9 | 黄荷凤院士：我的百岁恩师王曼先生 (Academician Huang Hefeng: my centenarian mentor Wang Man) | personal |

**What it shows (measured on these 9 only):** both judges said `in_scope` on 6 rows the owner calls personal, so
rubric v2.2's judges draw the line WIDER than the owner. A judged count of v3's top 30 with this rubric would
UNDERCOUNT against the bar.

**The assistant's gloss, not ruled:** the owner's dividing line reads as *does the story reach a group beyond the
person or family* (the valet supports many patients; the zookeeper's family serves a public zoo; the bell foundry
spans generations of a trade). Before step 2's count, test the judges against these 9 labels and, if they still
miss, tighten `out_one_moment` in the rubric, then re-test on held-back examples, not on these 9.

## How "personal" is measured — RULED 2026-10-12 (owner): a separate tag

Asked whether to (a) keep the lens rulings and add an independent `focus` tag that the bar counts, or (b) narrow
the lens so single-person / single-family stories become out of scope, the owner chose **(a), the separate tag**.
So a personal story can be in scope and still count toward the 6. This REPLACES the gloss above that applied the
bar through `out_one_moment`. That class is out-of-scope by definition, so it could never count an in-scope
personal story: the bar's own example ("husband's secret deal to care for wife") is ongoing care, which rubric v2.2
rules IN. The 10-02 lens rulings are unchanged. Tag definition and its first test:
`docs/evidence/2026-10-12-belonging-personal-tag/PREREGISTRATION.md`.
