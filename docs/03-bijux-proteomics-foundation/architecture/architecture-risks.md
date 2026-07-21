---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Architecture Risks

Foundation failures propagate widely because every higher package consumes its identifiers, models, serialization, hashes, or outcomes. A small convenience change can become a repository-wide contract break.

| Risk | Consequence | Control |
| --- | --- | --- |
| Identifier collapse | Programs, claims, evidence, assays, and artifacts become interchangeable strings | Preserve distinct validated identifier types |
| Non-canonical encoding | Equal logical values produce different bytes or hashes | Normalize supported values and test canonical JSON determinism |
| Hash semantic drift | Existing digests change after an implementation update | Version the contract and verify stable vectors across releases |
| Permissive model evolution | Unknown or misspelled fields are silently accepted | Keep strict models and explicit schema assessment |
| Migration guesswork | Unsupported documents are partially coerced | Require a known source, target, and declared migration path |
| Policy leakage | Shared results or states encode one package’s scientific decision | Keep foundation outcomes neutral and downstream policy local |
| Root API growth | Specialized concepts become de facto universal contracts | Enforce the curated export budget and owner-module boundaries |
| Time-dependent identity | Timestamps or process state alter content fingerprints | Separate audit metadata from contract-relevant canonical content |

```mermaid
flowchart TD
    C[Contract change] --> I{Identifier, schema, encoding, hash, outcome?}
    I -->|yes| V[Cross-package compatibility review]
    I -->|no| L[Local owner review]
    V --> M{Existing documents remain readable?}
    M -->|yes| T[Stable-vector and consumer tests]
    M -->|no| G[Versioned migration and release guidance]
```

The highest-risk change is one that appears backward compatible in Python but changes serialized meaning. Compatibility must be evaluated against persisted documents and downstream consumers, not import success alone.
