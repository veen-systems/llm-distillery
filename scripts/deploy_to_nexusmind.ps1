# Deploy a filter from llm-distillery to NexusMind
#
# Usage: .\scripts\deploy_to_nexusmind.ps1 <filter_name> <version>
#                                           [-Push] [-DryRun]
#                                           [-ForceSkipOwnedDrift]
#
# Examples:
#   .\scripts\deploy_to_nexusmind.ps1 uplifting v5
#   .\scripts\deploy_to_nexusmind.ps1 sustainability_technology v2 -Push
#   .\scripts\deploy_to_nexusmind.ps1 nature_recovery v2 -DryRun
#
# What it does:
#   1. Copies filter folder to NexusMind
#   2. Copies filters/common/ (shared utilities) — honors .nexusmind-owns
#      manifest at repo root: listed files are skipped, and the deploy fails
#      if a listed file has drifted from NexusMind's copy (issue #50).
#   3. Commits changes to NexusMind repo
#   4. Optionally pushes and shows pull commands for servers

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$FilterName,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$Version,

    [switch]$Push,
    [switch]$DryRun,
    [switch]$ForceSkipOwnedDrift,
    [switch]$ForceDirty,

    # Skip the gpu-server LoRA-weight probe, asserting by hand that
    # model/adapter_model.safetensors is already there. Offline use only: a
    # wrong assertion stops the scorer STARTING, and the cycle then scores
    # nothing for every filter (see guard D in preflight_deploy_guards.py).
    [switch]$WeightsPreplaced
)

$ErrorActionPreference = "Stop"

# Configuration
$DistilleryRoot = "C:\local_dev\llm-distillery"
$NexusMindRoot = "C:\local_dev\NexusMind"

$FilterPath = "filters\$FilterName\$Version"
$SourceDir = Join-Path $DistilleryRoot $FilterPath
$DestDir = Join-Path $NexusMindRoot $FilterPath
$CommonSource = Join-Path $DistilleryRoot "filters\common"
$CommonDest = Join-Path $NexusMindRoot "filters\common"
# Defensive: strip any trailing backslash so the Substring offset below is
# correct whether the join inserted one or not.
$CommonSource = $CommonSource.TrimEnd('\')
$CommonDest = $CommonDest.TrimEnd('\')

# Validate source exists
if (-not (Test-Path $SourceDir)) {
    Write-Error "ERROR: Filter not found: $SourceDir"
    exit 1
}

Write-Host "=== Deploying $FilterName $Version to NexusMind ===" -ForegroundColor Cyan
Write-Host ""

# Sanity: refuse to ship uncommitted changes (matches bash-side check).
$dirtyUnstaged  = git -C $DistilleryRoot diff --quiet -- $FilterPath; $dirtyUnstagedExit  = $LASTEXITCODE
$dirtyStaged    = git -C $DistilleryRoot diff --cached --quiet -- $FilterPath; $dirtyStagedExit    = $LASTEXITCODE
if ($dirtyUnstagedExit -ne 0 -or $dirtyStagedExit -ne 0) {
    Write-Host "ERROR: uncommitted changes in $FilterPath. Commit first, then re-run." -ForegroundColor Red
    git -C $DistilleryRoot status --short $FilterPath | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
}

# Sanity: NexusMind target tree must be clean before we begin. Prior versions
# of this script used `git add -A` after copying files in, which would sweep
# any unrelated WIP sitting in NexusMind's working tree into the deploy commit
# — and with -Push, straight to origin. The real hazard is unrelated authors'
# uncommitted work landing on origin without their review. See `memory/
# gotcha-log.md` "deploy_to_nexusmind.sh swept NexusMind WIP into deploy
# commit" (2026-05-23). Belt to the explicit-staging suspenders below.
if (-not $ForceDirty) {
    $nmStatus = git -C $NexusMindRoot status --porcelain
    if ($nmStatus) {
        Write-Host "ERROR: NexusMind working tree is dirty. Refusing to deploy." -ForegroundColor Red
        Write-Host "       Stash, commit, or revert these changes first:" -ForegroundColor Red
        git -C $NexusMindRoot status --short | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "       Or re-run with -ForceDirty if you know what you're doing" -ForegroundColor Red
        Write-Host "       (explicit staging below scopes the commit to deploy paths regardless)." -ForegroundColor Red
        exit 1
    }
}

# Step 0: Verify package is internally consistent (issue #44)
# Catches v_new config x v_old weights mismatches before copying.
Write-Host "0. Verifying filter package..." -ForegroundColor Yellow
$savedPythonPath = $env:PYTHONPATH
Push-Location $DistilleryRoot
try {
    $env:PYTHONPATH = "."
    python scripts\deployment\verify_filter_package.py --filter "$FilterPath" --check-hub
    if ($LASTEXITCODE -ne 0) {
        Write-Error "verify_filter_package failed. Aborting deploy. Fix the package (imports / repo_id / Hub upload) before retrying."
        exit 1
    }
}
finally {
    $env:PYTHONPATH = $savedPythonPath
    Pop-Location
}
Write-Host ""

# Step 0.5: Cross-repo pre-flight guards (2026-08-12).
# MUST MIRROR deploy_to_nexusmind.sh Step 0.5. This file is a documented
# alternative deploy path (docs/RUNBOOK.md), so a guard present only in the .sh
# is one keystroke from being bypassed — which is exactly the unreachable-
# mechanism defect these guards exist to catch. A 2026-08-12 review found this
# script had no Step 0.5 while the guard module's own docstring called the .sh
# "the ONE chokepoint".
Write-Host "0.5 Cross-repo pre-flight guards..." -ForegroundColor Yellow
$savedPythonPath = $env:PYTHONPATH
Push-Location $DistilleryRoot
try {
    $env:PYTHONPATH = "."
    $guardFlags = @()
    if ($WeightsPreplaced) { $guardFlags += "--weights-preplaced" }
    python scripts\deployment\preflight_deploy_guards.py `
        --filter-name "$FilterName" --version "$Version" `
        --distillery-root "$DistilleryRoot" --nexusmind-root "$NexusMindRoot" `
        @guardFlags
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pre-flight guards failed. Aborting deploy. These guard the llm-distillery -> NexusMind boundary; fix the package, do not bypass."
        exit 1
    }
}
finally {
    $env:PYTHONPATH = $savedPythonPath
    Pop-Location
}
Write-Host ""

# Step 1: Copy filter folder
Write-Host "1. Copying filter: $FilterPath" -ForegroundColor Yellow
if (-not (Test-Path $DestDir)) {
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
}
Copy-Item -Path "$SourceDir\*" -Destination $DestDir -Recurse -Force
Write-Host "   Copied to: $DestDir" -ForegroundColor Green

# Step 2: Copy common utilities, honoring .nexusmind-owns (issue #50).
# Files listed in .nexusmind-owns evolve independently in NexusMind and must
# NOT be overwritten by a blind sync from this repo. The manifest is empty by
# default — see gotcha-log "Manifest as Anti-Pattern" (2026-05-04). When an
# entry is added, pair it with a tracked issue and a deadline to remove it.
Write-Host ""
Write-Host "2. Copying common utilities: filters\common\ (honoring .nexusmind-owns)" -ForegroundColor Yellow
if (-not (Test-Path $CommonDest)) {
    New-Item -ItemType Directory -Path $CommonDest -Force | Out-Null
}

$ManifestPath = Join-Path $DistilleryRoot ".nexusmind-owns"
$OwnedPaths = @()
if (Test-Path $ManifestPath) {
    Get-Content $ManifestPath | ForEach-Object {
        $line = ($_ -split '#', 2)[0].Trim()
        if ($line) { $OwnedPaths += $line }
    }
}

# Surface manifest state explicitly. Empty is the steady state — a positive
# log line turns "no skip" into an active confirmation rather than a silent
# absence. (Refactoring-guide review, 2026-05-04: the original failure mode
# was "mechanism present, divergence reason evaporated, no one noticed.")
if ($OwnedPaths.Count -eq 0) {
    Write-Host "   .nexusmind-owns is empty - all common files will be synced." -ForegroundColor Green
} else {
    $entryWord = if ($OwnedPaths.Count -eq 1) { "entry" } else { "entries" }
    Write-Host "   .nexusmind-owns: $($OwnedPaths.Count) $entryWord skipped: $($OwnedPaths -join ', ')" -ForegroundColor Yellow
}

# Typo guard: every manifest entry must exist on at least one side.
foreach ($owned in $OwnedPaths) {
    $distSide = Join-Path $DistilleryRoot ($owned -replace '/', '\')
    $nmSide   = Join-Path $NexusMindRoot ($owned -replace '/', '\')
    if (-not (Test-Path $distSide) -and -not (Test-Path $nmSide)) {
        Write-Error "ERROR: .nexusmind-owns entry not found on either side: $owned (fix the typo or remove the line)"
        exit 1
    }
}

$OwnedSet = @{}
foreach ($p in $OwnedPaths) { $OwnedSet[$p] = $true }
$script:DriftFound = $false

# Walk the source tree and copy file-by-file, skipping owned files. Any drift
# between distillery and NexusMind copies of an owned file is collected and
# fails the deploy after the loop (unless -ForceSkipOwnedDrift was passed).
Get-ChildItem -Path $CommonSource -Recurse -File |
    Where-Object { $_.FullName -notmatch '\\__pycache__\\' } |
    ForEach-Object {
        $relInside = $_.FullName.Substring($CommonSource.Length + 1) -replace '\\', '/'
        $relFromRoot = "filters/common/$relInside"

        if ($OwnedSet.ContainsKey($relFromRoot)) {
            $nm = Join-Path $NexusMindRoot ($relFromRoot -replace '/', '\')
            if ((Test-Path $nm) -and (Get-FileHash -Algorithm SHA256 $_.FullName).Hash -ne (Get-FileHash -Algorithm SHA256 $nm).Hash) {
                Write-Host "   DRIFT NexusMind-owned: $relFromRoot" -ForegroundColor Red
                $script:DriftFound = $true
            } else {
                Write-Host "   skip  NexusMind-owned: $relFromRoot" -ForegroundColor DarkGray
            }
            return
        }

        $destFull = Join-Path $CommonDest ($relInside -replace '/', '\')
        $destDir = Split-Path $destFull -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item -Path $_.FullName -Destination $destFull -Force
    }

if ($script:DriftFound -and -not $ForceSkipOwnedDrift) {
    Write-Host ""
    Write-Host "ERROR: NexusMind-owned files have drifted from this repo (DRIFT lines above)." -ForegroundColor Red
    Write-Host "       Inspect with: Compare-Object (Get-Content $CommonSource\<file>) (Get-Content $CommonDest\<file>)" -ForegroundColor Red
    Write-Host "       Then either:" -ForegroundColor Red
    Write-Host "         (a) back-port the NexusMind change to this repo and re-run, or" -ForegroundColor Red
    Write-Host "         (b) re-run with -ForceSkipOwnedDrift to keep NexusMind's copy." -ForegroundColor Red
    exit 1
}
Write-Host "   Copied to: $CommonDest" -ForegroundColor Green

# Step 3: Git status in NexusMind
Write-Host ""
Write-Host "3. Changes in NexusMind:" -ForegroundColor Yellow
Push-Location $NexusMindRoot
git status --short

# Step 4: Commit
Write-Host ""
if ($DryRun) {
    Write-Host "4. DRY RUN: skipping git add/commit. Inspect $NexusMindRoot, then revert with" -ForegroundColor DarkGray
    Write-Host "   'git -C $NexusMindRoot checkout -- .' if you do not want to keep the changes." -ForegroundColor DarkGray
} else {
    Write-Host "4. Committing changes..." -ForegroundColor Yellow
    # Explicit staging: only commit paths this script intended to touch. Even
    # with -ForceDirty this scopes the commit to deploy-related files and
    # leaves unrelated WIP in the working tree for the operator to review.
    # The 2026-05-23 incident that motivated this hardening had `git add -A`
    # here, which silently bundled 1,400+ lines of unrelated WIP under a
    # misleading "Update <filter> ..." commit message.
    git add $FilterPath "filters/common/"
    $CommitMsg = "Update $FilterName $Version from llm-distillery"
    $commitResult = git commit -m $CommitMsg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Committed: $CommitMsg" -ForegroundColor Green
    } else {
        Write-Host "   (No changes to commit)" -ForegroundColor DarkGray
    }
}

# Step 5: Push if requested
if ($DryRun) {
    Write-Host ""
    Write-Host "5. DRY RUN: skipping push." -ForegroundColor DarkGray
} elseif ($Push) {
    Write-Host ""
    Write-Host "5. Pushing to origin..." -ForegroundColor Yellow
    git push origin main

    Write-Host ""
    Write-Host "=== Deploy commands for servers ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "# Sadalsuud (pull updated NexusMind from origin):" -ForegroundColor White
    Write-Host 'ssh sadalsuud "cd ~/local_dev/NexusMind && git pull origin main"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "# gpu-server (rsync filters/ + src/ from sadalsuud and restart scorer):" -ForegroundColor White
    Write-Host "# NOTE: gpu-server's ~/NexusMind is not a git checkout. deploy_filters.sh" -ForegroundColor DarkGray
    Write-Host "# runs from sadalsuud's checkout and pushes to gpu-server over SSH." -ForegroundColor DarkGray
    Write-Host 'ssh sadalsuud "cd ~/local_dev/NexusMind && bash scripts/deploy_filters.sh"' -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "5. Skipping push (use -Push flag to push automatically)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "=== Next steps ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "# Push to origin:" -ForegroundColor White
    Write-Host "cd $NexusMindRoot; git push origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "# Then on servers (sadalsuud first, then gpu-server via sadalsuud):" -ForegroundColor White
    Write-Host 'ssh sadalsuud "cd ~/local_dev/NexusMind && git pull origin main"' -ForegroundColor Gray
    Write-Host 'ssh sadalsuud "cd ~/local_dev/NexusMind && bash scripts/deploy_filters.sh"' -ForegroundColor Gray
}

Pop-Location

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
