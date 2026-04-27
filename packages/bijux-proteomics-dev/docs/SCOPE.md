# Scope

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`

## This package owns

`bijux-proteomics-dev` owns repository maintenance behavior.

It defines shared checks and helper entrypoints used by root automation and CI.

## Owned maintenance surfaces

- release-readiness and packaging policy checks
- docs integrity, publication, and contract-shape enforcement
- API freeze and schema drift checks
- runtime migration governance and compat-boundary validation
- maintainer-only operational helpers that support root `make` and CI entrypoints

## This package does not own

- runtime product APIs
- canonical proteomics domain models
- package-specific scientific semantics

## Downstream expectations

Repository automation should call into this package for shared checks instead of
duplicating gate logic in one-off shell fragments or workflow-local scripts.

## Change routing expectations

- if a change belongs to repository policy, it should land here before CI or
  shell wrappers depend on it
- if a change belongs to runtime or scientific behavior, it should be routed
  back to the owning package and only enforced here once the package contract is
  clear
- maintainer helpers should narrow ambiguity, not become a shadow owner for
  product behavior
