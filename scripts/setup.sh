#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/builder/.venv"
VENV_ACTIVATE="${VENV_DIR}/bin/activate"

echo "🔧 Setting up development environment..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found! Please install Python 3"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "$VENV_ACTIVATE" ]; then
        # shellcheck disable=SC1090
        . "$VENV_ACTIVATE"
    else
        echo "❌ Virtual environment activation script not found at $VENV_ACTIVATE"
        exit 1
    fi
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r "${PROJECT_ROOT}/builder/requirements.txt"

echo "✅ Setup complete! Run 'make test' to test the action"