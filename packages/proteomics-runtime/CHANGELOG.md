# Changelog

All notable changes for `proteomics-runtime` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the `proteomics-runtime` distribution as the short install and import
  alias for `bijux-proteomics-runtime`.
- Added alias-package contract and README guidance that points runtime users to
  the canonical execution owner, rerun docs, and compatibility expectations.

### Changed

- Aligned the fallback version and canonical dependency floors with the
  `0.3.8` release line.
- Routed the alias through governed compatibility helpers, lazy imports, and
  clean-checkout runtime verification instead of implicit shim behavior.
