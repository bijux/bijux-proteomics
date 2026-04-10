# Changelog

All notable changes for `bijux-proteomics-core` are recorded here.

## 0.3.2 - 2026-04-10

### Fixed

- Internal dependency floor now requires
  `bijux-proteomics-foundation>=0.3.2` for synchronized release installs.

## 0.3.1 - 2026-04-06

### Added

- Package family PyPI and docs badges were added to README and maintainer
  package notes for cross-package discoverability.

### Changed

- Versioning now uses tag-driven dynamic release metadata via `hatch-vcs`
  instead of static package version pinning.
- Internal dependency floor was raised to `bijux-proteomics-foundation>=0.3.1`
  to match synchronized release expectations.
- README content was rewritten to improve package purpose clarity, usage
  guidance, and ownership boundaries.
- Package description text was enhanced for clearer PyPI package discovery.

## 0.3.0 - 2026-04-06

### Added

- Package maintainer and ownership docs were added in canonical package-doc
  format.

### Changed

- Package metadata and release links now follow unified `bijux-proteomics`
  repository standards.

## 0.1.0 - 2026-04-06

### Added

- Program domain models for targets, assays, review gates, and lifecycle
  transitions.
- Domain invariant validation and identifier-contract checks.
- Runtime adapter and CLI boundaries for package-level integration.
