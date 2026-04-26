---
title: bijux-proteomics-core
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-core

`bijux-proteomics-core` is the program contract package in
`bijux-proteomics`. Start here when the question is about target
programs, gate definitions, lifecycle states, readiness rules, and the
cross-package contracts that higher layers must respect.

This section should make one boundary obvious: core defines the durable
program and lifecycle rules, but it does not own evidence policy,
scoring policy, or lab execution details.

If someone opens only this page, they should understand that this package owns
the durable program contract surface: assays, targets, constraints, lifecycle
states, readiness rules, execution contracts, and validation logic that the
rest of the stack must obey before it adds policy.

## Start Here

```mermaid
flowchart LR
    reader["reader question<br/>what rules are durable contracts rather than downstream policy?"]
    programs["programs.py, program_spec.py,<br/>targets.py, assays.py"]
    lifecycle["lifecycle.py, constraints.py,<br/>reviews.py, validation.py"]
    execution["execution_contracts.py,<br/>runtime_adapter.py, repositories.py"]
    dependents["knowledge, intelligence, lab,<br/>and runtime must obey these rules"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class programs,lifecycle,execution,dependents positive;
    reader --> programs
    reader --> lifecycle
    reader --> execution
    programs --> dependents
    lifecycle --> dependents
    execution --> dependents
```

## Use This Section When

- you need the package entrypoint for program and gate contracts
- you are checking lifecycle transitions, identifiers, or readiness validation
- you want the shortest route into durable program semantics

## Do Not Use This Section When

- the real disagreement is about evidence truth, ranking policy, lab execution,
  or runtime orchestration
- you need shared payload meaning rather than durable program rules
- you are trying to smuggle downstream policy into a layer that should stay
  contract-focused

## Package Sections

- [Foundation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/)
- [Quality](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/quality/)

## Cross-Package Handoffs

- move to [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/) when shared payload meaning is the real issue
- move to [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) when the question becomes ranking or recommendation policy
- stay here when you need to know whether a rule is part of the durable contract or just a downstream policy choice

## What This Package Clarifies

- which proteomics rules stay stable across downstream package
  disagreements
- how lifecycle, gate, and readiness logic is separated from policy layers
- where execution-facing contracts stop being runtime details and start being
  durable program obligations

## Concrete Anchors

- `packages/bijux-proteomics-core/src/bijux_proteomics/programs.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/lifecycle.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/constraints.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/execution_contracts.py`
- `packages/bijux-proteomics-core/tests` for contract, lifecycle, and
  validation proof

## Reader Takeaway

Open this page when the unresolved question is whether a rule belongs in the
durable program contract or in a downstream policy package. If the answer
depends on evidence judgment, ranking preference, or lab tactics rather than on
shared contract obligations, core should not quietly absorb it.
