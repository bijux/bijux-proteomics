---
title: Compatibility Commitments
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Compatibility commitments

Knowledge compatibility preserves evidence meaning and audit routes across
versions. Loading an old payload is insufficient if its source context,
polarity, ambiguity, freshness, or resolution state is interpreted differently.

## Stable contracts

| Surface | Commitment |
| --- | --- |
| `EvidenceRecord`, `EvidenceBundle`, and `EvidenceClaim` | identifiers, provenance, context, polarity, confidence, and state retain declared meaning |
| evidence graph | edge types and integrity findings remain machine-readable |
| conflict resolution | all contributing records remain available after resolution |
| biological mappings | resolved, ambiguous, unresolved, and source-version states remain distinct |
| `KnowledgeDecisionBrief` | citations and resolution lineage remain recoverable |
| `proteomics-knowledge` | forwards canonical exports without independent curation behavior |

The curated `bijux_proteomics_knowledge` root exposes core evidence models,
schema compatibility, biological resolvers, coverage reports, renderers, and
decision briefs. Domain-specific additions land in their owner modules before
they are considered for the root.

## Meaning-changing edits

Treat these changes as compatibility events:

- confidence, strength, polarity, freshness, or resolution categories change;
- missing context gains a default that resembles observed data;
- ambiguous mappings are collapsed into one identifier;
- a source or database version disappears from a result;
- conflict policy changes which evidence is preferred or escalated;
- flat exports omit identifiers required to reconstruct the typed record.

New optional metadata is additive only when old consumers can ignore it and
new consumers can distinguish absence from an observed default. Tightened
validation is a narrowing change. Removing provenance or changing a state label
is breaking for persisted memory and audit consumers.

## Persistence and migration

Persisted bundles carry schema identity and stable record identifiers. A newer
reader either accepts the version, migrates it explicitly while preserving
source lineage, or rejects it with a compatibility result. It must not guess a
record's version from its fields or rewrite historical evidence in place.

## Verification

```bash
make test PACKAGE=bijux-proteomics-knowledge
make api PACKAGE=bijux-proteomics-knowledge
make build PACKAGE=bijux-proteomics-knowledge
make test PACKAGE=proteomics-knowledge
```

Compatibility evidence includes old-bundle load cases, graph integrity cases,
contradiction and escalation cases, ambiguous mappings, reference-version
fixtures, decision-brief round trips, and alias forwarding when root exports
change. Release notes identify whether evidence semantics, mapping behavior,
artifact shape, or packaging changed.
