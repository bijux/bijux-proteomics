# bijux-proteomics-knowledge

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-knowledge.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-knowledge.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

`bijux-proteomics-knowledge` models the evidence layer that supports or blocks
program decisions through explicit claims, trust scoring, and contradiction
resolution.

If you need to track why a decision was made, what evidence conflicts exist, or
which gaps still block progression, start with this package.

## What this package owns

- evidence record and bundle models with schema-aware serialization
- trust and freshness scoring for evidence posture
- conflict detection, resolution actions, and claim belief updates
- evidence graph validation and decision-lineage construction

## What this package does not own

- core program stage transitions and review gate ownership
- candidate ranking policy and scenario decision synthesis
- lab scheduling and assay execution outcomes

## Source map

- [`src/bijux_proteomics_knowledge/evidence.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/evidence.py) for evidence models, scoring, and conflict detection
- [`src/bijux_proteomics_knowledge/resolution.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/resolution.py) for conflict-resolution policies
- [`src/bijux_proteomics_knowledge/graph.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/graph.py) for evidence graph rules
- [`src/bijux_proteomics_knowledge/claims.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/claims.py) for claim modeling and knowledge gap audits
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-knowledge/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/docs/maintainer/pypi.md)
