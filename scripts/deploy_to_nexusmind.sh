#!/bin/bash
# Deploy a filter from llm-distillery to NexusMind
#
# Usage: ./scripts/deploy_to_nexusmind.sh <filter_name> <version>
#                                          [--push] [--dry-run]
#                                          [--force-skip-owned-drift]
#
# Examples:
#   ./scripts/deploy_to_nexusmind.sh uplifting v5
#   ./scripts/deploy_to_nexusmind.sh sustainability_technology v2 --push
#   ./scripts/deploy_to_nexusmind.sh nature_recovery v2 --dry-run
#
# What it does:
#   1. Copies filter folder to NexusMind
#   2. Copies filters/common/ (shared utilities) — honors .nexusmind-owns
#      manifest at repo root: listed files are skipped, and the deploy fails
#      if a listed file has drifted from NexusMind's copy (issue #50).
#   3. Commits changes to NexusMind repo
#   4. Optionally pushes and shows pull commands for servers

set -e  # Exit on error

# Configuration. Env-overridable so this runs on any workstation (the defaults are
# the Windows box; on situla/Linux export DISTILLERY_ROOT + NEXUSMIND_ROOT).
DISTILLERY_ROOT="${DISTILLERY_ROOT:-C:/local_dev/llm-distillery}"
NEXUSMIND_ROOT="${NEXUSMIND_ROOT:-C:/local_dev/NexusMind}"

# Parse arguments
FILTER_NAME=""
VERSION=""
PUSH_FLAG=""
DRY_RUN=0
FORCE_SKIP_OWNED_DRIFT=0
FORCE_DIRTY=0
for arg in "$@"; do
    case "$arg" in
        --push)                       PUSH_FLAG="--push" ;;
        --dry-run)                    DRY_RUN=1 ;;
        --force-skip-owned-drift)     FORCE_SKIP_OWNED_DRIFT=1 ;;
        --force-dirty)                FORCE_DIRTY=1 ;;
        --*)                          echo "ERROR: unknown flag: $arg"; exit 1 ;;
        *)
            if [ -z "$FILTER_NAME" ]; then FILTER_NAME="$arg"
            elif [ -z "$VERSION" ]; then VERSION="$arg"
            else echo "ERROR: too many positional args ($arg)"; exit 1
            fi
            ;;
    esac
done

if [ -z "$FILTER_NAME" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <filter_name> <version> [--push] [--dry-run] [--force-skip-owned-drift] [--force-dirty]"
    echo ""
    echo "Flags:"
    echo "  --push                      git push origin main on NexusMind after the commit"
    echo "  --dry-run                   copy files but skip the git add/commit/push in NexusMind"
    echo "  --force-skip-owned-drift    proceed even if a NexusMind-owned file has drifted"
    echo "                              (use only after inspecting the drift and deciding"
    echo "                              the NexusMind copy is the one to keep)"
    echo "  --force-dirty               proceed even if NexusMind's working tree has uncommitted"
    echo "                              changes (see gotcha-log entry on the script's WIP-sweep"
    echo "                              hazard; even with --force-dirty the explicit staging"
    echo "                              below limits the commit to deploy paths)"
    echo ""
    echo "Examples:"
    echo "  $0 uplifting v5"
    echo "  $0 sustainability_technology v2 --push"
    exit 1
fi

FILTER_PATH="filters/${FILTER_NAME}/${VERSION}"
SOURCE_DIR="${DISTILLERY_ROOT}/${FILTER_PATH}"
DEST_DIR="${NEXUSMIND_ROOT}/${FILTER_PATH}"
COMMON_SOURCE="${DISTILLERY_ROOT}/filters/common"
COMMON_DEST="${NEXUSMIND_ROOT}/filters/common"
# Defensive: strip any trailing slash so the ${src#$COMMON_SOURCE/} prefix
# rewrite below works whether the assignment had a trailing slash or not.
COMMON_SOURCE="${COMMON_SOURCE%/}"
COMMON_DEST="${COMMON_DEST%/}"

# Validate source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Filter not found: $SOURCE_DIR"
    exit 1
fi

echo "=== Deploying ${FILTER_NAME} ${VERSION} to NexusMind ==="
echo ""

# Sanity: refuse to ship uncommitted changes in the filter dir. Otherwise a dirty
# working tree in llm-distillery propagates unreviewed code to NexusMind, and the
# NexusMind-side origin-diff gate would not catch it (since the code reached there
# via file copy, not via git).
if ! git -C "$DISTILLERY_ROOT" diff --quiet -- "$FILTER_PATH" \
   || ! git -C "$DISTILLERY_ROOT" diff --cached --quiet -- "$FILTER_PATH"; then
    echo "ERROR: uncommitted changes in $FILTER_PATH. Commit first, then re-run."
    git -C "$DISTILLERY_ROOT" status --short "$FILTER_PATH" | sed 's/^/  /'
    exit 1
fi

# Sanity: NexusMind target tree must be clean before we begin. Prior versions
# of this script used `git add -A` after copying files in, which would sweep
# any unrelated WIP sitting in NexusMind's working tree into the deploy commit
# — and with --push, straight to origin. The real hazard isn't a misleading
# commit message; it's that another author's uncommitted work (sensitive,
# unreleased, or simply unfinished) can land on origin without their review.
# See `memory/gotcha-log.md` "deploy_to_nexusmind.sh swept NexusMind WIP into
# deploy commit" (2026-05-23). Belt to the explicit-staging suspenders below.
if [ "$FORCE_DIRTY" -ne 1 ]; then
    if [ -n "$(git -C "$NEXUSMIND_ROOT" status --porcelain)" ]; then
        echo "ERROR: NexusMind working tree is dirty. Refusing to deploy."
        echo "       Stash, commit, or revert these changes first:"
        git -C "$NEXUSMIND_ROOT" status --short | sed 's/^/  /'
        echo ""
        echo "       Or re-run with --force-dirty if you know what you're doing"
        echo "       — the explicit staging below limits the commit to deploy"
        echo "       paths regardless, but the dirty files stay at risk if any"
        echo "       future change to this script regresses to git add -A."
        exit 1
    fi
fi

# Step 0: Verify package is internally consistent (issue #44)
# Catches v_new config x v_old weights mismatches before copying.
echo "0. Verifying filter package..."
(cd "$DISTILLERY_ROOT" && PYTHONPATH=. python scripts/deployment/verify_filter_package.py \
    --filter "$FILTER_PATH" --check-hub) || {
    echo "ERROR: verify_filter_package failed. Aborting deploy."
    echo "  Fix the package (imports / repo_id / Hub upload) before retrying."
    exit 1
}
echo ""

# Step 1: Copy filter folder
echo "1. Copying filter: ${FILTER_PATH}"
mkdir -p "$DEST_DIR"
cp -r "${SOURCE_DIR}/"* "$DEST_DIR/"
echo "   Copied to: $DEST_DIR"

# Step 2: Copy common utilities, honoring .nexusmind-owns (issue #50).
# Files listed in .nexusmind-owns evolve independently in NexusMind and must
# NOT be overwritten by a blind sync from this repo. The manifest is empty by
# default — see gotcha-log "Manifest as Anti-Pattern" (2026-05-04). When an
# entry is added, pair it with a tracked issue and a deadline to remove it.
echo ""
echo "2. Copying common utilities: filters/common/ (honoring .nexusmind-owns)"
mkdir -p "$COMMON_DEST"

NEXUSMIND_OWNS_FILE="${DISTILLERY_ROOT}/.nexusmind-owns"
OWNED_PATHS=()
DRIFT_FOUND=0
if [ -f "$NEXUSMIND_OWNS_FILE" ]; then
    while IFS= read -r raw || [ -n "$raw" ]; do
        line="${raw%%#*}"
        # Strip trailing CR — the manifest is often edited on Windows and
        # `read` does not strip \r in Git Bash.
        line="${line%$'\r'}"
        # Trim leading/trailing whitespace.
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [ -z "$line" ] && continue
        OWNED_PATHS+=("$line")
    done < "$NEXUSMIND_OWNS_FILE"
fi

# Surface manifest state explicitly. Empty is the steady state — a positive
# log line turns "no skip" into an active confirmation rather than a silent
# absence. (Refactoring-guide review, 2026-05-04: the original failure mode
# was "mechanism present, divergence reason evaporated, no one noticed.")
if [ ${#OWNED_PATHS[@]} -eq 0 ]; then
    echo "   .nexusmind-owns is empty — all common files will be synced."
else
    echo "   .nexusmind-owns: ${#OWNED_PATHS[@]} entr$( [ ${#OWNED_PATHS[@]} -eq 1 ] && echo 'y' || echo 'ies' ) skipped: ${OWNED_PATHS[*]}"
fi

# Typo guard: every manifest entry must exist on at least one side.
for owned in "${OWNED_PATHS[@]}"; do
    if [ ! -f "${DISTILLERY_ROOT}/${owned}" ] && [ ! -f "${NEXUSMIND_ROOT}/${owned}" ]; then
        echo "ERROR: .nexusmind-owns entry not found on either side: $owned"
        echo "       (fix the typo or remove the line)"
        exit 1
    fi
done

is_owned() {
    local rel="$1"
    for owned in "${OWNED_PATHS[@]}"; do
        [ "$rel" = "$owned" ] && return 0
    done
    return 1
}

# Walk the source tree and copy file-by-file, skipping owned files. Drift
# between distillery and NexusMind copies of an owned file is collected and
# fails the deploy after the loop (unless --force-skip-owned-drift was passed).
while IFS= read -r src; do
    rel_inside_common="${src#$COMMON_SOURCE/}"
    rel_from_root="filters/common/${rel_inside_common}"

    if is_owned "$rel_from_root"; then
        nm="${NEXUSMIND_ROOT}/${rel_from_root}"
        if [ -f "$nm" ] && ! diff -q "$src" "$nm" >/dev/null 2>&1; then
            echo "   DRIFT NexusMind-owned: ${rel_from_root}"
            DRIFT_FOUND=1
        else
            echo "   skip  NexusMind-owned: ${rel_from_root}"
        fi
        continue
    fi

    dest="${COMMON_DEST}/${rel_inside_common}"
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
done < <(find "$COMMON_SOURCE" -type f -not -path '*/__pycache__/*')

if [ "$DRIFT_FOUND" -eq 1 ] && [ "$FORCE_SKIP_OWNED_DRIFT" -ne 1 ]; then
    echo ""
    echo "ERROR: NexusMind-owned files have drifted from this repo (DRIFT lines above)."
    echo "       Inspect with: diff $COMMON_SOURCE/<file> $COMMON_DEST/<file>"
    echo "       Then either:"
    echo "         (a) back-port the NexusMind change to this repo and re-run, or"
    echo "         (b) re-run with --force-skip-owned-drift to keep NexusMind's copy."
    exit 1
fi
echo "   Copied to: $COMMON_DEST"

# Step 3: Git status in NexusMind
echo ""
echo "3. Changes in NexusMind:"
cd "$NEXUSMIND_ROOT"
git status --short

# Step 4: Commit
echo ""
if [ "$DRY_RUN" -eq 1 ]; then
    echo "4. DRY RUN: skipping git add/commit. Inspect $NEXUSMIND_ROOT, then revert with"
    echo "   'git -C $NEXUSMIND_ROOT checkout -- .' if you do not want to keep the changes."
else
    echo "4. Committing changes..."
    # Explicit staging: only commit paths this script intended to touch. Even
    # if --force-dirty was used, this scopes the commit to deploy-related files
    # and leaves any unrelated WIP in the working tree for the operator to
    # review separately. The 2026-05-23 incident that motivated this hardening
    # had `git add -A` here, which silently bundled 1,400+ lines of unrelated
    # WIP under a misleading "Update <filter> ..." commit message.
    git add "$FILTER_PATH" filters/common/
    COMMIT_MSG="Update ${FILTER_NAME} ${VERSION} from llm-distillery"
    git commit -m "$COMMIT_MSG" || echo "   (No changes to commit)"
fi

# Step 5: Push if requested
if [ "$DRY_RUN" -eq 1 ]; then
    echo ""
    echo "5. DRY RUN: skipping push."
elif [ "$PUSH_FLAG" == "--push" ]; then
    echo ""
    echo "5. Pushing to origin..."
    git push origin main

    echo ""
    echo "=== Deploy commands for servers ==="
    echo ""
    echo "# Sadalsuud (pull updated NexusMind from origin):"
    echo "ssh sadalsuud \"cd ~/local_dev/NexusMind && git pull origin main\""
    echo ""
    echo "# gpu-server (rsync filters/ + src/ from sadalsuud and restart scorer):"
    echo "# NOTE: gpu-server's ~/NexusMind is not a git checkout. The deploy_filters.sh"
    echo "# script runs from sadalsuud's checkout and pushes to gpu-server over SSH."
    echo "ssh sadalsuud \"cd ~/local_dev/NexusMind && bash scripts/deploy_filters.sh\""
else
    echo ""
    echo "5. Skipping push (use --push flag to push automatically)"
    echo ""
    echo "=== Next steps ==="
    echo ""
    echo "# Push to origin:"
    echo "cd $NEXUSMIND_ROOT && git push origin main"
    echo ""
    echo "# Then on servers (sadalsuud first, then gpu-server via sadalsuud):"
    echo "ssh sadalsuud \"cd ~/local_dev/NexusMind && git pull origin main\""
    echo "ssh sadalsuud \"cd ~/local_dev/NexusMind && bash scripts/deploy_filters.sh\""
fi

echo ""
echo "=== Done ==="
