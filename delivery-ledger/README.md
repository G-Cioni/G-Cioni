# Delivery Ledger

**Public engineering evidence from ambiguity to production.**

Most client production code and internal architecture cannot be published. This ledger is a deliberately narrow alternative: it documents **what kind of problem existed, what delivery work was required, how the work moved through the lifecycle, what was validated, and what can be learned from it** — while withholding client identities, proprietary source code, internal endpoints, credentials, business data, and confidential architecture.

This is not a collection of invented portfolio exercises. Every casefile must map to real work or a real independently built system.

## Evidence model

A casefile can expose evidence across five stages:

| Stage | What can be shown publicly |
| --- | --- |
| **Discover** | problem class, stakeholder questions, constraints, ambiguity reduced |
| **Design** | public-safe solution shape, LLD responsibility, trade-off categories |
| **Build** | implementation scope, interfaces touched, collaboration boundaries |
| **Validate** | test scenarios, UAT support, failure-path thinking |
| **Ship** | release support, production considerations, hypercare, lessons |

The goal is not to recreate a confidential system. The goal is to make engineering judgment inspectable.

## Casefiles

### [CF-001 · Enterprise change delivery — anonymized](./casefiles/CF-001-enterprise-change-delivery/README.md)

`Discover` → `Design / LLD` → `Build` → `Validate / UAT` → `Production / Hypercare`

A sanitized delivery casefile showing how an enterprise application change moved from stakeholder clarification into technical design, implementation, validation, and production support.

## Disclosure standard

A casefile must not publish:

- client or employer-confidential identifiers;
- private repository names or links;
- proprietary source code;
- internal API routes, credentials, hostnames, or environment details;
- non-public business data;
- diagrams that reconstruct confidential architecture;
- metrics or outcomes that cannot be supported.

When a detail is intentionally withheld, the casefile says so rather than replacing it with invented specificity.

## Why this exists

A CV can say “end-to-end delivery.” A repository should make that claim easier to interrogate.

The Delivery Ledger is designed to show the **shape of the work**: where ambiguity existed, how it was reduced, how the technical solution was expressed, how implementation fit into a wider team, how validation was structured, and what happened around release.
