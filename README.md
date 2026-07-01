# bijux-proteomics

`bijux-proteomics` is a bounded proteomics product and repository for
benchmark-backed scientific workflows, reviewable execution, grounded
interpretation, explicit recommendation posture, and downstream lab
consequence.

This repository now carries real scientific depth across biology, chemistry,
execution, evidence grounding, analytical judgment, and assay follow-up. The
package split exists so those responsibilities stay inspectable, but the root
README should first explain the product clearly before a reader has to learn
the package tree.

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

## What This Repository Ships

- a benchmark-backed proteomics workflow stack rather than a governance-only
  shell
- canonical packages for shared contracts, scientific core behavior, runtime
  execution, evidence grounding, analytical interpretation, and lab
  consequence
- public docs that let a hostile reviewer follow one evidence chain from
  benchmark intake to downstream consequence
- release and verification automation that keeps scientific claims tied to
  explicit package owners and reproducible evidence

## What Is Real In 0.3.8

- `bijux-proteomics-foundation` now owns the durable kernel for identifiers,
  compatibility checks, canonical serialization, and shared outcomes.
- `bijux-proteomics-core` now carries a materially broader scientific surface:
  FASTA intake, digestion, chemistry, modifications, spectra, mzML,
  identification, protein inference, label-free quantification, PTM review,
  QC, benchmark assets, and workflow contracts.
- `bijux-proteomics-runtime` is now the canonical execution owner for replay,
  rerun kits, operator handoff, archive bundles, and runtime proof.
- `bijux-proteomics-knowledge`, `bijux-proteomics-intelligence`, and
  `bijux-proteomics-lab` now make grounding, recommendation posture, and assay
  consequence explicit instead of leaving them implied in core or runtime
  prose.
- the numbered documentation tree now gives those routes durable owners
  instead of scattering reader journeys across extra top-level buckets.

## Current Release Posture

Current credible workflow-family language:

| Status | Workflow families |
| --- | --- |
| Outsider-auditable today | `dda`, `dia`, `ptm`, `targeted` |
| Review-grade but bounded | `lfq` |
| Internal support only | `multiplex` |

This repository does not currently claim:

- broad proteomics workflow coverage beyond the families above
- release-ready, reference-grade, or stronger product language than the
  evidence chain supports
- stronger lab confidence than the current benchmark, runtime, grounding, and
  consequence route can justify

The live ceiling on public language is tracked in
[Current capability limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)
and the current blockers are tracked in the
[Release readiness matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/).

## Package Map

These six packages are the real product owners:

| Package | Owns | Docs |
| --- | --- | --- |
| `bijux-proteomics-foundation` | shared contracts, identifiers, canonical serialization, and compatibility primitives | [Foundation handbook](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/) |
| `bijux-proteomics-core` | benchmark assets, scientific workflow contracts, and the flagship public proteomics surface | [Core handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) |
| `bijux-proteomics-runtime` | execution, replay, rerun comparability, archive bundles, and operator entrypoints | [Runtime handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) |
| `bijux-proteomics-knowledge` | scientific memory, provenance, contradiction handling, and claim grounding | [Knowledge handbook](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/) |
| `bijux-proteomics-intelligence` | interpretation posture, recommendation challenge routes, and bounded judgment | [Intelligence handbook](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) |
| `bijux-proteomics-lab` | assay consequence planning, readiness, refusal routes, and observed follow-up outcomes | [Lab handbook](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/) |

Additional repository surfaces:

- `agentic-proteins` preserves the historical runtime compatibility route and
  forwards into canonical runtime ownership.
- `bijux-proteomics-dev` owns repository-health automation, docs governance,
  release checks, and maintainer tooling.
- `bijux-proteomics`, `proteomics`, and `proteomics-*` reserve shorter install
  names without creating second owner packages.

## Install Surfaces

Choose install names by ownership rather than by convenience:

- install `bijux-proteomics-core` when you want the main scientific surface
- install `bijux-proteomics-runtime` when you need canonical execution and
  rerun behavior
- install `agentic-proteins` only when a historical runtime compatibility
  route is still required
- treat `bijux-proteomics`, `proteomics`, and `proteomics-*` as alias
  distributions that resolve into the canonical owners above

The package directories under [`packages/`](packages) and their package
README files explain each install surface in detail.

## Start Here

Best first routes for most readers:

- [Product overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
  for the shortest honest description of the product and its current scope
- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
  for the end-to-end route from benchmark intake to lab consequence
- [Workflow families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  for the current publishable, bounded, and internal workflow-family split
- [Flagship release candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
  for the shortest hostile-review route through shipped evidence
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
  for package boundaries and handoff responsibility

Role-specific routes:

- Scientist:
  [Scientist journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/)
- Operator:
  [Operator rerun journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
- Maintainer:
  [Maintainer safe change](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change/)

## Maintainer Quick Start

- `make help` to list repository automation
- `make ensure-venv` to sync the shared root check environment
- `make test` for the fast unit-focused test matrix
- `make quality` for typing, quality, docs, and MkDocs strict checks
- `make security` for static security and vulnerability gates
- `make quality-artifact-governance` to catch wrong output locations and
  package-root spillover early
- `make quality-architecture-regression` after architecture-facing changes
- `make release-preflight` before cutting a release candidate

For package-local behavior, use the package README under [`packages/`](packages).
For maintainer operations, use the
[maintainer handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/).

## Repository Operating Model

This repository keeps product code, repository automation, and transient local
state separate on purpose:

- runtime code lives in package-owned trees under [`packages/`](packages)
- repository-owned automation lives under [`makes/`](makes),
  [`configs/`](configs), [`apis/`](apis), [`docs/`](docs), and
  [`.github/workflows/`](.github/workflows)
- transient local outputs belong under [`artifacts/`](artifacts), not as
  root-level cache directories or package-local spillover
- package `CHANGELOG.md` files own package release notes, while the root
  [`CHANGELOG.md`](CHANGELOG.md) is only for repository-wide changes
- publishing is tag-driven and fans out into GitHub Release, PyPI, GHCR, and
  docs deployment workflows

That split is intentional: scientific ownership stays visible at package
boundaries, and repository policy stays visible at the root rather than being
hidden inside product packages.

## License

This repository is licensed under the Apache License 2.0. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
