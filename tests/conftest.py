"""
tests/conftest.py — pytest configuration for the test suite.

Adds the scripts/ directory to sys.path so that `import validate` works
regardless of which directory pytest is invoked from.
"""

import sys
from pathlib import Path

# Insert scripts/ at the front of the path once, for all test modules.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
