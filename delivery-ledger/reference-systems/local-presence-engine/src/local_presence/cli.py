from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .application import PresenceService
from .domain import Direction
from .sqlite_store import SQLiteStore


def _describe(label: str, outcome) -> str:
    if outcome.anomaly:
        return f"{label} -> {outcome.kind.value}: {outcome.anomaly}"
    return f"{label} -> {outcome.kind.value}"


def run_demo(database: Path) -> None:
    store = SQLiteStore(database)
    store.initialize()
    service = PresenceService(store)
    base = datetime(2026, 8, 25, 8, 0, tzinfo=UTC)
    try:
        first = service.accept(
            source_event_id="entry-001",
            direction=Direction.ENTRY,
            occurred_at_utc=base,
            raw_identity="synthetic-alpha",
        )
        print(_describe("entry-001", first))

        duplicate = service.accept(
            source_event_id="entry-001",
            direction=Direction.EXIT,
            occurred_at_utc=base + timedelta(seconds=30),
            raw_identity="synthetic-ignored-by-idempotency",
        )
        print(f"entry-001 duplicate -> {duplicate.kind.value} (idempotent)")

        duplicate_entry = service.accept(
            source_event_id="entry-002",
            direction=Direction.ENTRY,
            occurred_at_utc=base + timedelta(minutes=1),
            raw_identity="synthetic-alpha",
        )
        print(_describe("entry-002", duplicate_entry))

        closed = service.accept(
            source_event_id="exit-001",
            direction=Direction.EXIT,
            occurred_at_utc=base + timedelta(minutes=5),
            raw_identity="synthetic-alpha",
        )
        print(_describe("exit-001", closed))

        unmatched = service.accept(
            source_event_id="exit-002",
            direction=Direction.EXIT,
            occurred_at_utc=base + timedelta(minutes=6),
            raw_identity="synthetic-beta",
        )
        print(_describe("exit-002", unmatched))

        closed_count = store.connection.execute(
            "SELECT COUNT(*) FROM visits WHERE state='CLOSED'"
        ).fetchone()[0]
        anomaly_count = store.connection.execute(
            "SELECT COUNT(*) FROM anomalies"
        ).fetchone()[0]
        print(f"final visits: {closed_count} closed")
        print(f"anomalies: {anomaly_count}")
    finally:
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic local presence demo")
    parser.add_argument("--db", type=Path, required=True, help="Path to a local SQLite file")
    args = parser.parse_args()
    run_demo(args.db)


if __name__ == "__main__":
    main()
