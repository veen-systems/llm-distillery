# 2026-08-24 evening → 08-25 — the ledger settled, and #103 was measuring a price we cannot pay

**No spend. No model. No deploy.** Two threads: the block ledger's second flush (the one
number yesterday's session was blocked on), and llm-distillery#103, the DeepSeek
price-rise issue, which the owner asked me to check while waiting for it.

Started at *"where were we?"* again, so again the first act was reading state.

---

## 1. ✅ H-AR12 REFUTED — the ledger is fine, and the growth risk was not real

Second flush landed **17:04** (the cycle fires 16:02 and the ledger writes ~66 min in):
**3,257 rows / 6.72 MB**, against the first flush's 168,486 rows / 320 MB. The written-id
index works. `verify_block_ledger.py` exits **0**: 2 files, **171,743 rows**, all conformant
to `article-record.schema.json v0.4.0`.

**Reconciled against a different instrument**, the pipeline's own log line:

```
Block ledger: 3257 new blocked articles written (3169 with content), 165308 already recorded
168,486 + 3,257 = 171,743  = the verifier's row count
168,486 - 165,308 = 3,178  = ledger rows that aged out of this cycle's window
```

**Steady state ≈ 3.3K rows / 6.7 MB per cycle ⇒ ~20K rows / ~40 MB per day** at 6 cycles —
not the 1.9 GB/day worst case. The 320 MB was the standing backlog, one-time. Ledger stays
enabled; NM#403's off-site backup is affordable as-is (commented there with the table).

⚠️ **`freshness.too_old` is 87.6% of the increment** (2,852 of 3,257) — H-AR11's shape
holds at the margin, so any sizing that models the ledger as "gate-blocked articles" is
wrong by ~8× at steady state too, not just in the backlog.

⚠️ **The unbounded thing is the INDEX, not the ledger.** `.ledger_index.json` grew
12.36 → 12.59 MB for 3,257 ids ≈ **73.5 bytes/id ⇒ ~1.4 MB/day**, nothing prunes it, and it
still sits where cleanup sweeps — surviving only because the glob is `*.jsonl` and it is
`.json`. That is the thing to watch now.

⚠️ `placements per row` is now **`{6: 171741, 3: 1, 1: 1}`** — a *second* singleton appeared
at the second flush. Two distinct anomalies, each n=1. Still not diagnosable; no longer a
single stray.

## 2. ⛔⛔ #103: three days of arithmetic against a price we cannot pay

**There is no Gemini Batch API call site in this repo.** `ground_truth/batch_scorer.py:819`
and `scripts/score_ollama_oracle.py:266` both call `models.generate_content` — the
**real-time** endpoint — and `.batches` appears in no `.py` file in the tree. The
`~$0.0018/article` "Gemini Batch" figure that every comparison since 2026-08-16 was measured
against was an **unanchored planning number for an integration that does not exist**.

Against the Gemini path that exists:

| prompt (measured) | I/O | DeepSeek off-peak | Gemini Batch *(no call site)* | Gemini realtime *(implemented)* |
|---|---|---|---|---|
| nature_recovery v3, n=3,641 | 30.6 | 0.001442 | 0.001175 | 0.002350 |
| uplifting v7 | 19.9 | **0.001756** | 0.001526 | 0.003052 |
| human_thriving v8r3 | 42.8 | 0.002675 | 0.002127 | 0.004255 |

**DeepSeek off-peak is 1.74× cheaper than the oracle we can invoke. The cd v5
DeepSeek-as-default precedent is NOT void.**

⭐⭐ **The lesson is [[feedback-verify-call-path]] in a new costume: the PRICE was verified
three times over, the ABILITY TO OBTAIN IT never once.** Both rate cards were re-read
first-hand at the vendors; an outside commenter checked our arithmetic; the flip point was
computed to four decimals. Nobody grepped for the call site. **A number can be correct,
independently confirmed, and still not be a price you can pay.**

## 3. The anchor was measurable all along, and could never have decided it

#103 argued for three days over two figures **back-solved from invoice totals** under an
assumed input shape. ⭐ **A residual inherits the full error of every term subtracted from
it** — a 19% error in the assumed input wipes out more than half the estimated output
length. Meanwhile `datasets/scored/nr_v4_batch.log` had been on disk since **2026-07-07**
with the counts: **3,641 articles, 5,986 input / 195.9 output tokens per article, 0.34%
cache**, and its own `$3.24` line reconciles to the cent against the old rate card.

⭐⭐ **And it did not matter.** The crossover is a **ratio**: DeepSeek off-peak wins only
when **I/O < 8.4** (< 14.7 even at 14% cache). Every prompt we run measures **I/O = 20–43**.
No plausible output length reaches it. **Everyone was arguing about a parameter that could
not change the answer, while the parameter that could — whether the cheaper endpoint is
callable at all — went unexamined because it was not a number.**

## 4. The cache rate is structural (#131)

`build_prompt` substitutes the article **into the middle** of the template, so a prefix
cache can only hit what precedes the placeholder. That share is a per-prompt constant —
its **ceiling**: `human_thriving/v8` 1.5%, `uplifting/v7` 2.6%, `cultural_discovery/v5`
**16.9%**, `solutions/v6` **35.7%**.

⭐ **So the "14% cache hit" this project carried as a constant is cd v5's own ceiling**, and
`nature_recovery` measures 0.34% against its 3.2%. Each shape flips the DeepSeek/Gemini-Batch
ranking at **19–27%** cache; 32.9% flips it at any shape. Reordering to ~97% would put
`uplifting v7` at **$2.59 per 8K retrain** against $14.04 — a bigger lever than the vendor
choice, the peak windows and the weekend rule combined. ⛔ **It is a different prompt**
(ADR-010), so #131 carries a parity experiment, not a refactor.

## 5. ⛔ Four of my own

1. ⭐⭐ **The shipped artifact was broken and I had verified the working copy.** `oracle_cost.py`
   exits **1** on a clean clone: `datasets/` is gitignored (`.gitignore:76`, and #97 is why),
   so the log the whole analysis rests on was not in the repo. Found by self-review, not by
   running it. Fixed by copying both logs (counters only — no article text) to
   `docs/evidence/` and proving the clean clone now exits **0**.
   [[feedback-verified-artifact-is-the-shipped-one]].
2. ⛔ **I asserted "0% cache (measured)" from a dead field** — `score_ollama_oracle.py:359`
   reads `prompt_cache_hit_tokens` into `_cached_tokens` and then never sums it, never
   persists it, never prints it. The run logs carry no cache line at all. It lands near-right
   only by luck; what makes 0.34% believable is a *different* log whose instrument can report
   non-zero and did (1% mid-run).
3. ⛔ **"n=45 articles, k=3" was n=15 articles, k=3** = 45 calls — and those 15 are a
   hand-picked adversarial sample (median 3,482 chars vs production's 1,349), so their
   absolute $/article are upper bounds. [[feedback-hand-built-population]].
4. ⛔ **I wrote `#131` into a public comment before filing it** — the same error as
   yesterday's `#125`-that-was-`#130`, one session later. It happened to land on 131. **A
   guess that comes true is not a method**; file first, then cite.

## 6. Also worth keeping

⚠️ **A mid-run cache reading is not a run cache rate.** `nr_v4_positives.log` decays
**14% → 7% → 5%** across its progress lines to a 4.9% total — the likeliest origin of the
"14%" this project carried for months.

⚠️ **The file names say v4; the runs are v3.** `nr_v4_batch.log` reads
`nr_v3_batch_input.jsonl` → `nature_recovery_v3_deepseek.jsonl`.

## Next session

1. **🅑b populate the register** — unblocked, instrument fixed 08-24. Classify the **20
   undeclared** NexusMind fields in `docs/article_record_status.yaml`, then join + render
   behind `stamp_census.py --emit-register`. ⛔ Quote no field count without its window.
2. **🅒 migration step 3** — free, no external reader: hoist the 13 lens fields measured
   identical on all 2,495 multi-lens articles. Three more are invariant only because the
   *value* is constant and must **not** be hoisted.
3. **#123 the index-budget guard** is acute — four options are in the issue awaiting a call.
4. Not urgent: `.ledger_index.json` off the cleanup path; the two `placements` singletons.
