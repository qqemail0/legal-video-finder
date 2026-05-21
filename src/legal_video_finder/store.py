from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import VideoResult


class AppStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS favorites (
                    primary_url TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    kind TEXT,
                    year TEXT,
                    description TEXT,
                    watch_url TEXT,
                    source_url TEXT,
                    confidence REAL,
                    legal_status TEXT,
                    legal_note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_history(self, query: str) -> None:
        query = query.strip()
        if not query:
            return
        with self._connect() as conn:
            conn.execute("INSERT INTO history(query) VALUES (?)", (query,))

    def list_history(self, limit: int = 30) -> list[tuple[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT query, created_at FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def add_favorite(self, item: VideoResult) -> None:
        if not item.primary_url:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO favorites(
                    primary_url, title, provider, kind, year, description, watch_url,
                    source_url, confidence, legal_status, legal_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.primary_url,
                    item.title,
                    item.provider,
                    item.kind,
                    item.year,
                    item.description,
                    item.watch_url,
                    item.source_url,
                    item.confidence,
                    item.legal_status,
                    item.legal_note,
                ),
            )

    def remove_favorite(self, primary_url: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM favorites WHERE primary_url = ?", (primary_url,))

    def list_favorites(self) -> list[VideoResult]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT title, provider, kind, year, description, watch_url, source_url,
                       confidence, legal_status, legal_note
                FROM favorites
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            VideoResult(
                title=row[0],
                provider=row[1],
                kind=row[2] or "",
                year=row[3] or "",
                description=row[4] or "",
                watch_url=row[5] or "",
                source_url=row[6] or "",
                confidence=float(row[7] or 0),
                legal_status=row[8] or "",
                legal_note=row[9] or "",
            )
            for row in rows
        ]
