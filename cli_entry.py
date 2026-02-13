"""PyInstaller entry point for otel-distro-builder.

This launcher runs the real CLI as a package (builder.src.main) so that
relative imports inside main.py work when frozen. Do not run directly
in development; use `python -m builder.src.main` or run main.py with
PYTHONPATH=builder/src.
"""

from builder.src.main import main

if __name__ == "__main__":
    main()
