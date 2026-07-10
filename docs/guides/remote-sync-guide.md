# Remote Server Sync Guide

> **SUPERSEDED (2026-07-10).** We use `scp`/`rsync` (see `memory/gpu-server.md`) and the `deploy_filters.sh` chain (`docs/RUNBOOK.md`), not FreeFileSync. Nothing salvageable (FreeFileSync-specific; the git+scp/rsync workflow lives in `memory/gpu-server.md`). Kept for reference only.


This guide explains how to develop locally with Claude Code and run batch jobs on a remote server using FreeFileSync.

## Problem

- You want to develop code locally (with Claude Code on Windows)
- You want to run expensive batch jobs on a remote server (Linux)
- Data is too large to commit to git (datasets can be 100s of MB)
- You need to sync code and data between machines

## Solution: FreeFileSync + Git

**FreeFileSync** handles large data files (datasets/, reports/) via SFTP, while **git** handles code.

**Why FreeFileSync?**
- GUI interface with preview before sync
- Mirror mode: automatically deletes remote files that don't exist locally
- SFTP support with password or SSH key auth
- Save sync configurations for reuse
- Cross-platform (Windows, Mac, Linux)
- Free and open-source

---

## Setup (One-Time)

### 1. Install FreeFileSync

Download from: https://freefilesync.org/download.php

Install on your local Windows machine.

### 2. Configure SSH Access

Ensure you can SSH into your server:

```bash
ssh your-username@your-server.example.com
```

Test that your password works or SSH key is set up correctly.

### 3. Clone Repo on Server

```bash
# SSH into server
ssh your-username@your-server.example.com

# Clone repo
cd ~
git clone https://github.com/ducroq/llm-distillery.git
cd llm-distillery

# Set up environment (if needed)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create necessary directories
mkdir -p datasets/raw
mkdir -p reports
```

### 4. Configure FreeFileSync SFTP Connection

1. **Open FreeFileSync**

2. **Click folder browse button** (📁) on either left or right panel

3. **Select SFTP** from the dropdown at top

4. **Click "Manage Connections"** or add new connection

5. **Enter connection details:**
   ```
   Connection Name: llm-distiller
   Server: your-server.example.com
   Port: 22
   Username: your-username
   Authentication: Password (or Private Key File if you have one)
   ```

6. **Test the connection** - Click "Connect" to verify

7. **Save the connection profile**

### 5. Set Up Sync Pairs

Create two sync configurations (datasets and reports):

#### Datasets Sync

**Left (Local):**
`C:\local_dev\llm-distillery\datasets`

**Right (Remote):**
`sftp://your-username@your-server:/home/your-username/llm-distillery/datasets`

**Sync direction:** Mirror → (local to remote)

#### Reports Sync

**Left (Local):**
`C:\local_dev\llm-distillery\reports`

**Right (Remote):**
`sftp://your-username@your-server:/home/your-username/llm-distillery/reports`

**Sync direction:** Mirror → (local to remote)

**Save as batch job:** File → Save as Batch Job → `llm-distillery-sync.ffs_batch`

---

## Common Workflows

### Starting a Development Session

```bash
# 1. Pull latest code from git
git pull

# 2. Open FreeFileSync
# 3. Load your saved batch job (llm-distillery-sync.ffs_batch)
# 4. Click "Compare" to see differences
# 5. Switch direction to ← (remote to local) if you want to pull data FROM server
# 6. Click "Synchronize" to execute
```

### Deploying Code Changes

```bash
# 1. Push code changes via git
git add .
git commit -m "Your commit message"
git push

# 2. SSH to server and pull
ssh your-username@your-server
cd llm-distillery
git pull
```

### Running Batch Job on Server

```bash
# 1. Push latest code via git
git push

# 2. SSH to server
ssh your-username@your-server

# 3. Navigate and pull code
cd llm-distillery
git pull
source venv/bin/activate

# 4. Run batch labeler
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source "datasets/raw/master_dataset_2025*.jsonl" \
  --output-dir datasets/uplifting_training_1500 \
  --llm gemini-flash \
  --target-count 1500 \
  --random-sample \
  --seed 42

# 5. (Optional) Run in tmux for long jobs
tmux new -s labeling
# ... run command ...
# Ctrl+B, then D to detach
# Exit SSH - job keeps running
```

### Retrieving Results

```bash
# 1. Open FreeFileSync
# 2. Load your saved batch job
# 3. Click "Compare"
# 4. Switch direction to ← (remote to local) to pull FROM server
# 5. Preview changes (should show new files in reports/)
# 6. Click "Synchronize"

# 7. Now analyze locally with Claude Code
python -m ground_truth.analyze_coverage \
  --labeled-file datasets/uplifting_training_1500/uplifting/labeled_articles.jsonl
```

---

## FreeFileSync Configuration

### Sync Directions

FreeFileSync offers several sync modes:

- **Mirror →** (Recommended): Local becomes master, remote mirrors it exactly
  - New files on local → copied to remote
  - Deleted files on local → deleted from remote
  - **Use this for:** Pushing local changes to server

- **Mirror ←**: Remote becomes master, local mirrors it exactly
  - **Use this for:** Pulling server results to local

- **Update →**: Copy new/updated files local → remote, don't delete
  - **Use this for:** One-way updates without cleanup

- **Two-way**: Sync both directions
  - **Caution:** Can create conflicts

### Recommended Settings

1. **File Permissions:** Preserve
2. **Symbolic Links:** Skip
3. **Error Handling:** Show popup
4. **Filters:** None needed (datasets and reports should all be synced)

### Save Your Configuration

**Menu: File → Save as Batch Job**

Saves a `.ffs_batch` file you can double-click to run the sync quickly.

---

## What Gets Synced?

**Synced via FreeFileSync:**
- ✅ `datasets/` - Raw data, labeled data, training data
- ✅ `reports/` - Calibration reports, analysis results

**Synced via git:**
- ✅ Python code (`ground_truth/`, `filters/`, etc.)
- ✅ Configuration files (except sensitive ones)
- ✅ Documentation (`docs/`)

**NOT synced (gitignored):**
- ❌ Virtual environments (`venv/`, `env/`)
- ❌ Compiled Python (`__pycache__/`, `*.pyc`)
- ❌ Secrets (`.env`, API keys)
- ❌ Log files (`*.log`)
- ❌ Cache directories

---

## Troubleshooting

### "LIBSSH2_ERROR_AUTHENTICATION_FAILED"

Your SSH authentication failed. Options:

**Option 1: Use password authentication (simplest)**
1. In FreeFileSync connection settings
2. Authentication: Password
3. Enter your server password

**Option 2: Fix SSH key authentication**

If you want to use SSH keys instead of password:

1. Ensure public key is on server:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # Copy this and add to server's ~/.ssh/authorized_keys
   ```

2. Convert key format if needed:
   ```bash
   # FreeFileSync uses libssh2 which can be picky
   # Try converting to PEM format:
   ssh-keygen -p -f ~/.ssh/id_ed25519 -m PEM
   ```

3. Or use PuTTY key format (.ppk):
   - Download PuTTYgen
   - Load your private key
   - Save as .ppk format
   - Use .ppk file in FreeFileSync

### "Connection timed out"

- Check server hostname/IP is correct
- Check port (usually 22)
- Ensure server allows SSH connections
- Check firewall settings

### Sync is very slow

- Large datasets take time (normal behavior)
- Check your internet connection
- Consider compressing large files before syncing

### "Permission denied" on server

```bash
# SSH to server and fix permissions
ssh your-username@your-server
cd llm-distillery
chmod -R u+w datasets reports
```

---

## Architecture: Why This Approach?

### Why NOT put data in git?

❌ **Git is not designed for large binary files:**
- Slow clones (download entire history)
- Bloated repo size (100s of MB → GBs over time)
- Merge conflicts on binary files
- GitHub has 100 MB file limit

✅ **SFTP (via FreeFileSync) is designed for file transfer:**
- Visual diff before syncing
- Mirror mode: automatic cleanup of old files
- Cross-platform
- Works anywhere SSH works
- Free and open-source

### Why FreeFileSync instead of rsync/scp?

**FreeFileSync advantages:**
- ✅ GUI with preview before sync
- ✅ Easy to see what will change
- ✅ Mirror mode deletes old files automatically
- ✅ Save configurations
- ✅ Works on Windows without WSL

**Command-line tools (rsync/scp):**
- ❌ No preview
- ❌ Silent operation
- ❌ Must remember complex commands
- ❌ Windows compatibility issues

---

## Best Practices

### 1. Develop Locally, Run Remotely

```
┌─────────────────┐         ┌──────────────────┐
│  Local (Win)    │         │  Server (Linux)  │
│  - Claude Code  │──git──→│  - batch_scorer │
│  - Development  │←─SFTP───│  - Heavy compute │
│  - Analysis     │         │  - Data storage  │
└─────────────────┘         └──────────────────┘
```

### 2. Preview Before Sync

Always click "Compare" before "Synchronize" to see:
- What will be copied
- What will be deleted
- What will be updated

FreeFileSync shows a clear visual diff.

### 3. Use Batch Jobs

Save your sync configuration as a batch job:
1. Configure both datasets/ and reports/ sync pairs
2. File → Save as Batch Job
3. Name it: `llm-distillery-sync.ffs_batch`
4. Double-click to run sync anytime

### 4. Commit Code Often, Sync Data Less

- **Code changes**: Commit and push frequently via git
- **Data sync**: Only when needed (start/end of work session)

### 5. Use tmux for Long Jobs on Server

```bash
# On server
tmux new -s labeling

# Run long job
python -m ground_truth.batch_scorer ...

# Detach: Ctrl+B, then D

# Reattach later
tmux attach -t labeling
```

---

## Example: Complete Workflow

### Scenario: Run calibration on server, analyze locally

```bash
# 1. LOCAL: Push latest code via git
git add .
git commit -m "Update calibration parameters"
git push

# 2. SSH to server
ssh your-username@your-server
cd llm-distillery
git pull
source venv/bin/activate

# 3. Run calibration (on server)
python -m ground_truth.calibrate_oracle \
  --filter filters/uplifting/v1 \
  --source "datasets/raw/*.jsonl" \
  --models gemini-flash,gemini-pro \
  --sample-size 100 \
  --seed 42

# Report saved to: reports/uplifting_calibration.md

# 4. Exit SSH
exit

# 5. LOCAL: Open FreeFileSync
#    - Load saved batch job
#    - Switch reports/ sync to ← (pull FROM server)
#    - Click "Compare"
#    - Click "Synchronize"

# 6. LOCAL: Analyze with Claude Code
# reports/uplifting_calibration.md now available locally
```

---

## Security Considerations

### What NOT to commit to git:

- ❌ Passwords or server credentials
- ❌ SSH private keys
- ❌ API keys (`.env`, `secrets.ini`)
- ❌ Labeled data (may contain sensitive content)

### What's safe to commit:

- ✅ All Python code
- ✅ Filter configurations
- ✅ Documentation
- ✅ `.gitignore` and config templates

### FreeFileSync Security:

- Passwords are stored encrypted in FreeFileSync config
- SSH keys stay on your local machine
- SFTP connections are encrypted

---

## FAQ

### Q: Can I sync FROM server to local?

**A:** Yes! Change the sync direction to ← (mirror left) in FreeFileSync. This makes your local machine mirror the server.

### Q: What if I forget which direction I'm syncing?

**A:** Always click "Compare" first! FreeFileSync will show you exactly what will happen before you click "Synchronize".

### Q: Can multiple people use the same server?

**A:** Yes! Each person should:
1. Have their own user account on server
2. Clone repo to their own home directory
3. Use separate `output_dir` for batch jobs

### Q: What happens if I lose my FreeFileSync config?

**A:** Your `.ffs_batch` files are saved locally. Back them up! If lost, you can recreate the connection settings manually (takes 5 minutes).

### Q: How do I sync both directions?

**A:** Don't! Use:
- Mirror → for pushing local changes to server
- Mirror ← for pulling server results to local

Two-way sync can create conflicts.

---

## Summary

**Development Workflow:**

1. 📥 `git pull` - Get latest code
2. 🔨 Develop locally with Claude Code
3. 📤 `git push` - Push code changes
4. 🖥️ SSH to server, `git pull`, run batch jobs
5. 📥 FreeFileSync (←) - Pull results from server
6. 📊 Analyze locally with Claude Code
7. Repeat!

**Key Tools:**

```bash
git pull            # Get code from repo
git push            # Send code to repo
FreeFileSync (→)    # Push data TO server
FreeFileSync (←)    # Pull data FROM server
```

---

For questions or issues, see [GitHub Issues](https://github.com/ducroq/llm-distillery/issues).
