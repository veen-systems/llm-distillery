# Scaleway (EU) as an oracle host — trial, 2026-10-19

**Answer: DeepSeek V4.1 Flash on Scaleway, with `reasoning_effort: "none"`, agrees with our DeepSeek-API oracle
on human_thriving's 100-item canary set as closely as that oracle agrees with itself:** 4 flips at 4.5, shift
+0.02, which PASSES the canary's clean-run bar (flips > 5 + 1 or |shift| > 0.069 + 0.15 fails). Mistral Medium 3.5
does not: 21 flips, shift +0.51, and 80 of its 172 calls returned an empty `{}`.

⚠️ **Not pre-registered.** Owner 2026-10-19 asked for "an EU-hosted oracle trial" alongside the canary rollout; the
runs were started before a pre-registration was written, so this is a DESCRIPTION with no decision rule, not a
verdict. Every measured figure and the cost arithmetic are in `result.txt`, recomputed from the lab copies by
`analyse.py`.

Key and credit: the `sovereignstack-experiments` Scaleway project's (infra session; owner approved there and in
this session, 2026-10-19). Data: lab `experiments/2026-10-19-scaleway-oracle-trial/raw/` (`_LAB_MANIFEST.json`):
`scw_probe.py` / `scw_set_run.py` (the request is `score_deepseek_production.call_deepseek`'s: same prompt build,
temperature 0.3, max_tokens 4096, JSON mode) and their outputs.

## What was measured (`result.txt`)

| | DeepSeek V4.1 Flash, thinking off | Mistral Medium 3.5 (128b) |
|---|---|---|
| items scored / 100 | 100 | 84 (after resume passes) |
| flips at 4.5 vs the DeepSeek-API baseline | 4 | 21 |
| mean shift | +0.0212 | +0.5061 |
| median / max \|Δ\| | 0.13 / 1.17 | 0.80 / 4.68 |
| items ≥ 4.5 (model / baseline, same items) | 32 / 30 | 38 / 23 |
| failed calls | 2 × HTTP 429 | 80 × `{}`, 3 × bad JSON, 5 × HTTP 429 |
| input tokens cached | 1,013,824 of 1,212,380 | 0 reported (`prompt_tokens_details` null) |

- **Thinking switch (probe, one article each):** `reasoning_effort: "none"` → 0 reasoning tokens, and 0 on every one
  of the 106 successful calls made with it. `"low"`, `chat_template_kwargs.enable_thinking=false` and
  `thinking: {type: disabled}` all still reasoned (1,296 / 1,944 / 1,779 reasoning tokens). Thinking ON: 2 of 5
  articles spent the whole 4,096-token budget on reasoning and returned no content.
- **Provenance:** the response `model` field names the requested model (#157's `served_model` stamp works);
  `system_fingerprint` is null on every successful call.
- **Model ids:** `mistral-medium-3.5` is 422 (not found); the id is `mistral-medium-3.5-128b`. `/v1/models` also
  lists **`deepseek-v4-flash-0731`, a dated V4 snapshot** (listing saved after the runs, lab `models/`) — a pinned id of the kind #157 found DeepSeek's own API
  does not offer.
- **Rate limit:** HTTP 429 `INSUFFICIENT QUOTA … organization quota` at 4 concurrent workers; retries cleared most.

## What it does NOT show

- **Agreement is not identity.** Same weights, quantisation and pinning of `deepseek-v4.1-flash` are unknown (infra,
  2026-10-19); a canary PASS says the scores agree on this set, not that the model is the same.
- **One run per model, one prompt.** The bar was built from the DeepSeek API's own B1–B6 noise; Scaleway's
  run-to-run noise is unmeasured, and human_thriving is the only prompt tried.
- **Cost is an ESTIMATE**: ≈ €2.31 for all 298 calls at €0.60 in / €1.80 out per M (infra's reading of Scaleway's
  list, not re-checked; Mistral's price unknown, costed the same), with NO cache discount. Whether cached input is
  billed lower is unknown; without it, a 100-item canary costs ≈ €0.78 ≈ $0.91 here (at an assumed 1.16 USD/EUR)
  against about $0.03 on DeepSeek's API (EXP-052's README) — about 30× per canary. The bill: `scw billing
  consumption list` (infra's project).
- **#174 is not answered.** Infra's desk read of Scaleway's terms (zero retention by default, no training on inputs,
  not subject to the CLOUD Act) says nothing about training on OUTPUTS. DeepSeek's licence terms for the weights
  still apply whoever hosts them — unread.
- **Switching would be a new oracle key**: every canary baseline would be rebuilt on it (`canary.py` refuses another
  oracle by design), and `score_deepseek_production.py` has no way to send `reasoning_effort` today.
