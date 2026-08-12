def generate_er_diagram(schema):
    parts = ['erDiagram']
    for rel in schema['relationships']:
        parts.append(f"    {rel['references_table'].upper()} ||--o{{ {rel['from_table'].upper()} : relates")
    for name, table in schema['tables'].items():
        parts.append(f"    {name.upper()} {{")
        for col, typ in table['columns'].items():
            marker = ' PK' if col in table['primary_keys'] else ''
            marker += ' FK' if any(col in fk['columns'] for fk in table['foreign_keys']) else ''
            parts.append(f"        {str(typ).lower()} {col}{marker}")
        parts.append('    }')
    return '\n'.join(parts)

def generate_order_flowchart():
    return 'flowchart LR\n    A[Customer places order] --> B[Order created]\n    B --> C[Payment authorized]\n    C --> D[Inventory reserved]\n    D --> E[Shipment created]\n    E --> F[Order delivered]'
