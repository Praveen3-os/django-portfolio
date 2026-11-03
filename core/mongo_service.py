"""
MongoDB Service for Chat Logs and Feedback Storage
- Connects to MongoDB via MONGODB_URI (e.g. MongoDB Atlas or local daemon).
- Resilient fallback to a local persistent JSON file if MongoDB is offline/unreachable,
  ensuring zero crash rate in any execution environment.
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALLBACK_DIR = os.path.join(BASE_DIR, 'data', 'mongo_fallback')
os.makedirs(FALLBACK_DIR, exist_ok=True)

CHAT_LOGS_FILE = os.path.join(FALLBACK_DIR, 'chat_logs.json')
FEEDBACK_FILE = os.path.join(FALLBACK_DIR, 'feedback.json')

class MongoService:
    def __init__(self):
        self.uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/django_portfolio')
        self.client = None
        self.db = None
        self.is_connected = False
        self._connect()

    def _connect(self):
        try:
            # 1.5 second timeout to avoid blocking requests if mongo isn't available
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=1500)
            # Trigger connection check
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            self.is_connected = True
        except (PyMongoError, Exception):
            self.is_connected = False
            self.db = None

    def _read_fallback(self, file_path):
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _append_fallback(self, file_path, doc):
        docs = self._read_fallback(file_path)
        doc['_id'] = f"fallback_{int(datetime.now().timestamp() * 1000)}"
        docs.insert(0, doc)
        if len(docs) > 1000:
            docs = docs[:1000]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2)
        except Exception as e:
            print("Fallback write error:", e)

    def log_chat(self, session_id, user_message, assistant_response, error_code=None, ip='127.0.0.1'):
        doc = {
            'session_id': session_id,
            'user_message': user_message,
            'assistant_response': assistant_response,
            'error_code': error_code,
            'ip': ip,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        if self.is_connected and self.db is not None:
            try:
                self.db.chat_logs.insert_one(doc)
                return True
            except Exception:
                self.is_connected = False

        self._append_fallback(CHAT_LOGS_FILE, doc)
        return True

    def log_feedback(self, session_id, rating, comment='', ip='127.0.0.1'):
        doc = {
            'session_id': session_id,
            'rating': rating,
            'comment': comment,
            'ip': ip,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        if self.is_connected and self.db is not None:
            try:
                self.db.feedback.insert_one(doc)
                return True
            except Exception:
                self.is_connected = False

        self._append_fallback(FEEDBACK_FILE, doc)
        return True

    def get_recent_chat_logs(self, limit=10):
        if self.is_connected and self.db is not None:
            try:
                logs = list(self.db.chat_logs.find().sort('timestamp', -1).limit(limit))
                for log in logs:
                    if '_id' in log:
                        log['_id'] = str(log['_id'])
                return logs
            except Exception:
                self.is_connected = False

        logs = self._read_fallback(CHAT_LOGS_FILE)
        return logs[:limit]

    def get_recent_feedback(self, limit=10):
        if self.is_connected and self.db is not None:
            try:
                fb = list(self.db.feedback.find().sort('timestamp', -1).limit(limit))
                for item in fb:
                    if '_id' in item:
                        item['_id'] = str(item['_id'])
                return fb
            except Exception:
                self.is_connected = False

        fb = self._read_fallback(FEEDBACK_FILE)
        return fb[:limit]

    def get_status(self):
        return {
            'connected': self.is_connected,
            'mode': 'MongoDB Cluster' if self.is_connected else 'Persistent Local Document Store Fallback',
            'chat_logs_count': len(self._read_fallback(CHAT_LOGS_FILE)) if not self.is_connected else self.db.chat_logs.count_documents({}),
            'feedback_count': len(self._read_fallback(FEEDBACK_FILE)) if not self.is_connected else self.db.feedback.count_documents({})
        }

mongo_client = MongoService()
