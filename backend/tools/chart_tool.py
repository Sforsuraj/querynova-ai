def generate_chart(rows, question='', preferred=None):
    if not rows: return None
    keys = list(rows[0])
    numeric = [k for k in keys if isinstance(rows[0].get(k), (int, float))]
    labels = [k for k in keys if k not in numeric]
    if not numeric or len(keys) < 2: return None
    if len(numeric) >= 2 and any(x in question.lower() for x in ['relationship','correlation','scatter']): kind = 'scatter'; x, y = numeric[:2]
    elif labels and any(x in labels[0].lower() for x in ['date','month','year']): kind = 'line'; x, y = labels[0], numeric[0] if numeric else None
    elif any(x in question.lower() for x in ['distribution','share','proportion']): kind = 'pie'; x, y = (labels[0] if labels else keys[0]), (numeric[0] if numeric else keys[-1])
    else: kind = preferred or 'bar'; x, y = (labels[0] if labels else keys[0]), (numeric[0] if numeric else keys[-1])
    title = question[:90] or 'Query results'
    return {
        'type': kind,
        'title': title,
        'description': f'{kind.title()} visualization based on the query results.',
        # Keep legacy names while providing a predictable frontend contract.
        'x_axis': x,
        'y_axis': y,
        'xKey': x,
        'series': [{'dataKey': y, 'label': y.replace('_', ' ').title()}] if y else [],
        'nameKey': x if kind == 'pie' else None,
        'valueKey': y if kind == 'pie' else None,
        'data': rows,
    }
