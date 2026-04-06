# agentic-proteins

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-agentic-proteins.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-agentic-proteins.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

## Package Family

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![Agentic docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/agentic-proteins/)
[![Foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/)
[![Core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-core/)
[![Intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-intelligence/)
[![Knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-knowledge/)
[![Lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/)

`agentic-proteins` is the deterministic runtime package in the proteomics
workspace. It owns execution flow, runtime artifacts, and replay-oriented
guardrails for protein design workflows.

If you need execution behavior, runtime state transitions, or inspectable run
artifacts, start with this package.

## What this package owns

- deterministic design-loop execution and runtime lifecycle state
- run artifacts, report generation, and replay-safe execution records
- package-local CLI and API entry boundaries
- provider contracts and runtime capability checks

## What this package does not own

- protein program-stage governance and review gate domain contracts
- candidate ranking policy and scenario recommendation behavior
- evidence trust, contradiction policies, and claim-lineage semantics
- lab planning, scheduling, and rerun strategy outputs

## Source map

- [`src/agentic_proteins/runtime`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/runtime) for runtime execution control and lifecycle behavior
- [`src/agentic_proteins/design_loop`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/design_loop) for design-loop orchestration
- [`src/agentic_proteins/interfaces`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/interfaces) for CLI surfaces
- [`src/agentic_proteins/api`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/api) for HTTP-facing boundaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/docs/maintainer/pypi.md)

## Primary entrypoint

- console script: `agentic-proteins`
