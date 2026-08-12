import re


class SQLValidationError(ValueError):
    pass


FORBIDDEN = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|ATTACH|DETACH|VACUUM|REINDEX|REPLACE|GRANT|REVOKE|EXEC|EXECUTE)\b',
    re.IGNORECASE
)


def validate_read_only_sql(sql: str) -> str:
    if not isinstance(sql, str):
        raise SQLValidationError('SQL query must be a string.')

    cleaned = sql.strip().rstrip(';').strip()

    if not cleaned:
        raise SQLValidationError('SQL query cannot be empty.')

    if ';' in cleaned:
        raise SQLValidationError('Only a single SQL statement is allowed. Semicolon chaining is blocked.')

    if '--' in cleaned or '/*' in cleaned or '*/' in cleaned:
        raise SQLValidationError('SQL comments are not allowed.')

    if not re.match(r'^(SELECT|WITH)\b', cleaned, re.IGNORECASE):
        raise SQLValidationError('Only SELECT and WITH (CTE) queries are allowed.')

    if FORBIDDEN.search(cleaned):
        match = FORBIDDEN.search(cleaned)
        forbidden_word = match.group(0) if match else 'Forbidden keyword'
        raise SQLValidationError(f'Unsafe SQL operation detected: "{forbidden_word}" operations are blocked.')

    if re.search(r'\bPRAGMA\b', cleaned, re.IGNORECASE):
        raise SQLValidationError('PRAGMA commands are blocked for security.')

    return cleaned
