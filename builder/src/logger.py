"""Logging utilities for the OTel builder with colored output support."""

import logging
from typing import Optional

# ANSI color codes
HEADER = "\033[95m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END = "\033[0m"


class BuildLogger:
    """Logger wrapper that provides formatted output with colors and indentation."""

    def __init__(self, logger):
        self.logger = logger

    def section(self, title: str):
        """Log a section header."""
        self.logger.info(f"\n{HEADER}{BOLD}=== {title} ==={END}\n")

    def success(self, msg: str):
        """Log a success message."""
        self.logger.info(f"{GREEN}✓ {msg}{END}")

    def warning(self, msg: str):
        """Log a warning message."""
        self.logger.warning(f"{YELLOW}! {msg}{END}")

    def error(self, msg: str):
        """Log an error message."""
        self.logger.error(f"{RED}✗ {msg}{END}")

    def info(self, msg: str, indent: int = 0):
        """Log an info message with optional indentation."""
        prefix = "  " * indent
        self.logger.info(f"{prefix}{msg}")

    def command(self, cmd: str, output: Optional[str] = None):
        """Log a command execution and its output."""
        self.logger.info(f"{BLUE}$ {cmd}{END}")
        if output:
            for line in output.splitlines():
                self.logger.info(f"  {line}")


def get_logger(name: str) -> BuildLogger:
    """Get a configured BuildLogger instance."""
    logger = logging.getLogger(name)
    return BuildLogger(logger)
