# Delivery Ledger

**Public engineering evidence from ambiguity to production.**

Most client production code and internal architecture cannot be published. This ledger is a deliberately narrow alternative: it documents **what kind of problem existed, what delivery work was required, how technical judgment was applied, what was validated, and what can safely be inspected** — while withholding client identities, proprietary source code, internal endpoints, credentials, business data, and confidential architecture.

The ledger uses evidence with a clear provenance:

1. **Sanitized professional casefiles** — real delivery work described without reconstructing confidential systems.
2. **Existing public technical artifacts** — documents or systems that were genuinely produced and published as part of real projects, with their original provenance preserved.

## Evidence model

A casefile can expose evidence across five stages:

| Stage | What can be shown publicly |
| --- | --- |
| **Discover** | problem class, stakeholder questions, constraints, ambiguity reduced |
| **Design** | public-safe solution shape, LLD responsibility, data/state/API decisions |
| **Build** | implementation scope or already-public implementation evidence |
| **Validate** | tests, UAT support, integrity/concurrency thinking |
| **Ship / Publish** | production support, public technical disclosure, lessons |

The goal is not to manufacture portfolio projects. The goal is to make genuine engineering work easier to inspect.

## Casefiles

### [CF-001 · Enterprise change delivery — anonymized](./casefiles/CF-001-enterprise-change-delivery/README.md)

`Discover` → `Design / LLD` → `Build` → `Validate / UAT` → `Production / Hypercare`

A sanitized professional delivery casefile showing how an enterprise application change moved from stakeholder clarification into technical design, implementation, validation, and production support.

### [CF-002 · Connecting Beyond system architecture — public prior-art disclosure](./casefiles/CF-002-connecting-beyond-prior-art/README.md)

`Physical identifier` → `Intermediary activation` → `License claim` → `Digital-content linking`

A dated public technical specification co-authored by Gianluca Cioni and the Connecting Beyond team. It documents an offline-to-online license mechanism with a relational data model, explicit lifecycle states, API flows, intermediary traceability, conditional activation, email-based auto-claim, race-safe claiming, security controls, and implementation excerpts.

**[Inspect the original public repository →](https://github.com/G-Cioni/sys-arch-doc)**

## Disclosure standard

A casefile must not publish:

- client or employer-confidential identifiers;
- private repository names or links;
- proprietary source code that was not already intentionally public;
- internal API routes, credentials, hostnames, or environment details that were not already intentionally public;
- non-public business data;
- diagrams that reconstruct confidential architecture;
- metrics or outcomes that cannot be supported.

When a detail is intentionally withheld, the casefile says so rather than replacing it with invented specificity.

For existing public artifacts, the ledger preserves the original authorship and evidence boundary. It does not upgrade team work into sole authorship, or convert claims made in a source document into independently verified facts.

## Why this exists

A CV can say “end-to-end delivery.” A repository should make that claim easier to interrogate.

CF-001 makes professional delivery scope inspectable without exposing confidential systems. CF-002 points to a genuine public technical artifact whose provenance, architecture, implementation excerpts, and publication context can be inspected directly.
