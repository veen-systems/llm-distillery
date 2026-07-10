# External Papers

External papers we've read and decided to keep around for context. Not a literature review — see `docs/articles/` for written-up arguments.

Each entry: filename, one-line topic, and the verdict for *this* project (not a generic summary).

---

## kataiwa-2025-intrinsic-dim-token-embeddings.pdf

Kataiwa, Hakaze & Ohki (2025), "Measuring Intrinsic Dimension of Token Embeddings" — arXiv:2503.02142.

**Topic:** Intrinsic dimension (ID) of token embedding layers in Word2Vec/GloVe/FastText (ED=300, ID≈10-30) and Pythia 14M-12B (ID≈25-122, 90-98% redundancy). LoRA applied *to the embedding layer only* shows a sharp perplexity drop around ID, suggesting ID as a rank guideline.

**Verdict for llm-distillery: file as theoretical backing, not actionable.**

- Their LoRA-rank guideline does **not** transfer to our setup — they LoRA-adapt the embedding layer; we adapt attention/MLP + classification head. Different geometry, no parameter change implied.
- Their 300-dim word-embedding result (ID 10-30) is the closest analogue to our e5-small screening probe (384-dim). A PCA-reduce-to-~30-dims experiment on e5-small embeddings was considered and parked: probe latency is not a felt bottleneck (2026-05-29).
- Useful as a citation if an ADR ever needs to justify *why* low-rank distillation is geometrically sound at all.

Nothing here touches calibration, normalization, oracle scoring, prefilters, or NexusMind production scoring.
