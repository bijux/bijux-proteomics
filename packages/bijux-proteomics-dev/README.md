# bijux-proteomics-dev

`bijux-proteomics-dev` is the maintenance toolkit for this monorepo. It
provides Python helpers for root quality gates, security checks, release
validation, OpenAPI drift detection, and repository automation.

Use this package for CI and maintainer workflows that enforce repository
standards; it is intentionally separate from product runtime behavior.

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

## Why teams pick this package

- one toolkit for quality, security, release, docs, and API governance gates
- consistent local and CI behavior through shared maintainership utilities
- lower operational overhead by centralizing repetitive repo automation logic
- explicit checks that reduce release risk and configuration drift

## Typical use cases

- run and extend root quality and security gates used by all packages
- validate release readiness and metadata consistency before tagging
- detect OpenAPI and schema drift before publication
- automate maintainership checks for docs and repository health

## Installation

```bash
pip install -e packages/bijux-proteomics-dev
```

## Quick start

Use root `make` and `tox` commands that call this package under the hood:

```bash
make lint
make test
make quality
make security
```

## Package boundaries

This package owns maintainer automation and gate implementations for the monorepo.

It does not define runtime product APIs or proteomics domain behavior.

## Source guide

- [`src/bijux_proteomics_dev/quality`](src/bijux_proteomics_dev/quality) for repository quality checks
- [`src/bijux_proteomics_dev/security`](src/bijux_proteomics_dev/security) for security gates
- [`src/bijux_proteomics_dev/api`](src/bijux_proteomics_dev/api) for OpenAPI and schema checks
- [`src/bijux_proteomics_dev/release`](src/bijux_proteomics_dev/release) for release support
- [`src/bijux_proteomics_dev/docs`](src/bijux_proteomics_dev/docs) for documentation checks
- [`src/bijux_proteomics_dev/tools`](src/bijux_proteomics_dev/tools) for maintainer utility tools

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/)
- [Scope and non-goals](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/scope-and-non-goals/)
- [Module map](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/module-map/)
- [Quality gates](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/quality-gates/)
- [Release support](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/release-support/)
- [Changelog](CHANGELOG.md)
