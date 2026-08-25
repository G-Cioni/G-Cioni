# Delivery Ledger

**Public engineering evidence from ambiguity to production.**

Most client production code and internal architecture cannot be published. This ledger is a deliberately narrow alternative: it documents **what kind of problem existed, what delivery work was required, how technical judgment was applied, what was validated, and what can safely be inspected** — while withholding client identities, proprietary source code, internal endpoints, credentials, business data, and confidential architecture.

The ledger uses evidence with a clear provenance:

1. **Casefiles** — real delivery work or existing public technical artifacts.
2. **Decision records** — one consequential architecture decision, including rejected alternatives and failure modes.
3. **Field notes** — one reusable engineering lesson extracted from a real system constraint.

AI-assisted implementation is identified where it materially affects authorship. The ledger distinguishes **requirements and decisions** from **code production** rather than treating repository ownership as proof that every line was manually authored.

## Evidence model

| Evidence type | Primary question |
| --- | --- |
| **Casefile** | What did the real delivery situation require from discovery through validation/shipping? |
| **Decision record** | Why was this system shaped this way instead of the obvious alternatives? |
| **Field note** | What reusable engineering rule emerged from the real constraint? |

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

## Decision records

### [DR-001 · Rights before resources exist](./decision-records/DR-001-rights-before-resources-exist/README.md)

`Temporary creation authority` → `Atomic consumption` → `Persistent participation`

A public-safe architecture record about granting one-use authority before its target resource exists, then crossing the creation boundary without confusing temporary capability, ownership, and durable editor access. It includes rejected alternatives, concurrency/failure modes, model evolution, verification strategy, and an explicit AI-assistance provenance note.

## Field notes

### [FN-001 · Rate limiting when many legitimate users share one IP](./field-notes/FN-001-rate-limiting-shared-networks/README.md)

`Threat model` → `Abuse identity` → `Layered limiter key` → `Behavioral verification`

A reusable engineering lesson from a real shared-network constraint: strict IP-only limiting can punish legitimate groups, so the primary key should approximate the identity of the abuse being controlled while a network-level limiter remains a broad safety net.

## Disclosure standard

An evidence unit must not publish:

- client or employer-confidential identifiers;
- private repository names or links;
- proprietary source code that was not already intentionally public;
- internal API routes, credentials, hostnames, or environment details that were not already intentionally public;
- non-public business data;
- diagrams that reconstruct confidential architecture;
- metrics or outcomes that cannot be supported.

When a detail is intentionally withheld, the evidence unit says so rather than replacing it with invented specificity.

For existing public artifacts, the ledger preserves the original authorship and evidence boundary. It does not upgrade team work into sole authorship, or convert claims made in a source document into independently verified facts.

For private AI-assisted work, the ledger does not equate a commit under Gianluca's account with manual code authorship. The public claim is limited to provenance that can actually be supported: requirements originated or corrected by Gianluca, architecture constraints he selected, implemented behavior found in the repository, and verification evidence where available.

## Why this exists

A CV can say “end-to-end delivery.” A repository should make that claim easier to interrogate.

The casefiles make delivery scope inspectable. Decision records expose the reasoning behind consequential system boundaries. Field notes make the resulting engineering lessons reusable without disclosing the private implementation that produced them.
