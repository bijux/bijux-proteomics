# Changelog

All notable changes for `proteomics` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the `proteomics` distribution as the short install, import, and CLI
  alias for `bijux-proteomics-core`.
- Added explicit alias-package contract and README guidance so the short name
  still routes readers and imports to the canonical core owner.

### Changed

- Aligned the fallback version and canonical dependency floors with the
  `0.3.8` release line.
- Routed short-name compatibility through governed foundation helpers, lazy
  imports, and clean-checkout alias verification instead of durable shim
  modules.
