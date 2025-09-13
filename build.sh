#!/bin/bash

# Build script for Purview Router UI
set -e

echo "🚀 Building Purview Router UI..."

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Navigate to UI directory
cd ui

# Build the project (dependencies should already be installed)
echo "🔨 Building UI project..."
npm run build

# Create dist directory in root if it doesn't exist
cd ..
mkdir -p dist

# Copy built files to root dist directory
echo "📁 Copying build files..."
cp -r ui/dist/* dist/

echo "✅ Build complete! Files are ready in ./dist/"
echo "🌐 Run 'python app.py' to start the server on http://localhost:5000"