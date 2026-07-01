# Changelog

All notable changes for `bijux-proteomics` are recorded here.

## Unreleased

## 0.3.8 - 2026-07-01

### Added

- Added the `bijux-proteomics` distribution as an install and command alias for
  `bijux-proteomics-core`.
- Added explicit package-contract and README guidance that points users from
  the top-level alias back to the canonical core owner and the numbered
  handbook routes.

### Changed

- Aligned the fallback version and canonical dependency floor with the
  `0.3.8` release line.
- Routed alias imports and command entrypoints through governed compatibility
  helpers with lazy loading and clean-checkout compatibility coverage instead
  of root shim behavior.
