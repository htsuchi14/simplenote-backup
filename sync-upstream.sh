#!/bin/bash
# Fork元 (upstream) の最新を取り込む

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Fetching upstream..."
git fetch upstream

echo "Merging upstream/$BRANCH into $BRANCH..."
git merge upstream/$BRANCH

echo "Done! Synced with upstream."
