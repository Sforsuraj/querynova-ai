import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
try:
    from backend.config import DATABASE_URL, MAX_QUERY_ROWS
    from backend.database.sql_validator import validate_read_only_sql, SQLValidationError
except ModuleNotFoundError:
    from config import DATABASE_URL, MAX_QUERY_ROWS
    from database.sql_validator import validate_read_only_sql, SQLValidationError

def execute_query(sql: str):
    started = time.perf_counter()
    try:
        safe_sql = validate_read_only_sql(sql)
        engine = create_engine(DATABASE_URL)
        with engine.connect() as con:
            result = con.execute(text(safe_sql))
            rows = [dict(row._mapping) for row in result.fetchmany(MAX_QUERY_ROWS)]
            return {'success': True, 'columns': list(result.keys()), 'rows': rows, 'row_count': len(rows), 'execution_ms': round((time.perf_counter()-started)*1000, 1)}
    except (SQLValidationError, SQLAlchemyError) as exc:
        return {'success': False, 'error': str(exc), 'columns': [], 'rows': [], 'row_count': 0}
