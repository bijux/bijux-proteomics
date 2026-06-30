# Changelog

This file records notable repository-level changes for `bijux-proteomics`.

It does not replace package-level release history. Versioning and package-local
release notes belong to each distribution under `packages/`.

Use this changelog for workspace changes that affect multiple packages or
change contributor and maintainer workflows across the repository.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the canonical `bijux-proteomics-runtime` publication line, the
  `agentic-proteins` compatibility bridge, and the short alias distributions
  `bijux-proteomics`, `proteomics`, `proteomics-core`,
  `proteomics-foundation`, `proteomics-runtime`,
  `proteomics-intelligence`, `proteomics-knowledge`, and `proteomics-lab`.
- Added the shared foundation kernel for canonical serialization,
  compatibility checks, identifiers, stable outcomes, and repository-wide
  support helpers consumed by downstream packages and release gates.
- Added the first full public core workflow surface for FASTA intake,
  digestion, chemistry, identification, spectra, mzML, search adapters,
  protein inference, label-free quantification, PTM analysis, QC, and workflow
  planning, including benchmark-backed CLI routes and walkthrough assets.
- Added the canonical runtime execution package with deterministic replay,
  archived rerun bundles, benchmark rerun kits, and public runtime proof
  routes for outsider rerun review.
- Added grounded scientific-memory, analytical-judgment, and lab-consequence
  owner surfaces so recommendation posture, contradiction handling, assay
  burden, and observed follow-up now stay explicit instead of implied.

### Changed

- Reworked repository and package docs around canonical owner packages,
  workflow trust limits, reader-first navigation, and executable README API
  examples.
- Folded reader-first docs routes into the numbered handbook owners so public
  product overview, workflow, execution, benchmark, decision, lab, and
  maintenance pages no longer depend on extra top-level journey directories.
- Rebuilt the public documentation system around hostile-review questions:
  workflow trust limits, benchmark freshness, flagship release evidence,
  runtime comparability, recommendation drift, and lab follow-up boundaries.
- Expanded repository-owned quality and release gates with architecture
  regression, public-API typecheck, circular-import scope, package-tree
  layout, orphan-module, generated-file, scientific-concept-ownership, and
  cross-package smoke checkpoints.
- Aligned root and package build metadata, fallback versions, and dependency
  floors with the `0.3.8` release line.

### Fixed

- Hardened security and release gating around optional provider dependencies,
  dependency vulnerability floors, safe-msgpack handling, and alias-package
  publication surfaces.

## 0.3.7 - 2026-04-21

### Changed

- Updated root and package README link text to readable markdown hyperlinks and aligned package docs URL references with canonical numbered handbook routes.

### Fixed

- GitHub policy workflow now handles non-commit `before` SHAs on tag-push events so policy checks stay stable during release tagging.

## 0.3.6 - 2026-04-20

### Changed

- Prepared the `v0.3.6` release line by aligning fallback versions and inter-package dependency floors across the repository.
- Synchronized release automation and governance with the `bijux-std v0.1.3` shared standards baseline.

### Fixed

- `release-pypi.yml` now uses parse-safe publication gating for token/bootstrap checks.
- Protected workflow policy checks now accept shared-manifest-driven standards updates through approved control paths.

## 0.3.5 - 2026-04-19

### Changed

- Repository workflow topology now mirrors `bijux-canon`, including
  `automerge-pr.yml`, `ci.yml`, and split release workflows for artifacts,
  PyPI, GHCR, and GitHub releases.
- Maintainer release and workflow handbook pages now describe the split release
  model and reference only checked-in workflow files.
- GitHub workflow and standards governance were synchronized with shared
  `bijux-std` contracts, including split release lanes and protected-change
  policy enforcement for managed automation surfaces.
- Documentation information architecture moved to numbered handbook roots
  (`docs/01-...` through `docs/08-...`), and repository docs links were
  aligned to those canonical paths.
- Docs synchronization and docs source-of-truth checks now resolve directly
  from `.bijux/shared/bijux-docs/tooling`.
- Shared make-layer and standards checks now reference `.bijux/shared/*`
  paths as the single repository source.

### Fixed

- Legacy references to removed workflows (`publish.yml`,
  `build-release-artifacts.yml`, and `ci-package.yml`) were removed from root
  docs, maintainer docs, and workflow contract tests.
- Badge templates and generated README badge blocks now follow the same catalog
  model used in `bijux-canon`.
- Removed the legacy root `internal/` docs tooling directory to eliminate
  outdated dual-path maintenance.
- Quality gate execution now resolves deptry through the shared root check
  environment, and tox no longer overrides make-layer virtualenv wiring.

## 0.3.4 - 2026-04-11

### Changed

- Publishable package fallback versions, maintainer dependency floors, and
  repository version metadata now align with the synchronized `v0.3.4`
  proteomics release line.
- Repository release guidance now describes the current tag-driven
  `hatch-vcs` version model used across all publishable packages.

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
