# Architecture

## Package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`

## Architectural role

The package is organized by maintenance domains:

- `quality` for linting and repository quality checks
- `security` for vulnerability and dependency policy gates
- `api` for OpenAPI contract drift checks
- `release` for version and changelog checks
- `docs` for documentation consistency checks
- `tools` for maintainers-only operational helpers

## Design constraints

API governance helpers treat `apis/<package>/v1/` as the contract root and
enforce:

- schema lint validity (`schema.yaml`)
- freeze integrity (`pinned_openapi.json` and `schema.hash`)
- backward-compatibility checks across package schemas

## Module topology

- `governance/` owns package-shape audits, release-blocking repository
  contracts, and cross-package structural truth reports
- `quality/` owns repository-level quality, boundary, and migration checks
- `security/` owns dependency and audit policy enforcement
- `quality/architecture/` owns OpenAPI freeze, drift, and boundary tooling
- `docs/` owns publication, link, and consistency enforcement
- `release/` owns release-readiness and workflow validation helpers
- `tools/` owns maintainer-only operational utilities

## Canonical tree layout

- Import roots: `bijux_proteomics_dev`
- Top-level families: `docs/`, `governance/`, `quality/`, `release/`, `security/`, `tools/`
- Root modules: none

## Dependency direction

This package may inspect repository state across every package, but it should
not become the owner of product runtime or scientific domain behavior.

## Downstream expectations

Root automation and CI should call into these modules instead of duplicating
policy logic inside workflow YAML or one-off shell scripts.

## Extension signals

- add code here when a new concern changes repository policy, maintainer
  automation, or cross-package validation behavior
- extend `quality/`, `security/`, `api/`, `docs/`, `release/`, or `tools/`
  before shell scripts or workflow YAML re-encode the same rule
- keep new maintenance behavior here when it defines repository governance
  rather than product runtime or scientific semantics

## Misplacement signals

- if the change defines product execution behavior or scientific meaning, it
  belongs in an owning package instead of the maintainer toolkit
- if a helper exists only because one workflow wants ad hoc shell glue, prefer
  moving the durable policy into this package and keeping workflows thin
- if the policy cannot be explained without product semantics, the owning
  package contract is probably the right home for the behavior

## Review questions

- does the change define repository governance, release policy, docs integrity,
  or maintainer automation rather than product behavior
- would workflow YAML, ad hoc shell glue, or local scripts become the de facto
  owner if this rule stayed out of the maintainer package
- can the architecture still be explained without claiming runtime execution or
  scientific domain truth inside repository policy code
