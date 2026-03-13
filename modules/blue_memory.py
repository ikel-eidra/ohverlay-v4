"""
Blue Memory System - Ohverlay v4.0
Persistent memory for Blue, the AI desktop assistant.

Storage: SQLite database at ~/.ohverlay/blue_memory.db
Tracks: conversations, user facts, reminders, preferences, and context.
"""

import sqlite3
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path


class BlueMemory:
    """Persistent memory system for Blue AI assistant."""

    def __init__(self, db_path=None):
        if db_path is None:
            data_dir = Path.home() / '.ohverlay'
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / 'blue_memory.db')

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        c = self.conn.cursor()

        # Conversation history
        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            tokens_used INTEGER DEFAULT 0
        )''')

        # User facts - things Blue learns about the user
        c.execute('''CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            fact TEXT NOT NULL,
            source TEXT DEFAULT 'conversation',
            confidence REAL DEFAULT 1.0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            times_referenced INTEGER DEFAULT 0
        )''')

        # Reminders and notes
        c.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            deadline REAL,
            is_recurring INTEGER DEFAULT 0,
            recur_interval_mins INTEGER,
            is_completed INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            completed_at REAL
        )''')

        # Preferences Blue has learned
        c.execute('''CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            learned_from TEXT,
            updated_at REAL NOT NULL
        )''')

        # Session log - tracks usage patterns
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            started_at REAL NOT NULL,
            ended_at REAL,
            message_count INTEGER DEFAULT 0,
            summary TEXT
        )''')

        # Important context snippets Blue should remember
        c.execute('''CREATE TABLE IF NOT EXISTS context_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            importance INTEGER DEFAULT 5,
            created_at REAL NOT NULL,
            last_accessed REAL NOT NULL,
            access_count INTEGER DEFAULT 0
        )''')

        self.conn.commit()

    # ─── Conversation History ───

    def save_message(self, session_id, role, content, tokens=0):
        """Save a chat message."""
        self.conn.execute(
            'INSERT INTO conversations (session_id, role, content, timestamp, tokens_used) VALUES (?, ?, ?, ?, ?)',
            (session_id, role, content, time.time(), tokens)
        )
        self.conn.execute(
            'UPDATE sessions SET message_count = message_count + 1 WHERE session_id = ?',
            (session_id,)
        )
        self.conn.commit()

    def get_recent_messages(self, limit=20, session_id=None):
        """Get recent conversation messages."""
        if session_id:
            rows = self.conn.execute(
                'SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?',
                (session_id, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT role, content, timestamp FROM conversations ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_conversation_history(self, hours=24, limit=100):
        """Get conversation history from the last N hours."""
        cutoff = time.time() - (hours * 3600)
        rows = self.conn.execute(
            'SELECT role, content, timestamp FROM conversations WHERE timestamp > ? ORDER BY timestamp DESC LIMIT ?',
            (cutoff, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def search_conversations(self, query, limit=10):
        """Search past conversations by keyword."""
        rows = self.conn.execute(
            'SELECT role, content, timestamp, session_id FROM conversations WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?',
            (f'%{query}%', limit)
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── User Facts ───

    def add_fact(self, category, fact, source='conversation', confidence=1.0):
        """Store a fact about the user."""
        now = time.time()
        # Check if similar fact exists
        existing = self.conn.execute(
            'SELECT id FROM user_facts WHERE category = ? AND fact = ?',
            (category, fact)
        ).fetchone()

        if existing:
            self.conn.execute(
                'UPDATE user_facts SET confidence = ?, updated_at = ?, times_referenced = times_referenced + 1 WHERE id = ?',
                (confidence, now, existing['id'])
            )
        else:
            self.conn.execute(
                'INSERT INTO user_facts (category, fact, source, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                (category, fact, source, confidence, now, now)
            )
        self.conn.commit()

    def get_facts(self, category=None, limit=50):
        """Get stored user facts, optionally filtered by category."""
        if category:
            rows = self.conn.execute(
                'SELECT * FROM user_facts WHERE category = ? ORDER BY confidence DESC, updated_at DESC LIMIT ?',
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT * FROM user_facts ORDER BY confidence DESC, updated_at DESC LIMIT ?',
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_facts_summary(self):
        """Get a compact summary of all known facts for context injection."""
        rows = self.conn.execute(
            'SELECT category, fact FROM user_facts WHERE confidence >= 0.5 ORDER BY category, updated_at DESC'
        ).fetchall()

        summary = {}
        for r in rows:
            cat = r['category']
            if cat not in summary:
                summary[cat] = []
            summary[cat].append(r['fact'])
        return summary

    # ─── Reminders ───

    def add_reminder(self, content, deadline=None, is_recurring=False, recur_interval_mins=None):
        """Create a new reminder."""
        self.conn.execute(
            'INSERT INTO reminders (content, deadline, is_recurring, recur_interval_mins, created_at) VALUES (?, ?, ?, ?, ?)',
            (content, deadline, int(is_recurring), recur_interval_mins, time.time())
        )
        self.conn.commit()

    def get_active_reminders(self):
        """Get all incomplete reminders."""
        rows = self.conn.execute(
            'SELECT * FROM reminders WHERE is_completed = 0 ORDER BY deadline ASC NULLS LAST'
        ).fetchall()
        return [dict(r) for r in rows]

    def get_upcoming_reminders(self, hours=24):
        """Get reminders due in the next N hours."""
        cutoff = time.time() + (hours * 3600)
        rows = self.conn.execute(
            'SELECT * FROM reminders WHERE is_completed = 0 AND deadline IS NOT NULL AND deadline <= ? ORDER BY deadline ASC',
            (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]

    def complete_reminder(self, reminder_id):
        """Mark a reminder as completed."""
        self.conn.execute(
            'UPDATE reminders SET is_completed = 1, completed_at = ? WHERE id = ?',
            (time.time(), reminder_id)
        )
        self.conn.commit()

    # ─── Preferences ───

    def set_preference(self, key, value, learned_from='observation'):
        """Store or update a user preference."""
        self.conn.execute(
            '''INSERT INTO preferences (key, value, learned_from, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value = ?, learned_from = ?, updated_at = ?''',
            (key, value, learned_from, time.time(), value, learned_from, time.time())
        )
        self.conn.commit()

    def get_preference(self, key, default=None):
        """Get a stored preference."""
        row = self.conn.execute(
            'SELECT value FROM preferences WHERE key = ?', (key,)
        ).fetchone()
        return row['value'] if row else default

    def get_all_preferences(self):
        """Get all stored preferences as a dict."""
        rows = self.conn.execute('SELECT key, value FROM preferences').fetchall()
        return {r['key']: r['value'] for r in rows}

    # ─── Sessions ───

    def start_session(self, session_id):
        """Register a new session."""
        self.conn.execute(
            'INSERT OR IGNORE INTO sessions (session_id, started_at) VALUES (?, ?)',
            (session_id, time.time())
        )
        self.conn.commit()

    def end_session(self, session_id, summary=None):
        """End a session with optional summary."""
        self.conn.execute(
            'UPDATE sessions SET ended_at = ?, summary = ? WHERE session_id = ?',
            (time.time(), summary, session_id)
        )
        self.conn.commit()

    def get_session_stats(self):
        """Get usage statistics."""
        total = self.conn.execute('SELECT COUNT(*) as c FROM sessions').fetchone()['c']
        messages = self.conn.execute('SELECT COUNT(*) as c FROM conversations').fetchone()['c']
        facts = self.conn.execute('SELECT COUNT(*) as c FROM user_facts').fetchone()['c']
        reminders = self.conn.execute('SELECT COUNT(*) as c FROM reminders WHERE is_completed = 0').fetchone()['c']

        return {
            'total_sessions': total,
            'total_messages': messages,
            'known_facts': facts,
            'active_reminders': reminders,
        }

    # ─── Context Memory ───

    def remember(self, topic, content, importance=5):
        """Store an important context snippet."""
        now = time.time()
        self.conn.execute(
            'INSERT INTO context_memory (topic, content, importance, created_at, last_accessed) VALUES (?, ?, ?, ?, ?)',
            (topic, content, importance, now, now)
        )
        self.conn.commit()

    def recall(self, topic=None, query=None, limit=10):
        """Recall stored context. Search by topic or keyword."""
        if topic:
            rows = self.conn.execute(
                'SELECT * FROM context_memory WHERE topic = ? ORDER BY importance DESC, last_accessed DESC LIMIT ?',
                (topic, limit)
            ).fetchall()
        elif query:
            rows = self.conn.execute(
                'SELECT * FROM context_memory WHERE content LIKE ? OR topic LIKE ? ORDER BY importance DESC LIMIT ?',
                (f'%{query}%', f'%{query}%', limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT * FROM context_memory ORDER BY importance DESC, last_accessed DESC LIMIT ?',
                (limit,)
            ).fetchall()

        # Update access stats
        for r in rows:
            self.conn.execute(
                'UPDATE context_memory SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?',
                (time.time(), r['id'])
            )
        self.conn.commit()

        return [dict(r) for r in rows]

    # ─── Context Builder for LLM ───

    def build_context_prompt(self, session_id=None):
        """Build a context string for Blue's system prompt with relevant memories."""
        parts = []

        # User facts
        facts = self.get_all_facts_summary()
        if facts:
            parts.append("What I know about the user:")
            for cat, items in facts.items():
                parts.append(f"  {cat}: {', '.join(items[:5])}")

        # Active reminders
        reminders = self.get_active_reminders()
        if reminders:
            parts.append("\nActive reminders:")
            for r in reminders[:5]:
                deadline_str = ''
                if r['deadline']:
                    dt = datetime.fromtimestamp(r['deadline'])
                    deadline_str = f" (due: {dt.strftime('%b %d, %Y %H:%M')})"
                parts.append(f"  - {r['content']}{deadline_str}")

        # Preferences
        prefs = self.get_all_preferences()
        if prefs:
            parts.append("\nUser preferences:")
            for k, v in list(prefs.items())[:10]:
                parts.append(f"  {k}: {v}")

        # Session stats
        stats = self.get_session_stats()
        parts.append(f"\nSession stats: {stats['total_sessions']} sessions, {stats['total_messages']} messages exchanged, {stats['known_facts']} facts learned")

        return '\n'.join(parts)

    # ─── Cleanup ───

    def cleanup_old_data(self, days=90):
        """Remove conversation data older than N days."""
        cutoff = time.time() - (days * 86400)
        self.conn.execute('DELETE FROM conversations WHERE timestamp < ?', (cutoff,))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
