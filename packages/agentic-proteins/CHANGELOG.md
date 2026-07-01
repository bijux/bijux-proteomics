# Changelog

All notable changes for `agentic-proteins` are recorded here.

## Unreleased

## 0.3.8 - 2026-07-01

### Changed

- Reframed the package around the real compatibility-bridge contract instead
  of the retired full-runtime description, with docs and metadata that point
  readers back to canonical runtime ownership.
- Narrowed direct dependencies to the only owners the bridge should forward
  into: `bijux-proteomics-runtime` and `bijux-proteomics-core`.
- Kept legacy CLI and import continuity explicit while preserving
  forwarding-only package ownership and migration-ledger visibility.
- Aligned fallback version and optional dependency floors with the `0.3.8`
  release line.

### Fixed

- Restored clean-checkout compatibility imports, lazy forwarding behavior,
  package contract checks, and isolated local-model test surfaces so the bridge
  behaves like a compatibility shim instead of a second runtime owner.

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
  numbered handbook route `02-agentic-proteins` for stable docs navigation.

## 0.3.4 - 2026-04-11

### Changed

- Release history now records the synchronized `v0.3.4` proteomics publication
  line used by the shared tag-driven release workflow.

## 0.3.3 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.3.3` proteomics publication
  line used by the shared tag-driven release workflow.

## 0.3.2 - 2026-04-10

### Changed

- Release history now records the synchronized `v0.3.2` proteomics publication
  line used by the shared tag-driven release workflow.

## 0.3.1 - 2026-04-06

### Added

- Package family PyPI and docs badges were added to README and maintainer
  package notes for cross-package discoverability.

### Changed

- README content was rewritten with clearer package value proposition, usage
  scenarios, installation, quick-start guidance, and boundary definitions.
- Package description text was enhanced for stronger PyPI search relevance and
  package discovery.

## 0.3.0 - 2026-04-06

### Added

- Package-local release manifest and maintainer-facing package docs:
  `README.md`, `docs/ARCHITECTURE.md`, `docs/BOUNDARIES.md`,
  `docs/CONTRACTS.md`, and `docs/maintainer/pypi.md`.
- Package-local changelog publishing path wired in package and root metadata.

### Changed

- Package URLs now consistently reference `bijux.io/bijux-proteomics` and
  `github.com/bijux/bijux-proteomics`.

### Fixed

- Test path resolution now uses explicit monorepo-root detection so e2e,
  regression, and governance tests stay stable with nested package manifests.

## 0.2.3 - 2026-01-16

### Added

- Expanded provider test coverage for ColabFold, OpenProtein, and local
  ESMFold utilities.
- Runtime capability validation tests and candidate filter unit coverage.
- Stability marking test for module annotations.

### Changed

- Hardened local ESMFold utility tests to exercise error and success branches.

### Fixed

- Reliability checks and helper tests to keep coverage and gating stable.

## 0.2.2 - 2026-01-16

### Added

- Release alignment for docs, gates, and CI structure.

### Changed

- Consistent documentation build and validation wiring.

### Fixed

- Minor release hygiene issues discovered in CI.

## 0.2.1 - 2026-01-16

### Added

- Expanded unit and integration coverage with new invariants, API, and docs
  gates.
- Additional tests for provider isolation, reproducibility, and abuse-case
  blocking.
- Fancy PyPI readme fragments for README + changelog publishing.

### Changed

- Refactored `tests/unit` into a structured layout for clearer ownership.

### Fixed

- Coverage floors and CI gates stabilized around new test layout.

## 0.2.0 - 2026-01-16

### Added

- Architecture invariants, threat model skeleton, and design debt ledger.
- Reproducible runs via `agentic-proteins reproduce <run_id>` with hash
  checks.
- Determinism tests, artifact immutability tests, and invariant regression
  coverage.
- Provider isolation checks and chaos failure test for mid-run provider loss.
- Benchmark regression gate and per-module coverage floors in CI.
- Documentation system contracts, lint gates, and CLI surface audit coverage.
- API error taxonomy enforcement, correlation ID logging test, and OpenAPI
  drift guard.
- Dependency allowlist enforcement for SBOM changes.

## 0.1.0 - 2026-01-14

### Added

- Deterministic, artifact-first execution engine with explicit run directories
  and state snapshots.
- Agent-based architecture covering planning, analysis, execution,
  verification, and reporting.
- End-to-end design loop with failure handling, stagnation detection, and
  human-in-the-loop gating.
- CLI for running, resuming, inspecting, comparing, and exporting protein
  design runs.
- Local and remote provider abstractions with explicit capability and
  requirement checks.
- Structured reporting system with machine-readable artifacts and
  human-readable summaries.
- Integrated evaluation pipeline supporting structure-based metrics and
  ground-truth comparison.
- Reproducibility controls, observability hooks, and execution telemetry.
- Example datasets and reference runs for local experimentation and validation.
- Comprehensive test suite covering unit, integration, regression, and
  execution boundaries.
