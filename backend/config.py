import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parent
# This database is a versioned, read-only demo asset.  It is deliberately
# resolved from this module, never from the process working directory.
DATABASE_PATH = BACKEND_ROOT / 'data' / 'ecommerce.db'
# Backwards-compatible name for modules that import ROOT.
ROOT = BACKEND_ROOT

def database_url():
    """Use the bundled SQLite demo database for every SQLite deployment."""
    configured = os.getenv('DATABASE_URL')
    # Keep support for an explicitly configured non-SQLite database during
    # local development, but never allow a stale relative SQLite URL to point
    # outside the Vercel backend project root.
    if configured and not configured.startswith('sqlite'):
        return configured
    return f"sqlite:///{DATABASE_PATH.as_posix()}"

DATABASE_URL = database_url()
MAX_QUERY_ROWS = int(os.getenv('MAX_QUERY_ROWS', '500'))
QUERY_TIMEOUT_SECONDS = int(os.getenv('QUERY_TIMEOUT_SECONDS', '10'))
