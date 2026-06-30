# Changelog

All notable changes for `bijux-proteomics-core` are recorded here.

## Unreleased

- [robustness] No post-`0.3.8` label-free quantification change is queued yet;
  the next quantification or `quantify`-facing change must be recorded here
  before release.

## 0.3.8 - 2026-06-30

### Added

- Added sequence and database-preparation workflows for FASTA parsing,
  normalization, checksums, filtering, provenance manifests, decoy generation,
  and target-decoy validation, plus CLI routes for inspection and export.
- Added digestion and chemistry workflows for protease registries, digest
  manifests, reproducible exports, peptide mass and modification handling,
  site-validation reports, isotope approximations, and localized peptide-mass
  diagnostics.
- Added identification and evidence workflows for PSM parsing, engine-column
  normalization, target-decoy labeling, FDR, peptide and protein evidence
  rollups, spectrum annotation and similarity, mzML ingestion, search-adapter
  normalization, config validation, and calibration and conformance reports.
- Added downstream biological-result workflows for protein inference, grouped
  and picked-protein FDR, label-free quantification, PTM localization and
  occupancy, LC-MS QC, and workflow planning, each with governed CLI entry
  routes and machine-readable outputs.
- Added benchmark-backed walkthrough assets, production-style fixture packs,
  the shipped demo CLI path, and the first useful proteomics run route so
  readers can exercise the public core surface end to end.

### Changed

- Split the identification and quantification public facades into governed
  owner families with machine-readable export ledgers and narrower internal
  import contracts.
- Reorganized workflow reporting, biological result rendering, and quant-table
  surfaces into direct owner bundles instead of broad report wrappers.
- Expanded executable README examples, the shipped demo CLI tutorial, and
  package docs across FASTA, digestion, chemistry, identification, spectra,
  mzML, search adapters, protein inference, quantification, PTM, QC, and
  workflow planning.
- Aligned the foundation dependency floor and fallback version with the
  `0.3.8` release line.

### Fixed

- Restored PTM report compatibility, moved-owner facade contracts, and report
  and benchmark regression stability after the workflow-surface split.

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
  numbered handbook route `04-bijux-proteomics-core` for stable docs
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
