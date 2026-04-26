---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section shows which core surfaces are real contracts: commands, imports,
schemas, artifacts, and examples that other packages or operators can rely on
when they build against durable program rules.

These pages stop callers from depending on incidental implementation details
when what they really need is the explicit contract layer. For core,
that matters because lifecycle and readiness assumptions spread quickly into
knowledge, intelligence, lab, and runtime behavior.

## Start Here

- open [CLI Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/cli-surface/) when the dependency begins with operator or
  validation commands
- open [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/) when the real question is lifecycle,
  readiness, or program schema meaning
- open [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/) when the caller depends on Python
  entrypoints rather than CLI usage
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/) when a contract
  change may ripple into higher packages

## Pages In This Section

- [CLI Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/)

## Open This Section When

- you need to know which core surface is deliberate and supportable
- higher packages depend on lifecycle, readiness, or program contracts
- you are reviewing whether a change creates compatibility pressure across the
  proteomics stack

## Open Another Section When

- the real question is why the rule belongs in core at all
- you need structural layout or contract-code organization first
- the issue is operational, such as validation workflow, release steps, or test
  execution

## Across This Package

- open [Foundation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/) when the contract concern is really
  a boundary or ownership question
- open [Architecture](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/) when the surface depends on
  deeper lifecycle, domain, or runtime-adjacent structure
- open [Operations](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/) when you need repeatable workflows
  for exercising or shipping core contracts
- open [Quality](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/quality/) when the real issue is whether the
  documented contract is sufficiently defended

## Concrete Anchors

- CLI entrypoint in `src/bijux_proteomics/interfaces/cli.py`
- core contracts in `src/bijux_proteomics/programs.py`,
  `lifecycle.py`, and `validation.py`
- public exports in `src/bijux_proteomics/__init__.py`
- execution contract helpers in `src/bijux_proteomics/execution_contracts.py`

## Bottom Line

Open this section to separate stable core contracts from whatever merely happens
to be visible in the implementation. If another package cannot defend its
dependency in terms of named commands, imports, schemas, artifacts, examples,
and tests, that dependency is not yet an honest public surface.

