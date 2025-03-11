#!/bin/bash
set -e

echo "🔧 Setting up development environment..."

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found! Please install Python 3"
    exit 1
fi

# Create virtual environment
python3 -m venv builder/.venv
source builder/.venv/bin/activate

# Install dependencies
pip install -r builder/requirements.txt

echo "✅ Setup complete! Run 'make test' to test the action"