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

- `quality/` owns repository-level quality, boundary, and migration checks
- `security/` owns dependency and audit policy enforcement
- `api/` owns OpenAPI freeze and drift tooling
- `docs/` owns publication, link, and consistency enforcement
- `release/` owns release-readiness and workflow validation helpers
- `tools/` owns maintainer-only operational utilities

## Dependency direction

This package may inspect repository state across every package, but it should
not become the owner of product runtime or scientific domain behavior.

## Downstream expectations

Root automation and CI should call into these modules instead of duplicating
policy logic inside workflow YAML or one-off shell scripts.
