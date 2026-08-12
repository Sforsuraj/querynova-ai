import logging, os, uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
try:
    from backend.database.demo import ensure_demo_database
    from backend.tools.schema_tool import get_schema
    from backend.tools.query_tool import execute_query
    from backend.tools.chart_tool import generate_chart
    from backend.tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from backend.agent.agent import agent
    from backend.database import conversations
except ModuleNotFoundError:
    from database.demo import ensure_demo_database
    from tools.schema_tool import get_schema
    from tools.query_tool import execute_query
    from tools.chart_tool import generate_chart
    from tools.flowchart_tool import generate_er_diagram, generate_order_flowchart
    from agent.agent import agent
    from database import conversations

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
_initialized = False
def create_app():
    app = Flask(__name__)
    # Production is same-origin (/api); CORS is only needed for local Vite.
    CORS(app, resources={r'/api/*': {'origins': os.getenv('FRONTEND_URL', 'http://localhost:5173').split(',')}})
    @app.before_request
    def initialize_runtime():
        global _initialized
        if request.path == '/api/health' or _initialized:
            return None
        ensure_demo_database()
        conversations.initialize()
        _initialized = True
    @app.errorhandler(Exception)
    def unhandled_error(error):
        if isinstance(error, HTTPException):
            return jsonify(error=error.description), error.code
        app.logger.exception('Unhandled API error')
        return jsonify(error='QueryNova is temporarily unavailable. Please try again.'), 500
    @app.get('/api/health')
    def health():
        try:
            return jsonify(status='ok', service='QueryNova AI', runtime='vercel-python')
        except Exception:
            app.logger.exception('Health check failed')
            return jsonify(error=True, message='QueryNova is temporarily unavailable.'), 503
    @app.get('/api/schema')
    def schema(): return jsonify(get_schema())
    @app.post('/api/query')
    def query(): return jsonify(execute_query((request.get_json(silent=True) or {}).get('sql','')))
    @app.post('/api/chart')
    def chart():
        body=request.get_json(silent=True) or {}; return jsonify(generate_chart(body.get('rows',[]), body.get('question','')))
    @app.post('/api/flowchart')
    def flowchart():
        kind=(request.get_json(silent=True) or {}).get('type','er'); return jsonify({'type':kind,'code':generate_order_flowchart() if kind=='process' else generate_er_diagram(get_schema())})
    @app.post('/api/chat')
    def chat():
        body=request.get_json(silent=True) or {}; message=str(body.get('message','')).strip()
        if not message: return jsonify(error='message is required'), 400
        cid=body.get('conversation_id') or str(uuid.uuid4()); logging.info('chat request_id=%s query=%s', uuid.uuid4(), message)
        return jsonify(agent.respond(message,cid,body.get('mode','simple')))
    @app.get('/api/history')
    def history():
        cid=request.args.get('conversation_id',''); return jsonify(agent.memory.get(cid,[]))
    @app.get('/api/conversations')
    def list_conversations():
        return jsonify(conversations.list_conversations(request.args.get('search', '').strip()))
    @app.post('/api/conversations')
    def create_conversation():
        return jsonify(conversations.create_conversation((request.get_json(silent=True) or {}).get('title', 'New chat'))), 201
    @app.get('/api/conversations/<conversation_id>')
    def get_conversation(conversation_id):
        item = conversations.get_conversation(conversation_id)
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)
    @app.put('/api/conversations/<conversation_id>')
    def update_conversation(conversation_id):
        item = conversations.update_conversation(conversation_id, (request.get_json(silent=True) or {}).get('title', ''))
        return (jsonify(item), 200) if item else (jsonify(error='Conversation not found'), 404)
    @app.delete('/api/conversations/<conversation_id>')
    def delete_conversation(conversation_id):
        return ('', 204) if conversations.delete_conversation(conversation_id) else (jsonify(error='Conversation not found'), 404)
    @app.post('/api/conversations/<conversation_id>/messages')
    def add_conversation_message(conversation_id):
        body = request.get_json(silent=True) or {}; content = str(body.get('message', '')).strip()
        conversation = conversations.get_conversation(conversation_id)
        if not conversation: return jsonify(error='Conversation not found'), 404
        if not content: return jsonify(error='message is required'), 400
        user_message = conversations.add_message(conversation_id, 'user', content)
        response = agent.respond(content, conversation_id, body.get('mode', 'simple'), conversation['messages'])
        metadata = {key: response.get(key) for key in ('sql', 'query_result', 'visualization', 'diagram', 'insights', 'tool_calls')}
        assistant_message = conversations.add_message(conversation_id, 'assistant', response.get('message', ''), metadata)
        return jsonify({'conversation_id': conversation_id, 'user_message': user_message, 'message': assistant_message})
    @app.post('/api/conversations/<conversation_id>/messages/<message_id>/regenerate')
    def regenerate_conversation_message(conversation_id, message_id):
        conversation = conversations.get_conversation(conversation_id)
        if not conversation: return jsonify(error='Conversation not found'), 404
        index = next((i for i, item in enumerate(conversation['messages']) if item['id'] == message_id and item['role'] == 'assistant'), None)
        if index is None: return jsonify(error='Assistant message not found'), 404
        user_message = next((item for item in reversed(conversation['messages'][:index]) if item['role'] == 'user'), None)
        if not user_message: return jsonify(error='Original user message not found'), 400
        response = agent.respond(user_message['content'], conversation_id, 'simple', conversation['messages'][:index-1])
        metadata = {key: response.get(key) for key in ('sql', 'query_result', 'visualization', 'diagram', 'insights', 'tool_calls')}
        assistant_message = conversations.update_message(conversation_id, message_id, response.get('message', ''), metadata)
        return jsonify({'conversation_id': conversation_id, 'message': assistant_message})
    return app
app=create_app()
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.getenv('PORT','8080')), debug=True)
