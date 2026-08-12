"""Persistent, conversation-scoped chat history for QueryNova."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.config import ROOT

# Vercel's filesystem is not durable. /tmp lets the demo handle a warm function
# safely, while the README explicitly documents that production history needs a
# hosted database.
HISTORY_DB = Path('/tmp/querynova_history.db') if __import__('os').getenv('VERCEL') else Path(ROOT) / 'database' / 'querynova_history.db'

def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def connect():
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(HISTORY_DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con

def initialize():
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS conversations (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
          id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL,
          content TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL,
          FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, created_at, id);
        CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
        ''')

def title_for(text):
    clean = ' '.join(text.strip().replace('?', '').split())
    lowered = clean.lower()
    rules = [('product' in lowered and 'revenue' in lowered, 'Top products by revenue'),
             ('product' in lowered and any(x in lowered for x in ('name', 'catalog', 'all')), 'Product catalog'),
             ('monthly' in lowered and 'revenue' in lowered, 'Monthly revenue'),
             ('customer' in lowered, 'Customer analysis'),
             ('database' in lowered or 'table' in lowered or 'schema' in lowered, 'Database overview')]
    for matches, result in rules:
        if matches: return result
    clean = __import__('re').sub(r'^(can you |could you |please |show me |give me |tell me |i want )', '', clean, flags=__import__('re').I)
    clean = clean[:1].upper() + clean[1:]
    return clean if len(clean) <= 42 else clean[:39].rstrip() + '...'

def serialize_message(row):
    metadata = json.loads(row['metadata'] or '{}')
    return {'id': row['id'], 'conversationId': row['conversation_id'], 'role': row['role'],
            'content': row['content'], 'timestamp': row['created_at'], **metadata}

def list_conversations(search=''):
    query = 'SELECT id, title, created_at, updated_at FROM conversations'
    args = []
    if search:
        query += " WHERE title LIKE ? OR EXISTS (SELECT 1 FROM messages WHERE messages.conversation_id = conversations.id AND messages.content LIKE ?)"
        args.extend([f'%{search}%', f'%{search}%'])
    query += ' ORDER BY updated_at DESC'
    with connect() as con:
        return [{'id': r['id'], 'title': r['title'], 'createdAt': r['created_at'], 'updatedAt': r['updated_at']} for r in con.execute(query, args)]

def get_conversation(conversation_id):
    with connect() as con:
        row = con.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,)).fetchone()
        if not row: return None
        messages = [serialize_message(m) for m in con.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at, id', (conversation_id,))]
    return {'id': row['id'], 'title': row['title'], 'createdAt': row['created_at'], 'updatedAt': row['updated_at'], 'messages': messages}

def create_conversation(title='New chat'):
    item = {'id': str(uuid.uuid4()), 'title': title.strip()[:45] or 'New chat', 'createdAt': now()}
    with connect() as con:
        con.execute('INSERT INTO conversations VALUES (?, ?, ?, ?)', (item['id'], item['title'], item['createdAt'], item['createdAt']))
    return {**item, 'updatedAt': item['createdAt'], 'messages': []}

def update_conversation(conversation_id, title):
    with connect() as con:
        if not con.execute('SELECT 1 FROM conversations WHERE id=?', (conversation_id,)).fetchone(): return None
        con.execute('UPDATE conversations SET title=?, updated_at=? WHERE id=?', (title.strip()[:45] or 'New chat', now(), conversation_id))
    return get_conversation(conversation_id)

def delete_conversation(conversation_id):
    with connect() as con:
        return con.execute('DELETE FROM conversations WHERE id=?', (conversation_id,)).rowcount > 0

def add_message(conversation_id, role, content, metadata=None):
    stamp = now(); message_id = str(uuid.uuid4())
    with connect() as con:
        conversation = con.execute('SELECT title FROM conversations WHERE id=?', (conversation_id,)).fetchone()
        if not conversation: return None
        if role == 'user' and conversation['title'] == 'New chat':
            con.execute('UPDATE conversations SET title=? WHERE id=?', (title_for(content), conversation_id))
        con.execute('INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)', (message_id, conversation_id, role, content, json.dumps(metadata or {}, default=str), stamp))
        con.execute('UPDATE conversations SET updated_at=? WHERE id=?', (stamp, conversation_id))
    return {'id': message_id, 'conversationId': conversation_id, 'role': role, 'content': content, 'timestamp': stamp, **(metadata or {})}

def update_message(conversation_id, message_id, content, metadata=None):
    stamp = now()
    with connect() as con:
        row = con.execute('SELECT * FROM messages WHERE id=? AND conversation_id=?', (message_id, conversation_id)).fetchone()
        if not row: return None
        con.execute('UPDATE messages SET content=?, metadata=? WHERE id=?', (content, json.dumps(metadata or {}, default=str), message_id))
        con.execute('UPDATE conversations SET updated_at=? WHERE id=?', (stamp, conversation_id))
    return {'id': message_id, 'conversationId': conversation_id, 'role': row['role'], 'content': content, 'timestamp': row['created_at'], **(metadata or {})}
