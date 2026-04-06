# bijux-proteomics

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI: agentic-proteins](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-agentic-proteins.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-agentic-proteins.yml)
[![CI: foundation](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-foundation.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-foundation.yml)
[![CI: core](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-core.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-core.yml)
[![CI: intelligence](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-intelligence.yml)
[![CI: knowledge](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-knowledge.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-knowledge.yml)
[![CI: lab](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-lab.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/ci-bijux-proteomics-lab.yml)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

`bijux-proteomics` is a contract-first, multi-package Python workspace for
protein discovery and lab-in-the-loop workflows.

It separates execution runtime, domain program modeling, decision intelligence,
evidence governance, and lab planning into explicit package boundaries so
contributors can evolve each layer without collapsing the system into one
opaque codebase.

## Why `bijux-proteomics` Exists

Protein workflows become difficult to trust when target modeling, evidence
reasoning, candidate scoring, and experiment planning are bundled into one
surface.

This repository keeps those concerns separated and explicit:

- `agentic-proteins` for deterministic runtime execution
- `foundation` for shared schema and canonical serialization behavior
- `core` for durable program and review-gate domain contracts
- `intelligence` for policy-driven candidate ranking and scenario decisions
- `knowledge` for evidence trust, conflicts, and claim lineage
- `lab` for scheduling, outcomes, and rerun recommendations

## Package Map

| Package | Purpose | PyPI | Source |
| --- | --- | --- | --- |
| `agentic-proteins` | Deterministic runtime, CLI, and API execution | <https://pypi.org/project/agentic-proteins/> | [`packages/agentic-proteins`](packages/agentic-proteins) |
| `bijux-proteomics-foundation` | Shared schema and serialization contracts | <https://pypi.org/project/bijux-proteomics-foundation/> | [`packages/bijux-proteomics-foundation`](packages/bijux-proteomics-foundation) |
| `bijux-proteomics-core` | Program, lifecycle, and review-gate domain contracts | <https://pypi.org/project/bijux-proteomics-core/> | [`packages/bijux-proteomics-core`](packages/bijux-proteomics-core) |
| `bijux-proteomics-intelligence` | Candidate scoring, policy, and scenario evaluation | <https://pypi.org/project/bijux-proteomics-intelligence/> | [`packages/bijux-proteomics-intelligence`](packages/bijux-proteomics-intelligence) |
| `bijux-proteomics-knowledge` | Evidence bundles, trust scoring, and conflict resolution | <https://pypi.org/project/bijux-proteomics-knowledge/> | [`packages/bijux-proteomics-knowledge`](packages/bijux-proteomics-knowledge) |
| `bijux-proteomics-lab` | Lab planning, outcome modeling, and rerun policies | <https://pypi.org/project/bijux-proteomics-lab/> | [`packages/bijux-proteomics-lab`](packages/bijux-proteomics-lab) |

## Start Here

- Want runtime execution behavior: `packages/agentic-proteins/README.md`
- Want domain contracts: `packages/bijux-proteomics-core/README.md`
- Want ranking and scenarios: `packages/bijux-proteomics-intelligence/README.md`
- Want evidence lineage and conflicts: `packages/bijux-proteomics-knowledge/README.md`
- Want lab planning and outcomes: `packages/bijux-proteomics-lab/README.md`
- Want shared serialization/schema primitives: `packages/bijux-proteomics-foundation/README.md`

## Repository Design

The root keeps repository-owned concerns explicit:

- `apis/` for checked-in API contracts
- `configs/` for shared quality and gate settings
- `docs/` for repository handbook material
- `makes/` for gate and orchestration automation
- `.github/workflows/` for CI/release conventions
- `packages/` for publishable package boundaries

This structure is the governance surface for all package-level development.
