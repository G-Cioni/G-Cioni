# Delivery Ledger

**Public engineering evidence from ambiguity to production.**

Most client production code and internal architecture cannot be published. This ledger is a deliberately narrow alternative: it documents **what kind of problem existed, what delivery work was required, how technical judgment was applied, what was validated, and what can safely be inspected** — while withholding client identities, proprietary source code, internal endpoints, credentials, business data, and confidential architecture.

The ledger uses two evidence types:

1. **Sanitized professional casefiles** — real delivery work described without reconstructing confidential systems.
2. **Public reference systems** — newly written, runnable code that demonstrates an engineering capability directly without claiming to be private production code.

## Evidence model

A casefile can expose evidence across five stages:

| Stage | What can be shown publicly |
| --- | --- |
| **Discover** | problem class, stakeholder questions, constraints, ambiguity reduced |
| **Design** | public-safe solution shape, LLD responsibility, trade-off categories |
| **Build** | implementation scope or inspectable reference code |
| **Validate** | tests, UAT support, failure-path thinking |
| **Ship** | release support, production considerations, restart/durability thinking, lessons |

The goal is not to recreate a confidential system. The goal is to make engineering judgment inspectable.

## Casefiles

### [CF-001 · Enterprise change delivery — anonymized](./casefiles/CF-001-enterprise-change-delivery/README.md)

`Discover` → `Design / LLD` → `Build` → `Validate / UAT` → `Production / Hypercare`

A sanitized professional delivery casefile showing how an enterprise application change moved from stakeholder clarification into technical design, implementation, validation, and production support.

### [CF-002 · Local Presence Engine — public reference implementation](./casefiles/CF-002-local-presence-engine/README.md)

`Model` → `Persist` → `Process atomically` → `Recover` → `Verify`

A clean-room runnable system demonstrating deterministic domain decisions, privacy-aware token boundaries, SQLite transactions, idempotency, rollback, restart recovery, and automated tests.

## Reference systems

### [Local Presence Engine](./reference-systems/local-presence-engine/README.md)

Small enough to understand in one sitting; complete enough to execute and challenge. The artifact includes source, tests, architecture documentation, ADRs, and a deterministic synthetic CLI demo.

## Disclosure standard

A casefile or reference system must not publish:

- client or employer-confidential identifiers;
- private repository names or links;
- proprietary source code;
- internal API routes, credentials, hostnames, or environment details;
- non-public business data;
- diagrams that reconstruct confidential architecture;
- metrics or outcomes that cannot be supported.

When a detail is intentionally withheld, the casefile says so rather than replacing it with invented specificity.

A public reference implementation must additionally state that it is newly written public code and must not imply that its exact code, schema, or architecture is deployed in a private environment.

## Why this exists

A CV can say “end-to-end delivery.” A repository should make that claim easier to interrogate.

CF-001 makes professional delivery scope inspectable. CF-002 adds something different: code a reviewer can actually run, test, and question.
