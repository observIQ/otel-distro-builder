.PHONY: help setup test release clean venv deps lint lint-check build-local build-example

# Variables
VENV_DIR := builder/.venv
PYTHON := python3
VENV_BIN := $(VENV_DIR)/bin
PYTHON_FILES := builder/src builder/tests

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
CYAN := \033[0;36m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

$(VENV_DIR): ## Create virtual environment if it doesn't exist
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_BIN)/pip install --upgrade pip

venv: $(VENV_DIR) ## Create/update virtual environment
	@echo "$(BLUE)Virtual environment is ready. Activate with: source $(VENV_DIR)/bin/activate$(NC)"

deps: venv ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(VENV_BIN)/pip install -r builder/requirements.txt
	$(VENV_BIN)/pip install -r builder/requirements-dev.txt

setup: deps ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@chmod +x scripts/*.sh
	@./scripts/setup.sh

lint: deps ## Run linting and attempt to fix common issues
	@echo "$(BLUE)Running linter...$(NC)"
	$(VENV_BIN)/pip install pylint
	PYTHONPATH=builder/src $(VENV_BIN)/pylint --rcfile=builder/pylintrc $(PYTHON_FILES)

lint-check: deps ## Check linting without fixing
	@echo "$(BLUE)Checking linting...$(NC)"
	$(VENV_BIN)/pip install pylint
	PYTHONPATH=builder/src $(VENV_BIN)/pylint --rcfile=builder/pylintrc --score=y $(PYTHON_FILES)

test: deps lint-check ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	PYTHONPATH=builder/src $(VENV_BIN)/pytest builder/tests/test_build.py -v

test-coverage: deps lint-check ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(VENV_BIN)/pip install pytest-cov
	PYTHONPATH=builder/src $(VENV_BIN)/pytest builder/tests/test_build.py -v --cov=builder/src --cov-report=term-missing

release: test ## Create a new release (make release v=X.Y.Z)
	@echo "$(BLUE)Creating release...$(NC)"
	@./scripts/release.sh $(v)

build-local: ## Run a local build (requires manifest.yaml in current directory)
	@if [ ! -f manifest.yaml ]; then \
		echo "$(RED)Error: manifest.yaml not found in current directory$(NC)"; \
		exit 1; \
	fi
	./scripts/run_local_build.sh -m manifest.yaml -v 0.121.0 -s 0.121.0 -g 1.24.1

clean: ## Remove generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf artifacts/
	rm -rf build/
	rm -rf dist/
	rm -rf $(VENV_DIR)
	find builder -type d -name "__pycache__" -exec rm -rf {} +
	find builder -type d -name ".pytest_cache" -exec rm -rf {} +
	find builder -type f -name "*.pyc" -delete
	find builder -type f -name ".coverage" -delete

.PHONY: build
build:
	./builder/scripts/run_local_build.sh -m manifest.yaml
 