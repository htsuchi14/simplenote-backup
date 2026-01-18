#!/bin/bash
#
# Simplenote Backup launchd uninstaller
#

PLIST_NAME="com.simplenote.backup.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "=== Simplenote Backup launchd Uninstaller ==="
echo ""

# Unload service
if launchctl list | grep -q "com.simplenote.backup" 2>/dev/null; then
    echo "Unloading service..."
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
    echo "Service unloaded"
else
    echo "Service not running"
fi

# Remove plist
if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME" ]; then
    echo "Removing plist..."
    rm "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
    echo "Plist removed"
else
    echo "Plist not found"
fi

echo ""
echo "=== Uninstallation Complete ==="
