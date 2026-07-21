---
title: Library and Transport Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Library and transport boundaries

`bijux-proteomics-knowledge` is a Python library and installs no executable or
HTTP application. Evidence curation needs an explicit source corpus,
annotation authority, storage decision, and review identity; a package-level
command could not choose those safely on behalf of every deployment.

The root facade exposes high-value contracts and deterministic resolution
operations:

- `EvidenceRecord`, `EvidenceBundle`, and `EvidenceClaim` for scientific
  memory;
- `KnowledgeDecisionBrief` for review handoff;
- protein, pathway, complex, disease, drug-target, kinase-substrate, feature,
  ortholog, and coverage resolution;
- stable TSV renderers for reviewer-facing tables;
- schema compatibility evaluation for transported knowledge documents.

```python
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceRecord,
    resolve_protein_ids,
)
```

Specialized graph, ingestion, reconciliation, reference, and review operations
remain in their owner modules rather than expanding the root indefinitely.

## Wrap the library without weakening it

| Integration concern | Owning layer |
| --- | --- |
| Evidence and claim meaning | `bijux-proteomics-knowledge` typed contracts |
| Source authentication and access | Importing application or service |
| Database transactions and retention | Deployment repository implementation |
| CLI exit codes and terminal formatting | Consuming command |
| HTTP authentication, pagination, and rate limits | Publishing service |
| Runtime execution and run artifacts | `bijux-proteomics-runtime` |

A wrapper must return ambiguous, unresolved, stale, disputed, and held states
as data. HTTP 200 or process exit code 0 means the request was processed; it
does not mean an identifier resolved uniquely, a claim is supported, or a
decision can advance.

Preserve the complete typed result when crossing a transport boundary:
per-entity outcomes, unresolved inputs, policy identifiers, source locators,
schema metadata, issue codes, and provenance. Do not reduce a resolution
report to a dictionary of matched identifiers or a decision brief to its
headline recommendation.

See [Python API surface](api-surface.md) for the root capability map and
[Entrypoints and worked examples](entrypoints-and-examples.md) for concrete
imports.
