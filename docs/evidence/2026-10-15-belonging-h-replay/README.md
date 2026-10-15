# belonging v3 on ranking H: seven daily top-30 personal counts, replayed offline (2026-10-15)

Pre-registered in `PREREGISTRATION.md` (`188aabc`, before any population was built or tag read). $0 oracle; qwen
on b650 (freed by ovr.news the same morning). `docs/TODO.md` item 0a.

## Steps and files

1. `ovr_db_rows.json`: the baseline's ovr.db query (read-only on sadalsuud), run 2026-10-15T07:00Z, 1,170 rows.
   `page_ids_20261015.txt`: the 521 cards of https://ovr.news/en/belonging/, page built 2026-10-15T06:37:16Z.
2. `build_population.py > builds.json`: the population per build and each order's top 60 (H, control).
3. `extract_rows.py` (the baseline's, unchanged) on sadalsuud: version stamps and text for 334 ids. Lab
   `extract/rows.jsonl`.
4. `select_v3.py > selection.json`: the first 30 v3 rows per build and order.
5. qwen `focus` tags: 117 ids reused from earlier runs, 83 new, plus 10 reused ids re-tagged as the determinism
   control. Lab `tag/`.
6. `count.py > count_result.txt`.

## Checks

- **The rebuild reproduces today's live page order:** control order on the 10-15 population minus its removals
  matches the page's top 60 at **60/60** positions (`builds.json` `_meta`). ⚠️ This is **partly circular**:
  10-15's removals are defined as population minus page, so the check tests only that the control FORMULA orders the
  page's own cards correctly, and that the population rule covers every card on the page. It does not test the
  removal estimate for any other day, or the H order. (Found by review.)
- **Determinism control: 10/10** re-tagged ids match their earlier tags, so reuse stands.
- **Presence control: PASS** in both variants (control on 10-12: 6 primary, 8 dated).
- 1 reused tag (10-11 control, from a 10-12 tag file) is unparsed (`None` in every file). It is reported as is.
- Removal status is unknown for 327 / 289 / 176 / 87 rows of the 10-09 to 10-12 populations (no observed build
  covers them), and 0 from 10-13 on. No top-30 row has unknown status.
- All outputs reproduce byte-for-byte from the committed scripts (review).

## ⚠️ Deviation: the pre-registered removal rule is refuted by the data

The pre-registration (section 1) treats a removal as **sticky**: a row removed at either observed build (10-13 or
10-15) is dropped from every build. **Review found this false:** 46 of the 219 rows removed at 10-15 were ON the 10-13
live page, including 3 rows of the owner-labelled 10-12 page. So the primary rebuild drops rows readers really saw on
10-11 to 10-13. That is the whole reason its control top 30 overlaps the baseline's only **27/30** on 10-11 and 10-12
(counts 3 and 6, where the baseline had 4 and 8). (A second violation: one row removed at 10-13 is back on today's
page, at position 433, harmless to the top 60.)

**Dated variant (added after the result, so it is post hoc):** each observed removal applies only to builds on its own
side of 10-13: the 10-13 removals to builds through 10-13, the 10-15 removals to 10-14 and 10-15. Files with
`_dated`; `--dated` on the three scripts. 35 more ids extracted, 5 more tagged (lab `extract-dated/`,
`tag-dated/`). **It reproduces the 10-13 baseline's selection 30/30 on 10-11 and 10-12, with the baseline's counts
(4 and 8).** That makes it the better rebuild, but it was chosen after seeing the data.

## Result, qwen counts (a FLOOR), in-range builds (N = 30)

| build | H primary | H dated | control primary | control dated |
|---|---|---|---|---|
| 10-11 14:30Z | 6 | 6 | 3 | 4 |
| 10-12 14:30Z | 5 | 6 | 6 | 8 |
| 10-13 14:30Z | 4 | 5 | 4 | 5 |
| 10-14 14:30Z | 4 | 4 | 8 | 8 |
| 10-15 06:37Z | 5 | 5 | 7 | 7 |
| **weekly mean** | **4.80** | **5.20** | **5.60** | **6.40** |
| worst day | 6 | 6 | 8 | 8 |

10-09 and 10-10 are out of range in both variants (H: 2 and 7 v3 rows in its top 60; v1 rows still drain). H top
30s hold 5–9 rows under 24 h, against 27–30 for control. Full tables: `count_result.txt`, `count_result_dated.txt`.

**Predictions (§4), scored on the primary variant:** 2–5 hit (H mean ≤ control mean; ≤ 10 rows under 24 h; 5 of 7
in range; rebuild overlap 27 ≥ 26). Prediction 1 (H per build 2–8) hit on every in-range build (4–6), but 10-09
under H counts 1 (N = 2, out of range). The prediction did not say "in range", so it is a **miss on that build**.

## Reading

- MEASURED (primary, as pre-registered): H 4.80, control 5.60. Both are at or under 6 on a floor, which the
  pre-registration defines as **undetermined**.
- MEASURED, POST HOC (dated variant, the better rebuild): H **5.20**, control **6.40**. On the pre-registered rule
  (a floor mean above 6 is conclusive), **the current ranking fails the bar even on qwen's undercount**. Treat that as
  strong but post hoc: the rule was pre-registered, the variant was not.
- H's floor mean stays at or under 6 in both variants: undetermined. GUESS, not measured: scaling by the one
  calibration point (owner 10 vs qwen 7 on 10-12) puts H near 7.4 (dated) and control near 9.1. Only the owner's own
  labels can settle H.
- MEASURED: H replaces most of the top 30 (its v3 top 30 shares 5–10 of 30 rows with control per in-range day,
  primary `selection.json`). Per-day H − control: +3 to −4 (primary), +2 to −4 (dated). With five days, "H lowers the
  count" is a direction, not an established effect.
- This is the H "before" for c2d (TODO 0a). Use the **dated** variant's builds for c2d, and say so in c2d's
  pre-registration.
