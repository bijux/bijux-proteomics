---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Execution Model

Core executes scientific transformations as explicit, inspectable stages. Each stage accepts declared inputs, validates its assumptions, emits stable outputs, and preserves enough lineage to explain exclusions and derived values.

```mermaid
flowchart LR
    A[Files and study metadata] --> B[Parse and validate]
    B --> C[Normalized run bundle]
    C --> D[Identification and FDR]
    D --> E[Quantification and QC]
    E --> F[Specialized analyses]
    F --> G[Interpretation]
    G --> H[Reviewable tables, cards, and reports]
    B --> X[Rejected rows and diagnostics]
    D --> X
    E --> X
```

## Stage contracts

Ingestion does more than load files: it establishes format validity, sample and run identity, source-row lineage, and experimental-design consistency. Identification converts search output into explicit PSM, peptide, and protein evidence and records target-decoy and grouping decisions. Quantification carries normalization, missingness, roll-up, statistics, and QC choices forward instead of presenting a matrix without its derivation.

Specialized stages add acquisition or biological semantics—DIA transition evidence, multiplex interference, isotope labels, PTM localization, proteoforms, targeted assays—without discarding their upstream evidence. Interpretation then maps results to annotation, pathways, complexes, regulators, or biological context. Review modules package claims, evidence graphs, explanations, and structural diagnostics for inspection.

## Invocation paths

```mermaid
sequenceDiagram
    participant User
    participant Interface as CLI or Python API
    participant Workflow
    participant Domain as Scientific modules
    participant Output as Stable output writer
    User->>Interface: inputs and explicit options
    Interface->>Workflow: validated request
    Workflow->>Domain: compose scientific stages
    Domain-->>Workflow: results, exclusions, provenance
    Workflow->>Output: tables, cards, reports
    Output-->>User: reviewable artifact set
```

The CLI and Python entrypoints are adapters over the same owned functions. Workflow modules compose calculations; they do not replace family-level contracts. Runtime may schedule these calls and manage run state, but the result of a scientific function must not depend on whether it was invoked from a terminal, notebook, worker, or HTTP service.

## Determinism and refusals

Stable ordering, explicit policies, atomic writes, and retained provenance make repeat execution comparable. Malformed inputs, invalid designs, unsupported formats, and scientifically insufficient evidence are reported as such. They must not be converted into empty success, silently imputed, or omitted from the audit trail.
