---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Bijux Proteomics

`bijux-proteomics` is a split proteomics system with explicit ownership lines.
Foundation keeps shared payload meaning stable. Core owns durable program
contracts. Knowledge owns evidence state. Intelligence owns scoring and
explanations. Lab owns assay planning and outcomes. Runtime owns execution and
replay. `agentic-proteins` remains only as a legacy bridge to the canonical
runtime.

Start here when you need the right handbook before you need detailed code,
schema, or workflow proof. The site root should answer one question quickly:
which surface owns the behavior you are about to inspect.

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
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

## Read This Site In Three Moves

- Open the [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/)
  when the question crosses package boundaries or touches shared governance.
- Open one product handbook when the behavior is already local to one package.
- Open the [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
  when the issue is repository health, automation, schema enforcement, or
  release support.

## Package Roles

| Package | Owns |
| --- | --- |
| `bijux-proteomics-foundation` | shared schema compatibility, identifiers, and deterministic serialization |
| `bijux-proteomics-core` | program definitions, lifecycle contracts, and gate semantics |
| `bijux-proteomics-knowledge` | evidence records, claims, confidence, and contradiction state |
| `bijux-proteomics-intelligence` | scoring, ranking, scenario evaluation, and explanations |
| `bijux-proteomics-lab` | assay planning, outcome capture, and lab-facing loop control |
| `bijux-proteomics-runtime` | execution, replay, provider integration, and operator entrypoints |
| `agentic-proteins` | temporary compatibility forwarding for legacy runtime imports and CLI paths |

## Shared Handbooks

- [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/)
- [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
- [Runtime Handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)

## First Proof Check

- `packages/` for the package split this page is explaining
- `mkdocs.yml` for the published navigation spine
- package tests, schema artifacts, and workflows once one package clearly owns
  the claim

## Boundary

This landing page routes readers. It should not carry detailed product,
execution, or maintainer rules that belong deeper in the site.
