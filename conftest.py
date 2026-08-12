"""Pytest configuration — adds backend package root to sys.path."""
import sys
from pathlib import Path

# Make `backend` importable as a package when running from project root
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
