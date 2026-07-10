# GPU Training Guide

> **SUPERSEDED (2026-07-10).** Current GPU training/deploy operations live in `docs/RUNBOOK.md` and the gpu-server env in `memory/gpu-server.md`. Its still-useful operational tips (long-job pattern, OOM→batch-size, nvidia-smi monitoring, CPU fallback) were ported to `memory/gpu-server.md` 2026-07-10; the rest is Qwen-era and kept for reference only. Start from `docs/FILTER_PLAYBOOK.md`.


**Last Updated:** 2025-11-10
**Purpose:** Train models on remote GPU server using tmux for long-running jobs

---

## Overview

This guide covers training Qwen2.5-7B-Instruct models on a remote GPU machine using tmux sessions to ensure training continues even if you disconnect.

**Why tmux?**
- Training takes 2-4 hours (can't keep SSH session open)
- Network disconnections won't interrupt training
- Can check progress anytime by reattaching
- Can run multiple training jobs in separate sessions

---

## Prerequisites

**On GPU Machine:**
- GPU with 16GB+ VRAM
- Python 3.10+
- CUDA drivers installed
- `llm-distillery` repository cloned

**On Local Machine:**
- SSH access to GPU machine
- Training data prepared (see `getting-started.md`)

---

## Setup Workflow

### 1. Transfer Training Data to GPU Machine

**Option A: Using scp (Linux/Mac local machine)**
```bash
# Transfer prepared training data
scp -r datasets/training/sustainability_tech_deployment \
    user@gpu-machine:/path/to/llm-distillery/datasets/training/

# Verify transfer
ssh user@gpu-machine "ls -lh /path/to/llm-distillery/datasets/training/sustainability_tech_deployment/"
```

**Option B: Using FreeFileSync (Windows local machine)**
1. Configure FreeFileSync with remote server connection
2. Sync `datasets/training/` directory to GPU machine
3. Verify files transferred correctly

**Option C: Git (if data is in repo)**
```bash
# On GPU machine
ssh user@gpu-machine
cd /path/to/llm-distillery
git pull origin main
```

### 2. SSH into GPU Machine

```bash
ssh user@gpu-machine
cd /path/to/llm-distillery
```

### 3. Verify Environment

```bash
# Check GPU is visible
nvidia-smi

# Expected: Should show your GPU (e.g., RTX 4080 16GB)

# Check Python and dependencies
python --version  # Should be 3.10+
pip list | grep transformers  # Should show transformers installed
```

---

## Training with Tmux

### Starting a Training Session

**Step 1: Create tmux session**
```bash
# Start new tmux session named "training"
tmux new -s training
```

**Step 2: Navigate and run training**
```bash
# Inside tmux session
cd /path/to/llm-distillery

# Run training command
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5
```

**Step 3: Detach from tmux**
- Press `Ctrl+B`, then press `D`
- You'll return to normal terminal
- Training continues in background
- You can now close SSH connection safely

### Monitoring Progress

**Reattach to session:**
```bash
# SSH back into GPU machine (if needed)
ssh user@gpu-machine

# Reattach to training session
tmux attach -t training
```

**Check without attaching:**
```bash
# List running tmux sessions
tmux ls

# Output: training: 1 windows (created Mon Nov 10 14:30:00 2025)
```

**Monitor GPU usage:**
```bash
# In separate SSH session or tmux window
watch -n 1 nvidia-smi

# Shows real-time GPU utilization and VRAM usage
```

---

## Common Training Commands

### Basic Training (Recommended)
```bash
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5
```

### Training with Reduced VRAM (if OOM errors)
```bash
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 4 \
    --learning-rate 2e-5
```

### Training with More Epochs
```bash
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 5 \
    --batch-size 8 \
    --learning-rate 2e-5
```

### Training with Custom Output Directory
```bash
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5 \
    --output-dir models/tech_deployment_v2
```

---

## Managing Multiple Training Jobs

### Running Multiple Filters in Parallel

**Create separate tmux sessions:**
```bash
# Session 1: Tech Deployment
tmux new -s tech_deployment
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 --batch-size 4
# Ctrl+B, then D to detach

# Session 2: Economic Viability
tmux new -s economic_viability
python -m training.train \
    --filter filters/sustainability_economic_viability/v1 \
    --data-dir datasets/training/sustainability_economic_viability \
    --epochs 3 --batch-size 4
# Ctrl+B, then D to detach
```

**Note:** Reduce batch size (e.g., 4 instead of 8) if running multiple models simultaneously to avoid OOM.

### Switching Between Sessions

```bash
# List all sessions
tmux ls

# Attach to specific session
tmux attach -t tech_deployment

# Switch to another session while inside tmux
# Ctrl+B, then S (shows session list, use arrow keys to select)

# Detach from current session
# Ctrl+B, then D
```

---

## Expected Training Output

```
Loading training data from datasets/training/sustainability_tech_deployment...
  Train: 4,328 examples
  Val: 413 examples
  Test: 417 examples

Loading model: Qwen/Qwen2.5-7B-Instruct...
Downloading model files... (first run only)
  model.safetensors: 100%|████████| 15.0G/15.0G [03:24<00:00, 73.2MB/s]
Model loaded successfully!

Configuring LoRA adapters...
LoRA configured with rank 16

Starting training (3 epochs)...

Epoch 1/3:
  [████████████████████████████] 541/541 [42:15<00:00, 0.21it/s]
  Train loss: 1.234 - Val loss: 0.987
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-1

Epoch 2/3:
  [████████████████████████████] 541/541 [41:52<00:00, 0.22it/s]
  Train loss: 0.876 - Val loss: 0.765
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-2

Epoch 3/3:
  [████████████████████████████] 541/541 [42:08<00:00, 0.21it/s]
  Train loss: 0.654 - Val loss: 0.621
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-3

Training complete!
Best model saved: models/sustainability_tech_deployment/checkpoint-best

Total training time: 2h 8m 15s
```

---

## After Training Completes

### 1. Verify Training Success

**Reattach to session:**
```bash
tmux attach -t training
```

**Check for checkpoint files:**
```bash
ls -lh models/sustainability_tech_deployment/

# Expected output:
# checkpoint-epoch-1/
# checkpoint-epoch-2/
# checkpoint-epoch-3/
# checkpoint-best/
# training_args.bin
# trainer_state.json
```

### 2. Transfer Model to Local Machine

**Option A: Using scp**
```bash
# On local machine
scp -r user@gpu-machine:/path/to/llm-distillery/models/sustainability_tech_deployment \
    ./models/
```

**Option B: Using FreeFileSync**
1. Sync `models/sustainability_tech_deployment/` from GPU to local
2. Verify checkpoint files transferred (14-15GB total)

**Option C: Keep on GPU for evaluation**
```bash
# Run evaluation on GPU machine directly
python -m training.evaluate \
    --model-checkpoint models/sustainability_tech_deployment/checkpoint-best \
    --data-dir datasets/training/sustainability_tech_deployment \
    --output reports/model_evaluation.md
```

### 3. Clean Up Tmux Session

**After training is done and model transferred:**
```bash
# Kill the tmux session
tmux kill-session -t training
```

---

## Troubleshooting

### Training Stopped/Crashed

**Check tmux session status:**
```bash
# List sessions
tmux ls

# If session exists, reattach to see error
tmux attach -t training
```

**Common crash causes:**
1. **CUDA OOM** - Reduce batch size (try 4 or 2)
2. **Disk full** - Check `df -h` (model checkpoints are 14GB each)
3. **Lost connection** - Training should continue if in tmux, reattach to check

### Can't Reattach to Session

**Symptom:**
```
no sessions
```

**Cause:** Session was killed or training completed

**Solution:**
- Check training logs: `ls -lh models/sustainability_tech_deployment/`
- If checkpoints exist, training likely completed
- If no checkpoints, restart training in new tmux session

### GPU Not Detected

**Symptom:**
```
RuntimeError: CUDA not available
```

**Solution:**
```bash
# Check NVIDIA driver
nvidia-smi

# If driver not found, reinstall CUDA drivers
# (Requires sudo access)
```

### Slow Training

**Monitor GPU usage:**
```bash
nvidia-smi

# Check GPU utilization (should be 90-100%)
# Check VRAM usage (should be 10-12GB for batch size 8)
```

**If GPU utilization is low:**
- Increase batch size if VRAM allows
- Check CPU bottleneck (data loading)

---

## Tmux Quick Reference

| Action | Command |
|--------|---------|
| Create session | `tmux new -s <name>` |
| Detach from session | `Ctrl+B`, then `D` |
| List sessions | `tmux ls` |
| Attach to session | `tmux attach -t <name>` |
| Kill session | `tmux kill-session -t <name>` |
| New window | `Ctrl+B`, then `C` |
| Switch windows | `Ctrl+B`, then `0-9` |
| List windows | `Ctrl+B`, then `W` |
| Switch sessions | `Ctrl+B`, then `S` |

**See also:** [`tmux-usage.md`](tmux-usage.md) for more tmux commands

---

## Best Practices

1. **Always use tmux for training** - Prevents interruption from network issues
2. **Name sessions descriptively** - Use filter name (e.g., `tech_deployment` not `train1`)
3. **Monitor first epoch** - Stay attached for first epoch to catch errors early
4. **Check GPU usage** - Run `nvidia-smi` to verify GPU is being utilized
5. **Keep logs** - Training output is only visible in tmux session, copy important info
6. **Clean up sessions** - Kill old sessions after transferring models
7. **Backup checkpoints** - Transfer to local machine or cloud storage

---

## Next Steps

After training completes:

1. **Evaluate model** - See [`getting-started.md`](getting-started.md) Step 6
2. **Create postfilter** - Implement inference module for production
3. **Deploy on corpus** - Run inference on 99K articles
4. **Train next filter** - Repeat process for remaining 5 filters

---

**See Also:**
- [`getting-started.md`](getting-started.md) - Complete pipeline walkthrough
- [`tmux-usage.md`](tmux-usage.md) - Detailed tmux guide
- [`qwen-finetuning-guide.md`](qwen-finetuning-guide.md) - Training deep dive
- [`remote-sync-guide.md`](remote-sync-guide.md) - Data sync strategies
