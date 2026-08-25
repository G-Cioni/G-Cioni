# Local Presence Engine

**A clean-room, privacy-aware reference implementation for deterministic local presence tracking.**

This is a deliberately small public engineering artifact. It receives synthetic `ENTRY`, `EXIT`, or `UNKNOWN` events, converts a synthetic identity into an opaque token, and maintains durable open/closed visits in SQLite.

It is **not** copied from a private project and is **not** presented as production code from a client or pilot deployment. The value of the repository is that its engineering decisions are inspectable: pure domain logic, explicit anomalies, idempotency, atomic transactions, restart recovery, and tests.

## What this proves

- deterministic domain modeling rather than ad-hoc conditional persistence;
- ambiguity is represented explicitly instead of resolved arbitrarily;
- raw matching identities are transformed before persistence;
- one event is applied atomically to event/visit/anomaly state;
- duplicate source events are idempotent;
- a file-backed local database reconstructs state after restart;
- failure before commit leaves the event retryable with no partial visit/anomaly mutation;
- architecture decisions and limitations are documented next to the code.

## Architecture

```text
synthetic input
     |
     v
+-----------+       +----------------+       +----------------+
| Interface | ----> | Application    | ----> | Domain         |
| CLI       |       | orchestration  |       | pure decisions |
+-----------+       +-------+--------+       +----------------+
                            |
                            v
                    +----------------+
                    | Infrastructure |
                    | SQLite         |
                    +----------------+
```

Dependency direction stays inward: the domain does not import SQLite or the CLI. The application layer depends on a processing-store protocol; the SQLite implementation lives at the infrastructure edge.

See [Architecture](./docs/architecture.md) and the [ADRs](./docs/adr/).

## Decision model

For each accepted event, the pure domain engine returns exactly one of:

- `OPEN_VISIT`
- `CLOSE_VISIT`
- `NO_CHANGE` with an explicit anomaly

Handled anomaly classes:

- `UNKNOWN_DIRECTION`
- `UNREADABLE_EVENT`
- `ENTRY_WHILE_OPEN`
- `UNMATCHED_EXIT`
- `AMBIGUOUS_MATCH`
- `INVALID_TIMESTAMP_ORDER`

An ambiguous exit never chooses a visit arbitrarily.

## Run the deterministic demo

From this directory:

```bash
PYTHONPATH=src python -m local_presence.cli --db /tmp/local-presence-demo.db
```

Expected shape of output:

```text
entry-001 -> VISIT_OPENED
entry-001 duplicate -> VISIT_OPENED (idempotent)
entry-002 -> ANOMALY_RECORDED: ENTRY_WHILE_OPEN
exit-001 -> VISIT_CLOSED
exit-002 -> ANOMALY_RECORDED: UNMATCHED_EXIT
final visits: 1 closed
anomalies: 2
```

The demo uses fixed synthetic values and no external services.

## Run the tests

```bash
pytest -q
```

The suite covers:

- deterministic matching and ordering;
- open/close decisions;
- all modeled anomaly paths;
- schema and SQLite safety settings;
- raw-identity exclusion from persisted bytes;
- idempotent source events;
- end-to-end entry/exit processing;
- ambiguous-match behavior;
- rollback with a deliberately failing SQLite trigger;
- restart recovery through a closed/reopened database;
- CLI smoke behavior.

## Persistence and transactions

SQLite is configured with:

- foreign keys enabled;
- WAL journal mode;
- an explicit busy timeout.

Processing one new source event happens inside one `BEGIN IMMEDIATE` transaction:

```text
load duplicate? ── yes ──> return stored outcome
       |
       no
       v
insert pending event + opaque token
       |
       v
load open visits
       |
       v
pure decision
       |
       v
visit/anomaly mutation
       |
       v
mark event processed
       |
       v
commit
```

Any exception before commit rolls the entire transition back.

## Privacy boundary

The reference code intentionally separates a raw synthetic identity from persisted matching evidence:

```text
synthetic raw value -> SHA-256 namespaced token -> SQLite BLOB
```

The test suite checks that the raw synthetic identity does not appear in the SQLite database file.

This is an **architectural demonstration**, not a claim of complete cryptographic anonymity. A real deployment would require a threat model, key-management strategy, retention rules, access controls, and context-specific privacy review.

## Trade-offs

### Why exact deterministic matching?

Because ambiguity should be surfaced, not hidden. When one token matches multiple open visits, the system records `AMBIGUOUS_MATCH` and changes no visit state.

### Why SQLite?

Because the problem is local and the reference artifact should be runnable without infrastructure. SQLite also makes transaction semantics and restart recovery easy to inspect.

### Why no input-acquisition layer?

Input acquisition would add peripheral complexity while proving less about the engineering behavior this artifact is meant to expose. The reference starts at an already normalized synthetic event.

## Limitations

This reference implementation does not include:

- hardware or sensor integration;
- image processing or OCR;
- networking or cloud services;
- authentication or user management;
- production deployment automation;
- distributed concurrency guarantees;
- production key management;
- retention/erasure workflows;
- performance claims.

It is small on purpose: enough code to make the engineering choices inspectable without pretending to be a production platform.

## Evidence context

This system is linked from **CF-002** in the [Delivery Ledger](../../README.md). CF-002 explains what this public reference implementation demonstrates and, equally importantly, what it does not claim.
