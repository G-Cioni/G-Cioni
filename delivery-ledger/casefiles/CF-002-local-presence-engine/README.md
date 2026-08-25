# CF-002 · Local Presence Engine — public reference implementation

**Status:** shipped reference artifact  
**Evidence type:** public clean-room engineering system  
**Code:** [`local-presence-engine`](../../reference-systems/local-presence-engine/README.md)

> CF-002 is intentionally different from CF-001. CF-001 documents sanitized professional delivery work. CF-002 is newly written public code designed to make engineering judgment directly inspectable. It does **not** claim that this exact code, schema, or architecture is deployed in a client or pilot environment.

## Why this casefile exists

Much of my professional implementation work cannot be published. A profile that only says “architecture”, “testing”, or “production thinking” therefore leaves the strongest claims difficult to inspect.

CF-002 addresses that gap with a small reference system whose behavior can be cloned, executed, tested, and challenged.

The problem was chosen because it forces several non-trivial engineering questions without requiring external infrastructure:

- how should ambiguous matching behave?
- how do you prevent duplicate source events from creating duplicate effects?
- where should raw matching identity stop existing?
- what state must survive restart?
- how do you prove a multi-row transition is atomic?
- which decisions belong in the domain versus persistence layer?

## The problem

A local application receives synthetic passage events and must maintain whether an anonymous entity is currently present.

Each event has:

- a direction: `ENTRY`, `EXIT`, or `UNKNOWN`;
- a UTC timestamp;
- a source-event ID for idempotency;
- zero or one synthetic raw identity in the public demo.

The application transforms the raw synthetic identity into an opaque token before persistence and uses only opaque tokens for matching against open visits.

## Core design decisions

### 1. Ambiguity is a state, not a guess

The system never chooses arbitrarily when an exit matches multiple open visits. It records `AMBIGUOUS_MATCH` and performs no presence mutation.

This same principle is used for unknown direction, unreadable input, unmatched exits, duplicate entries, and invalid timestamp ordering: uncertainty becomes explicit durable evidence.

### 2. Domain decision logic is pure

The matching and transition rules have no SQLite dependency. Durable state is converted into immutable open-visit snapshots, evaluated by the domain, then applied by the application layer.

This makes the rules independently testable and separates “what should happen?” from “did the transaction commit?”.

### 3. One new event is one transaction

For a new source event, the application:

```text
insert event
   -> load open visits
   -> compute pure decision
   -> mutate visit or anomaly
   -> mark event processed
   -> commit
```

The integration suite installs a temporary SQLite trigger that fails the final status update. The test verifies that the preceding event/visit/anomaly writes are all rolled back and the same source event can then be retried successfully.

### 4. Restart state comes from persistence, not memory

The restart test opens a visit, closes the first SQLite connection, creates a new store/service instance, and closes the same visit with a matching exit.

No in-memory session state is needed to reconstruct the open visit.

### 5. Raw synthetic identity is not persisted

The application converts the raw synthetic value into a namespaced SHA-256 token before it crosses the persistence boundary.

A test checks the database bytes directly and verifies the raw synthetic string is absent.

This is a privacy-aware architectural boundary, not a claim of complete anonymity. A real deployment would need keyed derivation, retention controls, access rules, and a specific threat model.

## Inspectable evidence

The reference system includes:

- [`domain.py`](../../reference-systems/local-presence-engine/src/local_presence/domain.py) — deterministic matching and transition rules;
- [`application.py`](../../reference-systems/local-presence-engine/src/local_presence/application.py) — idempotent orchestration;
- [`sqlite_store.py`](../../reference-systems/local-presence-engine/src/local_presence/sqlite_store.py) — schema, transactions, durable mapping;
- [`test_domain.py`](../../reference-systems/local-presence-engine/tests/test_domain.py) — pure behavior tests;
- [`test_integration.py`](../../reference-systems/local-presence-engine/tests/test_integration.py) — persistence, rollback, restart, idempotency;
- [`architecture.md`](../../reference-systems/local-presence-engine/docs/architecture.md) — boundaries and data flow;
- [ADRs](../../reference-systems/local-presence-engine/docs/adr/) — explicit trade-offs.

## What it proves

CF-002 provides inspectable evidence of:

1. deterministic domain modeling;
2. explicit handling of ambiguity and invalid states;
3. privacy-aware data boundaries;
4. transactional SQLite persistence;
5. idempotent event processing;
6. rollback-safe mutation;
7. restart reconstruction;
8. automated unit/integration testing;
9. architecture and trade-off documentation.

## What it does not prove

It does not claim:

- that this exact implementation is deployed anywhere;
- that it is copied from professional/client source code;
- that it contains a production input-acquisition pipeline;
- that deterministic SHA-256 alone is sufficient privacy for a real deployment;
- distributed scalability or high availability;
- production performance numbers;
- ownership of every stage of a separate private project.

## Run it

```bash
cd delivery-ledger/reference-systems/local-presence-engine
PYTHONPATH=src python -m local_presence.cli --db /tmp/local-presence-demo.db
pytest -q
```

## Interview prompts

A reviewer can probe the artifact by asking:

- Why return an anomaly rather than pick the first ambiguous match?
- Why keep the decision engine pure?
- What exactly is guaranteed by the transaction boundary?
- Where could idempotency fail if the source-event key were not durable?
- Why is an unkeyed deterministic digest insufficient for some real privacy threat models?
- How would the design change with multiple concurrent writers?
- What would need to change before a real production deployment?

Those questions are the point of the artifact: the repository is meant to make technical judgment discussable, not merely display a stack.

---

**Casefile ID:** `CF-002`  
**Ledger principle:** when private implementation cannot be shown, create new public code that demonstrates the underlying engineering capability without reconstructing confidential systems.
