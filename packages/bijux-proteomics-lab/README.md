# bijux-proteomics-lab

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-lab/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-lab/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-lab.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-lab.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

`bijux-proteomics-lab` converts scientific requirements into executable assay
plans, schedule-aware experiment batches, and outcome summaries that feed back
into program decisions.

If you need planning outputs that are constrained by dependencies, capacity,
and review gates, this is the package boundary.

## What this package owns

- experiment planning, dependency ordering, and scheduling heuristics
- review packet generation and plan risk summaries
- assay outcome interpretation, failure triage, and rerun recommendations
- repository contracts for plan, queue, and feedback persistence

## What this package does not own

- core program-stage and review decision ownership
- candidate scoring and scenario recommendation policies
- evidence trust scoring and contradiction resolution semantics

## Source map

- [`src/bijux_proteomics_lab/planning.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py) for planning and scheduling models
- [`src/bijux_proteomics_lab/outcomes.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py) for outcome interpretation and rerun decisions
- [`src/bijux_proteomics_lab/repositories.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py) for repository contracts and trend summaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-lab/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/docs/maintainer/pypi.md)

## Primary entrypoint

- import-first library package; no console script is published
