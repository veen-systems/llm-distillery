# H-V8-8 — the prefix cache survives 90 minutes. The "repeat discount" does not exist for a corpus pass.

**2026-08-29, four passes 20:27 → 21:58. Spend $0.1044** (200 DeepSeek calls, 0 errors). No
model, no threshold, no probe, nothing in `filters/`, nothing deployed. Design fixed in
[`PREREGISTRATION.md`](PREREGISTRATION.md) **before the calls**, including the revision-2 rewrite
after the first attempt was found confounded.

## Answer, in two parts

1. ✅ **The shared prompt prefix survives at least 90 minutes of inactivity.** Every row of every
   pass hit **exactly 10,368 tokens** — the whole prefix — with **zero cold-prefix rows** across
   200 calls at four lags.
2. ⛔⛔ **But the "repeat discount" the corpus cost was built on is an ARTEFACT, and it does not
   apply to a corpus pass at all.** Phase A measured runs 2–3 at **$0.000266/article** and
   concluded k=3 would cost ≈$6.92. Those runs re-scored **the same 200 articles**, so the whole
   request came back from cache. **A corpus pass scores 6,590 different articles every time**:
   the prefix is cached, each article's own tokens are not. Measured here on articles never
   before sent to any oracle: **$0.000506–$0.000534 per article, per pass, flat across all four
   lags.**

| pass | lag | rows | hit rate | hit tokens | miss tokens (min/med/max) | cold-prefix rows | $/article |
|---|---|---|---|---|---|---|---|
| Q0 | t+0 | 50 | 89.4% | 10,368 (every row) | 661 / 1,216 / 2,390 | **0** | $0.000506 |
| Q1 | t+30 min | 50 | 88.7% | 10,368 (every row) | 712 / 1,238 / 2,629 | **0** | $0.000534 |
| Q2 | t+60 min | 50 | 88.9% | 10,368 (every row) | 703 / 1,149 / 2,818 | **0** | $0.000533 |
| Q3 | t+90 min | 50 | 89.4% | 10,368 (every row) | 673 / 1,116 / 2,450 | **0** | $0.000515 |

⭐ **The per-row discriminator is what makes this readable**, and it was pre-registered: a
prefix-only hit shows `hit == the prefix` and `miss == this article's own tokens`; a
whole-request hit shows `miss ≈ 0`. Every row here is the first kind. **`hit` has zero variance
— min equals max on all 200 calls — while `miss` tracks article length.** That is the shape of
prefix caching and nothing else.

## What it costs, corrected

| | per pass, 6,590 rows | k=3 |
|---|---|---|
| **reordered prompt** (measured here) | **$3.44** | **$10.32** |
| as-is prompt | $18.03 | $54.08 |

⚠️ **$10.32, not the $6.92 this project has been quoting** — and it lands on the figure Phase A
already printed as its *no-discount* branch ($10.27). The two arms of that estimate were "with
the repeat discount" and "without"; **"without" is the one that describes a corpus run.** The
as-is prompt puts the article near the front, so its prefix is broken by construction — it
measured 0.0% cache on a first pass and 99.5% only when re-sent the same articles.

**The reorder is 5.2× cheaper at corpus scale, measured rather than assumed** ($10.32 vs
$54.08 at k=3). ⚠️ That is a cost argument only; whether the reorder's *labels* are better is
H-V8-9, answered separately.

## The first attempt was confounded, and the review that caught it is the point

Revision 1 drew its four sets from the **Phase A cohort** — 200 articles that had been through
this exact prompt three times the day before. Its 99.5% hit rate was whole-request reuse, which
a corpus pass never gets. The tell was in the per-row usage: a row with 3,619 characters showed
`hit 11,776` against a **10,368-token prefix** — the hit exceeded the prefix, so article text
was cached too. ⛔ **The run was killed after one pass rather than left to produce three more
confounded points**, and the observation that the prefix "survived 77.9 minutes" was withdrawn
as under-determined: a 28-hour-old whole-request cache explained it equally well.

Revision 2 draws from the v8 corpus assembled the same evening — 6,590 articles, **none ever
sent to any oracle under any v8 prompt** (the 11 overlapping the Phase A cohort and the
no-regression set were removed explicitly).

## Predictions, scored

| prediction | outcome |
|---|---|
| Q0 60–85% (cold prefix, fresh articles) | **89.4% — missed high.** The prefix was already warm from the killed run 54 min earlier, so Q0 is not a cold start either. It does not affect the finding: the question is whether the prefix survives a *gap*, and three independent gaps (54, 78, 30/60/90 min) all show it does. |
| Q1–Q3 ≥85% if the TTL exceeds 90 min | **88.7 / 88.9 / 89.4% — hit.** |
| a decaying rate would put the TTL inside a corpus pass | **not observed.** Flat to within 0.7pp. |

## Limits

- **One prompt, one prefix, one account, one evening.** DeepSeek publishes no TTL guarantee and
  this measures behaviour, not a contract. A 90-minute floor is what was tested; nothing here
  says what happens at 6 hours.
- **The operative question turned out to be easier than the hypothesis assumed.** A corpus pass
  *calls continuously*, so its prefix never goes idle for 30 minutes in the first place. The TTL
  only has to cover the gap *between* passes — and if k=3 is scheduled as three back-to-back
  calls per article (the ledger's own alternative), it does not have to cover anything.
- **Prices are DeepSeek off-peak** at the rates in `memory/oracle-pricing-scheduling.md`.
  Weekends bill off-peak; a weekday-peak corpus run costs more.

## Reproduce

```bash
python3 docs/evidence/2026-08-29-v8-cache-ttl/analyse_ttl.py <dir with Q0..Q3_out.jsonl>
```

✅ The four 50-row inputs and outputs are staged at
`b650-gpu:~/v8_corpus/experiment_inputs/cache_ttl/` (2026-08-30, verified by sha256), with the
run log and the runner. They are not in this repo — they are full article text. Failing that,
they regenerate for ~$0.10 from any 200 unscored rows of the staged corpus.
