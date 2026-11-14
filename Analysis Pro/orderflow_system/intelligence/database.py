"""
Persistent SQLite database layer for Trading Intelligence Learning Engine.
Supports WAL mode, FTS5 full-text indexing, versioning, audit logging, and backup/restore.
"""
from __future__ import annotations

import sqlite3
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from orderflow_system.intelligence.models import (
    DocumentRecord,
    ExtractedConcept,
    LessonRecord,
    TradeLearningRecord,
    AuditLogRecord,
    KnowledgeCategory,
)

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "trading_intelligence.db"


class IntelligenceDatabase:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            # 1. Categories
            conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            # 2. Documents
            conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                category TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                upload_date TEXT NOT NULL,
                summary TEXT DEFAULT '',
                page_count INTEGER DEFAULT 1,
                metadata_json TEXT DEFAULT '{}'
            );
            """)

            # 3. Extracted Concepts
            conn.execute("""
            CREATE TABLE IF NOT EXISTS extracted_concepts (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                category TEXT NOT NULL,
                concept_name TEXT NOT NULL,
                explanation TEXT NOT NULL,
                trading_rules_json TEXT DEFAULT '[]',
                practical_examples_json TEXT DEFAULT '[]',
                relationships_json TEXT DEFAULT '[]',
                source_page INTEGER,
                source_reference TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
            """)

            # 4. Lessons (Teach Mode)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                user_explanation TEXT NOT NULL,
                ai_understanding TEXT NOT NULL,
                trading_rules_json TEXT DEFAULT '[]',
                practical_examples_json TEXT DEFAULT '[]',
                comparison_notes TEXT DEFAULT '',
                clarifications_json TEXT DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'pending',
                version INTEGER NOT NULL DEFAULT 1,
                source_document_id TEXT,
                chart_image_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                approved_at TEXT
            );
            """)

            # 5. Lesson Version History
            conn.execute("""
            CREATE TABLE IF NOT EXISTS lesson_history (
                id TEXT PRIMARY KEY,
                lesson_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                user_explanation TEXT NOT NULL,
                ai_understanding TEXT NOT NULL,
                trading_rules_json TEXT DEFAULT '[]',
                practical_examples_json TEXT DEFAULT '[]',
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
            );
            """)

            # 6. Personal Trades Journal (Architecture for Phase 1)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS trades_journal (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                outcome TEXT NOT NULL DEFAULT 'pending',
                why_entered TEXT DEFAULT '',
                gex_levels_json TEXT DEFAULT '[]',
                footprint_signals_json TEXT DEFAULT '[]',
                volume_profile_json TEXT DEFAULT '[]',
                checklist_json TEXT DEFAULT '[]',
                pnl REAL,
                lessons_learned TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """)

            # 7. Audit Log
            conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details_json TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL
            );
            """)

            # 8. FTS5 Virtual Table for full-text search
            conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS intelligence_fts USING fts5(
                id UNINDEXED,
                entity_type UNINDEXED,
                title,
                content,
                category,
                tokenize='porter unicode61'
            );
            """)

            # Seed default categories if empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM categories;")
            if cursor.fetchone()[0] == 0:
                now = datetime.utcnow().isoformat()
                for cat in KnowledgeCategory.DEFAULT_CATEGORIES:
                    cursor.execute(
                        "INSERT OR IGNORE INTO categories (id, name, created_at) VALUES (?, ?, ?);",
                        (str(uuid.uuid4()), cat, now)
                    )
            conn.commit()

    # ── Category Management ───────────────────────────────────────────────────

    def get_categories(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories ORDER BY name ASC;")
            return [row["name"] for row in cursor.fetchall()]

    def add_category(self, name: str) -> bool:
        clean = name.strip()
        if not clean:
            return False
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO categories (id, name, created_at) VALUES (?, ?, ?);",
                    (str(uuid.uuid4()), clean, datetime.utcnow().isoformat())
                )
                self._log_audit(conn, "category", clean, "create", {"name": clean})
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    # ── Document Management ───────────────────────────────────────────────────

    def insert_document(self, doc: DocumentRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents
                (id, filename, original_name, file_type, file_path, category, size_bytes, upload_date, summary, page_count, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                doc.id, doc.filename, doc.original_name, doc.file_type, doc.file_path,
                doc.category, doc.size_bytes, doc.upload_date, doc.summary,
                doc.page_count, json.dumps(doc.metadata)
            ))
            # Index in FTS5
            conn.execute("""
                INSERT OR REPLACE INTO intelligence_fts (id, entity_type, title, content, category)
                VALUES (?, 'document', ?, ?, ?);
            """, (doc.id, doc.original_name, f"{doc.summary} {doc.original_name}", doc.category))

            self._log_audit(conn, "document", doc.id, "create", {
                "name": doc.original_name, "category": doc.category, "type": doc.file_type
            })
            conn.commit()

    def get_documents(self, category: Optional[str] = None) -> List[DocumentRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM documents WHERE category = ? ORDER BY upload_date DESC;", (category,))
            else:
                cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC;")
            rows = cursor.fetchall()
            return [
                DocumentRecord(
                    id=r["id"],
                    filename=r["filename"],
                    original_name=r["original_name"],
                    file_type=r["file_type"],
                    file_path=r["file_path"],
                    category=r["category"],
                    size_bytes=r["size_bytes"],
                    upload_date=r["upload_date"],
                    summary=r["summary"],
                    page_count=r["page_count"],
                    metadata=json.loads(r["metadata_json"] or "{}")
                )
                for r in rows
            ]

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?;", (doc_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return DocumentRecord(
                id=r["id"],
                filename=r["filename"],
                original_name=r["original_name"],
                file_type=r["file_type"],
                file_path=r["file_path"],
                category=r["category"],
                size_bytes=r["size_bytes"],
                upload_date=r["upload_date"],
                summary=r["summary"],
                page_count=r["page_count"],
                metadata=json.loads(r["metadata_json"] or "{}")
            )

    def delete_document(self, doc_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?;", (doc_id,))
            conn.execute("DELETE FROM extracted_concepts WHERE document_id = ?;", (doc_id,))
            conn.execute("DELETE FROM intelligence_fts WHERE id = ?;", (doc_id,))
            self._log_audit(conn, "document", doc_id, "delete", {})
            conn.commit()
            return True

    # ── Extracted Concepts ────────────────────────────────────────────────────

    def insert_concepts(self, concepts: List[ExtractedConcept]) -> None:
        with self._get_connection() as conn:
            for c in concepts:
                conn.execute("""
                    INSERT OR REPLACE INTO extracted_concepts
                    (id, document_id, category, concept_name, explanation, trading_rules_json, practical_examples_json, relationships_json, source_page, source_reference, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    c.id, c.document_id, c.category, c.concept_name, c.explanation,
                    json.dumps(c.trading_rules), json.dumps(c.practical_examples),
                    json.dumps(c.relationships), c.source_page, c.source_reference,
                    c.confidence, c.created_at or datetime.utcnow().isoformat()
                ))
                # Index in FTS5
                full_content = f"{c.explanation} Rules: {' '.join(c.trading_rules)} Examples: {' '.join(c.practical_examples)}"
                conn.execute("""
                    INSERT OR REPLACE INTO intelligence_fts (id, entity_type, title, content, category)
                    VALUES (?, 'concept', ?, ?, ?);
                """, (c.id, c.concept_name, full_content, c.category))

            conn.commit()

    def get_concepts(self, document_id: Optional[str] = None, category: Optional[str] = None) -> List[ExtractedConcept]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM extracted_concepts WHERE 1=1"
            params = []
            if document_id:
                query += " AND document_id = ?"
                params.append(document_id)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY created_at DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                ExtractedConcept(
                    id=r["id"],
                    document_id=r["document_id"],
                    category=r["category"],
                    concept_name=r["concept_name"],
                    explanation=r["explanation"],
                    trading_rules=json.loads(r["trading_rules_json"] or "[]"),
                    practical_examples=json.loads(r["practical_examples_json"] or "[]"),
                    relationships=json.loads(r["relationships_json"] or "[]"),
                    source_page=r["source_page"],
                    source_reference=r["source_reference"],
                    confidence=r["confidence"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ── Lesson Management (Teach Mode & Approved Memory) ──────────────────────

    def insert_lesson(self, lesson: LessonRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lessons
                (id, title, category, user_explanation, ai_understanding, trading_rules_json, practical_examples_json, comparison_notes, clarifications_json, status, version, source_document_id, chart_image_path, created_at, updated_at, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                lesson.id, lesson.title, lesson.category, lesson.user_explanation,
                lesson.ai_understanding, json.dumps(lesson.trading_rules),
                json.dumps(lesson.practical_examples), lesson.comparison_notes,
                json.dumps(lesson.clarifications_asked), lesson.status,
                lesson.version, lesson.source_document_id, lesson.chart_image_path,
                lesson.created_at, lesson.updated_at, lesson.approved_at
            ))

            # Record version history
            conn.execute("""
                INSERT INTO lesson_history
                (id, lesson_id, version, title, category, user_explanation, ai_understanding, trading_rules_json, practical_examples_json, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                str(uuid.uuid4()), lesson.id, lesson.version, lesson.title, lesson.category,
                lesson.user_explanation, lesson.ai_understanding, json.dumps(lesson.trading_rules),
                json.dumps(lesson.practical_examples), lesson.status, lesson.updated_at
            ))

            # Index in FTS5 if approved or pending
            fts_content = f"{lesson.ai_understanding} {lesson.user_explanation} Rules: {' '.join(lesson.trading_rules)}"
            conn.execute("""
                INSERT OR REPLACE INTO intelligence_fts (id, entity_type, title, content, category)
                VALUES (?, 'lesson', ?, ?, ?);
            """, (lesson.id, lesson.title, fts_content, lesson.category))

            self._log_audit(conn, "lesson", lesson.id, "create" if lesson.version == 1 else "update", {
                "title": lesson.title, "status": lesson.status, "version": lesson.version
            })
            conn.commit()

    def get_lessons(self, category: Optional[str] = None, status: Optional[str] = None) -> List[LessonRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM lessons WHERE 1=1"
            params = []
            if category:
                query += " AND category = ?"
                params.append(category)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY updated_at DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                LessonRecord(
                    id=r["id"],
                    title=r["title"],
                    category=r["category"],
                    user_explanation=r["user_explanation"],
                    ai_understanding=r["ai_understanding"],
                    trading_rules=json.loads(r["trading_rules_json"] or "[]"),
                    practical_examples=json.loads(r["practical_examples_json"] or "[]"),
                    comparison_notes=r["comparison_notes"],
                    clarifications_asked=json.loads(r["clarifications_json"] or "[]"),
                    status=r["status"],
                    version=r["version"],
                    source_document_id=r["source_document_id"],
                    chart_image_path=r["chart_image_path"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    approved_at=r["approved_at"],
                )
                for r in rows
            ]

    def get_lesson(self, lesson_id: str) -> Optional[LessonRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lessons WHERE id = ?;", (lesson_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return LessonRecord(
                id=r["id"],
                title=r["title"],
                category=r["category"],
                user_explanation=r["user_explanation"],
                ai_understanding=r["ai_understanding"],
                trading_rules=json.loads(r["trading_rules_json"] or "[]"),
                practical_examples=json.loads(r["practical_examples_json"] or "[]"),
                comparison_notes=r["comparison_notes"],
                clarifications_asked=json.loads(r["clarifications_json"] or "[]"),
                status=r["status"],
                version=r["version"],
                source_document_id=r["source_document_id"],
                chart_image_path=r["chart_image_path"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                approved_at=r["approved_at"],
            )

    def approve_lesson(self, lesson_id: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, title FROM lessons WHERE id = ?;", (lesson_id,))
            row = cursor.fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE lessons SET status = 'approved', approved_at = ?, updated_at = ? WHERE id = ?;",
                (now, now, lesson_id)
            )
            self._log_audit(conn, "lesson", lesson_id, "approve", {"title": row["title"], "version": row["version"]})
            conn.commit()
            return True

    def reject_lesson(self, lesson_id: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM lessons WHERE id = ?;", (lesson_id,))
            row = cursor.fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE lessons SET status = 'rejected', updated_at = ? WHERE id = ?;",
                (now, lesson_id)
            )
            self._log_audit(conn, "lesson", lesson_id, "reject", {"title": row["title"]})
            conn.commit()
            return True

    def delete_lesson(self, lesson_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM lessons WHERE id = ?;", (lesson_id,))
            conn.execute("DELETE FROM lesson_history WHERE lesson_id = ?;", (lesson_id,))
            conn.execute("DELETE FROM intelligence_fts WHERE id = ?;", (lesson_id,))
            self._log_audit(conn, "lesson", lesson_id, "delete", {})
            conn.commit()
            return True

    # ── Trade Learning Journal ────────────────────────────────────────────────

    def insert_trade(self, trade: TradeLearningRecord) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO trades_journal
                (id, timestamp, symbol, direction, entry_price, exit_price, outcome, why_entered, gex_levels_json, footprint_signals_json, volume_profile_json, checklist_json, pnl, lessons_learned, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                trade.id, trade.timestamp, trade.symbol, trade.direction,
                trade.entry_price, trade.exit_price, trade.outcome, trade.why_entered,
                json.dumps(trade.gex_levels_used), json.dumps(trade.footprint_signals),
                json.dumps(trade.volume_profile_levels), json.dumps(trade.checklist_satisfied),
                trade.pnl, trade.lessons_learned, trade.created_at
            ))
            self._log_audit(conn, "trade", trade.id, "create", {
                "symbol": trade.symbol, "direction": trade.direction, "outcome": trade.outcome
            })
            conn.commit()

    def get_trades(self, limit: int = 50) -> List[TradeLearningRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades_journal ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            return [
                TradeLearningRecord(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    symbol=r["symbol"],
                    direction=r["direction"],
                    entry_price=r["entry_price"],
                    exit_price=r["exit_price"],
                    outcome=r["outcome"],
                    why_entered=r["why_entered"],
                    gex_levels_used=json.loads(r["gex_levels_json"] or "[]"),
                    footprint_signals=json.loads(r["footprint_signals_json"] or "[]"),
                    volume_profile_levels=json.loads(r["volume_profile_json"] or "[]"),
                    checklist_satisfied=json.loads(r["checklist_json"] or "[]"),
                    pnl=r["pnl"],
                    lessons_learned=r["lessons_learned"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # ── Search & Knowledge Retrieval (RAG) ───────────────────────────────────

    def search_knowledge(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search across FTS5 index for approved lessons, concepts, and documents."""
        clean_query = "".join(c for c in query if c.isalnum() or c.isspace()).strip()
        if not clean_query:
            return []

        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # FTS5 match query
            match_expr = f'"{clean_query}"' if " " in clean_query else f"{clean_query}*"
            sql = """
                SELECT id, entity_type, title, category, snippet(intelligence_fts, 3, '<b>', '</b>', '...', 20) as snippet
                FROM intelligence_fts
                WHERE intelligence_fts MATCH ?
            """
            params = [match_expr]
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " LIMIT ?;"
            params.append(limit)

            try:
                cursor.execute(sql, params)
                fts_rows = cursor.fetchall()
            except sqlite3.OperationalError:
                # Fallback to simple LIKE query if FTS expression is tricky
                sql = """
                    SELECT id, entity_type, title, category, substr(content, 1, 150) as snippet
                    FROM intelligence_fts
                    WHERE (title LIKE ? OR content LIKE ?)
                """
                like_param = f"%{clean_query}%"
                params = [like_param, like_param]
                if category:
                    sql += " AND category = ?"
                    params.append(category)
                sql += " LIMIT ?;"
                params.append(limit)
                cursor.execute(sql, params)
                fts_rows = cursor.fetchall()

            for r in fts_rows:
                entity_type = r["entity_type"]
                entity_id = r["id"]
                data: Dict[str, Any] = {
                    "id": entity_id,
                    "entity_type": entity_type,
                    "title": r["title"],
                    "category": r["category"],
                    "snippet": r["snippet"],
                }

                if entity_type == "lesson":
                    lesson = self.get_lesson(entity_id)
                    if lesson and lesson.status == "approved":
                        data["details"] = lesson.model_dump()
                        results.append(data)
                elif entity_type == "concept":
                    cursor.execute("SELECT * FROM extracted_concepts WHERE id = ?;", (entity_id,))
                    c_row = cursor.fetchone()
                    if c_row:
                        data["details"] = {
                            "concept_name": c_row["concept_name"],
                            "explanation": c_row["explanation"],
                            "trading_rules": json.loads(c_row["trading_rules_json"] or "[]"),
                            "source_reference": c_row["source_reference"],
                        }
                        results.append(data)
                elif entity_type == "document":
                    doc = self.get_document(entity_id)
                    if doc:
                        data["details"] = {"summary": doc.summary, "name": doc.original_name}
                        results.append(data)

        return results

    # ── Audit Log ─────────────────────────────────────────────────────────────

    def _log_audit(self, conn: sqlite3.Connection, entity_type: str, entity_id: str, action: str, details: Dict[str, Any]) -> None:
        conn.execute("""
            INSERT INTO audit_log (id, entity_type, entity_id, action, details_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            str(uuid.uuid4()), entity_type, entity_id, action,
            json.dumps(details), datetime.utcnow().isoformat()
        ))

    def get_audit_log(self, limit: int = 100) -> List[AuditLogRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            return [
                AuditLogRecord(
                    id=r["id"],
                    entity_type=r["entity_type"],
                    entity_id=r["entity_id"],
                    action=r["action"],
                    details=json.loads(r["details_json"] or "{}"),
                    timestamp=r["timestamp"]
                )
                for r in rows
            ]

    # ── Database Statistics ───────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents;")
            doc_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM extracted_concepts;")
            concept_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM lessons WHERE status = 'approved';")
            approved_lessons = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM lessons WHERE status = 'pending';")
            pending_lessons = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM trades_journal;")
            trades_count = cursor.fetchone()[0]

            cursor.execute("SELECT category, COUNT(*) as cnt FROM documents GROUP BY category;")
            cat_docs = {r["category"]: r["cnt"] for r in cursor.fetchall()}

            return {
                "total_documents": doc_count,
                "total_concepts": concept_count,
                "approved_lessons": approved_lessons,
                "pending_lessons": pending_lessons,
                "total_trades_recorded": trades_count,
                "documents_by_category": cat_docs,
            }

    # ── Backup & Restoration ──────────────────────────────────────────────────

    def export_database_dict(self) -> Dict[str, Any]:
        """Export all tables into a JSON-serializable dictionary for portable backup."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            def fetch_table(table_name):
                cursor.execute(f"SELECT * FROM {table_name};")
                return [dict(row) for row in cursor.fetchall()]

            return {
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "categories": fetch_table("categories"),
                "documents": fetch_table("documents"),
                "extracted_concepts": fetch_table("extracted_concepts"),
                "lessons": fetch_table("lessons"),
                "lesson_history": fetch_table("lesson_history"),
                "trades_journal": fetch_table("trades_journal"),
                "audit_log": fetch_table("audit_log"),
            }

    def import_database_dict(self, data: Dict[str, Any]) -> bool:
        """Safely restore/import data from a backup dictionary."""
        if not isinstance(data, dict) or "categories" not in data:
            return False

        with self._get_connection() as conn:
            # Insert categories
            for cat in data.get("categories", []):
                conn.execute(
                    "INSERT OR IGNORE INTO categories (id, name, created_at) VALUES (?, ?, ?);",
                    (cat["id"], cat["name"], cat["created_at"])
                )

            # Insert documents
            for doc in data.get("documents", []):
                conn.execute("""
                    INSERT OR REPLACE INTO documents
                    (id, filename, original_name, file_type, file_path, category, size_bytes, upload_date, summary, page_count, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    doc["id"], doc["filename"], doc["original_name"], doc["file_type"],
                    doc["file_path"], doc["category"], doc["size_bytes"], doc["upload_date"],
                    doc.get("summary", ""), doc.get("page_count", 1), doc.get("metadata_json", "{}")
                ))

            # Insert concepts
            for c in data.get("extracted_concepts", []):
                conn.execute("""
                    INSERT OR REPLACE INTO extracted_concepts
                    (id, document_id, category, concept_name, explanation, trading_rules_json, practical_examples_json, relationships_json, source_page, source_reference, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    c["id"], c["document_id"], c["category"], c["concept_name"], c["explanation"],
                    c["trading_rules_json"], c["practical_examples_json"], c["relationships_json"],
                    c.get("source_page"), c.get("source_reference", ""), c.get("confidence", 1.0),
                    c["created_at"]
                ))

            # Insert lessons
            for l in data.get("lessons", []):
                conn.execute("""
                    INSERT OR REPLACE INTO lessons
                    (id, title, category, user_explanation, ai_understanding, trading_rules_json, practical_examples_json, comparison_notes, clarifications_json, status, version, source_document_id, chart_image_path, created_at, updated_at, approved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    l["id"], l["title"], l["category"], l["user_explanation"], l["ai_understanding"],
                    l["trading_rules_json"], l["practical_examples_json"], l.get("comparison_notes", ""),
                    l.get("clarifications_json", "[]"), l["status"], l.get("version", 1),
                    l.get("source_document_id"), l.get("chart_image_path"), l["created_at"],
                    l["updated_at"], l.get("approved_at")
                ))

            # Insert trades
            for t in data.get("trades_journal", []):
                conn.execute("""
                    INSERT OR REPLACE INTO trades_journal
                    (id, timestamp, symbol, direction, entry_price, exit_price, outcome, why_entered, gex_levels_json, footprint_signals_json, volume_profile_json, checklist_json, pnl, lessons_learned, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    t["id"], t["timestamp"], t["symbol"], t["direction"], t["entry_price"],
                    t.get("exit_price"), t["outcome"], t.get("why_entered", ""),
                    t.get("gex_levels_json", "[]"), t.get("footprint_signals_json", "[]"),
                    t.get("volume_profile_json", "[]"), t.get("checklist_json", "[]"),
                    t.get("pnl"), t.get("lessons_learned", ""), t["created_at"]
                ))

            self._log_audit(conn, "database", "all", "restore", {"count": len(data.get("documents", []))})
            conn.commit()

        # Rebuild FTS index
        self._rebuild_fts()
        return True

    def _rebuild_fts(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM intelligence_fts;")
            # Re-index docs
            conn.execute("""
                INSERT INTO intelligence_fts (id, entity_type, title, content, category)
                SELECT id, 'document', original_name, summary || ' ' || original_name, category
                FROM documents;
            """)
            # Re-index concepts
            conn.execute("""
                INSERT INTO intelligence_fts (id, entity_type, title, content, category)
                SELECT id, 'concept', concept_name, explanation || ' ' || trading_rules_json, category
                FROM extracted_concepts;
            """)
            # Re-index lessons
            conn.execute("""
                INSERT INTO intelligence_fts (id, entity_type, title, content, category)
                SELECT id, 'lesson', title, ai_understanding || ' ' || user_explanation || ' ' || trading_rules_json, category
                FROM lessons;
            """)
            conn.commit()
