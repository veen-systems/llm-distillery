# Session 2026-08-16 (evening) — #121 measured, #120 closed, and five of my six errors caught by peers

**No filter, no model, no package, no deploy from this repo.** Doc/memory commits only.
Nothing was changed on any production box.

---

## What shipped

| | |
|---|---|
| **llm-distillery#121** | Measured over **233,338 rows** / 85 cycles / 14 days. Posted to the issue, disposition comment added, left OPEN for one lens-definition decision. Record: `memory/opinion-genre-hypotheses.md` |
| **llm-distillery#120** | References **50 → 1**, `48f48a5`. Closed. |
| **CLAUDE.md judgement** | `77dfc64` — the two new rules keep their imperatives, their evidence moved to `memory/working-rules.md`. 35,764 → 35,464, **still 464 over**. |

## The findings, ranked

⭐⭐ **#121's headline was the source confound and nothing else, in five of six lenses.**
`belonging` 5.9× at n=33 becomes **MH OR 0.98** at n=3,750 (pooled 4.0% vs 3.9%). The
issue's own caveat #2 — "this is the one that could dissolve the finding" — was right and
did dissolve it. The one survivor, `investment_risk` at **2.05** with 66 of 89 sources in
the same direction and zero ties, reproduces on three detector arms independently
(2.23 / 2.15 / 1.83) with near-identical stage composition, so it is not a probe artefact.

⭐⭐ **A wrong op-point in the issue body manufactured one of the two zeros its own
conclusion rested on.** `solutions` v6 surfaces at **2.25**, not 4.0; #121 measured 1.8
points too high. At the correct point that lens **reverses** (OR 0.50, 66 of 92 sources
negative) — it already discriminates against advocacy, which is the opposite of the
lens-fidelity story the issue was opened to test. **Refuted where measurable, not merely
unsupported.** ⚠️ The repo itself had 2.25 recorded correctly in three places; the error
was fresh, in the issue only.

⭐ **The detector nearly became the hand-built population the issue warned about.**
`*_tribune` (Express/Qatar/Texas/La Tribune, 57 rows), `village_voice_news`, `scotusblog`,
`aws_ml_blog` are publisher **names**; `live-blog` (52) is breaking news; tag `analysis`
(125) is mostly `fundamental-analysis`. Grounding every token in a captured corpus string
rather than guessing is what caught it.

⭐ **#120 reached 1 and that was tested, not asserted.** `run.sh` 24/24 either side plus
four seeded mutations — wrong-repo marker, fabricated file behind a correct repo name,
placeholder on a resolving path, mentioned-but-not-present — all caught. Every target was
located with `git ls-files` **before** the marker was written and the resolved list
re-read after, because naming a repo that does not hold the file is how the edit could
have laundered a real break.

⭐ **`nature_recovery`'s null carries no information**: 68 of 92 strata tied at 0 vs 0 on
a lens surfacing 0.16%. The instrument could not have said yes. This is the rule filed
into `working-rules.md` the same morning, paying out within hours in a different session.

## My errors — six, five caught by a peer re-deriving

1. **Bare `ADR-023`** in cross-repo advice. Three exist. Came back as a confident,
   well-evidenced rebuttal quoting a constraint from a file I had never cited. ⭐⭐ **An
   ADR that resolves wrongly arrives with authority, unlike an issue number.**
2. **Glob over `collection_*` hit metadata files**, returned `distinct ids: 0`.
3. **Re-implemented `refcheck.py`** instead of running it; my copy omitted `STATE_SHAPE`
   and reported a population of zero. Second instance of (2)'s root in one session.
4. **Named a population without sizing it** — empty-url rows are **1 in 157,870**, so my
   "this narrows the caveat" was backwards.
5. **Triaged #120 against the wrong lines** — findings dedup on (doc, frag), so the
   reported occurrence is not necessarily the first in the file.
6. **Read the gotcha log's tail expecting the newest entries.** It is newest-first.

## Cross-session

Long exchange with **nexusmind-65** on NM#390. ⛔ **I declined to rule** — #119 was ruled
by the owner and a relayed ruling is what cost a day on 08-15. Gave technical input only,
and flagged that NM#390 is an **equivalence** question, not the **identity** question #119
settled, so #119's answer may not transfer. Their owner then ruled *further* than their
own proposal (gate off by default, not repaired). **pipeline-atlas-57** came back clean on
the op-point: the atlas quotes no numeric operating point anywhere, so a figure that moved
in a sibling could not rot in its prose.

## ⛔ NM#390 is WRITTEN, NOT FIXED — checked against the artefact, not the report

Implemented and **uncommitted** in NexusMind's tree on branch
`docs/audit-corrections-and-contract-a-1.34.0`; no commit mentions it. Blocked on two
tests encoding the old behaviour (correctly stopped rather than edited). **Not deployed** —
sadalsuud is on `14b0f49`, `url_dedup` absent from its config and `main.py`, box 3 commits
behind including Contract A 1.34.0. **~800–1,000 distinct articles per fortnight are still
being dropped.** ⚠️ When it deploys, `duplicate_url` falling is the *intended* effect and
cannot distinguish a good fix from one that merely stops deduplicating — the kept-set
comparison belongs in the deploy note, and the rollback claim wants one execution.

## Open for the owner

1. **`datasets/` is not in `refcheck.py`'s `STATE_DIRS`** — the 15 new placeholders flip to
   *STALE PLACEHOLDER* if a corpus is re-materialised locally.
2. **A #119 addendum, offered and unwritten**: `id = md5(source + "_" + raw_url)[:12]`, so
   a URL edit presents as a new item and the supersede path cannot fire. Measured not to
   occur; a structural bound on an owner ruling, so the owner's to accept.
3. **CLAUDE.md 464 over budget** — an `/audit-context` job, not this one.

Related: `memory/opinion-genre-hypotheses.md`, `memory/working-rules.md`, `docs/TODO.md`.
