---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-22
---

# State and Persistence

Core produces durable scientific artifacts but does not own operational storage. Its responsibility is to make every persisted table, bundle, card, and report self-describing enough to validate and interpret later.

```mermaid
flowchart LR
    S[Source files and rows] --> N[Normalized scientific contracts]
    N --> A[Analysis outputs]
    S --> L[Source-row lineage]
    N --> P[Parameters and policy]
    A --> D[Diagnostics and rejected evidence]
    L --> B[Reviewable artifact bundle]
    P --> B
    A --> B
    D --> B
    B --> R[Runtime or caller persistence]
```

## Durable scientific state

- normalized run bundles retain input identity and experimental design;
- identification artifacts retain scores, evidence level, target-decoy policy, grouping, ambiguity, and FDR;
- quantitative tables retain entity and sample keys, missingness, normalization, roll-up, units, statistics, and provenance;
- PTM, DIA, multiplex, isotope-labeling, proteoform, and targeted outputs retain their specialized contracts;
- review cards, evidence graphs, structure reports, and workflow exports retain links to scientific owners;
- rejected-evidence and issue tables preserve material excluded from primary results.

Stable ordering and atomic file replacement prevent nondeterministic diffs and partial publication. Output validation checks schema and cross-table coherence before an artifact set is treated as complete.

## Persistence boundary

Runtime or the calling application chooses filesystem, database, object-store, retention, and access-control policy. Core must not read hidden service state to interpret a result. A persisted artifact should remain scientifically understandable from its schema, provenance, parameters, and linked inputs even after the process that created it has ended.

## Decide whether a bundle is complete

| Bundle element | Review question | Blocking absence |
| --- | --- | --- |
| input and design identities | which samples, source rows, references, and contrasts were eligible? | result population and comparison cannot be reconstructed |
| schema, units, and evidence level | what does each row and value represent? | rows can be parsed but not interpreted safely |
| active scientific policy | which digestion, search, confidence, inference, normalization, and QC rules applied? | output cannot support a bounded scientific statement |
| accepted and rejected partitions | what entered the result and what was excluded? | selection bias and denominator remain hidden |
| diagnostics and ambiguity | which warnings, shared evidence, missingness, and sensitivity remain? | summary appears stronger than the underlying evidence |
| lineage and content hashes | which source and derived bytes produced each artifact? | comparison and custody are ambiguous |
| disposition and limitations | was the operation accepted, partial, refused, or failed, and under which ceiling? | consumers can mistake file presence for scientific success |

A bundle may be intentionally partial and still complete for review when its
missing or rejected material and resulting claim ceiling are explicit. A set of
primary tables without those companion records is incomplete even when every
file is readable.
