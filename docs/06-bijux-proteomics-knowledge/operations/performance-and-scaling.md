---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

Knowledge workloads scale along different axes: records entering memory, identifiers and aliases being resolved, evidence-graph edges, potential conflict pairs, biological memberships, and the amount of provenance retained in review artifacts.

## Cost map

| Operation | Scale driver | Correctness pressure |
| --- | --- | --- |
| ingestion | source records and payload size | validation, deterministic fingerprints, rejection reasons, and duplicate detection |
| identity resolution | identifiers, aliases, species, and candidate matches | ambiguity must remain visible |
| graph integrity | evidence, claims, and edges | missing targets and invalid relationships must be traceable |
| conflict detection | comparable records within the same scientific context | naive all-pairs comparison can grow rapidly |
| reconciliation | conflict clusters, policies, and history | competing provenance and escalation state must survive |
| biological resolvers | queries × pathway, complex, kinase, drug, disease, feature, or ortholog entries | missing members, indirect relations, and sparse coverage affect confidence |
| decision briefs | claims, evidence, conflicts, citations, and findings | critical provenance and unresolved disagreement cannot be truncated |

## Partition without erasing meaning

Ingestion can be batched when each batch retains a source manifest and deterministic record identities. Integrity and conflict checks may be partitioned by stable scientific keys—such as target, species, assay context, or claim scope—only when a final cross-partition audit proves that no valid comparison was excluded.

`flag_conflicting_evidence` compares record pairs, so unconstrained bundles can become expensive. The safe optimization is a reviewed compatibility index that narrows candidates using the same context rules, followed by exact conflict evaluation. It is not an arbitrary first-match shortcut.

Identity and biological resolvers benefit from precomputed indexes over canonical accession, alias, species, or membership keys. Index entries must retain all candidates and evidence tiers; an index that collapses ambiguity changes the scientific result.

## Measure complete work

The package includes behavioral benchmark and reference-ledger tests, but it does not currently publish a dedicated end-to-end performance suite or service-level objective. Measure representative curation jobs in the deployment environment and record:

- source and accepted record counts;
- rejected, skipped, duplicate, and unresolved counts;
- claim and edge counts;
- candidate conflict pairs and resulting clusters;
- resolver query counts and ambiguous results;
- wall time and peak memory by stage;
- artifact size, coverage, and decision-brief size.

Performance evidence is incomplete if it omits the ambiguity, conflict, or coverage outcomes that determine whether two runs did equivalent scientific work.

## Safe optimization order

1. Validate and fingerprint once at ingestion boundaries.
2. Reuse immutable indexes keyed by artifact and policy fingerprints.
3. Batch independent source records while retaining per-record rejection detail.
4. Narrow pairwise comparisons with scientifically valid context keys.
5. Build layered review artifacts rather than dropping provenance.
6. Move scheduling, persistence, and parallel execution into Runtime.

When memory no longer fits one process, partition governed artifacts and keep a manifest that preserves global identity, cross-partition integrity, and reconciliation scope. Scaling storage is not complete until a reviewer can still trace a decision to the exact source record and conflict state.
