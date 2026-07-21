---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Execution Model

Foundation does not run analyses, schedule work, or manage services. Its execution model is a deterministic contract pipeline: accept a typed value, validate it, encode it canonically, and produce a stable document or an explicit outcome.

```mermaid
sequenceDiagram
    participant Caller
    participant Schema as Document schema
    participant Stable as Stable-value normalization
    participant JSON as Canonical JSON
    participant Digest as Fingerprint / SHA-256
    Caller->>Schema: construct or validate payload
    Schema->>Stable: normalize supported values
    Stable->>JSON: emit canonical representation
    JSON->>Digest: hash canonical bytes
    Digest-->>Caller: deterministic identity
```

## Document path

Typed identifiers and Pydantic models establish the input boundary. Stable-value conversion handles supported scalar and scientific values before canonical JSON fixes key ordering and representation. Fingerprint helpers hash that canonical form, so a digest describes content rather than incidental dictionary order or process state.

Callers should retain both the schema version and digest with persisted material. The version answers how to read the document; the digest answers whether its canonical content changed.

## Compatibility path

When a stored document uses another supported schema version, compatibility assessment identifies the relationship before any mutation occurs. A declared migration then moves the document between known shapes. Import migrations address approved historical module paths separately from schema migrations; neither mechanism guesses at unknown scientific meaning.

```mermaid
flowchart LR
    D[Versioned document] --> A{Compatibility assessment}
    A -->|current| V[Validate]
    A -->|supported migration| M[Migrate then validate]
    A -->|unsupported| R[Structured refusal or failure]
    V --> C[Canonical document]
    M --> C
```

## Failure semantics

Invalid data, unsupported versions, missing optional capabilities, and policy refusals are distinct outcomes. The `outcomes` family preserves that distinction so downstream software can report, retry, or stop deliberately. Exceptions remain available where Python call semantics require them, while structured results carry machine-readable failure information across package and process boundaries.

Because foundation owns no CLI, HTTP application, artifact store, or run manager, those concerns must remain in runtime. A caller can use these primitives inside any execution environment without giving foundation control of that environment.
