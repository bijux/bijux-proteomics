---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Architecture

Open this section when the important question is how the core contract layer is
organized: where program models live, how lifecycle and readiness logic flow,
and how domain rules, interfaces, and runtime-oriented helpers connect without
collapsing into one undifferentiated module.

These pages let readers trace contract logic through real modules
instead of guessing from package names. The goal is to make the structure
legible enough that lifecycle, validation, and runtime-adjacent code can be
changed without quietly blurring ownership boundaries.

## Start Here

- open [Module Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/module-map/) for the fastest route to directory-level
  ownership
- open [Execution Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/execution-model/) when the real question is how core
  rules move through the package
- open [Integration Seams](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/integration-seams/) when a change may blur the
  boundary between core contracts and downstream policy
- open [Architecture Risks](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/architecture-risks/) when structural clarity is
  under pressure from runtime or biology complexity

## Pages In This Section

- [Module Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/architecture-risks/)

## Open This Section When

- you need to trace structural ownership before refactoring contract logic
- you are checking whether lifecycle, domain, and runtime-adjacent code still
  respect a clear layering story
- you need to understand where contract logic ends and orchestration pressure
  begins

## Open Another Section When

- the question is mainly about public commands, imports, schemas, or artifacts
- the issue is operational, such as validation workflow or release handling
- you need proof, risk posture, or done-ness criteria more than a structural map

## Across This Package

- open [Foundation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/) when the structural issue is really
  an ownership question
- open [Interfaces](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/) when architecture reaches a public
  contract or caller-facing surface
- open [Operations](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/) when structure affects repeatable
  validation or release workflows
- open [Quality](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/quality/) when you need proof that the documented
  structure is still protected

## Concrete Anchors

- `src/bijux_proteomics/programs.py`, `targets.py`, and `program_spec.py` for
  durable program contracts
- `src/bijux_proteomics/lifecycle.py`, `validation.py`, and
  `execution_contracts.py` for lifecycle and readiness logic
- `src/bijux_proteomics/domain`, `biology`, `runtime_adapter.py`, and
  `interfaces/cli.py` for adjacent structural seams

## Bottom Line

Open this section to make the contract layer legible enough that a reviewer
can say where core rules live, how they flow, and where they meet neighboring
surfaces. If that answer depends on private memory rather than the docs and
code, the structure is too implicit.

