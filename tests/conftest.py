"""Test configuration and path setup for the OTel builder tests."""

import sys
from pathlib import Path

# Add the src directory to Python path
ROOT_DIR = Path(__file__).parent.parent
BUILDER_DIR = str(ROOT_DIR / "src")
sys.path.insert(0, BUILDER_DIR)
sys.path.insert(0, str(ROOT_DIR))
