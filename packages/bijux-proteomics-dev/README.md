# bijux-proteomics-dev

`bijux-proteomics-dev` is the maintenance package for this monorepo. It owns
the Python helpers behind root quality gates, security checks, release
validation, OpenAPI drift checks, and repository automation.

This package is for maintainers, CI, and root `make` targets. It is not part
of the product runtime surface.

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

## What this package owns

- shared quality and security helpers used across packages
- release and version governance helpers
- OpenAPI and schema drift tooling
- repository maintenance helpers invoked by root automation

## What this package does not own

- runtime or product behavior used by end users
- domain models owned by foundation, core, intelligence, knowledge, or lab
- compatibility shims whose only job is preserving legacy package names

## Source map

- [`src/bijux_proteomics_dev/quality`](src/bijux_proteomics_dev/quality) for repository quality checks
- [`src/bijux_proteomics_dev/security`](src/bijux_proteomics_dev/security) for security gates
- [`src/bijux_proteomics_dev/api`](src/bijux_proteomics_dev/api) for OpenAPI and schema checks
- [`src/bijux_proteomics_dev/release`](src/bijux_proteomics_dev/release) for release support
- [`src/bijux_proteomics_dev/docs`](src/bijux_proteomics_dev/docs) for documentation checks
- [`src/bijux_proteomics_dev/tools`](src/bijux_proteomics_dev/tools) for maintainer utility tools

## Read this next

- [Package guide](docs/index.md)
- [Scope](docs/SCOPE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contracts](docs/CONTRACTS.md)
- [Tests](docs/TESTS.md)
- [Changelog](CHANGELOG.md)
