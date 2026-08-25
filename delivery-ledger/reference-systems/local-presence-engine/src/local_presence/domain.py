from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from uuid import UUID


class Direction(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    UNKNOWN = "UNKNOWN"


class AnomalyKind(StrEnum):
    UNKNOWN_DIRECTION = "UNKNOWN_DIRECTION"
    UNREADABLE_EVENT = "UNREADABLE_EVENT"
    ENTRY_WHILE_OPEN = "ENTRY_WHILE_OPEN"
    UNMATCHED_EXIT = "UNMATCHED_EXIT"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    INVALID_TIMESTAMP_ORDER = "INVALID_TIMESTAMP_ORDER"


class DecisionKind(StrEnum):
    OPEN_VISIT = "OPEN_VISIT"
    CLOSE_VISIT = "CLOSE_VISIT"
    NO_CHANGE = "NO_CHANGE"


@dataclass(frozen=True, slots=True)
class OpaqueToken:
    digest: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.digest, bytes) or len(self.digest) != 32:
            raise ValueError("opaque token must be exactly 32 bytes")

    def __repr__(self) -> str:
        return "OpaqueToken(<redacted>)"


@dataclass(frozen=True, slots=True)
class OpenVisit:
    visit_id: UUID
    entry_at_utc: datetime
    tokens: tuple[OpaqueToken, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.visit_id, UUID):
            raise TypeError("visit_id must be a UUID")
        _require_utc(self.entry_at_utc)
        if not isinstance(self.tokens, tuple) or any(
            not isinstance(token, OpaqueToken) for token in self.tokens
        ):
            raise TypeError("tokens must be a tuple of OpaqueToken")


@dataclass(frozen=True, slots=True)
class Decision:
    kind: DecisionKind
    visit_id: UUID | None = None
    anomaly: AnomalyKind | None = None
    duration_seconds: int | None = None


def _require_utc(value: datetime) -> None:
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")


def tokenize(raw_identity: str) -> OpaqueToken:
    if not isinstance(raw_identity, str):
        raise TypeError("raw identity must be a string")
    if not raw_identity:
        raise ValueError("raw identity must not be empty")
    payload = b"local-presence-reference:v1:" + raw_identity.encode("utf-8")
    return OpaqueToken(sha256(payload).digest())


def match_open_visits(
    candidate_tokens: tuple[OpaqueToken, ...],
    open_visits: tuple[OpenVisit, ...],
) -> tuple[UUID, ...]:
    token_set = set(candidate_tokens)
    matched = {
        visit.visit_id
        for visit in open_visits
        if token_set.intersection(visit.tokens)
    }
    return tuple(sorted(matched, key=lambda value: value.int))


def decide(
    direction: Direction,
    occurred_at_utc: datetime,
    candidate_tokens: tuple[OpaqueToken, ...],
    open_visits: tuple[OpenVisit, ...],
) -> Decision:
    if not isinstance(direction, Direction):
        raise TypeError("direction must be a Direction")
    _require_utc(occurred_at_utc)

    if direction is Direction.UNKNOWN:
        return Decision(DecisionKind.NO_CHANGE, anomaly=AnomalyKind.UNKNOWN_DIRECTION)
    if not candidate_tokens:
        return Decision(DecisionKind.NO_CHANGE, anomaly=AnomalyKind.UNREADABLE_EVENT)

    matches = match_open_visits(candidate_tokens, open_visits)
    if direction is Direction.ENTRY:
        if not matches:
            return Decision(DecisionKind.OPEN_VISIT)
        return Decision(DecisionKind.NO_CHANGE, anomaly=AnomalyKind.ENTRY_WHILE_OPEN)

    if not matches:
        return Decision(DecisionKind.NO_CHANGE, anomaly=AnomalyKind.UNMATCHED_EXIT)
    if len(matches) > 1:
        return Decision(DecisionKind.NO_CHANGE, anomaly=AnomalyKind.AMBIGUOUS_MATCH)

    visit_id = matches[0]
    visit = next(item for item in open_visits if item.visit_id == visit_id)
    if occurred_at_utc < visit.entry_at_utc:
        return Decision(
            DecisionKind.NO_CHANGE,
            anomaly=AnomalyKind.INVALID_TIMESTAMP_ORDER,
        )
    duration_seconds = int((occurred_at_utc - visit.entry_at_utc).total_seconds())
    return Decision(
        DecisionKind.CLOSE_VISIT,
        visit_id=visit_id,
        duration_seconds=duration_seconds,
    )
