# bijux-proteomics-intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml)
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

`bijux-proteomics-intelligence` transforms program intent and evidence posture
into policy-governed candidate rankings, scenario recommendations, and
decision outputs with explicit explainability and risk signals.

Use this package when you need transparent prioritization logic, rejection
reasoning, and portfolio-aware progression guidance for protein design.

## Why teams pick this package

- policy-first ranking and recommendation outputs with traceable decision rationale
- scenario evaluators that support progression, redesign, and portfolio balancing
- structured rejection reasons and explainability fields for review conversations
- deterministic scoring patterns suitable for governance and automation

## Typical use cases

- rank candidate proteins against defined decision policies
- generate scenario recommendations for advancement or redesign
- produce explainable shortlists for expert review boards
- aggregate portfolio-level signals for sequencing and prioritization

## Installation

```bash
pip install bijux-proteomics-intelligence
```

## Quick start

```python
from bijux_proteomics_intelligence import briefs, policies, evaluators
```

## Package boundaries

This package owns decision intelligence, ranking policy, scenario scoring, and explainability outputs.

It does not own stage transition authority, evidence ingestion contracts, or lab execution scheduling.

## Source guide

- [`src/bijux_proteomics_intelligence/briefs.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py) for design brief construction and ranking behavior
- [`src/bijux_proteomics_intelligence/policies.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/policies.py) for ranking and decision policy models
- [`src/bijux_proteomics_intelligence/evaluators.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/evaluators.py) for scenario and portfolio evaluators
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-intelligence/tests) for executable behavior expectations

## Documentation

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/CONTRACTS.md)
- [PyPI maintainer notes](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/docs/maintainer/pypi.md)
