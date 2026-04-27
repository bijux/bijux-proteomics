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

## Escalation signals

- if the same repository check, release rule, or docs contract is being copied
  into CI, root `make`, and local scripts, escalate it here first
- if a proposed maintainer helper cannot be explained without changing runtime
  or scientific package meaning, escalate it back to the owning package instead
- if policy enforcement starts behaving like a shadow implementation of product
  logic, treat that as a boundary failure and redesign the check surface

## Review questions

- does the change define repository governance, release policy, docs integrity,
  or maintainer automation rather than product behavior
- would CI YAML, shell glue, or one-off scripts become the de facto policy
  owner if this behavior stayed out of the maintainer package
- can the change still be defended without claiming runtime execution or
  scientific domain truth as maintainer-owned logic
