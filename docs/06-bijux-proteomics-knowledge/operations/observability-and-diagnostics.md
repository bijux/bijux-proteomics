---
title: Observability and Diagnostics
audience: evidence-curator
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Knowledge observability is the ability to explain how source records became a
review recommendation. The principal diagnostic surfaces are serialized
reports and provenance-linked records, not process logs. Each surface answers a
different integrity or interpretation question.

## Evidence health signals

| Surface | Signals |
| --- | --- |
| Ingestion report | input, accepted, skipped, and rejected counts; duplicate identifiers; rejection reasons; accepted fingerprints |
| Identity and membership resolution | canonical accession, match method, ambiguity count, unresolved input, pathway or complex coverage |
| Graph validation and trace | missing nodes, invalid edges, claim-to-evidence paths, and context carried along those paths |
| Evidence-state index | trust, freshness, contradiction, caveat, and decision relevance by evidence record |
| Conflict clusters | participating records, severity, trust posture, resolution, and recommended hold |
| Quality audit | trust score, triangulation score, source balance, gaps, and limiting evidence |
| Critical-claim provenance | claim statement, source records, relation, and evidence state |
| Decision brief | readiness, recommendation, scientific conclusions, unresolved questions, caveats, and next evidence |

Begin with reconciliation invariants. Ingestion counts must balance. Every
evidence identifier referenced by a claim must exist. Fingerprints for accepted
normalized inputs must remain stable unless source meaning changed. Resolution
reports must retain ambiguous and unresolved identifiers instead of forcing a
single match. A direct evidence conflict must appear in the conflict and
decision surfaces.

## Diagnose recommendation changes

Compare source membership and fingerprints, then identity resolution, context,
freshness, trust, conflict clusters, coverage, and gate profile. This ordering
separates changed evidence from changed interpretation policy. A recommendation
may legitimately move because a source aged past a freshness threshold, a
direct contradiction was added, a sparse pathway lost coverage, or a required
context became available. The brief should expose that cause.

For an incident, record bundle and schema identity, affected claim and evidence
identifiers, ingestion reconciliation, graph issues, conflict cluster, state
index entries, gate thresholds, and before-and-after fingerprints. Include
source locations only when the incident channel is authorized for them.

Diagnostics are sufficient when a curator can traverse from recommendation to
claim, evidence, source, context, and governing threshold—and can see ambiguity,
disagreement, and missing coverage without consulting undocumented knowledge.
