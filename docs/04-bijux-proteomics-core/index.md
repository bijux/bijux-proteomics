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

Core defines the durable program and lifecycle rules, but it does not own
evidence policy, scoring policy, or lab execution details.

This page shows that the package owns the durable program contract surface:
assays, targets, constraints, lifecycle states, readiness rules, execution
contracts, and validation logic that the rest of the stack must obey before it
adds policy.

## Start Here

## Open This Section When

- you need the package entrypoint for program and gate contracts
- you are checking lifecycle transitions, identifiers, or readiness validation
- you want the shortest route into durable program semantics

## Open Another Package When

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

- open [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/) when shared payload meaning is the real issue
- open [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) when the question becomes ranking or recommendation policy
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

## Bottom Line

Open this page when the unresolved question is whether a rule belongs in the
durable program contract or in a downstream policy package. If the answer
depends on evidence judgment, ranking preference, or lab tactics rather than on
shared contract obligations, core should not quietly absorb it.
