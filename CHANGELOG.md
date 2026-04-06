# Changelog

This file records notable repository-level changes for `bijux-proteomics`.

It does not replace package-level release history. Versioning and package-local
release notes belong to each distribution under `packages/`.

Use this changelog for workspace changes that affect multiple packages or
change contributor and maintainer workflows across the repository.

## 0.3.0 - 2026-04-06

### Added

- Canon-style package documentation structure was applied across proteomics
  packages, including ownership boundaries, source maps, and maintainer notes.
- Package-level maintainer notes for PyPI workflows were added under each
  package `docs/maintainer/pypi.md`.

### Changed

- Repository workflow design now uses reusable package CI and release-artifact
  workflows with package-specific entry pipelines.
- Shared tool configuration moved to `configs/` and gate modules now resolve
  settings through centralized make configuration variables.
- Root README now describes repository governance and package boundaries using
  the same durable structure used in `bijux-canon`.

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
