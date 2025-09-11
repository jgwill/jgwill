#!/bin/bash
# Pull all changes from main repo and all submodules

set -e

echo "🔄 Pulling all changes..."

# Pull main repo first
echo "📥 Pulling main repo..."
git pull

# Update all submodules
echo "📥 Updating submodules..."
git submodule update --remote --merge

# Show status of all repos
echo ""
echo "📊 Status summary:"
echo "=== Main repo ==="
git status --porcelain

echo ""
echo "=== Submodules ==="
git submodule foreach 'echo "--- $name ---" && git status --porcelain'

echo ""
echo "✅ All changes pulled successfully!"