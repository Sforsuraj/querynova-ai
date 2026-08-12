from functools import lru_cache
from sqlalchemy import create_engine, inspect
from backend.config import DATABASE_URL

@lru_cache(maxsize=1)
def get_schema():
    inspector = inspect(create_engine(DATABASE_URL))
    tables, relationships = {}, []
    for table in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table):
            target = fk['referred_table']
            item = {'columns': fk['constrained_columns'], 'references_table': target, 'references_columns': fk['referred_columns']}
            fks.append(item); relationships.append({'from_table': table, **item})
        tables[table] = {'columns': {c['name']: str(c['type']) for c in inspector.get_columns(table)}, 'primary_keys': inspector.get_pk_constraint(table).get('constrained_columns', []), 'foreign_keys': fks}
    return {'tables': tables, 'relationships': relationships}
