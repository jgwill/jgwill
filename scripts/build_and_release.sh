#!/bin/bash

set -e

echo "Building jgwill package..."
python3 -m build

echo "Uploading to PyPI..."
python3 -m twine upload dist/*

echo "Build and release complete."
