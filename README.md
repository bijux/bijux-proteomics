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

`bijux-proteomics` is a contract-first Python package family for governed
protein discovery workflows across runtime execution, domain contracts,
decision intelligence, evidence governance, and lab planning.

The goal is not just to run a protein pipeline once. The goal is to keep
behavior reviewable and reproducible as the system evolves.

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

| Package | Role | PyPI | Source |
| --- | --- | --- | --- |
| `agentic-proteins` | Runtime execution surfaces (CLI and HTTP) plus deterministic run artifacts | <https://pypi.org/project/agentic-proteins/> | [`packages/agentic-proteins`](packages/agentic-proteins) |
| `bijux-proteomics-foundation` | Shared contracts, identifiers, and canonical serialization primitives | <https://pypi.org/project/bijux-proteomics-foundation/> | [`packages/bijux-proteomics-foundation`](packages/bijux-proteomics-foundation) |
| `bijux-proteomics-core` | Program models, lifecycle transitions, and review-gate domain logic | <https://pypi.org/project/bijux-proteomics-core/> | [`packages/bijux-proteomics-core`](packages/bijux-proteomics-core) |
| `bijux-proteomics-intelligence` | Candidate evaluation, scoring policy, and recommendation logic | <https://pypi.org/project/bijux-proteomics-intelligence/> | [`packages/bijux-proteomics-intelligence`](packages/bijux-proteomics-intelligence) |
| `bijux-proteomics-knowledge` | Evidence graphs, trust scoring, and conflict resolution policy | <https://pypi.org/project/bijux-proteomics-knowledge/> | [`packages/bijux-proteomics-knowledge`](packages/bijux-proteomics-knowledge) |
| `bijux-proteomics-lab` | Lab planning, scheduling decisions, and outcome promotion workflows | <https://pypi.org/project/bijux-proteomics-lab/> | [`packages/bijux-proteomics-lab`](packages/bijux-proteomics-lab) |
| `bijux-proteomics-dev` | Repository maintenance tooling for quality, security, docs, release, and API gates | not published on PyPI (maintainer package) | [`packages/bijux-proteomics-dev`](packages/bijux-proteomics-dev) |

## What This Repository Is Not

- not a single all-in-one package with hidden coupling
- not a promise of wet-lab correctness by documentation alone
- not a replacement for package-level tests and review gates

## Start Here

- Repository handbook: [`docs/index.md`](docs/index.md)
- API contract handbook: [`docs/bijux-proteomics/apis.md`](docs/bijux-proteomics/apis.md)
- Runtime package: [`packages/agentic-proteins/README.md`](packages/agentic-proteins/README.md)
- Domain core: [`packages/bijux-proteomics-core/README.md`](packages/bijux-proteomics-core/README.md)
- Intelligence package: [`packages/bijux-proteomics-intelligence/README.md`](packages/bijux-proteomics-intelligence/README.md)
- Knowledge package: [`packages/bijux-proteomics-knowledge/README.md`](packages/bijux-proteomics-knowledge/README.md)
- Lab package: [`packages/bijux-proteomics-lab/README.md`](packages/bijux-proteomics-lab/README.md)
- Foundation primitives: [`packages/bijux-proteomics-foundation/README.md`](packages/bijux-proteomics-foundation/README.md)
- Maintainer tooling: [`packages/bijux-proteomics-dev/README.md`](packages/bijux-proteomics-dev/README.md)

## Common Commands

- `make help` to list repository automation targets
- `make api` to validate all OpenAPI contracts in `apis/*/v1`
- `make quality` to run type, quality, docs, and MkDocs strict checks
- `make security` to run static security and vulnerability gates
- `make test` to execute the configured test matrix

## Release Model

- publishing is tag-driven: pushing `vX.Y.Z` triggers package publish workflows
- each publishable package owns its release notes in `packages/<package>/CHANGELOG.md`
- root `CHANGELOG.md` is only for repository-wide changes that span packages or shared automation
- trusted publishing is used in package publish workflows; no manual PyPI token step is required in the workflow definition

Recommended release order:

1. Update package `README.md`, `pyproject.toml`, and package `CHANGELOG.md`.
2. Run `make lint test quality security`.
3. Push the release tag (`vX.Y.Z`) and verify package publish workflows complete.

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
