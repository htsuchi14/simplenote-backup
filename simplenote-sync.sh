#!/bin/bash
#
# Simplenote Bidirectional Sync Script
# Syncs notes between local and remote Simplenote.
#
# Flow:
#   1. Check if local directory is empty -> Full backup
#   2. Otherwise: Pull (Remote -> Local) -> Push (Local -> Remote)
#
# Usage:
#   ./simplenote-sync.sh                    # Run sync
#   ./simplenote-sync.sh --dry-run          # Preview without changes
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/tmp/simplenote-sync.log"
BACKUP_DIR="${BACKUP_DIR:-$HOME/Dropbox/SimplenoteBackups}"
DRY_RUN=false

# Parse arguments
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
fi

# Timestamp logging function (stdout only - launchd redirects to log file)
log() {
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1"
}

log_section() {
    log "========================================"
    log "$1"
    log "========================================"
}

# Change to script directory
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

log_section "Simplenote Sync Started"

# Check if backup directory exists and has files
if [ ! -d "$BACKUP_DIR" ] || [ -z "$(find "$BACKUP_DIR" -name '*.md' -type f 2>/dev/null | head -1)" ]; then
    log "Local directory empty or not found. Running full backup..."

    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would run: python3 simplenote-backup.py"
    else
        python3 "$SCRIPT_DIR/simplenote-backup.py"
    fi

    log_section "Full Backup Complete"
    exit 0
fi

# Normal sync flow: Pull -> Organize -> Push

# Step 1: Pull remote changes to local
log_section "Step 1: Pull (Remote -> Local)"
if [ "$DRY_RUN" = true ]; then
    python3 "$SCRIPT_DIR/simplenote-pull.py" dry-run "$BACKUP_DIR"
else
    python3 "$SCRIPT_DIR/simplenote-pull.py" pull "$BACKUP_DIR"
fi

# Step 2: Organize files (move tagged files to correct directories)
log_section "Step 2: Organize (Move tagged files)"
python3 "$SCRIPT_DIR/simplenote-classify.py" organize

# Step 3: Auto-classify untagged files using keyword matching
UNCLASSIFIED=$(python3 "$SCRIPT_DIR/simplenote-classify.py" status 2>&1 | grep "Needs classification" | grep -oE '[0-9]+')
if [ -n "$UNCLASSIFIED" ] && [ "$UNCLASSIFIED" -gt 0 ]; then
    log_section "Step 2.5: Auto-classify ($UNCLASSIFIED untagged files)"
    if [ "$DRY_RUN" = true ]; then
        python3 "$SCRIPT_DIR/simplenote-classify.py" auto --dry-run
    else
        python3 "$SCRIPT_DIR/simplenote-classify.py" auto
    fi

    # Check if any files remain unclassified
    REMAINING=$(python3 "$SCRIPT_DIR/simplenote-classify.py" status 2>&1 | grep "Needs classification" | grep -oE '[0-9]+')
    if [ -n "$REMAINING" ] && [ "$REMAINING" -gt 0 ]; then
        log "WARNING: $REMAINING file(s) could not be auto-classified"
        log "Run '/classify' in Claude Code for manual classification"
    fi
fi

# Step 4: Push local changes to remote
log_section "Step 3: Push (Local -> Remote)"
if [ "$DRY_RUN" = true ]; then
    python3 "$SCRIPT_DIR/simplenote-import.py" dry-run "$BACKUP_DIR"
else
    python3 "$SCRIPT_DIR/simplenote-import.py" sync "$BACKUP_DIR"
fi

log_section "Sync Complete"

# Show summary
log "Sync finished at $(date)"
