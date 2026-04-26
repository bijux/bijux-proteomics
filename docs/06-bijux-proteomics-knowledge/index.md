---
title: bijux-proteomics-knowledge
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-knowledge

`bijux-proteomics-knowledge` is the evidence and claim package in
`bijux-proteomics`. Open this handbook when the question is about evidence
quality, claim state transitions, contradiction resolution, trust
scoring, or readiness summaries consumed by downstream decision layers.

This section should make one promise clear: knowledge owns the recorded
evidence and claim state that readers can audit later. It is the place
to ask what is known, what conflicts, and how much trust the system can
currently justify.

If someone opens only this page, they should understand that this package is
where proteomics evidence becomes an auditable state: records are stored,
claims are updated, conflicts are resolved, trust is summarized, and review can
work backward from a recommendation to the evidence that supported it.

## Visual Summary

```mermaid
flowchart LR
    reader["reader question<br/>what is currently known, contested, or trusted?"]
    evidence["evidence.py and adapters.py<br/>evidence records and normalization"]
    claims["claims.py and resolution.py<br/>claim state and contradiction handling"]
    review["review.py, graph.py, repositories.py<br/>audit, review, and lineage surfaces"]
    consumers["intelligence and runtime read<br/>the resulting evidence state"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class evidence,claims,review,consumers positive;
    reader --> evidence
    evidence --> claims
    claims --> review
    review --> consumers
```

## Start Here

- open [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/) when the question is why the
  knowledge layer exists or where its boundary stops
- open [Architecture](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/) when you need the
  module map for evidence, claims, resolution, and review behavior
- open [Interfaces](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/) when the question is
  about imports, schemas, payloads, or review artifacts
- open [Quality](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/quality/) when the issue is whether the
  current knowledge state is defended strongly enough to trust

## Use This Section When

- you need the package entrypoint for evidence and claim contracts
- you are checking contradiction handling, freshness, or trust logic
- you want the shortest route into auditable knowledge-state behavior

## Move On When

- the real question is already about ranking policy, experiment planning, or
  runtime orchestration
- you need durable core contracts or shared payload meaning rather than
  evidence-state behavior
- you are expecting this package to make policy decisions instead of to record
  and justify evidence state

## Pages In Knowledge Handbook

- [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/)
- [Quality](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/quality/)

## Cross-Package Handoffs

- move to [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) when the question becomes ranking policy rather than evidence state
- move to [bijux-proteomics-lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/) when the concern becomes assay execution or planning
- stay here when the real issue is whether the current claim state is justified and inspectable

## What This Package Clarifies

- where evidence records, claim state, contradiction handling, and trust
  summaries are actually owned
- how review can inspect why a claim is currently trusted or blocked
- which downstream consumers should read knowledge state rather than redefine
  it

## Concrete Anchors

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/evidence.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/claims.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/resolution.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/review.py`
- `packages/bijux-proteomics-knowledge/tests` for evidence, contradiction, and
  trust proof

## Reader Takeaway

Open this page when the unresolved question is what the system currently knows
and how well it can justify that state. If the answer depends on choosing a
path, scheduling an assay, or executing a run rather than on recording and
auditing evidence, another package owns the next step.
