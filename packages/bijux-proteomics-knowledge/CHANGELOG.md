# Changelog

All notable changes for `bijux-proteomics-knowledge` are recorded here.

## Unreleased

## 0.3.8 - 2026-07-01

### Added

- Added grounded scientific memory surfaces for cited references, ontologies,
  benchmark manifests, curated corpora, scientific rules, workflow briefing
  packets, comparator dossiers, contradiction audits, and machine-readable
  release-gate registries.
- Added query and resolution surfaces for protein identity, feature overlap,
  pathway membership, complex membership, kinase substrates, drug targets,
  disease terms, knowledge coverage, and cross-species orthologs.
- Added structured public grounding documentation and compatibility coverage
  for the public data-pack routes that now back workflow claim grounding.

### Changed

- Reorganized the package around durable `memory`, `references`, `reviews`,
  and `contracts` owner families, renamed public decision-brief routes, and
  tightened provenance and workflow caveat boundaries.
- Expanded executable README and package docs plus structured public docstrings
  for grounding and review APIs.
- Aligned dependency floors and fallback version with the `0.3.8` release
  line.

### Fixed

- Restored lint and typing contracts and stabilized accession-resolution
  assertions.

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
  numbered handbook route `06-bijux-proteomics-knowledge` for stable docs
  navigation.

## 0.3.4 - 2026-04-11

### Fixed

- Internal dependency floor now requires
  `bijux-proteomics-foundation>=0.3.4` for synchronized release installs.

## 0.3.3 - 2026-04-10

### Fixed

- Internal dependency floor now requires
  `bijux-proteomics-foundation>=0.3.3` for synchronized release installs.

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
  for synchronized package release expectations.
- README content was rewritten for clearer knowledge-layer responsibilities,
  usage context, and boundary guidance.
- Package description text was enhanced for clearer PyPI package discovery.

## 0.3.0 - 2026-04-06

### Added

- Canonical package maintainer documentation and package-level architecture
  references were added.

### Changed

- Package metadata now follows unified repository, issue, and documentation URL
  standards.

## 0.1.0 - 2026-04-06

### Added

- Evidence bundle and claim modeling with schema-aware serialization behavior.
- Trust scoring, freshness checks, and conflict detection semantics.
- Conflict-resolution actions and graph validation utilities.
