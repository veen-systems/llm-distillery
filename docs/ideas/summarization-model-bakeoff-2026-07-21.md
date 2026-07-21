# Local summarization model bake-off (2026-07-21)

**Question:** gpu-server runs ovr.news summaries on `gemma3:27b`, which spills ~20% of
layers onto CPU on the 16 GB card (`num_ctx 8192` → ~20 GB, 20/80 CPU/GPU). Can a model
that fits **fully** on the GPU beat it?

**Verdict: yes — on the trade, not on raw quality.** The 27B is still the most faithful
summarizer, but **`gpt-oss:20b` lands within ~0.5 quality points at 9.2× the throughput**,
fully on-GPU. Giving up ~7% quality for 9× speed on the ~40-min-every-4h summarize job is a
strong deal. `qwen3:14b` is out — it leaked Chinese script into English output.

> **This is an ovr.news decision** (the summarizer + `ollamaConfig.model` live in
> `ovr.news/src/lib/summarization.ts` / `config.ts`). Recorded here because the A/B was
> run from llm-distillery.

## Results

| Model | Quality | Faithful | English | Complete | tok/s | ×27B | GPU fit | Leaks |
|---|--:|--:|--:|--:|--:|--:|---|--:|
| `gemma3:27b` (baseline) | **8.17** | 8.17 | 9.33 | 8.28 | 15.6 | 1.0× | 20 GB · 20/80 | 0 |
| **`gpt-oss:20b`** (best trade) | 7.61 | 7.89 | 8.50 | **8.67** | **142.9** | **9.2×** | 14 GB · 100% | 2 |
| `gemma3:12b` | 7.33 | 7.78 | 8.83 | 8.00 | 71.5 | 4.6× | 10 GB · 100% | 1 |
| `qwen3:14b` | 6.56 | 6.72 | 8.11 | 8.06 | 64.8 | 4.2× | 10 GB · 100% | 3 |

Quality columns = means across 3 judges × 6 articles (0–10). **Leaks** = judge-scorings where
source-language text leaked into English output (english ≤ 3). tok/s + GPU fit measured live on
gpu-server via Ollama.

```
quality
 8.5 ┤
 8.0 ┤ ● gemma3:27b (15.6 t/s)  ·············· 27B quality ceiling ···
 7.5 ┤                                              ◆ gpt-oss:20b (142.9 t/s)
 7.0 ┤              ● gemma3:12b (71.5)
 6.5 ┤            ⊗ qwen3:14b (64.8, leak)
 6.0 ┼────┬────┬────┬────┬────┬────┬────┬────┬
      0   20   40   60   80  100  120  140   tok/s
```
Up-and-to-the-right wins. gpt-oss:20b sits closest to the 27B's quality line while being
fastest by far. All three challengers fit 100% on GPU; the 27B pays the CPU-offload tax.

## What each model did

- **`gemma3:27b`** — the quality ceiling: most faithful, cleanest English, zero leaks. But the
  ~20% CPU offload is the entire reason it crawls at 15.6 tok/s. Great summaries, slow + GPU-hungry.
- **`gpt-oss:20b`** — pragmatic winner. 20B that fits fully on GPU (MXFP4, 14 GB) and beats the
  27B on *completeness*, within ~0.5 overall. One caveat: left the Polish word "Wójt" untranslated
  in one summary (2 of 3 judges flagged) — not a hard blocker, worth watching.
- **`gemma3:12b`** — safe same-family option; slightly cleaner English than gpt-oss, thinner on
  completeness. Reasonable drop-in if you want to stay on Gemma / keep stylistic continuity.
- **`qwen3:14b`** — OUT. Embedded raw Chinese characters (院士, 院士大会) in the English summary and
  garbled proper names; all three judges caught it independently. "Multilingual" ≠ clean English-only.

## Method

- **Faithful generation** — every model ran the *actual* production prompt (reconstructed
  `getBrandVoicePrompt`: 150–200 words, English-only, `num_ctx 8192`, temp 0.7), not a generic one.
- **Real content** — 6 genuine non-English feed articles (es/fr/de/zh-cn/pl/vi), matching
  production's ~29% non-EN mix, incl. a CJK stress test.
- **Blind, in-session panel** — summaries shuffled to A–D per article; Opus 4.8 / Sonnet 5 /
  Fable 5 scored each against the original-language source without knowing the model. Agreement was
  tight (27B: 8.3/8.0/8.2) and all three flagged the same leak + hallucinations → the blinding held.
- Artifacts: `gen_ab.py` (generation harness) + the blinded judge inputs were run from the session
  scratchpad; raw results in `ab_results.json` (gpu-server / session scratch, not committed).

## Caveats & follow-ups

- **Small sample** — n=6, one generation each (temp 0.7 → variance). The ~0.5 quality gap is real
  but not bankable to a decimal; the 9.2× speed gap + the leak findings are robust.
- **Re-run if `summaryMaxWords` changes (ovr.news)** — word count moves both axes: longer output
  slows the offloaded 27B disproportionately and can change which model holds coherence at length.
  Today's numbers are at 150–200 words.
- **Not a regression to zero** — gpt-oss:20b and gemma3:12b both clear the bar of usable, faithful
  English summaries; the choice is throughput vs. the last ~7% of quality.
- Context: the earlier "5.8 GB VRAM phantom" that worsened 27B offload was **student GPU jobs, now
  gone** — but the 27B still offloads ~19–20% because 19–20 GB > 16 GB regardless.
