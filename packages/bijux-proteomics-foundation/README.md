# bijux-proteomics-foundation

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-foundation/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-foundation/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-foundation.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-foundation.yml)
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

`bijux-proteomics-foundation` provides the shared schema and serialization layer
for the package family, including canonical JSON behavior, document
fingerprinting, and compatibility contracts for persisted scientific records.

Use this package when you need versioned document governance, migration-safe
serialization, and cross-package consistency for reproducible proteomics data.

## What this package owns

- schema metadata primitives for package documents
- canonical JSON serialization and fingerprinting helpers
- migration and compatibility helpers for persisted documents

## What this package does not own

- protein program domain entities and lifecycle logic
- candidate ranking or scenario evaluation logic
- evidence modeling, conflict resolution, and lab planning rules

## Source map

- [`src/bijux_proteomics_foundation/schema.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/schema.py) for schema profile and compatibility contracts
- [`src/bijux_proteomics_foundation/serialization.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization.py) for canonical serialization and fingerprints
- [`src/bijux_proteomics_foundation/migrations.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/migrations.py) for migration-oriented helpers
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-foundation/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/docs/maintainer/pypi.md)

## Primary entrypoint

- import-first library package; no console script is published
