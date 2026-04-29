# Changelog

All notable changes for `bijux-proteomics-core` are recorded here.

## Unreleased

### Added

- Added strict and permissive FASTA parsing, protein normalization, sequence validation, normalized sequence checksums, FASTA deduplication, filtering, stats, provenance manifests, decoy generation, and target-decoy validation in `bijux_proteomics.sequences`.
- Added CLI surfaces for FASTA parsing, stats, deduplication, filtering, provenance manifests, sequence checksums, decoy generation, and target-decoy validation.
- Added protease registry contracts, full/semi-specific/non-specific digestion, missed-cleavage support, peptide length and mass filtering, uniqueness classification, and peptide-to-protein indexing in `bijux_proteomics.digestion`.
- Added digest manifests, stable TSV/JSONL exports, optional Parquet export, reproducibility fingerprints, benchmark reporting, and the `bijux-proteomics digest` CLI workflow with explicit diagnostics.
- Added peptide chemistry contracts for monoisotopic and average mass calculation, precursor m/z, fragment ions, neutral losses, static and variable modification models, modification registries, registry-file validation, and modified-peptide parsing in `bijux_proteomics.chemistry`.
- Added modified-peptide canonicalization, site-validation reports, charge-state models, isotope-envelope approximation, localization advisory output, checked chemistry regression fixtures, and the `bijux-proteomics peptide-mass` CLI workflow.
- Added search-result identification contracts for PSM parsing, engine column mapping, validation, target-decoy labeling, stable JSONL export, sorting, best-spectrum-hit selection, and peptide/protein evidence rollups in `bijux_proteomics.identification`.
- Added basic target-decoy FDR, monotonic q-value assignment, threshold filtering, PSM/peptide/protein summary reporting, provenance manifests, stable TSV export, and the `bijux-proteomics psm-inspect` and `bijux-proteomics fdr` CLI workflows.
- Added spectrum contracts for MGF parsing/rendering, peak normalization and filtering, TIC/base-peak metrics, precursor mass error, fragment annotation, TSV annotation export, and plot payload generation in `bijux_proteomics.spectra`.
- Added spectral similarity scoring, parser line diagnostics, spectrum provenance manifests, `spectrum-stats`, `spectrum-annotate`, `validate`, and `summarize` CLI workflows, and a checked first useful proteomics run fixture pack plus walkthrough documentation.

### Changed

- Exported the new FASTA and sequence-operation contracts through the package public API and README examples.
- Exported the new peptide chemistry and modification contracts through the package public API and README examples.
- Exported the new search-result identification contracts through the package public API and README examples.
- Expanded the README identification examples to cover thresholded FDR filtering, provenance manifests, and CLI inspection/export workflows.
- Expanded the README package examples to cover spectrum parsing, annotation, and plot payload generation.
- Expanded package docs with spectrum CLI examples and a copy-paste first useful proteomics run guide.

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
