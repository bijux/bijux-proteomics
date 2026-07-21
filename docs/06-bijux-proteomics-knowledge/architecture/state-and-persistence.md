---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# State and Persistence

Knowledge memory is append-oriented and provenance-preserving. Current state can be projected for use, but the records and resolutions that produced it remain available for audit.

```mermaid
flowchart LR
    E[Evidence records] --> B[Evidence bundle]
    C[Claims and assumptions] --> B
    B --> G[Validated evidence graph]
    G --> R[Resolution records]
    R --> S[Current state index]
    G --> H[Historical decision lineage]
    R --> H
    S --> V[Review and grounding views]
```

## Durable memory

- evidence records retain source URI, type, origin, extraction method, biological and experimental context, quantitative support, artifact flags, confidence, timestamps, and decision tags;
- claims retain structured statement, assumptions, supporting and contradicting evidence, status, polarity, confidence, resolution state, and proposed resolution assays;
- bundles retain document schema, target, records, trust, freshness, context, triangulation, coverage, and integrity findings;
- graphs retain targets, claims, evidence, decisions, assays, assumptions, questions, liabilities, and directed relations;
- reconciliation records retain compared evidence, action, policy, rationale, actor, time, and belief impact;
- biological grounding reports retain reference context, row-level status, ambiguity, coverage, and summaries.

## Mutation and projection

Source evidence is not edited merely to make the current claim state cleaner. Corrections and superseding sources create attributable records; reconciliation changes the current interpretation while preserving the prior conflict. Review briefs, coverage reports, and TSV exports are projections and should remain regenerable from durable memory.

The storage backend is not the authority. Whether records live in memory, files, or a service, their schema, identifiers, provenance, conflict history, and reference context determine their scientific meaning.
