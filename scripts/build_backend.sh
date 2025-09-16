#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🐍 Installing backend dependencies..."
python3 -m pip install -r "$REPO_ROOT/backend/requirements.txt"

echo "✅ Backend ready."
