from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import sqlite3
import pytest

from local_presence.application import OutcomeKind, PresenceService
from local_presence.domain import Direction, tokenize
from local_presence.sqlite_store import SQLiteStore

T0 = datetime(2026, 8, 25, 8, 0, tzinfo=UTC)


def test_schema_and_sqlite_safety_settings(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    try:
        tables = {
            row[0]
            for row in store.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {"events", "event_tokens", "visits", "visit_tokens", "anomalies"} <= tables
        assert store.connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    finally:
        store.close()


def test_service_persists_opaque_token_without_raw_identity(tmp_path: Path) -> None:
    path = tmp_path / "presence.db"
    raw_identity = "synthetic-person-alpha"

    store = SQLiteStore(path)
    store.initialize()
    try:
        result = PresenceService(store).accept(
            source_event_id="source-001",
            direction=Direction.ENTRY,
            occurred_at_utc=T0,
            raw_identity=raw_identity,
        )
        persisted = store.connection.execute(
            "SELECT token FROM event_tokens WHERE event_id = ?",
            (str(result.event_id),),
        ).fetchone()[0]
        assert persisted == tokenize(raw_identity).digest
    finally:
        store.close()

    assert raw_identity.encode() not in path.read_bytes()


def test_service_entry_then_exit_closes_same_visit(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    service = PresenceService(store)
    try:
        opened = service.accept(
            source_event_id="entry-001",
            direction=Direction.ENTRY,
            occurred_at_utc=T0,
            raw_identity="synthetic-alpha",
        )
        assert opened.kind is OutcomeKind.VISIT_OPENED
        assert opened.visit_id is not None

        closed = service.accept(
            source_event_id="exit-001",
            direction=Direction.EXIT,
            occurred_at_utc=T0.replace(minute=5),
            raw_identity="synthetic-alpha",
        )
        assert closed.kind is OutcomeKind.VISIT_CLOSED
        assert closed.visit_id == opened.visit_id

        visit = store.connection.execute(
            "SELECT state, duration_seconds FROM visits WHERE visit_id = ?",
            (str(opened.visit_id),),
        ).fetchone()
        assert visit == ("CLOSED", 300)
    finally:
        store.close()


def test_service_duplicate_source_event_returns_original_outcome_without_side_effects(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    service = PresenceService(store)
    try:
        first = service.accept(
            source_event_id="entry-repeat",
            direction=Direction.ENTRY,
            occurred_at_utc=T0,
            raw_identity="synthetic-alpha",
        )
        second = service.accept(
            source_event_id="entry-repeat",
            direction=Direction.EXIT,
            occurred_at_utc=T0.replace(minute=10),
            raw_identity="different-input-is-ignored-for-idempotency",
        )
        assert second == first
        assert store.connection.execute("SELECT COUNT(*) FROM events").fetchone() == (1,)
        assert store.connection.execute("SELECT COUNT(*) FROM visits").fetchone() == (1,)
    finally:
        store.close()


def test_service_duplicate_entry_records_anomaly_without_second_visit(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    service = PresenceService(store)
    try:
        first = service.accept(
            source_event_id="entry-one",
            direction=Direction.ENTRY,
            occurred_at_utc=T0,
            raw_identity="synthetic-alpha",
        )
        second = service.accept(
            source_event_id="entry-two",
            direction=Direction.ENTRY,
            occurred_at_utc=T0.replace(minute=1),
            raw_identity="synthetic-alpha",
        )
        assert first.kind is OutcomeKind.VISIT_OPENED
        assert second.kind is OutcomeKind.ANOMALY_RECORDED
        assert second.anomaly == "ENTRY_WHILE_OPEN"
        assert store.connection.execute("SELECT COUNT(*) FROM visits").fetchone() == (1,)
        assert store.connection.execute("SELECT COUNT(*) FROM anomalies").fetchone() == (1,)
    finally:
        store.close()


def test_service_unmatched_exit_records_anomaly(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    service = PresenceService(store)
    try:
        result = service.accept(
            source_event_id="exit-alone",
            direction=Direction.EXIT,
            occurred_at_utc=T0,
            raw_identity="synthetic-alpha",
        )
        assert result.kind is OutcomeKind.ANOMALY_RECORDED
        assert result.anomaly == "UNMATCHED_EXIT"
        assert result.visit_id is None
    finally:
        store.close()


def test_service_ambiguous_exit_records_anomaly_and_closes_nothing(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "presence.db")
    store.initialize()
    token = tokenize("synthetic-alpha")
    store.connection.execute("BEGIN IMMEDIATE")
    try:
        for visit_id in (
            UUID("11111111-1111-1111-1111-111111111111"),
            UUID("22222222-2222-2222-2222-222222222222"),
        ):
            store.connection.execute(
                "INSERT INTO visits(visit_id, state, entry_at_utc) VALUES (?, 'OPEN', ?)",
                (str(visit_id), "2026-08-25T08:00:00Z"),
            )
            store.connection.execute(
                "INSERT INTO visit_tokens(visit_id, token) VALUES (?, ?)",
                (str(visit_id), token.digest),
            )
        store.connection.commit()
    except BaseException:
        store.connection.rollback()
        raise

    service = PresenceService(store)
    try:
        result = service.accept(
            source_event_id="ambiguous-exit",
            direction=Direction.EXIT,
            occurred_at_utc=T0.replace(minute=5),
            raw_identity="synthetic-alpha",
        )
        assert result.kind is OutcomeKind.ANOMALY_RECORDED
        assert result.anomaly == "AMBIGUOUS_MATCH"
        assert store.connection.execute(
            "SELECT COUNT(*) FROM visits WHERE state='OPEN'"
        ).fetchone() == (2,)
    finally:
        store.close()


def test_restart_recovery_closes_visit_from_reopened_database(tmp_path: Path) -> None:
    path = tmp_path / "presence.db"
    first_store = SQLiteStore(path)
    first_store.initialize()
    opened = PresenceService(first_store).accept(
        source_event_id="restart-entry",
        direction=Direction.ENTRY,
        occurred_at_utc=T0,
        raw_identity="synthetic-restart",
    )
    first_store.close()

    second_store = SQLiteStore(path)
    second_store.initialize()
    try:
        closed = PresenceService(second_store).accept(
            source_event_id="restart-exit",
            direction=Direction.EXIT,
            occurred_at_utc=T0.replace(minute=7),
            raw_identity="synthetic-restart",
        )
        assert closed.kind is OutcomeKind.VISIT_CLOSED
        assert closed.visit_id == opened.visit_id
        assert second_store.connection.execute(
            "SELECT state, duration_seconds FROM visits WHERE visit_id=?",
            (str(opened.visit_id),),
        ).fetchone() == ("CLOSED", 420)
    finally:
        second_store.close()


def test_failure_before_commit_rolls_back_all_effects_and_event_is_retryable(tmp_path: Path) -> None:
    path = tmp_path / "presence.db"
    store = SQLiteStore(path)
    store.initialize()
    store.connection.executescript(
        """
        CREATE TRIGGER fail_before_processed
        BEFORE UPDATE OF status ON events
        WHEN NEW.status = 'PROCESSED'
        BEGIN
            SELECT RAISE(ABORT, 'injected failure');
        END;
        """
    )

    service = PresenceService(store)
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        service.accept(
            source_event_id="rollback-entry",
            direction=Direction.ENTRY,
            occurred_at_utc=T0,
            raw_identity="synthetic-rollback",
        )

    assert store.connection.execute("SELECT COUNT(*) FROM events").fetchone() == (0,)
    assert store.connection.execute("SELECT COUNT(*) FROM visits").fetchone() == (0,)
    assert store.connection.execute("SELECT COUNT(*) FROM anomalies").fetchone() == (0,)

    store.connection.execute("DROP TRIGGER fail_before_processed")
    retry = PresenceService(store).accept(
        source_event_id="rollback-entry",
        direction=Direction.ENTRY,
        occurred_at_utc=T0,
        raw_identity="synthetic-rollback",
    )
    assert retry.kind is OutcomeKind.VISIT_OPENED
    store.close()
