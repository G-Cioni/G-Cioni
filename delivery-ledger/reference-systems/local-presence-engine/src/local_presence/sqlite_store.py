from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4

from .application import OutcomeKind
from .domain import Direction, OpenVisit, OpaqueToken

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    visit_id TEXT PRIMARY KEY,
    state TEXT NOT NULL CHECK (state IN ('OPEN', 'CLOSED')),
    entry_at_utc TEXT NOT NULL,
    exit_at_utc TEXT,
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL UNIQUE,
    direction TEXT NOT NULL CHECK (direction IN ('ENTRY', 'EXIT', 'UNKNOWN')),
    occurred_at_utc TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'PROCESSED')),
    outcome TEXT CHECK (outcome IS NULL OR outcome IN ('VISIT_OPENED', 'VISIT_CLOSED', 'ANOMALY_RECORDED')),
    visit_id TEXT REFERENCES visits(visit_id),
    anomaly TEXT,
    processed_at_utc TEXT
);

CREATE TABLE IF NOT EXISTS event_tokens (
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    token BLOB NOT NULL CHECK (length(token) = 32),
    PRIMARY KEY (event_id, token)
);

CREATE TABLE IF NOT EXISTS visit_tokens (
    visit_id TEXT NOT NULL REFERENCES visits(visit_id) ON DELETE CASCADE,
    token BLOB NOT NULL CHECK (length(token) = 32),
    PRIMARY KEY (visit_id, token)
);

CREATE INDEX IF NOT EXISTS visit_tokens_lookup ON visit_tokens(token);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    visit_id TEXT REFERENCES visits(visit_id),
    kind TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL
);
"""


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


class _ProcessingSession:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def load_existing_outcome(
        self, source_event_id: str
    ) -> tuple[str, str, str | None, str | None] | None:
        row = self._connection.execute(
            "SELECT event_id, status, outcome, visit_id, anomaly FROM events WHERE source_event_id = ?",
            (source_event_id,),
        ).fetchone()
        if row is None:
            return None
        event_id, status, outcome, visit_id, anomaly = row
        if status != "PROCESSED" or outcome is None:
            raise RuntimeError("source event exists but is not processed")
        return event_id, outcome, visit_id, anomaly

    def insert_pending_event(
        self,
        *,
        event_id: UUID,
        source_event_id: str,
        direction: Direction,
        occurred_at_utc: datetime,
        token_digests: tuple[bytes, ...],
    ) -> None:
        self._connection.execute(
            "INSERT INTO events(event_id, source_event_id, direction, occurred_at_utc, status) "
            "VALUES (?, ?, ?, ?, 'PENDING')",
            (str(event_id), source_event_id, direction.value, _iso_utc(occurred_at_utc)),
        )
        self._connection.executemany(
            "INSERT INTO event_tokens(event_id, token) VALUES (?, ?)",
            [(str(event_id), digest) for digest in token_digests],
        )

    def load_open_visits(self) -> tuple[OpenVisit, ...]:
        rows = self._connection.execute(
            "SELECT visit_id, entry_at_utc FROM visits WHERE state='OPEN' ORDER BY visit_id"
        ).fetchall()
        visits: list[OpenVisit] = []
        for visit_id, entry_at in rows:
            token_rows = self._connection.execute(
                "SELECT token FROM visit_tokens WHERE visit_id = ? ORDER BY hex(token)",
                (visit_id,),
            ).fetchall()
            visits.append(
                OpenVisit(
                    UUID(visit_id),
                    _parse_utc(entry_at),
                    tuple(OpaqueToken(row[0]) for row in token_rows),
                )
            )
        return tuple(visits)

    def open_visit(
        self,
        *,
        visit_id: UUID,
        entry_at_utc: datetime,
        token_digests: tuple[bytes, ...],
    ) -> None:
        self._connection.execute(
            "INSERT INTO visits(visit_id, state, entry_at_utc) VALUES (?, 'OPEN', ?)",
            (str(visit_id), _iso_utc(entry_at_utc)),
        )
        self._connection.executemany(
            "INSERT INTO visit_tokens(visit_id, token) VALUES (?, ?)",
            [(str(visit_id), digest) for digest in token_digests],
        )

    def close_visit(
        self,
        *,
        visit_id: UUID,
        exit_at_utc: datetime,
        duration_seconds: int,
    ) -> None:
        cursor = self._connection.execute(
            "UPDATE visits SET state='CLOSED', exit_at_utc=?, duration_seconds=? "
            "WHERE visit_id=? AND state='OPEN'",
            (_iso_utc(exit_at_utc), duration_seconds, str(visit_id)),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("open visit was not found")
        self._connection.execute(
            "DELETE FROM visit_tokens WHERE visit_id = ?", (str(visit_id),)
        )

    def add_anomaly(
        self,
        *,
        event_id: UUID,
        visit_id: UUID | None,
        kind: str,
        occurred_at_utc: datetime,
    ) -> None:
        self._connection.execute(
            "INSERT INTO anomalies(anomaly_id, event_id, visit_id, kind, occurred_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                str(event_id),
                str(visit_id) if visit_id else None,
                kind,
                _iso_utc(occurred_at_utc),
            ),
        )

    def mark_processed(
        self,
        *,
        event_id: UUID,
        outcome: OutcomeKind,
        visit_id: UUID | None,
        anomaly: str | None,
        processed_at_utc: datetime,
    ) -> None:
        self._connection.execute(
            "UPDATE events SET status='PROCESSED', outcome=?, visit_id=?, anomaly=?, processed_at_utc=? "
            "WHERE event_id=?",
            (
                outcome.value,
                str(visit_id) if visit_id else None,
                anomaly,
                _iso_utc(processed_at_utc),
                str(event_id),
            ),
        )


class SQLiteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path, isolation_level=None)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA busy_timeout=5000")

    def initialize(self) -> None:
        self.connection.executescript(_SCHEMA)

    def close(self) -> None:
        self.connection.close()

    @contextmanager
    def processing_transaction(self) -> Iterator[_ProcessingSession]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield _ProcessingSession(self.connection)
        except BaseException:
            if self.connection.in_transaction:
                self.connection.rollback()
            raise
        else:
            if self.connection.in_transaction:
                self.connection.commit()
