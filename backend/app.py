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
        resources={r'/api/*': {
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
        skip = request.path in ('/api/health', '/api/database/health')
        if skip or request.method == 'OPTIONS' or _initialized:
            return None
        ensure_demo_database()
        conversations.initialize()
        _initialized = True

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

    @app.get('/api/health')
    def health():
        try:
            return jsonify(status='ok', service='QueryNova', runtime='vercel-python')
        except Exception:
            app.logger.exception('Health check failed')
            return jsonify(error=True, message='QueryNova is temporarily unavailable.'), 503

    @app.get('/api/database/health')
    def database_health():
        status = check_database()
        if not status['ok']:
            app.logger.error('Database health check failed: %s', status['reason'])
            return jsonify(status='unavailable', database='unavailable', reason=status.get('reason')), 503
        return jsonify(status='ok', database='available', table_count=status['table_count'])

    @app.get('/api/schema')
    def schema():
        return jsonify(get_schema())

    @app.post('/api/query')
    def query():
        body = request.get_json(silent=True) or {}
        sql = str(body.get('sql', '')).strip()
        return jsonify(execute_query(sql))

    @app.post('/api/chart')
    def chart():
        body = request.get_json(silent=True) or {}
        return jsonify(generate_chart(body.get('rows', []), body.get('question', '')))

    @app.post('/api/flowchart')
    def flowchart():
        body = request.get_json(silent=True) or {}
        kind = body.get('type', 'er')
        code = generate_order_flowchart() if kind == 'process' else generate_er_diagram(get_schema())
        return jsonify({'type': kind, 'code': code})

    @app.post('/api/chat')
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

    @app.get('/api/conversations')
    def list_conversations():
        return jsonify(conversations.list_conversations(request.args.get('search', '').strip()))

    @app.post('/api/conversations')
    def create_conversation():
        body = request.get_json(silent=True) or {}
        title = body.get('title', 'New chat')
        return jsonify(conversations.create_conversation(title)), 201

    @app.get('/api/conversations/<conversation_id>')
    def get_conversation(conversation_id):
        item = conversations.get_conversation(conversation_id)
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)

    @app.put('/api/conversations/<conversation_id>')
    def update_conversation(conversation_id):
        body = request.get_json(silent=True) or {}
        title = body.get('title', '')
        item = conversations.update_conversation(conversation_id, title)
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)

    @app.delete('/api/conversations/<conversation_id>')
    def delete_conversation(conversation_id):
        success = conversations.delete_conversation(conversation_id)
        return ('', 204) if success else (jsonify(error='Conversation not found'), 404)

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port, debug=True)
