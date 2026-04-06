# bijux-proteomics-intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

`bijux-proteomics-intelligence` converts program intent and evidence posture into
ranked candidate decisions with explicit policy, explainability, and risk
signals.

If you need design briefs, ranking decisions, rejection reasons, or scenario
recommendations, this package is the decision intelligence boundary.

## What this package owns

- program-to-brief translation and decision context derivation
- policy-driven candidate ranking, screening, and rejection coding
- scenario evaluators for progression, synthesis, scale-up, and redesign
- explainability and portfolio-level decision summaries

## What this package does not own

- core program entity definitions and review-gate state ownership
- evidence ingestion, trust scoring, and contradiction resolution
- lab batch scheduling, execution outcomes, and rerun planning

## Source map

- [`src/bijux_proteomics_intelligence/briefs.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py) for design brief and ranking behavior
- [`src/bijux_proteomics_intelligence/policies.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/policies.py) for ranking and decision policy models
- [`src/bijux_proteomics_intelligence/evaluators.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/evaluators.py) for scenario and portfolio evaluators
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-intelligence/tests) for executable package expectations

## Read this next

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/maintainer/pypi.md)
