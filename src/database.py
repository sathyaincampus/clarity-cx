"""Database Layer — SQLite persistence for call records and analysis results"""

import sqlite3
import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for storing call records and analysis results."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            from src.config import config
            db_path = config.database_path
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    case_id TEXT,
                    order_id TEXT,
                    caller_id TEXT,
                    agent_name TEXT,
                    duration_seconds INTEGER,
                    call_date TEXT,
                    source_type TEXT,
                    source_path TEXT,
                    language TEXT DEFAULT 'en',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS transcripts (
                    id TEXT PRIMARY KEY,
                    call_id TEXT REFERENCES calls(id),
                    full_text TEXT NOT NULL,
                    word_count INTEGER,
                    speaker_count INTEGER,
                    confidence REAL,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    call_id TEXT REFERENCES calls(id),
                    summary TEXT NOT NULL,
                    key_points TEXT,
                    action_items TEXT,
                    topics TEXT,
                    customer_intent TEXT,
                    resolution_status TEXT,
                    sentiment_trajectory TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS quality_scores (
                    id TEXT PRIMARY KEY,
                    call_id TEXT REFERENCES calls(id),
                    overall_score REAL NOT NULL,
                    empathy_score REAL,
                    empathy_justification TEXT,
                    resolution_score REAL,
                    resolution_justification TEXT,
                    professionalism_score REAL,
                    professionalism_justification TEXT,
                    compliance_score REAL,
                    compliance_justification TEXT,
                    efficiency_score REAL,
                    efficiency_justification TEXT,
                    flags TEXT,
                    recommendations TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        finally:
            conn.close()

    @staticmethod
    def _generate_case_id() -> str:
        """Generate a human-readable case ID like CX-20260310-A4F2."""
        date_part = datetime.now().strftime("%Y%m%d")
        rand_part = uuid.uuid4().hex[:4].upper()
        return f"CX-{date_part}-{rand_part}"

    @staticmethod
    def _extract_order_id(text: str) -> str:
        """Extract order ID from transcript or summary text (e.g. ORD-5678)."""
        if not text:
            return ""
        match = re.search(r'\b(ORD-\w+)\b', text, re.IGNORECASE)
        return match.group(1).upper() if match else ""

    def save_analysis(self, report: Dict[str, Any]) -> str:
        """Save a complete analysis report to the database.

        Returns:
            call_id of the saved record
        """
        conn = self._get_conn()
        call_id = str(uuid.uuid4())

        try:
            metadata = report.get("call_metadata", {})
            summary = report.get("summary", {})
            quality = report.get("quality_scores", {})

            # Generate case ID and extract order ID
            case_id = metadata.get("case_id") or self._generate_case_id()
            # Try to find order ID in transcript or summary
            transcript_text = report.get("transcript_preview", "")
            summary_text = summary.get("summary", "") if isinstance(summary, dict) else ""
            order_id = metadata.get("order_id") or self._extract_order_id(
                transcript_text + " " + summary_text
            )

            # Save call record
            conn.execute(
                """INSERT INTO calls (id, case_id, order_id, caller_id, agent_name,
                   duration_seconds, call_date, source_type, source_path, language)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    call_id,
                    case_id,
                    order_id,
                    metadata.get("caller_id", ""),
                    metadata.get("agent_name", ""),
                    metadata.get("duration_seconds", 0),
                    metadata.get("call_date") or datetime.now().isoformat(),
                    metadata.get("source", ""),
                    metadata.get("file_path", ""),
                    metadata.get("language", "en"),
                ),
            )

            # Save transcript
            transcript_preview = report.get("transcript_preview", "")
            if transcript_preview:
                conn.execute(
                    """INSERT INTO transcripts (id, call_id, full_text, word_count)
                       VALUES (?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        call_id,
                        transcript_preview,
                        report.get("transcript_word_count", 0),
                    ),
                )

            # Save analysis
            if summary:
                conn.execute(
                    """INSERT INTO analyses (id, call_id, summary, key_points,
                       action_items, topics, customer_intent, resolution_status,
                       sentiment_trajectory)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        call_id,
                        summary.get("summary", ""),
                        json.dumps(summary.get("key_points", [])),
                        json.dumps(summary.get("action_items", [])),
                        json.dumps(summary.get("topics", [])),
                        summary.get("customer_intent", ""),
                        summary.get("resolution_status", ""),
                        summary.get("sentiment_trajectory", ""),
                    ),
                )

            # Save quality scores
            if quality and quality.get("overall_score", 0) > 0:
                conn.execute(
                    """INSERT INTO quality_scores (id, call_id, overall_score,
                       empathy_score, empathy_justification,
                       resolution_score, resolution_justification,
                       professionalism_score, professionalism_justification,
                       compliance_score, compliance_justification,
                       efficiency_score, efficiency_justification,
                       flags, recommendations)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        call_id,
                        quality.get("overall_score", 0),
                        quality.get("empathy", {}).get("score", 0),
                        quality.get("empathy", {}).get("justification", ""),
                        quality.get("resolution", {}).get("score", 0),
                        quality.get("resolution", {}).get("justification", ""),
                        quality.get("professionalism", {}).get("score", 0),
                        quality.get("professionalism", {}).get("justification", ""),
                        quality.get("compliance", {}).get("score", 0),
                        quality.get("compliance", {}).get("justification", ""),
                        quality.get("efficiency", {}).get("score", 0),
                        quality.get("efficiency", {}).get("justification", ""),
                        json.dumps(quality.get("flags", [])),
                        json.dumps(quality.get("recommendations", [])),
                    ),
                )

            conn.commit()
            logger.info(f"Saved analysis for call {call_id}")
            return call_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise
        finally:
            conn.close()

    def get_call_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call analysis history with dimension scores"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT c.*, a.summary, a.customer_intent, a.resolution_status,
                          a.key_points, a.action_items, a.topics, a.sentiment_trajectory,
                          q.overall_score,
                          q.empathy_score, q.empathy_justification,
                          q.resolution_score, q.resolution_justification,
                          q.professionalism_score, q.professionalism_justification,
                          q.compliance_score, q.compliance_justification,
                          q.efficiency_score, q.efficiency_justification,
                          q.flags, q.recommendations,
                          t.full_text as transcript_text, t.word_count
                   FROM calls c
                   LEFT JOIN analyses a ON a.call_id = c.id
                   LEFT JOIN quality_scores q ON q.call_id = c.id
                   LEFT JOIN transcripts t ON t.call_id = c.id
                   ORDER BY c.created_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_call_detail(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get full detail for a single call across all tables."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                """SELECT c.*,
                          a.summary, a.key_points, a.action_items, a.topics,
                          a.customer_intent, a.resolution_status, a.sentiment_trajectory,
                          q.overall_score,
                          q.empathy_score, q.empathy_justification,
                          q.resolution_score, q.resolution_justification,
                          q.professionalism_score, q.professionalism_justification,
                          q.compliance_score, q.compliance_justification,
                          q.efficiency_score, q.efficiency_justification,
                          q.flags, q.recommendations,
                          t.full_text as transcript_text, t.word_count
                   FROM calls c
                   LEFT JOIN analyses a ON a.call_id = c.id
                   LEFT JOIN quality_scores q ON q.call_id = c.id
                   LEFT JOIN transcripts t ON t.call_id = c.id
                   WHERE c.id = ?""",
                (call_id,),
            ).fetchone()

            return dict(row) if row else None
        finally:
            conn.close()

    def get_agent_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get agents ranked by average quality score."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT c.agent_name,
                          COUNT(*) as call_count,
                          ROUND(AVG(q.overall_score), 1) as avg_score,
                          ROUND(AVG(q.empathy_score), 1) as avg_empathy,
                          ROUND(AVG(q.resolution_score), 1) as avg_resolution,
                          ROUND(AVG(q.professionalism_score), 1) as avg_professionalism
                   FROM calls c
                   JOIN quality_scores q ON q.call_id = c.id
                   WHERE c.agent_name IS NOT NULL AND c.agent_name != ''
                   GROUP BY c.agent_name
                   ORDER BY avg_score DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        conn = self._get_conn()
        try:
            # Total calls
            total = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]

            # Average score
            avg_score = conn.execute(
                "SELECT AVG(overall_score) FROM quality_scores"
            ).fetchone()[0] or 0

            # Score distribution
            excellent = conn.execute(
                "SELECT COUNT(*) FROM quality_scores WHERE overall_score >= 8"
            ).fetchone()[0]
            good = conn.execute(
                "SELECT COUNT(*) FROM quality_scores WHERE overall_score >= 6 AND overall_score < 8"
            ).fetchone()[0]
            needs_work = conn.execute(
                "SELECT COUNT(*) FROM quality_scores WHERE overall_score >= 4 AND overall_score < 6"
            ).fetchone()[0]
            critical = conn.execute(
                "SELECT COUNT(*) FROM quality_scores WHERE overall_score < 4"
            ).fetchone()[0]

            # Resolution rate
            resolved = conn.execute(
                "SELECT COUNT(*) FROM analyses WHERE resolution_status = 'resolved'"
            ).fetchone()[0]
            total_analyzed = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            resolution_rate = (resolved / total_analyzed * 100) if total_analyzed > 0 else 0

            return {
                "total_calls": total,
                "avg_score": round(avg_score, 1),
                "resolution_rate": round(resolution_rate, 1),
                "score_distribution": {
                    "excellent": excellent,
                    "good": good,
                    "needs_work": needs_work,
                    "critical": critical,
                },
            }
        finally:
            conn.close()
    def get_trends_data(self) -> Dict[str, Any]:
        """Get trends and analytics data from the database."""
        conn = self._get_conn()
        try:
            # Score trends by date (group by day)
            daily_scores = conn.execute(
                """SELECT DATE(c.call_date) as day, AVG(q.overall_score) as avg_score,
                          COUNT(*) as call_count
                   FROM calls c
                   JOIN quality_scores q ON q.call_id = c.id
                   GROUP BY DATE(c.call_date)
                   ORDER BY day
                   LIMIT 30"""
            ).fetchall()

            # Dimension averages
            dim_avgs = conn.execute(
                """SELECT
                    AVG(empathy_score) as empathy,
                    AVG(resolution_score) as resolution,
                    AVG(professionalism_score) as professionalism,
                    AVG(compliance_score) as compliance,
                    AVG(efficiency_score) as efficiency
                   FROM quality_scores"""
            ).fetchone()

            # Topic frequency from analyses
            topics_raw = conn.execute(
                "SELECT topics FROM analyses WHERE topics IS NOT NULL AND topics != ''"
            ).fetchall()

            topic_counts = {}
            for row in topics_raw:
                try:
                    topics = json.loads(row["topics"]) if row["topics"] else []
                    for topic in topics:
                        t = topic.strip().replace("_", " ").title()
                        topic_counts[t] = topic_counts.get(t, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            # Sort topics by count, take top 8
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:8]

            return {
                "daily_scores": [
                    {"day": r["day"], "avg_score": round(r["avg_score"], 1), "count": r["call_count"]}
                    for r in daily_scores
                ],
                "dimension_averages": {
                    "empathy": round(dim_avgs["empathy"] or 0, 1),
                    "resolution": round(dim_avgs["resolution"] or 0, 1),
                    "professionalism": round(dim_avgs["professionalism"] or 0, 1),
                    "compliance": round(dim_avgs["compliance"] or 0, 1),
                    "efficiency": round(dim_avgs["efficiency"] or 0, 1),
                } if dim_avgs else {},
                "top_topics": sorted_topics,
            }
        finally:
            conn.close()


# Singleton
_db = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
