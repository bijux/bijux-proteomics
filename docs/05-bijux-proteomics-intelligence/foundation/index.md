---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Foundation

Open this section when you need the durable answer to a simple question: why
does `bijux-proteomics-intelligence` exist between auditable knowledge state
below and lab or runtime execution above?

This package is where proteomics evidence and constraints become choices. It
owns ranking policy, candidate comparison, scenario evaluation, explainability
surfaces, and decision summaries that justify why one path should advance over
another.

## Visual Summary

```mermaid
flowchart LR
    inputs["knowledge state, constraints, and candidate inputs"]
    ranking["ranking and portfolio policy"]
    scenarios["scenario evaluation and escalation logic"]
    explain["explanations, briefs, and recommendation reports"]
    handoff["lab and runtime consume the chosen path"]
    reader["reader question<br/>what belongs in the intelligence layer?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class inputs,page reader;
    class ranking,scenarios,explain positive;
    class handoff anchor;
    inputs --> ranking --> scenarios --> explain --> handoff
    ranking --> reader
    scenarios --> reader
    explain --> reader
```

## Start Here

- open [Package Overview](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/package-overview/) for the shortest description of
  the package role
- open [Ownership Boundary](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/ownership-boundary/) when the question is whether
  behavior belongs in knowledge, intelligence, lab, or runtime
- open [Lifecycle Overview](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/lifecycle-overview/) when you need the path from
  candidate inputs to recommended action

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/change-principles/)

## Open This Section When

- you need the package role before looking at modules, policies, or tests
- you are deciding whether a rule is decision policy rather than evidence state
  or lab execution
- a reader needs one page that explains why this package exists without reading
  the whole handbook

## Open Another Section When

- the main question is where a module or result surface lives
- you are deciding whether an import, artifact, or schema is a supported
  contract
- the issue is procedural or proof-oriented rather than boundary-oriented

## Read Across The Package

- open [Architecture](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/) for module groups, execution
  flow, and dependency direction
- open [Interfaces](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/) for imports, artifacts, and
  explanation contracts
- open [Operations](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/) for workflows, diagnostics, and
  release procedures
- open [Quality](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/quality/) for proof surfaces, invariants, and
  decision-risk pressure

## Concrete Anchors

- `packages/bijux-proteomics-intelligence` as the package root
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence` as the import boundary
- `packages/bijux-proteomics-intelligence/tests` as the package proof surface

## Reader Takeaway

`Foundation` leaves no doubt about the package boundary: knowledge tells
us what the evidence currently supports, intelligence decides how to rank and
explain options, lab turns the chosen path into work, and runtime governs how
that work runs.

