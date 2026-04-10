# Changelog

This file records notable repository-level changes for `bijux-proteomics`.

It does not replace package-level release history. Versioning and package-local
release notes belong to each distribution under `packages/`.

Use this changelog for workspace changes that affect multiple packages or
change contributor and maintainer workflows across the repository.

## 0.3.3 - 2026-04-10

### Changed

- Publishable package fallback versions and cross-package dependency floors now
  align with the synchronized `v0.3.3` proteomics release line.
- Packaging contract checks now treat `0.3.3` as the current public fallback
  version for tag-derived builds.

## 0.3.2 - 2026-04-10

### Fixed

- Internal package dependency floors now align with the synchronized `0.3.2`
  proteomics release line.
- Tox checks now delegate installation ownership to the repository make system,
  matching the release-gate execution model.
- Workspace lock metadata now reflects the current package extras and
  maintainer-tool dependencies used by release checks.
- Release workflow contract tests now follow the enforced Ruff formatting
  baseline.

## 0.3.1 - 2026-04-06

### Added

- Cross-package discoverability badges were added to package maintainer notes
  and package READMEs for PyPI and documentation navigation.

### Changed

- Package README content was rewritten across the workspace to improve package
  purpose clarity, boundaries, installation guidance, and quick-start usage.
- Package metadata descriptions were strengthened for clearer PyPI package
  discovery and search relevance.
- Publishable package version strategy now uses tag-driven dynamic versioning
  (`hatch-vcs`) across the workspace for release consistency on `v*` tags.

### Fixed

- Release workflow behavior now avoids static version drift between tagged
  releases and package metadata for multi-package publication.

## 0.3.0 - 2026-04-06

### Added

- Unified package documentation structure was applied across proteomics
  packages, including ownership boundaries, source maps, and maintainer notes.
- Package-level maintainer notes for PyPI workflows were added under each
  package `docs/maintainer/pypi.md`.

### Changed

- Repository workflow design now uses reusable package CI and release-artifact
  workflows with package-specific entry pipelines.
- Shared tool configuration moved to `configs/` and gate modules now resolve
  settings through centralized make configuration variables.
- Root README now describes repository governance and package boundaries with a
  durable package-map-first structure.

### Fixed

- Monorepo test-root resolution was stabilized for nested package manifests by
  improving shared test path detection in `agentic-proteins`.
- Quality gates now use a repository-owned deptry configuration path while
  preserving current dependency hygiene behavior.

## Changelog Scope

Use this file for changes such as:

- root governance and contributor policy
- shared automation under `makes/`
- shared configuration under `configs/`
- root handbook and repository navigation
- repository-level CI, publish, and release process changes
- shared API artifact conventions under `apis/`

Do not use this file for changes that only affect one package release stream
unless the repository-level workflow changed too.
