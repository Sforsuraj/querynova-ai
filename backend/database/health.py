"""Read-only diagnostics for the packaged QueryNova demo database."""
import sqlite3

try:
    from backend.config import DATABASE_PATH
except ModuleNotFoundError:
    from config import DATABASE_PATH

REQUIRED_TABLES = {
    'categories', 'customers', 'inventory', 'order_items',
    'orders', 'payments', 'products', 'shipments',
}


def check_database():
    """Return safe database status details; never return a filesystem path."""
    if not DATABASE_PATH.is_file():
        return {'ok': False, 'reason': 'Bundled database file is missing.'}
    try:
        connection = sqlite3.connect(f'{DATABASE_PATH.as_uri()}?mode=ro', uri=True)
        try:
            names = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return {'ok': False, 'reason': f'SQLite could not open database: {exc}'}

    missing = REQUIRED_TABLES - names
    if missing:
        return {'ok': False, 'reason': f'Database schema is incomplete. Missing tables: {missing}'}
    return {'ok': True, 'table_count': len(names)}
