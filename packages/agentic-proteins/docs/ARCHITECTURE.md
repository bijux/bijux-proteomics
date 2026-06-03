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

- package root exposes version metadata only
- `interfaces/`, `agents/`, `orchestration/`, `providers/`, `state/`, and
  `tools/` are the durable bridge families
- `execution/`, `agents/execution/`, and `providers/experimental/` survive
  only as legacy aliases that forward into the durable families
- compat docs explain canonical owners and the migration route away from each
  surviving family

## Canonical tree layout

- Import roots: `agentic_proteins`, `agentic_proteins_testsupport`
- Top-level families: `agents/`, `execution/`, `interfaces/`, `orchestration/`, `providers/`, `state/`, `tools/`
- Root modules: none

## Dependency direction

Compat may depend on canonical packages to preserve historical entrypoints.

Canonical packages must not depend on `agentic_proteins`.

## Downstream expectations

New integrations should start from canonical packages. This package exists to
reduce migration risk, not to accumulate fresh runtime or scientific logic.

## Extension signals

- add code here only when a new concern preserves legacy import or CLI
  continuity for an already-canonical surface
- extend forwarding trees before reintroducing behavioral code into compat
- keep compat changes narrowly focused on migration safety and canonical-owner
  visibility

## Misplacement signals

- if the change defines runtime orchestration, provider behavior, or any domain
  semantics, it belongs in the canonical owning package instead
- if a helper mainly serves new integrations rather than legacy continuity, it
  should start in canonical packages and only then gain compat forwarding
- if a module stops being forwarding-only, treat that as an architecture smell
  and route the implementation back to the owner

## Review questions

- does the change preserve legacy continuity for an already-canonical surface
  without inventing fresh product behavior
- would the behavior still make sense if the compat package were removed after
  migration, with the true implementation living only in canonical packages
- can the architecture still be described as forwarding-only without ambiguity
  about the runtime or lower canonical owner
