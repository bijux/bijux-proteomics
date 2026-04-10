# bijux-proteomics

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/publish.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/publish.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR bundles](https://img.shields.io/badge/ghcr-06%20bundles-181717?logo=github)](https://github.com/orgs/bijux/packages?repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-06-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

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

`bijux-proteomics` is a contract-first Python package family for governed
protein discovery workflows across runtime execution, domain contracts,
decision intelligence, evidence governance, and lab planning.

The goal is not just to run a protein pipeline once. The goal is to keep
behavior reviewable and reproducible as the system evolves.

This repository publishes `06` packages. Each release tag builds one staged
bundle per package, uploads distributions to PyPI, publishes release bundles to
`ghcr.io/bijux/bijux-proteomics/<package>`, and attaches the same staged assets
to the GitHub Release.

## Why `bijux-proteomics` Exists

Protein programs become difficult to trust when execution logic, domain models,
evidence reasoning, policy decisions, and lab planning are merged into one
surface.

`bijux-proteomics` keeps those concerns explicit and separable:

- deterministic runtime behavior in `agentic-proteins`
- shared primitives in `bijux-proteomics-foundation`
- domain contracts in `bijux-proteomics-core`
- ranking and policy decisions in `bijux-proteomics-intelligence`
- evidence and trust resolution in `bijux-proteomics-knowledge`
- lab orchestration boundaries in `bijux-proteomics-lab`

## Package Map

The `06` publishable packages in this repository are:

| Package | Role | Links |
| --- | --- | --- |
| `agentic-proteins` | Runtime execution surfaces (CLI and HTTP) plus deterministic run artifacts | [![PyPI](https://img.shields.io/pypi/v/agentic-proteins?label=PyPI&logo=pypi)](https://pypi.org/project/agentic-proteins/) [![Docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/agentic-proteins/) [`source`](packages/agentic-proteins) |
| `bijux-proteomics-foundation` | Shared contracts, identifiers, and canonical serialization primitives | [![PyPI](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=PyPI&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/) [![Docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/) [`source`](packages/bijux-proteomics-foundation) |
| `bijux-proteomics-core` | Program models, lifecycle transitions, and review-gate domain logic | [![PyPI](https://img.shields.io/pypi/v/bijux-proteomics-core?label=PyPI&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/) [![Docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-core/) [`source`](packages/bijux-proteomics-core) |
| `bijux-proteomics-intelligence` | Candidate evaluation, scoring policy, and recommendation logic | [![PyPI](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=PyPI&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/) [![Docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-intelligence/) [`source`](packages/bijux-proteomics-intelligence) |
| `bijux-proteomics-knowledge` | Evidence graphs, trust scoring, and conflict resolution policy | [![PyPI](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=PyPI&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/) [![Docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-knowledge/) [`source`](packages/bijux-proteomics-knowledge) |
| `bijux-proteomics-lab` | Lab planning, scheduling decisions, and outcome promotion workflows | [![PyPI](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=PyPI&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/) [![Docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/) [`source`](packages/bijux-proteomics-lab) |
| `bijux-proteomics-dev` | Repository maintenance tooling for quality, security, docs, release, and API gates | [![Docs](https://img.shields.io/badge/docs-maintainer-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/) [`source`](packages/bijux-proteomics-dev) |

## What This Repository Is Not

- not a single all-in-one package with hidden coupling
- not a promise of wet-lab correctness by documentation alone
- not a replacement for package-level tests and review gates

## Start Here

- Repository handbook: <https://bijux.io/bijux-proteomics/>
- API contract handbook: <https://bijux.io/bijux-proteomics/bijux-proteomics/operations/api-and-schema-governance/>
- Runtime package: <https://bijux.io/bijux-proteomics/agentic-proteins/>
- Domain core: <https://bijux.io/bijux-proteomics/bijux-proteomics-core/>
- Intelligence package: <https://bijux.io/bijux-proteomics/bijux-proteomics-intelligence/>
- Knowledge package: <https://bijux.io/bijux-proteomics/bijux-proteomics-knowledge/>
- Lab package: <https://bijux.io/bijux-proteomics/bijux-proteomics-lab/>
- Foundation primitives: <https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/>
- Maintainer tooling: <https://bijux.io/bijux-proteomics/bijux-proteomics-maintain/bijux-proteomics-dev/>

## Common Commands

- `make help` to list repository automation targets
- `make api` to validate all OpenAPI contracts in `apis/*/v1`
- `make quality` to run type, quality, docs, and MkDocs strict checks
- `make security` to run static security and vulnerability gates
- `make test` to execute the configured test matrix

## Release Model

- publishing is tag-driven: pushing `vX.Y.Z` triggers the shared `publish.yml` workflow
- each publishable package owns its release notes in `packages/<package>/CHANGELOG.md`
- root `CHANGELOG.md` is only for repository-wide changes that span packages or shared automation
- `publish.yml` builds and publishes each package through its matrix entries
- `publish.yml` also publishes one GHCR bundle per package and assembles a GitHub Release from the staged assets
- `publish.yml` uses PyPI trusted publishing with the GitHub Actions OIDC token

Recommended release order:

1. Update package `README.md`, `pyproject.toml`, and package `CHANGELOG.md`.
2. Run `make lint test quality security`.
3. Push the release tag (`vX.Y.Z`) and verify the shared `publish.yml` workflow completes.

## Repository Boundaries

The root keeps repository-owned concerns explicit:

- `apis/` for checked-in OpenAPI contracts, pinned JSON, and schema digests
- `configs/` for shared lint, typing, test, and coverage settings
- `docs/` for the repository handbook and package handbook index
- `makes/` for root and package gate orchestration
- `.github/workflows/` for CI, release, and docs deployment pipelines
- `packages/` for publishable package boundaries plus maintainer tooling

That split is intentional: package runtime code stays local to packages, and
repository governance stays visible and reviewable at the root.
