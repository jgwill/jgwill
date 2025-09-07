# Makefile for jgwill

.PHONY: install test build release clean

install:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	@echo "Installing jgwill in editable mode..."
	pip install -e .

test:
	@echo "Running tests (placeholder)..."
	# pytest

build:
	@echo "Building jgwill package..."
	python3 -m build

release: build
	@echo "Uploading jgwill to PyPI..."
	python3 -m twine upload dist/*

clean:
	@echo "Cleaning up build artifacts..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/
	@echo "Cleanup complete."
