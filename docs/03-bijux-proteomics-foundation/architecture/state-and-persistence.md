---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# State and Persistence

Foundation defines portable state contracts but does not operate a database, artifact store, or run ledger. Persisted documents remain owned by the package that gives them domain meaning.

```mermaid
flowchart LR
    P[Producer package] --> D[Typed payload]
    D --> S[DocumentSchema]
    D --> C[Canonical JSON]
    C --> H[Content hash]
    S --> A[Persisted artifact]
    H --> A
    A --> R[Consumer validates version, lineage, and hash]
```

## Durable contract elements

- typed identifiers retain entity meaning across package and storage boundaries;
- `DocumentSchema` records producer, package version, schema version, status, lineage, trace links, revision, timestamps, and optional content hash;
- canonical JSON defines the durable byte-level representation for supported values;
- hashes and fingerprints detect content change and support replay comparison;
- provenance pointers address files, records, references, documents, and artifacts without prescribing their storage backend;
- compatibility assessments and migrations keep known historical shapes readable.

## Ownership rules

Foundation can say how a document identifies and describes itself. It cannot decide retention, access control, database indexing, artifact layout, or when a domain record becomes authoritative. Runtime owns operational persistence; knowledge owns evidence memory; lab owns planning and outcome state; intelligence owns decision records.

Timestamps, trace identifiers, and mutable status are audit metadata. Callers must not accidentally include volatile metadata in a content fingerprint intended to identify stable scientific payload. Conversely, omitting schema version or lineage from a stored artifact makes later interpretation unsafe even when the payload still parses.
