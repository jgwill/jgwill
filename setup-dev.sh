#!/bin/bash
# Initial development setup for jgwill project with submodules

set -e

echo "🚀 Setting up jgwill development environment..."

# Check if submodules are initialized
if [ ! -f "libs/coaiapy/setup.py" ] && [ ! -f "libs/coaiapy/pyproject.toml" ]; then
    echo "📦 Initializing submodules..."
    git submodule update --init --recursive
else
    echo "📦 Submodules already initialized"
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -e .

# Install submodules in development mode
echo "📦 Installing submodules in development mode..."
if [ -d "libs/coaiapy" ]; then
    echo "  Installing coaiapy..."
    pip install -e libs/coaiapy
fi

if [ -d "libs/storytelling" ]; then
    echo "  Installing storytelling..."
    pip install -e libs/storytelling  
fi

echo ""
echo "✅ Development environment ready!"
echo ""
echo "📁 Project structure:"
echo "  jgwill/                  - Main project (current repo)"
echo "  ├── libs/coaiapy/       - coaiapy submodule (editable)"
echo "  ├── libs/storytelling/  - storytelling submodule (editable)"
echo "  ├── mcp/servers/        - MCP servers distribution"
echo "  └── src/jgwill/         - Main package code"
echo ""
echo "🛠️  Available commands:"
echo "  ./pull-all.sh           - Pull changes from all repos"
echo "  ./push-all.sh           - Push changes to all repos"
echo ""
echo "💡 To develop in submodules:"
echo "  cd libs/coaiapy && git checkout main"
echo "  cd libs/storytelling && git checkout main"