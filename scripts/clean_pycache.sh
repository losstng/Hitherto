#!/usr/bin/env bash
# Remove all __pycache__ directories within the repository
find "$(dirname "$0")/.." -type d -name '__pycache__' -exec rm -rf {} +
