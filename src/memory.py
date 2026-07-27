"""Long-term memory for the research digest agent.

A persistent SQLite store that gives the agent durable memory across runs:
- dedup: remember which article URLs have already been processed (only push new)
- archive: accumulate full content + summaries into a searchable corpus (the KB)
- run log: record each run for observability

This file is the heart of the "长期记忆" requirement.
"""

import datetime
import sqlite3


class Memory:
    def __init__(self, db_path="kb.db"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url         TEXT UNIQUE NOT NULL,
                source      TEXT,
                title       TEXT,
                published   TEXT,
                fetched_at  TEXT NOT NULL,
                content     TEXT,
                summary     TEXT
            );
            CREATE TABLE IF NOT EXISTS runs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at     TEXT NOT NULL,
                new_count  INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at);
            """
        )
        # Migration: category classifies entries learned ad hoc while answering
        # questions (architecture/error-code/api/session-insight/general), as
        # opposed to the RSS-sourced daily digest articles (category NULL).
        try:
            self.conn.execute("ALTER TABLE articles ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        self.conn.commit()

    def is_seen(self, url):
        cur = self.conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
        return cur.fetchone() is not None

    def add_article(self, url, source=None, title=None, published=None,
                    content=None, summary=None, category=None):
        self.conn.execute(
            """INSERT OR IGNORE INTO articles
               (url, source, title, published, fetched_at, content, summary, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (url, source, title, published,
             datetime.datetime.utcnow().isoformat(), content, summary, category),
        )
        self.conn.commit()

    def update_summary(self, url, summary):
        self.conn.execute("UPDATE articles SET summary = ? WHERE url = ?", (summary, url))
        self.conn.commit()

    def log_run(self, new_count):
        self.conn.execute(
            "INSERT INTO runs (ran_at, new_count) VALUES (?, ?)",
            (datetime.datetime.utcnow().isoformat(), new_count),
        )
        self.conn.commit()

    def recent(self, limit=20):
        cur = self.conn.execute(
            "SELECT * FROM articles ORDER BY fetched_at DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in cur.fetchall()]

    def search(self, keyword, limit=20):
        """Simple keyword recall over the long-term corpus."""
        like = f"%{keyword}%"
        cur = self.conn.execute(
            """SELECT * FROM articles
               WHERE title LIKE ? OR content LIKE ? OR summary LIKE ?
               ORDER BY fetched_at DESC LIMIT ?""",
            (like, like, like, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def stats(self):
        total = self.conn.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
        runs = self.conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"]
        return {"total_articles": total, "total_runs": runs}

    def close(self):
        self.conn.close()
