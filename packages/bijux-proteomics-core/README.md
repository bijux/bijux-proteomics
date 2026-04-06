# bijux-proteomics-core

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-core/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-core/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-core.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-core.yml)
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

`bijux-proteomics-core` defines protein program entities, lifecycle transitions,
review gates, assay requirements, and execution adapters used by the platform.

If you need to understand what a program is, when it can advance, and which
review constraints must hold before progression, this is the package boundary.

## What this package owns

- program, target, assay, and review domain models
- lifecycle transition and stage eligibility logic
- invariant validation for identifiers, gating, and scientific consistency
- runtime adapter interfaces and CLI entrypoints for program workflows

## What this package does not own

- evidence bundle conflict resolution and trust scoring
- candidate ranking and scenario evaluation policies
- lab scheduling, outcome promotion, and rerun policies

## Source map

- [`src/bijux_proteomics/program_spec.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/program_spec.py) for core program entities
- [`src/bijux_proteomics/repositories.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/repositories.py) for decision and gate repository protocols
- [`src/bijux_proteomics/validation.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/validation.py) for domain invariant checks
- [`src/bijux_proteomics/interfaces`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces) for package-facing CLI boundaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/maintainer/pypi.md)

## Primary entrypoint

- console script: `bijux-proteomics`
