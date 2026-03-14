"""
PlumberPass Question Bank - SQLite Database
=============================================
Stores all exam questions extracted from PDF reviewers.

Tables:
  subjects      - Exam subject categories
  questions     - Individual questions with options and answers
  user_progress - Track which questions user got right/wrong
  pdf_sources   - Record of processed PDF files
  study_sessions - Study session logs

Designed for:
  - Philippine Master Plumber Licensure Examination
  - June 2026 exam target
"""

import os
import sqlite3
import json
import time
import random
from typing import List, Dict, Optional
from pathlib import Path


DB_PATH = os.path.join(os.path.expanduser("~"), ".ohverlay", "plumberpass.db")


class QuestionBank:
    """SQLite-backed question bank for PlumberPass."""

    SUBJECTS = [
        ("plumbing-code", "Plumbing Code of the Philippines", "RA 1378, National Plumbing Code provisions"),
        ("sanitary-eng", "Sanitary Engineering", "Sanitary systems, waste treatment, public health"),
        ("design-layout", "Plumbing Design & Layout", "System design, blueprint reading, specifications"),
        ("water-supply", "Water Supply Systems", "Water distribution, pressure, pipe sizing, pumps"),
        ("drainage", "Drainage & Sewage Systems", "DWV systems, venting, traps, sewage disposal"),
        ("fixtures", "Plumbing Fixtures & Materials", "Fixture units, materials, standards, installation"),
        ("mathematics", "Plumbing Mathematics", "Calculations, formulas, pipe sizing, flow rates"),
        ("environmental", "Environmental Laws", "RA 9275 Clean Water Act, DENR regulations"),
        ("ethics", "Professional Ethics & Practice", "RA 1378 practice, board regulations, ethics"),
        ("general", "General Plumbing Knowledge", "Mixed topics, general knowledge"),
    ]

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                question_count INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id  TEXT NOT NULL,
                question    TEXT NOT NULL,
                options     TEXT NOT NULL,  -- JSON array of strings
                answer      INTEGER NOT NULL,  -- 0-indexed correct option
                explanation TEXT,  -- Why this is correct
                difficulty  INTEGER DEFAULT 2,  -- 1=easy, 2=medium, 3=hard
                source_pdf  TEXT,  -- Which PDF it came from
                page_ref    TEXT,  -- Page reference in source
                tags        TEXT,  -- Comma-separated tags
                times_shown INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0,
                created_at  REAL DEFAULT 0,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                was_correct INTEGER NOT NULL,  -- 1 or 0
                time_taken  REAL DEFAULT 0,  -- seconds to answer
                answered_at REAL DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS pdf_sources (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                filepath    TEXT,
                pages       INTEGER DEFAULT 0,
                questions_extracted INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'pending',  -- pending, processing, done, failed
                processed_at REAL DEFAULT 0,
                created_at  REAL DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id  TEXT,
                questions_shown INTEGER DEFAULT 0,
                correct     INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                mode        TEXT DEFAULT 'overlay',  -- overlay, focused, timed
                started_at  REAL DEFAULT 0,
                ended_at    REAL DEFAULT 0
            )
        """)

        # Seed subjects
        for sid, name, desc in self.SUBJECTS:
            c.execute(
                "INSERT OR IGNORE INTO subjects (id, name, description) VALUES (?, ?, ?)",
                (sid, name, desc),
            )

        conn.commit()
        conn.close()

    # ─── Question CRUD ───

    def add_question(
        self,
        subject_id,
        question,
        options,
        answer,
        explanation="",
        difficulty=2,
        source_pdf="",
        page_ref="",
        tags="",
    ) -> int:
        """Add a question to the bank. Returns question ID."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """INSERT INTO questions
               (subject_id, question, options, answer, explanation,
                difficulty, source_pdf, page_ref, tags, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                question,
                json.dumps(options),
                answer,
                explanation,
                difficulty,
                source_pdf,
                page_ref,
                tags,
                time.time(),
            ),
        )
        qid = c.lastrowid

        # Update subject count
        c.execute(
            "UPDATE subjects SET question_count = (SELECT COUNT(*) FROM questions WHERE subject_id = ?) WHERE id = ?",
            (subject_id, subject_id),
        )

        conn.commit()
        conn.close()
        return qid

    def add_questions_bulk(self, questions: List[Dict]) -> int:
        """Add multiple questions at once. Returns count added."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        count = 0

        for q in questions:
            try:
                c.execute(
                    """INSERT INTO questions
                       (subject_id, question, options, answer, explanation,
                        difficulty, source_pdf, page_ref, tags, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        q.get("subject_id", "general"),
                        q["question"],
                        json.dumps(q["options"]),
                        q["answer"],
                        q.get("explanation", ""),
                        q.get("difficulty", 2),
                        q.get("source_pdf", ""),
                        q.get("page_ref", ""),
                        q.get("tags", ""),
                        time.time(),
                    ),
                )
                count += 1
            except (KeyError, sqlite3.Error):
                continue

        # Update all subject counts
        for sid, _, _ in self.SUBJECTS:
            c.execute(
                "UPDATE subjects SET question_count = (SELECT COUNT(*) FROM questions WHERE subject_id = ?) WHERE id = ?",
                (sid, sid),
            )

        conn.commit()
        conn.close()
        return count

    def get_random_question(self, subject_id=None, difficulty=None, exclude_ids=None):
        """Get a random question, optionally filtered."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        query += " ORDER BY RANDOM() LIMIT 1"
        c.execute(query, params)
        row = c.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_questions_for_overlay(self, count=10, subject_id=None, smart=True):
        """
        Get questions for overlay mode.
        If smart=True, prioritizes questions the user gets wrong more often
        (spaced repetition lite).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if smart:
            # Prioritize: never shown > frequently wrong > least recently shown
            query = """
                SELECT q.*,
                    COALESCE(q.times_shown, 0) as shown,
                    CASE WHEN q.times_shown > 0
                         THEN CAST(q.times_correct AS REAL) / q.times_shown
                         ELSE 0 END as accuracy
                FROM questions q
                WHERE 1=1
            """
            params = []
            if subject_id:
                query += " AND q.subject_id = ?"
                params.append(subject_id)

            query += """
                ORDER BY
                    CASE WHEN q.times_shown = 0 THEN 0 ELSE 1 END,
                    accuracy ASC,
                    q.times_shown ASC,
                    RANDOM()
                LIMIT ?
            """
            params.append(count)
        else:
            query = "SELECT * FROM questions WHERE 1=1"
            params = []
            if subject_id:
                query += " AND subject_id = ?"
                params.append(subject_id)
            query += " ORDER BY RANDOM() LIMIT ?"
            params.append(count)

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        return [self._row_to_dict(r) for r in rows]

    def record_answer(self, question_id, was_correct, time_taken=0):
        """Record that a user answered a question."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Update question stats
        c.execute(
            "UPDATE questions SET times_shown = times_shown + 1 WHERE id = ?",
            (question_id,),
        )
        if was_correct:
            c.execute(
                "UPDATE questions SET times_correct = times_correct + 1 WHERE id = ?",
                (question_id,),
            )

        # Log the attempt
        c.execute(
            "INSERT INTO user_progress (question_id, was_correct, time_taken, answered_at) VALUES (?, ?, ?, ?)",
            (question_id, 1 if was_correct else 0, time_taken, time.time()),
        )

        conn.commit()
        conn.close()

    # ─── Stats ───

    def get_stats(self, subject_id=None):
        """Get study statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if subject_id:
            c.execute("SELECT COUNT(*) FROM questions WHERE subject_id = ?", (subject_id,))
        else:
            c.execute("SELECT COUNT(*) FROM questions")
        total_questions = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM user_progress WHERE was_correct = 1")
        total_correct = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM user_progress")
        total_attempts = c.fetchone()[0]

        c.execute("SELECT COUNT(DISTINCT question_id) FROM user_progress")
        unique_answered = c.fetchone()[0]

        # Subject breakdown
        c.execute("""
            SELECT s.id, s.name, s.question_count,
                   COUNT(DISTINCT up.question_id) as answered,
                   SUM(CASE WHEN up.was_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM subjects s
            LEFT JOIN questions q ON q.subject_id = s.id
            LEFT JOIN user_progress up ON up.question_id = q.id
            GROUP BY s.id
            ORDER BY s.name
        """)
        subjects = []
        for row in c.fetchall():
            subjects.append({
                "id": row[0],
                "name": row[1],
                "total": row[2] or 0,
                "answered": row[3] or 0,
                "correct": row[4] or 0,
            })

        conn.close()

        return {
            "total_questions": total_questions,
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "accuracy": round(total_correct / max(total_attempts, 1) * 100, 1),
            "unique_answered": unique_answered,
            "coverage": round(unique_answered / max(total_questions, 1) * 100, 1),
            "subjects": subjects,
        }

    def get_subjects(self):
        """List all subjects with question counts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM subjects ORDER BY name")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_total_questions(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM questions")
        count = c.fetchone()[0]
        conn.close()
        return count

    # ─── Helpers ───

    def _row_to_dict(self, row):
        d = dict(row)
        if "options" in d and isinstance(d["options"], str):
            d["options"] = json.loads(d["options"])
        return d
