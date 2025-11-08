#!/bin/bash
# Push changes to main repo and all submodules that have commits

set -e

echo "🚀 Pushing changes to all repositories..."

# Check and push submodules first
echo "📤 Checking submodules for changes..."
git submodule foreach '
    if [ -n "$(git status --porcelain)" ] || [ -n "$(git log @{u}.. --oneline 2>/dev/null)" ]; then
        echo "📤 Pushing changes in $name..."
        if git remote get-url origin >/dev/null 2>&1; then
            if git push; then
                echo "✅ Successfully pushed $name"
            else
                echo "❌ Failed to push $name"
                exit 1
            fi
        else
            echo "⚠️  No remote configured for $name"
        fi
    else
        echo "✅ No changes to push in $name"
    fi
'

# Push main repo
echo ""
echo "📤 Checking main repo for changes..."
if [ -n "$(git status --porcelain)" ] || [ -n "$(git log @{u}.. --oneline 2>/dev/null)" ]; then
    echo "📤 Pushing changes in main repo..."
    git push
else
    echo "✅ No changes to push in main repo"
fi

echo ""
echo "✅ All repositories synchronized!"