#!/bin/bash

# Python Code Linting Script
# Run this script to execute all linting tools on the Python codebase

set -e

echo "🧹 Running Python linting tools..."

echo "📦 Installing/updating linting dependencies..."
pip install -r requirements-dev.txt > /dev/null 2>&1

echo "🖤 Running Black formatter..."
black --check --diff --exclude="\.ipynb$" .

echo "📋 Checking import order with isort..."
isort --check-only --diff .

echo "🔍 Running Flake8 linter..."
flake8 . --statistics

echo "🔍 Running MyPy type checker..."
mypy . --show-error-codes || echo "⚠️  MyPy found type issues (non-blocking)"

echo "✅ All linting checks completed!"
echo ""
echo "To fix formatting issues automatically, run:"
echo "  black ."
echo "  isort ."