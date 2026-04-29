# bijux-proteomics-lab

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-lab/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-lab/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/workflows/repo%20/%20verify/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)

[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)

[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-lab` converts scientific requirements into executable assay
plans, dependency-aware schedules, and outcome interpretation that feeds back
into program progression decisions.

Use this package when you need lab-in-the-loop planning under gate constraints,
capacity-aware batch construction, and rerun recommendations tied to assay
outcomes.

Its role is downstream of the scientific workflow blueprint, not a substitute
for it. Lab turns stage-owned assay work into executable batches and feedback
loops once core, knowledge, and intelligence have made the workflow legible.

It also now provides typed experiment-design and protocol-planning helpers for
sample preparation, instrument metadata, run-order randomization, multiplex
planning, QC insertion, carryover review, and bundled lab evidence payloads.

## Why teams pick this package

- practical lab planning built around dependencies, capacity, and timing limits
- structured assay plans and review packets ready for scientific operations
- outcome interpretation flows that support rerun and escalation decisions
- repository contracts for integrating plan queues and feedback loops
- deterministic experiment-design validation and protocol planning artifacts

## Typical use cases

- convert candidate requirements into executable assay schedules
- sequence assay batches while respecting constraints and review gates
- summarize execution outcomes and recommend reruns with explicit rationale
- track plan quality trends and feed outcomes back into decision pipelines
- validate design tables and generate reviewable lab protocol bundles

## Installation

```bash
pip install bijux-proteomics-lab
```

## Quick start

```python
from bijux_proteomics_lab import planning, outcomes, repositories
```

For design and protocol planning:

```python
from bijux_proteomics_lab import (
    plan_batch_randomization,
    plan_multiplex_labeling,
    validate_experiment_design,
)
```

## Package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`
- Stable entrypoints: `planning`, `design`, `outcomes`, `repositories`,
  `schema`, and `serialization`

## Package boundaries

This package owns assay planning, schedule generation, outcome interpretation, and rerun strategy support.

It also owns typed experiment-design and protocol-planning contracts when those
surfaces are about executable lab operations rather than raw scientific parsing
or runtime dispatch.

It does not own program-stage authority, ranking policy, or evidence truth semantics.

It also should not define scientific stage meaning on its own. Lab consumes the
workflow spine, then decides how that work gets executed and fed back into the
next cycle.

## Contract checkpoints

- planning outputs must preserve gate, dependency, and material context
- outcome summaries must retain explicit failure, rerun, and promotion signals
- repository contracts must stay storage-agnostic and typed for feedback loops
- downstream packages should ask this layer for execution planning instead of embedding schedule logic locally

## Choose this package when

- you need canonical assay planning, batching, or outcome interpretation logic
- the change affects laboratory behavior rather than only how operators see it
- queues, feedback loops, and rerun guidance should stay typed and reusable

## Route elsewhere when

- the change defines lifecycle authority, evidence truth, ranking policy, or
  transport-bound interfaces
- the helper only reshapes lab results for CLI or API output
- the behavior belongs to one evidence or recommendation workflow instead of
  shared laboratory execution logic

## Verification route

- check `tests` for planning, outcome, repository, and schema proof before
  treating a lab change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when ownership or planning-semantics claims are part of the change
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

## Review questions

- does the change preserve planning, batching, rerun, or outcome-promotion
  semantics rather than interface transport or one-off reporting
- would runtime or intelligence start carrying shadow scheduling or rerun logic
  if this behavior stayed outside lab
- can the change be justified without claiming lifecycle, evidence, ranking, or
  provider-interface ownership

## Escalation route

- route the change outward when the behavior mainly defines lifecycle law,
  evidence truth, recommendation policy, or operator transport
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  proposal looks like workflow-local reporting instead of reusable lab
  scheduling or outcome semantics
- escalate before release when downstream consumers would need package-specific
  rerun or batching exceptions to adopt the change

## Consumer impact signals

- expect downstream review when planning, batching, rerun, or outcome-promotion
  semantics change because operator workflows depend on them staying stable
- treat changes that alter scheduling behavior, rerun decisions, or outcome
  meaning as high-impact even when imports stay stable
- expect a narrower release burden when the change only improves internal
  implementation without changing lab execution semantics

## Explicit non-goals

- this package does not own canonical runtime transport, provider binding, or
  operator entrypoints
- this package does not redefine evidence semantics or recommendation policy
  owned by lower packages
- this package does not exist to preserve compatibility-only imports or release
  governance rules

## Source guide

- [`src/bijux_proteomics_lab/planning.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py) for planning and scheduling models
- [`src/bijux_proteomics_lab/design.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/design.py) for experiment-design validation, protocol metadata, and run-setup planning
- [`src/bijux_proteomics_lab/outcomes.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py) for outcome interpretation and rerun decisions
- [`src/bijux_proteomics_lab/repositories.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py) for repository contracts and trend summaries
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-lab/tests) for executable behavior expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/release-and-versioning/)
- [Experiment design and protocol planning](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/docs/EXPERIMENT_DESIGN.md)
