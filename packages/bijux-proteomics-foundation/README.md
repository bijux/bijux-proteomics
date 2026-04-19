# bijux-proteomics-foundation

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-foundation/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-foundation/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-foundation` provides the shared schema and serialization layer
for the package family, including canonical JSON behavior, document
fingerprinting, and compatibility contracts for persisted scientific records.

Use this package when you need versioned document governance, migration-safe
serialization, and cross-package consistency for reproducible proteomics data.

## Why teams pick this package

- one canonical schema baseline across every proteomics package
- stable fingerprints for cache keys, lineage, and provenance checks
- compatibility helpers for migration-safe long-lived scientific records
- typed primitives that reduce duplicated schema logic in downstream packages

## Typical use cases

- define document schema metadata with explicit version and compatibility policy
- serialize domain models into canonical JSON for reproducible comparisons
- validate migration paths before accepting persisted record upgrades
- centralize schema behavior so other packages stay focused on domain logic

## Installation

```bash
pip install bijux-proteomics-foundation
```

## Quick start

```python
from bijux_proteomics_foundation import schema, serialization
```

## Package boundaries

This package owns schema metadata, canonical serialization, and migration compatibility helpers.

It does not own product decision logic, lab logic, or runtime orchestration.

## Source guide

- [`src/bijux_proteomics_foundation/schema.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/schema.py) for schema profile and compatibility contracts
- [`src/bijux_proteomics_foundation/serialization.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization.py) for canonical serialization and fingerprints
- [`src/bijux_proteomics_foundation/migrations.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/migrations.py) for migration behavior
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-foundation/tests) for executable behavior expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/operations/release-and-versioning/)
