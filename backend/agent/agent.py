import json
import re
from typing import Any
from backend.llm.client import LLMClient, LLMServiceError
from backend.llm.config import OpenRouterConfig
from backend.tools.chart_tool import generate_chart
from backend.tools.explain_tool import explain_data
from backend.tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
from backend.tools.query_tool import execute_query
from backend.tools.schema_tool import get_schema

TOOL_DEFINITIONS = [
    {'type':'function','function':{'name':'get_schema','description':'Retrieve the actual database schema before database analysis.','parameters':{'type':'object','properties':{},'additionalProperties':False}}},
    {'type':'function','function':{'name':'execute_query','description':'Run one safe read-only SQL SELECT/WITH query against the database.','parameters':{'type':'object','properties':{'sql':{'type':'string'}},'required':['sql'],'additionalProperties':False}}},
    {'type':'function','function':{'name':'generate_chart','description':'Create structured chart metadata from the latest query result.','parameters':{'type':'object','properties':{'question':{'type':'string'}},'additionalProperties':False}}},
    {'type':'function','function':{'name':'generate_flowchart','description':'Create an ER diagram or an order process flowchart.','parameters':{'type':'object','properties':{'kind':{'type':'string','enum':['er','process']}},'required':['kind'],'additionalProperties':False}}},
    {'type':'function','function':{'name':'explain_data','description':'Create grounded insights from the latest query result.','parameters':{'type':'object','properties':{'question':{'type':'string'},'mode':{'type':'string','enum':['simple','technical','executive']}},'additionalProperties':False}}},
]

class DataAnalystAgent:
    def __init__(self): self.memory: dict[str, list[dict[str, Any]]] = {}

    def _sql_for_demo(self, message, prior):
        q = message.lower()
        if any(x in q for x in ['all tables', 'tables present', 'list tables']): return None
        if 'never been ordered' in q or ('products' in q and 'never ordered' in q):
            return "SELECT p.name AS product FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = p.id) ORDER BY p.name"
        if ('monthly' in q and 'revenue' in q) or ('revenue trend' in q):
            return "SELECT substr(o.order_date, 1, 7) AS month, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id WHERE substr(o.order_date, 1, 4) = '2026' GROUP BY month ORDER BY month"
        if ('all table' in q or 'tables' in q) and any(w in q for w in ['name', 'present', 'give']): return None
        if 'product' in q and any(w in q for w in ['name', 'catalog', 'order item', 'order_item']):
            if 'order item' in q or 'order_item' in q: return "SELECT DISTINCT p.name AS product FROM products p JOIN order_items oi ON oi.product_id=p.id ORDER BY p.name"
            return "SELECT name AS product FROM products ORDER BY name"
        if 'trend' in q or ('last year' in q and 'product' in q): return "SELECT substr(o.order_date, 1, 7) AS month, p.name AS product, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id JOIN products p ON p.id=oi.product_id GROUP BY month, product ORDER BY month"
        if 'customer' in q and any(w in q for w in ['spent','most','spending']): return "SELECT c.name AS customer, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_spent FROM customers c JOIN orders o ON o.customer_id=c.id JOIN order_items oi ON oi.order_id=o.id GROUP BY c.id, c.name ORDER BY total_spent DESC LIMIT 10"
        if 'distribution' in q and 'category' in q: return "SELECT c.name AS category, COUNT(DISTINCT o.id) AS orders FROM categories c JOIN products p ON p.category_id=c.id JOIN order_items oi ON oi.product_id=p.id JOIN orders o ON o.id=oi.order_id GROUP BY c.name ORDER BY orders DESC"
        if any(w in q for w in ['relationship','correlation','price and quantity']): return "SELECT p.price AS price, SUM(oi.quantity) AS quantity_sold FROM products p JOIN order_items oi ON oi.product_id=p.id GROUP BY p.id, p.price ORDER BY p.price"
        if ('top' in q and 'product' in q) or 'revenue' in q:
            n = (re.search(r'top\s+(\d+)', q) or [None, '5'])[1]
            period = " WHERE o.order_date >= '2026-04-01' AND o.order_date < '2026-07-01'" if 'quarter' in q else ''
            return f"SELECT p.name AS product, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM products p JOIN order_items oi ON oi.product_id=p.id JOIN orders o ON o.id=oi.order_id{period} GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT {n}"
        return None

    def _tool_registry(self, state):
        def run_query(sql=''):
            if not isinstance(sql, str): return {'success':False,'error':'sql must be a string'}
            state['sql'] = sql; state['result'] = execute_query(sql); return state['result']
        def chart(question=''):
            result = state.get('result') or {}; state['visualization'] = generate_chart(result.get('rows', []), question); return state['visualization'] or {'error':'No query rows available'}
        def flowchart(kind):
            if kind == 'er': state['diagram']={'type':'er','code':generate_er_diagram(get_schema())}
            elif kind == 'process': state['diagram']={'type':'flowchart','code':generate_order_flowchart()}
            else: return {'error':'kind must be er or process'}
            return state['diagram']
        def explain(question='', mode='simple'):
            result=state.get('result') or {}; state['insights']=explain_data(question, state.get('sql',''), result, mode); return state['insights']
        return {'get_schema': lambda: get_schema(), 'execute_query': run_query, 'generate_chart': chart, 'generate_flowchart': flowchart, 'explain_data': explain}

    def _openrouter_response(self, message, conversation_id, mode, prior_messages=None):
        config=OpenRouterConfig.from_environment()
        if not config.api_key: return None
        state={'sql':None,'result':None,'visualization':None,'diagram':None,'insights':None}; registry=self._tool_registry(state); calls=[]
        previous = (prior_messages or [])[-8:]
        context='\n'.join(f"{'User' if item.get('role') == 'user' else 'Assistant'}: {item.get('content','')}" for item in previous)
        messages=[{'role':'system','content':'You are QueryNova, a senior AI data analyst. Prioritize correctness over confidence. Internally classify the request, then use get_schema when schema facts are needed and execute_query before making any database claim. Never invent values, relationships, percentages, trends, causes, or missing data. SQL must be safe and read-only. Answer naturally: be concise for simple lookups; for analysis give a short summary, supporting table where useful, grounded key insights, and a chart only when it materially improves understanding. State limitations when evidence is insufficient. Maintain context only from the current conversation. Do not expose hidden reasoning or tool internals.'}, {'role':'user','content':(f'Prior context:\n{context}\n\n' if context else '') + message}]
        try:
            client=LLMClient(config)
            for _ in range(6):
                completion=client.complete(messages, TOOL_DEFINITIONS); choice=completion.choices[0].message; tool_calls=choice.tool_calls or []
                if not tool_calls:
                    return {'conversation_id':conversation_id,'message':choice.content or 'I completed the analysis.','sql':state['sql'],'query_result':state['result'],'visualization':state['visualization'],'diagram':state['diagram'],'insights':state['insights'],'tool_calls':calls,'model':getattr(completion,'model',None)}
                messages.append({'role':'assistant','content':choice.content,'tool_calls':[call.model_dump() for call in tool_calls]})
                for call in tool_calls:
                    name=call.function.name
                    try: args=json.loads(call.function.arguments or '{}')
                    except json.JSONDecodeError: args={}; output={'error':'Tool arguments were not valid JSON.'}
                    else:
                        handler=registry.get(name)
                        if not handler: output={'error':'Unknown tool requested.'}
                        else:
                            try: output=handler(**args)
                            except (TypeError, ValueError) as exc: output={'error':f'Invalid arguments: {exc}'}
                    calls.append({'tool':name})
                    messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(output, default=str)})
            raise LLMServiceError('The AI agent reached its tool-call limit. Please try a more specific request.')
        except LLMServiceError as exc:
            # The local schema-aware paths remain usable during provider outages.
            # Unknown requests receive a safe, friendly fallback below.
            return None

    def respond(self, message, conversation_id, mode='simple', prior_messages=None):
        history=self.memory.setdefault(conversation_id, []); response=self._openrouter_response(message, conversation_id, mode, prior_messages)
        if response is None:
            schema=get_schema(); q=message.lower(); calls=[{'tool':'get_schema'}]; response={'conversation_id':conversation_id,'message':'','sql':None,'query_result':None,'visualization':None,'diagram':None,'insights':None,'tool_calls':calls}
            if any(x in q for x in ['er diagram','entity relationship']): response.update(message='Here is the database relationship map.',diagram={'type':'er','code':generate_er_diagram(schema)}); calls.append({'tool':'generate_flowchart','kind':'er'})
            elif any(x in q for x in ['flowchart','order flow','order moves','order lifecycle']): response.update(message='Here is the order lifecycle.',diagram={'type':'flowchart','code':generate_order_flowchart()}); calls.append({'tool':'generate_flowchart','kind':'process'})
            elif 'related to' in q or ('tables' in q and 'customer' in q):
                related=[r for r in schema['relationships'] if r['from_table']=='customers' or r['references_table']=='customers']; response['message']='Customers is directly related to: '+(', '.join(f"{r['from_table']} via {', '.join(r['columns'])}" for r in related) or 'No direct relationships')+'.'
            elif ('all table' in q or 'tables' in q) and any(w in q for w in ['name', 'present', 'give', 'list']):
                tables=list(schema['tables']); response['message']='### Database tables\n\nYour database contains **'+str(len(tables))+' tables**:\n\n`'+'` · `'.join(tables)+'`'
            else:
                sql=self._sql_for_demo(message, history[-1] if history else None)
                if not sql: response['message']='### AI service temporarily unavailable\n\nI can still help with the included database queries, but open-ended analysis is unavailable right now. Please try again in a moment.' if OpenRouterConfig.from_environment().api_key else 'Configure OPENROUTER_API_KEY for open-ended analysis, or try an included demo prompt.'
                else:
                    result=execute_query(sql); response.update(sql=sql,query_result=result); calls.append({'tool':'execute_query','sql':sql})
                    if result['success']:
                        rows=result['rows']; response.update(visualization=generate_chart(rows,message),insights=explain_data(message,sql,result,mode));
                        if not rows: response['message']='### No matching data\n\nI couldn\'t find any records matching that request. Try broadening the date range or changing the filter.'; response['visualization']=None
                        elif len(rows[0]) == 1:
                            label=next(iter(rows[0])); values=[str(r[label]) for r in rows]; title='Products with orders' if 'order item' in q else ('Products in your catalog' if 'product' in q else 'Results')
                            response['message']=f'### {title}\n\nYou have **{len(values)}** results:\n\n'+'\n'.join(f'{i}. {value}' for i,value in enumerate(values,1))
                        else: response['message']=response['insights']['summary']
                        calls.extend([{'tool':'generate_chart'},{'tool':'explain_data'}])
                    else: response['message']='I could not run that read-only query. Please try a different phrasing.'
        history.append({'question':message,'response':response}); self.memory[conversation_id]=history[-12:]; return response

agent=DataAnalystAgent()
