# Changelog

All notable changes for `proteomics-foundation` are recorded here.

## Unreleased

## 0.3.8 - 2026-06-30

### Added

- Added the `proteomics-foundation` distribution as the short install and
  import alias for `bijux-proteomics-foundation`.
- Added alias-package contract and README guidance that points short-name
  users back to the canonical foundation owner and its handbook.

### Changed

- Aligned the fallback version and canonical dependency floor with the
  `0.3.8` release line.
- Routed the alias through governed compatibility helpers and clean-checkout
  verification so the short distribution stays a forwarding layer instead of a
  second foundation surface.
