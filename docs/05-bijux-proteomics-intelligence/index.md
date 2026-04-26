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

Use this section to distinguish decision policy from the lower-layer contracts
it depends on. Intelligence turns evidence and program constraints into
inspectable recommendations; it does not define the shared payload model or
the execution machinery itself.

This page shows that the package is where proteomics policy becomes an
inspectable recommendation: candidates are scored, scenarios are compared,
outcomes are summarized, and explanations are produced without pretending that
the package also owns evidence truth or execution.

## Start Here

## Open This Section When

- you need the package entrypoint for scoring and recommendation logic
- you are checking ranking policy, scenario evaluation, or explanation outputs
- you want the shortest route into inspectable decision behavior

## Open Another Package When

- the real disagreement is about evidence quality or trust state rather than
  decision policy
- you need durable core contracts or runtime execution behavior instead of
  recommendation logic
- you are expecting this package to settle biology or laboratory truth on its
  own

## Package Sections

- [Foundation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/)
- [Quality](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/quality/)

## Cross-Package Handoffs

- open [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/) when the real disagreement is about evidence or trust state
- open [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) when the rule belongs in a durable contract rather than a ranking policy
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

## Bottom Line

Open this page when the unresolved question is why a recommendation was made.
If the answer depends on evidence truth, durable contract meaning, or run
execution rather than on policy and explanation, intelligence should hand you
to the correct package instead of pretending to own the whole story.
