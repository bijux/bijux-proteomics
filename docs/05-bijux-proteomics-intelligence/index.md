---
title: bijux-proteomics-intelligence
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-intelligence

`bijux-proteomics-intelligence` is the decision and ranking package in
`bijux-proteomics`. Start here when the question is about candidate
scoring, portfolio ordering, scenario evaluation, or explainability
outputs used to advance or redesign programs.

Readers should use this section to distinguish decision policy from the
lower-layer contracts it depends on. Intelligence turns evidence and
program constraints into inspectable recommendations; it does not define
the shared payload model or the execution machinery itself.

If someone opens only this page, they should understand that this package is
where proteomics policy becomes an inspectable recommendation: candidates are
scored, scenarios are compared, outcomes are summarized, and explanations are
produced without pretending that the package also owns evidence truth or
execution.

## Start Here

```mermaid
flowchart LR
    reader["reader question<br/>why was this candidate or path recommended?"]
    candidates["candidates.py and briefs.py<br/>candidate sets and brief outputs"]
    policy["policies.py and evaluators.py<br/>scoring, weighting, and evaluation rules"]
    outcomes["outcomes.py and serialization.py<br/>explanations and decision artifacts"]
    consumers["lab and runtime consume<br/>the chosen path, not the policy itself"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class candidates,policy,outcomes,consumers positive;
    reader --> candidates
    candidates --> policy
    policy --> outcomes
    outcomes --> consumers
```

## Use This Section When

- you need the package entrypoint for scoring and recommendation logic
- you are checking ranking policy, scenario evaluation, or explanation outputs
- you want the shortest route into inspectable decision behavior

## Do Not Use This Section When

- the real disagreement is about evidence quality or trust state rather than
  decision policy
- you need durable core contracts or runtime execution behavior instead of
  recommendation logic
- you are expecting this package to settle biology or laboratory truth on its
  own

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-knowledge](../06-bijux-proteomics-knowledge/index.md) when the real disagreement is about evidence or trust state
- move to [bijux-proteomics-core](../04-bijux-proteomics-core/index.md) when the rule belongs in a durable contract rather than a ranking policy
- stay here when you need to understand why one candidate or path was recommended over another

## What This Package Clarifies

- where proteomics scoring and ordering policy is actually implemented
- how scenario comparison and explainability artifacts are produced
- which recommendations should stay inspectable without pretending they are
  upstream facts

## Concrete Anchors

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/candidates.py`
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/evaluators.py`
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/policies.py`
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/outcomes.py`
- `packages/bijux-proteomics-intelligence/tests` for ranking and
  explainability proof

## Reader Takeaway

Use this page when the unresolved question is why a recommendation was made.
If the answer depends on evidence truth, durable contract meaning, or run
execution rather than on policy and explanation, intelligence should hand you
to the correct package instead of pretending to own the whole story.
