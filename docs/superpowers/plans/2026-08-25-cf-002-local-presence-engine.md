# CF-002 Local Presence Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public, clean-room local presence reference system with deterministic domain logic, SQLite durability, idempotent processing, restart recovery, synthetic demo data, tests, architecture documentation, and a CF-002 casefile.

**Architecture:** The system has four inward-facing layers: pure domain decisions, application orchestration, SQLite infrastructure, and a tiny CLI. Opaque tokens are the only persisted matching evidence; raw synthetic identities are transformed before persistence. One source event is processed inside one explicit transaction so visit/anomaly mutations and event outcome commit or roll back together.

**Tech Stack:** Python 3.11+, stdlib `sqlite3`, `hashlib`, `argparse`; pytest for tests.

**Spec:** `docs/superpowers/specs/2026-08-25-cf-002-local-presence-engine-design.md`

## Global Constraints

- All implementation code must be newly written in the public profile repository.
- Do not copy private source, private identifiers, private file/class/schema names, private commit hashes, real operational data, secrets, URLs, or deployment details.
- Use only generic `ENTRY`, `EXIT`, `UNKNOWN`, event, visit, opaque token, and anomaly concepts.
- Use deterministic synthetic data only.
- Keep `G-Cioni/garage_time` private and unchanged.
- Never claim this reference implementation is the code or exact architecture used in a client/pilot environment.
- TDD is mandatory for behavior: write a failing test, observe the correct failure, then add minimal production code.
- Final publication requires passing tests, CLI verification, prohibited-term scan, final diff review, and a non-force fast-forward only.

---

### Task 1: Pure domain decision engine

**Files:**
- Create: `delivery-ledger/reference-systems/local-presence-engine/pyproject.toml`
- Create: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/__init__.py`
- Create: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/domain.py`
- Test: `delivery-ledger/reference-systems/local-presence-engine/tests/test_domain.py`

**Interfaces:**
- Produces: `Direction`, `AnomalyKind`, `DecisionKind`, `OpaqueToken`, `OpenVisit`, `Decision`, `tokenize()`, `decide()`.
- `decide(direction, occurred_at_utc, candidate_tokens, open_visits)` must be pure and deterministic.

- [ ] Write failing tests for no/unique/ambiguous matching, entry/open, duplicate-entry anomaly, unmatched/ambiguous exit, unknown direction, unreadable event, invalid timestamp order, and deterministic visit ordering.
- [ ] Run `pytest tests/test_domain.py -q` and verify failures are caused by missing domain implementation.
- [ ] Implement the minimal domain types and decision rules required by the tests.
- [ ] Re-run `pytest tests/test_domain.py -q`; all domain tests must pass.

### Task 2: SQLite schema and durable repository

**Files:**
- Create: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/sqlite_store.py`
- Test: `delivery-ledger/reference-systems/local-presence-engine/tests/test_integration.py`

**Interfaces:**
- Produces: `SQLiteStore(path)`, `initialize()`, `record_event(...)`, `process_event(...)`, `list_visits()`, `list_anomalies()`, `close()`.
- SQLite tables: `events`, `event_tokens`, `visits`, `visit_tokens`, `anomalies`.

- [ ] Add failing integration tests for schema creation, foreign keys, WAL mode, one durable source event, and absence of raw synthetic identity strings in persisted tables.
- [ ] Run the integration tests and observe expected failures.
- [ ] Implement SQLite connection configuration, schema creation, constraints, token persistence, and read models.
- [ ] Run domain + integration tests; all implemented persistence tests must pass.

### Task 3: Atomic application processing and idempotency

**Files:**
- Create: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/application.py`
- Modify: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/sqlite_store.py`
- Modify: `delivery-ledger/reference-systems/local-presence-engine/tests/test_integration.py`

**Interfaces:**
- Produces: `PresenceService(store)` and `Outcome`.
- `PresenceService.accept(source_event_id, direction, occurred_at_utc, raw_identity)` tokenizes before persistence and returns a durable result.

- [ ] Add failing tests for entry→open, exit→close, duplicate source-event idempotency, duplicate-entry anomaly, unmatched-exit anomaly, and ambiguous-match anomaly.
- [ ] Run those tests and verify correct RED failures.
- [ ] Implement minimal orchestration using the pure domain engine inside one explicit SQLite transaction.
- [ ] Re-run tests and keep all prior tests green.

### Task 4: Rollback and restart recovery

**Files:**
- Modify: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/application.py`
- Modify: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/sqlite_store.py`
- Modify: `delivery-ledger/reference-systems/local-presence-engine/tests/test_integration.py`

**Interfaces:**
- Produces: deterministic retry after rollback and reconstruction from a reopened file-backed database.

- [ ] Add a failing restart test: process ENTRY, close store, reopen store, process matching EXIT, verify same visit closes.
- [ ] Add a failing rollback test using an explicit test hook that raises before commit; verify the event remains retryable and no partial visit/anomaly rows persist.
- [ ] Implement only the transaction/recovery behavior needed for those tests.
- [ ] Run the full suite and verify all tests pass.

### Task 5: Synthetic CLI and public documentation

**Files:**
- Create: `delivery-ledger/reference-systems/local-presence-engine/src/local_presence/cli.py`
- Create: `delivery-ledger/reference-systems/local-presence-engine/README.md`
- Create: `delivery-ledger/reference-systems/local-presence-engine/docs/architecture.md`
- Create: `delivery-ledger/reference-systems/local-presence-engine/docs/adr/001-pure-domain-boundary.md`
- Create: `delivery-ledger/reference-systems/local-presence-engine/docs/adr/002-sqlite-local-durability.md`
- Create: `delivery-ledger/casefiles/CF-002-local-presence-engine/README.md`

**Interfaces:**
- CLI command: `python -m local_presence.cli --db <path>`.
- Demo sequence: readable entry, duplicate source event, duplicate entry anomaly, matching exit, unmatched exit; print only synthetic IDs/state.

- [ ] Add a failing CLI smoke test or subprocess assertion for the deterministic scenario output.
- [ ] Implement the minimal CLI to satisfy the smoke test.
- [ ] Write README, architecture, ADRs, and CF-002 with explicit reference-implementation and confidentiality boundaries.
- [ ] Run CLI manually and capture successful deterministic output.

### Task 6: Ledger/profile integration

**Files:**
- Modify: `delivery-ledger/README.md`
- Modify: `delivery-ledger/manifest.yml`
- Modify: `README.md`

**Interfaces:**
- CF-002 and the reference system must be reachable from the Delivery Ledger and profile without implying private production deployment.

- [ ] Add CF-002 and `local-presence-engine` to the ledger index and manifest.
- [ ] Add one concise profile link to the inspectable reference system/casefile.
- [ ] Verify wording distinguishes professional evidence (CF-001) from public reference implementation (CF-002).

### Task 7: Verification and privacy gate

**Files:**
- Review all files under `delivery-ledger/reference-systems/local-presence-engine/` and `delivery-ledger/casefiles/CF-002-local-presence-engine/`.

**Interfaces:**
- Produces: verified branch suitable for final review/publication.

- [ ] Run `pytest -q` from the reference-system root; require zero failures.
- [ ] Run the CLI against a fresh temporary DB; require expected entry/idempotent/anomaly/exit output.
- [ ] Scan new public files for prohibited private names and sensitive-domain terms selected for this build, including private repository name and real-world deployment terms.
- [ ] Scan for obvious secrets (`BEGIN PRIVATE KEY`, API key/token assignment patterns, real URLs/hostnames) and confirm only public documentation URLs are present.
- [ ] Compare `main...feat/cf-002-local-presence-engine` and review every changed filename.
- [ ] Verify `G-Cioni/garage_time` visibility remains private and no write was made to it.
- [ ] Only after all checks pass, fast-forward `main` with `force:false` and re-read CF-002/reference README from `main`.
