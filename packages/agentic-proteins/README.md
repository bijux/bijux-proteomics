# agentic-proteins

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
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

`agentic-proteins` is a legacy compatibility bridge for runtime entrypoints and imports.

Canonical runtime ownership is `bijux-proteomics-runtime`.

This package owns one thing: legacy compatibility routing for historical CLI,
HTTP, agent, execution, provider, state, and tool entrypoints while all real
behavior stays in canonical packages.

## At a glance

- Use `agentic-proteins` only when an existing integration still depends on
  the legacy command, import root, or bridge submodule tree.
- Start new execution work from the
  [canonical runtime package docs](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  and treat this package as a migration bridge, not as a second runtime owner.
- Route runtime behavior to `bijux-proteomics-runtime`, lower scientific
  behavior to the canonical `bijux-proteomics-*` packages, and keep this layer
  forwarding-only.

## Compatibility routing

```mermaid
flowchart LR
    caller["existing agentic-proteins caller"]
    bridge["forwarding import or command"]
    runtime["bijux-proteomics-runtime"]
    owners["canonical scientific packages"]

    caller --> bridge --> runtime
    bridge --> owners
    new["new integration"] --> runtime
```

The bridge preserves call compatibility, not independent behavior. A forwarded
symbol must resolve to its canonical owner, and any new implementation belongs
in that owner before a compatibility export is considered.

## Removal is a consumer claim

The bridge can disappear only when supported callers no longer depend on its
observable contracts. Repository search establishes local absence; it cannot
establish that a deployed service, notebook collection, or automation system
has migrated.

| Evidence | What it establishes | What remains unknown |
| --- | --- | --- |
| forwarding test | the legacy path reaches the declared owner | whether a caller depends on different defaults or side effects |
| repository import scan | checked-in source no longer imports the path | external and generated consumers |
| CLI or HTTP parity test | selected observable behavior agrees | persistence and replay compatibility outside the fixture |
| caller acceptance record | one named consumer accepts the canonical contract | readiness of every other supported consumer |
| complete consumer inventory | the retirement decision covers the declared support set | undeclared consumers outside that support boundary |

Until the inventory and caller evidence close, the honest disposition is
`migrated for this caller` or `blocked`, not `bridge removable`.

## Compatibility contract

- mirrors the canonical runtime root exports at `agentic_proteins`
- forwards surviving bridge families to `bijux-proteomics-runtime`
- forwards structure-report and lower scientific surfaces to canonical packages
- keeps the historical submodule tree explicit so legacy imports stay
  inspectable
- exists to preserve migration safety for existing integrations

## Installation

```bash
pip install agentic-proteins
```

## Quick start

For new workflow execution, start from the canonical runtime CLI:

```bash
bijux-proteomics-runtime --help
```

Use the compatibility CLI only when an existing integration still depends on
the legacy command:

```bash
agentic-proteins --help
```

Prefer canonical imports for new integrations:

```python
from bijux_proteomics_runtime.api.cli import cli
```

Legacy imports continue to work via forwarding:

```python
from agentic_proteins import cli
from agentic_proteins.interfaces.cli import cli
```

## Public APIs

New integrations should prefer canonical runtime imports, but the compatibility
surface remains executable:

```python
from agentic_proteins import cli as legacy_cli
from bijux_proteomics_runtime import cli as canonical_cli

assert legacy_cli is canonical_cli
```

## Package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Legacy compatibility CLI command: `agentic-proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## Package boundaries

- this package owns compatibility routing only
- the root import `agentic_proteins` mirrors canonical runtime root exports
- this package keeps the durable bridge tree under `interfaces/`, `agents/`,
  `orchestration/`, `providers/`, `state/`, and `tools/`
- historical `execution/`, `agents/execution/`, and
  `providers/experimental/` paths remain only as legacy aliases
- canonical runtime behavior belongs in `bijux-proteomics-runtime`
- canonical domain behavior belongs in the lower `bijux-proteomics-*` packages
- new features should land in canonical packages before compat forwarding expands

## What this package must not do

- introduce package-local runtime semantics
- fork canonical provider or workflow behavior
- become a second owner for scientific or execution logic

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
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

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

- [Product overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Execution overview](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
- [Canonical runtime package docs](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
- [Compatibility package docs](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
- [Changelog](CHANGELOG.md)
