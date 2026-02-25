"""SQLite storage layer."""

import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager


class Storage:
    """SQLite storage for Reddit data."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path("data") / "reddit_scraper.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            subreddit TEXT NOT NULL,
            title TEXT NOT NULL,
            selftext TEXT,
            author TEXT,
            created_utc INTEGER,
            score INTEGER,
            num_comments INTEGER,
            url TEXT,
            permalink TEXT,
            fetched_at_utc INTEGER,
            source TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
        CREATE INDEX IF NOT EXISTS idx_posts_fetched ON posts(fetched_at_utc);
        
        CREATE TABLE IF NOT EXISTS runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT,
            subreddit TEXT,
            query TEXT,
            sort TEXT,
            time TEXT,
            limit_n INTEGER,
            ran_at_utc INTEGER,
            notes TEXT
        );
        
        CREATE TABLE IF NOT EXISTS subreddits (
            name TEXT PRIMARY KEY,
            title TEXT,
            subscribers INTEGER,
            active_user_count INTEGER,
            created_utc INTEGER,
            over18 INTEGER,
            public_description TEXT,
            url TEXT,
            fetched_at_utc INTEGER,
            source TEXT
        );
        
        CREATE TABLE IF NOT EXISTS comments (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            author TEXT,
            body TEXT,
            created_utc INTEGER,
            score INTEGER,
            parent_id TEXT,
            fetched_at_utc INTEGER
        );
        
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id TEXT,
            tag TEXT,
            PRIMARY KEY(post_id, tag)
        );
        """

        with self._connection() as conn:
            conn.executescript(schema)

    def save_run(
        self,
        run_type,
        subreddit=None,
        query=None,
        sort=None,
        time=None,
        limit_n=None,
        notes=None,
    ):
        """Record a run in the database."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_type, subreddit, query, sort, time, limit_n, ran_at_utc, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    run_type,
                    subreddit,
                    query,
                    sort,
                    time,
                    limit_n,
                    int(datetime.utcnow().timestamp()),
                    notes,
                ),
            )

    def save_post(self, post_data, source="fetch"):
        """Save a post, ignoring duplicates."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO posts 
                (post_id, subreddit, title, selftext, author, created_utc, score, 
                 num_comments, url, permalink, fetched_at_utc, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    post_data.get("id"),
                    post_data.get("subreddit"),
                    post_data.get("title", ""),
                    post_data.get("selftext", ""),
                    post_data.get("author"),
                    post_data.get("created_utc"),
                    post_data.get("score"),
                    post_data.get("num_comments"),
                    post_data.get("url"),
                    post_data.get("permalink"),
                    int(datetime.utcnow().timestamp()),
                    source,
                ),
            )
            return conn.total_changes > 0

    def save_subreddit(self, name, data, source="subreddits_search"):
        """Save subreddit metadata."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO subreddits 
                (name, title, subscribers, active_user_count, created_utc, over18,
                 public_description, url, fetched_at_utc, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    name,
                    data.get("title"),
                    data.get("subscribers"),
                    data.get("active_user_count"),
                    data.get("created_utc"),
                    1 if data.get("over18") else 0,
                    data.get("public_description", ""),
                    data.get("url"),
                    int(datetime.utcnow().timestamp()),
                    source,
                ),
            )

    def save_comment(self, comment_data, post_id):
        """Save a comment, ignoring duplicates."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO comments 
                (comment_id, post_id, author, body, created_utc, score, parent_id, fetched_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    comment_data.get("id"),
                    post_id,
                    comment_data.get("author"),
                    comment_data.get("body", ""),
                    comment_data.get("created_utc"),
                    comment_data.get("score"),
                    comment_data.get("parent_id"),
                    int(datetime.utcnow().timestamp()),
                ),
            )

    def save_tag(self, post_id, tag):
        """Save a tag for a post."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO post_tags (post_id, tag)
                VALUES (?, ?)
            """,
                (post_id, tag),
            )

    def get_posts_for_tagging(self, limit=1000):
        """Get posts that haven't been tagged yet."""
        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT p.post_id, p.title, p.selftext
                FROM posts p
                LEFT JOIN post_tags pt ON p.post_id = pt.post_id
                WHERE pt.post_id IS NULL
                LIMIT ?
            """,
                (limit,),
            )
            return cursor.fetchall()

    def get_stats(self, days=7):
        """Get statistics for reporting."""
        cutoff = int((datetime.utcnow().timestamp()) - (days * 86400))

        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM posts WHERE fetched_at_utc >= ?", (cutoff,)
            )
            total_posts = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT subreddit, COUNT(*) as cnt
                FROM posts
                WHERE fetched_at_utc >= ?
                GROUP BY subreddit
                ORDER BY cnt DESC
                LIMIT 10
            """,
                (cutoff,),
            )
            top_subreddits = cursor.fetchall()

            cursor = conn.execute("""
                SELECT name, subscribers
                FROM subreddits
                ORDER BY subscribers DESC
                LIMIT 10
            """)
            top_by_subs = cursor.fetchall()

            cursor = conn.execute("""
                SELECT tag, COUNT(*) as cnt
                FROM post_tags
                GROUP BY tag
                ORDER BY cnt DESC
                LIMIT 10
            """)
            tag_freq = cursor.fetchall()

            return {
                "total_posts": total_posts,
                "top_subreddits": top_subreddits,
                "top_by_subscribers": top_by_subs,
                "tag_frequency": tag_freq,
            }

    def export_table(self, table_name):
        """Export a table as list of dicts."""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            return [dict(row) for row in cursor.fetchall()]
