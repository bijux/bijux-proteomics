---
title: Knowledge Artifact Contracts
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Knowledge artifact contracts

Knowledge artifacts are the durable memory between analytical execution and a
decision. They must preserve enough context to reproduce a claim's support,
challenge it, and detect when its evidence has become stale.

## Canonical artifacts

| Artifact | Durable content |
| --- | --- |
| evidence record | source, context, quantitative support, flags, confidence, lineage |
| evidence bundle | target-scoped records plus schema and provenance envelope |
| governed bundle | evidence plus digested runtime, summary, and review references |
| evidence graph | explicit relationships among evidence, claims, targets, and decisions |
| claim dossier | support, contradictions, assumptions, falsifiers, and resolution route |
| decision brief | evidence posture translated for a bounded review decision |
| resolution report | matched, ambiguous, missing, and unresolved biological mappings |

Every artifact has a different trust claim. A source digest establishes content
identity, a graph establishes recorded connectivity, and a decision brief
establishes a review view. None alone establishes biological truth.

## Provenance and reconciliation

Conflict resolution produces a new resolution record; it does not edit the
losing evidence into agreement. Provenance lines retain the claim, source,
artifact, and decision route. Escalation queues capture unresolved conflicts
that need human or experimental adjudication.

```mermaid
flowchart TD
    records["immutable evidence records"] --> graph["evidence graph"]
    graph --> conflict["conflict detection"]
    conflict -->|policy can resolve| resolution["new resolution record"]
    conflict -->|insufficient basis| queue["escalation queue"]
    resolution --> brief["decision brief"]
    queue --> brief
```

Literature freshness audits, unsupported-claim ledgers, contradiction dossiers,
knowledge-deficit reports, and replay-proof ledgers expose weaknesses instead
of removing them from publication artifacts.

## Biological reference artifacts

Resolution reports carry structured entries and summaries. Their TSV renderers
provide stable reviewer columns for protein IDs, features, pathways, complexes,
kinases, drugs, disease terms, orthologs, and coverage. Publish the typed report
beside a TSV when ambiguity, policy, or nested provenance cannot be represented
faithfully in a flat row.

Reference packs should be versioned and attributable. A result without the
reference-pack identity cannot be distinguished from drift caused by updated
aliases, memberships, or annotations.

## Publication checklist

Before publishing a knowledge artifact, confirm:

1. schema, artifact, target, and evidence identifiers are stable;
2. source URI or locator, source type, origin, extraction method, and curator
   are recoverable;
3. biological and experimental context is present where it constrains meaning;
4. supporting, contradicting, stale, ambiguous, and unresolved states remain
   visible;
5. reference-pack and policy identity accompany biological resolution;
6. canonical JSON is retained when a TSV or narrative is emitted;
7. derived decisions reference rather than replace their upstream artifacts.

This set is the minimum needed to audit what was known at the time of a
decision.
