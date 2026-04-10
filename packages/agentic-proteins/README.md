# agentic-proteins

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
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

`agentic-proteins` provides the deterministic execution engine for protein
design workflows, including replayable runtime artifacts, policy-safe runtime
state transitions, CLI automation, and API boundaries.

Use this package when you need production execution behavior, traceable
artifacts for auditability, or runtime integration points for agentic and
lab-in-the-loop protein design systems.

## Why teams pick this package

- reproducible execution with deterministic run state and replay-oriented controls
- inspectable artifacts for scientific review, incident analysis, and compliance
- integration-ready boundaries for CLI usage, API orchestration, and provider wiring
- clear runtime contracts that keep orchestration behavior stable across releases

## Typical use cases

- run deterministic protein design loops in CI, batch systems, or orchestrators
- capture run artifacts as evidence for downstream review and approval workflows
- expose runtime capabilities through CLI or HTTP integration surfaces
- enforce provider capability checks before expensive or irreversible execution

## Installation

```bash
pip install agentic-proteins
```

## Quick start

```bash
agentic-proteins --help
```

Import-driven usage starts from the runtime and design loop modules:

```python
from agentic_proteins.runtime import models as runtime_models
from agentic_proteins.design_loop import orchestrator
```

## Package boundaries

This package owns runtime execution, lifecycle state, run artifacts, and runtime-facing entrypoints.

It does not own cross-package scientific governance:

- domain lifecycle and review-gate semantics live in `bijux-proteomics-core`
- ranking and scenario reasoning live in `bijux-proteomics-intelligence`
- evidence trust and contradiction resolution live in `bijux-proteomics-knowledge`
- lab scheduling and rerun planning live in `bijux-proteomics-lab`

## Source guide

- [`src/agentic_proteins/runtime`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/runtime) for runtime lifecycle and execution control
- [`src/agentic_proteins/design_loop`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/design_loop) for design-loop orchestration
- [`src/agentic_proteins/interfaces`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/interfaces) for CLI surfaces
- [`src/agentic_proteins/api`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/src/agentic_proteins/api) for HTTP-facing boundaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins/tests) for executable behavior expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/agentic-proteins/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/agentic-proteins/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/agentic-proteins/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/agentic-proteins/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/agentic-proteins/operations/release-and-versioning/)
