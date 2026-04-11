# bijux-proteomics-lab

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-lab/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-lab/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)

[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)

[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-core/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-knowledge/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-lab` converts scientific requirements into executable assay
plans, dependency-aware schedules, and outcome interpretation that feeds back
into program progression decisions.

Use this package when you need lab-in-the-loop planning under gate constraints,
capacity-aware batch construction, and rerun recommendations tied to assay
outcomes.

## Why teams pick this package

- practical lab planning built around dependencies, capacity, and timing limits
- structured assay plans and review packets ready for scientific operations
- outcome interpretation flows that support rerun and escalation decisions
- repository contracts for integrating plan queues and feedback loops

## Typical use cases

- convert candidate requirements into executable assay schedules
- sequence assay batches while respecting constraints and review gates
- summarize execution outcomes and recommend reruns with explicit rationale
- track plan quality trends and feed outcomes back into decision pipelines

## Installation

```bash
pip install bijux-proteomics-lab
```

## Quick start

```python
from bijux_proteomics_lab import planning, outcomes, repositories
```

## Package boundaries

This package owns assay planning, schedule generation, outcome interpretation, and rerun strategy support.

It does not own program-stage authority, ranking policy, or evidence truth semantics.

## Source guide

- [`src/bijux_proteomics_lab/planning.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py) for planning and scheduling models
- [`src/bijux_proteomics_lab/outcomes.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py) for outcome interpretation and rerun decisions
- [`src/bijux_proteomics_lab/repositories.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py) for repository contracts and trend summaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-lab/tests) for executable behavior expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/operations/release-and-versioning/)
