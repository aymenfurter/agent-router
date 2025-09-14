#!/bin/bash

# Python Code Formatting Script
# Run this script to automatically format Python code

set -e

echo "🧹 Formatting Python code..."

echo "📦 Installing/updating formatting dependencies..."
pip install -r requirements-dev.txt > /dev/null 2>&1

echo "🖤 Running Black formatter..."
black --exclude="\.ipynb$" .

echo "📋 Running isort..."
isort .

echo "✅ Code formatting completed!"