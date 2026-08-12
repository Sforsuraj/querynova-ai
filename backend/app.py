import logging
import os
import time
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

try:
    from backend.database.demo import ensure_demo_database
    from backend.database.health import check_database
    from backend.tools.schema_tool import get_schema
    from backend.tools.query_tool import execute_query
    from backend.tools.chart_tool import generate_chart
    from backend.tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from backend.agent.agent import agent
    from backend.database import conversations
except ModuleNotFoundError:
    from database.demo import ensure_demo_database
    from database.health import check_database
    from tools.schema_tool import get_schema
    from tools.query_tool import execute_query
    from tools.chart_tool import generate_chart
    from tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from agent.agent import agent
    from database import conversations

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
_initialized = False


def allowed_frontend_origins():
    """Read a comma-separated origin allow-list without trailing slashes."""
    configured = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    origins = [origin.strip().rstrip('/') for origin in configured.split(',') if origin.strip()]
    for always in [
        'https://querynova-frontend.vercel.app',
        'http://localhost:5173',
        'http://localhost:3000',
        'http://localhost:4173',
    ]:
        if always not in origins:
            origins.append(always)
    return origins


def create_app():
    app = Flask(__name__)

    # --------------- CORS ---------------
    CORS(
        app,
        resources={r'/*': {
            'origins': allowed_frontend_origins(),
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'max_age': 3600,
        }},
        supports_credentials=False
    )

    @app.after_request
    def add_cors_headers(response):
        """Ensure CORS headers are always set — even on error responses."""
        origin = request.headers.get('Origin', '')
        if origin in allowed_frontend_origins():
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Max-Age'] = '3600'
        return response

    # --------------- Lifecycle ---------------

    @app.before_request
    def initialize_runtime():
        global _initialized
        skip_paths = ('/api/health', '/health', '/api/database/health', '/database/health')
        if request.path in skip_paths or request.method == 'OPTIONS' or _initialized:
            return None
        ensure_demo_database()
        conversations.initialize()
        _initialized = True

    # --------------- Helper for Dual Route Registration ---------------
    def route_dual(rule, **options):
        """Register route both with and without /api prefix."""
        def decorator(f):
            api_rule = rule if rule.startswith('/api') else f'/api{rule}'
            plain_rule = rule[4:] if rule.startswith('/api/') else rule
            endpoint = options.pop('endpoint', None)
            
            app.add_url_rule(api_rule, endpoint=endpoint or f'{f.__name__}_api', view_func=f, **options)
            if plain_rule != api_rule:
                app.add_url_rule(plain_rule, endpoint=f'{f.__name__}_plain', view_func=f, **options)
            return f
        return decorator

    # --------------- Error handlers ---------------

    @app.errorhandler(Exception)
    def unhandled_error(error):
        if isinstance(error, HTTPException):
            return jsonify(error=True, code='HTTP_ERROR', message=error.description), error.code
        app.logger.exception('Unhandled API error')
        return jsonify(
            error=True,
            code='INTERNAL_SERVER_ERROR',
            message='QueryNova backend encountered an internal error. Please try again.',
            details=str(error)
        ), 500

    # --------------- API routes ---------------

    @route_dual('/api/health', methods=['GET'])

    def health():
        try:
            return jsonify(status='ok', service='QueryNova', runtime='vercel-python')
        except Exception:
            app.logger.exception('Health check failed')
            return jsonify(error=True, message='QueryNova is temporarily unavailable.'), 503

    @route_dual('/api/database/health', methods=['GET'])
    def database_health():
        status = check_database()
        if not status['ok']:
            app.logger.error('Database health check failed: %s', status['reason'])
            return jsonify(status='unavailable', database='unavailable', reason=status.get('reason')), 503
        return jsonify(status='ok', database='available', table_count=status['table_count'])

    @route_dual('/api/schema', methods=['GET'])
    def schema():
        return jsonify(get_schema())

    @route_dual('/api/query', methods=['POST'])
    def query():
        body = request.get_json(silent=True) or {}
        sql = str(body.get('sql', '')).strip()
        return jsonify(execute_query(sql))

    @route_dual('/api/chart', methods=['POST'])
    def chart():
        body = request.get_json(silent=True) or {}
        return jsonify(generate_chart(body.get('rows', []), body.get('question', '')))

    @route_dual('/api/flowchart', methods=['POST'])
    def flowchart():
        body = request.get_json(silent=True) or {}
        kind = body.get('type', 'er')
        code = generate_order_flowchart() if kind == 'process' else generate_er_diagram(get_schema())
        return jsonify({'type': kind, 'code': code})

    @route_dual('/api/chat', methods=['POST'])
    def chat():
        body = request.get_json(silent=True) or {}
        message = str(body.get('message', '')).strip()
        if not message:
            return jsonify(error=True, code='VALIDATION_ERROR', message='message is required'), 400

        cid = body.get('conversation_id') or str(uuid.uuid4())
        request_id = uuid.uuid4()
        started = time.perf_counter()
        prior_messages = body.get('messages') if isinstance(body.get('messages'), list) else None

        app.logger.info('CHAT REQUEST START request_id=%s cid=%s', request_id, cid)
        response = agent.respond(message, cid, body.get('mode', 'simple'), prior_messages)
        app.logger.info('CHAT FINAL RESPONSE request_id=%s total_ms=%.1f', request_id, (time.perf_counter() - started) * 1000)

        status_code = 200
        if isinstance(response, dict) and response.get('error'):
            code = response.get('code')
            if code in ('INVALID_API_KEY', 'MISSING_API_KEY'):
                status_code = 401
            elif code in ('RATE_LIMIT_EXCEEDED',):
                status_code = 429
            elif code in ('AI_TIMEOUT', 'CONNECTION_FAILURE'):
                status_code = 504
            else:
                status_code = 500

        return jsonify(response), status_code

    @route_dual('/api/conversations', methods=['GET'])
    def list_conversations():
        return jsonify(conversations.list_conversations(request.args.get('search', '').strip()))

    @route_dual('/api/conversations', methods=['POST'])
    def create_conversation():
        body = request.get_json(silent=True) or {}
        title = body.get('title', 'New chat')
        return jsonify(conversations.create_conversation(title)), 201

    @route_dual('/api/conversations/<conversation_id>', methods=['GET'])
    def get_conversation(conversation_id):
        item = conversations.get_conversation(conversation_id)
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)

    @route_dual('/api/conversations/<conversation_id>', methods=['PUT'])
    def update_conversation(conversation_id):
        body = request.get_json(silent=True) or {}
        title = body.get('title', '')
        item = conversations.update_conversation(conversation_id, title)
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)

    @route_dual('/api/conversations/<conversation_id>', methods=['DELETE'])
    def delete_conversation(conversation_id):
        success = conversations.delete_conversation(conversation_id)
        return ('', 204) if success else (jsonify(error='Conversation not found'), 404)

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port, debug=True)
