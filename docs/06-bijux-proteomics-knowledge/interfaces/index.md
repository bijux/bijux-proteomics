---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Interfaces

Knowledge owns the durable path from source evidence to contradiction-aware
scientific memory. Its interfaces preserve evidence origin, context,
quantitative support, claims, graph lineage, biological annotation resolution,
conflict handling, coverage gaps, and review handoffs.

```mermaid
flowchart LR
    sources["Literature, databases,<br/>runtime and lab artifacts"]
    records["Evidence records"]
    claims["Evidence-backed claims"]
    graph["Lineage graph"]
    grounding["Identity and biological<br/>context resolution"]
    conflicts{"Conflicts or gaps?"}
    resolve["Resolve, split,<br/>curate, or hold"]
    brief["Decision brief"]

    sources --> records --> claims --> graph --> grounding --> conflicts
    conflicts -->|yes| resolve --> brief
    conflicts -->|no| brief
```

## Interface layers

| Layer | Public responsibility | Required uncertainty |
| --- | --- | --- |
| evidence memory | records, bundles, claim links, provenance, expiry | observed, inferred, imported, and synthetic origins remain distinct |
| graph integrity | nodes, relations, decision traces, unresolved questions | missing nodes and support edges are validation findings |
| identity grounding | accession, annotation identifier, gene-symbol resolution | ambiguous aliases and unresolved identifiers remain explicit |
| biological context | pathway, complex, disease, drug, kinase, feature, ortholog resolution | annotation source, coverage, ambiguity, and evidence status remain visible |
| reconciliation | conflict classification, policy, resolution action, belief impact | holds and required curation are valid outcomes |
| review | provenance reports, explanations, decision briefs | unresolved and contradicting evidence travels with the brief |

## Entry routes

The package root provides a curated set of high-value models, resolution
operations, report types, TSV renderers, and schema checks:

```python
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceClaim,
    EvidenceRecord,
    KnowledgeDecisionBrief,
    resolve_protein_ids,
)
```

Specialized evidence-memory and reference-workflow contracts live in documented
owner modules. [Python API surface](api-surface.md) maps the root facade;
[Public imports](public-imports.md) explains when a direct owner-module import
is the more accurate dependency.

## Read by scientific question

- Use [Data contracts](data-contracts.md) for evidence, claims, status,
  provenance, graph, and resolution semantics.
- Use [Artifact contracts](artifact-contracts.md) for persisted bundles,
  coverage reports, contradiction dossiers, and decision briefs.
- Use [Operator workflows](operator-workflows.md) for ingestion, graph
  validation, conflict review, and grounding sequences.
- Use [Compatibility commitments](compatibility-commitments.md) before changing
  a status enum, relation name, resolution action, or report field.

## Trust boundary

Knowledge can show that an identifier resolved against a supplied annotation
pack, that an evidence record supports a claim, or that one resolution policy
prefers an action. It cannot prove that an external source is complete,
current, unbiased, or biologically correct. Resolution is contextual and
policy-bound; it is not deletion of disagreement.

A consumer must therefore keep `ambiguous`, `unresolved`, `conflicted`,
`contradicted`, stale, and hold states intact. Converting them to an empty
result or a generic success destroys the evidence boundary this package exists
to preserve.
