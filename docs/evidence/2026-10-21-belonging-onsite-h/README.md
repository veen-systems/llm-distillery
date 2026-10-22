# EXP-056: belonging v3 on the LIVE H page, 7 daily top-30 personal counts (2026-10-21)

Pre-registered in `PREREGISTRATION.md` (`a01e545`, 17:12:34, before tagging started). `select.py` ran before it was
committed. `count.py` was committed (`2161463`, 17:16:07) after tagging FINISHED (17:15:45) but before any tag was
read. File times alone cannot show that order, so it rests on this session's record. $0: local qwen on b650.

## Result: v3 almost certainly FAILS the owner's bar on the live page (`count_result.txt`)

| build (14:30Z) | 10-15 | 10-16 | 10-17 | 10-18 | 10-19 | 10-20 | 10-21 |
|---|---|---|---|---|---|---|---|
| qwen `personal` in the top 30 | 7 | 8 | 8 | 9 | 7 | 8 | 8 |

- **Weekly qwen mean 7.86** against the bar of ≤ 6. Worst day 9 (10-18); best day 7 (10-15 and 10-19). All 7 builds
  have N = 30. The days overlap by 13–24 of their 30 ids: this is 101 articles (26 personal), not 7 independent draws.
- **Every day is above 6.** qwen is treated as a FLOOR: on the owner's 30 labelled rows of 10-12 (old ranking), all 3
  disagreements went one way (owner personal, qwen group), with 0 false positives on about 20 group rows
  (`docs/evidence/2026-10-12-belonging-personal-tag/README.md`).
- ⚠️ **Why "almost certainly" and not "conclusively" (review):** 0 of about 20 still allows a false-positive rate up to
  about 15% (95%). At that rate, over about 22 group rows a day, qwen could overcount by about 3 and the true mean
  could sit under 6. The floor rests on ONE 30-row calibration. **The owner's count on one of these pages would settle
  it.**
- **Not an automatic rollback** (TODO 0): v3's rollback rule predates the bar, and the call is the owner's.

## Controls

- **Determinism: 10/10** re-tagged ids match their earlier tags, so reuse stands. 23 ids were reused (from EXP-049,
  the 10-13 baseline and c2d) and 78 tagged new.
- **Presence: PASS.** No tag is unparsed; every top-30 card is `personal` or `group`.
- **Version:** all 207 distinct top-60 ids carry `belonging.version == "3.0"`, so no v1 card remains on the page.
- **Parser:** on the 10-15 T0750Z hand capture it finds 495 of EXP-049's 521 cards (fetched 07:01Z, before H went
  live at 07:40Z), with a top-30 overlap of 6 of 30: same set, H's order.

## Predictions, scored

1. Weekly mean in [4, 7]: **MISSED**, 7.86.
2. P(> 6) about 0.35: the less likely branch happened.
3. At least one day > 6: **HIT** (all 7 days).
4. All 7 builds in range: **HIT**.

The miss on 1 is informative: EXP-049's offline replay of H predicted 5.20 (dated variant), and the live page runs
2.7 above it. The replay is not a good stand-in for the live page.

## Deviations

- **§3, "under 24 h old":** the pages show a day ("· 20 Oct"), not a time, so it is not reported.
- **§2, the `api/ps` check:** done from situla at about 17:13 (`{"models":[]}`), recorded in this session only, not in a
  run log.
- **Pages:**

  `lab.py move` moves directories only, and moving `inbox/ovr-lens-pages/` would break the daily capture cron that
  writes into it.   So the 7 pages were COPIED to a staging dir and `lab.py pull`ed, hash-verified, into lab
  `experiments/2026-10-21-belonging-onsite-h/pages/`. The originals stay in the inbox.

## Data

- Lab `experiments/2026-10-21-belonging-onsite-h/{pages,run}`, both hash-verified pulls. The b650 copy
  (`~/llm-distillery/runs/exp056`) is a FINISHED run: delete it once a snapshot holds the pull (b650 rule).
- The selection inputs are lab `selection/`: `top60.json`, the sadalsuud `rows.jsonl` (version stamps + text, lab
  only), `selection.json`, `reused.json`. This was added after review, so the all-v3 claim is checkable from the lab.

## Addendum 2026-10-22: two cloud taggers beside qwen (EXP-058)

**Not pre-registered**: the owner asked on 2026-10-22 for "a different oracle to count via API", after qwen's 7.86 was
known. Same prompt (`system.txt`, byte-identical copy), same user-message shape, same 101 unique ids (the 78 freshly
tagged plus the 23 reused from EXP-049). `tag_api.py` (here; the Fable path differs from the Mistral copy only in the
docstring) and `compare_taggers.py` (output: `compare_taggers_result.txt`, which reproduces qwen's 7.86).

- **Fable**: `claude-fable-5-1`, effort low, structured JSON, no fallbacks (a fallback model would be a different
  instrument). 101 calls + 3 probe calls (the probe rows are the first 3 of the 101, not re-run). $3.60 at list
  price (303,527 in / 11,358 out), on the Anthropic promo credit (logged in infra `ai-tooling/stack.md`).
- **Mistral**: `mistral-large-4-0`, temperature 0 + top_p 1, JSON mode, reasoning ON (the reply carries thinking
  chunks). 0 unparsed. A first attempt (4 rows, list content not parsed) was deleted before the run; one 600 s
  timeout, resumed by id. Paid from Mistral's monthly API allowance.

| tagger | weekly mean (bar ≤ 6) | days > 6 |
|---|---|---|
| qwen | 7.86 | 7 of 7 |
| Fable | 7.43 | 6 of 7 (5 on 10-19) |
| Mistral | 9.14 | 7 of 7 |

Pairwise agreement on 101 ids: qwen–Fable agree 95/101, qwen–Mistral agree 94/101, Fable–Mistral agree 96/101.
Mistral is the strictest (5 ids personal where Fable says group, 0 the other way).

**Reading.** Three taggers from three model families all put v3 above the bar, so the failure is not a qwen artefact.
qwen is not a strict floor against Fable (Fable is lower on 10-19 and 10-20), but every tagger is above 6. All three
share one prompt, so a prompt that leans "personal" would move them together; only the owner's count tests that.
Data: lab `experiments/2026-10-21-belonging-onsite-h/run/{tag-fable,tag-mistral}` (written on situla directly, no
scratch host), `run/TAGGERS.md`.
