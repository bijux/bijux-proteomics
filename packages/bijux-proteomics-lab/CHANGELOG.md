# Changelog

All notable changes for `bijux-proteomics-lab` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added typed experiment-design, protocol-planning, planning-readiness,
  handoff, reconciliation, and follow-up packet contracts for DDA, DIA, LFQ,
  PTM, and targeted workflows.
- Added targeted benchmark rehearsal, refusal, outcome dossier, and learning
  surfaces so assay burden, handoff quality, and observed follow-up stay
  reviewable.

### Changed

- Reorganized the package around durable owner bands for design, planning,
  readiness, lifecycle, handoffs, outcomes, reconciliation, and benchmarks and
  narrowed the package root to planning entrypoints.
- Expanded package docs with executable API examples and workflow notes for
  experiment design, handoff safety, refusal limits, and outcome learning.
- Aligned dependency floors and fallback version with the `0.3.8` release
  line.

### Fixed

- Decoupled feedback forecasting from queue ownership and normalized handoff
  and package contracts.

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
  numbered handbook route `07-bijux-proteomics-lab` for stable docs
  navigation.

## 0.3.4 - 2026-04-11

### Fixed

- Internal dependency floors now require
  `bijux-proteomics-foundation>=0.3.4`,
  `bijux-proteomics-core>=0.3.4`, and
  `bijux-proteomics-knowledge>=0.3.4` for synchronized release installs.

## 0.3.3 - 2026-04-10

### Fixed

- Internal dependency floors now require
  `bijux-proteomics-foundation>=0.3.3`,
  `bijux-proteomics-core>=0.3.3`, and
  `bijux-proteomics-knowledge>=0.3.3` for synchronized release installs.

## 0.3.2 - 2026-04-10

### Fixed

- Internal dependency floors now require
  `bijux-proteomics-foundation>=0.3.2`,
  `bijux-proteomics-core>=0.3.2`, and
  `bijux-proteomics-knowledge>=0.3.2` for synchronized release installs.

## 0.3.1 - 2026-04-06

### Added

- Package family PyPI and docs badges were added to README and maintainer
  package notes for cross-package discoverability.

### Changed

- Versioning now uses tag-driven dynamic release metadata via `hatch-vcs`
  instead of static package version pinning.
- Internal dependency floors were raised to
  `bijux-proteomics-foundation>=0.3.1`,
  `bijux-proteomics-core>=0.3.1`, and
  `bijux-proteomics-knowledge>=0.3.1`.
- README content was rewritten for clearer lab-planning responsibilities,
  usage scenarios, and package boundaries.
- Package description text was enhanced for clearer PyPI package discovery.

## 0.3.0 - 2026-04-06

### Added

- Canonical package documentation and maintainer notes were added for lab
  package ownership boundaries.

### Changed

- Package metadata and release links now match the shared `bijux-proteomics`
  standards.

## 0.1.0 - 2026-04-06

### Added

- Experiment planning and dependency-aware scheduling utilities.
- Outcome summarization, failure triage, and rerun recommendation models.
- Repository contracts for plan, queue, and feedback persistence.
