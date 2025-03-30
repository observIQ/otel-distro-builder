.PHONY: help setup test release clean venv deps format lint type-check quality shell-check check-all build docker-build docker-rebuild build-local scan-fs scan-image scan-all security-update

# Variables
VENV_DIR := builder/.venv
PYTHON := python3
VENV_BIN := $(VENV_DIR)/bin
PYTHON_FILES := builder/src builder/tests
DOCKER_IMAGE := otel-distro-builder

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
CYAN := \033[0;36m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Development Environment:$(NC)"
	@echo "  setup            Setup complete development environment"
	@echo "  venv             Create/update Python virtual environment"
	@echo "  deps             Install project dependencies"
	@echo ""
	@echo "$(CYAN)Quality & Testing:$(NC)"
	@echo "  format           Format code using black and isort"
	@echo "  lint             Run linting checks"
	@echo "  type-check       Run type checking"
	@echo "  quality          Run all code quality checks (format, lint, type-check)"
	@echo "  shell-check      Check shell scripts"
	@echo "  test             Run tests"
	@echo "  check-all        Run all checks (quality, shell-check, test)"
	@echo ""
	@echo "$(CYAN)Docker Operations:$(NC)"
	@echo "  docker-build     Build the builder Docker image"
	@echo "  docker-rebuild   Force rebuild the Docker image without cache"
	@echo ""
	@echo "$(CYAN)Building & Release:$(NC)"
	@echo "  build            Build distribution using manifest.yaml (auto-builds Docker if needed)"
	@echo "  build-local      Build with specific versions (requires manifest.yaml in current dir)"
	@echo "  release          Create a new release (usage: make release v=X.Y.Z)"
	@echo ""
	@echo "$(CYAN)Cleanup:$(NC)"
	@echo "  clean            Remove all generated files and caches"
	@echo ""
	@echo "$(CYAN)Security Scanning:$(NC)"
	@echo "  scan-fs          Run Trivy filesystem scan"
	@echo "  scan-image       Run Trivy container scan"
	@echo "  scan-all         Run all security scans"
	@echo ""
	@echo "For more details, see the README.md file."

###################
# Dev Environment #
###################

$(VENV_DIR): ## Create virtual environment if it doesn't exist
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_BIN)/pip install --upgrade pip

venv: $(VENV_DIR) ## Create/update virtual environment
	@echo "$(BLUE)Virtual environment is ready. Activate with: source $(VENV_DIR)/bin/activate$(NC)"

deps: venv ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(VENV_BIN)/pip install -r builder/requirements.txt
	$(VENV_BIN)/pip install -r builder/requirements-dev.txt

setup: ## Setup complete development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@chmod +x scripts/*.sh
	@./scripts/setup.sh
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(CYAN)To activate the virtual environment, run:$(NC)"
	@echo "    source $(VENV_DIR)/bin/activate"

#####################
# Quality & Testing #
#####################

format: deps ## Format code using black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(VENV_BIN)/black builder/
	$(VENV_BIN)/isort builder/

lint: deps ## Run linting checks
	@echo "$(BLUE)Running linter...$(NC)"
	PYTHONPATH=builder/src $(VENV_BIN)/pylint --rcfile=builder/pylintrc --score=y $(PYTHON_FILES)

type-check: deps ## Run type checking
	@echo "$(BLUE)Running type checks...$(NC)"
	$(VENV_BIN)/mypy builder/src

quality: format lint type-check ## Run all code quality checks
	@echo "$(GREEN)All quality checks passed!$(NC)"

shell-check: ## Check shell scripts
	@echo "$(BLUE)Checking shell scripts...$(NC)"
	shellcheck scripts/*.sh

test: deps ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	PYTHONPATH=builder/src $(VENV_BIN)/pytest builder/tests/

check-all: quality shell-check test scan-all ## Run all checks including security scans

######################
# Docker Operations #
######################

docker-build: ## Build the Docker image for the builder
	@echo "$(BLUE)Building Docker image...$(NC)"
	cd builder && docker build -t $(DOCKER_IMAGE) .

docker-rebuild: ## Force rebuild the Docker image without cache
	@echo "$(BLUE)Rebuilding Docker image from scratch...$(NC)"
	cd builder && docker build --no-cache -t $(DOCKER_IMAGE) .

#######################
# Building & Release #
#######################

build: docker-build ## Build distribution using manifest.yaml
	@echo "$(BLUE)Building distribution...$(NC)"
	./scripts/run_local_build.sh -m manifest.yaml

build-local: docker-build ## Build distribution with specific versions
	@if [ ! -f manifest.yaml ]; then \
		echo "$(RED)Error: manifest.yaml not found in current directory$(NC)"; \
		exit 1; \
	fi
	./scripts/run_local_build.sh -m manifest.yaml -v 0.121.0 -s 0.122.0 -g 1.24.1

release: test ## Create a new release (make release v=X.Y.Z)
	@echo "$(BLUE)Creating release...$(NC)"
	@./scripts/release.sh $(v)

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

#####################
# Security Scanning #
#####################

scan-fs: ## Run Trivy filesystem scan
	@echo "$(BLUE)Running filesystem security scan...$(NC)"
	trivy fs .

scan-image: docker-build ## Run Trivy container scan
	@echo "$(BLUE)Running container security scan...$(NC)"
	trivy image $(DOCKER_IMAGE)

scan-all: scan-fs scan-image ## Run all security scans
	@echo "$(GREEN)All security scans completed!$(NC)"
 