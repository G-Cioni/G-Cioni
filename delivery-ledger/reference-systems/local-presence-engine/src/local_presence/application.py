from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ContextManager, Protocol
from uuid import UUID, uuid4

from .domain import DecisionKind, Direction, OpenVisit, decide, tokenize


class OutcomeKind(StrEnum):
    VISIT_OPENED = "VISIT_OPENED"
    VISIT_CLOSED = "VISIT_CLOSED"
    ANOMALY_RECORDED = "ANOMALY_RECORDED"


@dataclass(frozen=True, slots=True)
class Outcome:
    event_id: UUID
    kind: OutcomeKind
    visit_id: UUID | None = None
    anomaly: str | None = None


class ProcessingSession(Protocol):
    def load_existing_outcome(
        self, source_event_id: str
    ) -> tuple[str, str, str | None, str | None] | None: ...

    def insert_pending_event(
        self,
        *,
        event_id: UUID,
        source_event_id: str,
        direction: Direction,
        occurred_at_utc: datetime,
        token_digests: tuple[bytes, ...],
    ) -> None: ...

    def load_open_visits(self) -> tuple[OpenVisit, ...]: ...

    def open_visit(
        self,
        *,
        visit_id: UUID,
        entry_at_utc: datetime,
        token_digests: tuple[bytes, ...],
    ) -> None: ...

    def close_visit(
        self,
        *,
        visit_id: UUID,
        exit_at_utc: datetime,
        duration_seconds: int,
    ) -> None: ...

    def add_anomaly(
        self,
        *,
        event_id: UUID,
        visit_id: UUID | None,
        kind: str,
        occurred_at_utc: datetime,
    ) -> None: ...

    def mark_processed(
        self,
        *,
        event_id: UUID,
        outcome: OutcomeKind,
        visit_id: UUID | None,
        anomaly: str | None,
        processed_at_utc: datetime,
    ) -> None: ...


class ProcessingStore(Protocol):
    def processing_transaction(self) -> ContextManager[ProcessingSession]: ...


class PresenceService:
    def __init__(self, store: ProcessingStore) -> None:
        self._store = store

    def accept(
        self,
        *,
        source_event_id: str,
        direction: Direction,
        occurred_at_utc: datetime,
        raw_identity: str | None,
    ) -> Outcome:
        tokens = () if raw_identity is None else (tokenize(raw_identity),)
        token_digests = tuple(token.digest for token in tokens)

        with self._store.processing_transaction() as session:
            existing = session.load_existing_outcome(source_event_id)
            if existing is not None:
                event_id_text, kind_text, visit_id_text, anomaly = existing
                return Outcome(
                    event_id=UUID(event_id_text),
                    kind=OutcomeKind(kind_text),
                    visit_id=UUID(visit_id_text) if visit_id_text else None,
                    anomaly=anomaly,
                )

            event_id = uuid4()
            session.insert_pending_event(
                event_id=event_id,
                source_event_id=source_event_id,
                direction=direction,
                occurred_at_utc=occurred_at_utc,
                token_digests=token_digests,
            )

            decision = decide(
                direction,
                occurred_at_utc,
                tokens,
                session.load_open_visits(),
            )

            if decision.kind is DecisionKind.OPEN_VISIT:
                visit_id = uuid4()
                session.open_visit(
                    visit_id=visit_id,
                    entry_at_utc=occurred_at_utc,
                    token_digests=token_digests,
                )
                outcome = Outcome(
                    event_id,
                    OutcomeKind.VISIT_OPENED,
                    visit_id=visit_id,
                )
            elif decision.kind is DecisionKind.CLOSE_VISIT:
                if decision.visit_id is None or decision.duration_seconds is None:
                    raise RuntimeError("close decision is incomplete")
                session.close_visit(
                    visit_id=decision.visit_id,
                    exit_at_utc=occurred_at_utc,
                    duration_seconds=decision.duration_seconds,
                )
                outcome = Outcome(
                    event_id,
                    OutcomeKind.VISIT_CLOSED,
                    visit_id=decision.visit_id,
                )
            else:
                if decision.anomaly is None:
                    raise RuntimeError("no-change decision requires an anomaly")
                session.add_anomaly(
                    event_id=event_id,
                    visit_id=decision.visit_id,
                    kind=decision.anomaly.value,
                    occurred_at_utc=occurred_at_utc,
                )
                outcome = Outcome(
                    event_id,
                    OutcomeKind.ANOMALY_RECORDED,
                    anomaly=decision.anomaly.value,
                )

            session.mark_processed(
                event_id=event_id,
                outcome=outcome.kind,
                visit_id=outcome.visit_id,
                anomaly=outcome.anomaly,
                processed_at_utc=occurred_at_utc,
            )
            return outcome
