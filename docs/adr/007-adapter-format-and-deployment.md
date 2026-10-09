# ADR 007: LoRA Adapter Format and Hub Deployment

**Date**: 2026-02-19
**Status**: Accepted
**Context**: Deploying uplifting v6 (Gemma-3-1B) to HuggingFace Hub revealed incompatibilities between adapter key formats and two different loading paths.

## Problem

There are two ways to load a PEFT LoRA adapter, and they expect **different key formats**:

### Path A: Local inference (`get_peft_model` + `load_state_dict`)
Used by `inference.py` for loading from local files.

```python
model = get_peft_model(base_model, peft_config)
adapter = load_file("adapter_model.safetensors")
model.load_state_dict(adapter, strict=False)
```

Expects keys WITH `.default.` suffix:
- `base_model.model.model.layers.0.self_attn.q_proj.lora_A.default.weight`
- `base_model.model.score.modules_to_save.default.weight`

### Path B: Hub inference (`PeftModel.from_pretrained`)
Used by `inference_hub.py` for loading from HuggingFace Hub.

```python
model = PeftModel.from_pretrained(base_model, repo_id)
```

Expects keys WITHOUT `.default.` suffix (PEFT adds it internally):
- `base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight`
- `base_model.model.score.weight`

### Additional issue: Gemma-3-1B Auto mapping

`google/gemma-3-1b-pt` uses `Gemma3TextConfig` (model_type `gemma3_text`), but `AutoModelForSequenceClassification` only maps `gemma3` (multimodal). Loading via Auto fails with a `ValueError` about unrecognized config class.

## Decision

1. **Keep adapters in OLD format** (without `.default.`). This is the format produced by training. Do NOT resave adapters before Hub upload.

2. **Local `inference.py` handles remapping at load time**. It detects the key format and adds `.default.` as needed for `load_state_dict`.

3. **Use `filters/common/model_loading.py`** instead of `AutoModelForSequenceClassification` directly. The `load_base_model_for_seq_cls()` function tries Auto first and falls back to a manual `Gemma3TextForSequenceClassification` construction.

4. **Upload script verifies Hub loading** after upload. If `PeftModel.from_pretrained()` fails, it warns before the developer walks away.

## Consequences

- `resave_adapter.py` has a warning and confirmation prompt — it's only for local-only edge cases
- All Gemma-3-1B filters must import from `filters.common.model_loading` instead of using Auto directly
- Adapter files in git/Hub should always be in the original training output format
- Two slightly different score values between local and Hub inference (~0.03 difference) are expected due to different loading paths

## Deployment Checklist

When deploying a new filter to HuggingFace Hub:

1. Do NOT run `resave_adapter.py`
2. Write a proper `model/README.md` <!-- placeholder --> (not the PEFT template)
3. Use `load_base_model_for_seq_cls()` in both `inference.py` and `inference_hub.py`
4. Run `upload_to_huggingface.py` — it will verify Hub loading automatically
5. Run `inference_hub.py` to confirm scores match local inference
