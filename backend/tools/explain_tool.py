def explain_data(question, sql, result, mode='simple'):
    rows = result.get('rows', [])
    if not rows: return {'summary': 'No matching records were found.', 'key_insights': [], 'recommendations': []}
    first = rows[0]; keys = list(first); numeric = [key for key in keys if isinstance(first.get(key), (int, float))]
    label = next((key for key in keys if key not in numeric), keys[0])
    value = numeric[0] if numeric else None
    if value and len(rows) > 1:
        lead = first[label]; lead_value = first[value]
        summary = f"### What the data shows\n\n**{lead}** is the leading result at **{lead_value:,.2f}**. The query returned **{len(rows)}** rows."
        insights = [f"Top result: **{lead}** ({lead_value:,.2f})."]
        if len(rows) >= 3:
            total = sum(row.get(value, 0) for row in rows if isinstance(row.get(value), (int, float)))
            insights.append(f"The displayed results total **{total:,.2f}**.")
    else:
        summary = f"### Results\n\nI found **{len(rows)}** matching record{'s' if len(rows) != 1 else ''}."
        insights = []
    return {'summary': summary, 'key_insights': insights, 'recommendations': []}
