# Changelog

All notable changes to `bijux-proteomics-dev` are documented in this file.

The format follows Keep a Changelog and this package follows Semantic
Versioning.

## [Unreleased]

## [0.3.8] - 2026-07-01

### Added

- Added runtime boundary automation that enforces lower-layer import direction, compat forwarding policy for `agentic-proteins`, and runtime type ownership collision checks.
- Added runtime migration ledger generation and coverage enforcement for full `agentic-proteins` module classification with owner and reason fields.
- Added repository quality and governance gates for architecture regression,
  canonical package tree layout, orphan-module audits, generated-file markers,
  core dependency minimization, circular-import scope, public-API typecheck,
  scientific-concept ownership, cross-package smoke boundaries, and repo-wide
  pytest collection.
- Added executable package README API examples, reproducible test dependency
  surfaces, and documented fast and slow test lanes.
- Added artifact-root and package-hygiene enforcement so disposable caches,
  reports, and benchmark byproducts stay under repository-owned `artifacts/`
  paths instead of hardening into package roots.

### Changed

- Repository quality flow now includes a dedicated
  `make quality-runtime-boundaries` gate.
- Quality flow now routes package docs, public API smoke, release checkpoints,
  and runtime handoff validation through explicit repository-owned maintainer
  gates.
- Documentation and release governance now track numbered handbook owners,
  shared MkDocs baseline separation, scoped external review-kit authority, and
  narrower LFQ public authority wording.
- Aligned the dependency floor and fallback version with the `0.3.8` release
  line.

### Fixed

- Hardened governance subprocess execution, bytecode cleanup, package
  ownership inventories, security dependency floors, and safe-msgpack
  auditing.
- Stopped package-root artifact aliasing, tolerated disappearing cache
  directories during hygiene checks, and aligned repository artifact contracts
  with disposable local worktree behavior.

## [0.3.7] - 2026-04-21

### Changed

- Updated package README links to readable markdown hyperlink text and aligned maintainer navigation references with canonical proteomics docs routes.

### Fixed

- Tag-push policy checks now handle non-commit `before` SHAs in workflow governance validation.

## [0.3.6] - 2026-04-20

### Changed

- Prepared the `v0.3.6` release line by aligning fallback versions and inter-package dependency floors across the repository.
- Synchronized release automation and governance with the `bijux-std v0.1.3` shared standards baseline.

### Fixed

- `release-pypi.yml` now uses parse-safe publication gating for token/bootstrap checks.
- Protected workflow policy checks now accept shared-manifest-driven standards updates through approved control paths.

## [0.3.5] - 2026-04-19

### Changed

- Repository workflow contract tests now validate the canon-aligned workflow
  tree (`automerge-pr.yml`, `ci.yml`, split release workflows) and reject
  legacy workflow references.
- Badge synchronization now follows the same catalog contract shape as
  `bijux-canon`, including repository and public-package generated surfaces.
- Documentation governance helpers now resolve repository handbook contracts
  from numbered docs roots (for example `docs/01-bijux-proteomics/...`) rather
  than legacy flat handbook paths.
- Docs publication and navigation contract tests now validate numbered site
  paths across repository, package, and maintainer sections.
- Package metadata documentation links now point to the numbered maintainer
  route `08-bijux-proteomics-maintain/bijux-proteomics-dev/`.

### Fixed

- Maintainer handbook navigation and release documentation contracts now resolve
  `gh-workflows/release-workflows` routes and split release workflow names.

## [0.3.4] - 2026-04-11

### Fixed

- Maintainer package dependency floor now requires `agentic-proteins>=0.3.4`
  for synchronized release checks.

## [0.3.3] - 2026-04-10

### Fixed

- Maintainer package dependency floor now requires `agentic-proteins>=0.3.3`
  for synchronized release checks.

## [0.3.2] - 2026-04-10

### Fixed

- Maintainer package dependency floor now requires `agentic-proteins>=0.3.2`
  for synchronized release checks.
- Release workflow contract tests now follow the enforced Ruff formatting
  baseline.

## [0.3.1] - 2026-04-06

### Added

- Package family PyPI and docs badges were added to package README for
  cross-package discoverability.

### Changed

- README content was rewritten with clearer maintainer workflow orientation and
  gate ownership guidance.
- Package description text was enhanced for clearer PyPI package discovery.

## [0.3.0] - 2026-04-06

### Added

- Created the `bijux-proteomics-dev` package as the repository-owned home for
  quality, security, API, release, docs, and maintainer tooling.
