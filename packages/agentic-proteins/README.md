# agentic-proteins

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/workflows/repo%20/%20verify/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`agentic-proteins` is a strict compatibility package.

Canonical runtime ownership is `bijux-proteomics-runtime`.

This package keeps legacy import and CLI entrypoints available while forwarding
all implementation surfaces to canonical packages.

## Compatibility contract

- forwards runtime surfaces to `bijux-proteomics-runtime`
- forwards domain surfaces to canonical lower-layer packages
- contains no canonical runtime or domain implementation
- exists to preserve migration safety for existing integrations

## Installation

```bash
pip install agentic-proteins
```

## Quick start

```bash
agentic-proteins --help
```

Prefer canonical imports for new integrations:

```python
from bijux_proteomics_runtime.interfaces.cli import cli
```

Legacy imports continue to work via forwarding:

```python
from agentic_proteins.interfaces.cli import cli
```

## Package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Legacy CLI command: `agentic-proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## Package boundaries

- this package owns compatibility routing only
- canonical runtime behavior belongs in `bijux-proteomics-runtime`
- canonical domain behavior belongs in the lower `bijux-proteomics-*` packages
- new features should land in canonical packages before compat forwarding expands

## Contract checkpoints

- legacy imports must forward without redefining canonical behavior
- compat docs must name the canonical owner for the surface they describe
- compat modules must stay forwarding-only unless migration policy explicitly says otherwise
- new integrations should start from canonical packages even while compat remains available

## Choose this package when

- you must preserve legacy imports or CLI entrypoints during migration
- the change is forwarding-only and names a canonical owner clearly
- integration continuity matters more than adding fresh behavior

## Route elsewhere when

- the change defines runtime orchestration, provider behavior, or domain
  semantics
- the helper mainly serves new integrations rather than compatibility
- the module would stop being forwarding-only

## Verification route

- check compat `tests` for forwarding and migration proof before treating a new
  legacy surface as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when a change claims to remain forwarding-only
- use `docs/maintainer/pypi.md` when the change affects package publication,
  metadata, or release-readiness expectations

## Review questions

- does the change preserve legacy continuity for a surface that already has a
  clear canonical owner
- would the implementation still live entirely in canonical packages if the
  compat layer disappeared
- can the change be justified as forwarding-only without adding fresh runtime or
  domain behavior

## Escalation route

- route the change to the canonical owner when the proposal introduces any new
  runtime orchestration or domain semantics
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  compat layer would need behavior beyond import forwarding or stable aliases
- escalate before release when adopting the change would require documenting
  compat-only exceptions instead of the canonical package surface

## Consumer impact signals

- expect review against the canonical owner when compat exports or forwarding
  targets change because consumers rely on stable migration continuity
- treat changes that alter forwarding behavior or canonical mapping as
  high-impact even when public import names stay stable
- expect a lower release burden when the change only tightens documentation or
  internal compat wiring without changing forwarding behavior

## Explicit non-goals

- this package does not own canonical runtime orchestration or lower-package
  domain semantics
- this package does not add fresh product behavior for new integrations
- this package does not replace repository governance or release policy owned by
  the maintainer package

## Documentation

- [Canonical runtime package docs](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
- [Compatibility package docs](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
