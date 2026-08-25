# ADR-002: Use file-backed SQLite for local durability

**Status:** accepted

## Context

The reference problem needs durable state, idempotent source events, atomic transitions, and restart reconstruction, but it does not need distributed infrastructure.

Using a remote database would add setup and network concerns that do not improve the core demonstration.

## Decision

Use file-backed SQLite with foreign keys, WAL journal mode, an explicit busy timeout, and explicit `BEGIN IMMEDIATE` processing transactions.

## Consequences

### Positive

- the entire reference system runs locally;
- transaction behavior is visible in a small amount of code;
- restart recovery can be tested by closing and reopening the same database file;
- no external service or credentials are required.

### Negative

- the design does not demonstrate horizontal scale or distributed coordination;
- WAL and local filesystem semantics are not equivalent to a distributed datastore;
- the reference makes no high-availability or throughput claim.

For this artifact, local inspectability is more valuable than infrastructure breadth.
