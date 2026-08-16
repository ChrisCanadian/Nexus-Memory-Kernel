import sqlite3
import uuid
from pathlib import Path

from .models import MemoryRecord, TrustedScope
from .receipts import utc_now

class MemoryStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS memory_record (
                memory_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                supersedes_id TEXT
            )
            '''
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_user_created ON memory_record(user_id, created_at)"
        )
        self._conn.commit()

    @staticmethod
    def _row(row):
        return MemoryRecord(**dict(row))

    def store(self, scope: TrustedScope, *, content: str, source: str = "host") -> MemoryRecord:
        now = utc_now()
        rec = MemoryRecord(
            memory_id=str(uuid.uuid4()),
            user_id=scope.user_id,
            session_id=scope.session_id,
            content=content,
            created_at=now,
            updated_at=now,
            status="active",
            source=source,
        )
        self._conn.execute(
            "INSERT INTO memory_record VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rec.memory_id, rec.user_id, rec.session_id, rec.content,
                rec.created_at, rec.updated_at, rec.status, rec.source, rec.supersedes_id
            ),
        )
        self._conn.commit()
        return rec

    def get(self, scope: TrustedScope, memory_id: str) -> MemoryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM memory_record WHERE memory_id=? AND user_id=?",
            (memory_id, scope.user_id),
        ).fetchone()
        return self._row(row) if row else None

    def search(
        self,
        scope: TrustedScope,
        *,
        query: str = "",
        start_at: str | None = None,
        end_at: str | None = None,
        limit: int = 10,
        include_superseded: bool = False,
    ) -> list[MemoryRecord]:
        clauses = ["user_id = ?"]
        args = [scope.user_id]

        if query:
            clauses.append("LOWER(content) LIKE ?")
            args.append(f"%{query.lower()}%")
        if start_at:
            clauses.append("created_at >= ?")
            args.append(start_at)
        if end_at:
            clauses.append("created_at <= ?")
            args.append(end_at)
        if not include_superseded:
            clauses.append("status = 'active'")

        sql = "SELECT * FROM memory_record WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(max(1, min(int(limit), 100)))

        rows = self._conn.execute(sql, args).fetchall()
        return [self._row(row) for row in rows]

    def context(self, scope: TrustedScope, *, limit: int = 20) -> list[MemoryRecord]:
        if not scope.session_id:
            return []
        rows = self._conn.execute(
            '''
            SELECT * FROM memory_record
            WHERE user_id=? AND session_id=? AND status='active'
            ORDER BY created_at DESC LIMIT ?
            ''',
            (scope.user_id, scope.session_id, max(1, min(int(limit), 100))),
        ).fetchall()
        return [self._row(row) for row in rows]

    def correct(self, scope: TrustedScope, *, memory_id: str, replacement: str, source: str = "correction"):
        old = self.get(scope, memory_id)
        if old is None:
            raise KeyError("memory not found in trusted scope")

        now = utc_now()
        self._conn.execute(
            "UPDATE memory_record SET status='superseded', updated_at=? WHERE memory_id=? AND user_id=?",
            (now, memory_id, scope.user_id),
        )

        new = MemoryRecord(
            memory_id=str(uuid.uuid4()),
            user_id=scope.user_id,
            session_id=old.session_id,
            content=replacement,
            created_at=now,
            updated_at=now,
            status="active",
            source=source,
            supersedes_id=old.memory_id,
        )
        self._conn.execute(
            "INSERT INTO memory_record VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new.memory_id, new.user_id, new.session_id, new.content,
                new.created_at, new.updated_at, new.status, new.source, new.supersedes_id
            ),
        )
        self._conn.commit()
        return old, new

    def supersede(self, scope: TrustedScope, *, memory_id: str) -> MemoryRecord:
        record = self.get(scope, memory_id)
        if record is None:
            raise KeyError("memory not found in trusted scope")
        now = utc_now()
        self._conn.execute(
            "UPDATE memory_record SET status='superseded', updated_at=? WHERE memory_id=? AND user_id=?",
            (now, memory_id, scope.user_id),
        )
        self._conn.commit()
        return self.get(scope, memory_id)
