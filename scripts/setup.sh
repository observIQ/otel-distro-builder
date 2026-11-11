#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/builder/.venv"

echo "🔧 Setting up development environment..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found! Please install Python 3"
    exit 1
fi

# Require Python 3.10+ (pinned dependencies no longer support 3.9)
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "❌ Python 3.10+ is required, but python3 is $(python3 --version 2>&1)."
    echo "   Install a newer Python, or create the venv manually, e.g.: make deps PYTHON=python3.12"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r "${PROJECT_ROOT}/builder/requirements.txt"
pip install -r "${PROJECT_ROOT}/builder/requirements-dev.txt"

echo "✅ Setup complete!"
echo "ℹ️  To activate the virtual environment in your shell, run:"
echo "    source ${VENV_DIR}/bin/activate"