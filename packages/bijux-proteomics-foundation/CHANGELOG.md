# Changelog

All notable changes for `bijux-proteomics-foundation` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added versioned document, identifier, serialization, hashing, refusal,
  result, and compatibility primitives as the shared kernel for persisted
  proteomics records.
- Added shared package-alias helpers, explicit root public-API contracts,
  optional dependency guards, shared test marker and skip-policy helpers,
  governed generated-file markers, and public type, docstring, line-count, and
  complexity support utilities used by downstream packages and maintainer
  gates.

### Changed

- Reorganized the package around durable `compatibility`, `identity`,
  `outcomes`, `serialization`, and `support` owner families and narrowed the
  root exports to curated shared primitives plus explicit migration helpers.
- Expanded executable README examples and package docs for canonical JSON,
  hashing, compatibility checks, and stable testing helpers.
- Aligned the fallback version with the `0.3.8` release line.

### Fixed

- Restored strict lint and typing coverage for optional dependency helpers,
  hypothesis-aware testing helpers, and other shared support surfaces that
  downstream packages rely on during verification.

## 0.3.7 - 2026-04-21

### Changed

- Updated package README links to readable markdown hyperlink text and aligned handbook navigation references with canonical proteomics docs routes.

## 0.3.6 - 2026-04-20

### Changed

- Prepared the `v0.3.6` release line by aligning fallback versions and inter-package dependency floors across the repository.
- Synchronized release automation and governance with the `bijux-std v0.1.3` shared standards baseline.

### Fixed

- `release-pypi.yml` now uses parse-safe publication gating for token/bootstrap checks.
- Protected workflow policy checks now accept shared-manifest-driven standards updates through approved control paths.

## 0.3.5 - 2026-04-19

### Changed

- Maintainer release documentation now references the split repository release
  workflows (`release-artifacts.yml`, `release-pypi.yml`, `release-ghcr.yml`,
  `release-github.yml`) instead of legacy publish workflow names.
- README docs badges and package metadata documentation links now point to the
  numbered handbook route `03-bijux-proteomics-foundation` for stable docs
  navigation.

## 0.3.4 - 2026-04-11

### Changed

- Release history now records the synchronized `v0.3.4` proteomics publication
  line used by dependent packages.

## 0.3.3 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.3.3` proteomics publication
  line used by dependent packages.

## 0.3.2 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.3.2` proteomics publication
  line used by dependent packages.

## 0.3.1 - 2026-04-06

### Added

- Package family PyPI and docs badges were added to README and maintainer
  package notes for cross-package discoverability.

### Changed

- Versioning now uses tag-driven dynamic release metadata via `hatch-vcs`
  instead of static package version pinning.
- README content was rewritten to provide stronger package purpose, usage
  scenarios, and integration guidance.
- Package description text was enhanced for clearer PyPI package discovery.

## 0.3.0 - 2026-04-06

### Changed

- Package metadata now uses unified maintainer, repository, and docs URL
  standards across `bijux-proteomics`.
- Package docs and maintainer references were aligned with the canon package
  documentation template.

## 0.1.0 - 2026-04-06

### Added

- Shared schema profile models for package-level document version contracts.
- Canonical serialization and fingerprinting helpers for deterministic payload
  behavior.
- Migration-oriented helpers for schema compatibility workflows.
