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
flowchart TD
    S[Source records] --> N[Normalize fields and retain source context]
    N --> I{Identity resolution}
    I -->|exact or governed alias| E[Typed evidence records]
    I -->|ambiguous| A[Retain candidate mappings]
    I -->|unresolved| U[Retain unresolved input]
    E --> C[Claims, support, and contradiction links]
    C --> G{Graph integrity}
    G -->|valid| R[Reconcile overlap without erasing conflict]
    G -->|invalid| F[Integrity failure]
    R --> B[Versioned evidence bundle]
    B --> P{Sufficient for requested use?}
    P -->|yes| O[Coverage, provenance, and review output]
    P -->|partial| D[Deficit and narrowed claim]
    P -->|no| X[Refusal with missing evidence]
```

## Ingestion and identity

Normalization establishes stable identifiers, schema shape, source lineage, and comparable values before records enter memory. Biological resolvers expose status and ambiguity explicitly: unresolved and multiply resolved identifiers remain visible outcomes rather than disappearing from a join.

## Graph and reconciliation

Claims point to supporting or challenging evidence. Integrity validation checks that referenced nodes exist and that the graph remains structurally coherent. Reconciliation groups overlapping assertions, records contradictions, and creates a resolution account where policy permits one. It does not overwrite an adverse record merely because another source is preferred.

| Condition | Durable outcome | Why it is not “no result” |
| --- | --- | --- |
| identifier has several candidates | ambiguous resolution with candidates | the search succeeded but identity remains non-unique |
| identifier has no governed match | unresolved input | absence may expose coverage or source-version limits |
| records disagree in matched context | contradiction retained in the bundle | adverse evidence changes the claim posture |
| relationship exists outside requested context | qualified or non-transferable support | the source may be valid while the transfer is not |
| graph references missing nodes | integrity failure | the knowledge structure is invalid, not merely incomplete |
| coverage misses a declared threshold | evidence deficit or refusal | the requested use exceeds available support |

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

Rebuilding a review output requires the source identities, normalization rules,
resolver versions or corpora, reconciliation policy, graph-integrity result,
and sufficiency threshold. Matching narrative summaries without those inputs is
not an evidence replay.
