"""SQLite-based analytics tracking for marketing content performance.

Tracks all generated suggestions, published posts, and their engagement metrics.
Provides data for the Vercel performance dashboard via JSON API.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS suggestions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    content_category TEXT DEFAULT 'general',
    blog_title TEXT,
    blog_hook TEXT,
    blog_outline TEXT,
    blog_target_audience TEXT,
    blog_ai_angle TEXT,
    blog_seo_keywords TEXT,
    linkedin_text TEXT,
    linkedin_hashtags TEXT,
    twitter_text TEXT,
    twitter_hashtags TEXT,
    twitter_post_type TEXT,
    image_prompt TEXT,
    source_articles TEXT,
    approval_status TEXT DEFAULT 'pending',
    approved_by TEXT,
    approved_at TEXT
);

CREATE TABLE IF NOT EXISTS published_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    post_type TEXT NOT NULL,
    content_category TEXT DEFAULT 'general',
    title TEXT,
    content_preview TEXT,
    url TEXT,
    post_id TEXT,
    published_at TEXT NOT NULL,
    image_used INTEGER DEFAULT 0,
    FOREIGN KEY (suggestion_id) REFERENCES suggestions(id)
);

CREATE TABLE IF NOT EXISTS engagement_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    published_post_id INTEGER NOT NULL,
    measured_at TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    FOREIGN KEY (published_post_id) REFERENCES published_posts(id)
);

CREATE TABLE IF NOT EXISTS scan_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    articles_found INTEGER DEFAULT 0,
    suggestions_generated INTEGER DEFAULT 0,
    sources_scanned INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_suggestions_category ON suggestions(content_category);
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(approval_status);
CREATE INDEX IF NOT EXISTS idx_published_platform ON published_posts(platform);
CREATE INDEX IF NOT EXISTS idx_published_category ON published_posts(content_category);
CREATE INDEX IF NOT EXISTS idx_engagement_post ON engagement_metrics(published_post_id);
"""


class AnalyticsDB:
    """SQLite database for tracking marketing content performance."""

    def __init__(self, db_path: str = "marketing_analytics.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(DB_SCHEMA)
        logger.info(f"Analytics DB initialized at {self.db_path}")

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_suggestion(self, suggestion) -> None:
        """Record a generated content suggestion."""
        twitter = suggestion.twitter_post
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO suggestions
                (id, created_at, content_category, blog_title, blog_hook, blog_outline,
                 blog_target_audience, blog_ai_angle, blog_seo_keywords,
                 linkedin_text, linkedin_hashtags,
                 twitter_text, twitter_hashtags, twitter_post_type,
                 image_prompt, source_articles, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    suggestion.id,
                    suggestion.created_at,
                    getattr(suggestion, 'content_category', 'general'),
                    suggestion.blog_idea.title,
                    suggestion.blog_idea.hook,
                    json.dumps(suggestion.blog_idea.outline),
                    suggestion.blog_idea.target_audience,
                    suggestion.blog_idea.ai_angle,
                    json.dumps(suggestion.blog_idea.seo_keywords),
                    suggestion.linkedin_post.text,
                    json.dumps(suggestion.linkedin_post.hashtags),
                    twitter.text if twitter else None,
                    json.dumps(twitter.hashtags) if twitter else None,
                    twitter.post_type if twitter else None,
                    suggestion.image_prompt,
                    json.dumps([
                        {"title": a.title, "url": a.url, "source": a.source}
                        for a in suggestion.source_articles
                    ]),
                    suggestion.approval_status,
                ),
            )

    def record_approval(self, suggestion_id: str, action: str, user_name: str) -> None:
        """Record an approval/rejection action."""
        status = "approved" if action != "reject" else "rejected"
        with self._conn() as conn:
            conn.execute(
                "UPDATE suggestions SET approval_status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
                (status, user_name, datetime.now().isoformat(), suggestion_id),
            )

    def record_published_post(
        self,
        suggestion_id: str,
        platform: str,
        post_type: str,
        content_category: str,
        title: str,
        content_preview: str,
        url: Optional[str],
        post_id: Optional[str],
        image_used: bool = False,
    ) -> int:
        """Record a published post. Returns the published_post_id."""
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO published_posts
                (suggestion_id, platform, post_type, content_category, title,
                 content_preview, url, post_id, published_at, image_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    suggestion_id,
                    platform,
                    post_type,
                    content_category,
                    title,
                    content_preview[:500],
                    url,
                    post_id,
                    datetime.now().isoformat(),
                    1 if image_used else 0,
                ),
            )
            return cursor.lastrowid

    def record_engagement(
        self,
        published_post_id: int,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        impressions: int = 0,
        clicks: int = 0,
        saves: int = 0,
    ) -> None:
        """Record engagement metrics for a published post."""
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO engagement_metrics
                (published_post_id, measured_at, likes, comments, shares, impressions, clicks, saves)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (published_post_id, datetime.now().isoformat(), likes, comments, shares, impressions, clicks, saves),
            )

    def record_scan_cycle(self, articles_found: int, suggestions_generated: int, sources_scanned: int) -> None:
        """Record a completed scan cycle."""
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO scan_cycles (started_at, completed_at, articles_found, suggestions_generated, sources_scanned)
                VALUES (?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), datetime.now().isoformat(), articles_found, suggestions_generated, sources_scanned),
            )

    # ---- Dashboard API methods ----

    def get_dashboard_summary(self) -> dict:
        """Get summary stats for the dashboard."""
        with self._conn() as conn:
            total_suggestions = conn.execute("SELECT COUNT(*) FROM suggestions").fetchone()[0]
            approved = conn.execute("SELECT COUNT(*) FROM suggestions WHERE approval_status = 'approved'").fetchone()[0]
            rejected = conn.execute("SELECT COUNT(*) FROM suggestions WHERE approval_status = 'rejected'").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM suggestions WHERE approval_status = 'pending'").fetchone()[0]
            total_published = conn.execute("SELECT COUNT(*) FROM published_posts").fetchone()[0]
            total_scans = conn.execute("SELECT COUNT(*) FROM scan_cycles").fetchone()[0]

            # Engagement totals
            eng = conn.execute(
                "SELECT COALESCE(SUM(likes),0), COALESCE(SUM(comments),0), COALESCE(SUM(shares),0), COALESCE(SUM(impressions),0), COALESCE(SUM(clicks),0) FROM engagement_metrics"
            ).fetchone()

        return {
            "total_suggestions": total_suggestions,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "total_published": total_published,
            "total_scans": total_scans,
            "total_engagement": {
                "likes": eng[0],
                "comments": eng[1],
                "shares": eng[2],
                "impressions": eng[3],
                "clicks": eng[4],
            },
        }

    def get_posts_by_category(self) -> list[dict]:
        """Get published posts grouped by content category."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT content_category, COUNT(*) as count, platform
                FROM published_posts
                GROUP BY content_category, platform
                ORDER BY count DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_posts(self, limit: int = 20) -> list[dict]:
        """Get recent published posts with latest engagement."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT p.*,
                    COALESCE(e.likes, 0) as likes,
                    COALESCE(e.comments, 0) as comments,
                    COALESCE(e.shares, 0) as shares,
                    COALESCE(e.impressions, 0) as impressions,
                    COALESCE(e.clicks, 0) as clicks
                FROM published_posts p
                LEFT JOIN (
                    SELECT published_post_id, likes, comments, shares, impressions, clicks
                    FROM engagement_metrics
                    WHERE id IN (SELECT MAX(id) FROM engagement_metrics GROUP BY published_post_id)
                ) e ON p.id = e.published_post_id
                ORDER BY p.published_at DESC
                LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_category_performance(self) -> list[dict]:
        """Get engagement performance by content category."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT p.content_category,
                    COUNT(DISTINCT p.id) as post_count,
                    COALESCE(SUM(e.likes), 0) as total_likes,
                    COALESCE(SUM(e.comments), 0) as total_comments,
                    COALESCE(SUM(e.shares), 0) as total_shares,
                    COALESCE(SUM(e.impressions), 0) as total_impressions,
                    COALESCE(AVG(e.likes), 0) as avg_likes,
                    COALESCE(AVG(e.comments), 0) as avg_comments
                FROM published_posts p
                LEFT JOIN engagement_metrics e ON p.id = e.published_post_id
                GROUP BY p.content_category
                ORDER BY total_likes DESC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_platform_stats(self) -> list[dict]:
        """Get stats grouped by platform."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT platform, COUNT(*) as count,
                    COALESCE(SUM(e.likes), 0) as total_likes,
                    COALESCE(SUM(e.comments), 0) as total_comments
                FROM published_posts p
                LEFT JOIN engagement_metrics e ON p.id = e.published_post_id
                GROUP BY platform"""
            ).fetchall()
        return [dict(r) for r in rows]

    def get_timeline_data(self, days: int = 30) -> list[dict]:
        """Get daily post counts for timeline chart."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT DATE(published_at) as date, COUNT(*) as posts,
                    platform, content_category
                FROM published_posts
                WHERE published_at >= datetime('now', ?)
                GROUP BY DATE(published_at), platform
                ORDER BY date""",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_suggestions(self, limit: int = 50) -> list[dict]:
        """Get all suggestions with status."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, created_at, content_category, blog_title,
                    approval_status, approved_by, approved_at
                FROM suggestions
                ORDER BY created_at DESC
                LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
