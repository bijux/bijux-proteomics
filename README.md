# bijux-proteomics

`bijux-proteomics` is a bounded proteomics product for benchmark-backed
execution, scientific review, recommendation posture, and lab consequence.

Six real product packages own that chain. `agentic-proteins` stays as a legacy
compatibility install surface for historical runtime entrypoints and imports,
while `bijux-proteomics-dev` owns repository-health automation. Short install
aliases now reserve `bijux-proteomics`, `proteomics`, and the family-scoped
`proteomics-*` package names without creating second owner surfaces.

## Product Scope

This repository is strongest when a reviewer needs to inspect one bounded
evidence chain from benchmark asset intake through execution, scientific
review, recommendation, and possible lab follow-up without guessing who owns
each handoff.

The product shape is explicit:

- shared contracts, identifiers, and deterministic serialization in
  [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- package roles, allowed imports, and owned artifact handoffs in
  [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- repository-level release pressure in
  [Release readiness matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/)

## 0.3.8 Release Snapshot

- `foundation` now carries the durable shared kernel for canonical
  serialization, identifiers, compatibility checks, and package-wide helper
  primitives used by release gates.
- `core` now publishes reader-facing scientific surfaces for FASTA intake,
  digestion, chemistry, identification, spectra, mzML, search adapters,
  protein inference, label-free quantification, PTM analysis, QC, and workflow
  planning.
- `runtime` is now the canonical execution package for reviewable sequence and
  import paths, deterministic replay, advanced DIA-NN workflow planning,
  archive bundles, and machine-readable rerun contracts.
- `knowledge`, `intelligence`, and `lab` now expose the cited-memory,
  analytical-judgment, and assay-follow-up surfaces needed to keep downstream
  consequence claims explicit instead of implied.
- package README examples and package changelogs now track the shipped public
  surfaces instead of lagging behind the code line.

## Current Credible Workflow Families

Outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.

Review-grade-bounded workflow families today: `lfq`.

Internal-support-only workflow families today: `multiplex`.

Hard evidence starts with these checked surfaces:

- [Flagship release candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
- [What one workflow family supports today](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today/)
- [Public artifact index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/)
- [Independent rerun dossiers](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/independent-rerun-dossiers/)
- [External review kits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/external-review-kits/)

## Forbidden Claims

This repository does not yet claim:

- broad proteomics workflow coverage beyond the checked workflow families above
- release-ready, reference-grade, elite, or product-grade status
- stronger wet-lab confidence than the current evidence chain can justify

The live repository limits are tracked in
[Current capability limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/),
and the current hostile-review blockers are tracked in
[Release readiness matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/).

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-15%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-15-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

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

## Reader Paths

- Scientist: start with
  [What one workflow family supports today](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today/)
  and then open the
  [Flagship release candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/).
- Operator: start with the
  [Runtime package handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  and then the
  [Runtime migration validation runbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/runtime-migration-validation/).
- Maintainer: start with
  [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
  and then the
  [Release readiness matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/).

## Package Map

The canonical publishable surface is `6` real product packages:

| Package | Role | Links |
| --- | --- | --- |
| `bijux-proteomics-foundation` | Shared contracts, identifiers, and deterministic serialization | <a href="https://pypi.org/project/bijux-proteomics-foundation/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-foundation"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `bijux-proteomics-core` | Benchmark assets, durable scientific contracts, and workflow requests | <a href="https://pypi.org/project/bijux-proteomics-core/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `bijux-proteomics-runtime` | Execution, provider binding, deterministic replay, and operator entrypoints | <a href="https://pypi.org/project/bijux-proteomics-runtime/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `bijux-proteomics-knowledge` | Scientific memory, provenance, contradiction handling, and review state | <a href="https://pypi.org/project/bijux-proteomics-knowledge/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-knowledge"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `bijux-proteomics-intelligence` | Recommendation posture, ranking sensitivity, and refusal behavior | <a href="https://pypi.org/project/bijux-proteomics-intelligence/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-intelligence"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `bijux-proteomics-lab` | Assay consequence planning, readiness, and observed outcomes | <a href="https://pypi.org/project/bijux-proteomics-lab/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-lab"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |

Repository-owned developer tooling also lives here in
[`packages/bijux-proteomics-dev`](packages/bijux-proteomics-dev), but it is for
maintaining the workspace rather than for end-user installation.

## Install Aliases

The repository also publishes `8` install aliases and `1` compatibility install
surface so the canonical packages can be discovered under shorter,
reserve-worthy, or migration-safe package names. Those installs forward into
the same owner packages above, so the badge catalog stays focused on canonical
package owners rather than duplicating the same runtime under multiple names.

| Install surface | Resolves to | Reference docs | Purpose |
| --- | --- | --- | --- |
| `agentic-proteins` | `bijux-proteomics-runtime` plus legacy compatibility submodules | [Compatibility handbook](https://bijux.io/bijux-proteomics/02-agentic-proteins/) | preserve the historical runtime CLI and import tree while new work defaults to canonical runtime ownership |
| `bijux-proteomics` | `bijux-proteomics-core` | [Core handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) | reserve the top-level project name as an install and command surface |
| `proteomics` | `bijux-proteomics-core` | [Core handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) | short install, import, and CLI alias for the core package |
| `proteomics-core` | `bijux-proteomics-core` | [Core handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) | short family-specific alias for the core package |
| `proteomics-foundation` | `bijux-proteomics-foundation` | [Foundation handbook](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/) | short alias for the shared foundation package |
| `proteomics-runtime` | `bijux-proteomics-runtime` | [Runtime handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) | short alias for the execution package and runtime CLI |
| `proteomics-intelligence` | `bijux-proteomics-intelligence` | [Intelligence handbook](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) | short alias for recommendation and review logic |
| `proteomics-knowledge` | `bijux-proteomics-knowledge` | [Knowledge handbook](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/) | short alias for evidence memory and contradiction handling |
| `proteomics-lab` | `bijux-proteomics-lab` | [Lab handbook](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/) | short alias for assay follow-up planning |

## Common Commands

- `make help` to list repository automation targets
- `make api` to validate all OpenAPI contracts in `apis/*/v1`
- `make api-freeze` to enforce frozen OpenAPI payloads and schema digests
- `make openapi-drift` to catch breaking schema changes without version bumps
- `make quality-artifact-governance` to enforce artifact roots, drift audit, and
  package-root hygiene
- `make quality-architecture-regression` to re-check import collection, public
  API snapshots, package tree, architecture map, workflow output snapshots, and
  the shipped demo CLI path after architecture-facing changes
- `make quality-runtime-boundaries` to re-check runtime ownership boundaries,
  the `agentic-proteins` forwarding contract, and runtime type-collision rules
- `make release-preflight` to run the exact-order hostile-review release gate
- `make quality` to run type, quality, docs, and MkDocs strict checks
- `make security` to run static security and vulnerability gates
- `make test` to execute the fast unit-focused test matrix
- `make test-slow` to run slow, benchmark, and external-data suites
- `make ensure-venv` to sync the shared root check environment
- `make nlenv` to print the root environment activation command
- `make manage_examples` to refresh governed repository example assets
- `make manage_models` to refresh governed repository model metadata
- `uv sync --group test` to build the reproducible repository test environment

## Repository Extension Contract

Proteomics owns a few root-level extensions that are real repository surfaces,
not silent drift from the other `bijux-g3` repos.

- root `interrogate` and `bandit` settings stay here because this repository
  owns checked maintainer tooling, docs policy, API governance, and release
  automation in `bijux-proteomics-dev`
- root optional dependency groups `api`, `local-esmfold`,
  `local-rosettafold`, `nl`, and `test` stay here because runtime and
  maintainer tools need explicit provider, model, language-stack, and
  reproducible test extras that sibling repos do not own; the local folding
  groups intentionally stop short of vendoring `torch` until PyTorch ships a
  patched release for the current JIT advisory
- `api-freeze` and `openapi-drift` are repository-level API governance gates
  because Proteomics checks in versioned OpenAPI contracts and refuses
  unreviewed schema drift
- `ensure-venv` and `nlenv` are root environment helpers for the shared check
  environment, while `manage_examples` and `manage_models` are repository-owned
  maintenance commands for governed examples and model metadata

## Local Artifact Contract

- transient local outputs belong under `artifacts/`, not as durable root-level
  cache directories
- `make quality-artifact-governance` is the fastest root check when you want to
  catch cache spillover, package-local artifact drift, or wrong storage
  locations before broader verification
- the shared root environment lives at `artifacts/root/check-venv/`
- the MkDocs site builds to `artifacts/root/docs/site/`
- package roots must stay free of local `artifacts/`, `.venv`, `.hypothesis`,
  and `.benchmarks` spillover; repository automation cleans those paths and
  rebuilds the canonical artifact tree under `artifacts/`
- publishable package roots must stay free of `.pytest_cache`, `.ruff_cache`,
  `__pycache__`, and comparable transient spillover

## Release Model

- publishing is tag-driven: pushing `vX.Y.Z` triggers the release workflow split
- each publishable package owns its release notes in `packages/<package>/CHANGELOG.md`
- root `CHANGELOG.md` is only for repository-wide changes that span packages or shared automation
- `release-artifacts.yml` builds each package artifact bundle, then calls `release-pypi.yml`, `release-ghcr.yml`, and `release-github.yml`
- `release-ghcr.yml` publishes one GHCR bundle per package and `release-github.yml` assembles the GitHub Release from staged assets
- `release-pypi.yml` uses PyPI trusted publishing with the GitHub Actions OIDC token
- coordinated release language must keep `bijux-proteomics-runtime` as canonical and `agentic-proteins` as compatibility, while treating `bijux-proteomics` and `proteomics*` names as install aliases rather than second owners

Recommended release order:

1. Update package `README.md`, `pyproject.toml`, and package `CHANGELOG.md`.
2. Run `make lint test quality security`.
3. Run `make quality-runtime-migration-validation`.
4. Run `make release-preflight`.
5. Push the release tag (`vX.Y.Z`) and verify the release workflow split completes.

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

## License

This repository is licensed under the Apache License 2.0. Copyright 2026 Bijan Mousavi <bijan@bijux.io>. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
