# The adverse-pool consult — three findings, $0, and a review that corrected all three (2026-09-09)

⛔ **Headline, in the form that survived review: `human_thriving v8`'s labelled corpus cannot
exhibit the student/oracle DISAGREEMENT that v9 and #156 must learn — because its labels are the
oracle's own output.** `harm_is_subject` is **1,253** rows and **not one reaches
`weighted_mean_all` 4.0** (max **2.7667**); **all 316 rows at or above the 4.50 op-point are
`in_scope`**, asserted not printed.

⛔ **The stronger absolute I first published — "zero examples and CANNOT have any" — is FALSE and
was refuted by this repo's own review.** The corpus's per-run votes contain the shape: **1 row at
5.367** carries a `harm_is_subject` run-vote with an `in_scope` final verdict, **178** rows carry
≥1 harm run-vote with a non-harm final verdict, **1,079** are `scope_flipped`, and **178**
`harm_is_subject` rows have split run votes. That is a **$0 route** the first write-up foreclosed
by declaring a production pool "the only" one. It is not.

Reproduce: `python3 docs/evidence/2026-09-09-adverse-pool-consult/analyze.py`
(committed output `analyze.txt`). No oracle calls, no network.

## ⛔ Read this before quoting any number below

| trap | what it means here |
|---|---|
| **The aggregate is DECLARED, not chosen.** | Every row carries `aggregate_used`, `"all"` on **6,586/6,586**, so the score is `weighted_mean_all`. The first version of `analyze.py` preferred `weighted_mean_major` with a fallback and published **351 / 5.3%**; the declared aggregate gives **316 / 4.798%**. Asserted uniform at load. |
| **Part B's input is GITIGNORED.** | `datasets/*` (`.gitignore:83`), so `labels_v84_merged.jsonl` is in no clone. Pinned `sha256 b085b01b07d835eff93f3507e1dad940de594c4e7edcf14fcd2dda8a990d614c` and asserted; a clean checkout gets an error, not a wrong number. **Part A and C inputs ARE committed.** |
| **Every share is a SAMPLE share unless marked.** | The corpus is a 6,586-row subset of the 6,590-row stratified draw in `corpus.jsonl`, `inclusion_probability` spanning **25.132×**. Both are printed: `harm_is_subject` **19.03% unweighted / 20.96% design-weighted**; above-op **4.798% / 2.709%**. Counts, maxima and zeros are weight-invariant. |
| **The op-point is on the CALIBRATED scale; these labels are not.** | 4.50 comes from `base_scorer.py`'s `TIER_THRESHOLDS`, read by **executing** it. `weighted_mean_all` is an uncalibrated oracle mean, and `docs/decisions/2026-09-05-v8-op-point.md` measures 4.5-calibrated as the stricter bar (17 test rows vs 26 raw). **Every count here is a raw-scale count and is the more permissive of the two.** |
| **The 300-char minimum is an EXCLUSION.** | The #93 labelling-time floor in `ground_truth.batch_scorer.make_oracle_prefilter`. Sub-300-char rows are absent by construction. |

## A. κ 0.375 is the wrong statistic — but the κ *rescue* does not work either

The panel's headline disagreement is the **4-class** κ **0.3753** (76/137 agreements). ⛔ **The
binary-`harmful` κ is 0.3749 — indistinguishable.** Saying "that's the 4-class figure" implies the
binary one is better. It is not. **The screen argument rests entirely on NESTING, not on κ.**

| | DeepSeek k=3 | Gemini k=1 | overlap | DeepSeek-only |
|---|---|---|---|---|
| `harmful` | 9 | 32 | 9 | **0** |

⭐ **And it nests within every stratum** — v7_only 2⊂14, both 3⊂8, v8_only 4⊂10, zero reversals in
each. Pooling is not hiding one. Not boundary flutter either: of the 23 Gemini-only-harmful rows,
DeepSeek cast ≥1 harmful vote out of 3 on only **3** (asserted).

⚠️ **Two limits on "recall-safe", both now printed:**
- **P = 7.83e-07 tests the wrong null.** It is independence between two judges reading the same
  137 articles — guaranteed false. Rejecting it establishes **correlation, not screen safety**.
- **Screen safety is 0 misses in 9.** Rule-of-three 95% upper bound on the miss rate = **33%**.
  "Recall-safe" is **bounded, not shown**.

Staged cost **on this panel**: 32/137 = **23.4%** reach the k=3 arm. ⚠️ That is a stratified panel
of two lenses' display-eligible rows; transferring it to a 4,698-row long-only production pool is
an assumption. Design-weighting barely moves it (22.9%), but the nearer anchor for a v8-shaped pool
is `v8_only`'s own **27.0%**.

## B. The corpus cannot exhibit the disagreement — and the above-op population is one prompt arm

| | value |
|---|---|
| `harm_is_subject` | **1,253** — 19.03% unweighted, **20.96% design-weighted** |
| max `weighted_mean_all` among them | **2.7667** |
| `harm_is_subject` rows at ≥ 4.0 | **0** (asserted) |
| rows at or above 4.50 | **316** — 4.798% unweighted, **2.709% design-weighted** |
| their `scope_verdict` | **`in_scope`: 316**, nothing else (asserted) |

⛔ **The confound, and it is large.** The above-op population is **not a corpus rate**:

| prompt | file | n | above-op |
|---|---|---|---|
| `003cd35a5122` | `prompt-candidate-tail.md` | 6,130 | **0 = 0.00%** |
| `c4705408c477` | `prompt-v8-4.md` | 456 | **316 = 69.30%** |

**All 316 come from the 456-row minority arm, which was itself selected for being above-op under an
earlier pass.** The 6,130-row majority arm has **zero**. And `H-V8-30` measured that this exact
prompt swap moves `in_scope` by **+0.1774** (McNemar p=0.0034) — it moves the very variable being
cross-tabulated. So "all rows above the op-point are `in_scope`" is substantially a property of a
deliberately-selected relabel census, restated.

**What survives all of that** (verified under every aggregate definition, and weight-invariant):
no `harm_is_subject` row reaches 4.0, and no row at or above the op-point carries any verdict but
`in_scope`. The defensible conclusion is the narrow one: **the corpus's FINAL LABELS cannot exhibit
student/oracle disagreement, because they ARE the oracle's output** — not that no route exists.

⛔ **Routes that are NOT foreclosed, and were wrongly foreclosed in the first draft:**
1. **Per-run scope disagreement, $0.** 178 rows with ≥1 harm run-vote and a non-harm final verdict;
   1 of them above the op-point; 178 `harm_is_subject` rows with split run votes; 1,079
   `scope_flipped`. `analyze.py`'s first version never read these fields.
2. **A detector trained on the existing labels, $0.** #156's positive class is (article, harm
   label) — 1,011 / 105 / 137 across the splits — and evaluating it against EXP-031's 9/32
   judge-flagged rows costs nothing. That arm was never costed before the pool was called "the only
   route".

The production pool remains the only route to *student*/oracle disagreement specifically. That is a
narrower claim than the one first published, and it is the one to act on.

⚠️ **The harm stratum is 39.74% English against 52.47% corpus-wide.** That is the SUPPLY of harm
content per language in a labelled corpus, **not** an error-rate signal, and not a prior about
where the student fails. Recorded because it was offered as one, in this session, by me.

## C. The `fits` clause leaks something — but the pooled effect is SUBSTANTIALLY COMPOSITION

Mechanism, from `judge.py`'s `RUBRIC`: *"If you cannot name who is better off and how, it is not
`fits`."* Pooled (English 78 / non-English 59):

| judge | `fits` en→non-en | `misleading` en→non-en | `harmful` |
|---|---|---|---|
| DeepSeek k=3 | 37.2% → 22.0% (−15.1pp) | 37.2% → 49.2% (+12.0pp) | 7.7% (6) → 5.1% (3) — flat |
| Gemini k=1 | 46.2% → 33.9% (−12.3pp) | 26.9% → 42.4% (+15.4pp) | 24.4% (19) → 22.0% (13) — flat |

⛔ **Within stratum the sign REVERSES, under both judges:**

| stratum | n | English | DeepSeek `fits` Δ | Gemini `fits` Δ |
|---|---|---|---|---|
| v7_only | 60 | 45.0% | −7.1pp | −2.4pp |
| both | 40 | 70.0% | **−40.5pp** | **−39.3pp** |
| v8_only | 37 | 62.2% | **+12.4pp** | **+13.7pp** |

The panel is stratified and English share varies with stratum, so *"both families, same direction,
same rows"* **does not survive the panel's own design variable**. `H-AP1` stays OPEN and its method
must stratify. The `harmful` flatness is also weak — **6 vs 3 rows** on the DeepSeek arm.

⛔ **DeepSeek's k=3 split-vote rate is 43.1% (59/137), not 45.8%.** 45.8% is the **non-English**
rate (41.0% English). The first draft cited it as the judge's rate — in an entry whose own subject
is borrowing a floor across populations.

## What this does NOT establish

- **What either lens MISSES.** Every population here is selected on having been surfaced or
  labelled. No recall claim is valid.
- **Absolute harm levels** — unchanged from EXP-031; the judges differ ~3× on the same articles.
- **That the fluency shift is the judge rather than the content**, and after §C's stratum
  breakdown, not even that the pooled shift is real. `H-AP1`'s three-arm control has not run.
- **A production harm rate.** Nothing here reads the NexusMind pool; no number in it is quoted.
- ⚠️ **That EXP-031 is unrecoverable.** `panel_frame.jsonl` carries no `content` field (0 of 137),
  so the panel cannot be replayed **from this directory**. `NexusMind/config/app.yaml` sets
  `archive_retention_days: 730`, and EXP-030's registry entry names the four source
  `filtered_*.jsonl` files — **the archive was never checked.** Scope the claim to this repo.

## Files

`analyze.py` · `analyze.txt` (committed output) · this README.
Registry entry: `EXP-032`. Issues: llm-distillery#150, #156, #91, #125.
Review: four lenses, 2026-09-09 — **5 blockers, 8 warnings**, all folded in above.
