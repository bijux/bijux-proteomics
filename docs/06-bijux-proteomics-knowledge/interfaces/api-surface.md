---
title: Python API Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Python API surface

`bijux-proteomics-knowledge` exposes a Python facade for evidence memory and
biological grounding. It does not own a standalone HTTP service or command-line
product. Applications may transport these contracts, but they must not replace
knowledge statuses with transport-level success or failure.

## Root facade

The curated root contains 61 symbols grouped by durable responsibility.

| Group | Representative root exports |
| --- | --- |
| memory anchors | `EvidenceRecord`, `EvidenceBundle`, `EvidenceClaim` |
| review handoff | `KnowledgeDecisionBrief` |
| protein identity | `resolve_protein_ids`, `ProteinIdResolutionEntry`, `ProteinIdentityResolutionStatus` |
| coverage | `compute_knowledge_coverage`, coverage policies, entries, summaries, reports |
| pathways and complexes | resolution operations, coverage policies, confidence statuses, reports |
| disease and drug context | term and target resolution operations, entries, summaries, reports |
| PTM context | kinase-substrate resolution and match types |
| sequence context | feature-overlap intervals, types, entries, and operation |
| cross-species context | ortholog mapping, evidence statuses, ambiguities, reports |
| portability | TSV renderers and `evaluate_schema_compatibility` |

## Evidence-memory contracts

```python
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceClaim, EvidenceRecord
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceKind,
    EvidenceOrigin,
    EvidenceStrength,
)
```

An `EvidenceRecord` requires a stable ID, evidence kind, title, source, claim,
confidence, and strength. It can also retain source URI, origin, extraction
method, assay and biological context, quantitative support, proteomics artifact
flags, decision tags, derivation, observation time, and expiry. An
`EvidenceClaim` separately records its statement, support and contradiction
links, assumptions, resolution assays, status, polarity, evidence state,
confidence, and decision impact.

Keeping records and claims separate permits several claims to cite one record,
allows contradictions to remain explicit, and avoids treating a source
statement as an already adjudicated conclusion.

## Grounding operation pattern

```python
from bijux_proteomics_knowledge import (
    render_protein_id_resolution_tsv,
    resolve_protein_ids,
)

entries = resolve_protein_ids(
    ("P69905", "HBA1", "unknown-protein"),
    annotation_pack,
    species="Homo sapiens",
)
review_table = render_protein_id_resolution_tsv(entries)
```

The output can contain exact accession matches, annotation-identifier matches,
gene-symbol matches, ambiguous aliases, and unresolved entries. The operation
does not query an implicit global database: its authority is the supplied
annotation pack and optional species constraint.

The pathway, complex, disease, drug-target, kinase-substrate, feature-overlap,
and ortholog surfaces follow the same design: explicit input collections or
annotation packs, typed per-entity outcomes, a stable summary, and a reviewable
TSV representation.

## Specialized owner modules

The root intentionally does not flatten every contract. Use these documented
owners for deeper work:

- `memory.models` for the full evidence and claim vocabulary;
- `memory.integrity` for graph construction, validation, and decision traces;
- `memory.normalization` for evidence ingestion;
- `memory.reconciliation` for conflict policies, actions, records, and belief
  updates;
- `references.grounding` for citation, literature, ontology, context, and rule
  contracts;
- `references.workflows` for comparator, literature-audit, evidence-sufficiency,
  contradiction, replay, release, and risk artifacts;
- `reviews` for explanations, provenance, trends, flagship evidence, and
  decision briefs.

## Failure and ambiguity

Validation errors reject malformed typed payloads. Resolution operations keep
unresolved and ambiguous rows in their results. Graph validation reports
dangling or missing relations. Reconciliation can require curation, split by
context or modality, or hold a decision. None of these states is equivalent to
a software crash, and consumers must serialize them faithfully.

Schema compatibility checks cover document shape, not scientific equivalence
or annotation freshness. See [Compatibility commitments](compatibility-commitments.md)
for the combined import, schema, enum, and meaning contract.
