# Candidates — NOT adverse rows

Everything here carries `"label": "CANDIDATE_UNADJUDICATED"` and **must not be
used as training or gating evidence**.

## Why a subdirectory

`.gitignore` re-includes `datasets/adverse/*.jsonl`, and `docs/TODO.md` (#91)
describes a future gate that reads those files with the criterion *"every
adverse record scores below `max_acceptable_wa`"*. A candidate file sitting
directly in `datasets/adverse/` would be picked up by that glob and silently
treated as curated evidence.

That is this repo's signature failure — a mechanism reading a population it was
never meant to read. So candidates get their own directory and their own
`.gitignore` negation. **Nothing in `datasets/adverse/*.jsonl` is unadjudicated;
nothing in here is adjudicated.** Keep it that way.

## Promotion

A candidate becomes an adverse row only by editorial judgement, moved into
`../<filter>.jsonl` with `label: adverse`, `labelled_by` naming the human, and
the reasoning recorded in a dated note beside it. The precedent to follow is
[`../2026-08-05-ovr-flag-adjudication.md`](../2026-08-05-ovr-flag-adjudication.md),
which **rejected one of five** staged rows and explained why — because the
reasoning behind a rejection is worth as much as an acceptance, and a row that
is simply absent looks like an oversight.

The standing hazard it names, and the reason bulk import is refused here:

> Labelling this adverse teaches the scorer to suppress a **category**.

## Current contents

| file | n | source | status |
|---|---|---|---|
| `2026-08-09-uplifting-oracle-batch.jsonl` | 34 | gemini-flash oracle, sampled above the op-point (ADR-023) | **21 `solutions_story` rows adjudicated 2026-08-10**: 7 accepted, 3 rejected, 11 held. **The other 13 (`doom_framed` 7, `community_building` 3, `speculation` 2, `politics` 1) are untouched.** |
| `2026-08-09-reader-flags.jsonl` | 1 | ovr.news reader flags, free text | 3 accepted + 1 rejected 2026-08-09; **1 still open** |

**Rows stay in this file after adjudication.** They keep
`label: CANDIDATE_UNADJUDICATED`, because this file is the record of what the
batch contained; the disposition of each row lives in the adjudication note, and
an accepted row is *copied* into `../<filter>.jsonl` with `label: adverse`, not
moved. Do not edit labels here to reflect a decision — that would make the file
disagree with its own name and re-open the glob hazard this directory exists to
prevent.

See [`../2026-08-10-uplifting-oracle-batch-adjudication.md`](../2026-08-10-uplifting-oracle-batch-adjudication.md)
(the decisions and reasoning),
[`../2026-08-09-uplifting-oracle-batch.md`](../2026-08-09-uplifting-oracle-batch.md)
(how the batch was built — note its "absorbing solutions-lens material" reading
is corrected by the adjudication note) and
[`../2026-08-09-reader-flags.md`](../2026-08-09-reader-flags.md).
