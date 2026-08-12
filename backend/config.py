import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
def database_url():
    """Resolve SQLite paths from the repository, never from a developer machine."""
    configured = os.getenv('DATABASE_URL')
    if not configured:
        return f"sqlite:///{ROOT / 'database' / 'ecommerce.db'}"
    prefix = 'sqlite:///'
    if configured.startswith(prefix):
        path = Path(configured[len(prefix):])
        if not path.is_absolute() and str(path) != ':memory:':
            return f"{prefix}{(ROOT.parent / path).resolve()}"
    return configured

DATABASE_URL = database_url()
MAX_QUERY_ROWS = int(os.getenv('MAX_QUERY_ROWS', '500'))
QUERY_TIMEOUT_SECONDS = int(os.getenv('QUERY_TIMEOUT_SECONDS', '10'))
