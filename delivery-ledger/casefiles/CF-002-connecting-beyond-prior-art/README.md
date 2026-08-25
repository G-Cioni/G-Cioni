# CF-002 · Connecting Beyond system architecture — public prior-art disclosure

**Status:** published technical evidence  
**Evidence type:** public prior-art specification  
**Source repository:** [G-Cioni/sys-arch-doc](https://github.com/G-Cioni/sys-arch-doc)  
**Original specification:** [spec_v1.pdf](https://github.com/G-Cioni/sys-arch-doc/blob/main/spec_v1.pdf)

## Why this casefile exists

This casefile points to a technical system that was already made public independently of this portfolio.

The specification identifies its authors as **Connecting Beyond – Cioni Gianluca & team** and states that it was published on December 2, 2025 as a defensive prior-art disclosure. The purpose of the publication is to place the described technical solution in the public domain as prior art against later patent claims covering identical or substantially equivalent methods.

This is therefore different from a portfolio exercise: the underlying technical document, implementation excerpts, data model, state model, API surface, and publication date pre-date this Delivery Ledger.

## System described

The document describes an offline-to-online provisioning mechanism for Connecting Beyond in which a digital license is associated with a physical **Memory Link** identified by QR Code or NFC.

The flow separates three roles and moments:

1. a Memory Link exists as a physical/digital identifier;
2. an authorized intermediary associates and activates it for a recipient;
3. the end user later authenticates, claims the license, and links it to a digital memory.

The design avoids requiring the recipient to create an account or complete an online purchase before receiving the physical medium.

## Inspectable technical surface

The public specification exposes concrete system design and implementation details, including:

- a PostgreSQL data model via Supabase for licenses, physical/digital links, intermediaries, and association records;
- a license lifecycle derived from persisted state: `unclaimed` → `claimed` → `linked`;
- unique immutable `link_key` identifiers for QR/NFC media;
- idempotent Memory Link creation;
- intermediary-to-link and intermediary-to-license traceability;
- conditional activation of a link before license creation;
- email-based auto-claim when the intended recipient already has an account;
- a dynamic landing-state resolver for unauthenticated users, owners, non-owners, and already-linked memories;
- atomic conditional claiming to prevent two users from claiming the same license;
- validation of link identifiers, database-level race-condition protection, JWT authentication, Supabase RLS, and protected administrative endpoints;
- an explicit license state diagram and a documented API surface.

The specification also includes excerpts labelled as actual code for several of these flows.

## The core architecture decision

The interesting design choice is the separation of **physical distribution**, **license activation**, **user ownership**, and **digital-content creation**.

The physical object can move through an intermediary channel before the final user has an account. Ownership is not permanently assigned merely because an intermediary activates the medium; instead, the system carries an intended recipient and resolves ownership through the later authenticated claim flow.

That requires the system to model intermediate states explicitly rather than collapsing the physical link, digital license, user, and final content into one record.

## Concurrency and state integrity

Two implementation choices are especially inspectable in the public document:

### Conditional reservation during activation

The link is updated only while it is inactive and has no existing license. This prevents a second activation path from silently overwriting an already-reserved link.

### Atomic license claim

The claim operation updates ownership only while `id_user` is still `NULL`. If no row is updated, the flow distinguishes an already-claimed license from a missing license rather than assigning ownership optimistically.

These are small details, but they show that the architecture treats race conditions as part of the business workflow rather than as an afterthought.

## What this evidence supports

This public artifact supports evidence of work around:

- relational data and lifecycle modeling;
- offline-to-online system design;
- API and state-machine thinking;
- authentication/authorization boundaries;
- concurrency-aware application logic;
- intermediary and end-user workflow design;
- translating a product mechanism into a formal technical specification.

## Evidence boundary

The source document names **Gianluca Cioni & team**, so this casefile does **not** claim sole authorship of every idea, line of code, or implementation detail.

It also does not independently assert that the document's legal novelty claims are correct; those claims are part of the prior-art publication itself. The portfolio claim is narrower: this is a genuine, dated, public technical specification associated with work Gianluca participated in on Connecting Beyond, and its technical content can be inspected directly.

## Read the original evidence

- [Open the public repository →](https://github.com/G-Cioni/sys-arch-doc)
- [Read `spec_v1.pdf` →](https://github.com/G-Cioni/sys-arch-doc/blob/main/spec_v1.pdf)
- The repository also contains the corresponding `spec_v1.pdf.m7m` artifact.
