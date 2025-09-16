#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

pushd "$REPO_ROOT/frontend" >/dev/null

if [ ! -d node_modules ]; then
  echo "📦 Installing frontend dependencies..."
  npm install
fi

echo "🎨 Building frontend..."
npm run build

popd >/dev/null

echo "✅ Frontend build complete."
