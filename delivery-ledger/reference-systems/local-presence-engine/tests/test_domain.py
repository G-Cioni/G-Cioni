from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from local_presence.domain import (
    AnomalyKind,
    DecisionKind,
    Direction,
    OpenVisit,
    OpaqueToken,
    decide,
    match_open_visits,
    tokenize,
)

T0 = datetime(2026, 8, 25, 8, 0, tzinfo=UTC)
VISIT_A = UUID("11111111-1111-1111-1111-111111111111")
VISIT_B = UUID("22222222-2222-2222-2222-222222222222")
TOKEN_A = OpaqueToken(bytes.fromhex("aa" * 32))
TOKEN_B = OpaqueToken(bytes.fromhex("bb" * 32))


def visit(visit_id: UUID, token: OpaqueToken, at: datetime = T0) -> OpenVisit:
    return OpenVisit(visit_id=visit_id, entry_at_utc=at, tokens=(token,))


def test_tokenize_is_deterministic_and_hides_raw_value() -> None:
    first = tokenize("synthetic-alpha")
    second = tokenize("synthetic-alpha")
    assert first == second
    assert b"synthetic-alpha" not in first.digest
    assert len(first.digest) == 32


def test_match_no_overlap_returns_empty_tuple() -> None:
    assert match_open_visits((TOKEN_A,), (visit(VISIT_A, TOKEN_B),)) == ()


def test_match_unique_returns_visit_id() -> None:
    assert match_open_visits((TOKEN_A,), (visit(VISIT_A, TOKEN_A),)) == (VISIT_A,)


def test_match_ambiguous_is_sorted_deterministically() -> None:
    result = match_open_visits(
        (TOKEN_A,),
        (visit(VISIT_B, TOKEN_A), visit(VISIT_A, TOKEN_A)),
    )
    assert result == (VISIT_A, VISIT_B)


def test_entry_without_match_opens_visit() -> None:
    result = decide(Direction.ENTRY, T0, (TOKEN_A,), ())
    assert result.kind is DecisionKind.OPEN_VISIT
    assert result.anomaly is None


def test_entry_matching_open_visit_is_anomaly() -> None:
    result = decide(Direction.ENTRY, T0, (TOKEN_A,), (visit(VISIT_A, TOKEN_A),))
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.ENTRY_WHILE_OPEN


def test_unmatched_exit_is_anomaly() -> None:
    result = decide(Direction.EXIT, T0, (TOKEN_A,), (visit(VISIT_A, TOKEN_B),))
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.UNMATCHED_EXIT


def test_ambiguous_exit_never_chooses_arbitrarily() -> None:
    result = decide(
        Direction.EXIT,
        T0 + timedelta(minutes=5),
        (TOKEN_A,),
        (visit(VISIT_B, TOKEN_A), visit(VISIT_A, TOKEN_A)),
    )
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.AMBIGUOUS_MATCH
    assert result.visit_id is None


def test_unique_exit_closes_visit_with_duration() -> None:
    result = decide(
        Direction.EXIT,
        T0 + timedelta(minutes=5),
        (TOKEN_A,),
        (visit(VISIT_A, TOKEN_A),),
    )
    assert result.kind is DecisionKind.CLOSE_VISIT
    assert result.visit_id == VISIT_A
    assert result.duration_seconds == 300


def test_unknown_direction_is_anomaly() -> None:
    result = decide(Direction.UNKNOWN, T0, (TOKEN_A,), ())
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.UNKNOWN_DIRECTION


def test_unreadable_event_is_anomaly() -> None:
    result = decide(Direction.ENTRY, T0, (), ())
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.UNREADABLE_EVENT


def test_exit_before_entry_records_invalid_timestamp_without_negative_duration() -> None:
    result = decide(
        Direction.EXIT,
        T0 - timedelta(seconds=1),
        (TOKEN_A,),
        (visit(VISIT_A, TOKEN_A),),
    )
    assert result.kind is DecisionKind.NO_CHANGE
    assert result.anomaly is AnomalyKind.INVALID_TIMESTAMP_ORDER
    assert result.duration_seconds is None


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="UTC"):
        decide(Direction.ENTRY, datetime(2026, 1, 1), (TOKEN_A,), ())
