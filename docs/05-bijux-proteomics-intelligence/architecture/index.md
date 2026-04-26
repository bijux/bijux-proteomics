---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Architecture

Use this section when the question is structural: which modules own candidate
state, ranking policy, scenario evaluators, design-loop control,
explainability, and decision outcomes, and how those parts cooperate without
blurring policy, reporting, and domain semantics together.

`bijux-proteomics-intelligence` is easiest to read as a decision system.
Candidate and metric models define the decision substrate, policies and
evaluators score it, briefs and reports explain the result, and design-loop
logic tracks whether progress is converging or stalling.

## Visual Summary

```mermaid
flowchart LR
    candidates["candidate state and portfolio surfaces"]
    policies["ranking factors, policies, and metrics"]
    evaluators["scenario evaluators and decision summaries"]
    briefs["briefs, reports, and explainability outputs"]
    loop["design-loop convergence and stagnation control"]
    reader["reader question<br/>where does this decision behavior live?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class candidates,page reader;
    class policies,evaluators,briefs positive;
    class loop anchor;
    candidates --> policies --> evaluators --> briefs
    evaluators --> loop
    policies --> reader
    evaluators --> reader
    briefs --> reader
```

## Start Here

- open [Module Map](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/module-map/) for the shortest route from filenames to
  owned behavior
- open [Execution Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/execution-model/) when you need the flow from
  candidate input to reviewed recommendation
- open [State and Persistence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/state-and-persistence/) when the question is
  which decisions, outcomes, and reports become durable

## Pages In This Section

- [Module Map](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/architecture-risks/)

## Open This Section When

- you need to know which module family owns a behavior before editing it
- a review is about decomposition, decision flow, or module drift
- you need to explain how candidate models, policies, evaluators, and decision
  outputs relate

## Open Another Section When

- the main question is why the package owns the behavior at all
- you are deciding whether an import, artifact, or schema is a public contract
- the issue is procedural or proof-oriented rather than structural

## Read Across The Package

- open [Foundation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/) for package purpose and ownership
- open [Interfaces](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/) for imports, artifacts, and
  explainability contracts
- open [Operations](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/) for workflows, diagnostics, and
  release procedures
- open [Quality](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/quality/) for invariants, tests, and decision-risk
  pressure

## Concrete Anchors

- `src/bijux_proteomics_intelligence/candidates.py` and `domain/candidates/`
  for candidate state and portfolio logic
- `src/bijux_proteomics_intelligence/policies.py` and `domain/metrics/` for
  ranking factors, metrics, and policy constraints
- `src/bijux_proteomics_intelligence/evaluators.py`, `briefs.py`, and
  `report/` for scenario scoring and explainability outputs
- `src/bijux_proteomics_intelligence/design_loop/` and `outcomes.py` for
  convergence control and post-decision state

## Reader Takeaway

`Architecture` should make the intelligence package legible as a decision
system with named responsibilities. If candidate state, policy logic,
evaluators, and explainability outputs start blending together, the package
becomes harder to trust as the place where recommendations are justified.

## Purpose

This page introduces the intelligence architecture handbook and routes readers
to the pages that explain module groups, dependency direction, execution flow,
and durable state.
