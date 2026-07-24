---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Extend Knowledge when a capability creates reusable, reviewable scientific context. Keep analysis policy in Intelligence, measured-data algorithms in Core, operational feasibility in Lab, and transport concerns in Runtime.

## Supported extension shapes

### Curated reference or corpus

Add source metadata and citation grounding under `references/grounding`; add benchmark-specific manifests or narratives under `references/workflows`. External references and bundled fixtures must remain distinguishable. Record source identity, version or retrieval context, scope, and caveats so an evidence record can be reconstructed without package-local lore.

### Identity or biological resolver

An identity resolver belongs in `identity`; domain-specific resolvers live in the narrow biological family they own. A resolver must represent exact matches, weaker associations, ambiguity, and no-match outcomes. Examples include residue-specific kinase evidence, direct versus pathway-neighbor drug relationships, missing complex subunits, sparse pathway coverage, and one-to-many ortholog mappings.

### Evidence and relation model

Shared claim and evidence structures belong in `memory/models`. Ingestion belongs in `memory/normalization`, graph constraints in `memory/integrity`, and conflict policy in `memory/reconciliation`. Do not combine these layers in one generic registry: normalization answers whether a record can enter memory; integrity answers whether links are coherent; reconciliation answers how competing valid records are presented or resolved.

### Coverage or review artifact

Add reusable completeness measures under `coverage` and reviewer-facing synthesis under `reviews`. A new decision artifact should identify its inputs, critical provenance, unresolved conflicts, readiness conditions, and recommendation limits. Deterministic tabular output is part of the contract when the result crosses package or audit boundaries.

## Admission criteria

Every extension must establish:

- a durable scientific owner and a narrow public contract;
- provenance for each externally sourced fact;
- explicit species, coordinate system, evidence context, and applicable scope;
- deterministic normalization, ordering, fingerprints, and rendering;
- first-class unresolved, ambiguous, contradictory, sparse, and unsupported states;
- coverage or confidence behavior when source material is incomplete;
- schema compatibility for persisted artifacts;
- tests for boundary cases and downstream caveat preservation;
- a root export ledger entry only when cross-package use is intentional.

## Rejection rules

Do not add a network client, credential workflow, scheduler, or mutable service cache to Knowledge. Those are runtime or integration responsibilities. Do not add a resolver that converts every alias into a match, a trust score with hidden precedence, or a reference pack without traceable source context. Do not encode an Intelligence recommendation as a curated fact.

An extension is ready when a reviewer can move from a reported association to the exact input record, resolver outcome, source citation, conflict state, and coverage limitation—and when downstream packages can preserve that chain without importing private modules.
