---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Execution Model

Knowledge processing is an evidence-preserving pipeline. Source material is normalized into records and claims, linked into a validated graph, reconciled without erasing disagreement, and projected into coverage and review outputs.

```mermaid
flowchart LR
    S[Source records] --> N[Normalize identifiers and fields]
    N --> E[Evidence records]
    E --> C[Claims and support links]
    C --> G{Graph integrity}
    G -->|valid| R[Reconcile overlap and conflict]
    G -->|invalid| F[Integrity failure]
    R --> B[Evidence bundle]
    B --> O[Coverage and review outputs]
```

## Ingestion and identity

Normalization establishes stable identifiers, schema shape, source lineage, and comparable values before records enter memory. Biological resolvers expose status and ambiguity explicitly: unresolved and multiply resolved identifiers remain visible outcomes rather than disappearing from a join.

## Graph and reconciliation

Claims point to supporting or challenging evidence. Integrity validation checks that referenced nodes exist and that the graph remains structurally coherent. Reconciliation groups overlapping assertions, records contradictions, and creates a resolution account where policy permits one. It does not overwrite an adverse record merely because another source is preferred.

```mermaid
sequenceDiagram
    participant Caller
    participant Resolver
    participant Memory
    participant Integrity
    participant Review
    Caller->>Resolver: source values and reference context
    Resolver->>Memory: typed entries with status and lineage
    Memory->>Integrity: claims, evidence, relationships
    Integrity->>Review: validated bundle plus conflicts
    Review-->>Caller: coverage, provenance, explanation
```

## Durable outputs

Resolution reports pair row-level entries with summaries, and TSV renderers provide stable, reviewable interchange. Evidence bundles retain source and schema context. Decision briefs, trends, and explanations are derived views and should be regenerable from the retained knowledge state.

Failures distinguish malformed input, schema incompatibility, unresolved identity, incomplete coverage, and graph inconsistency. None of these should be collapsed into “no result”: absence, ambiguity, conflict, and invalidity have different scientific consequences for downstream judgment.
