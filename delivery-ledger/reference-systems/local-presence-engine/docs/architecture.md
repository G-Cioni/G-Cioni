# Architecture

## Goal

Maintain durable local presence state from synthetic passage events while keeping the decision logic deterministic, persistence inspectable, and raw matching identities outside the database.

## Boundaries

### Domain — `domain.py`

Owns:

- direction and anomaly vocabulary;
- opaque token value object;
- open-visit snapshot;
- deterministic matching;
- pure open/close/no-change decisions.

Does not know about SQLite, transactions, CLI arguments, or filesystem paths.

### Application — `application.py`

Owns:

- source-event idempotency behavior;
- tokenization before persistence;
- orchestration of one event;
- translation from a pure decision into store mutations;
- durable outcome returned to the caller.

The application consumes a processing-store protocol rather than importing SQLite.

### Infrastructure — `sqlite_store.py`

Owns:

- connection configuration;
- schema creation;
- explicit transaction scope;
- mapping rows into domain snapshots;
- durable event/visit/anomaly mutations.

The infrastructure depends inward on application/domain types.

### Interface — `cli.py`

Owns only the deterministic synthetic demonstration and command-line parsing.

## Data flow

```text
raw synthetic identity
        |
        v
 application tokenization
        |
        v
 opaque 32-byte token
        |
        +-------> event_tokens (durable event evidence)
        |
        v
 open visit snapshots
        |
        v
 pure domain decision
        |
        +---- OPEN_VISIT ----> visits + visit_tokens
        |
        +---- CLOSE_VISIT ---> visits closed + visit_tokens removed
        |
        +---- NO_CHANGE -----> anomalies
        |
        v
 events.status = PROCESSED + durable outcome
```

## Idempotency

`events.source_event_id` is unique. A repeated source ID returns the already stored outcome before any new domain decision or mutation runs.

The source event key is modeled as a non-sensitive idempotency identifier. The CLI uses synthetic values only.

## Atomicity

One new event is inserted and processed inside one explicit `BEGIN IMMEDIATE` transaction. If marking the event processed fails, the preceding visit or anomaly mutation is rolled back with it.

The integration test proves this with a temporary SQLite trigger that raises during the final status update.

## Restart recovery

Open visits and their opaque tokens are stored in SQLite. After the first application instance closes, a second instance can reconstruct open-visit snapshots directly from persisted state and correctly evaluate a matching synthetic exit.

This demonstrates application-level durability across restart. It does not claim hardware-level fault tolerance.

## Privacy design

The raw synthetic identity is accepted only at the application boundary and immediately converted to a deterministic namespaced SHA-256 token. Domain matching and persistence use the token rather than the raw value.

This prevents accidental raw-identity storage in this reference implementation, but it is not a complete privacy system. Deterministic digests can be vulnerable to guessing when the input space is small. A real system should consider keyed derivation, key rotation, data minimization, retention, erasure, and threat-model-specific controls.

## Failure model

The reference system fails closed with respect to ambiguous state transitions:

- unknown direction -> anomaly;
- no readable token -> anomaly;
- duplicate entry -> anomaly;
- unmatched exit -> anomaly;
- multiple matching visits -> anomaly;
- exit timestamp before entry -> anomaly.

No ambiguous branch silently chooses a target visit.
