# ADR-001: Keep presence decisions pure

**Status:** accepted

## Context

Presence transitions are easier to reason about when the rules for entry, exit, ambiguity, and timestamp ordering are independent from database state changes.

Putting SQL calls directly inside conditional decision logic would make it harder to test the rules exhaustively and easier to accidentally mix “what should happen?” with “did persistence succeed?”.

## Decision

Represent currently open visits as immutable snapshots and implement matching/transition selection as pure functions in `domain.py`.

The application layer loads durable state, calls the domain function, and then applies the returned decision through the store boundary.

## Consequences

### Positive

- domain tests do not require SQLite;
- ambiguous behavior is deterministic and easy to exhaustively test;
- persistence failures cannot change what the domain rule means;
- the application/infrastructure boundary is visible to reviewers.

### Negative

- durable state must be mapped into domain snapshots;
- there are more explicit types than in a script that mixes SQL and conditionals.

The extra boundary is justified because the artifact is specifically meant to make reasoning and failure behavior inspectable.
