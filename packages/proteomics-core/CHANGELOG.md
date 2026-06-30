# Changelog

All notable changes for `proteomics-core` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the `proteomics-core` distribution as the short install and import
  alias for `bijux-proteomics-core`.
- Added alias-package contract and architecture docs that explain why the
  short distribution is a forwarding surface rather than a second owner.

### Changed

- Aligned the fallback version and canonical dependency floors with the
  `0.3.8` release line.
- Routed the alias through governed compatibility helpers, lazy imports, and
  clean-checkout verification so the short name stays a thin surface over the
  canonical core package.
