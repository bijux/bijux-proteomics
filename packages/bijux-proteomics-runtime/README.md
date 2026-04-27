# bijux-proteomics-runtime

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-runtime` is the canonical runtime package for execution control,
provider binding, deterministic replay, and operator-facing orchestration
surfaces in `bijux-proteomics`.

Use this package when you need the supported CLI, HTTP API, provider wiring,
runtime state handling, and replay-safe orchestration for canonical
`bijux-proteomics` execution.

## Why teams pick this package

- one canonical runtime surface for CLI, API, orchestration, and providers
- deterministic replay and artifact shaping for repeatable execution outcomes
- adapter-based composition that keeps lower layers runtime-agnostic
- explicit migration target for `agentic-proteins` compatibility forwarding

## Typical use cases

- run the canonical proteomics workflow through CLI or HTTP entrypoints
- bind local or API-backed structure providers behind one orchestration layer
- enforce replay-safe runtime execution without moving domain semantics upward
- integrate canonical runtime surfaces while legacy imports remain compat-only

## Installation

```bash
pip install bijux-proteomics-runtime
```

## Quick start

```bash
bijux-proteomics-runtime --help
```

Python integrations should start from the canonical runtime package:

```python
from bijux_proteomics_runtime import AppConfig, RunManager, create_app
```

## Package identity

- Distribution name: `bijux-proteomics-runtime`
- Import root: `bijux_proteomics_runtime`
- Canonical CLI command: `bijux-proteomics-runtime`
- Stable entrypoints: `AppConfig`, `RunManager`, `create_app`, and `interfaces.cli:cli`

## Package boundaries

This package owns runtime execution behavior and orchestration interfaces.

Domain meaning, evidence semantics, scoring policy, and lab planning semantics
remain in their dedicated lower-layer packages.

## Contract checkpoints

- runtime entrypoints must remain canonical while compat imports forward to them
- lower-layer meaning must stay below runtime adapters rather than being redefined here
- replay, artifact, and provider contracts must remain explicit and testable
- changes to canonical ownership should land in runtime before compat forwarding expands

## Choose this package when

- you need canonical CLI, API, provider binding, or replay-safe orchestration
- the change affects how canonical execution runs rather than what lower layers mean
- operator-facing entrypoints or runtime adapters need to evolve without pushing
  runtime ownership downward

## Route elsewhere when

- the change defines schema, lifecycle, evidence, ranking, or lab semantics
- the helper only exists to preserve historical imports instead of canonical
  runtime behavior
- the provider-specific rule would force lower packages to import runtime

## Verification route

- check `tests` for runtime surface, provider, replay, and migration proof
  before treating a runtime change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when canonical ownership or adapter law is part of the change
- use `docs/maintainer/pypi.md` when the change affects package publication,
  metadata, or release-readiness expectations

## Review questions

- does the change preserve canonical operator entrypoints, provider binding, or
  replay-safe orchestration rather than lower-layer domain semantics
- would compat or lower packages start carrying shadow execution transport or
  adapter law if this behavior stayed outside runtime
- can the change be justified as runtime-local work instead of a missing lower
  package contract or a compat-only bridge

## Escalation route

- route the change downward when the behavior actually defines schema,
  lifecycle, evidence, ranking, or lab semantics
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  proposal starts looking like compatibility glue or provider-specific policy
  rather than canonical runtime orchestration
- escalate before release when adopting the change would force lower packages or
  compat surfaces to mirror new runtime-local exceptions

## Consumer impact signals

- expect cross-surface review when CLI, API, provider binding, replay behavior,
  or migration expectations change because operators consume them directly
- treat changes that alter canonical entrypoints, runtime adapters, or compat
  expectations as high-impact even when import paths stay stable
- expect a narrower release burden when the change only improves internal
  orchestration without changing runtime-facing behavior

## Explicit non-goals

- this package does not redefine schema, lifecycle, evidence, ranking, or lab
  semantics owned by lower layers
- this package does not serve as a dumping ground for compat-only exceptions or
  migration shims
- this package does not decide scientific truth, only how canonical execution
  runs over lower-layer contracts

## Source guide

- [`src/bijux_proteomics_runtime/runtime/control`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/runtime/control) for orchestration, replay, and execution helpers
- [`src/bijux_proteomics_runtime/interfaces`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/interfaces) for CLI contracts
- [`src/bijux_proteomics_runtime/api`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/api) for HTTP entrypoints
- [`src/bijux_proteomics_runtime/providers`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/providers) for provider binding
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime/tests) for executable surface and migration expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operations/release-and-versioning/)
