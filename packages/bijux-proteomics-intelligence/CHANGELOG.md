# Changelog

All notable changes for `bijux-proteomics-intelligence` are recorded here.

## Unreleased

## 0.3.8 - 2026-07-01

### Added

- Added typed proteomics interpretation contracts for run summaries,
  differential-abundance interpretation, PTM interpretation, contaminant and
  artifact intelligence, contrast recommendation, missingness analysis, outlier
  explanation, overrepresentation enrichment, and ranked enrichment.
- Added typed review and report contracts that keep benchmark workflow packets,
  contradiction-ready audits, and external review preparation explicit instead
  of spreading them across ad hoc helpers.

### Changed

- Reorganized the package around durable owner families for candidates,
  judgment, posture, interpretation, reviews, and learning, including stable
  review-entrypoint naming for decision briefs.
- Expanded package docs with executable API examples and a dedicated
  interpretation workflow guide.
- Aligned dependency floors and fallback version with the `0.3.8` release
  line.

### Fixed

- Normalized audit, contradiction, benchmark-review, and strict question
  contracts so flagship and PTM review evidence remains consistent under
  package typing and review checks.

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
  numbered handbook route `05-bijux-proteomics-intelligence` for stable docs
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
- README content was rewritten to improve decision-intelligence usage guidance,
  package boundaries, and quick-start orientation.
- Package description text was enhanced for clearer PyPI package discovery.

## 0.3.0 - 2026-04-06

### Added

- Canonical package documentation set and maintainer notes were added for
  stable contributor onboarding.

### Changed

- Package metadata now aligns with shared project URL and release-link
  conventions.

## 0.1.0 - 2026-04-06

### Added

- Candidate ranking policies and structured rejection outcomes.
- Program-to-brief conversion and explainability-oriented scoring outputs.
- Scenario and portfolio evaluators for progression and redesign decisions.
