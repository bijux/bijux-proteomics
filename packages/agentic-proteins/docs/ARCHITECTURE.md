# Architecture

## Package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## Architectural role

`agentic-proteins` is the strict compatibility bridge for historical runtime
entrypoints.

## Design constraints

- compat imports must forward to canonical packages instead of redefining behavior
- legacy CLI and import roots remain available while migration proceeds
- canonical ownership stays in runtime and lower `bijux-proteomics-*` packages

## Module topology

- package root preserves legacy convenience exports
- `interfaces/`, `api/`, `core/`, `runtime/`, and related trees act as forwarding surfaces
- compat docs explain canonical owners and API-root mirroring

## Dependency direction

Compat may depend on canonical packages to preserve historical entrypoints.

Canonical packages must not depend on `agentic_proteins`.

## Downstream expectations

New integrations should start from canonical packages. This package exists to
reduce migration risk, not to accumulate fresh runtime or domain logic.
