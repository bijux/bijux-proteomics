---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Bijux Proteomics

`bijux-proteomics` is a modular proteomics system. It does not hide its ideas
inside one large package. It separates shared meaning, durable program rules,
evidence state, decision policy, lab execution, and runtime control so each
kind of responsibility can stay legible.

The point of this split is not packaging for its own sake. The point is to make
serious scientific and operational work reviewable: what the system means,
what it knows, how it decides, how it runs, and how it touches the lab are not
the same question and should not collapse into the same code story.

That does not mean the full scientific workflow already exists. Today the
repository is strongest where contracts, package boundaries, and reviewable
domain surfaces are concerned. The end-to-end proteomics workflow story still
needs more explicit stage blueprints and clearer current-scope boundaries.

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/workflows/repo%20/%20verify/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://github.com/bijux/bijux-proteomics/workflows/release-pypi/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://github.com/bijux/bijux-proteomics/workflows/release-ghcr/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-proteomics/workflows/release-github/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-7%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-7-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

```mermaid
flowchart LR
    foundation["foundation<br/>shared meaning<br/>schemas, ids, migrations"]
    core["core<br/>durable program rules<br/>gates, lifecycle, workflows"]
    knowledge["knowledge<br/>evidence state<br/>claims, confidence, contradictions"]
    intelligence["intelligence<br/>decision policy<br/>ranking, scenarios, explanations"]
    lab["lab<br/>assay-facing loop<br/>plans, outcomes, promotion"]
    runtime["runtime<br/>execution control<br/>operators, providers, replay"]
    legacy["agentic-proteins<br/>legacy bridge"]
    maintain["maintain<br/>repo health<br/>docs, checks, release, policy"]

    foundation --> core
    foundation --> knowledge
    foundation --> intelligence
    core --> intelligence
    core --> runtime
    knowledge --> intelligence
    intelligence --> lab
    lab --> knowledge
    runtime --> lab
    legacy -. migrate .-> runtime
    maintain -. verifies .-> foundation
    maintain -. verifies .-> core
    maintain -. verifies .-> knowledge
    maintain -. verifies .-> intelligence
    maintain -. verifies .-> lab
    maintain -. verifies .-> runtime
```

## What Makes This Repository Worth Reading

- it treats proteomics work as a system with distinct layers of truth, policy,
  execution, and experiment
- it keeps evidence and recommendation separate, so a ranking is never allowed
  to masquerade as raw fact
- it keeps runtime and lab behavior separate, so orchestration and assay action
  can evolve without erasing their seam
- it keeps the migration from `agentic-proteins` visible instead of pretending
  the transition never happened

## Current Limit

The current repository can explain and validate package-level responsibilities,
but it is still building the scientific workflow spine that should carry one
proteomics program from sequence intake through assay planning, evidence review,
and advancement decisions.

## Start Here

- Open the [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/)
  when the question is about the system as a whole and not yet about one
  package.
- Open the [Scientific Workflow Roadmap](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientific-workflow-roadmap/)
  when the question is what the current package stack still needs before it
  becomes a full proteomics workflow engine.
- Open one product handbook when you already know where the real idea lives:
  evidence, decisions, lab work, execution, or shared contracts.
- Open the [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
  when the question is how the repository keeps itself honest.

## Package Family At A Glance

The live publishable shape is six real product packages plus one compatibility
bridge:

| Package | Owns |
| --- | --- |
| `bijux-proteomics-foundation` | shared schema compatibility, identifiers, and deterministic serialization |
| `bijux-proteomics-core` | program definitions, lifecycle contracts, and gate semantics |
| `bijux-proteomics-knowledge` | evidence records, claims, confidence, and contradiction state |
| `bijux-proteomics-intelligence` | scoring, ranking, scenario evaluation, and explanations |
| `bijux-proteomics-lab` | assay planning, outcome capture, and lab-facing loop control |
| `bijux-proteomics-runtime` | execution, replay, provider integration, and operator entrypoints |
| `agentic-proteins` | explicit compatibility bridge for legacy imports and checked migration-off paths |

<code>bijux-proteomics-runtime</code> governs execution and replay.
<code>agentic-proteins</code> preserves compatibility entrypoints.

## Reading Paths

- If you want the architecture story first:
  [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/)
  then
  [Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
  then
  [Core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
- If you want the scientific reasoning story first:
  [Knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
  then
  [Intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
  then
  [Lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
- If you want the operational story first:
  [Runtime Handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  then
  [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
  then
  [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)

## First Proof Check

- `packages/` for the package split this page is explaining
- `mkdocs.yml` for the published navigation spine
- package tests, schema artifacts, and workflows once one package clearly owns
  the claim

## Boundary

This page should make the system feel coherent before the reader sees code. It
should not try to replace the owning handbooks for package-level detail.
