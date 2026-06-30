# proteomics-runtime

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/proteomics-runtime/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![proteomics-runtime](https://img.shields.io/pypi/v/proteomics-runtime?label=proteomics--runtime&logo=pypi)](https://pypi.org/project/proteomics-runtime/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![proteomics-runtime](https://img.shields.io/badge/proteomics--runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fproteomics-runtime)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![proteomics-runtime docs](https://img.shields.io/badge/docs-proteomics--runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`proteomics-runtime` is the compatibility alias for the canonical runtime owner
`bijux-proteomics-runtime`.
It is the install and import alias for bijux-proteomics-runtime.

Use this package when you want a shorter runtime distribution and import name
without creating a second execution owner.

## Installation

```bash
pip install proteomics-runtime
```

## Public APIs

The alias forwards the canonical runtime execution surface through
`proteomics_runtime`:

```python
from pathlib import Path

from proteomics_runtime import AppConfig, create_app

base_dir = Path("artifacts/readme-runtime-alias-app")
app = create_app(AppConfig(base_dir=base_dir, docs_enabled=False))

assert app.state.base_dir == base_dir
assert app.docs_url is None
```

## Package identity

- Distribution name: `proteomics-runtime`
- Import root: `proteomics_runtime`
- Canonical owner package: `bijux-proteomics-runtime`
- Canonical owner import root: `bijux_proteomics_runtime`

## Package boundaries

- this package owns compatibility naming for runtime installs, imports, and CLI
  routing
- execution planning, providers, state, and workflow delivery remain owned by
  `bijux-proteomics-runtime`
- new runtime behavior must land in the canonical owner before alias exports
  change

## What this package must not do

- define a second runtime execution owner
- fork provider, run-manager, or API behavior from the canonical runtime
- become an independent migration target for runtime semantics

## Contract checkpoints

- alias exports must keep forwarding to canonical runtime behavior
- docs must keep the canonical runtime owner explicit
- compatibility changes must stay covered by alias-package tests

## Choose this package when

- you need a shorter import and distribution name for runtime entrypoints
- migration constraints prefer `proteomics_runtime`
- packaging or compatibility work needs a short runtime alias

## Route elsewhere when

- the change alters execution planning, providers, workflow delivery, or API
  semantics
- the work introduces runtime behavior that is not already owned by the
  canonical package
- the alias would stop being forwarding-only

## Verification route

- run alias compatibility tests before changing runtime imports or metadata
- review `docs/ARCHITECTURE.md`, `docs/BOUNDARIES.md`, and `docs/CONTRACTS.md`
  when alias routing or claims change
- validate the canonical runtime README and tests when behavior changes are
  proposed

## Review questions

- does the change preserve this package as a runtime alias only
- is the canonical runtime owner still explicit in docs and behavior
- would the same outcome remain correct if consumers imported the canonical
  runtime directly

## Escalation route

- route runtime behavior changes to `bijux-proteomics-runtime`
- stop and review boundaries when the alias starts gaining package-local
  execution semantics
- escalate before release when routing or metadata drift could confuse runtime
  ownership

## Consumer impact signals

- import-path, command-name, or package-name changes are high-impact because
  runtime automation may depend on them directly
- alias documentation changes should still be reviewed against the canonical
  runtime owner
- wording-only clarifications carry lower release risk than routing or behavior
  changes

## Explicit non-goals

- this package does not own scientific workflow semantics
- this package does not define a second provider or execution policy layer
- this package does not replace the canonical runtime release surface

## Documentation

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Canonical runtime package docs](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
- [Changelog](CHANGELOG.md)
