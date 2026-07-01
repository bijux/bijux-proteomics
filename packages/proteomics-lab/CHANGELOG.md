# Changelog

All notable changes for `proteomics-lab` are recorded here.

## Unreleased

## 0.3.8 - 2026-07-01

### Added

- Added the `proteomics-lab` distribution as the short install and import alias
  for `bijux-proteomics-lab`.
- Added alias-package contract and README guidance that points readers to the
  canonical assay-planning and outcome-learning owner.

### Changed

- Aligned the fallback version and canonical dependency floors with the
  `0.3.8` release line.
- Routed the alias through governed compatibility helpers and clean-checkout
  verification so the short distribution stays a forwarding layer over the
  lab package.
