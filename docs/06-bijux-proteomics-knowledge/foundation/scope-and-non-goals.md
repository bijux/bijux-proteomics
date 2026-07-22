---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-22
---

# Scope and Non-Goals

`bijux-proteomics-knowledge` owns durable evidence state: what source was
observed, which biological subject and context it concerns, which claim it
supports or contradicts, how disagreement was reviewed, and what remains
unknown. It preserves evidence for later judgment without making the judgment
itself.

## In Scope

- source, retrieval, release, license, and derivation provenance;
- protein, gene, isoform, ortholog, pathway, complex, disease, drug, feature,
  and assay identity resolution;
- evidence records, bundles, claims, typed relationships, and decision lineage;
- biological context, quantitative uncertainty, artifact flags, and source
  independence;
- evidence graphs, integrity checks, coverage, freshness, and knowledge gaps;
- contradiction detection, clustering, reconciliation, escalation, and holds;
- decision-scoped briefs that preserve support, adverse evidence, and
  unresolved questions; and
- append-only belief updates linked to named evidence and policy revisions.

## Explicit Non-Goals

| Not owned here | Responsible boundary |
| --- | --- |
| parsing raw proteomics formats, statistical analysis, and scientific acceptance | Core |
| executing, resuming, or replaying work | Runtime |
| ranking candidates, choosing an action, and promoting advisory policy | Intelligence |
| assay feasibility, custody, observations, and evidence-promotion execution | Lab |
| shared identifiers, document envelopes, canonical bytes, and schema primitives | Foundation |
| source access credentials, database transactions, and service transport | deploying application |

Knowledge does not claim exhaustive coverage merely because a graph is valid.
It does not treat a citation as contextual support, a resolved identifier as
biological equivalence, record count as independent replication, or confidence
as calibrated decision probability.

```mermaid
flowchart LR
    source["versioned source"] --> record["contextual evidence record"]
    record --> claim["support or contradiction"]
    claim --> graph["validated evidence graph"]
    graph --> review{"reconciliation and sufficiency"}
    review --> brief["decision-scoped evidence brief"]
    review --> hold["gap, dispute, or hold"]
    brief -. "consumed by" .-> judgment["Intelligence judgment"]
```

## Ownership test

A behavior belongs here when it changes what evidence is retained, connected,
qualified, or considered sufficient while leaving the underlying scientific
calculation and downstream decision policy unchanged. It belongs elsewhere
when it creates the scientific observation, executes work, ranks actions, or
authorizes a laboratory handoff.

A trustworthy handoff includes the source and retrieval identity, subject and
context, relationship direction, quantitative uncertainty, derivation and
independence, freshness, competing evidence, resolution history, coverage,
gaps, and review disposition.
