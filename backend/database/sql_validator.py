import re

class SQLValidationError(ValueError):
    pass

FORBIDDEN = re.compile(r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|ATTACH|DETACH|VACUUM|REINDEX|REPLACE|GRANT|REVOKE)\b', re.I)

def validate_read_only_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(';').strip()
    if not cleaned:
        raise SQLValidationError('SQL cannot be empty.')
    if ';' in cleaned:
        raise SQLValidationError('Only one statement is allowed.')
    if not re.match(r'^(SELECT|WITH)\b', cleaned, re.I):
        raise SQLValidationError('Only SELECT and WITH queries are allowed.')
    if FORBIDDEN.search(cleaned) or re.search(r'\bPRAGMA\b', cleaned, re.I):
        raise SQLValidationError('Unsafe SQL operation rejected.')
    if '--' in cleaned or '/*' in cleaned:
        raise SQLValidationError('SQL comments are not allowed.')
    return cleaned
