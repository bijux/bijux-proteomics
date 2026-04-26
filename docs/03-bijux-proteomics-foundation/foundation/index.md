---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Foundation

`bijux-proteomics-foundation` exists to keep shared payload meaning stable
across the proteomics package family. Open this section when the important
question is not how a workflow runs, but why schemas, identifiers,
serialization, and migration helpers belong here in the first place.

These pages should help readers separate shared meaning from downstream policy.
When this section is doing its job well, a scientist or maintainer can explain
why higher packages may change workflow rules without changing what a payload,
identifier, or fingerprint means.

## Start Here

- open [Package Overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/package-overview/) for the shortest explanation of
  what the shared meaning layer owns
- open [Ownership Boundary](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/ownership-boundary/) when the issue may actually
  belong in core, knowledge, intelligence, lab, or runtime
- open [Lifecycle Overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/lifecycle-overview/) when the key question is how
  identifiers, payloads, and migrations stay stable over time

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/change-principles/)

## Open This Section When

- you need the durable ownership story before reading code or compatibility
  details
- you are deciding whether a change affects shared payload meaning or only a
  downstream workflow
- you need the package vocabulary for schemas, fingerprints, identifiers, and
  migrations

## Open Another Section When

- the question is already about public imports, schema contracts, or serialized
  artifacts
- the real issue is operational, such as setup, validation, or release
- you already know the boundary and need proof, risk posture, or review
  criteria instead

## Across This Package

- open [Architecture](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/) when you need the structural
  map behind schema, serialization, and migration code
- open [Interfaces](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/) when the question is about imports,
  contracts, or compatibility promises
- open [Operations](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/) when you need repeatable maintainer
  workflows for shared contract changes
- open [Quality](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/quality/) when you need evidence that the shared
  meaning layer is actually protected

## Concrete Anchors

- `packages/bijux-proteomics-foundation` as the package root
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation` as the
  import boundary
- `packages/bijux-proteomics-foundation/tests` as the proof surface for shared
  contracts

## Bottom Line

Open this section to answer the ownership question with integrity:
`bijux-proteomics-foundation` exists so every downstream package can agree on
payload meaning before they disagree on policy. If a proposal broadens this
package without making that shared-meaning story clearer, it is probably
crossing the boundary rather than improving it.

