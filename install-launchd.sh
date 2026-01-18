#!/bin/bash
#
# Simplenote launchd installer
# Installs scheduled sync service for macOS
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

PLIST_NAME="com.simplenote.sync.plist"
SERVICE_NAME="com.simplenote.sync"
LOG_FILE="/tmp/simplenote-sync.log"

echo "=== Simplenote Sync launchd Installer ==="
echo ""
echo "Install directory: $SCRIPT_DIR"
echo ""

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Error: .env file not found"
    echo "Please create .env with your TOKEN first:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Check if venv exists
if [ ! -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    echo "Error: venv not found"
    echo "Please create virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  ./venv/bin/pip install simperium"
    exit 1
fi

# Unload existing service if running
if launchctl list | grep -q "$SERVICE_NAME" 2>/dev/null; then
    echo "Unloading existing service..."
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
fi

# Generate plist from template
echo "Generating plist..."
TEMPLATE_FILE="$SCRIPT_DIR/${PLIST_NAME}.template"
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi
sed "s|{{INSTALL_DIR}}|$SCRIPT_DIR|g" "$TEMPLATE_FILE" > "$SCRIPT_DIR/$PLIST_NAME"

# Create LaunchAgents directory if needed
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist
echo "Installing to $LAUNCH_AGENTS_DIR..."
cp "$SCRIPT_DIR/$PLIST_NAME" "$LAUNCH_AGENTS_DIR/"

# Load service
echo "Loading service..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

# Verify
echo ""
echo "=== Installation Complete ==="
if launchctl list | grep -q "$SERVICE_NAME"; then
    echo "Status: Running"
    launchctl list | grep "$SERVICE_NAME"
else
    echo "Status: Not running (check logs)"
fi

echo ""
echo "Commands:"
echo "  Start now:  launchctl start $SERVICE_NAME"
echo "  Stop:       launchctl unload ~/Library/LaunchAgents/$PLIST_NAME"
echo "  Logs:       tail -f $LOG_FILE"
