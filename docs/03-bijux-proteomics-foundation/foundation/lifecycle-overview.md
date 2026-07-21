---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Lifecycle Overview

Foundation contracts outlive individual workflows. Their lifecycle therefore separates document revision, schema evolution, content identity, and package release versioning.

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Reviewed: contract validation
    Reviewed --> Revised: content changes
    Revised --> Reviewed: revision and lineage recorded
    Reviewed --> Superseded: replacement accepted
    Superseded --> [*]
```

## Document lifecycle

`DocumentSchema` carries a normalized schema version, producer, source system, document identity and kind, package version, lifecycle status, derivation links, trace links, timestamps, revision, tags, and optional content hash. `touch()` records the actor and advances the revision; `with_content_hash()` binds metadata to canonical payload content.

A revision changes one document instance. A schema migration changes the shape expected for a class of documents. Those events are related but not interchangeable: updating content must not impersonate a schema version change, and migrating shape must preserve enough lineage to explain the new document.

## Schema lifecycle

```mermaid
flowchart LR
    S[Stored schema version] --> A{Assess compatibility}
    A -->|same| V[Validate directly]
    A -->|additive and supported| M[Apply declared migration]
    A -->|breaking or unknown| R[Reject with explicit outcome]
    M --> V
    V --> C[Canonical document and digest]
```

Schema versions use normalized `major.minor.patch` form. Compatibility helpers can recognize supported additive evolution within a major version; migrations remain declared transformations, not best-effort guessing. Import-path migrations are handled separately because Python symbol routing and persisted document shape are different contracts.

Existing hashes, fingerprints, and identifiers must retain their meaning across compatible releases. Any intentional break requires a major schema decision, migration guidance, and downstream verification across every consumer of the affected contract.
