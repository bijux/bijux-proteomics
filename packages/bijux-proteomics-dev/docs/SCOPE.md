# Scope

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`

## This package owns

`bijux-proteomics-dev` owns repository maintenance behavior.

It defines shared checks and helper entrypoints used by root automation and CI.

## This package does not own

- runtime product APIs
- canonical proteomics domain models
- package-specific scientific semantics

## Downstream expectations

Repository automation should call into this package for shared checks instead of
duplicating gate logic in one-off shell fragments or workflow-local scripts.
