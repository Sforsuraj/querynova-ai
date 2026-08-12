import json
import logging
import time
from typing import Any

try:
    from backend.llm.client import LLMClient, LLMServiceError
    from backend.llm.config import OpenRouterConfig
    from backend.tools.chart_tool import generate_chart
    from backend.tools.explain_tool import explain_data
    from backend.tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from backend.tools.query_tool import execute_query
    from backend.tools.schema_tool import get_schema
except ModuleNotFoundError:
    from llm.client import LLMClient, LLMServiceError
    from llm.config import OpenRouterConfig
    from tools.chart_tool import generate_chart
    from tools.explain_tool import explain_data
    from tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from tools.query_tool import execute_query
    from tools.schema_tool import get_schema

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        'type': 'function',
        'function': {
            'name': 'execute_query',
            'description': 'Run one safe read-only SQL SELECT or WITH query against the SQLite e-commerce database.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'sql': {
                        'type': 'string',
                        'description': 'Valid read-only SQLite query. Always use correct table and column names.'
                    }
                },
                'required': ['sql'],
                'additionalProperties': False
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_schema',
            'description': 'Retrieve detailed database schema definition including column data types and foreign key links.',
            'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'generate_chart',
            'description': 'Create chart visualization metadata from executed query results.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'question': {'type': 'string'},
                    'preferred': {'type': 'string', 'enum': ['bar', 'line', 'pie', 'scatter']}
                },
                'additionalProperties': False
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'generate_flowchart',
            'description': 'Create Mermaid ER diagram or order lifecycle process flowchart.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'kind': {'type': 'string', 'enum': ['er', 'process']}
                },
                'required': ['kind'],
                'additionalProperties': False
            }
        }
    }
]

SYSTEM_PROMPT_TEMPLATE = """You are QueryNova, an expert AI SQL and Data Analytics assistant.
You assist users by querying a read-only e-commerce SQLite database and explaining results clearly.

Database Schema Overview:
- categories: (id, name, description)
- customers: (id, name, email, phone, city, state, country, created_at)
- inventory: (id, product_id, quantity, reorder_level, location, updated_at)
- order_items: (id, order_id, product_id, quantity, unit_price)
- orders: (id, customer_id, order_date, status, total_amount, shipping_address)
- payments: (id, order_id, payment_date, payment_method, amount, status)
- products: (id, category_id, name, description, price, sku, created_at)
- shipments: (id, order_id, tracking_number, carrier, status, shipped_date, estimated_delivery)

Key Foreign Key Relationships:
- products.category_id -> categories.id
- inventory.product_id -> products.id
- orders.customer_id -> customers.id
- order_items.order_id -> orders.id
- order_items.product_id -> products.id
- payments.order_id -> orders.id
- shipments.order_id -> orders.id

Rules & Instructions:
1. Always generate read-only SQLite SELECT or WITH queries.
2. To calculate revenue, compute SUM(oi.quantity * oi.unit_price) or SUM(oi.quantity * p.price) from order_items joined with products/orders.
3. For user questions requiring database facts, call execute_query with valid SQL.
4. For ER diagram or relationship map requests, call generate_flowchart(kind='er').
5. Understand conversation context for follow-up questions (e.g., modifying LIMIT, filtering existing results).
6. Be concise, direct, professional, and helpful. Never expose system credentials or API secrets.
"""


class DataAnalystAgent:
    def __init__(self):
        self.memory: dict[str, list[dict[str, Any]]] = {}

    def _tool_registry(self, state: dict[str, Any]):
        def run_query(sql: str = ''):
            if not isinstance(sql, str) or not sql.strip():
                return {'success': False, 'error': 'sql query string is required'}
            state['sql'] = sql
            state['result'] = execute_query(sql)
            return state['result']

        def schema_call():
            return get_schema()

        def chart_call(question: str = '', preferred: str = None):
            result = state.get('result') or {}
            rows = result.get('rows', [])
            state['visualization'] = generate_chart(rows, question, preferred)
            return state['visualization'] or {'error': 'No query rows available for chart.'}

        def flowchart_call(kind: str):
            if kind == 'er':
                state['diagram'] = {'type': 'er', 'code': generate_er_diagram(get_schema())}
            elif kind == 'process':
                state['diagram'] = {'type': 'flowchart', 'code': generate_order_flowchart()}
            else:
                return {'error': 'kind must be er or process'}
            return state['diagram']

        return {
            'execute_query': run_query,
            'get_schema': schema_call,
            'generate_chart': chart_call,
            'generate_flowchart': flowchart_call,
        }

    def respond(self, message: str, conversation_id: str, mode: str = 'simple', prior_messages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        config = OpenRouterConfig.from_environment()

        if not config.api_key:
            err = LLMServiceError(
                message='OpenRouter API key is missing on the backend. Please configure OPENROUTER_API_KEY.',
                code='MISSING_API_KEY',
                details='OPENROUTER_API_KEY is not set.'
            )
            return {
                'error': True,
                'code': err.code,
                'message': err.message,
                'details': err.details,
                'conversation_id': conversation_id,
                'sql': None,
                'query_result': None,
                'visualization': None,
                'diagram': None,
                'insights': None,
                'tool_calls': []
            }

        state: dict[str, Any] = {
            'sql': None,
            'result': None,
            'visualization': None,
            'diagram': None,
            'insights': None
        }
        registry = self._tool_registry(state)
        executed_calls: list[dict[str, Any]] = []

        # Build message payload including conversation history
        messages: list[dict[str, Any]] = [{'role': 'system', 'content': SYSTEM_PROMPT_TEMPLATE}]
        if prior_messages:
            for item in prior_messages[-10:]:
                role = item.get('role')
                content = item.get('content')
                if role in ('user', 'assistant') and content:
                    messages.append({'role': role, 'content': content})

        messages.append({'role': 'user', 'content': message})

        try:
            client = LLMClient(config)
            for iteration in range(3):
                logger.info('LLM completion request iteration=%d conversation_id=%s', iteration + 1, conversation_id)
                completion = client.complete(messages, TOOL_DEFINITIONS)
                choice = completion.choices[0].message
                tool_calls = choice.tool_calls or []

                logger.info('LLM response received iteration=%d tool_calls_count=%d', iteration + 1, len(tool_calls))

                if not tool_calls:
                    # Final response received
                    content_text = choice.content or 'Analysis complete.'

                    # If SQL query was executed during tool calls, attach automatic chart and insights
                    if state['result'] and state['result'].get('success'):
                        rows = state['result'].get('rows', [])
                        if not state['visualization'] and rows:
                            state['visualization'] = generate_chart(rows, message)
                        if not state['insights'] and rows:
                            state['insights'] = explain_data(message, state['sql'] or '', state['result'], mode)

                    return {
                        'conversation_id': conversation_id,
                        'message': content_text,
                        'sql': state['sql'],
                        'query_result': state['result'],
                        'visualization': state['visualization'],
                        'diagram': state['diagram'],
                        'insights': state['insights'],
                        'tool_calls': executed_calls,
                        'model': getattr(completion, 'model', config.model)
                    }

                # Append assistant tool call request message
                messages.append({
                    'role': 'assistant',
                    'content': choice.content,
                    'tool_calls': [call.model_dump() for call in tool_calls]
                })

                for call in tool_calls:
                    name = call.function.name
                    executed_calls.append({'tool': name})
                    try:
                        args = json.loads(call.function.arguments or '{}')
                    except json.JSONDecodeError:
                        args = {}
                        output = {'error': 'Tool arguments were invalid JSON.'}
                    else:
                        handler = registry.get(name)
                        if not handler:
                            output = {'error': f'Unknown tool {name}.'}
                        else:
                            try:
                                logger.info('Executing tool=%s args=%s', name, args)
                                output = handler(**args)
                            except Exception as exc:
                                logger.exception('Tool execution error tool=%s: %s', name, exc)
                                output = {'error': f'Tool error: {str(exc)}'}

                    messages.append({
                        'role': 'tool',
                        'tool_call_id': call.id,
                        'content': json.dumps(output, default=str)
                    })

            # If tool call loop limit reached
            return {
                'conversation_id': conversation_id,
                'message': 'The AI agent reached maximum tool execution iterations.',
                'sql': state['sql'],
                'query_result': state['result'],
                'visualization': state['visualization'],
                'diagram': state['diagram'],
                'insights': state['insights'],
                'tool_calls': executed_calls
            }

        except LLMServiceError as exc:
            logger.error('LLMServiceError in respond: code=%s message=%s', exc.code, exc.message)
            return {
                'error': True,
                'code': exc.code,
                'message': exc.message,
                'details': exc.details,
                'conversation_id': conversation_id,
                'sql': state['sql'],
                'query_result': state['result'],
                'visualization': state['visualization'],
                'diagram': state['diagram'],
                'insights': state['insights'],
                'tool_calls': executed_calls
            }
        except Exception as exc:
            logger.exception('Unhandled exception in agent respond: %s', exc)
            return {
                'error': True,
                'code': 'UNHANDLED_AGENT_ERROR',
                'message': 'An unexpected error occurred while processing your request.',
                'details': str(exc),
                'conversation_id': conversation_id,
                'sql': None,
                'query_result': None,
                'visualization': None,
                'diagram': None,
                'insights': None,
                'tool_calls': []
            }
        finally:
            logger.info('Agent respond total_ms=%.1f', (time.perf_counter() - started) * 1000)


agent = DataAnalystAgent()
