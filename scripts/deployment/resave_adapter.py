"""
Resave LoRA adapter in current PEFT format.

WARNING: This script is for LOCAL inference compatibility only!
Do NOT run this before uploading to HuggingFace Hub.

PeftModel.from_pretrained() (used by Hub inference) expects the ORIGINAL
key format (.lora_A.weight, score.weight) and handles remapping internally.
Resaving to the new format (.lora_A.default.weight) will BREAK Hub loading.

See ADR-007 for details on the two loading paths and their format requirements.

If you need Hub-compatible loading, use the original training output directly.
Local inference.py handles key remapping at load time for either format.

Usage (for LOCAL inference fixes only):
    python scripts/deployment/resave_adapter.py --filter filters/sustainability_technology/v1
    python scripts/deployment/resave_adapter.py --filter filters/uplifting/v7
"""

import argparse
import shutil
from pathlib import Path

import torch
from transformers import AutoTokenizer
from peft import PeftConfig, get_peft_model, PeftModel
from safetensors.torch import load_file

from filters.common.model_loading import load_base_model_for_seq_cls


def get_dimension_count(filter_path: Path) -> int:
    """Get number of dimensions from config.yaml."""
    import yaml
    config_path = filter_path / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return len(config["scoring"]["dimensions"])


def resave_adapter(filter_path: Path, backup: bool = True) -> bool:
    """
    Load adapter with key remapping and resave in current PEFT format.

    Args:
        filter_path: Path to filter directory (e.g., filters/sustainability_technology/v1)
        backup: Whether to backup original model directory

    Returns:
        True if successful, False otherwise
    """
    model_path = filter_path / "model"
    adapter_path = model_path / "adapter_model.safetensors"

    if not model_path.exists():
        print(f"Error: Model directory not found: {model_path}")
        return False

    if not adapter_path.exists():
        print(f"Error: Adapter file not found: {adapter_path}")
        return False

    print(f"Loading adapter from {model_path}")

    # Get dimension count
    num_labels = get_dimension_count(filter_path)
    print(f"Dimensions: {num_labels}")

    # Load PEFT config
    peft_config = PeftConfig.from_pretrained(str(model_path))
    base_model_name = peft_config.base_model_name_or_path
    print(f"Base model: {base_model_name}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model (handles Gemma3Text config gap)
    print("Loading base model...")
    base_model = load_base_model_for_seq_cls(
        base_model_name,
        num_labels=num_labels,
        problem_type="regression",
    )

    if base_model.config.pad_token_id is None:
        base_model.config.pad_token_id = tokenizer.pad_token_id

    # Create PEFT model
    model = get_peft_model(base_model, peft_config)

    # Load adapter weights with OLD format
    print("Loading adapter weights (old format)...")
    adapter_state_dict = load_file(str(adapter_path))

    # Check if remapping is needed by looking for old-style keys
    needs_remapping = any(".lora_A.weight" in k or ".lora_B.weight" in k
                          for k in adapter_state_dict.keys())

    if needs_remapping:
        print("Remapping keys from old PEFT format to new format...")
        remapped = {}
        for key, value in adapter_state_dict.items():
            if ".lora_A.weight" in key or ".lora_B.weight" in key:
                new_key = key.replace(".lora_A.weight", ".lora_A.default.weight")
                new_key = new_key.replace(".lora_B.weight", ".lora_B.default.weight")
                remapped[new_key] = value
            elif key == "base_model.model.score.weight":
                remapped["base_model.model.score.modules_to_save.default.weight"] = value
            elif key == "base_model.model.score.bias":
                remapped["base_model.model.score.modules_to_save.default.bias"] = value
            else:
                remapped[key] = value
        adapter_state_dict = remapped
        print(f"  Remapped {len(remapped)} keys")
    else:
        print("Adapter already in current PEFT format (no remapping needed)")

    # Load weights into model
    model.load_state_dict(adapter_state_dict, strict=False)
    model.eval()
    print("Weights loaded successfully")

    # Backup original model directory
    if backup:
        backup_path = filter_path / "model_backup"
        if backup_path.exists():
            print(f"Removing existing backup at {backup_path}")
            shutil.rmtree(backup_path)
        print(f"Backing up original model to {backup_path}")
        shutil.copytree(model_path, backup_path)

    # Save in current PEFT format
    print(f"Saving adapter in current PEFT format to {model_path}")
    model.save_pretrained(str(model_path))

    # Also save tokenizer (in case format changed)
    tokenizer.save_pretrained(str(model_path))

    print("Done! Adapter resaved in current PEFT format.")

    # Verify by trying to load with PeftModel.from_pretrained
    print("\nVerifying: Loading with PeftModel.from_pretrained()...")
    try:
        # Reload base model (handles Gemma3Text config gap)
        base_model_verify = load_base_model_for_seq_cls(
            base_model_name,
            num_labels=num_labels,
            problem_type="regression",
        )
        if base_model_verify.config.pad_token_id is None:
            base_model_verify.config.pad_token_id = tokenizer.pad_token_id

        # Load with PeftModel.from_pretrained (the way Hub inference does it)
        model_verify = PeftModel.from_pretrained(base_model_verify, str(model_path))
        model_verify.eval()
        print("Verification successful! Model loads correctly with PeftModel.from_pretrained()")
        return True
    except Exception as e:
        print(f"Verification FAILED: {e}")
        print("You may want to restore from backup and investigate.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Resave LoRA adapter in current PEFT format"
    )
    parser.add_argument(
        "--filter",
        type=Path,
        required=True,
        help="Path to filter directory (e.g., filters/sustainability_technology/v1)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't backup original model directory",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    if not args.yes:
        print("WARNING: Resaving adapter keys changes the format from OLD (.lora_A.weight)")
        print("to NEW (.lora_A.default.weight). This BREAKS PeftModel.from_pretrained()")
        print("used by Hub inference. Only do this if you need local-only inference.")
        print("See ADR-007 for details.")
        print()
        response = input("Continue? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            exit(0)

    success = resave_adapter(args.filter, backup=not args.no_backup)
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
